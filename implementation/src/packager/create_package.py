#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path


def run(command):
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def canonical_json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def ensure_keys(private_key, public_key):
    private_key.parent.mkdir(parents=True, exist_ok=True)
    if not private_key.exists():
        run([
            "openssl",
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            str(private_key),
        ])
        private_key.chmod(0o600)

    if not public_key.exists():
        run([
            "openssl",
            "pkey",
            "-in",
            str(private_key),
            "-pubout",
            "-out",
            str(public_key),
        ])


def sign_file(private_key, input_file, signature_file):
    run([
        "openssl",
        "dgst",
        "-sha256",
        "-sign",
        str(private_key),
        "-out",
        str(signature_file),
        str(input_file),
    ])


def verify_signature(public_key, input_file, signature_file):
    result = subprocess.run([
        "openssl",
        "dgst",
        "-sha256",
        "-verify",
        str(public_key),
        "-signature",
        str(signature_file),
        str(input_file),
    ], text=True, capture_output=True)
    return result.returncode == 0


def write_checksum_manifest(root, manifest_path, files):
    lines = []
    for file_path in sorted(files):
        rel = file_path.relative_to(root).as_posix()
        lines.append(f"{sha256_file(file_path)}  {rel}")
    write_text(manifest_path, "\n".join(lines) + "\n")


def build_package(args):
    segments_dir = Path(args.segments_dir)
    package_root = Path(args.output_dir) / args.package_id
    payload_dir = package_root / "data"
    payload_segments_dir = payload_dir / "segments"
    private_key = Path(args.private_key)
    public_key = Path(args.public_key)

    segments = sorted(segments_dir.glob("segment_*.mp4"))
    if not segments:
        raise SystemExit(f"Nenhum segmento encontrado em {segments_dir}")

    if package_root.exists():
        shutil.rmtree(package_root)
    payload_segments_dir.mkdir(parents=True, exist_ok=True)

    ensure_keys(private_key, public_key)

    capture_start = datetime.fromisoformat(args.capture_start.replace("Z", "+00:00"))
    if capture_start.tzinfo is None:
        capture_start = capture_start.replace(tzinfo=timezone.utc)

    manifest_segments = []
    previous_hash = None
    for seq, segment in enumerate(segments):
        target = payload_segments_dir / segment.name
        shutil.copy2(segment, target)
        segment_hash = sha256_file(target)
        start = capture_start + timedelta(seconds=seq * args.segment_seconds)
        end = start + timedelta(seconds=args.segment_seconds)
        if seq == len(segments) - 1 and args.source_duration_seconds:
            end = capture_start + timedelta(seconds=args.source_duration_seconds)

        manifest_segments.append({
            "seq": seq,
            "filename": f"segments/{segment.name}",
            "start": start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "end": end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sha256": segment_hash,
            "prev_segment_hash": previous_hash,
        })
        previous_hash = segment_hash

    capture_end = manifest_segments[-1]["end"]
    hour_manifest = {
        "schema": "cftv-custody-hour-manifest/v1",
        "camera_id": args.camera_id,
        "device_id": args.device_id,
        "gateway_id": args.gateway_id,
        "capture_start": capture_start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "capture_end": capture_end,
        "segment_duration_seconds": args.segment_seconds,
        "segment_count": len(manifest_segments),
        "hash_algorithm": "sha256",
        "signature_algorithm": "rsa-2048-sha256",
        "segments": manifest_segments,
        "prev_package_manifest_hash": args.prev_package_manifest_hash,
        "status": "COMPLETE",
    }

    manifest_path = payload_dir / "hour_manifest.json"
    write_text(manifest_path, canonical_json(hour_manifest))
    manifest_hash = sha256_file(manifest_path)

    signature_path = payload_dir / "device_signature.sig"
    sign_file(private_key, manifest_path, signature_path)
    signature_valid = verify_signature(public_key, manifest_path, signature_path)
    if not signature_valid:
        raise SystemExit("Assinatura gerada nao foi validada pela chave publica.")

    write_text(package_root / "bagit.txt", "BagIt-Version: 0.97\nTag-File-Character-Encoding: UTF-8\n")
    write_text(package_root / "bag-info.txt", "\n".join([
        "Bag-Software-Agent: cftv-custody-mvp/0.1",
        "Source-Organization: Universidade de Brasilia",
        f"External-Identifier: {args.package_id}",
        f"Camera-ID: {args.camera_id}",
        f"Device-ID: {args.device_id}",
        f"Gateway-ID: {args.gateway_id}",
        f"Capture-Start: {hour_manifest['capture_start']}",
        f"Capture-End: {hour_manifest['capture_end']}",
        f"Segment-Duration-Seconds: {args.segment_seconds}",
        f"Payload-File-Count: {len(list(payload_dir.rglob('*')))}",
    ]) + "\n")

    payload_files = [path for path in payload_dir.rglob("*") if path.is_file()]
    write_checksum_manifest(package_root, package_root / "manifest-sha256.txt", payload_files)

    tag_files = [
        package_root / "bagit.txt",
        package_root / "bag-info.txt",
        package_root / "manifest-sha256.txt",
    ]
    write_checksum_manifest(package_root, package_root / "tagmanifest-sha256.txt", tag_files)

    package_root_hash = sha256_file(package_root / "manifest-sha256.txt")
    summary = {
        "package_id": args.package_id,
        "package_path": str(package_root),
        "camera_id": args.camera_id,
        "device_id": args.device_id,
        "gateway_id": args.gateway_id,
        "segment_count": len(manifest_segments),
        "manifest_hash": manifest_hash,
        "package_root_hash": package_root_hash,
        "signature_valid": signature_valid,
    }
    write_text(package_root / "package_summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Gera pacote SIP BagIt assinado para o MVP CFTV.")
    parser.add_argument("--segments-dir", default="data/segments")
    parser.add_argument("--output-dir", default="data/packages")
    parser.add_argument("--package-id", default="camera-001-20260615T210000Z")
    parser.add_argument("--camera-id", default="camera-001")
    parser.add_argument("--device-id", default="edge-001")
    parser.add_argument("--gateway-id", default="gateway-001")
    parser.add_argument("--capture-start", default="2026-06-15T21:00:00Z")
    parser.add_argument("--segment-seconds", type=int, default=2)
    parser.add_argument("--source-duration-seconds", type=float, default=7.7)
    parser.add_argument("--private-key", default="keys/device_private.pem")
    parser.add_argument("--public-key", default="keys/device_public.pem")
    parser.add_argument("--prev-package-manifest-hash", default=None)
    args = parser.parse_args()

    summary = build_package(args)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
