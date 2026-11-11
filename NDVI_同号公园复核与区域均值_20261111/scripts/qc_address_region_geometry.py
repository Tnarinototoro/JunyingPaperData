"""Private-address, coarse-region geometry screening; no identifying output.

The author has confirmed Excel NO = old S1 Pxx = SAV ParkID. This checks
that the corresponding geometry does not obviously contradict the address
region. It does not identify a park from extrema or certify exact boundaries.
All names, addresses and coordinates stay in memory and are never emitted.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))
from audit_vectors_std import read_shp
from qc_regional_means_stdlib import inverse_albers

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

# Intentionally generous, hand-specified screening envelopes in WGS84,
# not official administrative boundary data or geocoded park locations.
# Values are generic public-region approximations, not park coordinates.
PREFECTURES = [
    (1, "北海道", (138.8, 40.9, 146.3, 46.2)),
    (2, "青森県", (139.2, 39.9, 142.0, 41.9)),
    (3, "岩手県", (140.3, 38.5, 142.4, 40.8)),
    (4, "宮城県", (139.9, 37.4, 142.1, 39.4)),
    (5, "秋田県", (139.3, 38.7, 141.3, 40.9)),
    (6, "山形県", (139.2, 37.4, 141.0, 39.6)),
    (7, "福島県", (138.8, 36.4, 141.6, 38.4)),
    (8, "茨城県", (139.3, 35.4, 141.3, 37.3)),
    (9, "栃木県", (139.0, 35.8, 140.7, 37.5)),
    (10, "群馬県", (138.1, 35.6, 140.2, 37.5)),
    (11, "埼玉県", (138.4, 35.4, 140.3, 36.7)),
    (12, "千葉県", (139.4, 34.6, 141.3, 36.5)),
    (13, "東京都", (138.3, 24.0, 154.2, 36.5)),
    (14, "神奈川県", (138.6, 34.7, 140.1, 36.0)),
    (15, "新潟県", (137.2, 36.4, 140.1, 38.9)),
    (16, "富山県", (136.5, 35.9, 138.0, 37.3)),
    (17, "石川県", (135.8, 35.9, 137.8, 38.0)),
    (18, "福井県", (135.1, 35.1, 137.2, 36.7)),
    (19, "山梨県", (138.0, 35.0, 139.5, 36.2)),
    (20, "長野県", (137.0, 35.0, 139.0, 37.4)),
    (21, "岐阜県", (135.6, 34.7, 138.2, 36.9)),
    (22, "静岡県", (137.2, 34.2, 139.5, 35.9)),
    (23, "愛知県", (136.3, 34.1, 138.5, 35.9)),
    (24, "三重県", (135.1, 33.3, 137.6, 35.8)),
    (25, "滋賀県", (135.4, 34.6, 136.9, 36.0)),
    (26, "京都府", (134.5, 34.4, 136.5, 36.0)),
    (27, "大阪府", (134.7, 33.9, 136.1, 35.4)),
    (28, "兵庫県", (133.7, 33.8, 135.9, 36.1)),
    (29, "奈良県", (135.1, 33.5, 136.8, 35.4)),
    (30, "和歌山県", (134.5, 33.0, 136.4, 35.0)),
    (31, "鳥取県", (132.8, 34.6, 135.0, 36.0)),
    (32, "島根県", (130.8, 33.9, 134.0, 36.7)),
    (33, "岡山県", (132.9, 33.9, 135.0, 35.7)),
    (34, "広島県", (131.5, 33.6, 134.0, 35.7)),
    (35, "山口県", (130.5, 33.3, 132.8, 35.2)),
    (36, "徳島県", (133.3, 33.1, 135.2, 34.8)),
    (37, "香川県", (133.2, 33.8, 134.8, 34.8)),
    (38, "愛媛県", (131.6, 32.5, 134.3, 34.7)),
    (39, "高知県", (131.8, 32.3, 134.9, 34.7)),
    (40, "福岡県", (129.7, 32.8, 131.7, 34.4)),
    (41, "佐賀県", (129.4, 32.7, 131.1, 34.0)),
    (42, "長崎県", (128.0, 31.7, 130.9, 35.0)),
    (43, "熊本県", (129.4, 31.8, 131.6, 33.7)),
    (44, "大分県", (130.3, 32.2, 132.7, 34.2)),
    (45, "宮崎県", (130.3, 30.8, 132.0, 33.0)),
    (46, "鹿児島県", (127.8, 27.0, 131.9, 32.6)),
    (47, "沖縄県", (122.6, 23.7, 131.8, 28.1)),
]

# Unambiguous municipality / ward tokens for addresses omitting the prefecture.
# Generic locality-to-region knowledge, not a polygon-based identity inference.
# Ambiguous bare wards (Chuo/Minato/Kita) and Fuchu are intentionally omitted.
LOCALITIES = {
    1: "札幌市 旭川市 釧路市 帯広市 函館市 小樽市 北見市 苫小牧市 千歳市 恵庭市 江別市 北広島市 石狩市 岩見沢市 富良野市 稚内市 根室市",
    4: "仙台市 名取市 多賀城市 岩沼市 石巻市 登米市 大崎市 塩竈市 白石市 角田市 気仙沼市 東松島市 富谷市 栗原市",
    5: "秋田市 大館市 由利本荘市 にかほ市 横手市 大仙市 仙北市 湯沢市 能代市 潟上市 鹿角市 北秋田市",
    11: "さいたま市 川口市 川越市 飯能市 所沢市 入間市 秩父市 熊谷市 上尾市 戸田市 朝霞市 和光市 ふじみ野市 志木市 新座市 草加市 八潮市 三郷市 越谷市 久喜市 行田市 東松山市 本庄市 深谷市 北本市 鴻巣市 吉川市 春日部市 狭山市 日高市 蓮田市 白岡市 鳩山町 越生町 吉見町 嵐山町 滑川町 ときがわ町",
    12: "千葉市 習志野市 八千代市 船橋市 佐倉市 成田市 流山市 浦安市 松戸市 市川市 柏市 市原市 鎌ケ谷市 八街市 白井市 印西市 四街道市 袖ケ浦市 木更津市 君津市 富津市 南房総市 館山市 東金市 茂原市 勝浦市 野田市",
    13: "千代田区 新宿区 文京区 台東区 墨田区 江東区 品川区 目黒区 大田区 世田谷区 渋谷区 中野区 杉並区 豊島区 荒川区 板橋区 練馬区 足立区 葛飾区 江戸川区 三鷹市 八王子市 町田市 多摩市 立川市 国分寺市 国立市 日野市 調布市 武蔵野市 小金井市 小平市 東村山市 東大和市 昭島市 狛江市 清瀬市 東久留米市 武蔵村山市 西東京市 福生市 羽村市 稲城市 あきる野市 青梅市",
    14: "川崎市 横浜市 相模原市 鎌倉市 藤沢市 横須賀市 逗子市 大和市 厚木市 海老名市 座間市 小田原市 南足柄市 平塚市 茅ヶ崎市 秦野市 伊勢原市 綾瀬市",
    22: "静岡市 浜松市 沼津市 三島市 富士市 富士宮市 裾野市 御殿場市 磐田市 焼津市 藤枝市 島田市 牧之原市 掛川市 袋井市 菊川市 湖西市 伊豆市 伊豆の国市 熱海市 伊東市 下田市",
    23: "名古屋市 豊田市 岡崎市 豊橋市 豊川市 春日井市 一宮市 犬山市 瀬戸市 尾張旭市 長久手市 日進市 東海市 大府市 刈谷市 安城市 知立市 知多市 半田市 常滑市 西尾市 碧南市 豊明市 清須市 北名古屋市 あま市 津島市 愛西市 稲沢市 岩倉市 江南市 小牧市 弥富市 田原市",
    25: "大津市 草津市 守山市 栗東市 野洲市 近江八幡市 湖南市 甲賀市 東近江市 彦根市 米原市 長浜市 高島市",
    26: "京都市 宇治市 城陽市 向日市 長岡京市 京田辺市 八幡市 木津川市 亀岡市 南丹市 福知山市 綾部市 舞鶴市 宮津市 京丹後市",
    27: "大阪市 堺市 吹田市 高槻市 茨木市 箕面市 枚方市 交野市 四條畷市 門真市 守口市 寝屋川市 摂津市 豊中市 池田市 大阪狭山市 富田林市 河内長野市 羽曳野市 松原市 藤井寺市 八尾市 柏原市 東大阪市 泉大津市 泉佐野市 岸和田市 貝塚市 泉南市 高石市 阪南市 忠岡町 熊取町 田尻町",
    28: "神戸市 西宮市 尼崎市 宝塚市 伊丹市 川西市 三田市 姫路市 明石市 加古川市 高砂市 加西市 西脇市 小野市 三木市 加東市 たつの市 宍粟市 赤穂市 相生市 丹波市 丹波篠山市 養父市 豊岡市 朝来市 淡路市 洲本市 南あわじ市",
    29: "奈良市 生駒市 大和郡山市 天理市 橿原市 大和高田市 桜井市 宇陀市 葛城市 香芝市 五條市 御所市",
    34: "広島市 福山市 呉市 東広島市 廿日市市 三原市 尾道市 庄原市 三次市 大竹市 竹原市 江田島市 安芸高田市",
    41: "佐賀市 唐津市 伊万里市 鳥栖市 武雄市 多久市 嬉野市 小城市 神埼市",
    47: "那覇市 浦添市 沖縄市 宜野湾市 糸満市 豊見城市 南城市 うるま市 名護市 宮古島市 石垣市",
}


def resolve_region(address, explicit_only=False):
    explicit = [(code, bounds) for code, label, bounds in PREFECTURES if label in address]
    if len(explicit) == 1:
        return explicit[0][0], explicit[0][1], "explicit_prefecture_in_address"
    if len(explicit) > 1:
        return None, None, "multiple_explicit_prefecture_labels"
    if explicit_only:
        return None, None, "no_unique_region_label"
    matches = [(len(label), code) for code, labels in LOCALITIES.items() for label in labels.split() if label in address]
    if not matches:
        return None, None, "no_unique_region_label"
    longest = max(length for length, _ in matches)
    codes = {code for length, code in matches if length == longest}
    if len(codes) != 1:
        return None, None, "ambiguous_locality_label"
    code = codes.pop()
    bounds = next(bounds for pref_code, _, bounds in PREFECTURES if pref_code == code)
    return code, bounds, "unambiguous_address_locality_token"


def private_rows(path):
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(node.text or "" for node in item.iter(NS + "t"))
                for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relations = {item.get("Id"): item.get("Target") for item in
            ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        out = []
        for sheet in workbook.find(NS + "sheets"):
            target = relations[sheet.get(RNS + "id")]
            part = target.lstrip("/") if target.startswith("/") else "xl/" + target
            xml = ET.fromstring(archive.read(part))
            for row in xml.iter(NS + "row"):
                cells = {}
                for cell in row.findall(NS + "c"):
                    col = re.sub(r"\d", "", cell.get("r"))
                    if cell.get("t") == "inlineStr":
                        value = "".join(node.text or "" for node in cell.iter(NS + "t"))
                    else:
                        node = cell.find(NS + "v")
                        value = node.text if node is not None else ""
                        if cell.get("t") == "s" and value:
                            value = shared[int(value)]
                    cells[col] = value
                try:
                    number = int(cells.get("A", ""))
                except ValueError:
                    continue
                if 1 <= number <= 39 and cells.get("B", "").strip() and cells.get("C", "").strip():
                    out.append({"ParkID": number, "private_name": cells["B"],
                        "private_address": unicodedata.normalize("NFKC", cells["C"])})
        return out


def centroid(ring):
    pts = ring[:-1] if ring[0] == ring[-1] else ring
    ox, oy = pts[0]
    shifted = [(x - ox, y - oy) for x, y in pts]
    edges = list(zip(shifted, shifted[1:] + shifted[:1]))
    crosses = [a[0] * b[1] - b[0] * a[1] for a, b in edges]
    twice_area = math.fsum(crosses)
    if abs(twice_area) < 1e-12:
        raise ValueError("Degenerate polygon cannot supply an area centroid")
    return (ox + math.fsum((a[0] + b[0]) * c for (a, b), c in zip(edges, crosses)) / (3 * twice_area),
            oy + math.fsum((a[1] + b[1]) * c for (a, b), c in zip(edges, crosses)) / (3 * twice_area))


def main():
    explicit_only = "--explicit-only" in sys.argv
    source = ROOT / "39个公园地址.xlsx"
    addresses = private_rows(source)
    by_id = {row["ParkID"]: row for row in addresses}
    features = read_shp(ROOT / "NDVI/parks_metric.shp", include_points=True)["feature_details"]
    records = []
    for feature in features:
        park_id = feature["record"]
        ring = feature["private_parts"][0]
        lon, lat = inverse_albers(*centroid(ring))
        row = by_id[park_id]
        code, bounds, region_method = resolve_region(row["private_address"], explicit_only=explicit_only)
        center_pass = bounds[0] <= lon <= bounds[2] and bounds[1] <= lat <= bounds[3] if bounds else None
        if bounds:
            transformed = [inverse_albers(x, y) for x, y in ring]
            vertices_pass = all(bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3] for x, y in transformed)
        else:
            vertices_pass = None
        records.append({"ParkID": park_id, "same_number_address_row_found": park_id in by_id,
            "address_prefecture_recognized_uniquely": code is not None,
            "address_region_resolution_method": region_method,
            "address_prefecture_numeric_code": code,
            "centroid_within_generous_address_prefecture_envelope": center_pass,
            "all_polygon_vertices_within_same_generous_envelope": vertices_pass,
            "centroid_in_broad_japan_longitude_latitude_range": 122.0 <= lon <= 155.0 and 20.0 <= lat <= 47.0,
            "screen_status": "not_assessed_no_unique_address_prefecture" if not bounds else "no_obvious_regional_contradiction" if center_pass and vertices_pass else "coarse_regional_mismatch_needs_map_check"})
    report = {
        "author_confirmed_identity_rule": "Excel NO = old S1 Pxx = SAV ParkID for all 39 parks; accepted as authority, not overridden by extrema fingerprints",
        "purpose": "Private-address coarse geographic consistency screening of same-number supplied geometry; not an identity remapping or exact-boundary certification",
        "address_region_mode": "explicit_prefecture_only" if explicit_only else "explicit_prefecture_plus_unambiguous_locality_screen",
        "source_workbook_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "polygon_source_sha256": hashlib.sha256((ROOT / "NDVI/parks_metric.shp").read_bytes()).hexdigest(),
        "address_rows_found": len(addresses), "geometry_rows_checked": len(records),
        "rows_with_unique_address_prefecture": sum(row["address_prefecture_recognized_uniquely"] for row in records),
        "rows_resolved_by_explicit_prefecture_label": sum(row["address_region_resolution_method"] == "explicit_prefecture_in_address" for row in records),
        "rows_resolved_by_unambiguous_locality_token": sum(row["address_region_resolution_method"] == "unambiguous_address_locality_token" for row in records),
        "ids_without_unique_address_prefecture": [row["ParkID"] for row in records if not row["address_prefecture_recognized_uniquely"]],
        "ids_with_obvious_coarse_regional_contradiction": [row["ParkID"] for row in records if row["screen_status"] == "coarse_regional_mismatch_needs_map_check"],
        "all_centroids_in_broad_japan_range": all(row["centroid_in_broad_japan_longitude_latitude_range"] for row in records),
        "priority_ids_9_18_28_32": [row for row in records if row["ParkID"] in (9, 18, 28, 32)],
        "records": records,
        "privacy": "Names, full addresses, polygon/centroid coordinates and geocoding queries are not output or stored; only anonymous IDs, numeric prefecture codes and screening booleans emitted",
        "input_files_modified": False, "geometry_or_id_reordering_performed": False, "sem_run_performed": False,
        "limitations": [
            "Region envelopes are deliberately generous hand-specified geographic approximations, not official administrative boundary data. Passing is evidence against an obvious wrong-region mismatch, not proof of the exact municipality or park boundary.",
            "Addresses omitting a prefecture are resolved only by an unambiguous known municipality or ward token; ambiguous labels are not guessed from the geometry. Locality names and full addresses are not emitted.",
            "No new geocoding is used. Prior generic service probes did not yield an HTTP response; no private address query was sent.",
            "The supplied actual park geometry and the author's same-number confirmation remain the operational authority for calculation. The screen creates no additional requirement for a cross-ID author table.",
            "SHP/SHX/DBF structural agreement and regional consistency cannot prove that every polygon corresponds to the exact named park; they do not exclude a same-region wrong-version label file.",
            "Prior cross-ID extrema matches remain numeric clues about the old values, not grounds to overturn the author's identity rule or rearrange the geometry."
        ],
    }
    print(json.dumps(report, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
