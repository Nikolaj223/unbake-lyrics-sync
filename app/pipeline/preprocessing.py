from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx

from .types import AudioAsset


class AudioPreprocessor:
    def __init__(self, tmp_dir: str, max_audio_duration_sec: int) -> None:
        self.tmp_dir = Path(tmp_dir)
        self.max_audio_duration_sec = max_audio_duration_sec
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def prepare(self, source_url: str) -> AudioAsset:
        workdir = Path(tempfile.mkdtemp(prefix="unbake_", dir=self.tmp_dir))
        downloaded_path = workdir / "input.m4a"
        normalized_path = workdir / "normalized.wav"

        self._download(source_url, downloaded_path)
        self._transcode(downloaded_path, normalized_path)
        duration_ms = self._probe_duration_ms(normalized_path)

        if duration_ms and duration_ms > self.max_audio_duration_sec * 1000:
            raise ValueError(
                f"Audio is too long: {duration_ms} ms exceeds limit {self.max_audio_duration_sec * 1000} ms"
            )

        return AudioAsset(
            source_url=source_url,
            downloaded_path=str(downloaded_path),
            normalized_path=str(normalized_path),
            original_format="m4a",
            duration_ms=duration_ms,
        )

    def prepare_local_file(self, source_path: str) -> AudioAsset:
        original_path = Path(source_path).expanduser().resolve()
        if not original_path.exists():
            raise FileNotFoundError(f"Audio file does not exist: {original_path}")

        workdir = Path(tempfile.mkdtemp(prefix="unbake_", dir=self.tmp_dir))
        downloaded_path = workdir / f"input{original_path.suffix or '.audio'}"
        normalized_path = workdir / "normalized.wav"

        shutil.copyfile(original_path, downloaded_path)
        self._transcode(downloaded_path, normalized_path)
        duration_ms = self._probe_duration_ms(normalized_path)

        if duration_ms and duration_ms > self.max_audio_duration_sec * 1000:
            raise ValueError(
                f"Audio is too long: {duration_ms} ms exceeds limit {self.max_audio_duration_sec * 1000} ms"
            )

        return AudioAsset(
            source_url=str(original_path),
            downloaded_path=str(downloaded_path),
            normalized_path=str(normalized_path),
            original_format=original_path.suffix.lstrip(".") or "unknown",
            duration_ms=duration_ms,
        )

    def cleanup(self, asset: AudioAsset) -> None:
        workdir = Path(asset.downloaded_path).parent
        if workdir.exists():
            shutil.rmtree(workdir, ignore_errors=True)

    def _download(self, source_url: str, destination: Path) -> None:
        with httpx.stream("GET", source_url, follow_redirects=True, timeout=120.0) as response:
            response.raise_for_status()
            with destination.open("wb") as file_handle:
                for chunk in response.iter_bytes():
                    file_handle.write(chunk)

    def _transcode(self, input_path: Path, output_path: Path) -> None:
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _probe_duration_ms(self, normalized_path: Path) -> int | None:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(normalized_path),
        ]
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        value = result.stdout.strip()
        if not value:
            return None
        return round(float(value) * 1000)
