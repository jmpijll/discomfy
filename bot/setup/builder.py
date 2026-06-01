"""Generate Discord Setup UI from a Manifest (ADR-0003).

ADR-0003 spells out the mapping table. This module implements it.

The builder produces three artefacts:

1. A :class:`SlotBinning` - which slots go in the modal, which become
   select menus, which are command-level attachments, which are toggle
   buttons. This is the shape the bot reasons about; it is testable
   without instantiating Discord components.
2. A ``discord.ui.Modal`` populated with up to 5 ``TextInput``s for
   text / number / seed slots (with an "overflow" button on the View
   when there are > 5).
3. A ``discord.ui.View`` carrying select menus for enum slots and a
   "Generate" button plus the overflow modal button when needed.

Discord component construction is lazy: the dataclass-y planning step
is import-safe; only :meth:`SetupBuilder.build_view` and
:meth:`SetupBuilder.build_modal` import discord.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from core.comfyui.v3.capability import Inventory
from core.manifest.schema import Manifest, Slot, SlotType, UIHint

MAX_MODAL_TEXT_INPUTS: int = 5
MAX_SELECT_OPTIONS: int = 25
MAX_TEXT_INPUT_LENGTH: int = 4000
MAX_SHORT_TEXT_LENGTH: int = 100


class SetupBuildError(ValueError):
    """The Manifest cannot be rendered as a Discord UI."""


@dataclass
class SlotBinning:
    """Where each Slot ends up in the Discord UI (ADR-0003).

    All four lists are ordered to match the user's declared slot order
    in the Manifest. ``overflow_text`` carries slots that would have
    gone into the modal but exceeded Discord's 5-input cap; they land
    on the second-page modal.
    """

    modal_text: list[Slot] = field(default_factory=list)
    overflow_text: list[Slot] = field(default_factory=list)
    selects: list[Slot] = field(default_factory=list)
    booleans: list[Slot] = field(default_factory=list)
    attachments: list[Slot] = field(default_factory=list)

    @property
    def has_overflow(self) -> bool:
        return bool(self.overflow_text)

    def all(self) -> list[Slot]:
        return [
            *self.modal_text,
            *self.overflow_text,
            *self.selects,
            *self.booleans,
            *self.attachments,
        ]


@dataclass
class BuiltSetup:
    """The output of :meth:`SetupBuilder.build`."""

    manifest: Manifest
    binning: SlotBinning
    select_options: dict[str, list[str]]
    """select slot name -> list of options (after Inventory resolution + cap)."""
    overflow_truncated: dict[str, int] = field(default_factory=dict)
    """select slot name -> count of options truncated by the 25-option cap."""


class SetupBuilder:
    """Produces a Discord Setup UI from one Manifest.

    Usage:

        builder = SetupBuilder(manifest, inventory)
        plan = builder.build()
        modal = builder.build_modal(on_submit=...)
        view = builder.build_view(on_generate=..., on_overflow=...)
    """

    def __init__(self, manifest: Manifest, inventory: Inventory) -> None:
        self.manifest = manifest
        self.inventory = inventory
        self._plan: BuiltSetup | None = None

    def build(self) -> BuiltSetup:
        """Plan the binning + resolve select options. Pure / no discord."""
        if self._plan is not None:
            return self._plan
        binning = SlotBinning()
        select_options: dict[str, list[str]] = {}
        overflow_truncated: dict[str, int] = {}
        for slot in self.manifest.slots:
            hint = slot.ui.hint
            if hint in (UIHint.SHORT_TEXT, UIHint.LONG_TEXT, UIHint.NUMBER, UIHint.SEED):
                if len(binning.modal_text) < MAX_MODAL_TEXT_INPUTS:
                    binning.modal_text.append(slot)
                else:
                    binning.overflow_text.append(slot)
            elif hint in (UIHint.SELECT, UIHint.SELECT_STATIC):
                opts = self._resolve_select_options(slot)
                if len(opts) > MAX_SELECT_OPTIONS:
                    overflow_truncated[slot.name] = len(opts) - MAX_SELECT_OPTIONS
                    opts = opts[:MAX_SELECT_OPTIONS]
                select_options[slot.name] = opts
                binning.selects.append(slot)
            elif hint == UIHint.BOOLEAN:
                binning.booleans.append(slot)
            elif hint in (UIHint.IMAGE, UIHint.AUDIO):
                binning.attachments.append(slot)
            else:
                raise SetupBuildError(
                    f"slot '{slot.name}': unhandled ui.hint {hint!r}"
                )
        self._plan = BuiltSetup(
            manifest=self.manifest,
            binning=binning,
            select_options=select_options,
            overflow_truncated=overflow_truncated,
        )
        return self._plan

    def _resolve_select_options(self, slot: Slot) -> list[str]:
        if slot.ui.hint == UIHint.SELECT_STATIC or slot.type == SlotType.ENUM_STATIC:
            return list(slot.options or [])
        if slot.options_from is None:
            raise SetupBuildError(
                f"slot '{slot.name}': select slot has no options_from and no inline options"
            )
        return self.inventory.options_for(slot.options_from)

    def build_modal(
        self,
        *,
        on_submit: Callable[..., Any] | None = None,
        title: str | None = None,
        overflow: bool = False,
    ) -> Any:
        """Construct a ``discord.ui.Modal`` for the first 5 text slots.

        ``overflow=True`` builds the second-page modal for slots that
        spilled past the 5-input cap.
        """
        import discord  # type: ignore
        from discord import ui  # type: ignore

        plan = self.build()
        slots = plan.binning.overflow_text if overflow else plan.binning.modal_text
        modal_title = (
            title
            or (f"{self.manifest.name} (more)" if overflow else self.manifest.name)
        )
        modal_title = _clip(modal_title, 45)

        class _Modal(ui.Modal):
            def __init__(self) -> None:
                super().__init__(title=modal_title)

            async def on_submit(self, interaction: "discord.Interaction") -> None:
                if on_submit is not None:
                    await on_submit(interaction, self)

        modal = _Modal()
        for slot in slots[:MAX_MODAL_TEXT_INPUTS]:
            modal.add_item(_text_input_for_slot(slot))
        return modal

    def build_view(
        self,
        *,
        on_generate: Callable[..., Any] | None = None,
        on_overflow: Callable[..., Any] | None = None,
        on_boolean: Callable[[str, bool], Any] | None = None,
        on_select: Callable[[str, list[str]], Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Construct a ``discord.ui.View`` carrying select menus + buttons.

        The view holds:

        - one SelectMenu per select slot (paginated across rows; Discord
          allows 5 components per row, 5 rows).
        - one Button per boolean slot (toggle state via callback).
        - a "Generate" button that triggers ``on_generate``.
        - if the binning has overflow text slots, an "Advanced options"
          button that triggers ``on_overflow``.
        """
        import discord  # type: ignore
        from discord import ui  # type: ignore

        plan = self.build()

        class _View(ui.View):
            def __init__(self) -> None:
                super().__init__(timeout=timeout)

        view = _View()

        for slot in plan.binning.selects:
            options = plan.select_options[slot.name]
            if not options:
                continue

            default = str(slot.ui.default) if slot.ui.default is not None else None
            select_options = []
            for opt in options:
                select_options.append(
                    discord.SelectOption(
                        label=_clip(opt, 100),
                        value=_clip(opt, 100),
                        default=(default == opt),
                    )
                )

            placeholder = _clip(
                slot.ui.placeholder or f"Select {slot.ui.label}", 150
            )

            class _Select(ui.Select):
                def __init__(self, slot_name: str) -> None:
                    super().__init__(
                        placeholder=placeholder,
                        min_values=0 if not slot.ui.required else 1,
                        max_values=1,
                        options=select_options,
                        custom_id=f"v3_setup_select_{slot_name}",
                    )
                    self.slot_name = slot_name

                async def callback(
                    self, interaction: "discord.Interaction"
                ) -> None:
                    if on_select is not None:
                        await on_select(self.slot_name, list(self.values))
                    await interaction.response.defer()

            view.add_item(_Select(slot.name))

        for slot in plan.binning.booleans:
            default = bool(slot.ui.default)
            style = (
                discord.ButtonStyle.success if default else discord.ButtonStyle.secondary
            )

            class _Toggle(ui.Button):
                def __init__(self, slot_name: str, label: str, state: bool) -> None:
                    super().__init__(
                        label=f"{label}: {'on' if state else 'off'}",
                        style=style,
                        custom_id=f"v3_setup_toggle_{slot_name}",
                    )
                    self.slot_name = slot_name
                    self.state = state

                async def callback(
                    self, interaction: "discord.Interaction"
                ) -> None:
                    self.state = not self.state
                    self.label = f"{slot.ui.label}: {'on' if self.state else 'off'}"
                    self.style = (
                        discord.ButtonStyle.success
                        if self.state
                        else discord.ButtonStyle.secondary
                    )
                    if on_boolean is not None:
                        await on_boolean(self.slot_name, self.state)
                    await interaction.response.edit_message(view=view)

            view.add_item(_Toggle(slot.name, slot.ui.label, default))

        if plan.binning.has_overflow:

            class _OverflowButton(ui.Button):
                def __init__(self) -> None:
                    super().__init__(
                        label="Advanced options",
                        style=discord.ButtonStyle.secondary,
                        custom_id="v3_setup_overflow",
                    )

                async def callback(
                    self, interaction: "discord.Interaction"
                ) -> None:
                    if on_overflow is not None:
                        await on_overflow(interaction)

            view.add_item(_OverflowButton())

        class _GenerateButton(ui.Button):
            def __init__(self) -> None:
                super().__init__(
                    label="Generate",
                    style=discord.ButtonStyle.primary,
                    custom_id="v3_setup_generate",
                )

            async def callback(
                self, interaction: "discord.Interaction"
            ) -> None:
                if on_generate is not None:
                    await on_generate(interaction)

        view.add_item(_GenerateButton())
        return view


