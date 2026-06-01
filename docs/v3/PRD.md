# PRD: DisComfy v3.0

**Owner:** jmpijll
**Branch:** `v3.0` (long-lived, off `main` at `2c77dcc7`)
**Anchored evidence:** `CONTEXT.md`, `docs/v3/discovery.md`,
`docs/v3/workflows-static.md`, `docs/v3/scope.md`, `docs/v3/adr/`

## Problem Statement

DisComfy v2.x was supposed to be "a modular Discord bot that can adjust to
support multiple ComfyUI workflows in multiple modalities." It is not. The
current code branches on a `model_type` magic string (`"flux"`,
`"dype_flux_krea"`, ...) across 11+ files. Every new model required a code
change, a new modal subclass, a new updater branch, and a `config/migration.py`
patch. As a result:

- Of 13 workflows shipped in `workflows/`, only **one**
  (`qwen_image_2512_lora.json`) actually runs against the user's current
  ComfyUI install. The other 12 reference models the user has since
  replaced (FLUX 1 era -> FLUX 2 Klein 9B / Qwen-2512 / WAN 2.2 / LTX 2.3
  / Qwen-Edit-2511).
- Audio (TTS, music) is not supported at all, despite ComfyUI offering
  Fish-Speech S2 and ACE-Step 1.5 on the user's box.
- A v2.0 -> v2.1.0 -> v2.1.1 -> v2.1.2 chain of "add one more model"
  patches has accreted dead code (`config.py` at root, broken `bot.py`
  fallback, `htmlcov/`, `wiki-temp/`, dead deps).
- The "100% backward compatibility with v1.4.0" guarantee blocks every
  cleanup; v2 has been fixing problems caused by its own commitment to
  not change.

The user wants to "really dig deep ... so we can upgrade this project
which was made with ancient agents and models." The right answer is a
clean v3 break with a manifest-driven core.

## Solution

A workflow becomes **data, not code**. Every Workflow is described by a
**Manifest** (YAML in `workflows/manifests/`) declaring its `Modality`,
`Slots`, `NodeMap`, `Outputs`, `Actions`, and `requires` block. Code never
hardcodes node IDs, model names, or per-Workflow logic; it reads
manifests and dispatches by Modality.

Each `Modality` (image_t2i, image_edit, image_upscale, video, audio_tts,
audio_music) has exactly one Plugin that implements
`Validator/Renderer/ProgressMapper/PostActions`. Discord Setup UI is
generated from the Manifest's `slots[].ui` hints by a single parameterized
View/Modal builder. Adding a new ComfyUI workflow becomes "drop the
JSON, write a manifest, restart" - zero code changes for the typical
case. Adding a brand-new modality requires one new Plugin module.

## User Stories

### Core users (Discord end-users)

1. As a Discord user, I want to type `/image prompt:"a red panda"` and
   get an image back, so that I have a working text-to-image bot.
2. As a Discord user, I want the bot to show me which models / LoRAs are
   available _right now_, so that I don't pick something the server
   uninstalled.
3. As a Discord user, I want to click an "Upscale" button under a posted
   image, so that I can chain workflows without re-typing the prompt.
4. As a Discord user, I want to click an "Animate" button under a
   posted image, so that I can turn a still into a short video.
5. As a Discord user, I want to upload an image to `/edit` with a
   prompt, so that I can do natural-language edits.
6. As a Discord user editing with Qwen, I want to attach 1, 2, or 3
   reference images, so that I can do multi-reference edits without
   picking between three commands.
7. As a Discord user, I want to type `/video prompt:"..."` and get an MP4
   back, so that I have working text-to-video.
8. As a Discord user, I want to attach an image to `/video` to drive
   motion from a still, so that I can do image-to-video.
9. As a Discord user, I want to type `/tts text:"..."` and get spoken
   audio back, so that I have a usable TTS feature.
10. As a Discord user, I want to attach a reference voice clip to `/tts`,
    so that the bot clones my chosen voice (Fish-Speech VoiceClone).
11. As a Discord user, I want to type `/music prompt:"lo-fi beat"
    duration:30` and get an MP3 back, so that I can generate music.
12. As a Discord user, I want to see a live progress bar with a
    percentage, current node name, and ETA on every Run, so that I know
    the bot is working.
13. As a Discord user, I want errors posted as friendly Discord messages
    (not Python tracebacks), so that I can act on them.
14. As a Discord user, I want to be rate-limited fairly (5/min/user, 20/min
    global) so that one user can't starve the others.

