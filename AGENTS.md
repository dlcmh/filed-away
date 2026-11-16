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
GitHub renders each `README.md` as the subfolder's landing page). The
collection's `notes/README.md` is an auto-generated index of every note, newest
first.

## Writing style

Write in a formal technical register suitable for university-level prose:
avoid anthropomorphic or colloquial framing — no "lies", "honest(ly)",
"eats", "footgun", "garbage", or ascribing intent to code and compilers.
State the behavior and the consequence directly instead ("is
mathematically inconsistent", "truncates", "produces an implicit
conversion"). This applies to hand-written notes and to titles/descriptions
given to the converter. Transcript bodies follow the separate light-copyedit
rule below.

Escape literal dollar signs in hand-written prose (`\$1.4 trillion`). An
unescaped `$` opens an inline-math span on GitHub and corrupts the rest of the
line. `tools/ds2md.py` does this automatically for converted transcripts.

## Adding a note by hand

Create a single Markdown file under the matching topic subfolder in `notes/`
(or a subfolder with a `README.md` if it needs images) and start it with a
top-level `# Title` — the index uses it. Then refresh the index with
`tools/ds2md.py --reindex -o notes/`; never edit `notes/README.md` directly.

## Adding a transcript from a conversation

**Input is either a live share URL or an HTML export.** Both paths end in the
same converter; do not hand-transcribe.

1. **Capture, if the input is a URL.** Run
   `node tools/fetch_share.js <share-url> -o /tmp/chat.html`. It drives the
   installed Chrome headless, scrolls the virtualized list to the end, and
   writes a standalone export with the page title and `og:url`. Setup and the
   correctness rules are in `tools/README.md` → Recovering a full
   conversation. Capture and convert in the same session: attachment URLs are
   signed and expire.
2. **Convert.** `tools/ds2md.py <input.html> -o notes/ --topic <topic>
   --title "..." --description "..."`. The script preserves math, spacing,
   tables, citations, and attachments byte-faithfully, verifies its own output,
   and regenerates `notes/README.md`. Setup is in `tools/README.md`.
3. **Choose the title.** Pass a short, descriptive `--title` derived from the
   conversation (a few words). The script's fallbacks — first-question
   heuristic, then the page title — are stopgaps; DeepSeek's own titles are
   auto-generated poetry. Every submitted export is standalone: never assert a
   relationship to earlier exports or notes, in titles, descriptions, or
   commentary.
4. **Check.** All four self-checks must pass (math fidelity `MATCH`, `$`
   balance, display fences, image refs == files on disk). Read the Gotchas
   section of `tools/README.md` before handling anything the script flags —
   especially partial or truncated captures, and expired image URLs, where a
   low item count can mean truncation or a deliberate subset. Grep the output
   for a distinctive chain-of-thought phrase; it must come up empty.
5. **Copyedit.** Review the transcript for spelling, punctuation,
   capitalization, and grammar, without changing meaning, tone, order,
   structure, code, commands, URLs, or technical claims. Do not summarize or
   rewrite passages. The converter remains the source; the copyedit is a
   post-conversion step.
6. **Commit.** After the checks pass and the rendered result has been skimmed,
   commit and push autonomously (standing approval from the repo owner). Never
   `git add -A` — add only the new transcript folder, the regenerated index,
   and tooling if that is the task.

Never rename or restructure existing notes — they are addressed by path.

## Synthesizing an article from a conversation

When the owner asks for an article, summary, or thematic reorganization rather
than a transcript, the content still comes from a verified conversion:

1. Capture and convert exactly as above, so the source is complete, the math
   is exact, and the chain-of-thought and image rules have been applied.
2. Reorganize the converted text by subject rather than by turn: one `##`
   section per theme, prose in the formal register, no second person and no
   question-and-answer structure.
3. Preserve every quantitative claim, named source, and attribution. Keep the
   conversation's own epistemic status: anything the source called a rumour
   stays marked as a rumour, with the competing figures if they differ.
4. Keep the conversation's images unless the owner asked to omit them, and
   record the share URL in the header as provenance — it is expected to
   expire, and the note is the archive.
5. File it as a single Markdown file under the topic subfolder, keep the
   converter's index refresh, and commit as above.

If the owner later wants the full question-and-answer record instead, the
converted transcript is the artifact to commit; the article is a reading of
it, not a substitute.

## Preserving conversation images

Screenshots and other images attached to a conversation are part of the note by
default. Unless the user explicitly asks to omit them, download each attachment
before its signed URL expires, store it under the note's `images/` directory,
and reference it from the Markdown. The converter does this during conversion
for both exports and captures, so a URL input converted in the same session
loses nothing. `--skip-images` is the explicit opt-out.

If an image cannot be retrieved, state that in the note and report it to the
user; do not silently drop it. Interface chrome — favicons, source-card
thumbnails, avatars, and similar page decoration — is not conversation content
and may be omitted.

## After the note is committed

A verified note is the archive. The owner deletes the source conversation from
DeepSeek, which kills the share link, so the note and its locally stored images
become the only copy and must stay complete and self-contained. The header's
Source link is provenance and is expected to expire; never rely on it for
content.
