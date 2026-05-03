"""
YAML frontmatter parser for Markdown files.

Provides functions to parse, extract, and inject YAML frontmatter
fields.  No external dependencies — uses only stdlib `re`.
The frontmatter is assumed to be flat scalar key: value pairs.
"""

import re


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """
    Parse a Markdown file's YAML frontmatter block.

    Returns:
        (fields_dict, body_text)

        fields_dict: key-value pairs from the frontmatter (excluding '---').
        body_text: everything after the closing '---'.

    Raises:
        ValueError: if the frontmatter is malformed (missing opening/closing ---).
    """
    lines = content.splitlines(keepends=True)
    frontmatter_lines: list[str] = []
    in_frontmatter = False
    delim_count = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---":
            delim_count += 1
            if delim_count == 1:
                in_frontmatter = True
                continue
            elif delim_count == 2:
                body = "".join(lines[i + 1:])
                break
        if in_frontmatter:
            frontmatter_lines.append(line)
    else:
        msg = "Malformed frontmatter: "
        if delim_count == 0:
            msg += "missing opening '---'"
        elif delim_count == 1:
            msg += "missing closing '---'"
        else:
            msg += f"unexpected delimiter count: {delim_count}"
        raise ValueError(msg)

    fields: dict[str, str] = {}
    for line in frontmatter_lines:
        line = line.strip()
        if not line:
            continue
        # Split on the first colon-space
        m = re.match(r"^([^:]+?):\s*(.*?)$", line)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            fields[key] = value

    return fields, body


def get_field(content: str, field_name: str) -> str | None:
    """
    Extract a named scalar value from the file content's frontmatter.
    Returns None if field not found.
    """
    try:
        fields, _ = parse_frontmatter(content)
    except ValueError:
        return None
    return fields.get(field_name)


def inject_field(content: str, field_name: str, value: str,
                 after_field: str | None = None) -> str:
    """
    Insert a new field into the frontmatter.

    If after_field is given, insert it on the line after that field;
    otherwise append just before the closing '---'.

    If field_name already exists, replace its value.  If the
    frontmatter is missing, return the content unchanged.

    Returns: modified content string.
    """
    lines = content.splitlines(keepends=True)
    frontmatter_start: int | None = None
    frontmatter_end: int | None = None

    for i, line in enumerate(lines):
        if line.strip() == "---":
            if frontmatter_start is None:
                frontmatter_start = i
            elif frontmatter_end is None:
                frontmatter_end = i
                break

    if frontmatter_start is None or frontmatter_end is None:
        # No valid frontmatter — return unchanged
        return content

    # Check if field already exists
    for i in range(frontmatter_start + 1, frontmatter_end):
        m = re.match(rf"^{re.escape(field_name)}\s*:", lines[i].strip())
        if m:
            # Replace value
            lines[i] = f"{field_name}: {value}\n"
            return "".join(lines)

    if after_field:
        for i in range(frontmatter_start + 1, frontmatter_end):
            if lines[i].strip().startswith(f"{after_field}:"):
                lines.insert(i + 1, f"{field_name}: {value}\n")
                frontmatter_end += 1
                return "".join(lines)

    # Append before closing ---
    lines.insert(frontmatter_end, f"{field_name}: {value}\n")
    return "".join(lines)
