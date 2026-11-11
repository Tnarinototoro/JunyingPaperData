param([string]$ImagePath)

# Read-only visual crops of the supplied anonymous Q4 table; no OCR or scoring.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$paperQ4Path=(Resolve-Path -LiteralPath $ImagePath).Path
$paperQ4Image=[System.Drawing.Image]::FromFile($paperQ4Path)
$paperQ4CropRoot=Join-Path (Get-Location).Path '.paper16_work\q4_visual'
New-Item -ItemType Directory -Path $paperQ4CropRoot -Force | Out-Null
try {
    $paperQ4Regions=@(
        @{Name='left_upper';X=0;Y=190;Width=860;Height=470},
        @{Name='left_lower';X=0;Y=650;Width=860;Height=475},
        @{Name='ratings_upper';X=850;Y=190;Width=1150;Height=470},
        @{Name='ratings_lower';X=850;Y=650;Width=1150;Height=475}
    )
    foreach($paperQ4Region in $paperQ4Regions){
        $paperQ4Bounds=[System.Drawing.Rectangle]::new($paperQ4Region.X,$paperQ4Region.Y,$paperQ4Region.Width,$paperQ4Region.Height)
        $paperQ4Crop=[System.Drawing.Bitmap]::new($paperQ4Region.Width*2,$paperQ4Region.Height*2)
        $paperQ4Graphics=[System.Drawing.Graphics]::FromImage($paperQ4Crop)
        try{
            $paperQ4Graphics.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
            $paperQ4Graphics.DrawImage($paperQ4Image,[System.Drawing.Rectangle]::new(0,0,$paperQ4Crop.Width,$paperQ4Crop.Height),$paperQ4Bounds,[System.Drawing.GraphicsUnit]::Pixel)
            $paperQ4CropPath=Join-Path $paperQ4CropRoot ($paperQ4Region.Name+'.png')
            $paperQ4Crop.Save($paperQ4CropPath,[System.Drawing.Imaging.ImageFormat]::Png)
            Write-Output $paperQ4CropPath
        }finally{
            $paperQ4Graphics.Dispose()
            $paperQ4Crop.Dispose()
        }
    }
}finally{
    $paperQ4Image.Dispose()
}
