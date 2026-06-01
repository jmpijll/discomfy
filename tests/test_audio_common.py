"""Tests for :mod:`core.modalities.audio_common`.

Three behaviours under test:

- ``extract_duration_seconds`` returns a real number for a WAV fixture
  (always works via the stdlib ``wave`` fallback) and ``-1.0`` when no
  audio tooling can decode the file at all.
- ``render_waveform_png`` produces a valid PNG header (or ``None`` on
  hosts without ffmpeg).
- ``package_for_discord`` builds an :class:`AudioPackage` whose
  ``duration_label`` is well-formed and whose oversize flag flips at
  the 25 MB Discord cap.

A tiny mono 16-bit WAV fixture is generated via :mod:`wave` so the
tests run on hosts without ffmpeg / ffprobe.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import pytest

from core.modalities import audio_common
from core.modalities.audio_common import (
    AudioPackage,
    DISCORD_AUDIO_SIZE_LIMIT_BYTES,
    AudioToolingMissing,
    extract_duration_seconds,
    package_for_discord,
    render_waveform_png,
    transcode_to_mp3,
)


def _write_sine_wav(path: Path, *, duration_s: float = 0.5, freq: float = 440.0) -> Path:
    """Write a tiny mono 16-bit sine WAV to ``path``."""
    sample_rate = 8000
    n_samples = int(sample_rate * duration_s)
    import math

    frames = bytearray()
    for i in range(n_samples):
        amp = int(0.4 * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        frames.extend(struct.pack("<h", amp))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(bytes(frames))
    return path


@pytest.fixture
def sine_wav(tmp_path: Path) -> Path:
    return _write_sine_wav(tmp_path / "sine.wav", duration_s=0.5)


@pytest.fixture
def long_wav(tmp_path: Path) -> Path:
    return _write_sine_wav(tmp_path / "long.wav", duration_s=2.5)


class TestExtractDurationSeconds:
    def test_wave_fallback_returns_duration(self, sine_wav: Path) -> None:
        d = extract_duration_seconds(sine_wav)
        assert d == pytest.approx(0.5, abs=0.05)

    def test_returns_negative_for_missing_file(self, tmp_path: Path) -> None:
        d = extract_duration_seconds(tmp_path / "nope.wav")
        assert d == -1.0

    def test_no_tooling_returns_negative(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Force the all-fail path: garbage extension + no tooling."""
        garbage = tmp_path / "noaudio.bin"
        garbage.write_bytes(b"not really audio")

        monkeypatch.setattr(audio_common.shutil, "which", lambda name: None)
        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)

        assert extract_duration_seconds(garbage) == -1.0


class TestRenderWaveformPng:
    def test_returns_none_when_no_ffmpeg(
        self, sine_wav: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)
        assert render_waveform_png(sine_wav) is None

    def test_validates_dimensions(self, sine_wav: Path) -> None:
        with pytest.raises(ValueError):
            render_waveform_png(sine_wav, width=0, height=10)


class TestDrawWaveformPng:
    def test_draws_valid_png(self) -> None:
        samples = [int(32767 * (i % 100 - 50) / 50) for i in range(2000)]
        png = audio_common._draw_waveform_png(samples, width=200, height=40)
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(png) > 100

    def test_handles_empty(self) -> None:
        png = audio_common._draw_waveform_png([], width=50, height=20)
        assert png[:8] == b"\x89PNG\r\n\x1a\n"


class TestPackageForDiscord:
    def test_packages_small_wav_without_ffmpeg(
        self,
        sine_wav: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)
        pkg = package_for_discord(sine_wav, "audio/wav")
        assert isinstance(pkg, AudioPackage)
        assert pkg.filename == "sine.wav"
        assert pkg.content_type == "audio/wav"
        assert pkg.data == sine_wav.read_bytes()
        assert pkg.oversize is False
        assert pkg.waveform_png is None
        assert pkg.duration_seconds > 0
        assert pkg.duration_label() == "0:00" or pkg.duration_label() == "0:01"

    def test_oversize_flag_skips_waveform(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        big = tmp_path / "big.bin"
        big.write_bytes(b"\x00" * (DISCORD_AUDIO_SIZE_LIMIT_BYTES + 16))

        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)
        pkg = package_for_discord(big, "audio/mpeg")
        assert pkg.oversize is True
        assert pkg.waveform_png is None

    def test_duration_label_unknown_for_negative(self) -> None:
        pkg = AudioPackage(
            filename="x.mp3",
            content_type="audio/mpeg",
            data=b"",
            duration_seconds=-1.0,
            waveform_png=None,
        )
        assert pkg.duration_label() == "unknown"

    def test_duration_label_minutes_seconds(self) -> None:
        pkg = AudioPackage(
            filename="x.mp3",
            content_type="audio/mpeg",
            data=b"",
            duration_seconds=125.4,
            waveform_png=None,
        )
        assert pkg.duration_label() == "2:05"

    def test_duration_label_hours_minutes_seconds(self) -> None:
        pkg = AudioPackage(
            filename="x.mp3",
            content_type="audio/mpeg",
            data=b"",
            duration_seconds=3725,
            waveform_png=None,
        )
        assert pkg.duration_label() == "1:02:05"


class TestTranscodeToMp3:
    def test_raises_when_no_ffmpeg(
        self,
        sine_wav: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)
        with pytest.raises(AudioToolingMissing):
            transcode_to_mp3(sine_wav)

    def test_raises_for_missing_input(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            transcode_to_mp3(tmp_path / "nope.wav")
