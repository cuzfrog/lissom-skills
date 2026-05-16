/**
 * lissom-agent — Pi extension tool that spawns headless pi subagent processes.
 *
 * Each invocation reads the named agent's .md definition from the bundled
 * agents/ directory, passes it to a child `pi --print --no-skills --no-session`
 * process, and returns stdout as the tool result.
 *
 * Agents are bundled alongside this file under agents/<name>.md.
 */

import { spawn } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const TIMEOUT_MS = 20 * 60 * 1000; // 20 minutes

// Claude Code tool name → Pi --tools flag name
const TOOL_FLAG_MAP: Record<string, string> = {
  Bash: "bash",
  Read: "read",
  Write: "write",
  Edit: "edit",
  Glob: "find,ls",
  Grep: "grep",
};

interface AgentFrontmatter {
  tools: string;
}

/**
 * Naive frontmatter parser for agent .md files.
 * Extracts scalar key: value pairs from YAML frontmatter between --- delimiters.
 */
function parseAgentFrontmatter(
  content: string
): { fields: AgentFrontmatter; body: string } {
  const lines = content.split("\n");
  const fields: Record<string, string> = {};
  let inFm = false;
  let fmDone = false;
  let bodyStart = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trimEnd();
    if (!inFm && line.trim() === "---") {
      inFm = true;
      continue;
    }
    if (inFm && line.trim() === "---") {
      fmDone = true;
      bodyStart = i + 1;
      break;
    }
    if (inFm) {
      const m = line.trim().match(/^([^:]+?):\s*(.*?)$/);
      if (m) {
        fields[m[1].trim()] = m[2].trim();
      }
    }
  }

  const body = fmDone ? lines.slice(bodyStart).join("\n") : content;
  return { fields: fields as unknown as AgentFrontmatter, body };
}

/**
 * Resolve the `pi` binary invocation using the same pattern as the
 * reference subagent example.
 */
function getPiInvocation(args: string[]): { command: string; args: string[] } {
  const currentScript = process.argv[1];
  if (currentScript && !currentScript.startsWith("/$bunfs/root/") && fs.existsSync(currentScript)) {
    return { command: process.execPath, args: [currentScript, ...args] };
  }

  const execName = path.basename(process.execPath).toLowerCase();
  if (!/^(node|bun)(\.exe)?$/.test(execName)) {
    return { command: process.execPath, args };
  }

  return { command: "pi", args };
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "lissom-agent",
    label: "Lissom Agent",
    description:
      "Spawn a lissom subagent with an isolated context window. " +
      "Pass the agent name and a fully self-contained prompt (with args already interpolated).",
    parameters: Type.Object({
      agent: Type.String({
        description: "Agent name, e.g. lissom-researcher",
      }),
      prompt: Type.String({
        description:
          "Fully self-contained task prompt with args interpolated by the caller",
      }),
    }),

    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const agentPath = path.join(
        import.meta.dirname,
        "agents",
        `${params.agent}.md`
      );

      let agentContent: string;
      try {
        agentContent = fs.readFileSync(agentPath, "utf-8");
      } catch {
        return {
          content: [
            {
              type: "text",
              text: `Agent "${params.agent}" not found. Expected file: ${agentPath}`,
            },
          ],
          isError: true,
        };
      }

      // Parse frontmatter to extract tools
      const { fields } = parseAgentFrontmatter(agentContent);
      const toolList = fields.tools
        ? fields.tools
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean)
        : [];

      // Build pi args
      const args: string[] = ["--print", "--no-skills", "--no-session"];

      if (toolList.length > 0) {
        const piTools: string[] = [];
        for (const t of toolList) {
          const mapped = TOOL_FLAG_MAP[t];
          if (mapped) {
            // Glob maps to "find,ls" - split comma-separated entries
            piTools.push(...mapped.split(","));
          }
        }
        if (piTools.length > 0) {
          args.push("--tools", [...new Set(piTools)].join(","));
        }
      }

      // The prompt is the positional message argument
      args.push(params.prompt);

      const invocation = getPiInvocation(args);

      return new Promise((resolve) => {
        let stdout = "";
        let stderr = "";
        let killed = false;

        const proc = spawn(invocation.command, invocation.args, {
          cwd: ctx.cwd,
          shell: false,
          stdio: ["pipe", "pipe", "pipe"],
        });

        // Write agent definition to stdin and close it
        proc.stdin.write(agentContent);
        proc.stdin.end();

        proc.stdout.on("data", (data: Buffer) => {
          stdout += data.toString();
        });

        proc.stderr.on("data", (data: Buffer) => {
          stderr += data.toString();
        });

        // Timeout
        const timer = setTimeout(() => {
          killed = true;
          proc.kill("SIGTERM");
          setTimeout(() => {
            if (!proc.killed) proc.kill("SIGKILL");
          }, 5000);
        }, TIMEOUT_MS);

        // Abort signal
        if (signal) {
          const onAbort = () => {
            clearTimeout(timer);
            killed = true;
            proc.kill("SIGTERM");
            setTimeout(() => {
              if (!proc.killed) proc.kill("SIGKILL");
            }, 5000);
          };
          if (signal.aborted) {
            onAbort();
          } else {
            signal.addEventListener("abort", onAbort, { once: true });
          }
        }

        proc.on("close", (code) => {
          clearTimeout(timer);

          if (killed) {
            resolve({
              content: [
                {
                  type: "text",
                  text: "Subagent was aborted or timed out.",
                },
              ],
              isError: true,
            });
            return;
          }

          if (code !== 0) {
            resolve({
              content: [
                {
                  type: "text",
                  text:
                    `Subagent exited with code ${code}.\n\n` +
                    (stderr ? `Stderr:\n${stderr}\n\n` : "") +
                    (stdout ? `Output:\n${stdout}` : "(no output)"),
                },
              ],
              isError: true,
            });
            return;
          }

          resolve({
            content: [{ type: "text", text: stdout || "(no output)" }],
          });
        });

        proc.on("error", (err) => {
          clearTimeout(timer);
          resolve({
            content: [
              {
                type: "text",
                text: `Failed to spawn subagent process: ${err.message}`,
              },
            ],
            isError: true,
          });
        });
      });
    },
  });
}