### Operators (people running the bot)

15. As an operator, I want to add a new ComfyUI workflow by dropping a
    JSON and a YAML manifest into the repo, so that I never have to touch
    Python.
16. As an operator, I want a manifest whose required model is missing on
    ComfyUI to fail registration with a clear log line, so that I can
    fix the install instead of debugging cryptic ComfyUI errors at Run
    time.
17. As an operator, I want a `--dry-run` validate command that checks
    every manifest against the live `/object_info`, so that I can verify
    a deployment without enqueueing real work.
18. As an operator upgrading from v2.x, I want to run
    `python scripts/migrate_v2_to_v3_config.py`, so that my old
    `config.json` and surviving `workflows/*.json` become v3 manifests
    automatically with a migration report.
19. As an operator, I want per-environment manifest overlays
    (`<id>.dev.yaml` merged on top of `<id>.yaml`), so that I can change
    defaults without forking a manifest.
20. As an operator, I want one Discord file_size_mb knob, one rate-limit
    pair, and one ComfyUI URL in `config.json`, and **nothing else** about
    workflows in `config.json`, so that "what workflows exist" is
    answered by `ls workflows/manifests`.
21. As an operator, I want logs that show me the manifest id, prompt id,
    and Discord author id for every Run, so that I can correlate user
    reports with ComfyUI logs.

### Developers (people contributing)

22. As a developer adding a new Modality, I want to write one Plugin
    module against the `ModalityPlugin` Protocol and have the bot pick
    it up via the registry, so that I never edit a switch statement.
23. As a developer, I want unit tests for each Plugin that pass without
    a running ComfyUI, so that CI is fast and reliable.
24. As a developer, I want the manifest schema typed with Pydantic, so
    that bad manifests fail fast with a precise error.
25. As a developer reading the codebase six months from now, I want
    `CONTEXT.md` to tell me what "Slot" / "NodeMap" / "Run" mean, so that
    I don't have to reverse-engineer terminology.

### Reliability & migration

26. As an operator on v2.1.2, I want `main` to keep working unchanged
    until v3.0 is parity-tested, so that nothing breaks for me during
    the redesign.
27. As an operator cutting over to v3.0, I want a `MIGRATION-REPORT.md`
    listing every v2 workflow that was dropped and why, so that I know
    what changed.
28. As an operator who depends on a workflow that v3.0 dropped because
    the model is missing, I want a clear pointer to the manifest schema
    so I can re-author it once I reinstall the model.

## Implementation Decisions

(Anchors: ADR-0001..0007 plus `CONTEXT.md`.)

### Manifests are the source of truth (ADR-0001)

- One YAML per Workflow at `workflows/manifests/<id>.yaml`.
- Schema versioned (`schema_version: 1`); unknown versions refuse to
  load.
- Slots declare `{name, type, role, target: {node, field}, ui, validation}`;
  multi-target slots use `targets: [...]`.
- `requires` block lists `unets, vaes, clips, loras, packs`; all are
  validated against `/object_info` at startup. A missing dep DISABLES
  the manifest (logged), it does not crash the bot.
- Actions reference target manifests by id and map source-output role
  to target-slot name. No code in the chain.
- Multi-UNET workflows (WAN 2.2 HIGH+LOW) use two slots with
  `role: model_high` / `role: model_low`. Roles are a closed enum in
  `core/manifest/roles.py`; new roles cost a code change deliberately.

### Modality plugins replace per-model branching (ADR-0002)

- `core/modalities/<modality>/__init__.py` exposes a class implementing
  `ModalityPlugin` Protocol.
- The Modality Registry binds each `Modality` enum value to one Plugin.
- Plugins know about output media, validation rules, Discord rendering,
  progress mapping, and default post-Run actions. **They do not know
  about specific models.**
- Six Plugins ship in v3.0: `image_t2i`, `image_edit`, `image_upscale`,
  `video`, `audio_tts`, `audio_music`.

### Discord UI is generated from manifests (ADR-0003)

- One `SetupView`, one `SetupModal`, one `SlotSelectMenu` for the entire
  bot. They consume `Manifest.slots[].ui`.
- `ui.hint` -> Discord component table is in ADR-0003.
- Discord caps (5 modal text inputs, 25 select options, 25 MB file size)
  are enforced by the builder; manifests that would render an illegal UI
  fail registration.
- Dynamic `options_from` resolves at View-construction time from the
  capability inventory, so LoRA / sampler / scheduler lists refresh
  without restart.

### Thin ComfyUI client (ADR-0004)

