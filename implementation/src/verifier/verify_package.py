#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.gateway.validate_package import validate_package  # noqa: E402


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_opentimestamps(package_path, require_ots=True):
    package_path = Path(package_path)
    manifest_path = package_path / "data" / "hour_manifest.json"
    proof_path = package_path / "timestamp" / "hour_manifest.json.ots"

    result = {
        "ots_required": require_ots,
        "ots_cli_available": shutil.which("ots") is not None,
        "manifest_path": str(manifest_path),
        "ots_proof_path": str(proof_path),
        "ots_proof_found": proof_path.exists(),
        "ots_verified": False,
        "ots_pending": False,
        "ots_returncode": None,
        "ots_stdout": "",
        "ots_stderr": "",
        "errors": [],
    }

    if not require_ots:
        return result

    if not manifest_path.exists():
        result["errors"].append("manifesto ausente para verificacao OpenTimestamps")
        return result

    if not proof_path.exists():
        result["errors"].append("prova OpenTimestamps ausente")
        return result

    if not result["ots_cli_available"]:
        result["errors"].append("cliente ots ausente; instale opentimestamps-client")
        return result

    # O cliente ots espera encontrar o arquivo original junto da prova .ots.
    temp_proof_path = manifest_path.with_suffix(manifest_path.suffix + ".ots")
    copied = False
    if temp_proof_path != proof_path:
        if temp_proof_path.exists():
            temp_proof_path.unlink()
        shutil.copy2(proof_path, temp_proof_path)
        copied = True

    try:
        completed = subprocess.run(
            ["ots", "verify", str(temp_proof_path)],
            text=True,
            capture_output=True,
        )
    finally:
        if copied and temp_proof_path.exists():
            temp_proof_path.unlink()

    result["ots_returncode"] = completed.returncode
    result["ots_stdout"] = completed.stdout.strip()
    result["ots_stderr"] = completed.stderr.strip()
    result["ots_verified"] = completed.returncode == 0
    combined_output = "\n".join(part for part in [result["ots_stdout"], result["ots_stderr"]] if part)
    result["ots_pending"] = "Pending confirmation in Bitcoin blockchain" in combined_output
    if completed.returncode != 0:
        if result["ots_pending"]:
            result["errors"].append("prova OpenTimestamps pendente de confirmacao em Bitcoin")
        else:
            result["errors"].append(result["ots_stderr"] or result["ots_stdout"] or "prova OpenTimestamps invalida")

    return result


def verify_package(package_path, public_key, require_ots=True):
    gateway_report = validate_package(package_path, public_key)
    ots_report = verify_opentimestamps(package_path, require_ots=require_ots)

    gateway_errors = list(gateway_report.get("errors", []))
    ots_errors = list(ots_report.get("errors", []))
    errors = gateway_errors + ots_errors
    ots_ok = (not require_ots) or ots_report.get("ots_verified")
    if gateway_report.get("status") == "COMPLETE" and ots_ok and not errors:
        status = "INTEGRO"
    elif (
        gateway_report.get("status") == "COMPLETE"
        and require_ots
        and ots_report.get("ots_pending")
        and not gateway_errors
    ):
        status = "PENDENTE_BITCOIN"
    else:
        status = "INVALIDO"

    return {
        "verification_mode": "opentimestamps-bitcoin",
        "package_path": str(package_path),
        "camera_id": gateway_report.get("camera_id"),
        "device_id": gateway_report.get("device_id"),
        "gateway_id": gateway_report.get("gateway_id"),
        "segment_count": gateway_report.get("segment_count"),
        "gateway_validation": {
            "bagit_valid": gateway_report.get("bagit_valid"),
            "payload_checksums_valid": gateway_report.get("payload_checksums_valid"),
            "tag_checksums_valid": gateway_report.get("tag_checksums_valid"),
            "signature_valid": gateway_report.get("signature_valid"),
            "sequence_valid": gateway_report.get("sequence_valid"),
            "package_root_hash": gateway_report.get("package_root_hash"),
        },
        "timestamp_validation": ots_report,
        "status": status,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Verificador independente do pacote CFTV com OpenTimestamps.")
    parser.add_argument("--package", default="data/packages/camera-001-20260615T210000Z")
    parser.add_argument("--public-key", default="keys/device_public.pem")
    parser.add_argument("--report", default="reports/integrity_report.json")
    parser.add_argument(
        "--skip-ots",
        action="store_true",
        help="Valida apenas integridade local, assinatura e BagIt. Use somente para testes antes de gerar .ots.",
    )
    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help="Retorna sucesso operacional quando a unica pendencia for confirmacao Bitcoin da prova OpenTimestamps.",
    )
    args = parser.parse_args()

    report = verify_package(args.package, args.public_key, require_ots=not args.skip_ots)
    write_json(args.report, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "INTEGRO" and not (args.allow_pending and report["status"] == "PENDENTE_BITCOIN"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
