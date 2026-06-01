# ADR-0004: Thin ComfyUI client; capability checks via /object_info

**Status:** accepted (v3.0 design phase, 2026-06-01)

## Context

v2.x has `core/comfyui/client.py` (HTTP, aiohttp), `core/comfyui/websocket.py`
(WS, `websockets`), and a `WorkflowUpdater` that mutates dict-of-dict
node graphs. The HTTP and WS pieces are sound; the breakage is that the
Updater knows about specific node IDs and `class_type`s, which makes it a
parallel switch statement.

The live ComfyUI probe (2026-06-01) confirmed:

- `/system_stats`, `/object_info`, `/embeddings`, `/queue`, `/prompt`,
  `/history/{prompt_id}`, `/view?filename=...&type=output` all behave as
  documented.
- `/object_info` returns a 6.3 MB JSON enumerating 2471 nodes. Per-input
  option arrays (e.g. `LoraLoader.lora_name[0]`) are the canonical source
  for "what's installed".
- WebSocket on `/ws?clientId=<uuid>` emits `executing`, `progress`,
  `execution_complete`, `executed`, plus binary frames for previews.

## Decision

`core/comfyui/` exposes three modules and nothing else from the public
package:

1. **`core/comfyui/http.py`** - aiohttp wrapper. One method per ComfyUI
   endpoint (`queue_prompt`, `get_history`, `get_view`, `get_object_info`,
   `get_system_stats`, `get_queue`, `upload_image`, `upload_audio`).
   Connection pooling via singleton `aiohttp.ClientSession` per process.
   No retries inside this layer; retries are a Run-level concern (ADR-0006).
2. **`core/comfyui/ws.py`** - WebSocket consumer. Returns an `AsyncIterator[Event]`
   typed-with-Pydantic events: `Executing`, `Progress`, `ExecutionComplete`,
   `ExecutionError`, `BinaryPreview`. Reconnects on `WebSocketException`
   with exponential backoff but yields a `Reconnected` event so the
   ProgressMapper can resync.
3. **`core/comfyui/capability.py`** - typed view of `/object_info`.
   Provides `inventory.unets()`, `inventory.loras()`, `inventory.has_node(name)`,
   `inventory.has_pack("ComfyUI-WanVideoWrapper")`. Refreshable on demand;
   does NOT cache forever.

### Workflow application is data, not code

The v2 `WorkflowUpdater` is replaced by `core/manifest/applier.py`:

```python
def apply_slots(workflow: dict, manifest: Manifest, values: SlotValues) -> dict:
    """Pure function: clone the workflow JSON, write each slot value to its
    manifest-declared (node, field), return the new workflow ready to POST
    to /prompt. Knows nothing about FLUX / Qwen / WAN."""
```

Multi-target slots (one value into two nodes - `width` into
`EmptyLatentImage` AND `DyPE_FLUX`) are supported via `targets: [...]` in
the manifest. Multi-output Runs (a workflow that produces both a video
and a thumbnail image) are supported via `outputs: [...]` of differing
roles.

### What we do NOT use

- **`comfy_api_simplified` / `comfyclient` PyPI packages** - extra
  dependency, less control, often lag the live API. Our footprint is < 200
  lines; not worth the dependency.
- **Auto-generated TypedDicts from `/object_info`** - tempting but the
  schema is a moving target. The `capability` module exposes runtime
  helpers, not generated types.
- **A node-graph DSL** - we treat ComfyUI JSON as opaque data and only
  poke through manifest-declared node IDs. Anyone wanting a programmatic
  graph can edit ComfyUI in its native UI and export the JSON.

## Consequences

- Network code does not branch on model. The ImageGenerator /
  VideoGenerator split goes away; both become Plugin + manifest +
  `applier` + `http` + `ws`.
- Capability checks are honest: a manifest's `requires` block is verified
  before queueing a Run. v2's "queue first, fail with a cryptic ComfyUI
  error" pattern is replaced with a startup-time disable.
- The `Inventory` is a thin object that any test can stub; Plugins can
  be unit-tested without ComfyUI by passing a `FakeInventory`.

## Rejected alternatives

- **Keep `WorkflowUpdater` and add per-modality methods** - just splits
  the switch statement across files.
- **Replace HTTP+WS with a single WS-only client** - WS doesn't carry
  history reads or model uploads. We'd reinvent HTTP.
- **Synchronous client** - the bot is async-first (discord.py is async).
  No reason to pay for a thread pool.
