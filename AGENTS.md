# AGENTS.md

This repository holds faithful Markdown transcripts of AI chat conversations.
One folder per transcript (e.g. `deepseek/`, `glm/`), each containing a single
`.md` file and its images under `images/`. Transcripts must render correctly
on github.com.

## Adding a transcript from a chat HTML export

1. Use the converter: `tools/ds2md.py <input.html> -o <folder>/` — setup,
   options, and self-checks are documented in `tools/README.md`. Do not
   hand-transcribe: the script preserves math, spacing, and tables
   byte-faithfully and verifies its own output.
2. Read the Gotchas section of `tools/README.md` before handling anything the
   script flags — especially partial/truncated captures and expired image URLs.
3. Choose the output folder name with the user (existing convention: one
   folder per transcript). Never rename or restructure existing folders —
   transcripts are addressed by path.
4. Verify before committing: the script's self-check must pass (math fidelity
   MATCH, balanced `$`, image refs == files on disk), then skim the rendered
   result for anything structural the checks can't see.
5. Commit and push autonomously once checks pass (standing approval from the
   repo owner). Never `git add -A` — add only the new transcript folder (and
   tooling, if that is the task).
