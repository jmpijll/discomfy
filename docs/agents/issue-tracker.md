# Issue tracker: GitHub

Issues, PRDs, and slice tracking for `jmpijll/discomfy` live on GitHub.
Use the `gh` CLI for all operations.

## Conventions

- **Create issue:** `gh issue create -R jmpijll/discomfy --title "..." --body "$(cat <<'EOF'\n...\nEOF\n)"`
- **Read issue:** `gh issue view <N> -R jmpijll/discomfy --comments`
- **List v3 issues:** `gh issue list -R jmpijll/discomfy -l v3.0 --json number,title,labels,milestone --jq '.'`
- **Comment:** `gh issue comment <N> -R jmpijll/discomfy --body "..."`
- **Apply / remove labels:** `gh issue edit <N> -R jmpijll/discomfy --add-label "..."` / `--remove-label "..."`
- **Close:** `gh issue close <N> -R jmpijll/discomfy --comment "..."`
- **Milestone:** `v3.0.0` is `gh api repos/jmpijll/discomfy/milestones/1`. Set with `gh issue edit <N> --milestone v3.0.0`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue on `jmpijll/discomfy`. Apply `v3.0` + `slice` +
either `ready-for-agent` or `hitl` per the slice's nature.

## When a skill says "fetch the relevant ticket"

`gh issue view <N> -R jmpijll/discomfy --comments`.
