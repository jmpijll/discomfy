# DisComfy

A Discord bot that runs ComfyUI workflows for users. v3.0 reframes the bot as
a thin transport layer between Discord and ComfyUI, with workflows expressed as
declarative manifests so adding a new workflow needs zero code changes.

## Language

### Core abstractions (v3 design)

**Workflow**:
A ComfyUI graph saved as JSON in `workflows/` plus its companion `Manifest`. A
Workflow always belongs to exactly one `Modality`.
_Avoid_: pipeline, graph, recipe, model, generator.

**Manifest**:
A YAML file in `workflows/manifests/` describing how a Workflow is exposed to
users: its `Modality`, its `Slots`, its `NodeMap`, its post-`Run` `Actions`, and
the `Pack`s it requires from ComfyUI. The Manifest is the source of truth; the
ComfyUI JSON is data the Manifest points at.
_Avoid_: schema, descriptor, config, definition, model_type.

**Modality**:
The output kind a Workflow produces. v3 ships four: `image`, `video`, `audio`,
and `upscale` (treated as its own Modality even though it outputs an image —
because its `Slot`s, `Renderer`, and `Action`s differ from `image_t2i`). Each
Modality has exactly one `Plugin`.
_Avoid_: type, kind, category, output_type.

**Slot**:
A user-facing parameter of a Workflow declared in the Manifest. Each Slot has
a name, a type, validation, an optional UI hint, and a `NodeMap` target that
says where the value lands in the ComfyUI JSON before queueing.
_Avoid_: parameter, input, field, argument.

**NodeMap**:
The Manifest's mapping from logical roles (`prompt_positive`, `lora`, `seed`,
`latent_size`, `output_image`, ...) to concrete ComfyUI node IDs in the
Workflow's JSON. NodeMap entries are how the bot knows which node to mutate
for a given Slot.
_Avoid_: nodes, bindings, ids, lookup.

**Run**:
A single end-to-end execution of a Workflow triggered by a Discord interaction.
A Run has an `Author` (the Discord user), a `Status` (queued, running,
succeeded, failed, cancelled), `Slot` values, a `Progress` stream, and zero or
more `Output`s.
_Avoid_: job, task, request, generation, invocation.

**Output**:
A file produced by a Run. Each Output has a Modality-determined MIME type, a
size, and is delivered to Discord by the Modality's `Renderer`.
_Avoid_: result, artifact, file, attachment.

**Action**:
A post-Run interaction (button) declared in a Manifest, e.g. "Upscale this
image", "Animate this image", "Edit this image". Each Action triggers a new
Run, often on a different Workflow, with the previous Run's Output(s) feeding
into specific Slots of the new Run.
_Avoid_: button, follow-up, next step.

**Plugin**:
The code module implementing one Modality. A Plugin exposes four interfaces:
`Validator` (Slot value validation), `Renderer` (turning Outputs into a
Discord message), `ProgressMapper` (turning ComfyUI WebSocket events into a
user-facing percentage), and `PostActions` (default Actions for this Modality).
_Avoid_: handler, adapter, driver, processor.

**Pack**:
A ComfyUI custom node bundle (e.g. `ComfyUI-Wan`, `ComfyUI-DyPE`,
`ComfyUI-VideoHelperSuite`). Manifests declare their required Packs; the bot
verifies them against ComfyUI's `/object_info` at startup and refuses to
register Manifests whose Packs are missing.
_Avoid_: extension, plugin (overloaded — Plugin is for our own modules), node
pack, dependency.

### ComfyUI surface

**ComfyUI**:
The external GPU-bound image/video/audio inference server we drive. Reachable
via HTTP (REST + uploads) and WebSocket (progress).

**Queue**:
ComfyUI's internal job queue, accessed via `/prompt` (enqueue) and `/queue`
(inspect). Each enqueued workflow gets a `prompt_id` we use to track a Run.
_Avoid_: jobs, batch.

**Progress**:
The stream of `executing`, `progress`, and `execution_complete` WebSocket
messages emitted by ComfyUI for a `prompt_id`. The Plugin's ProgressMapper
turns this into a Discord-rendered percentage.
_Avoid_: status updates, events.

### Discord surface

**Author**:
The Discord user who triggered the Run. Distinct from anyone clicking an
Action button on a posted Output (those clicks become new Runs with their own
Author).
_Avoid_: user, requester, owner.

**Channel**:
The Discord text channel a Run was triggered in. Outputs and Progress messages
are posted here.
_Avoid_: room, conversation.

**Setup**:
The pre-Run Discord UI (modal + select menus + buttons) generated _from the
Manifest's Slots_, used to gather Slot values from the Author. v2 hardcoded
one Setup view per model_type; v3 generates Setup from Manifest.
_Avoid_: form, prompt UI, modal, configurator.

## Out of scope for the glossary

These are general programming concepts, not DisComfy concepts, and do not
belong in CONTEXT.md even though the codebase uses them: rate limit, cache,
session, retry, timeout, logger, validator (the abstract pattern, distinct
from the Modality interface above), config, factory, registry.
