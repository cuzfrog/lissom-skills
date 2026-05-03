export const VersionTimestampPlugin = async ({ directory, $ }) => {
  return {
    "file.watcher.updated": async (input) => {
      const filePath = input.filePath || input.path;
      if (!filePath) return;

      const relative = filePath.replace(directory + "/", "");
      if (!relative.startsWith("agents/") && !relative.startsWith("skills/")) return;

      const payload = JSON.stringify({ file_path: relative });
      await $`echo ${payload} | ${directory}/dev/update-version-timestamp.sh`;
    },
  };
};
