# Domain docs

Single-context repository.

- **Glossary:** [`CONTEXT.md`](../../CONTEXT.md) at the repo root.
  Use these terms verbatim in issue titles, PR descriptions, test
  names, and code identifiers. Synonyms listed under `_Avoid_` must
  not appear in code.
- **ADRs:** [`docs/v3/adr/`](../v3/adr/) for the v3 redesign. Will move
  to `docs/adr/` (project-canon) in Slice 10. Read every ADR that
  touches the area you're working in before writing code.
- **PRD:** [`docs/v3/PRD.md`](../v3/PRD.md) is the source of truth for
  what v3.0 ships. Treat it as the contract slices implement.
- **Discovery:** [`docs/v3/discovery.md`](../v3/discovery.md),
  [`docs/v3/workflows-static.md`](../v3/workflows-static.md), and
  [`docs/v3/scope.md`](../v3/scope.md) are evidence sources for the
  PRD and ADRs. Regenerate via `scripts/discover_comfyui.py` and
  `scripts/analyze_workflows.py`.

## Flagging ADR conflicts

If a slice naturally drifts into contradicting an ADR, do not silently
override. Surface it: open a comment on the slice issue saying
"Contradicts ADR-XXXX because <reason>; proposing supersede." Then
either write a new ADR (numbered next-in-sequence with status
`accepted`, marking the old one `superseded by ADR-XXXX`) or revise
the slice plan to fit the existing ADR.
