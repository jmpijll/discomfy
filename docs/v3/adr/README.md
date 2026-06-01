# DisComfy v3.0 - ADRs

Architectural Decision Records for the v3.0 redesign. Read in order.

| # | Title | Status |
| --- | --- | --- |
| [0001](./0001-workflow-manifest-format.md) | Workflow manifests are the source of truth | accepted |
| [0002](./0002-modality-plugin-interface.md) | Modality plugins, not per-model branches | accepted |
| [0003](./0003-discord-ui-from-manifest.md) | Discord Setup UI is generated from the Manifest | accepted |
| [0004](./0004-comfyui-client-layer.md) | Thin ComfyUI client; capability checks via `/object_info` | accepted |
| [0005](./0005-configuration.md) | Configuration is bot-level only; manifests own workflow knowledge | accepted |
| [0006](./0006-backward-compatibility.md) | v3.0 is a clean break with a one-shot migration script | accepted |
| [0007](./0007-audio-modality-picks.md) | Audio modality - Fish-Speech for TTS, ACE-Step for music | accepted |

The accepted decisions are anchored to evidence in `../discovery.md`,
`../workflows-static.md`, and `../scope.md`. If a decision is reversed,
supersede the ADR rather than editing it; the audit trail is the value.

## When v3.0 ships

These ADRs may be moved from `docs/v3/adr/` to `docs/adr/` (project-wide)
since they represent the canonical architecture, not a transient design
phase. The directory move is mechanical and does not change content.
