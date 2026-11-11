"""Render exact relative outlines using only the standard library.

Generated PNGs are private diagnostics. No names, addresses or absolute
coordinates are included. Does not modify source GIS or analysis inputs.
"""
import json
import math
from pathlib import Path
import struct
import zlib

FONT_ROWS = {
 "A":"01110 10001 10001 11111 10001 10001 10001", "B":"11110 10001 10001 11110 10001 10001 11110",
 "C":"01111 10000 10000 10000 10000 10000 01111", "D":"11110 10001 10001 10001 10001 10001 11110",
 "E":"11111 10000 10000 11110 10000 10000 11111", "F":"11111 10000 10000 11110 10000 10000 10000",
 "G":"01111 10000 10000 10111 10001 10001 01111", "H":"10001 10001 10001 11111 10001 10001 10001",
 "I":"11111 00100 00100 00100 00100 00100 11111", "J":"00111 00010 00010 00010 10010 10010 01100",
 "K":"10001 10010 10100 11000 10100 10010 10001", "L":"10000 10000 10000 10000 10000 10000 11111",
 "M":"10001 11011 10101 10101 10001 10001 10001", "N":"10001 11001 10101 10011 10001 10001 10001",
 "O":"01110 10001 10001 10001 10001 10001 10001 01110", "P":"11110 10001 10001 11110 10000 10000 10000",
 "Q":"01110 10001 10001 10001 10101 10010 01101", "R":"11110 10001 10001 11110 10100 10010 10001",
 "S":"01111 10000 10000 01110 00001 00001 11110", "T":"11111 00100 00100 00100 00100 00100 00100",
 "U":"10001 10001 10001 10001 10001 10001 01110", "V":"10001 10001 10001 10001 10001 01010 00100",
 "W":"10001 10001 10001 10101 10101 11011 10001", "X":"10001 10001 01010 00100 01010 10001 10001",
 "Y":"10001 10001 01010 00100 00100 00100 00100", "Z":"11111 00001 00010 00100 01000 10000 11111",
 "0":"01110 10001 10011 10101 11001 10001 01110", "1":"00100 01100 00100 00100 00100 00100 01110",
 "2":"01110 10001 00001 00010 00100 01000 11111", "3":"11110 00001 00001 01110 00001 00001 11110",
 "4":"00010 00110 01010 10010 11111 00010 00010", "5":"11111 10000 10000 11110 00001 00001 11110",
 "6":"01110 10000 10000 11110 10001 10001 01110", "7":"11111 00001 00010 00100 01000 01000 01000",
 "8":"01110 10001 10001 01110 10001 10001 01110", "9":"01110 10001 10001 01111 00001 00001 01110",
 ".":"00000 00000 00000 00000 00000 00110 00110", ":":"00000 00110 00110 00000 00110 00110 00000",
 "-":"00000 00000 00000 11111 00000 00000 00000", "/":"00001 00010 00010 00100 01000 01000 10000",
 " ":"00000 00000 00000 00000 00000 00000 00000", "|":"00100 00100 00100 00100 00100 00100 00100",
}
FONT = {key:[int(bits,2) for bits in value.split()] for key,value in FONT_ROWS.items()}
W,H = 1200,1000


def rect(pixels,x0,y0,x1,y1,color):
    lo,hi=max(0,int(x0)),min(W-1,int(x1))
    if lo>hi:return
    word=bytes(color)*(hi-lo+1)
    for y in range(max(0,int(y0)),min(H-1,int(y1))+1):
        start=(y*W+lo)*3
        pixels[start:start+len(word)]=word


def line(pixels,a,b,color,width=2):
    x0,y0=map(round,a);x1,y1=map(round,b)
    dx,dy=abs(x1-x0),-abs(y1-y0)
    sx,sy=1 if x0<x1 else -1,1 if y0<y1 else -1
    err=dx+dy
    while True:
        rect(pixels,x0-width,y0-width,x0+width,y0+width,color)
        if x0==x1 and y0==y1:break
        twice=2*err
        if twice>=dy:err+=dy;x0+=sx
        if twice<=dx:err+=dx;y0+=sy


