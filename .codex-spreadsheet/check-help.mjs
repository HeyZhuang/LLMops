import { Workbook } from "@oai/artifact-tool";
const wb = Workbook.create();
const res = wb.help('*', { search: 'print|page setup|pageSetup|paper|fitToPage|page layout|margins', include: 'index', maxChars: 4000 });
console.log(res.ndjson || JSON.stringify(res));
