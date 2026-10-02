# AGENTS.md

This repository holds faithful Markdown transcripts of AI chat conversations.
Transcripts live in collection folders (e.g. `glm/`); each
conversion creates a subfolder named after the slugified transcript title,
containing `README.md` (the transcript — GitHub renders it as the subfolder's
landing page) and `images/` when the conversation has attachments. Transcripts
must render correctly on github.com.

## Adding a transcript from a chat HTML export

1. Use the converter: `tools/ds2md.py <input.html> -o <folder>/` — setup,
   options, and self-checks are documented in `tools/README.md`. Do not
   hand-transcribe: the script preserves math, spacing, and tables
   byte-faithfully and verifies its own output. It also regenerates the
   collection's `README.md` index on every conversion (or via `--reindex`) —
   refresh it that way after hand edits instead of editing the index.
2. Pass a short, descriptive `--title` derived from the conversation (a few
   words, e.g. "HS math gap: CS vs ML"). The script's automatic fallbacks —
   first-question heuristic, then the page title — are stopgaps; DeepSeek's
   own titles are auto-generated poetry. See `tools/README.md` → Title.
2. Read the Gotchas section of `tools/README.md` before handling anything the
   script flags — especially partial/truncated captures and expired image URLs.
3. Convert into the collection folder the user specifies (`-o glm/`); the
   script creates the slug-named subfolder itself. Never rename or restructure
   existing transcript folders — transcripts are addressed by path.
4. Verify before committing: the script's self-check must pass (math fidelity
   MATCH, balanced `$`, image refs == files on disk), then skim the rendered
   result for anything structural the checks can't see.
5. Commit and push autonomously once checks pass (standing approval from the
   repo owner). Never `git add -A` — add only the new transcript folder (and
   tooling, if that is the task).
