"""Independent CRS/mask/aggregation QC; no input writes or location output.

Uses a sixth-order Krueger transverse-Mercator implementation, bisection
Albers inverse, nonzero winding numbers, and direct Float32 pixel reads.
Only the audited TIFF header decoder and original SHP reader are reused.
"""
import json
import math
import mmap
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

from audit_rasters_stdlib import read_ifd, first, geo_keys
from audit_vectors_std import read_shp, ring_edges, point_segment_distance
import geo_math_stdlib as primary_geo

A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
E = math.sqrt(E2)
N = F / (2 - F)
ABAR = A / (1 + N) * (1 + N**2/4 + N**4/64 + N**6/256)
ALPHA = [N/2 - 2*N**2/3 + 5*N**3/16 + 41*N**4/180 - 127*N**5/288 + 7891*N**6/37800,
         13*N**2/48 - 3*N**3/5 + 557*N**4/1440 + 281*N**5/630 - 1983433*N**6/1935360,
         61*N**3/240 - 103*N**4/140 + 15061*N**5/26880 + 167603*N**6/181440,
         49561*N**4/161280 - 179*N**5/168 + 6601661*N**6/7257600,
         34729*N**5/80640 - 3418889*N**6/1995840,
         212378941*N**6/319334400]
BETA = [N/2 - 2*N**2/3 + 37*N**3/96 - N**4/360 - 81*N**5/512 + 96199*N**6/604800,
        N**2/48 + N**3/15 - 437*N**4/1440 + 46*N**5/105 - 1118711*N**6/3870720,
        17*N**3/480 - 37*N**4/840 - 209*N**5/4480 + 5569*N**6/90720,
        4397*N**4/161280 - 11*N**5/504 - 830251*N**6/7257600,
        4583*N**5/161280 - 108847*N**6/3991680,
        20648693*N**6/638668800]


def q(phi):
    s = math.sin(phi)
    return (1-E2) * (s/(1-E2*s*s) + math.atanh(E*s)/E)


def m(phi):
    return math.cos(phi) / math.sqrt(1-E2*math.sin(phi)**2)


P1, P2, P0, L0 = map(math.radians, (15, 65, 30, 95))
AN = (m(P1)**2-m(P2)**2)/(q(P2)-q(P1))
AC = m(P1)**2+AN*q(P1)
RHO0 = A * math.sqrt(AC-AN*q(P0))/AN


def inverse_albers(x, y):
    rho = math.hypot(x, RHO0-y)
    target = (AC-(rho*AN/A)**2)/AN
    lo, hi = -math.pi/2, math.pi/2
    for _ in range(60):
        mid = (lo+hi)/2
        if q(mid) < target:
            lo = mid
        else:
            hi = mid
    return math.degrees(L0+math.atan2(x, RHO0-y)/AN), math.degrees((lo+hi)/2)


def forward_albers(lon, lat):
    rho = A * math.sqrt(AC-AN*q(math.radians(lat)))/AN
    theta = AN*(math.radians(lon)-L0)
    return rho*math.sin(theta), RHO0-rho*math.cos(theta)


def tau_prime(phi):
    tau = math.tan(phi)
    sigma = math.sinh(E*math.atanh(E*tau/math.sqrt(1+tau*tau)))
    return tau*math.sqrt(1+sigma*sigma)-sigma*math.sqrt(1+tau*tau)


def forward_utm(lon, lat, epsg):
    delta = math.radians(lon-(6*(epsg-32600)-183))
    tp = tau_prime(math.radians(lat))
    xp = math.atan2(tp, math.cos(delta))
    ep = math.asinh(math.sin(delta)/math.sqrt(tp*tp+math.cos(delta)**2))
    xi = xp + math.fsum(coef*math.sin(2*j*xp)*math.cosh(2*j*ep) for j, coef in enumerate(ALPHA,1))
    eta = ep + math.fsum(coef*math.cos(2*j*xp)*math.sinh(2*j*ep) for j, coef in enumerate(ALPHA,1))
    return 500000+0.9996*ABAR*eta, 0.9996*ABAR*xi


def inverse_utm(x, y, epsg):
    xi, eta = y/(0.9996*ABAR), (x-500000)/(0.9996*ABAR)
    xp = xi - math.fsum(coef*math.sin(2*j*xi)*math.cosh(2*j*eta) for j, coef in enumerate(BETA,1))
    ep = eta - math.fsum(coef*math.cos(2*j*xi)*math.sinh(2*j*eta) for j, coef in enumerate(BETA,1))
    target = math.sin(xp)/math.sqrt(math.sinh(ep)**2+math.cos(xp)**2)
    lo, hi = -math.pi/2+1e-12, math.pi/2-1e-12
    for _ in range(60):
        mid = (lo+hi)/2
        if tau_prime(mid) < target:
            lo = mid
        else:
            hi = mid
    lon = math.degrees(math.atan2(math.sinh(ep),math.cos(xp)))+6*(epsg-32600)-183
    return lon, math.degrees((lo+hi)/2)


def winding_contains(point, vertices):
    px, py = point
    count = 0
    for (ax,ay),(bx,by) in ring_edges(vertices):
        direction = (bx-ax)*(py-ay)-(by-ay)*(px-ax)
        if ay <= py < by and direction > 0:
            count += 1
        elif by <= py < ay and direction < 0:
            count -= 1
    return count != 0


def summarize(values, counts):
    n = len(values)
    mean = math.fsum(values)/n if n else None
    return counts | {"valid_n":n,"mean":mean,"minimum":min(values) if n else None,
                     "maximum":max(values) if n else None,
                     "valid_fraction":n/counts["eligible_n"] if counts["eligible_n"] else None,
                     "sd_population":math.sqrt(math.fsum((v-mean)**2 for v in values)/n) if n else None}


