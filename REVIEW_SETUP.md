# Review System Setup

## What this is

Four architectural review prompts packaged as Claude Code slash commands.
No agents, no infrastructure, no dependencies beyond Claude Code itself.

## Setup (one time, 2 minutes)

1. Copy `CLAUDE.md` to your project root (or merge into existing one)
2. Create the reviews directory:
   ```bash
   mkdir -p reviews
   echo "*.json" >> reviews/.gitignore  # optional: keep reviews out of git
   ```
3. Adjust the paths in CLAUDE.md if your project structure differs:
   - `docs/architecture/pipeline_overview.puml` → your diagram path
   - `src/` → your source code directory
   - `src/prompts/` → where you keep LLM prompt templates

## Usage

Open Claude Code in your project directory, then:

```bash
# Individual reviews
/review diagram        # Is the diagram internally sound?
/review code           # Is the code well-written?
/review consistency    # Do diagram and code agree?
/review architecture   # Is the overall approach right?
/review project        # Does the repo look professional?

# Run everything
/review all
```

Findings land in `reviews/` as timestamped JSON files.

## Execution order

Run diagram + code first (independent, can be parallel).
Fix CRITICAL and MAJOR findings. Then run consistency.
Fix CRITICAL and MAJOR. Then run architecture + project (parallel).

```
diagram ──┐
           ├── fix ── consistency ── fix ──┬── architecture
code    ──┘                                └── project
```

## When to upgrade beyond this

You'll know it's time to build a script or automation when:
- You're running `/review all` more than twice a week
- You want to diff findings between runs
- You want to track finding resolution over time
- Multiple people need to run the same reviews

Until then, this is enough.
