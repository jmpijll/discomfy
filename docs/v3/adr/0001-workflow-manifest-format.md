# ADR-0001: Workflow manifests are the source of truth

**Status:** accepted (v3.0 design phase, 2026-06-01)

## Context

In v2.x, "what a workflow is" is split across three places: a JSON file in
`workflows/`, a hand-written entry in `config.json` with a magic
`model_type` string (`"flux"`, `"flux_krea"`, `"dype_flux_krea"`, ...), and
a switch statement that lives in code (`core/comfyui/workflows/updater.py`,
`core/generators/image.py`, `bot/ui/generation/{modals,select_menus}.py`,
`bot/commands/loras.py`). Adding a new workflow requires touching all
three. The static analysis (`docs/v3/workflows-static.md`) shows that the
13 existing JSONs use a small, recurring set of logical roles -
`prompt_positive`, `lora`, `latent_size`, `seed`, `output_image`,
`output_video` - and the only thing the code actually needs is a mapping
from these roles to concrete node IDs.

## Decision

A **Manifest** is a YAML file in `workflows/manifests/<id>.yaml` that
declares everything the bot needs to know about a Workflow. The ComfyUI
JSON in `workflows/` becomes pure data the Manifest points at. Code never
hardcodes node IDs, model names, or per-Workflow logic.

Manifest schema (Pydantic, formal version lives in `core/manifest/schema.py`):

```yaml
# workflows/manifests/qwen_image_2512.yaml
schema_version: 1
id: qwen_image_2512
name: "Qwen-Image 2512"
description: "Qwen 2512 with 4-step Lightning LoRA, ~10s generations"
modality: image_t2i
workflow_file: workflows/qwen_image_2512_lora.json

requires:
  packs: []                      # third-party node packs by python_module
  unets:                         # checked against /object_info on register
    - qwen_image_2512_fp8_e4m3fn_scaled_comfyui_4steps_v1.0.safetensors
  vaes: [qwen_image_vae.safetensors]
  clips: [qwen_2.5_vl_7b_fp8_scaled.safetensors]

slots:
  - name: prompt
    type: text
    role: prompt_positive
    target: { node: "18", field: "text" }
    ui: { hint: long_text, label: "Prompt", placeholder: "..." }
    validation: { min_length: 1, max_length: 2000 }
  - name: negative_prompt
    type: text
    role: prompt_negative
    target: { node: "17", field: "text" }
    ui: { hint: long_text, label: "Negative prompt", required: false }
    validation: { max_length: 2000 }
  - name: width
    type: int
    role: latent_size
    target: { node: "59", field: "width" }
    ui: { hint: number, label: "Width", default: 1024, step: 64 }
    validation: { min: 512, max: 2048, multiple_of: 64 }
  - name: height
    type: int
    role: latent_size
    target: { node: "59", field: "height" }
    ui: { hint: number, label: "Height", default: 1024, step: 64 }
    validation: { min: 512, max: 2048, multiple_of: 64 }
  - name: seed
    type: int
    role: seed
    target: { node: "8", field: "seed" }
    ui: { hint: seed, label: "Seed", default: random }
  - name: lora
    type: enum_dynamic
    role: lora
    target: { node: "122", field: "lora_name" }
    options_from: comfyui.loras   # populated from /object_info at register
    ui: { hint: select, label: "LoRA", required: false, default: none }

outputs:
  - role: output_image
    node: "13"
    media: image/png

actions:
  - id: upscale
    label: "Upscale"
    target_workflow: image_upscale_latent
    map:
      - { from_output: output_image, to_slot: source_image }
  - id: animate
    label: "Animate"
    target_workflow: video_wan22_i2v
    map:
      - { from_output: output_image, to_slot: init_image }
  - id: edit
    label: "Edit"
    target_workflow: qwen_image_edit_2511
    map:
      - { from_output: output_image, to_slot: image_1 }
```

### Mandatory schema rules

1. **`schema_version`** is required; the loader rejects manifests with an
   unknown version. Migration paths are explicit.
2. **`role`** values come from a closed enum defined in
   `core/manifest/roles.py`. New roles require a code change. This is
   intentional friction: the Plugin layer has to know what each role
   means.
3. **`target`** is a `{node, field}` pair; multi-target slots (a value
   that lands in two places, e.g. `width` for both `EmptyLatentImage` and
   `DyPE_FLUX`) use `targets: [...]` instead.
4. **`requires`** is verified against `/object_info` at startup; any
   missing UNET / VAE / CLIP / pack causes the manifest to be **disabled,
   not crashed** - the bot logs a clear warning and the workflow does not
   appear in the Discord UI.
5. **`actions[].map`** entries reference `output_role -> slot_name` of the
   target workflow's manifest. Action wiring is data-driven; no code
   changes needed to add a new chain.
6. **Multi-UNET workflows** (e.g. WAN 2.2 HIGH+LOW pair) declare two UNETs
   in `requires.unets` and two slots with `role: model_high` /
   `role: model_low` that map to two distinct UNETLoader nodes.
7. **No defaults in code.** Every default lives in the manifest under
   `slots[].ui.default`. This is the only reason a non-developer can
   tune a workflow.

## Consequences

- Adding a new workflow becomes: drop the JSON, write a manifest, restart
  the bot. Zero code changes for the typical case.
- A manifest is the canonical Discord help text source. We do not
  duplicate descriptions between `config.json`, the modal, and a README.
- Workflows whose JSON references missing models are disabled gracefully
  on startup. v2's "the bot crashes when you select a missing workflow"
  failure mode is gone.
- Per-workflow modal subclasses (currently in
  `bot/ui/generation/modals.py`) are deleted. ADR-0003 covers the
  replacement.

## Rejected alternatives

- **Embed the manifest inline in `config.json`** - keeps the v2 layout
  alive but inherits the "config.json fails one schema means whole bot
  fails to start" risk. One file per workflow lets a bad manifest
  disable just that workflow.
- **JSON manifests** - YAML wins on multi-line text fields (descriptions,
  prompts, comments) which Discord help text needs.
- **Auto-derive everything from `/object_info`** - tempting but fragile;
  the JSON's logical roles are not knowable without human authoring
  (e.g. "node 18 is the *positive* prompt encoder") because ComfyUI's
  node titles are author-set strings, not stable identifiers.
- **TOML** - acceptable, but YAML is what every other ComfyUI tool uses
  for declarative configs and the user already has muscle memory.
