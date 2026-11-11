const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const work = __dirname;
const sourcePath = path.resolve(work, '..', '英语 アンケート.txt');
const outputPath = path.join(work, 'questionnaire_print.html');
const source = fs.readFileSync(sourcePath, 'utf8').replace(/^\uFEFF/, '');
const pages = [];
let current = null;
source.split(/\r?\n/).forEach((text, index) => {
  const match = /^PAGE (\d+)\s*$/.exec(text);
  if (match) {
    current = { number: Number(match[1]), lines: [] };
    pages.push(current);
  } else if (text.trim()) {
    if (!current) throw new Error('Text outside a PAGE section');
    current.lines.push({ text: text.trim(), id: index + 1 });
  }
});
if (pages.length !== 12 || pages.some((p, i) => p.number !== i + 1)) {
  throw new Error('The finalized source must contain PAGE 1 through PAGE 12.');
}

const used = new Map();
const escapeHtml = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
function textHtml(s) {
  return escapeHtml(s).replace(/\[( |x)\]/g, (match, value) =>
    `<span class="checkbox${value === 'x' ? ' checked' : ''}" data-checked="${value === 'x'}">${match}</span>`);
}
function use(line) {
  used.set(line.id, (used.get(line.id) || 0) + 1);
  return line;
}
function element(line, tag = 'p', className = '') {
  use(line);
  return `<${tag} data-line="${line.id}"${className ? ` class="${className}"` : ''}>${textHtml(line.text)}</${tag}>`;
}
const isSeparator = line => /^\|?\s*:?-{3,}/.test(line.text);
const isTableLine = line => line.text.includes('|');
const isBlankLine = line => /^_{10,}$/.test(line.text);
function cells(line) {
  return line.text.replace(/^\|\s*/, '').replace(/\s*\|$/, '').split('|').map(s => s.trim());
}
function table(lines, tableClass = '') {
  const data = lines.filter(line => !isSeparator(line));
  lines.filter(isSeparator).forEach(use);
  const columnCount = cells(data[0]).length;
  const colgroup = tableClass.includes('rules')
    ? '<colgroup><col style="width:47%"><col style="width:10.6%"><col style="width:10.6%"><col style="width:10.6%"><col style="width:10.6%"><col style="width:10.6%"></colgroup>'
    : tableClass.includes('conservation')
      ? '<colgroup><col style="width:53%"><col style="width:18%"><col style="width:29%"></colgroup>'
      : tableClass.includes('stakeholders')
        ? '<colgroup><col style="width:73%"><col style="width:27%"></colgroup>' : '';
  const rows = data.map((line, index) => {
    use(line);
    const row = cells(line);
    if (row.length !== columnCount) throw new Error(`Wrong column count at source line ${line.id}`);
    const tag = index === 0 ? 'th' : 'td';
    return `<tr data-line="${line.id}">${row.map((cell, cellIndex) =>
      `<${tag}${cellIndex > 0 && tableClass.match(/rules|conservation/) ? ' class="response-cell"' : ''}>${textHtml(cell)}</${tag}>`).join('')}</tr>`;
  });
  return `<table class="${tableClass}">${colgroup}<thead>${rows[0]}</thead><tbody>${rows.slice(1).join('')}</tbody></table>`;
}

