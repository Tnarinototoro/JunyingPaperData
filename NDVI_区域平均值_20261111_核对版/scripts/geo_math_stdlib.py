"""WGS84 ellipsoidal Albers/UTM transforms; no raster resampling.

These functions are restricted to the supplied Asia North Albers definition
and northern-hemisphere WGS84 UTM zones. They are not a general CRS library.
Angles at the public interface are degrees; planar coordinates are metres.
"""

import math

A = 6378137.0
E2 = 0.0066943799901413165
E = math.sqrt(E2)
EP2 = E2 / (1.0 - E2)
K0 = 0.9996


def _q(phi):
    s = math.sin(phi)
    return (1.0 - E2) * (s / (1.0 - E2 * s * s)
                        - math.log((1.0 - E * s) / (1.0 + E * s)) / (2.0 * E))


def _m(phi):
    return math.cos(phi) / math.sqrt(1.0 - E2 * math.sin(phi) ** 2)


P1, P2, P0, L0 = map(math.radians, (15.0, 65.0, 30.0, 95.0))
ALBERS_N = (_m(P1) ** 2 - _m(P2) ** 2) / (_q(P2) - _q(P1))
ALBERS_C = _m(P1) ** 2 + ALBERS_N * _q(P1)
ALBERS_RHO0 = A * math.sqrt(ALBERS_C - ALBERS_N * _q(P0)) / ALBERS_N


def lonlat_to_albers(lon, lat):
    phi, lam = math.radians(lat), math.radians(lon)
    rho = A * math.sqrt(ALBERS_C - ALBERS_N * _q(phi)) / ALBERS_N
    theta = ALBERS_N * (lam - L0)
    return rho * math.sin(theta), ALBERS_RHO0 - rho * math.cos(theta)


def albers_to_lonlat(x, y):
    rho = math.copysign(math.hypot(x, ALBERS_RHO0 - y), ALBERS_N)
    theta = math.atan2(math.copysign(1.0, ALBERS_N) * x,
                       math.copysign(1.0, ALBERS_N) * (ALBERS_RHO0 - y))
    target_q = (ALBERS_C - (rho * ALBERS_N / A) ** 2) / ALBERS_N
    phi = math.asin(max(-1.0, min(1.0, target_q / 2.0)))
    for _ in range(12):
        derivative = 2.0 * (1.0 - E2) * math.cos(phi) / (1.0 - E2 * math.sin(phi) ** 2) ** 2
        step = (_q(phi) - target_q) / derivative
        phi -= step
        if abs(step) < 2e-15:
            break
    return math.degrees(L0 + theta / ALBERS_N), math.degrees(phi)


def _meridional_arc(phi):
    return A * ((1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256) * phi
                - (3 * E2 / 8 + 3 * E2 ** 2 / 32 + 45 * E2 ** 3 / 1024) * math.sin(2 * phi)
                + (15 * E2 ** 2 / 256 + 45 * E2 ** 3 / 1024) * math.sin(4 * phi)
                - 35 * E2 ** 3 / 3072 * math.sin(6 * phi))


def lonlat_to_utm(lon, lat, epsg):
    if epsg not in range(32601, 32661) or not (-80 <= lat <= 84):
        raise ValueError("Only WGS84 northern UTM EPSG32601..32660 is supported")
    zone = epsg - 32600
    lam0 = math.radians(zone * 6 - 183)
    phi, lam = math.radians(lat), math.radians(lon)
    if abs(lam - lam0) > math.radians(12):
        raise ValueError("Point is too far from this UTM central meridian")
    n = A / math.sqrt(1 - E2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = EP2 * math.cos(phi) ** 2
    aa = math.cos(phi) * (lam - lam0)
    x = 500000 + K0 * n * (aa + (1 - t + c) * aa ** 3 / 6
                           + (5 - 18 * t + t * t + 72 * c - 58 * EP2) * aa ** 5 / 120)
    y = K0 * (_meridional_arc(phi) + n * math.tan(phi)
              * (aa ** 2 / 2 + (5 - t + 9 * c + 4 * c * c) * aa ** 4 / 24
                 + (61 - 58 * t + t * t + 600 * c - 330 * EP2) * aa ** 6 / 720))
    return x, y


def utm_to_lonlat(x, y, epsg):
    if epsg not in range(32601, 32661):
        raise ValueError("Only WGS84 northern UTM EPSG32601..32660 is supported")
    zone = epsg - 32600
    mu = (y / K0) / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
            + (21 * e1 * e1 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
            + 151 * e1 ** 3 / 96 * math.sin(6 * mu)
            + 1097 * e1 ** 4 / 512 * math.sin(8 * mu))
    n1 = A / math.sqrt(1 - E2 * math.sin(phi1) ** 2)
    r1 = A * (1 - E2) / (1 - E2 * math.sin(phi1) ** 2) ** 1.5
    t1 = math.tan(phi1) ** 2
    c1 = EP2 * math.cos(phi1) ** 2
    d = (x - 500000) / (n1 * K0)
    phi = phi1 - (n1 * math.tan(phi1) / r1) * (
        d * d / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * EP2) * d ** 4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * EP2 - 3 * c1 * c1) * d ** 6 / 720)
    lam = math.radians(zone * 6 - 183) + (
        d - (1 + 2 * t1 + c1) * d ** 3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * EP2 + 24 * t1 * t1) * d ** 5 / 120) / math.cos(phi1)
    return math.degrees(lam), math.degrees(phi)


def albers_to_utm(x, y, epsg):
    return lonlat_to_utm(*albers_to_lonlat(x, y), epsg)


def utm_to_albers(x, y, epsg):
    return lonlat_to_albers(*utm_to_lonlat(x, y, epsg))


def self_test():
    cases = [(139.767125, 35.681236, 32654), (135.0, 35.0, 32653),
             (130.0, 33.0, 32652), (142.0, 43.0, 32654), (127.7, 26.2, 32652)]
    max_albers_m = max_utm_m = 0.0
    for lon, lat, epsg in cases:
        axy = lonlat_to_albers(lon, lat)
        ll = albers_to_lonlat(*axy)
        max_albers_m = max(max_albers_m, math.dist(axy, lonlat_to_albers(*ll)))
        uxy = lonlat_to_utm(lon, lat, epsg)
        ll = utm_to_lonlat(*uxy, epsg)
        max_utm_m = max(max_utm_m, math.dist(uxy, lonlat_to_utm(*ll, epsg)))
    assert lonlat_to_albers(95.0, 30.0) == (0.0, 0.0)
    assert math.dist(lonlat_to_utm(135.0, 0.0, 32653), (500000.0, 0.0)) < 1e-8
    assert max_albers_m < 1e-6
    assert max_utm_m < 0.005
    return {"albers_roundtrip_max_m": max_albers_m, "utm_roundtrip_max_m": max_utm_m,
            "scope": "Supplied Albers and northern UTM only; series transforms, no resampling"}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test()))
