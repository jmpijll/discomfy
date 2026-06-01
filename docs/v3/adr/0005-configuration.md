# ADR-0005: Configuration is bot-level only; manifests own workflow knowledge

**Status:** accepted (v3.0 design phase, 2026-06-01)

## Context

v2.x's `config.json` mixes three concerns:

1. **Secrets and bot infra** - Discord token, ComfyUI URL, log levels.
2. **Workflow registry** - 7 to 9 hand-written entries each with a
   `model_type` magic string, `default_width`, `default_dype_exponent`,
   `supports_lora` flag, etc.
3. **Per-workflow defaults** that should live with the workflow itself.

The result: every workflow change touches `config.json` AND code AND a
JSON in `workflows/`. Migrations between v2.0 / v2.1.0 / v2.1.1 / v2.1.2
have all included `config/migration.py` patches because the workflow
registry is in the wrong place.

## Decision

`config.json` shrinks to bot-level concerns only:

```json
{
  "discord": {
    "token": "SET_VIA_ENVIRONMENT",
    "guild_id": null,
    "max_file_size_mb": 25
  },
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout_seconds": 300,
    "video_timeout_seconds": 900,
    "ws_reconnect_max_attempts": 10
  },
  "rate_limits": {
    "per_user_per_minute": 5,
    "global_per_minute": 20
  },
  "logging": {
    "level": "INFO",
    "file": "logs/bot.log",
    "max_mb": 10,
    "backup_count": 5
  },
  "manifests": {
    "directory": "workflows/manifests",
    "disabled_ids": []
  }
}
```

**Workflow knowledge** (model_type, default_width, supports_lora,
default_dype_exponent, type, ...) lives **only** in
`workflows/manifests/<id>.yaml`. There is no parallel registry in
`config.json`.

### Discoverability

- Manifests are loaded from `manifests.directory`. The bot enumerates
  them at startup and registers each one whose `requires` block validates
  against the live `/object_info`.
- A manifest can be force-disabled via `manifests.disabled_ids`. This is
  the only knob `config.json` has over the workflow registry.
- Per-environment variation (different default LoRAs in dev vs. prod)
  uses **manifest overlays** - a sibling YAML at
  `workflows/manifests/<id>.<env>.yaml` is merged on top of the base
  manifest at load time. `config.json` does not embed workflow defaults.

### Environment variables

Existing `.env` precedence is kept (env > config.json > built-in defaults)
but the env keys shrink to: `DISCORD_TOKEN`, `COMFYUI_URL`,
`COMFYUI_API_KEY` (optional), `DISCOMFY_LOG_LEVEL`, `DISCOMFY_ENV`. No
workflow knobs in env.

## Consequences

- `config/migration.py`'s "add workflow X to default registry" logic
  goes away. Adding a workflow no longer touches migration code.
- `config.example.json` is small and stable.
- Users upgrading from v2.x get a one-time auto-migration via
  `scripts/migrate_v2_to_v3_config.py` (Slice 1 deliverable in
  ADR-0006). The migration drops `workflows.*`, generates one
  manifest YAML per v2 entry that still has matching models, and warns
  about ones that don't.
- Per-deployment customization (e.g. "this Discord server defaults width
  to 1280 because it's a 16:9 community") uses an environment overlay
  YAML, NOT a code patch.

## Rejected alternatives

- **Keep workflow registry in config.json, just drop `model_type`** - the
  hardcoded default knobs (`default_dype_exponent`, etc.) still leak
  workflow knowledge into bot config. Same shape, same problems.
- **Pydantic Settings auto-generated from env only** - locks out
  non-developer admins; the bot is run by people who edit config.json.
- **TOML configuration** - YAML for manifests, JSON for bot config keeps
  one tool per role. JSON is what discord.py / ComfyUI users already
  know.
