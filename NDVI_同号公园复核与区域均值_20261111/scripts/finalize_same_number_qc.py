"""Append completed independent QC to our generated same-number handoff.

The prior generated ZIP is preserved. No original research input is edited.
"""

import json
from pathlib import Path
import shutil

from build_same_number_handoff import ROOT, OUT, AUDIT, archive_directory, digest


def main():
    original_archive = ROOT / (OUT.name + ".zip")
    backup = ROOT / (OUT.name + "_独立QC增补前存档.zip")
    temporary = ROOT / (OUT.name + "_独立QC临时.zip")
    expected_before = "01ef7ca3a435d6128e390aad5dd634fd2632f87c5bb410bed8e18b61821a0d68"
    assert original_archive.is_file() and digest(original_archive) == expected_before
    assert all(p.resolve().is_relative_to(ROOT.resolve())
               for p in (OUT, original_archive, backup, temporary))
    if backup.exists() or temporary.exists():
        raise FileExistsError("Refusing to overwrite a prior QC backup/temp file")
    independent = Path(__file__).with_name("qc_same_number_handoff_independent.json")
    independent_report = json.loads(independent.read_text(encoding="utf-8"))
    assert independent_report["all_checks_pass"]
    qc = OUT / "QC"
    for path in (independent, AUDIT / "address_region_geometry_screen.json"):
        shutil.copy2(path, qc / path.name)
    for path in (Path(__file__), Path(__file__).with_name("build_same_number_handoff.py"),
                 Path(__file__).with_name("qc_same_number_handoff_independent.py")):
        shutil.copy2(path, OUT / "scripts" / path.name)
    shutil.copy2(AUDIT / "qc_address_region_geometry.py",
                 OUT / "scripts" / "qc_address_region_geometry.py")
    shutil.copy2(original_archive, backup)
    assert digest(backup) == expected_before
    result = archive_directory(OUT, temporary)
    temporary.replace(original_archive)  # Exact target verified and backed up.
    print(json.dumps({**result, "archive": original_archive.name,
                      "prior_generated_zip_backup": backup.name,
                      "independent_QC_all_pass": True,
                      "geography_screen_scope": "31 explicit-address regions plus 8 limited screens; not precise boundary validation",
                      "final_unique_39_park_input": False,
                      "original_inputs_modified": False}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
