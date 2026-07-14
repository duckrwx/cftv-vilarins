#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checksum_manifest(path):
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel_path = line.split(None, 1)
        entries[rel_path.strip()] = digest
    return entries


def validate_checksums(package_root, manifest_name):
    manifest_path = package_root / manifest_name
    if not manifest_path.exists():
        return False, [f"manifesto ausente: {manifest_name}"]

    errors = []
    for rel_path, expected_hash in read_checksum_manifest(manifest_path).items():
        file_path = package_root / rel_path
        if not file_path.exists():
            errors.append(f"arquivo ausente: {rel_path}")
            continue
        actual_hash = sha256_file(file_path)
        if actual_hash != expected_hash:
            errors.append(f"checksum divergente: {rel_path}")
    return not errors, errors


def verify_signature(public_key, manifest_path, signature_path):
    if not public_key.exists():
        return False, f"chave publica ausente: {public_key}"
    if not signature_path.exists():
        return False, f"assinatura ausente: {signature_path}"

    result = subprocess.run([
        "openssl",
        "dgst",
        "-sha256",
        "-verify",
        str(public_key),
        "-signature",
        str(signature_path),
        str(manifest_path),
    ], text=True, capture_output=True)
    if result.returncode != 0:
        return False, (result.stderr.strip() or result.stdout.strip() or "assinatura invalida")
    return True, "assinatura valida"


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_sequence(package_root, manifest):
    errors = []
    segments = manifest.get("segments", [])
    if manifest.get("segment_count") != len(segments):
        errors.append("segment_count nao corresponde a lista de segmentos")

    previous_hash = None
    previous_end = None
    for expected_seq, segment in enumerate(segments):
        if segment.get("seq") != expected_seq:
            errors.append(f"seq inesperado: esperado {expected_seq}, recebido {segment.get('seq')}")

        filename = segment.get("filename")
        file_path = package_root / "data" / filename
        if not file_path.exists():
            errors.append(f"segmento ausente: {filename}")
            continue

        actual_hash = sha256_file(file_path)
        if actual_hash != segment.get("sha256"):
            errors.append(f"hash do segmento divergente: {filename}")

        if segment.get("prev_segment_hash") != previous_hash:
            errors.append(f"prev_segment_hash divergente no segmento {expected_seq}")

        start = parse_time(segment["start"])
        end = parse_time(segment["end"])
        if end <= start:
            errors.append(f"janela temporal invalida no segmento {expected_seq}")
        if previous_end is not None and start != previous_end:
            errors.append(f"lacuna ou sobreposicao temporal no segmento {expected_seq}")

        previous_hash = segment.get("sha256")
        previous_end = end

    if segments:
        if manifest.get("capture_start") != segments[0].get("start"):
            errors.append("capture_start nao corresponde ao primeiro segmento")
        if manifest.get("capture_end") != segments[-1].get("end"):
            errors.append("capture_end nao corresponde ao ultimo segmento")

    return not errors, errors


def validate_package(package_root, public_key):
    package_root = Path(package_root)
    public_key = Path(public_key)
    manifest_path = package_root / "data" / "hour_manifest.json"
    signature_path = package_root / "data" / "device_signature.sig"

    errors = []
    required_files = [
        "bagit.txt",
        "bag-info.txt",
        "manifest-sha256.txt",
        "tagmanifest-sha256.txt",
        "data/hour_manifest.json",
        "data/device_signature.sig",
    ]
    for rel_path in required_files:
        if not (package_root / rel_path).exists():
            errors.append(f"arquivo obrigatorio ausente: {rel_path}")

    payload_ok, payload_errors = validate_checksums(package_root, "manifest-sha256.txt")
    tag_ok, tag_errors = validate_checksums(package_root, "tagmanifest-sha256.txt")
    errors.extend(payload_errors)
    errors.extend(tag_errors)

    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    signature_ok, signature_message = verify_signature(public_key, manifest_path, signature_path)
    if not signature_ok:
        errors.append(signature_message)

    sequence_ok = False
    sequence_errors = []
    if manifest:
        sequence_ok, sequence_errors = validate_sequence(package_root, manifest)
        errors.extend(sequence_errors)

    package_root_hash = sha256_file(package_root / "manifest-sha256.txt") if (package_root / "manifest-sha256.txt").exists() else None

    report = {
        "package_path": str(package_root),
        "camera_id": manifest.get("camera_id"),
        "device_id": manifest.get("device_id"),
        "gateway_id": manifest.get("gateway_id"),
        "segment_count": manifest.get("segment_count"),
        "bagit_valid": payload_ok and tag_ok,
        "payload_checksums_valid": payload_ok,
        "tag_checksums_valid": tag_ok,
        "signature_valid": signature_ok,
        "sequence_valid": sequence_ok,
        "package_root_hash": package_root_hash,
        "status": "COMPLETE" if not errors else "INVALID",
        "errors": errors,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Valida pacote SIP BagIt no gateway.")
    parser.add_argument("--package", default="data/packages/camera-001-20260615T210000Z")
    parser.add_argument("--public-key", default="keys/device_public.pem")
    parser.add_argument("--report", default="reports/gateway_validation_report.json")
    args = parser.parse_args()

    report = validate_package(args.package, args.public_key)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "COMPLETE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
