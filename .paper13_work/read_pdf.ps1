param(
    [Parameter(Mandatory=$true)][string]$InputPdf,
    [Parameter(Mandatory=$true)][string]$OutputName,
    [string]$OcrLanguage='zh-Hans-CN',
    [int]$RenderWidth=2000
)

# Local PDF rendering and OCR only. Source PDFs are never modified.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null
$pdfActionMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and -not $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' } | Select-Object -First 1
$pdfAwaitMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Wait-PaperPdfOperation($operation,[Type]$resultType) {
    $pdfTask=$pdfAwaitMethod.MakeGenericMethod($resultType).Invoke($null,@($operation))
    $pdfTask.Wait()
    $pdfTask.Result
}
$pdfInputPath=(Resolve-Path -LiteralPath $InputPdf).Path
$pdfOutputRoot=Join-Path $PSScriptRoot $OutputName
New-Item -ItemType Directory -Path $pdfOutputRoot -Force | Out-Null
$pdfInputFile=Wait-PaperPdfOperation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfInputPath)) ([Windows.Storage.StorageFile])
$pdfDocument=Wait-PaperPdfOperation ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($pdfInputFile)) ([Windows.Data.Pdf.PdfDocument])
$pdfOcrEngine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language $OcrLanguage))
if($null -eq $pdfOcrEngine){
    $pdfOcrEngine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if($null -eq $pdfOcrEngine){throw "No local OCR engine available"}
    Write-Output "Requested OCR language unavailable; using local profile OCR with visual checks."
}
$pdfPageOutputs=@()
$pdfTextParts=New-Object System.Collections.Generic.List[string]
for($pdfPageIndex=0;$pdfPageIndex -lt $pdfDocument.PageCount;$pdfPageIndex++){
    $pdfPage=$pdfDocument.GetPage([uint32]$pdfPageIndex)
    $pdfRenderStream=New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $pdfRenderOptions=New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $pdfRenderOptions.DestinationWidth=[uint32]$RenderWidth
    $pdfRenderOptions.DestinationHeight=[uint32][Math]::Round($pdfPage.Size.Height*$RenderWidth/$pdfPage.Size.Width)
    $pdfRenderTask=$pdfActionMethod.Invoke($null,@($pdfPage.RenderToStreamAsync($pdfRenderStream,$pdfRenderOptions)))
    $pdfRenderTask.Wait()
    $pdfRenderStream.Seek(0)
    $pdfOutputPath=Join-Path $pdfOutputRoot ('page_'+($pdfPageIndex+1)+'.png')
    $pdfReadStream=[System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($pdfRenderStream)
    $pdfOutputStream=[System.IO.File]::Open($pdfOutputPath,[System.IO.FileMode]::Create)
    $pdfReadStream.CopyTo($pdfOutputStream)
    $pdfOutputStream.Dispose()
    $pdfRenderStream.Seek(0)
    $pdfBitmapDecoder=Wait-PaperPdfOperation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($pdfRenderStream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $pdfBitmap=Wait-PaperPdfOperation ($pdfBitmapDecoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $pdfOcrResult=Wait-PaperPdfOperation ($pdfOcrEngine.RecognizeAsync($pdfBitmap)) ([Windows.Media.Ocr.OcrResult])
    $pdfLines=@($pdfOcrResult.Lines | ForEach-Object {
        $pdfFirstWord=$_.Words | Select-Object -First 1
        [pscustomobject]@{Text=$_.Text;X=$pdfFirstWord.BoundingRect.X;Y=$pdfFirstWord.BoundingRect.Y}
    })
    $pdfPageText=($pdfLines | ForEach-Object {$_.Text}) -join "`n"
    $pdfPageOutputs += [pscustomobject]@{Page=$pdfPageIndex+1;ImagePath=$pdfOutputPath;Text=$pdfPageText;Lines=$pdfLines}
    $pdfTextParts.Add("@@ PAGE $($pdfPageIndex+1) / $($pdfDocument.PageCount) @@`n$pdfPageText")
    [System.IO.File]::WriteAllText((Join-Path $pdfOutputRoot ('page_'+($pdfPageIndex+1)+'.txt')),$pdfPageText,[System.Text.UTF8Encoding]::new($false))
    Write-Output "Rendered/OCR page $($pdfPageIndex+1)/$($pdfDocument.PageCount)"
    $pdfBitmap.Dispose()
    $pdfRenderStream.Dispose()
    $pdfPage.Dispose()
}
[System.IO.File]::WriteAllText((Join-Path $pdfOutputRoot 'ocr.txt'),($pdfTextParts -join "`n`n"),[System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $pdfOutputRoot 'pages.json'),($pdfPageOutputs | ConvertTo-Json -Depth 6),[System.Text.UTF8Encoding]::new($false))
[pscustomobject]@{Source=$pdfInputPath;PageCount=$pdfDocument.PageCount;TextPath=(Join-Path $pdfOutputRoot 'ocr.txt');OutputFolder=$pdfOutputRoot} | ConvertTo-Json
