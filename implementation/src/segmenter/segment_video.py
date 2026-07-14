#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def run(command):
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def probe_video(path):
    output = run([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,format_name,bit_rate",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,r_frame_rate,duration",
        "-of",
        "json",
        str(path),
    ])
    return json.loads(output)


def segment_video(input_path, output_dir, segment_seconds, mode):
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_segment in output_dir.glob("segment_*.mp4"):
        old_segment.unlink()

    pattern = output_dir / "segment_%04d.mp4"
    command = ["ffmpeg", "-y", "-i", str(input_path), "-map", "0"]
    if mode == "copy":
        command.extend(["-c", "copy"])
    else:
        command.extend([
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-force_key_frames",
            f"expr:gte(t,n_forced*{segment_seconds})",
        ])
    command.extend([
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        str(pattern),
    ])
    run(command)


def main():
    parser = argparse.ArgumentParser(description="Segmenta video de entrada para o MVP CFTV.")
    parser.add_argument("--input", default="data/input/video.mp4")
    parser.add_argument("--output-dir", default="data/segments")
    parser.add_argument("--segment-seconds", type=int, default=2)
    parser.add_argument("--metadata", default="data/segments/segments_metadata.json")
    parser.add_argument(
        "--mode",
        choices=["copy", "reencode"],
        default="reencode",
        help="copy preserva codec original mas depende de keyframes; reencode força cortes no intervalo definido.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    metadata_path = Path(args.metadata)

    if not input_path.exists():
        raise SystemExit(f"Video de entrada nao encontrado: {input_path}")

    source_probe = probe_video(input_path)
    segment_video(input_path, output_dir, args.segment_seconds, args.mode)

    segments = sorted(output_dir.glob("segment_*.mp4"))
    if not segments:
        raise SystemExit("Nenhum segmento foi gerado.")

    metadata = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "segment_seconds": args.segment_seconds,
        "mode": args.mode,
        "source_probe": source_probe,
        "segments": [],
    }

    for index, segment in enumerate(segments):
        probe = probe_video(segment)
        metadata["segments"].append({
            "seq": index,
            "filename": segment.name,
            "path": str(segment),
            "probe": probe,
        })

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"input={input_path}")
    print(f"segments={len(segments)}")
    print(f"metadata={metadata_path}")


if __name__ == "__main__":
    main()