function standard(lines, pageNumber) {
  const result = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (isTableLine(line)) {
      const group = [line];
      while (i + 1 < lines.length && isTableLine(lines[i + 1])) group.push(lines[++i]);
      const cls = pageNumber === 2 || pageNumber === 3 ? 'rules'
        : pageNumber === 4 ? 'conservation' : pageNumber === 11 ? 'complaints' : '';
      result.push(table(group, cls));
    } else if (isBlankLine(line)) {
      const group = [line];
      while (i + 1 < lines.length && isBlankLine(lines[i + 1])) group.push(lines[++i]);
      result.push(`<div class="writing-area">${group.map(l => element(l, 'p', 'writing-line')).join('')}</div>`);
    } else if (/^\d+\. /.test(line.text)) {
      result.push(element(line, 'h2'));
    } else if (line.text === 'Guidance for completing the questionnaire') {
      result.push(element(line, 'h1', 'guidance-title'));
    } else if (line.text === 'Survey details') {
      result.push(element(line, 'h2', 'survey-details'));
    } else if (/^(How to answer|Example of a completed response|Activity reference list)/.test(line.text)) {
      result.push(element(line, 'h3'));
    } else if (line.text.startsWith('Q')) {
      result.push(element(line, 'p', 'question'));
    } else if (line.text === '↓') {
      result.push(element(line, 'p', 'down-arrow'));
    } else if (line.text.startsWith('[ ]') || line.text.startsWith('[x]')) {
      result.push(element(line, 'p', 'option'));
    } else {
      const cls = /^(\(1\) Student conducting|\(2\) Contact information)/.test(line.text) ? 'contact-heading'
        : line.text.startsWith('This completes the questionnaire.') ? 'closing'
          : line.text.startsWith('If there are several activities,') ? 'example-explanation' : '';
      result.push(element(line, 'p', cls));
    }
  }
  return result.join('\n');
}

function q3(page) {
  const firstTable = page.lines.findIndex(isTableLine);
  let tableEnd = firstTable;
  while (tableEnd < page.lines.length && isTableLine(page.lines[tableEnd])) tableEnd++;
  const arrow = page.lines.findIndex(line => line.text === '↓');
  const referenceEnd = arrow === -1 ? page.lines.length : arrow;
  const prefix = standard(page.lines.slice(0, firstTable), page.number);
  const left = table(page.lines.slice(firstTable, tableEnd), 'stakeholders');
  const right = standard(page.lines.slice(tableEnd, referenceEnd), page.number);
  const suffix = arrow === -1 ? '' : standard(page.lines.slice(arrow), page.number);
  return `${prefix}<div class="q3-layout"><div class="stakeholder-panel">${left}</div><aside class="activity-reference">${right}</aside></div>${suffix}`;
}

function q4(page) {
  const itemStarts = page.lines.map((line, i) => /^\(\d+\) /.test(line.text) ? i : -1).filter(i => i >= 0);
  const suffixIndex = page.lines.findIndex(line => line.text.startsWith('If you use any approaches'));
  const end = suffixIndex === -1 ? page.lines.length : suffixIndex;
  const prefix = page.lines.slice(0, itemStarts[0]);
  let header = '';
  let introduction = '';
  if (prefix.length) {
    introduction = standard(prefix.slice(0, 1), page.number);
    header = `<thead><tr><th>${element(prefix[1], 'p')}</th><th>${element(prefix[2], 'p')}</th></tr></thead>`;
  }
  const rows = itemStarts.map((start, index) => {
    const itemEnd = index + 1 < itemStarts.length ? itemStarts[index + 1] : end;
    const group = page.lines.slice(start, itemEnd);
    if (group.length !== 7) throw new Error(`Expected seven lines for Q4 item at ${group[0].id}, got ${group.length}`);
    return `<tr><td class="item-label">${element(group[0])}</td><td class="impact-responses">${element(group[1], 'p', 'implementation')}${element(group[2], 'p', 'impact-label')}${group.slice(3).map(l => element(l, 'p', 'option')).join('')}</td></tr>`;
  }).join('');
  return `${introduction}<table class="q4"><colgroup><col style="width:37%"><col style="width:63%"></colgroup>${header}<tbody>${rows}</tbody></table>${suffixIndex === -1 ? '' : standard(page.lines.slice(suffixIndex), page.number)}`;
}

