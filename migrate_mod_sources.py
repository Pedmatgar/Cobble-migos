from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import tomllib


@dataclass
class CurseForgeMod:
    meta_path: Path
    slug: str
    name: str
    filename: str
    addon_id: str
    file_id: str


def _run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def _load_curseforge_mods(pack_root: Path) -> List[CurseForgeMod]:
    mods_dir = pack_root / "mods"
    mods: List[CurseForgeMod] = []
    for meta_path in sorted(mods_dir.glob("*.pw.toml")):
        text = meta_path.read_text(encoding="utf-8")
        if 'mode = "metadata:curseforge"' not in text:
            continue
        data = tomllib.loads(text)
        update_cf = data.get("update", {}).get("curseforge", {})
        mods.append(
            CurseForgeMod(
                meta_path=meta_path,
                slug=meta_path.stem.replace(".pw", ""),
                name=data.get("name", meta_path.stem),
                filename=data.get("download", {}).get("filename", ""),
                addon_id=str(update_cf.get("project-id", "")),
                file_id=str(update_cf.get("file-id", "")),
            )
        )
    return mods


def migrate_curseforge_to_modrinth(
    pack_root: str | Path,
    packwiz_bin: str = "packwiz",
    yes: bool = True,
    dry_run: bool = False,
) -> Dict[str, object]:
    root = Path(pack_root).resolve()
    mods = _load_curseforge_mods(root)
    migrated: List[str] = []
    fallback_curseforge: List[str] = []
    failures: List[Dict[str, str]] = []

    for mod in mods:
        remove_cmd = [packwiz_bin, "remove", mod.slug]
        if yes:
            remove_cmd.append("-y")
        if not dry_run:
            rm = _run(remove_cmd, root)
            if rm.returncode != 0:
                remove_by_name = [packwiz_bin, "remove", mod.name]
                if yes:
                    remove_by_name.append("-y")
                rm2 = _run(remove_by_name, root)
                if rm2.returncode != 0:
                    failures.append(
                        {
                            "mod": mod.name,
                            "stage": "remove",
                            "error": (rm.stdout + rm.stderr + rm2.stdout + rm2.stderr)[:1200],
                        }
                    )
                    continue

        add_mr_cmd = [packwiz_bin, "mr", "add", mod.name]
        if mod.filename:
            add_mr_cmd.extend(["--version-filename", mod.filename])
        if yes:
            add_mr_cmd.append("-y")

        if dry_run:
            migrated.append(mod.name)
            continue

        add_mr = _run(add_mr_cmd, root)
        if add_mr.returncode == 0:
            migrated.append(mod.name)
            continue

        if mod.addon_id and mod.file_id:
            add_cf_cmd = [
                packwiz_bin,
                "cf",
                "add",
                "--addon-id",
                mod.addon_id,
                "--file-id",
                mod.file_id,
            ]
            if yes:
                add_cf_cmd.append("-y")
            add_cf = _run(add_cf_cmd, root)
            if add_cf.returncode == 0:
                fallback_curseforge.append(mod.name)
                continue
            failures.append(
                {
                    "mod": mod.name,
                    "stage": "restore_curseforge",
                    "error": (add_mr.stdout + add_mr.stderr + add_cf.stdout + add_cf.stderr)[:1200],
                }
            )
        else:
            failures.append(
                {
                    "mod": mod.name,
                    "stage": "restore_curseforge_missing_ids",
                    "error": (add_mr.stdout + add_mr.stderr)[:1200],
                }
            )

    if not dry_run:
        refresh_cmd = [packwiz_bin, "refresh"]
        if yes:
            refresh_cmd.append("-y")
        refresh = _run(refresh_cmd, root)
        if refresh.returncode != 0:
            failures.append(
                {
                    "mod": "index",
                    "stage": "refresh",
                    "error": (refresh.stdout + refresh.stderr)[:1200],
                }
            )

    return {
        "pack_root": str(root),
        "total_curseforge_mods": len(mods),
        "migrated_to_modrinth_count": len(migrated),
        "fallback_to_curseforge_count": len(fallback_curseforge),
        "failures_count": len(failures),
        "migrated_to_modrinth": migrated,
        "fallback_to_curseforge": fallback_curseforge,
        "failures": failures,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate CurseForge-sourced packwiz mods to Modrinth with CurseForge fallback."
    )
    parser.add_argument(
        "--pack-root",
        default=".",
        help="Path to the packwiz pack root (contains pack.toml).",
    )
    parser.add_argument(
        "--packwiz-bin",
        default="packwiz",
        help="packwiz executable path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration loop without changing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = migrate_curseforge_to_modrinth(
        pack_root=args.pack_root,
        packwiz_bin=args.packwiz_bin,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
