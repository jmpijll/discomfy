"""v3 Setup UI builder (ADR-0003).

Generates one Discord View + Modal per Manifest from
``Manifest.slots[].ui`` hints. There is exactly one
:class:`~bot.setup.builder.SetupBuilder`; per-Workflow modal subclasses
are gone (ADR-0003).
"""

from bot.setup.builder import (
    BuiltSetup,
    SetupBuilder,
    SetupBuildError,
    SlotBinning,
)

__all__ = [
    "BuiltSetup",
    "SetupBuilder",
    "SetupBuildError",
    "SlotBinning",
]