function q5(page) {
  const suffixIndex = page.lines.findIndex(line => line.text.startsWith('For the approaches described above'));
  const end = suffixIndex === -1 ? page.lines.length : suffixIndex;
  const itemStarts = page.lines.slice(0, end).map((line, i) => /^\(\d+\) /.test(line.text) ? i : -1).filter(i => i >= 0);
  const prefix = page.lines.slice(0, itemStarts[0]);
  const introduction = prefix.length ? standard(prefix.slice(0, 2), page.number) : '';
  const header = prefix.length
    ? `<thead><tr><th>${element(prefix[2], 'p')}</th><th>${element(prefix[3], 'p')}</th></tr></thead>` : '';
  const rows = itemStarts.map((start, index) => {
    const itemEnd = index + 1 < itemStarts.length ? itemStarts[index + 1] : end;
    const group = page.lines.slice(start, itemEnd);
    const descriptions = group.filter(l => !l.text.startsWith('[ ]'));
    const options = group.filter(l => l.text.startsWith('[ ]'));
    if (options.length !== 3) throw new Error(`Expected three Q5 options at source line ${group[0].id}`);
    return `<tr><td class="item-label">${descriptions.map(l => element(l, 'p', l.text.startsWith('Note:') ? 'item-note' : '')).join('')}</td><td>${options.map(l => element(l, 'p', 'option')).join('')}</td></tr>`;
  }).join('');
  return `${introduction}<table class="q5"><colgroup><col style="width:65%"><col style="width:35%"></colgroup>${header}<tbody>${rows}</tbody></table>${suffixIndex === -1 ? '' : standard(page.lines.slice(suffixIndex), page.number)}`;
}

const renderedPages = pages.map(page => {
  let html;
  if (page.number === 5 || page.number === 6) html = q3(page);
  else if (page.number === 7 || page.number === 8) html = q4(page);
  else if (page.number === 9 || page.number === 10) html = q5(page);
  else if (page.number === 1) html = element(page.lines[0], 'h1') + standard(page.lines.slice(1), 1);
  else html = standard(page.lines, page.number);
  return `<section class="sheet page-${page.number}" data-page="${page.number}"><main class="page-content">${html}</main><footer>${page.number}</footer></section>`;
}).join('\n');

const allLines = pages.flatMap(p => p.lines);
const badUsage = allLines.filter(l => used.get(l.id) !== 1);
if (badUsage.length) throw new Error('Missing or duplicated source lines: ' + JSON.stringify(badUsage));
const checkboxCount = (source.match(/\[(?: |x)\]/g) || []).length;
const checkedCount = (source.match(/\[x\]/g) || []).length;
if (checkboxCount !== 263 || checkedCount !== 12) throw new Error(`Unexpected source checkbox counts: ${checkboxCount}/${checkedCount}`);