def independent_case(park, buffer, source):
    path = Path("NDVI")/source["source_raster"]
    tags, container = read_ifd(path)
    assert container["byte_order"] == "<"
    assert first(tags,259)==1 and first(tags,258)==32 and first(tags,339)==3
    epsg = geo_keys(tags)["3072"]["value"]
    w,h = first(tags,256),first(tags,257)
    assert first(tags,278)==1 and geo_keys(tags).get("1025",{}).get("value",1)==1
    dx,dy = tags[33550][:2]
    tie = tags[33922]
    x0,y0 = tie[3]-tie[0]*dx, tie[4]+tie[1]*dy
    nodata = struct.unpack("<f",struct.pack("<f",float(tags[42113])))[0] if tags.get(42113) else None
    scale,offset = 1.0,0.0
    if tags.get(42112):
        for item in ET.fromstring(tags[42112]).iter():
            if item.attrib.get("role")=="scale": scale=float(item.text)
            if item.attrib.get("role")=="offset": offset=float(item.text)
    mapped=[]
    for a,b in zip(buffer,buffer[1:]):
        steps=max(1,math.ceil(math.dist(a,b)/50))
        for j in range(steps):
            t=j/steps
            mapped.append(forward_utm(*inverse_albers(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])),epsg))
    mapped.append(forward_utm(*inverse_albers(*buffer[-1]),epsg))
    c0=math.floor((min(p[0] for p in mapped)-x0)/dx)-3
    c1=math.ceil((max(p[0] for p in mapped)-x0)/dx)+3
    r0=math.floor((y0-max(p[1] for p in mapped))/dy)-3
    r1=math.ceil((y0-min(p[1] for p in mapped))/dy)+3
    counts={z:dict(eligible_n=0,nodata_n=0,outside_extent_n=0,out_of_range_n=0) for z in (1,2)}
    vals={1:[],2:[]}
    max_transform_delta=0.0
    with path.open("rb") as stream:
        with mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as pixels:
            for row in range(r0,r1+1):
                y=y0-(row+0.5)*dy
                for col in range(c0,c1+1):
                    x=x0+(col+0.5)*dx
                    point=forward_albers(*inverse_utm(x,y,epsg))
                    max_transform_delta=max(max_transform_delta,math.dist(point,primary_geo.utm_to_albers(x,y,epsg)))
                    if not winding_contains(point,buffer): continue
                    zone=1 if winding_contains(point,park) else 2
                    counts[zone]["eligible_n"]+=1
                    if not (0<=row<h and 0<=col<w):
                        counts[zone]["outside_extent_n"]+=1
                        continue
                    strip=tags[273][row]
                    raw=struct.unpack_from("<f",pixels,strip+col*4)[0] if strip or tags[279][row] else None
                    if raw is None or not math.isfinite(raw) or raw==nodata:
                        counts[zone]["nodata_n"]+=1
                        continue
                    value=raw*scale+offset
                    if not -1.000001<=value<=1.000001:
                        counts[zone]["out_of_range_n"]+=1
                    vals[zone].append(value)
    stats={"inside":summarize(vals[1],counts[1]),"outside":summarize(vals[2],counts[2])}
    delta={side:{key:stats[side][key]-source[side][key] for key in stats[side]
                 if isinstance(stats[side][key],(int,float)) and isinstance(source[side][key],(int,float))}
           for side in stats}
    return {"ParkID":source["ParkID"],"independent_stats":stats,"minus_primary":delta,
            "maximum_inverse_transform_difference_m":max_transform_delta,
            "all_count_and_stat_differences_zero":all(value==0 for side in delta.values() for value in side.values())}


def run():
    scan=json.loads(Path("NDVI_mean_work/regional_mean_source_scan.json").read_text(encoding="utf-8"))
    audit=json.loads(Path("NDVI_mean_work/audit_vector_topology.json").read_text(encoding="utf-8"))
    park_rows=read_shp(Path("NDVI/parks_metric.shp"),include_points=True)["feature_details"]
    buffer_parts=read_shp(Path("NDVI/100m_buffer.shp"),include_points=True)["feature_details"][0]["private_parts"]
    sources={row["ParkID"]:row["selected"] for row in scan["parks"]}
    pairing={row["park_id"]:row["covering_buffer_parts"][0]-1 for row in audit["matches"]}
    max_albers_delta=max_utm_delta=0.0
    checked_vertices=0
    for row in park_rows:
        source=sources[row["record"]]
        if source is None: continue
        for x,y in row["private_parts"][0]:
            ll=inverse_albers(x,y)
            max_albers_delta=max(max_albers_delta,math.dist((x,y),primary_geo.lonlat_to_albers(*ll)))
            max_utm_delta=max(max_utm_delta,math.dist(forward_utm(*ll,source["epsg"]),primary_geo.albers_to_utm(x,y,source["epsg"])))
            checked_vertices+=1
    cases=[]
    for park_id in (1,7,11,27):
        park=park_rows[park_id-1]["private_parts"][0]
        buffer=buffer_parts[pairing[park_id]]
        cases.append(independent_case(park,buffer,sources[park_id]))
    return {"methods":"Independent sixth-order Krueger UTM, bisection Albers inverse, nonzero winding masks, direct Float32 reads and fsum/n; reused TIFF header decoder and audited SHP reader",
            "source_selection_unchanged":True,"coordinates_or_attribute_values_published":False,
            "checked_selected_source_vertices":checked_vertices,
            "albers_forward_difference_max_m":max_albers_delta,
            "utm_forward_difference_max_m":max_utm_delta,"cases":cases}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=True,indent=2,allow_nan=False))
