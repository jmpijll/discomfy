"""Shared audio helpers for the audio_tts and audio_music Plugins.

This module is **Plugin-agnostic** by design: nothing here knows about
Fish-Speech, ACE-Step, or any other model. It packages an audio file
for Discord, extracts a duration, transcodes when ComfyUI emits a
non-MP3, and renders a small monochrome waveform PNG preview.

ADR anchors:

- ADR-0007 mandates "MP3 + duration label + waveform preview" for the
  audio Modalities and notes that ``imageio-ffmpeg`` is already a
  transitive dep, so we shell out to its bundled binary when the host
  has neither ``ffprobe`` nor a system ``ffmpeg`` on ``$PATH``.
- ADR-0002 says Plugins do not know about specific models; this module
  encodes that boundary for audio packaging.

ffmpeg / ffprobe handling:

The bot may run on hosts with no ffmpeg / ffprobe on ``$PATH`` (Docker
slim images, fresh dev VMs). All subprocess calls are fail-soft:

- Duration extraction returns ``-1.0`` and logs a warning if no ffprobe
  / ffmpeg is found.
- Transcoding raises :class:`AudioToolingMissing` so the caller can
  fall back to delivering the original audio with a friendly note.
- Waveform rendering returns ``None`` when ffmpeg is unavailable; the
  Plugin then posts only the audio file, no preview attachment.

The shared :class:`AudioPackage` dataclass is what each Plugin's
renderer returns to the bot layer.
"""

from __future__ import annotations

import logging
import re
import shutil
import struct
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DISCORD_AUDIO_SIZE_LIMIT_BYTES: int = 25 * 1024 * 1024
"""Discord's per-file attachment cap for free / non-boosted servers."""

DEFAULT_WAVEFORM_WIDTH: int = 600
DEFAULT_WAVEFORM_HEIGHT: int = 100

_DURATION_RE = re.compile(
    r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", re.IGNORECASE
)


class AudioToolingMissing(RuntimeError):
    """Raised when an operation needs ffmpeg / ffprobe and neither is present."""


@dataclass(frozen=True)
class AudioPackage:
    """A Discord-ready bundle for one audio output.

    A Plugin renderer constructs one of these per audio Output:

    - ``filename`` / ``content_type`` / ``data``: the audio file itself
      ready to attach to a Discord message.
    - ``duration_seconds``: best-effort length probe; ``-1.0`` means
      the host is missing ffmpeg / ffprobe and the Plugin should label
      the duration as "unknown" rather than block.
    - ``waveform_png``: a small monochrome PNG preview, or ``None`` if
      ffmpeg was unavailable / the audio could not be decoded.
    - ``oversize``: the file exceeds Discord's 25 MB cap. The Plugin
      should NOT attach ``data`` in that case; instead it can post a
      stub message pointing to the on-disk path.
    """

    filename: str
    content_type: str
    data: bytes
    duration_seconds: float
    waveform_png: bytes | None
    oversize: bool = False

    @property
    def size_bytes(self) -> int:
        return len(self.data)

    def duration_label(self) -> str:
        """Return a human-friendly mm:ss label, or 'unknown'."""
        if self.duration_seconds < 0:
            return "unknown"
        total = int(round(self.duration_seconds))
        m, s = divmod(total, 60)
        if m >= 60:
            h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"


def package_for_discord(
    audio_path: Path,
    mime: str,
    *,
    waveform_width: int = DEFAULT_WAVEFORM_WIDTH,
    waveform_height: int = DEFAULT_WAVEFORM_HEIGHT,
) -> AudioPackage:
    """Build an :class:`AudioPackage` from an on-disk audio file.

    The returned package always has ``data`` populated (even when
    ``oversize`` is ``True``) so the Plugin can decide whether to
    attach the bytes or post a stub. ``waveform_png`` is omitted for
    oversize files to save work.
    """
    audio_path = Path(audio_path)
    data = audio_path.read_bytes()
    duration = extract_duration_seconds(audio_path)
    oversize = len(data) > DISCORD_AUDIO_SIZE_LIMIT_BYTES
    waveform: bytes | None = None
    if not oversize:
        try:
            waveform = render_waveform_png(
                audio_path, width=waveform_width, height=waveform_height
            )
        except Exception as e:  # noqa: BLE001 - waveform is decorative
            logger.warning(
                "waveform render failed for %s: %s; posting without preview",
                audio_path,
                e,
            )
            waveform = None
    return AudioPackage(
        filename=audio_path.name,
        content_type=mime,
        data=data,
        duration_seconds=duration,
        waveform_png=waveform,
        oversize=oversize,
    )