def _text_input_for_slot(slot: Slot) -> Any:
    """Convert a Slot into a ``discord.ui.TextInput``.

    Imports discord lazily so ``SlotBinning`` is testable without Discord.
    """
    import discord  # type: ignore
    from discord import ui  # type: ignore

    if slot.ui.hint == UIHint.LONG_TEXT:
        style = discord.TextStyle.paragraph
        max_length = (
            slot.validation.max_length if (slot.validation and slot.validation.max_length) else MAX_TEXT_INPUT_LENGTH
        )
        max_length = min(max_length, MAX_TEXT_INPUT_LENGTH)
    else:
        style = discord.TextStyle.short
        max_length = (
            slot.validation.max_length if (slot.validation and slot.validation.max_length) else MAX_SHORT_TEXT_LENGTH
        )
        max_length = min(max_length, MAX_SHORT_TEXT_LENGTH)

    default = slot.ui.default
    if default is None:
        default_str = None
    elif slot.ui.hint == UIHint.SEED and (
        default == "random" or default is None
    ):
        default_str = "random"
    else:
        default_str = str(default)

    return ui.TextInput(
        label=_clip(slot.ui.label, 45),
        style=style,
        placeholder=_clip(slot.ui.placeholder or "", 100) if slot.ui.placeholder else None,
        default=default_str,
        required=slot.ui.required and slot.ui.hint != UIHint.SEED,
        max_length=max_length,
        custom_id=f"v3_setup_text_{slot.name}",
    )


def _clip(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[: n - 1] + "\u2026"


__all__ = [
    "BuiltSetup",
    "MAX_MODAL_TEXT_INPUTS",
    "MAX_SELECT_OPTIONS",
    "SetupBuildError",
    "SetupBuilder",
    "SlotBinning",
]