- `core/comfyui/http.py` (aiohttp), `core/comfyui/ws.py` (websockets),
  `core/comfyui/capability.py` (typed view of `/object_info`). Nothing
  else exposed from the package.
- Workflow application is `apply_slots(workflow, manifest, values) -> dict`,
  a pure function. No `WorkflowUpdater` god class.
- No PyPI ComfyUI client wrapper; our footprint stays small and current.

### Configuration shrinks to bot-only (ADR-0005)

- `config.json` covers Discord, ComfyUI URL/timeouts, rate limits,
  logging, manifest directory + disabled ids. Nothing about workflows.
- `manifests.disabled_ids` is the only operator switch on the registry.
- Per-env overlays via sibling YAML files (no env-specific code).

### Clean break with one-shot migration (ADR-0006)

- v3.0 ships from `v3.0` branch; `main` stays on v2.1.x until parity.
- No in-process fallbacks; v3 boots from the manifest registry or it
  doesn't boot.
- `scripts/migrate_v2_to_v3_config.py` reads v2 `config.json` +
  `workflows/*.json` and emits a v3 `config.json` plus per-workflow
  manifests, dropping entries whose models are missing with a
  `MIGRATION-REPORT.md` explaining each drop.

### Audio picks anchored to install (ADR-0007)

- TTS: Fish-Speech S2 (`FishS2TTS` simple, `FishS2VoiceCloneTTS` clone).
  F5-TTS is **not installed**, contrary to the original plan guess.
- Music: ACE-Step 1.5 (`EmptyAceStep1.5LatentAudio` +
  `TextEncodeAceStepAudio1.5` + KSampler + `VAEDecodeAudio` + `SaveAudioMP3`).
- Stable Audio Open deferred (checkpoint not provisioned).

### What the manifest YAML looks like (excerpt from ADR-0001)

```yaml
schema_version: 1
id: qwen_image_2512
name: "Qwen-Image 2512"
modality: image_t2i
workflow_file: workflows/qwen_image_2512_lora.json
requires:
  unets: [qwen_image_2512_fp8_e4m3fn_scaled_comfyui_4steps_v1.0.safetensors]
  vaes: [qwen_image_vae.safetensors]
  clips: [qwen_2.5_vl_7b_fp8_scaled.safetensors]
slots:
  - { name: prompt, type: text, role: prompt_positive,
      target: { node: "18", field: "text" },
      ui: { hint: long_text, label: "Prompt" } }
  # ...
outputs:
  - { role: output_image, node: "13", media: image/png }
actions:
  - { id: upscale, target_workflow: image_upscale_latent,
      map: [ { from_output: output_image, to_slot: source_image } ] }
```

(Came from the Phase 2 ADR; this snippet is the schema-anchor.)

## Testing Decisions

### What makes a good test in this project

A good test exercises **external behaviour** through the highest seam
that doesn't need ComfyUI:

- Manifest loading: input YAML, output `Manifest` dataclass + accept/reject.
- Slot validation: input `(manifest, raw_values)`, output canonical values
  or a typed validation error.
- Slot application: input `(workflow_dict, manifest, values)`, output
  workflow_dict ready to send. Pure function; trivially tested.
- ComfyUI capability check: stub `/object_info` JSON, assert the
  inventory exposes the right helpers.
- Plugin renderers: input a fake `Run` with synthetic outputs, assert
  the produced `DiscordPayload` has the right embeds and file shapes.
- Progress mapper: input a stream of WS events, assert the percentage
  series matches expectations.
- The Discord layer (slash commands, modal flow, button clicks) is
  tested via the existing `tests/test_command_handlers.py` style with
  mocked `discord.Interaction`.

### What we do NOT test

- "Did ComfyUI generate a good picture?" - ComfyUI is a third-party,
  GPU-bound service; we test our wiring and our payloads, not its
  outputs.
- Internal helper signatures. Tests survive refactors; they don't pin
  implementation.

### Modules tested

| module | seam | prior art |
| --- | --- | --- |
| `core/manifest/loader.py` | YAML -> Manifest | `tests/test_workflow_manager.py` |
| `core/manifest/applier.py` | apply_slots pure function | none yet (new) |
| `core/comfyui/capability.py` | `/object_info` JSON -> Inventory | `tests/test_comfyui_client.py` |
| `core/modalities/<m>/plugin.py` | Plugin Protocol | `tests/test_generators.py` |
| `bot/setup/builder.py` | Manifest -> Discord components | new |
| `bot/commands/*.py` | Mocked Interaction -> handler call | `tests/test_command_handlers.py` |
| `scripts/migrate_v2_to_v3_config.py` | golden v2 config -> v3 + report | new |

