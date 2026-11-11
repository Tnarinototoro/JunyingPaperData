param(
    [Parameter(Mandatory=$true)][string]$InputPdf,
    [string]$OcrLanguage='en',
    [switch]$PageCountOnly
)

$ErrorActionPreference = 'Stop'

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
function Wait-PdfReadOperation($operation,[Type]$resultType) {
    $pdfTask=$pdfAwaitMethod.MakeGenericMethod($resultType).Invoke($null,@($operation))
    $pdfTask.Wait()
    $pdfTask.Result
}
$pdfInputPath=(Resolve-Path -LiteralPath $InputPdf).Path
$pdfInputFile=Wait-PdfReadOperation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfInputPath)) ([Windows.Storage.StorageFile])
$pdfDocument=Wait-PdfReadOperation ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($pdfInputFile)) ([Windows.Data.Pdf.PdfDocument])
if($PageCountOnly){ [pscustomobject]@{PageCount=$pdfDocument.PageCount} | ConvertTo-Json; exit }
$pdfReadTemp=Join-Path ([System.IO.Path]::GetTempPath()) ('paper_en12_english_review_'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $pdfReadTemp | Out-Null
$pdfOcrEngine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language $OcrLanguage))
$pdfPageOutputs=@()
for($pdfPageIndex=0;$pdfPageIndex -lt $pdfDocument.PageCount;$pdfPageIndex++){
    $pdfPage=$pdfDocument.GetPage([uint32]$pdfPageIndex)
    $pdfRenderStream=New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $pdfRenderOptions=New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $pdfRenderOptions.DestinationWidth=[uint32]1800
    $pdfRenderOptions.DestinationHeight=[uint32][Math]::Round($pdfPage.Size.Height*1800/$pdfPage.Size.Width)
    $pdfRenderTask=$pdfActionMethod.Invoke($null,@($pdfPage.RenderToStreamAsync($pdfRenderStream,$pdfRenderOptions)))
    $pdfRenderTask.Wait()
    $pdfRenderStream.Seek(0)
    $pdfOutputPath=Join-Path $pdfReadTemp ('en_page_'+($pdfPageIndex+1)+'.png')
    $pdfReadStream=[System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($pdfRenderStream)
    $pdfOutputStream=[System.IO.File]::Open($pdfOutputPath,[System.IO.FileMode]::CreateNew)
    $pdfReadStream.CopyTo($pdfOutputStream)
    $pdfOutputStream.Dispose()
    $pdfRenderStream.Seek(0)
    $pdfBitmapDecoder=Wait-PdfReadOperation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($pdfRenderStream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $pdfBitmap=Wait-PdfReadOperation ($pdfBitmapDecoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $pdfOcrResult=Wait-PdfReadOperation ($pdfOcrEngine.RecognizeAsync($pdfBitmap)) ([Windows.Media.Ocr.OcrResult])
    $pdfPageOutputs += [pscustomobject]@{Page=$pdfPageIndex+1;ImagePath=$pdfOutputPath;Text=$pdfOcrResult.Text}
    $pdfBitmap.Dispose()
    $pdfPage.Dispose()
}
$pdfPageOutputs | ConvertTo-Json -Depth 5

