"""Archive only the supplied NDVI rasters and original GIS vector components.

Standard-library only. Never overwrite an existing archive or change a source.
Original file hashes are calculated while the very same bytes enter the ZIP.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parent.parent
SOURCE_DIR = WORKSPACE / "NDVI"
ARCHIVE = WORKSPACE / "NDVI_完整原始GIS源文件_仅内部_20261111.zip"
CHUNK_BYTES = 8 * 1024 * 1024
EXPECTED_TIFF_NAMES = {
    "NDVI_fukushima.tif",
    "NDVI_fukushima_up.tif",
    "NDVI_hokka_test.tif",
    "NDVI_island.tif",
    "NDVI_kyoto.tif",
    "NDVI_nagoya.tif",
    "NDVI_nara.tif",
    "NDVI_tokyo.tif",
    "NDVI_tokyo_down.tif",
    "NDVI_west.tif",
}
README_NAME = "README_内部使用说明.txt"
MANIFEST_NAME = "manifest.json"


def progress(message: str) -> None:
    print(message, flush=True)


def select_sources() -> list[Path]:
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError(SOURCE_DIR)
    rasters = sorted(SOURCE_DIR.glob("NDVI_*.tif"))
    if {path.name for path in rasters} != EXPECTED_TIFF_NAMES:
        raise RuntimeError("The original NDVI TIFF inventory differs from the ten reviewed files.")
    sources = list(rasters)
    for raster in rasters:
        auxiliary = raster.with_name(raster.name + ".aux.xml")
        if auxiliary.is_file():
            sources.append(auxiliary)
    for stem in ("parks_metric", "100m_buffer"):
        sources.extend(path for path in SOURCE_DIR.glob(stem + ".*") if path.is_file())
    for source in sources:
        if not source.is_file() or source.resolve().parent != SOURCE_DIR.resolve():
            raise RuntimeError(f"Source is not a regular file within NDVI: {source}")
    for required in ("parks_metric.shp", "parks_metric.dbf", "parks_metric.shx",
                     "parks_metric.prj", "parks_metric.cpg", "parks_metric.qmd",
                     "100m_buffer.shp", "100m_buffer.shx", "100m_buffer.prj", "100m_buffer.cpg"):
        if not (SOURCE_DIR / required).is_file():
            raise RuntimeError(f"Reviewed original vector component is missing: {required}")
    return sorted(set(sources), key=lambda path: path.name.casefold())


def make_readme(sources: list[Path]) -> bytes:
    buffer_components = ", ".join(path.name for path in sources if path.name.startswith("100m_buffer."))
    missing_dbf_note = (
        "源目录未发现 100m_buffer.dbf；本包保留实际存在的原组件，未补造、修复或改写属性表。\n"
        if not (SOURCE_DIR / "100m_buffer.dbf").exists() else ""
    )
    return (
        "原始 NDVI 与 GIS 源文件归档（仅作者 / 教授内部使用）\n"
        "日期：2026-11-11\n\n"
        "本包仅复制用户提供的 NDVI 目录内原始 GIS 数据，原文件字节内容不作任何更改。\n"
        "包含全部 10 幅 NDVI_*.tif、现有同名 .tif.aux.xml、parks_metric.* 原组件、"
        "100m_buffer.* 原组件。未读取或使用 NDBI；未收录无关论文、SAV、Excel 或新模型 / 图。\n"
        f"100m_buffer 原组件：{buffer_components}\n"
        f"{missing_dbf_note}\n"
        "CRS 注意：parks_metric.qmd 中的旧 CRS 元数据声明不替代 .prj；本包不修改原有 CRS 信息。\n\n"
        "与另一个主分析包的关系：本包不执行像元选择、100 m 园外缓冲区扣除园区内部、"
        "39Z 或统计 / SEM 分析。上述规则、结果及派生输入由另一个主分析包说明。\n"
        "本轮主分析影像选择：园区 9 = NDVI_nagoya.tif；园区 18、28 = NDVI_nara.tif；"
        "园区 32 = NDVI_fukushima_up.tif；其余 35 个园区采用各自唯一可用的影像。\n"
        "本源归档仍保留全部 10 幅原始影像，以便独立复核上述选择。\n\n"
        "完整性：manifest.json 列明原文件名、ZIP 成员名、大小与 SHA256。原文件 SHA256 与"
        "压缩输入采用同一次流式读取；生成后进行 ZIP CRC testzip 检查以及逐成员 SHA256 核验。\n"
        "manifest.json 不包含自身的 SHA256；其 SHA256 和整个 ZIP 的 SHA256 由生成脚本输出。\n\n"
        "隐私：空间数据包含可识别位置，仅限作者 / 教授内部使用，不应作为匿名数据公开传播。\n"
    ).encode("utf-8")


def stream_hash(stream) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(CHUNK_BYTES):
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if ARCHIVE.exists():
        raise FileExistsError(f"Refusing to overwrite existing archive: {ARCHIVE}")
    sources = select_sources()
    initial_stats = {source.name: source.stat() for source in sources}
    source_bytes = sum(stat.st_size for stat in initial_stats.values())
    free_bytes = shutil.disk_usage(WORKSPACE).free
    required_free_bytes = (source_bytes * 103 + 99) // 100 + 64 * 1024 * 1024
    if free_bytes < required_free_bytes:
        raise RuntimeError(f"Insufficient disk space: {free_bytes} free; {required_free_bytes} required.")
    readme_bytes = make_readme(sources)
    records: list[dict] = []
    progress(json.dumps({"phase": "preflight", "original_file_count": len(sources),
                         "ndvi_tiff_count": len(EXPECTED_TIFF_NAMES),
                         "source_bytes": source_bytes, "free_disk_bytes": free_bytes,
                         "required_free_bytes": required_free_bytes,
                         "archive": str(ARCHIVE)}, ensure_ascii=False))
    with zipfile.ZipFile(ARCHIVE, mode="x", compression=zipfile.ZIP_DEFLATED,
                        compresslevel=1, allowZip64=True) as archive:
        for index, source in enumerate(sources, start=1):
            expected_stat = initial_stats[source.name]
            member_name = "NDVI/" + source.name
            member_info = zipfile.ZipInfo.from_file(source, arcname=member_name)
            member_info.compress_type = zipfile.ZIP_DEFLATED
            # ZipInfo.compress_level is public only in Python 3.13+.
            member_info._compresslevel = 1
            digest = hashlib.sha256()
            size = 0
            progress(f"WRITE_BEGIN {index}/{len(sources)} {source.name} bytes={expected_stat.st_size}")
            with source.open("rb") as input_stream, archive.open(member_info, mode="w", force_zip64=True) as output_stream:
                while chunk := input_stream.read(CHUNK_BYTES):
                    output_stream.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            final_stat = source.stat()
            if (size != expected_stat.st_size or final_stat.st_size != expected_stat.st_size
                    or final_stat.st_mtime_ns != expected_stat.st_mtime_ns
                    or final_stat.st_ino != expected_stat.st_ino):
                raise RuntimeError(f"Source changed while archiving: {source.name}")
            records.append({"file_name": source.name, "source_relative_path": member_name,
                            "member_name": member_name, "size_bytes": size,
                            "sha256": digest.hexdigest(), "role": "unchanged_original_source"})
            progress(f"WRITE_OK {index}/{len(sources)} {source.name} sha256={digest.hexdigest()}")
        archive.writestr(README_NAME, readme_bytes)
        readme_record = {"file_name": README_NAME, "member_name": README_NAME,
                        "size_bytes": len(readme_bytes),
                        "sha256": hashlib.sha256(readme_bytes).hexdigest(),
                        "role": "generated_documentation"}
        manifest = {
            "schema_version": 1,
            "created_at": datetime.now().astimezone().isoformat(),
            "classification": "INTERNAL: authors and professors only; identifiable spatial locations",
            "archive_kind": "unchanged user-provided original NDVI and vector sources",
            "compression": {"method": "ZIP_DEFLATED", "level": 1, "zip64_allowed": True},
            "original_source_file_count": len(records),
            "ndvi_tiff_count": len(EXPECTED_TIFF_NAMES),
            "total_original_source_bytes": source_bytes,
            "ndbi_read_or_used": False,
            "qmd_crs_note": "Old CRS metadata in parks_metric.qmd does not replace the .prj declaration.",
            "main_analysis_package_is_separate": True,
            "main_analysis_source_selection": {
                "9": "NDVI_nagoya.tif", "18": "NDVI_nara.tif", "28": "NDVI_nara.tif",
                "32": "NDVI_fukushima_up.tif",
                "remaining_35_parks": "each park's only available original NDVI raster",
                "source_archive_retains_all_10_rasters": True,
            },
            "source_absence_notes": (["100m_buffer.dbf was not present; no attribute table was reconstructed."]
                                     if not (SOURCE_DIR / "100m_buffer.dbf").exists() else []),
            "files": records + [readme_record],
            "manifest_self_hash": "Not embedded; emitted together with the whole-archive SHA256 after verification.",
        }
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        archive.writestr(MANIFEST_NAME, manifest_bytes)

    progress("CRC_TESTZIP_BEGIN")
    with zipfile.ZipFile(ARCHIVE, mode="r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"ZIP CRC validation failed: {bad_member}")
        progress("CRC_TESTZIP_OK")
        saved_manifest_bytes = archive.read(MANIFEST_NAME)
        if saved_manifest_bytes != manifest_bytes:
            raise RuntimeError("Saved manifest differs from generated manifest.")
        saved_manifest = json.loads(saved_manifest_bytes)
        saved_records = saved_manifest["files"]
        expected_members = {record["member_name"] for record in saved_records} | {MANIFEST_NAME}
        actual_members = archive.namelist()
        if len(actual_members) != len(expected_members) or set(actual_members) != expected_members:
            raise RuntimeError("ZIP member inventory does not match the manifest.")
        for index, record in enumerate(saved_records, start=1):
            with archive.open(record["member_name"], mode="r") as member_stream:
                size, digest = stream_hash(member_stream)
            if size != record["size_bytes"] or digest != record["sha256"]:
                raise RuntimeError(f"Manifest size/SHA256 validation failed: {record['member_name']}")
            progress(f"VERIFY_OK {index}/{len(saved_records)} {record['member_name']} sha256={digest}")
    for source in sources:
        final_stat = source.stat()
        initial_stat = initial_stats[source.name]
        if (final_stat.st_size, final_stat.st_mtime_ns, final_stat.st_ino) != (
                initial_stat.st_size, initial_stat.st_mtime_ns, initial_stat.st_ino):
            raise RuntimeError(f"Source metadata changed during the completed archive run: {source.name}")
    progress("ARCHIVE_SHA256_BEGIN")
    with ARCHIVE.open("rb") as archive_stream:
        archive_size, archive_sha256 = stream_hash(archive_stream)
    summary = {"status": "verified", "archive": str(ARCHIVE),
               "size_bytes": archive_size, "sha256": archive_sha256,
               "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
               "member_count": len(actual_members), "original_source_file_count": len(sources),
               "ndvi_tiff_count": len(EXPECTED_TIFF_NAMES), "source_bytes": source_bytes,
               "testzip": "passed", "manifest_member_size_and_sha256": "all passed",
               "original_source_metadata": "unchanged", "ndbi_read_or_used": False}
    progress("FINAL_SUMMARY " + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
