param([switch]$AuditOnly)
$ErrorActionPreference = 'Stop'
$questionnaireWork = $PSScriptRoot
$questionnaireHtml = Join-Path $questionnaireWork 'questionnaire_print.html'
$questionnairePdf = Join-Path (Split-Path $questionnaireWork -Parent) '英语 アンケート.pdf'
$browserPath = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$browserProfile = Join-Path $questionnaireWork 'chrome_questionnaire_psprint'
$browserStdout = Join-Path $questionnaireWork 'questionnaire_browser_dom.txt'
$browserStderr = Join-Path $questionnaireWork 'questionnaire_browser_stderr.txt'
$htmlUri = ([uri]$questionnaireHtml).AbsoluteUri
$commonArgs = @('--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions','--disable-background-networking', ('--user-data-dir="' + $browserProfile + '"'),'--virtual-time-budget=2500')
$auditProcess = Start-Process -FilePath $browserPath -ArgumentList ($commonArgs + @('--dump-dom',$htmlUri)) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $browserStdout -RedirectStandardError $browserStderr
$browserDom = Get-Content -LiteralPath $browserStdout -Raw -Encoding UTF8
$auditMatch = [regex]::Match($browserDom, '<output id="layout-audit">([\s\S]*?)</output>')
if (-not $auditMatch.Success) {
  Get-Content -LiteralPath $browserStderr -Encoding UTF8 -TotalCount 30
  throw 'Browser did not return the layout audit.'
}
$layoutReport = $auditMatch.Groups[1].Value | ConvertFrom-Json
$layoutReport | ConvertTo-Json -Depth 6
if ($layoutReport.Count -ne 12 -or @($layoutReport | Where-Object { $_.verticalOverflow -gt 0.5 -or $_.horizontalOverflow -gt 0.5 }).Count -gt 0) { throw 'Layout overflow: adjust HTML before printing.' }
if (-not $AuditOnly) {
  $pdfProcess = Start-Process -FilePath $browserPath -ArgumentList ($commonArgs + @('--no-pdf-header-footer',('--print-to-pdf="' + $questionnairePdf + '"'),$htmlUri)) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $questionnaireWork 'questionnaire_print_stdout.txt') -RedirectStandardError (Join-Path $questionnaireWork 'questionnaire_print_stderr.txt')
  Get-Item -LiteralPath $questionnairePdf | Select-Object FullName,Length
}