### Live integration test

One end-to-end smoke test runs the tracer-bullet manifest (Slice 1) from
slash command -> Setup -> ComfyUI queue -> WS progress -> Discord post.
Requires ComfyUI reachable. Marked `@pytest.mark.integration`, skipped
in CI unless `DISCOMFY_INTEGRATION=1` is set, run manually before each
Slice merge. This is the only test that touches the real ComfyUI.

## Success Criteria

v3.0 ships when:

1. Adding a new Workflow requires writing **only** a manifest YAML and a
   ComfyUI JSON (verified by completing Slice 1 with one manifest commit).
2. All six Modalities (image_t2i, image_edit, image_upscale, video,
   audio_tts, audio_music) have at least one runnable manifest.
3. `git grep -E 'model_type|DyPE|hidream|krea' -- ':!docs/'` returns zero
   matches in code (legacy strings allowed in changelog/docs).
4. `pytest` passes with at least the same coverage as v2.1.2 (target:
   no regression below the current 93/93).
5. The migration script applied to the user's v2.1.2 `config.json`
   produces a v3 `config.json` + a manifest set + a `MIGRATION-REPORT.md`
   that the user signs off on.
6. A live Discord smoke against the user's ComfyUI succeeds for at least:
   one image t2i, one image edit, one upscale, one video i2v, one TTS,
   one music generation. Recorded in `docs/v3/parity-report.md`.

## Out of Scope

- **Text-output modality** (chat, captioning) - bot stays generation-only;
  vision nodes may be used internally for prompt expansion in v3.x.
- **External API modalities** (ElevenLabs / Stability / BFL / Recraft /
  Vidu / Bytedance / Kling). Self-hosted ComfyUI only.
- **HiDream, ZI Turbo, FLUX 1 (dev / krea / DyPE-on-krea)** - models are
  no longer installed; corresponding workflow JSONs deleted in Slice 9.
- **Two of the three near-duplicate `qwen_image_edit_*.json` files** -
  merged into one parameterized manifest (Slice 3).
- **A web admin UI for authoring manifests** - the YAML files are the UI.
- **AnimateDiff / Mochi / Cosmos / HunyuanVideo** - nodes installed but
  user's checkpoints not provisioned. Reassess in v3.x.
- **Stable Audio Open as the music default** - checkpoint not provisioned;
  ACE-Step is the v3.0 pick (ADR-0007).
- **A "v2 compatibility mode"** - clean break per ADR-0006.

## Risks

| risk | likelihood | mitigation |
| --- | --- | --- |
| Discord 25-option select-menu cap breaks LoRA picker | medium | builder enforces cap with truncation + filter overflow (ADR-0003); tracer-bullet manifest in Slice 1 hits the LoRA picker |
| Wan 2.2 i2v VRAM (HIGH+LOW models, 16-frame batches) exceeds 32 GB | medium | Slice 5 includes a smoke against the user's actual install; if it OOMs, fall back to Wan 2.1 GGUF (already proven in v2 video workflow) and document |
| Fish-Speech voice clone refuses some attached audio formats | low | manifest declares accepted MIME types; bot transcodes via ffmpeg before upload |
| Migration script drops a workflow the user wanted to keep | medium | report is human-readable; user reviews before deleting v2 JSONs (Slice 9 is gated on user sign-off) |
| `/object_info` parse breaks on a future ComfyUI upgrade | low | `capability.py` is the single point of fragility; changes there are the only ComfyUI-tracking maintenance |
| Audio file > 25 MB Discord cap | low | ACE-Step + Fish-Speech outputs at default settings are < 5 MB; longer durations in v3.x will need chunked upload or external link |

## Further Notes

- This PRD is the single source of truth for Phase 4. `to-issues` reads
  it and the ADRs to slice the work into vertical-slice GitHub issues.
- The slice ordering is locked: tracer-bullet first (Slice 1), then
  parallel migrations within a Modality, then deletion of v2 paths
  (Slice 9), then release (Slice 10).
- Each slice issue references this PRD and the relevant ADR(s) by id.
- `CONTEXT.md` is the project-wide glossary. PRD prose uses those terms;
  reviewers should call out any drift.
- Cursor Cloud agents picking up issues run `/handoff` between sessions
  and `/tdd` per behaviour. `/review` runs against this PRD on each PR.
