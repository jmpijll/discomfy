# ADR-0003: Discord Setup UI is generated from the Manifest

**Status:** accepted (v3.0 design phase, 2026-06-01)

## Context

v2.x has hand-written View / Modal / SelectMenu classes per model type:
`bot/ui/generation/modals.py`, `select_menus.py`, `complete_setup_view.py`,
each with `if model_type == "dype_flux_krea": ...` branches. The DyPE
release (v2.1.0) had to add a custom modal subclass just to expose
`dype_exponent`. Discord's 25-option select-menu cap and 5-input modal cap
have already caused user-visible bugs (LoRA dropdown overflow, fixed in
v2.1.0).

## Decision

The pre-Run **Setup** UI - modal text inputs, select menus, action buttons -
is rendered from `Manifest.slots[].ui` by a single
`core/setup/builder.py` module. There is exactly one parameterized
`SetupView`, one parameterized `SetupModal`, and one parameterized
`SlotSelectMenu` for the whole bot.

### Mapping `slots[].ui.hint` to Discord components

| `ui.hint` | Discord component | Notes |
| --- | --- | --- |
| `short_text` | `TextInput(style=short)` | <= 100 chars |
| `long_text` | `TextInput(style=paragraph)` | up to 4000 chars |
| `number` | `TextInput(style=short)` + parse-int with validation | Discord modals do not have native number inputs |
| `seed` | `TextInput(style=short)` with `default: random` placeholder | empty or `random` -> generate seed |
| `select` | `SelectMenu(options=...)` | options from `options_from` (e.g. `comfyui.loras`) |
| `select_static` | `SelectMenu(options=...)` | options listed inline in manifest |
| `boolean` | `Button` toggle in the View | modals don't support checkboxes |
| `image` | `discord.Attachment` slot on the slash command | modals don't support file pickers |

### Slot binning

Discord's modal cap is 5 `TextInput`s. The builder bins manifest slots:

1. Slots with `ui.hint in {short_text, long_text, number, seed}` go into
   the modal in declaration order until 5 are placed; overflow goes to
   the View as a button that opens a second modal page (`SetupModalNext`).
2. Slots with `ui.hint == select | select_static` become select menus
   directly on the View (Discord allows up to 5 components per row, 5
   rows; the builder paginates).
3. Slots with `ui.hint == image` are on the slash command itself, not on
   any View - Discord requires attachment slots up front. The manifest
   declares them as command parameters: `slots[].ui.attachment_position: 1`.
4. Slots with `ui.hint == boolean` become toggle buttons on the View.

### Dynamic option sources

`options_from` values resolve at View-construction time, not at bot start.
This lets the LoRA list refresh when the user adds files to ComfyUI without
restarting:

- `comfyui.loras` -> `/object_info -> LoraLoader.lora_name[0]`
- `comfyui.unets` -> ` -> UNETLoader.unet_name[0]`
- `comfyui.vaes` -> ` -> VAELoader.vae_name[0]`
- `comfyui.samplers` -> ` -> KSampler.sampler_name[0]`
- `comfyui.schedulers` -> ` -> KSampler.scheduler[0]`
- `comfyui.checkpoints` -> ` -> CheckpointLoaderSimple.ckpt_name[0]`

The 25-option Discord cap is enforced by truncation + a "Type to filter"
modal fallback: if `len(options) > 24`, the select menu shows
`[1..24] + "More... (type to filter)"`; the last option opens a text
input that the bot fuzzy-matches.

### What the bot layer still owns

- Slash command registration (one slash command per Modality, e.g.
  `/image`, `/edit`, `/video`, `/tts`, `/music`).
- Interaction lifecycle, deferral, ephemeral error responses.
- Workflow choice itself: when multiple manifests share a Modality, the
  user picks via a top-level select menu before the manifest's Setup is
  rendered.

## Consequences

- 100% of `bot/ui/generation/{modals,select_menus,complete_setup_view,
  setup_view,buttons,post_view,complete_setup_view}.py` legacy
  per-model classes are deleted.
- Adding a new slot type to the schema requires a code change in the
  builder. This is the right place for that friction; only schema-level
  changes hit code.
- Discord component caps become declarative validation: a manifest with
  > 5 short_text/number slots fails registration with a clear error
  pointing to a binning fix. The bot can't ship a UI Discord refuses to
  render.

## Rejected alternatives

- **Keep per-model modals** - the failure mode this ADR exists to remove.
- **Web admin UI to author manifests** - heavy lift, scope creep,
  contradicts "Discord-driven self-hosted bot" positioning.
- **JSON Schema for slot validation** - we use Pydantic for validation
  and a tiny custom DSL for the `ui.*` hints; full JSON Schema is
  overkill and obscures Discord-specific binning rules.