const styles = `
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #e6e6e6; }
body { color: #111; font-family: Arial, "Yu Gothic", sans-serif; font-size: 10.5pt; line-height: 1.22; }
.sheet { width: 210mm; height: 297mm; padding: 12mm 11mm 15mm; margin: 5mm auto; position: relative; background: white; break-after: page; break-inside: avoid; }
.page-content { height: 270mm; width: 188mm; }
footer { position: absolute; bottom: 6.5mm; left: 0; right: 0; text-align: center; font-size: 10pt; line-height: 1; }
h1 { font-size: 16pt; line-height: 1.24; margin: 0 0 7mm; font-weight: 700; }
h2 { font-size: 12pt; line-height: 1.2; margin: 4mm 0 3mm; padding: 1.8mm 2mm; background: #eeeeee; border-left: 1mm solid #333; }
h2:first-child { margin-top: 0; }
h3 { font-size: 10.8pt; line-height: 1.2; margin: 3mm 0 2mm; }
p { margin: 0 0 2.6mm; }
.question { font-weight: 600; margin-bottom: 3mm; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 10.25pt; line-height: 1.17; margin: 2mm 0 3mm; }
th, td { border: 0.25mm solid #444; padding: 2.1mm 2.2mm; vertical-align: top; overflow-wrap: normal; }
th { font-weight: 600; background: #f3f3f3; text-align: left; }
th p, td p:last-child { margin-bottom: 0; }
.response-cell { text-align: center; vertical-align: middle; }
.checkbox { font-size: 0; display: inline-block; width: 2.7mm; height: 2.7mm; border: 0.28mm solid #111; position: relative; margin-right: 1mm; vertical-align: -0.15mm; flex-shrink: 0; }
.checkbox.checked::after { content: "✓"; font: bold 12pt/2.7mm "Segoe UI Symbol", Arial, sans-serif; position: absolute; left: -0.2mm; top: -0.45mm; color: #111; }
.option { padding-left: 4.2mm; text-indent: -4.2mm; margin-bottom: 1.7mm; }
.option .checkbox { text-indent: 0; }
.writing-area { border: 0.25mm solid #777; min-height: 27mm; margin: 1.5mm 0 4mm; padding: 4mm 3mm; display: flex; flex-direction: column; justify-content: space-between; }
.writing-line { font-family: Arial, sans-serif; font-size: 10pt; line-height: 1; margin: 0; color: #777; letter-spacing: -0.01mm; white-space: nowrap; }
.guidance-title { font-size: 14pt; margin-bottom: 5mm; }
.rules { margin-bottom: 3mm; }
.rules th { text-align: center; font-size: 10pt; }
.rules th:first-child { text-align: left; }
.rules td { padding-top: 2.15mm; padding-bottom: 2.15mm; }
.rules td:not(:first-child) .checkbox { margin: 0; }
.conservation th { font-size: 10pt; }
.conservation td { padding-top: 2.8mm; padding-bottom: 2.8mm; }
.conservation .response-cell { white-space: nowrap; padding-left: 1mm; padding-right: 1mm; }
.page-1 { padding: 16mm 14mm 15mm; }
.page-1 .page-content { width: 182mm; height: 266mm; }
.page-1 h1 { text-align: center; font-size: 16pt; }
.page-1 p { margin-bottom: 4mm; line-height: 1.3; }
.page-1 .survey-details { margin-top: 6mm; }
.page-1 .contact-heading { font-weight: 600; margin-top: 3mm; margin-bottom: 2mm; }
.page-1 [data-line="24"], .page-1 [data-line="25"], .page-1 [data-line="30"], .page-1 [data-line="31"], .page-1 [data-line="34"] { margin-bottom: 1.5mm; }
.page-2 .writing-area, .page-3 .writing-area { min-height: 28mm; }
.page-5, .page-6 { font-size: 10.25pt; line-height: 1.17; }
.page-5 p, .page-6 p { margin-bottom: 2mm; }
.q3-layout { display: grid; grid-template-columns: 1.06fr 1fr; gap: 4mm; align-items: stretch; margin-top: 2mm; }
.stakeholder-panel table { height: 100%; margin: 0; font-size: 10pt; }
.stakeholders th, .stakeholders td { padding: 2.5mm 2mm; }
.stakeholders td:last-child { font-size: 10.5pt; min-height: 17mm; }
.activity-reference { border: 0.25mm solid #555; padding: 2.3mm 2.5mm; font-size: 10pt; line-height: 1.14; }
.activity-reference h3 { font-size: 10pt; margin: 0 0 2.2mm; }
.activity-reference p { margin-bottom: 2mm; }
.down-arrow { font-size: 12pt; text-align: center; margin: 1.2mm 0 0; }
.example-explanation { border: 0.25mm solid #666; padding: 2mm; margin-top: 1.5mm; }
.q4 { font-size: 10.25pt; line-height: 1.14; }
.q4 th { font-size: 10.25pt; }
.q4 .item-label { font-size: 10.5pt; }
.q4 td { padding: 2mm 2.5mm; }
.q4 .implementation { border-bottom: 0.2mm solid #777; padding-bottom: 1.5mm; margin-bottom: 1.5mm; font-weight: 600; }
.q4 .impact-label { margin-bottom: 1.4mm; }
.q4 .option { margin-bottom: 1.4mm; }
.page-8 .writing-area { min-height: 24mm; }
.q5 { font-size: 10.25pt; line-height: 1.14; }
.q5 th { font-size: 10.25pt; }
.q5 td { padding: 1.9mm 2.2mm; }
.q5 .option { margin-bottom: 2mm; }
.q5 .item-note { margin-top: 2mm; }
.page-10 .writing-area { min-height: 25mm; }
.page-10 .option { margin-bottom: 1.9mm; }
.page-11 { font-size: 10pt; line-height: 1.15; }
.page-11 p { margin-bottom: 2mm; }
.page-11 h2 { font-size: 11.5pt; margin-top: 3mm; margin-bottom: 2.5mm; }
.page-11 .writing-area { min-height: 25mm; margin-bottom: 3mm; }
.page-11 .option { margin-bottom: 1.5mm; }
.complaints { font-size: 10pt; line-height: 1.14; margin: 1.5mm 0 3mm; }
.complaints th, .complaints td { padding: 1.5mm 2mm; }
.page-12 .option { margin-bottom: 3mm; }
.page-12 .writing-area { min-height: 72mm; }
.closing { font-weight: 600; text-align: center; margin-top: 5mm; }
#layout-audit { display: none; }
@media print {
  html, body { background: white; }
  .sheet { margin: 0; box-shadow: none; }
  .sheet:last-of-type { break-after: auto; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
`;

