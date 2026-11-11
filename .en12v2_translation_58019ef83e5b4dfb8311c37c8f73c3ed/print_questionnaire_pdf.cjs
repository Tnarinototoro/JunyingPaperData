const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { spawnSync } = require('node:child_process');

const browser = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const html = path.join(__dirname, 'questionnaire_print.html');
const pdf = path.resolve(__dirname, '..', '英语 アンケート.pdf');
const auditOnly = process.argv.includes('--audit-only');
const baseArgs = [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--disable-background-networking',
  `--user-data-dir=${path.join(__dirname, 'chrome_questionnaire_print')}`,
  '--virtual-time-budget=2500'
];
const audit = spawnSync(browser, [...baseArgs, '--dump-dom', pathToFileURL(html).href], {
  encoding:'utf8', timeout:30000, maxBuffer:8*1024*1024, windowsHide:true
});
if (audit.error) throw audit.error;
if (audit.status !== 0) throw new Error('Browser audit failed: ' + audit.stderr);
const match = /<output id="layout-audit">([\s\S]*?)<\/output>/.exec(audit.stdout);
if (!match) throw new Error('Layout audit missing: ' + audit.stderr);
const report = JSON.parse(match[1]);
fs.writeFileSync(path.join(__dirname, 'questionnaire_layout_audit.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
if (report.length !== 12 || report.some(p => p.verticalOverflow > 0.5 || p.horizontalOverflow > 0.5)) {
  throw new Error('Layout overflows; adjust layout before printing.');
}
if (!auditOnly) {
  const printed = spawnSync(browser, [...baseArgs, '--no-pdf-header-footer', `--print-to-pdf=${pdf}`, pathToFileURL(html).href], {
    encoding:'utf8', timeout:30000, maxBuffer:4*1024*1024, windowsHide:true
  });
  if (printed.error) throw printed.error;
  if (printed.status !== 0 || !fs.existsSync(pdf)) throw new Error('Printing failed: ' + printed.stderr);
  console.log(JSON.stringify({pdf,bytes:fs.statSync(pdf).size}));
}
