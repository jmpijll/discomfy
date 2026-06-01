"""v3 ``/image`` slash command (Slice 1).

End-to-end Manifest-driven image text-to-image flow:

1. Operator gates registration with ``DISCOMFY_V3=1``.
2. When the user runs ``/image``, the command looks up every Manifest
   in the registry whose Modality is ``IMAGE_T2I``.
3. If only one is registered, jumps straight into its Setup. Multiple
   manifests get a top-level select for workflow choice.
4. The :class:`~bot.setup.builder.SetupBuilder` renders the modal +
   view from the chosen Manifest.
5. On submit, the bot coerces values via the Plugin's
   :meth:`validate_slot_values`, applies them via
   :func:`core.manifest.apply_slots`, opens a v3
   :class:`~core.comfyui.v3.WSClient`, queues via
   :class:`~core.comfyui.v3.ComfyHTTPClient`, follows progress, and
   hands the Outputs to the Plugin's :meth:`render_outputs`.

This module never imports v2 paths.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import discord
from discord import app_commands

from bot.setup import SetupBuilder
from core.comfyui.v3 import (
    ComfyHTTPClient,
    Executing,
    ExecutionComplete,
    ExecutionError,
    Inventory,
    Progress,
    Reconnected,
    WSClient,
)
from core.manifest import Manifest, apply_slots, load_manifest_directory
from core.manifest.roles import Modality, Role
from core.modalities import default_registry
from core.run import Output, Run, RunStatus

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFESTS_DIR = REPO_ROOT / "workflows" / "manifests"

PROGRESS_DELTA_MIN = 5
PROGRESS_REPAINT_INTERVAL_S = 2.0


def is_v3_enabled() -> bool:
    """True iff the ``DISCOMFY_V3=1`` flag is set."""
    return os.environ.get("DISCOMFY_V3") == "1"


def register(bot: Any) -> None:
    """Attach the v3 ``/image`` slash command to ``bot.tree``.

    Called from ``main.py`` ONLY when :func:`is_v3_enabled` returns True.
    Does NOT touch any v2 wiring.
    """
    if not is_v3_enabled():
        return

    manifests_dir = Path(
        os.environ.get("DISCOMFY_V3_MANIFESTS_DIR", DEFAULT_MANIFESTS_DIR)
    )
    registry, errors = load_manifest_directory(manifests_dir)
    for err in errors:
        logger.warning("v3: manifest load error: %s", err)
    t2i_manifests = {m.id: m for m in registry if m.modality == Modality.IMAGE_T2I}
    logger.info(
        "v3: registered %d image_t2i manifests: %s",
        len(t2i_manifests),
        sorted(t2i_manifests),
    )
    if not t2i_manifests:
        logger.warning("v3: no image_t2i manifests found; /image will be inert")

    base_url = bot.config.comfyui.url

    @bot.tree.command(
        name="image",
        description="(v3) Generate an image from a Manifest-driven workflow",
    )
    @app_commands.describe(prompt="Quick prompt override (optional)")
    async def v3_image_command(
        interaction: discord.Interaction,
        prompt: str | None = None,
    ) -> None:
        await _handle_v3_image(
            interaction=interaction,
            manifests=t2i_manifests,
            base_url=base_url,
            inline_prompt=prompt,
        )


async def _handle_v3_image(
    *,
    interaction: discord.Interaction,
    manifests: dict[str, Manifest],
    base_url: str,
    inline_prompt: str | None,
) -> None:
    if not manifests:
        await interaction.response.send_message(
            "No v3 image workflows are registered on this bot.",
            ephemeral=True,
        )
        return

    if len(manifests) == 1:
        manifest = next(iter(manifests.values()))
    else:
        manifest = await _pick_manifest(interaction, manifests)
        if manifest is None:
            return

    await _start_setup(
        interaction=interaction,
        manifest=manifest,
        base_url=base_url,
        inline_prompt=inline_prompt,
    )


async def _pick_manifest(
    interaction: discord.Interaction,
    manifests: dict[str, Manifest],
) -> Manifest | None:
    options = [
        discord.SelectOption(label=m.name, value=m.id, description=m.description[:100])
        for m in manifests.values()
    ]

    chosen: dict[str, str] = {}
    done = asyncio.Event()

    class _ManifestPicker(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=120)

    view = _ManifestPicker()

    class _PickSelect(discord.ui.Select):
        def __init__(self) -> None:
            super().__init__(
                placeholder="Choose a workflow", options=options, min_values=1, max_values=1
            )

        async def callback(self, inter: discord.Interaction) -> None:
            chosen["id"] = self.values[0]
            done.set()
            await inter.response.defer()

    view.add_item(_PickSelect())
    await interaction.response.send_message(
        "Choose a workflow:", view=view, ephemeral=True
    )
    try:
        await asyncio.wait_for(done.wait(), timeout=120)
    except asyncio.TimeoutError:
        return None
    return manifests.get(chosen.get("id", ""))


async def _start_setup(
    *,
    interaction: discord.Interaction,
    manifest: Manifest,
    base_url: str,
    inline_prompt: str | None,
) -> None:
    """Build Setup UI, present modal, then queue + track on submit."""
    async with ComfyHTTPClient(base_url) as http:
        object_info = await http.get_object_info()
    inventory = Inventory(object_info)

    builder = SetupBuilder(manifest, inventory)
    plan = builder.build()
    plugin = default_registry.get(manifest.modality)

    slot_values: dict[str, Any] = {}
    if inline_prompt:
        slot_values["prompt"] = inline_prompt

    async def _on_modal_submit(
        inter: discord.Interaction, modal: discord.ui.Modal
    ) -> None:
        for item in modal.children:
            if isinstance(item, discord.ui.TextInput):
                slot_name = item.custom_id.removeprefix("v3_setup_text_")
                slot_values[slot_name] = item.value
        await inter.response.defer(thinking=True)
        await _execute_run(
            interaction=inter,
            manifest=manifest,
            base_url=base_url,
            slot_values=slot_values,
        )

    modal = builder.build_modal(on_submit=_on_modal_submit)
    if interaction.response.is_done():
        await interaction.followup.send(
            "Open the setup modal:",
            ephemeral=True,
        )
    else:
        await interaction.response.send_modal(modal)


async def _execute_run(
    *,
    interaction: discord.Interaction,
    manifest: Manifest,
    base_url: str,
    slot_values: dict[str, Any],
) -> None:
    """Coerce + apply slots, queue, follow progress, post Outputs."""
    plugin = default_registry.get(manifest.modality)
    try:
        coerced = await plugin.validate_slot_values(manifest, slot_values)
    except Exception as e:  # noqa: BLE001 - we want a friendly Discord error
        await interaction.followup.send(
            f"Slot validation failed: {e}", ephemeral=True
        )
        return

    workflow_path = REPO_ROOT / manifest.workflow_file
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    try:
        workflow_to_queue = apply_slots(workflow, manifest, coerced)
    except Exception as e:
        await interaction.followup.send(
            f"apply_slots failed: {e}", ephemeral=True
        )
        return

    run = Run(
        id=uuid.uuid4().hex,
        manifest_id=manifest.id,
        slot_values=coerced,
        status=RunStatus.QUEUED,
    )
    client_id = uuid.uuid4().hex
    mapper = plugin.progress_mapper()

    progress_msg = await interaction.followup.send(
        embed=_progress_embed(manifest, "queued", 0), wait=True
    )

    async with ComfyHTTPClient(base_url, client_id=client_id) as http:
        async with WSClient(base_url, client_id=client_id) as ws:
            try:
                prompt_id = await http.queue_prompt(workflow_to_queue)
            except Exception as e:
                await progress_msg.edit(
                    embed=_progress_embed(manifest, f"queue failed: {e}", 0)
                )
                return
            run.prompt_id = prompt_id
            run.status = RunStatus.RUNNING

            last_pct_shown = 0
            last_repaint = 0.0
            try:
                async for event in ws.events():
                    if isinstance(event, Reconnected):
                        continue
                    pid = getattr(event, "prompt_id", None)
                    if pid is not None and pid != prompt_id:
                        continue
                    pct = mapper.update(event)
                    if isinstance(event, ExecutionError):
                        await progress_msg.edit(
                            embed=_progress_embed(
                                manifest,
                                f"failed on node {event.node_id}: {event.message}",
                                last_pct_shown,
                            )
                        )
                        run.status = RunStatus.FAILED
                        return
                    is_complete = (
                        isinstance(event, ExecutionComplete)
                        or (
                            isinstance(event, Executing)
                            and event.node is None
                            and pid == prompt_id
                        )
                    )
                    if is_complete:
                        break
                    if (
                        pct is not None
                        and (
                            pct - last_pct_shown >= PROGRESS_DELTA_MIN
                            or (time.monotonic() - last_repaint) > PROGRESS_REPAINT_INTERVAL_S
                        )
                    ):
                        last_pct_shown = pct
                        last_repaint = time.monotonic()
                        await progress_msg.edit(
                            embed=_progress_embed(manifest, "running", pct)
                        )
            except Exception as e:
                await progress_msg.edit(
                    embed=_progress_embed(manifest, f"error: {e}", last_pct_shown)
                )
                run.status = RunStatus.FAILED
                return

        try:
            history = await http.get_history(prompt_id)
            entry = history.get(prompt_id) or {}
        except Exception as e:
            await progress_msg.edit(
                embed=_progress_embed(manifest, f"history error: {e}", 100)
            )
            return

        outputs = await _download_outputs(http, manifest, entry, run)

    payload = await plugin.render_outputs(run, outputs)
    discord_kwargs = payload.to_discord()
    await progress_msg.edit(
        embed=discord_kwargs.get("embed"),
        attachments=discord_kwargs.get("files", []),
    )


async def _download_outputs(
    http: ComfyHTTPClient,
    manifest: Manifest,
    history_entry: dict[str, Any],
    run: Run,
) -> list[Output]:
    node_outputs: dict[str, dict[str, Any]] = history_entry.get("outputs", {}) or {}
    collected: list[Output] = []
    for spec in manifest.outputs:
        node_data = node_outputs.get(spec.node)
        if not node_data:
            continue
        bucket = (
            "images"
            if spec.media.startswith("image/")
            else "videos"
            if spec.media.startswith("video/")
            else "audio"
            if spec.media.startswith("audio/")
            else "files"
        )
        for f in node_data.get(bucket, []) or []:
            filename = f.get("filename")
            if not filename:
                continue
            data = await http.get_view(
                filename,
                type=f.get("type", "output"),
                subfolder=f.get("subfolder", "") or "",
            )
            collected.append(
                Output(
                    role=spec.role,
                    media=spec.media,
                    path=Path(filename),
                    bytes_read=data,
                )
            )
    return collected


def _progress_embed(manifest: Manifest, status: str, pct: int) -> discord.Embed:
    bar = _bar(pct)
    embed = discord.Embed(
        title=f"v3 \u00b7 {manifest.name}",
        description=f"{bar}  {pct}%\nstatus: {status}",
        color=0x5865F2,
    )
    return embed


def _bar(pct: int, width: int = 20) -> str:
    pct = max(0, min(100, pct))
    filled = int(width * pct / 100)
    return "\u2588" * filled + "\u2591" * (width - filled)


__all__ = ["is_v3_enabled", "register"]
