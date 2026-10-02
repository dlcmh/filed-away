# AGENTS.md

This repository holds notes of all kinds — AI chat transcripts, summaries,
study notes, and anything else worth keeping — and everything must render
correctly on github.com.

The `notes/` folder is the main collection, classified into topic subfolders:
`notes/<topic>/<note>`. Current topics: **mathematics**, **machine-learning**,
**programming**, **hardware**, **health**, **finance**, **general**. The agent
picks the closest fit; create a new topic only when nothing fits. Notes are
either single Markdown files or subfolders with a `README.md` (chat transcripts
produced by `tools/ds2md.py` take the subfolder form because of their images;
GitHub renders each README.md as the subfolder's landing page). The collection's
`notes/README.md` is an auto-generated index of every note, newest first.

## Adding other notes by hand

Create a single Markdown file under the matching topic subfolder in `notes/`
(or a subfolder with a `README.md` if it needs images), and start it with a
top-level `# Title` — the index uses it. Then refresh the index with
`tools/ds2md.py --reindex -o notes/`; never edit `notes/README.md` directly.

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
3. Read the Gotchas section of `tools/README.md` before handling anything the
   script flags — especially partial/truncated captures and expired image URLs.
4. Convert into the collection folder the user specifies (`-o notes/`),
   passing `--topic` from the scheme above; the script creates the
   `<topic>/<slug>/` subfolder itself. Never rename or restructure existing
   notes — they are addressed by path.
5. Verify before committing: the script's self-check must pass (math fidelity
   MATCH, balanced `$`, image refs == files on disk), then skim the rendered
   result for anything structural the checks can't see.
6. Commit and push autonomously once checks pass (standing approval from the
   repo owner). Never `git add -A` — add only the new transcript folder (and
   tooling, if that is the task).

After a verified conversion the owner deletes the source conversation from
DeepSeek, which kills the share link — from that point the note (with its
locally stored images) is the only copy, so it must stay complete and
self-contained. The header's Source link is provenance and is expected to
expire.
