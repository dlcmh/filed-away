# tools/ — chat-export → Markdown transcript converter

`ds2md.py` converts a DeepSeek chat HTML export (a `chat.deepseek.com/share/…`
page or an app-side save) into a faithful, GitHub-renderable Markdown
transcript: original LaTeX math, tables, numbered web citations, and attached
screenshots. It self-checks its own output and exits non-zero on failure.

**Do not hand-transcribe.** Every conversion rule in the script encodes a
rendering failure that was hit in practice — the Gotchas section below
explains what and why.

## Setup (once per machine)

Converter (Python):

```sh
python3 -m venv /tmp/dsenv
/tmp/dsenv/bin/pip install -r tools/requirements.txt
```

Share-page capture (Node, used only when the input is a live URL):

```sh
cd tools && npm install
```

`fetch_share.js` drives the installed Google Chrome through Playwright
(falling back to Playwright's bundled Chromium), so no browser download is
needed on a machine that has Chrome. The capture runs headless by default.

## Convert

```sh
/tmp/dsenv/bin/python tools/ds2md.py ~/Desktop/chat.html -o notes/ \
    --title "HS math gap: CS vs ML" \
    --description "One-line summary of what the conversation covers"
```

Outputs `<out-dir>/[<topic>/]<slug>/README.md` (GitHub renders it as the
subfolder's landing page, so the collection folder reads as an index) and
downloads attachments into the transcript subfolder's `images/` — only created
when the conversation actually has attachments. The subfolder name is the
slugified title (override with `--name`); pass `--topic` to file it under a
high-level topic subfolder (scheme in AGENTS.md). Other options: `--title`,
`--source-url`, `--skip-images`. The script prints a self-check report at the
end:

- math fidelity — every LaTeX formula emitted is multiset-identical to the
  source annotations
- `$` balance — inline math delimiters pair within each line
- display fences — every ` ```math ` block is closed
- image refs — every image referenced exists on disk

Commit only after all checks pass and you have skimmed the diff.

## Collection index

After every conversion the script also regenerates `<out-dir>/README.md` —
an index of *every* note in the collection at any depth (transcript
subfolders and loose `.md` files alike), newest first, with a Topic column
(the note's first path segment) and dates from the last commit touching each
entry. `--reindex` regenerates just the index (also the way to refresh it
after hand-editing any note):

```sh
/tmp/dsenv/bin/python tools/ds2md.py --reindex -o notes/
```

## Title

The H1 title (and the subfolder name — the slugified title, unless `--name` is
given) are chosen in this order:

1. `--title "…"` — preferred: a short, descriptive title derived by the agent
   running the conversion (a few words, e.g. "HS math gap: CS vs ML").
2. Derived from the first user message: conversational openers stripped
   ("how is it that…", "can you tell me why…"), then the first short sentence
   or a 60-character word-boundary cut with dangling function words trimmed.
3. The page `<title>` as a last resort — DeepSeek auto-titles are poetic
   ("Into the Unknown"), so it is rarely what you want.

The script logs which source produced the title alongside the page title, so
the choice is visible in the run output.

## Recovering a full conversation from a live share URL

Share pages render the conversation as a **virtualized list**: the DOM only
holds messages near the viewport, so a naive fetch yields an empty shell (the
page is bot-gated; `curl` gets a WAF challenge, and a save without scrolling
yields a subset). While a share link is alive — before the owner deletes the
conversation — capture the whole thing with:

```sh
node tools/fetch_share.js <share-url> -o /tmp/chat.html
```

The script performs the capture and writes a standalone HTML export with the
page `<title>` and `og:url`, so the converter recovers the title and source
link exactly as it would from a saved export. It prints the title, the message
count, any gap keys, and whether the scroll reached the end. Then convert the
file like any export:

```sh
/tmp/dsenv/bin/python tools/ds2md.py /tmp/chat.html -o notes/ --topic <topic> --title "..."
```

What the script does, for the record: it presents an ordinary desktop Chrome
user agent (`HeadlessChrome` is rejected by the bot protection), finds the
ancestor of `.ds-virtual-list` whose `scrollHeight` exceeds its `clientHeight`,
steps `scrollTop` toward the bottom at about 1,400 px per 260 ms, and harvests
every mounted `[data-virtual-list-item-key]` row into a page-side map after
each step — virtualization mounts and unmounts rows, so harvesting must happen
during the scroll. It then passes back to the top for a final sweep and sorts
by numeric key.

Options: `--headful` if a challenge cannot be solved headless (the window is
then visible, and the user can complete it), and `--timeout <seconds>`.
Non-contiguous message IDs are normal — they are rows deleted from the
conversation — and are reported as gap keys. The capture is complete when the
script reports that the scroll reached the end. Keep the usual checks after
conversion: math fidelity, `$` balance, and the CoT leak grep.

Attachments are captured with the rows: their signed `files.deepseeksvc.com`
URLs are in the harvested DOM, so the converter downloads the images on the
same run. Capture and convert in one session; the signed URLs expire.

## Gotchas (why the rules are what they are)

1. **Message DOM.** Messages live in `div[data-virtual-list-item-key]` inside
   a virtual list; the keys can be non-contiguous and appear out of order, so
   they are sorted numerically. Role: `.ds-collapsible-text` = user,
   `.ds-assistant-message-main-content` = assistant. The `-999` item is a
   "generated by AI" banner, not a message.
2. **Partial captures.** App-side saves (page title `… - DeepSeek`) may
   contain only the messages the virtual list had rendered, and share-page
   saves capture only what was in the DOM at save time — so a low item count
   can mean truncation *or* a deliberate subset (scrolling to just the turns
   you want is a valid workflow). Either way the transcript is faithful to
   the export; the script warns so the choice is a conscious one.
3. **Whitespace.** The export writer never emits bare whitespace text nodes:
   every real space lives inside a `<span>`, and whitespace-only nodes are
   pretty-printer newlines. The script drops them; collapsing them to spaces
   instead produces spurious gaps (`**bold** .`, `math** —logic`).
4. **Display math must use ` ```math ` fences, not `$$…$$`.** GitHub's
   markdown layer processes backslash escapes *before* MathJax, so `\\` row
   separators arrive as a single `\` and every bmatrix collapses into one row.
   Fence content passes through verbatim. Inline math stays `$…$` (its content
   is backslash-letter commands only, which Markdown leaves alone). Inside a
   list item, every line of the fence — opening, LaTeX body, closing — must be
   indented at the item's continuation level: a half-indented fence (body and
   closing at column 0) makes GitHub parse the opening as an indented code
   block and the rest of the list is swallowed into it.
5. **Literal dollars are escaped.** A `$` in model prose (money, a shell
   variable) is text, not a delimiter: real math always arrives through the
   katex annotation. The converter escapes prose dollars as `\$`, otherwise
   an unescaped one opens an inline-math span and corrupts the rest of the
   line. The `$` balance check counts only unescaped dollars.
6. **Raw `\(` … `\)` in model text is not math.** Some DeepSeek replies emit
   LaTeX with `\(` delimiters that DeepSeek itself never renders — they are
   plain text. The script backslash-escapes them so GitHub shows them
   literally, as the original chat did.
7. **Citations.** `<a><span class="ds-markdown-cite">n</span></a>` becomes
   `[[n]](href)`; the favicon `<img>`s next to them are UI chrome and are
   dropped.
8. **Chain of thought is never transcribed.** Reasoning traces ("Thought for
   N seconds" and the `ds-think-content` block) live in a sibling container
   outside `.ds-assistant-message-main-content`, so the extractor never sees
   them. After converting an export that contains one, grep the output for a
   distinctive CoT phrase — it must come up empty.
9. **Attachment images.** Hosted on `files.deepseeksvc.com` with *signed,
   expiring* URLs — download promptly after saving the export. Quality tiers:
   `ty=o` is rejected (HTTP 400), `ty=p` is the full-resolution preview, `ty=t`
   a small thumbnail. The CDN serves webp even for `.png` originals; the script
   converts those back to PNG via macOS `sips` (falls back to renaming the file
   to the real format elsewhere). Screenshot names contain narrow no-break
   spaces (U+202F); the sanitizer strips them into clean filenames.
10. **The note is the archive.** After a verified conversion the owner deletes
   the source conversation from DeepSeek, which kills the share link — the
   note (with its locally stored images) becomes the only copy. The header's
   Source link is provenance and is expected to expire; never rely on it for
   content.
11. **Metadata.** The share link comes from the `og:url` meta (upgraded to
   https), the conversation title from `<title>` (`DeepSeek - X` share format
   or `X - DeepSeek` app format), and the date range from the attachment
   filenames.
12. **Safe by construction.** Intraword underscores (`y_2`, `a_i,j`) need no
   escaping — GFM never italicizes them.

## When the script is not enough

- **A different chat platform** (not DeepSeek): the DOM walker is
  DeepSeek-specific. Keep the general lessons — math from the source of truth,
  display math in ` ```math ` fences, never trust inter-tag whitespace, download
  images locally before URLs expire — and write a sibling converter rather
  than bending this one.
- **Broken exports** (missing annotations, unknown blocks): the script warns
  loudly instead of guessing; resolve the warnings by hand in the output, and
  extend the script if the case will recur.