const auditScript = `
addEventListener('load', async () => {
  await document.fonts.ready;
  const report = Array.from(document.querySelectorAll('.sheet')).map(sheet => {
    const content = sheet.querySelector('.page-content');
    const contentRect = content.getBoundingClientRect();
    const descendants = Array.from(content.querySelectorAll('*'));
    const maxBottom = Math.max(contentRect.top, ...descendants.map(e => e.getBoundingClientRect().bottom));
    const maxRight = Math.max(contentRect.left, ...descendants.map(e => e.getBoundingClientRect().right));
    return {page:Number(sheet.dataset.page), width:contentRect.width, height:contentRect.height,
      usedHeight:Math.round((maxBottom-contentRect.top)*100)/100,
      verticalOverflow:Math.max(0,Math.round((maxBottom-contentRect.bottom)*100)/100),
      horizontalOverflow:Math.max(0,Math.round((maxRight-contentRect.right)*100)/100),
      checkboxes:content.querySelectorAll('.checkbox').length,
      checked:content.querySelectorAll('.checked').length};
  });
  document.getElementById('layout-audit').textContent=JSON.stringify(report);
  document.body.dataset.layoutReady='true';
});`;
const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Questionnaire for park managers</title><style>${styles}</style></head><body>${renderedPages}<output id="layout-audit"></output><script>${auditScript}</script></body></html>`;
fs.writeFileSync(outputPath, html, 'utf8');
fs.writeFileSync(path.join(work, 'questionnaire_source_audit.json'), JSON.stringify({
  source:sourcePath, sourceSHA256:crypto.createHash('sha256').update(source).digest('hex'),
  output:outputPath, pages:pages.length, sourceLines:allLines.length,
  everySourceLineRenderedExactlyOnce:true, checkboxes:checkboxCount, checkedExamples:checkedCount,
  pageCheckboxes:pages.map(p => ({page:p.number,
    checkboxes:(p.lines.map(l=>l.text).join('\n').match(/\[(?: |x)\]/g)||[]).length,
    checked:(p.lines.map(l=>l.text).join('\n').match(/\[x\]/g)||[]).length}))
}, null, 2), 'utf8');
console.log(JSON.stringify({output:outputPath,pages:pages.length,checkboxes:checkboxCount,checkedExamples:checkedCount}));