def extract_duration_seconds(audio_path: Path) -> float:
    """Best-effort audio duration in seconds.

    Tries, in order:

    1. ``ffprobe`` on ``$PATH`` (cheapest + most accurate).
    2. ``ffmpeg -i`` (system or imageio-bundled), parsing
       ``Duration: HH:MM:SS.ms`` from stderr.
    3. Python stdlib :mod:`wave` for ``.wav`` containers.

    Returns ``-1.0`` and logs a warning if every method fails. The
    Plugin renderer should treat negative values as "unknown".
    """
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        logger.warning("extract_duration_seconds: %s not found", audio_path)
        return -1.0

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            out = subprocess.run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if out.returncode == 0:
                value = out.stdout.strip()
                if value:
                    return float(value)
        except (subprocess.TimeoutExpired, ValueError, OSError) as e:
            logger.warning("ffprobe failed for %s: %s; falling back", audio_path, e)

    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        try:
            proc = subprocess.run(
                [ffmpeg, "-hide_banner", "-i", str(audio_path)],
                capture_output=True,
                text=True,
                timeout=20,
            )
            stderr = proc.stderr or ""
            match = _DURATION_RE.search(stderr)
            if match:
                hours, minutes, seconds = match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.warning("ffmpeg duration probe failed for %s: %s", audio_path, e)

    if audio_path.suffix.lower() in (".wav", ".wave"):
        try:
            with wave.open(str(audio_path), "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate() or 0
                if rate > 0:
                    return frames / float(rate)
        except (wave.Error, OSError, EOFError) as e:
            logger.warning("wave fallback failed for %s: %s", audio_path, e)

    logger.warning(
        "no ffprobe/ffmpeg available; duration unknown for %s", audio_path
    )
    return -1.0


def transcode_to_mp3(input_path: Path, *, output_path: Path | None = None) -> Path:
    """Transcode any ffmpeg-readable audio to a 192k MP3.

    Used when a manifest's downstream node emits WAV (e.g. plain
    ``SaveAudio`` instead of ``SaveAudioMP3``). Writes alongside the
    input by default (``foo.wav`` -> ``foo.mp3``).

    Raises:
        AudioToolingMissing: no ffmpeg available on the host.
        RuntimeError: ffmpeg returned a non-zero exit.
    """
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise AudioToolingMissing(
            "ffmpeg not available on PATH and imageio-ffmpeg lookup failed; "
            "cannot transcode to MP3"
        )
    out = output_path if output_path is not None else input_path.with_suffix(".mp3")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(input_path),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg transcode failed: {proc.stderr.strip()[:500]}"
        )
    return out


def render_waveform_png(
    audio_path: Path,
    *,
    width: int = DEFAULT_WAVEFORM_WIDTH,
    height: int = DEFAULT_WAVEFORM_HEIGHT,
) -> bytes | None:
    """Render a tiny monochrome waveform preview as PNG bytes.

    Decodes the audio to mono int16 PCM via ffmpeg, downsamples into
    ``width`` peak/trough pairs, and draws the silhouette in black on
    a white background using PIL. Returns ``None`` if ffmpeg is
    unavailable - the bot then posts the audio file alone, no preview.

    Args:
        audio_path: input audio (anything ffmpeg can read).
        width: output PNG width in pixels.
        height: output PNG height in pixels.
    """
    audio_path = Path(audio_path)
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        logger.warning(
            "render_waveform_png: no ffmpeg, skipping waveform for %s", audio_path
        )
        return None
    if width <= 0 or height <= 0:
        raise ValueError("width/height must be positive")

    sample_rate = 8000
    proc = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "s16le",
            "-",
        ],
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0 or not proc.stdout:
        logger.warning(
            "render_waveform_png: ffmpeg decode failed for %s (%s)",
            audio_path,
            (proc.stderr or b"").decode("utf-8", "replace")[:200],
        )
        return None

    raw = proc.stdout
    sample_count = len(raw) // 2
    if sample_count == 0:
        return None
    samples = struct.unpack(f"<{sample_count}h", raw[: sample_count * 2])

    return _draw_waveform_png(samples, width=width, height=height)


def _draw_waveform_png(samples, *, width: int, height: int) -> bytes:
    """Bin samples into ``width`` columns, draw silhouette, return PNG."""
    from io import BytesIO

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    sample_count = len(samples)
    if sample_count == 0:
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    bin_size = max(sample_count // width, 1)
    mid_y = height // 2
    max_amp = 32768
    for col in range(width):
        start = col * bin_size
        end = start + bin_size
        if start >= sample_count:
            break
        chunk = samples[start:end]
        if not chunk:
            continue
        peak_pos = max(chunk)
        peak_neg = min(chunk)
        top_y = int(mid_y - (peak_pos / max_amp) * mid_y)
        bot_y = int(mid_y - (peak_neg / max_amp) * mid_y)
        if top_y == bot_y:
            top_y -= 1
            bot_y += 1
        draw.line([(col, top_y), (col, bot_y)], fill=(20, 20, 20))

    draw.line([(0, mid_y), (width - 1, mid_y)], fill=(180, 180, 180))

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _find_ffmpeg() -> str | None:
    """Return a path to an ffmpeg executable, or ``None``.

    Order:

    1. ``ffmpeg`` on ``$PATH`` (system install).
    2. ``imageio_ffmpeg.get_ffmpeg_exe()`` (already a dependency for
       video frame export, ADR-0007).
    """
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg  # type: ignore[import-untyped]

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).is_file():
            return exe
    except Exception as e:  # noqa: BLE001 - any failure -> fallback to None
        logger.debug("imageio_ffmpeg lookup failed: %s", e)
    return None


__all__ = [
    "AudioPackage",
    "AudioToolingMissing",
    "DEFAULT_WAVEFORM_HEIGHT",
    "DEFAULT_WAVEFORM_WIDTH",
    "DISCORD_AUDIO_SIZE_LIMIT_BYTES",
    "extract_duration_seconds",
    "package_for_discord",
    "render_waveform_png",
    "transcode_to_mp3",
]
