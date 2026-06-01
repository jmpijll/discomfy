# ADR-0008: Optional `options_filter` regex on dynamic-select Slots

**Status:** proposed (drafted during Slice 2, 2026-06-01; not accepted)
**Supersedes:** none
**Anchors:** ADR-0001, ADR-0003

## Context

ADR-0003 wires dynamic select Slots (`type: enum_dynamic`, e.g. the LoRA
picker) to a single `options_from` source string such as
`comfyui.loras`. The shared inventory works fine when every Workflow
under a Modality is compatible with every option in the source list.

Slice 2 (issue #4) breaks that assumption. The user's live ComfyUI hosts
16 LoRAs (`docs/v3/discovery.md`): seven `qwen_image_*` LoRAs trained
against the Qwen 2512 UNET, one `Klein-consistency.safetensors` trained
against FLUX 2 Klein, and assorted WAN/LTX/Gemma helpers. Picking a
Qwen LoRA in the FLUX 2 Klein workflow loads tensors with mismatched
shape and ComfyUI errors out at execution time. The user-facing modal
should hide options that can't be valid for the selected Workflow.

The closed set of FLUX 2 Klein-compatible LoRAs is **author-known**
(`^Klein-`, `^f2k_consist_`, …); the closed set of Qwen-compatible
LoRAs is similarly author-known (`^qwen_image_`, `^Qwen-Image-`). The
manifest is the natural place to declare which side of that line the
Workflow lives on.

## Decision (proposed)

Add an optional `options_filter` field to the `Slot` schema in
`core/manifest/schema.py`. The field is a Python regex applied with
`re.search` to each dynamically-resolved option before the 25-option
Discord cap is enforced. Options whose name matches the regex are
**excluded** from the dropdown. The field has no effect on
`enum_static` slots (their options are author-supplied verbatim) and no
effect when omitted (current behaviour preserved).

```yaml
# workflows/manifests/flux2_klein.yaml
slots:
  - name: lora
    type: enum_dynamic
    role: lora
    target: { node: "4", field: "lora_name" }
    options_from: comfyui.loras
    options_filter: '^qwen_image_|^Qwen-Image-'
    ui: { hint: select, label: "LoRA", required: false }
```

`bot/setup/builder.py:SetupBuilder._resolve_select_options` performs
the filter once per `build()` call, after the inventory resolution and
before the cap. The filter is documented as an authoring affordance,
not a security boundary - the bot still validates the user's chosen
value against the manifest's `requires` and the live inventory at queue
time.

### Schema impact

- New field on `Slot`: `options_filter: str | None = None`.
- Backwards-compatible: existing manifests omit the field and validate
  unchanged.
- No `schema_version` bump. ADR-0001 reserves the bump for **breaking**
  schema changes ("manifests with an unknown version refuse to load");
  an optional additive field does not break older loaders.
- `Slot.model_config = ConfigDict(extra="forbid")` stays. We declare the
  field properly rather than relaxing the forbid.

### What this is NOT

- Not a runtime filter. ComfyUI still errors loudly if a manifest picks
  an incompatible LoRA programmatically.
- Not a sort key. The filter only removes; ordering remains the
  inventory's declared order.
- Not a per-user preference. The filter is the Workflow author's
  declared compatibility statement, not a user setting.

## Consequences

- One-line addition per affected manifest; no code change at the call
  site beyond the SetupBuilder filter pass.
- The shared `ImageT2IPlugin` continues to be agnostic to model family;
  the filter lives in declarative manifest land, not in plugin code.
- A regex typo silently empties the LoRA picker; the SetupBuilder
  should warn via the existing `overflow_truncated` channel (extend
  with `filter_excluded` counts) so operators can spot it.

## Rejected alternatives

- **Per-Modality global filter** (e.g. "image_t2i manifests filter Qwen
  LoRAs"). Coupling filter rules to Modality re-introduces the
  per-family branching ADR-0002 is built to avoid.
- **Separate LoRA folders per family** in ComfyUI itself. Operator
  hostile; requires symlink discipline on every install.
- **Sidecar `.filters.yaml`** next to each manifest. Splits Workflow
  authoring across two files for no schema gain.
- **Allow `extra` on `Slot`**. Violates the project hard rule that all
  Pydantic models declare explicit fields with `extra="forbid"`.

## Why this is a *proposed* ADR

Slice 2 was charter-bound not to touch `core/manifest/`. Slice 2 ships
the FLUX 2 Klein manifest with the full 16-LoRA picker (the seven
Qwen-only entries surface but error at execution if chosen). This ADR
documents the cleanest follow-up. Acceptance should be paired with the
schema change, the SetupBuilder filter pass, and a unit test
demonstrating `^qwen_image_|^Qwen-Image-` removes the seven Qwen LoRAs
from the FLUX 2 Klein picker while preserving `Klein-consistency`.
