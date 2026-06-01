"""v3 value types for a Run, its Outputs, and the Discord payload.

These are deliberately tiny Pydantic models, not service objects. They
exist so the Plugin layer and the bot layer can share a typed contract
without dragging in Discord or ComfyUI imports.

A :class:`Run` is the canonical record of one end-to-end execution
triggered by a Discord interaction. An :class:`Output` is one file the
Run produced. A :class:`DiscordPayload` is what a Plugin's renderer
hands to the bot layer; the bot converts it to discord.py objects at
the seam.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.manifest.roles import Role


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Run(BaseModel):
    """One end-to-end execution of a Workflow on behalf of an Author."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(..., description="DisComfy-side run id (uuid4 hex)")
    manifest_id: str
    prompt_id: str | None = Field(
        default=None,
        description="ComfyUI-assigned prompt_id; absent until queued",
    )
    slot_values: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: RunStatus = RunStatus.QUEUED
    output_files: list[Path] = Field(default_factory=list)
    error: str | None = None


class Output(BaseModel):
    """One file a Run produced."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    role: Role
    media: str = Field(..., description="MIME type, e.g. image/png")
    path: Path
    bytes_read: bytes = Field(
        ..., description="The file's raw bytes, ready to attach to Discord"
    )

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def size_bytes(self) -> int:
        return len(self.bytes_read)


class DiscordFile(BaseModel):
    """A file attachment as a Plugin produces it.

    The bot layer is responsible for turning this into a ``discord.File``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    filename: str
    content_type: str
    data: bytes

    def to_discord_file(self) -> Any:
        """Return a ``discord.File`` constructed from this attachment.

        Imported lazily so this module stays Discord-free for tests.
        """
        import discord  # type: ignore

        return discord.File(io.BytesIO(self.data), filename=self.filename)


class DiscordPayload(BaseModel):
    """The Discord message a Plugin renderer produces for a finished Run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    embed: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw embed dict; converted to discord.Embed by the bot",
    )
    files: list[DiscordFile] = Field(default_factory=list)
    content: str | None = None

    def to_discord(self) -> dict[str, Any]:
        """Return a kwargs dict ready to pass to ``interaction.followup.send``.

        Imports discord lazily so unit tests can construct DiscordPayloads
        without a Discord runtime.
        """
        import discord  # type: ignore

        kwargs: dict[str, Any] = {}
        if self.content:
            kwargs["content"] = self.content
        if self.embed:
            kwargs["embed"] = discord.Embed.from_dict(self.embed)
        if self.files:
            kwargs["files"] = [f.to_discord_file() for f in self.files]
        return kwargs


__all__ = [
    "DiscordFile",
    "DiscordPayload",
    "Output",
    "Run",
    "RunStatus",
]