def text(pixels,x,y,value,scale=2,color=(37,49,63)):
    for char in value.upper():
        for row,bits in enumerate(FONT.get(char,FONT[" "])):
            for col in range(5):
                if bits&(1<<(4-col)):
                    rect(pixels,x+col*scale,y+row*scale,x+(col+1)*scale-1,y+(row+1)*scale-1,color)
        x+=6*scale


def fill_polygon(pixels,points,color):
    for row in range(max(0,math.floor(min(y for _,y in points))),min(H-1,math.ceil(max(y for _,y in points)))+1):
        y=row+0.5
        crossings=[]
        for a,b in zip(points,points[1:]+points[:1]):
            if (a[1]>y)!=(b[1]>y):
                crossings.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
        crossings.sort()
        for lo,hi in zip(crossings[::2],crossings[1::2]):
            rect(pixels,math.ceil(lo),row,math.floor(hi),row,color)


def png_bytes(pixels):
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
    rows=b"".join(b"\x00"+pixels[y*W*3:(y+1)*W*3] for y in range(H))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">2I5B",W,H,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(rows,9))+chunk(b"IEND",b"")


def render(row,path):
    pixels=bytearray(bytes((255,255,255))*W*H)
    width,height=row["local_utm_east_west_extent_m"],row["local_utm_north_south_extent_m"]
    scale=min(1080/width,680/height)
    ox=60+(1080-width*scale)/2
    oy=160+(680-height*scale)/2
    points=[(ox+x*scale,oy+(height-y)*scale) for x,y in row["relative_plot_vertices_m"]]
    fill_polygon(pixels,points,(225,242,230))
    for a,b in zip(points,points[1:]+points[:1]):line(pixels,a,b,(36,102,156),2)
    for x,y in points[:-1]:rect(pixels,x-3,y-3,x+3,y+3,(213,112,45))
    text(pixels,40,24,f"P{row['ParkID']:02d} - SUPPLIED POLYGON ONLY - PRIVATE QC",3)
    text(pixels,40,70,f"AREA {row['equal_area_native_projection_area_ha']:.2f} HA | E-W {width:.0f} M | N-S {height:.0f} M",2)
    text(pixels,40,101,f"ONE CLOSED EXTERIOR RING | NO SUB-AREA BOUNDARIES | EPSG {row['local_utm_epsg_for_relative_outline']}",2)
    line(pixels,(1100,180),(1100,135),(37,49,63),2)
    line(pixels,(1100,135),(1090,151),(37,49,63),2)
    line(pixels,(1100,135),(1110,151),(37,49,63),2)
    text(pixels,1072,193,"GRID N",2)
    target=max(width,height)/5
    distance=max(number for number in (1,2,5,10,20,50,100,200,500,1000,2000,5000,10000) if number<=target)
    bar=distance*scale
    line(pixels,(50,875),(50+bar,875),(37,49,63),2)
    line(pixels,(50,868),(50,882),(37,49,63),2)
    line(pixels,(50+bar,868),(50+bar,882),(37,49,63),2)
    text(pixels,50,896,f"{distance} M",2)
    text(pixels,40,938,"VERTICES SHOWN - RELATIVE ORIGIN - NOT AN OFFICIAL PARK OR SECTION MAP",2)
    path.write_bytes(png_bytes(pixels))


def main():
    work=Path(__file__).resolve().parent
    report=json.loads((work/"four_supplied_geometry_extent_qc.json").read_text(encoding="utf-8"))
    out=work/"private_four_outlines"
    out.mkdir(exist_ok=True)
    files=[]
    for row in report["records"]:
        name=f"P{row['ParkID']:02d}_supplied_outline_PRIVATE.png"
        render(row,out/name)
        files.append("private_four_outlines/"+name)
    print(json.dumps({"rendered_private_anonymous_outlines":len(files),"files":files,"source_gis_modified":False},ensure_ascii=True))


if __name__=="__main__":main()
