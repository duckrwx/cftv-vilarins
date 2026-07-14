#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path):
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command, cwd=None, check=True):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message)
    return result


def require_ots():
    if shutil.which("ots") is None:
        raise SystemExit(
            "Cliente OpenTimestamps nao encontrado. Instale com: pip install opentimestamps-client"
        )


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stamp_manifest(package_path, report_path, upgrade=False):
    require_ots()

    package_path = Path(package_path)
    manifest_path = package_path / "data" / "hour_manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Manifesto nao encontrado: {manifest_path}")

    timestamp_dir = package_path / "timestamp"
    timestamp_dir.mkdir(parents=True, exist_ok=True)

    proof_path = manifest_path.with_suffix(manifest_path.suffix + ".ots")
    final_proof_path = timestamp_dir / proof_path.name

    if proof_path.exists():
        proof_path.unlink()

    stamp_result = run(["ots", "stamp", str(manifest_path)])
    if not proof_path.exists():
        raise SystemExit(f"OpenTimestamps nao gerou a prova esperada: {proof_path}")

    shutil.move(str(proof_path), final_proof_path)

    upgrade_result = None
    if upgrade:
        upgrade_result = run(["ots", "upgrade", str(final_proof_path)], check=False)

    report = {
        "anchor_type": "opentimestamps-bitcoin",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "package_path": str(package_path),
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "ots_proof_path": str(final_proof_path),
        "ots_proof_sha256": sha256_file(final_proof_path),
        "stamp_stdout": stamp_result.stdout.strip(),
        "stamp_stderr": stamp_result.stderr.strip(),
        "upgrade_attempted": upgrade,
        "upgrade_returncode": upgrade_result.returncode if upgrade_result else None,
        "upgrade_stdout": upgrade_result.stdout.strip() if upgrade_result else None,
        "upgrade_stderr": upgrade_result.stderr.strip() if upgrade_result else None,
    }
    write_json(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Gera prova OpenTimestamps para o manifesto do pacote CFTV.")
    parser.add_argument("--package", default="data/packages/camera-001-20260615T210000Z")
    parser.add_argument("--report", default="reports/ots_stamp_report.json")
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Tenta atualizar a prova logo apos o stamp. Normalmente a prova so completa apos confirmacao em Bitcoin.",
    )
    args = parser.parse_args()

    report = stamp_manifest(args.package, args.report, upgrade=args.upgrade)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

