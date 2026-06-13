import { FileBlob, SpreadsheetFile } from "file:///C:/Users/vince/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const targetPath = process.argv[2];

if (!targetPath) {
  console.error("Usage: node inspect_lqp14_template.mjs <xls-path>");
  process.exit(1);
}

async function main() {
  const input = await FileBlob.load(targetPath);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const summary = await workbook.inspect({
    kind: "workbook,sheet,table,region",
    maxChars: 12000,
    tableMaxRows: 20,
    tableMaxCols: 16,
    tableMaxCellChars: 120,
  });
  console.log(summary.ndjson);
}

main().catch((error) => {
  console.error("IMPORT_FAILED");
  console.error(error?.stack || String(error));
  process.exit(2);
});
