#!/usr/bin/env python3
"""Convert a DeepSeek chat HTML export into a faithful GitHub-Flavored Markdown transcript.

Usage:
    python3 ds2md.py ~/Desktop/chat1.html -o notes/ [--title "..."] [--name slug]

Writes <out-dir>/<slug>/README.md (GitHub renders it as the subfolder's
landing page) plus <out-dir>/<slug>/images/ when the chat has attachments.

Requires beautifulsoup4 + lxml (see tools/README.md for the one-line setup).

Read tools/README.md ("Gotchas") before modifying the conversion rules —
every rule below encodes a rendering failure that was hit in practice.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
except ImportError:
    sys.exit("beautifulsoup4 is required — see tools/README.md for the one-line setup")

try:
    import lxml  # noqa: F401
except ImportError:
    sys.exit("lxml is required — see tools/README.md for the one-line setup")

stats = {}


def bump(key, n=1):
    stats[key] = stats.get(key, 0) + n


warnings = []


def warn(msg):
    warnings.append(msg)


WS = re.compile(r"\s+")
SPECIAL = re.compile(r"[*_`\[\]<~]|(?<!\\)\$")
# ASCII punctuation, i.e. exactly the characters Markdown backslash-escapes
ESCAPABLE = "-!\"#$%&'()*+,./:;<=>?@[\\]^_`{|}~"

MATH_SLOTS = []     # inline tex, keyed by placeholder index
EMITTED_TEX = []    # every tex string emitted, for the fidelity check
ALL_ATTS = []       # every attachment found, for download + manifest
USED_NAMES = set()


def collapse(s):
    return WS.sub(" ", s)


def tighten_and_flush(s):
    """Collapse boundary whitespace, then restore math placeholders.

    Only spaces/tabs are squeezed so hard breaks ('\\\n') survive.
    """
    s = re.sub(r" {2,}", " ", s)
    s = re.sub(r"\n +", "\n", s)
    return re.sub("\x00(\\d+)\x00", lambda m: f"${MATH_SLOTS[int(m.group(1))]}$", s)


# ---------------------------------------------------------------- math

def get_tex(katex_node):
    ann = katex_node.find("annotation", attrs={"encoding": "application/x-tex"})
    if ann is None:
        ann = katex_node.find("annotation")
    if ann is None:
        warn(f"katex node without annotation: {str(katex_node)[:120]}")
        return ""
    tex = ann.get_text().strip()
    if "<" in tex or ">" in tex:
        warn(f"raw </> in tex (needs \\lt/\\gt): {tex[:80]}")
    if "`" in tex:
        warn(f"backtick in tex (would break a ```math fence): {tex[:80]}")
    EMITTED_TEX.append(tex)
    return tex


def math_placeholder(katex_node):
    MATH_SLOTS.append(get_tex(katex_node))
    return f"\x00{len(MATH_SLOTS) - 1}\x00"


# ---------------------------------------------------------------- inline

def render_children(node, in_cell=False):
    return "".join(render_inline(c, in_cell) for c in node.children)


def wrap(node, inner, marker):
    """Wrap inner in emphasis markers, keeping surrounding whitespace outside."""
    core = inner.strip()
    if not core:
        return inner
    lead = inner[: len(inner) - len(inner.lstrip())]
    trail = inner[len(inner.rstrip()):]
    return f"{lead}{marker}{core}{marker}{trail}"


def render_inline(node, in_cell=False):
    if isinstance(node, NavigableString):
        raw = str(node)
        if not raw.strip():
            # The export writer never emits bare whitespace text nodes: every
            # real space lives inside a <span>, so these are writer newlines.
            return ""
        raw = collapse(raw)
        # GitHub's markdown layer eats backslash escapes before text is shown;
        # restore them so e.g. the model's raw \( ... \) survives literally.
        raw = re.sub(r"\\(?=[" + re.escape(ESCAPABLE) + r"])", lambda m: "\\\\", raw)
        if SPECIAL.search(raw):
            warn(f"markdown-special chars in plain text: {raw.strip()[:90]!r}")
        return raw
    if not isinstance(node, Tag):
        return ""

    classes = node.get("class") or []
    name = node.name

    if name == "br":
        bump("br")
        return "<br>" if in_cell else "\\\n"

    if name == "span" and "katex" in classes:
        bump("math_inline")
        return math_placeholder(node)

    if name == "img":
        src = node.get("src", "")
        if "site-icons" in src or "fe-static" in src:
            return ""  # citation favicons / UI chrome
        warn(f"non-attachment <img> in content: {src[:100]}")
        return ""

    if name == "a":
        href = node.get("href", "")
        cite = node.find("span", class_="ds-markdown-cite")
        if cite is not None:
            bump("cites")
            m = re.search(r"\d+", cite.get_text())
            num = m.group(0) if m else "?"
            return f"[[{num}]]({href})"
        inner = render_children(node, in_cell).strip()
        if not href:
            return inner
        if "]" in inner:
            warn(f"']' inside link text: {inner[:60]!r}")
        return f"[{inner}]({href})"

    if name in ("strong", "b"):
        bump("strong")
        return wrap(node, render_children(node, in_cell), "**")

    if name in ("em", "i"):
        bump("em")
        return wrap(node, render_children(node, in_cell), "*")

    if name in ("del", "s", "strike"):
        return wrap(node, render_children(node, in_cell), "~~")

    if name in ("sub", "sup"):
        bump(name)
        return wrap(node, render_children(node, in_cell), "~" if name == "sub" else "^")

    if name == "code":
        bump("code")
        text = node.get_text()
        if "`" in text:
            runs = re.findall(r"`+", text)
            delim = "`" * (max(len(r) for r in runs) + 1)
        else:
            delim = "`"
        return f"{delim}{text}{delim}"

    # generic transparent element (span, u, mark, ...)
    return render_children(node, in_cell)


# ---------------------------------------------------------------- blocks

def render_blocks(container):
    out = []
    for child in container.children:
        if isinstance(child, NavigableString):
            if collapse(str(child)).strip():
                warn(f"stray text between blocks: {collapse(str(child)).strip()[:70]!r}")
            continue
        if not isinstance(child, Tag):
            continue
        cls = child.get("class") or []
        name = child.name

        if name == "p":
            bump("p")
            txt = tighten_and_flush(render_children(child)).strip()
            if txt:
                out.append(txt)
        elif name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            bump("heading")
            txt = tighten_and_flush(render_children(child)).strip()
            if txt:
                out.append("#" * int(name[1]) + " " + txt)
        elif name in ("ul", "ol"):
            out.append(render_list(child))
        elif name == "table":
            bump("tables")
            out.append(render_table(child))
        elif name == "hr":
            bump("hr")
            out.append("---")
        elif name == "blockquote":
            inner = render_blocks(child)
            out.append("\n".join("> " + b.replace("\n", "\n> ") for b in inner))
        elif name == "pre":
            out.append(f"```\n{child.get_text()}\n```")
        elif name == "span" and ("katex-display" in cls or "ds-markdown-math" in cls):
            bump("math_display")
            # ```math fences pass the LaTeX to MathJax verbatim; inside $$...$$
            # GitHub's markdown layer eats backslash escapes (\\ -> \), which
            # collapses bmatrix row separators into a single row.
            out.append("```math\n" + get_tex(child) + "\n```")
        elif name in ("span", "div", "section", "details", "summary"):
            # transparent wrapper: treat as block if it holds blocks, else inline
            if child.find(["p", "ul", "ol", "table", "hr", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"]):
                out.extend(render_blocks(child))
            else:
                txt = tighten_and_flush(render_children(child)).strip()
                if txt:
                    warn(f"inline-only wrapper block <{name} class={cls}>")
                    out.append(txt)
        else:
            warn(f"unhandled block <{name} class={cls}>")
            txt = tighten_and_flush(render_children(child)).strip()
            if txt:
                out.append(txt)
    return out


def render_list(node, indent=""):
    lines = []
    is_ol = node.name == "ol"
    idx = int(node.get("start", 1))
    for li in node.find_all("li", recursive=False):
        bump("li")
        parts = []       # inline-ish pieces of this item
        nested = []      # nested lists
        for c in li.children:
            if isinstance(c, NavigableString):
                if collapse(str(c)).strip():
                    parts.append(collapse(str(c)).strip())
                continue
            if not isinstance(c, Tag):
                continue
            ccls = c.get("class") or []
            if c.name in ("ul", "ol"):
                nested.append(c)
            elif c.name == "p":
                t = tighten_and_flush(render_children(c)).strip()
                if t:
                    parts.append(t)
            elif c.name == "span" and "katex-display" in ccls:
                parts.append("```math\n" + get_tex(c) + "\n```")
            else:
                t = tighten_and_flush(render_inline(c)).strip()
                if t:
                    parts.append(t)
        marker = f"{idx}." if is_ol else "-"
        if is_ol:
            idx += 1
        first = parts[0] if parts else ""
        rest = parts[1:]
        lines.append(f"{indent}{marker} {first}")
        cont = indent + " " * (len(marker) + 1)
        for r in rest:
            lines.append("")
            lines.append(cont + r)
        for sub in nested:
            lines.append(render_list(sub, indent=indent + " " * (len(marker) + 1)))
    return "\n".join(lines)


def render_table(node):
    def row_cells(tr):
        cells = []
        for c in tr.children:
            if isinstance(c, Tag) and c.name in ("td", "th"):
                cell = tighten_and_flush(render_children(c, in_cell=True)).strip()
                # keep the GFM table intact: \vert renders identically inside math
                cell = re.sub(r"\$([^$]*)\$", lambda m: "$" + m.group(1).replace("|", "\\vert") + "$", cell)
                cells.append(cell.replace("|", "\\|"))
        return cells

    header, body = None, []
    thead = node.find("thead")
    if thead is not None:
        tr = thead.find("tr")
        if tr is not None:
            header = row_cells(tr)
    tbody = node.find("tbody")
    source_body = tbody if tbody is not None else node
    for tr in source_body.find_all("tr"):
        if tr.find_parent("thead") is not None:
            continue
        cells = row_cells(tr)
        if header is None and all(c.name == "th" for c in tr.find_all(["th", "td"], recursive=False)):
            header = cells
        else:
            body.append(cells)

    if header is None and body:
        header = body.pop(0)
    if header is None:
        warn("table without header row")
        return ""
    width = max(len(header), max((len(r) for r in body), default=0))
    header += [""] * (width - len(header))
    out = ["| " + " | ".join(header) + " |",
           "| " + " | ".join(["---"] * width) + " |"]
    for r in body:
        r = r + [""] * (width - len(r))
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


# ---------------------------------------------------------------- attachments

def sanitize_filename(alt, fallback):
    # strips unicode oddities like the narrow no-break space (U+202F) in
    # macOS screenshot names ("...4.27.16 PM.png")
    stem = re.sub(r"[^\w.\- ]", "", alt or "").strip().replace(" ", "-")
    return stem or fallback


def collect_attachments(div):
    atts = []
    for img in div.select("img[src*='files.deepseeksvc.com']"):
        alt = img.get("alt", "")
        fname = sanitize_filename(alt, f"attachment-{len(ALL_ATTS) + 1}")
        stem, dot, ext = fname.rpartition(".")
        n = 2
        while fname in USED_NAMES:
            fname = f"{stem}-{n}.{ext}" if dot else f"{fname}-{n}"
            n += 1
        USED_NAMES.add(fname)
        att = {"alt": alt, "url": img["src"], "file": fname, "status": None}
        ALL_ATTS.append(att)
        bump("images")
        atts.append(att)
    return atts


def sniff_image(data):
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:4] == b"GIF8":
        return "gif"
    return ""


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def match_extension(fname, data):
    """Make the file extension tell the truth about the bytes.

    The CDN serves webp renditions even for .png originals; convert back to
    PNG via macOS sips when possible, otherwise rename to the real format.
    """
    actual = sniff_image(data)
    ext = Path(fname).suffix.lower().lstrip(".")
    if not actual or actual == ext:
        return fname, data
    if ext == "png" and actual == "webp" and shutil.which("sips"):
        try:
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "in.webp"
                src.write_bytes(data)
                dst = Path(td) / "out.png"
                subprocess.run(["sips", "-s", "format", "png", str(src), "--out", str(dst)],
                               check=True, capture_output=True)
                out = dst.read_bytes()
                if sniff_image(out) == "png":
                    warn(f"{fname}: CDN served webp for a .png original; converted back to PNG")
                    return fname, out
        except Exception as exc:
            warn(f"{fname}: sips conversion failed ({exc}); keeping webp bytes")
    fixed = str(Path(fname).with_suffix("." + actual))
    warn(f"{fname}: CDN served {actual}; renamed attachment to {fixed}")
    return fixed, data


def download_attachments(images_dir: Path):
    """Signed URLs expire — download promptly after saving the HTML export."""
    if not ALL_ATTS:
        print("no attachments — no images folder needed")
        return
    images_dir.mkdir(parents=True, exist_ok=True)
    for att in ALL_ATTS:
        base = re.sub(r"&ty=[a-z]+$", "", att["url"])
        got = None
        for ty in ("o", "p", "t"):  # o = original, p = preview (full res), t = thumbnail
            try:
                data = fetch(base + f"&ty={ty}")
            except Exception:
                continue
            if len(data) > 1000 and sniff_image(data):
                got = (ty, data)
                break
        if got is None:
            att["status"] = "failed"
            warn(f"could not download {att['file']}; hotlinking the (expiring) URL instead")
            continue
        ty, data = got
        fname, data = match_extension(att["file"], data)
        att["file"] = fname
        att["status"] = "ok"
        (images_dir / fname).write_bytes(data)
        print(f"image: {fname} (ty={ty}, {len(data) // 1024} KB)")


# ---------------------------------------------------------------- messages

def render_user_message(div, atts, images_rel):
    blocks = []
    for att in atts:
        if att["status"] == "failed":
            blocks.append(f"![{att['alt']}]({att['url']})")
        else:
            blocks.append(f"![{att['alt']}]({images_rel}/{att['file']})")
    coll = div.select_one(".ds-collapsible-text")
    paras = []
    for d in coll.find_all("div", recursive=False):
        t = tighten_and_flush(render_children(d)).strip()
        if t:
            paras.append(t)
    if not paras:
        t = tighten_and_flush(render_children(coll)).strip()
        if t:
            paras.append(t)
    blocks.extend(paras)
    return blocks


def derive_title(soup):
    raw = (soup.title.get_text() if soup.title else "").strip()
    for pat in ("DeepSeek - ", " - DeepSeek"):
        if raw.startswith(pat):
            return raw[len(pat):].strip()
        if raw.endswith(pat):
            return raw[: -len(pat)].strip()
    return raw or "Untitled conversation"


# Conversational openers that make poor titles ("how is it that…",
# "can you tell me why…"). Stripped before deriving a short title.
OPENERS = re.compile(
    r"^(?:please|hey|hi|hello|ok(?:ay)?|so|well|and|but|also|now)[,.\s]+"
    r"|^(?:how is it that|how come|is it (?:true|correct) that|why is it that"
    r"|can you (?:please )?(?:explain|tell me|clarify)(?: (?:to me))?(?: (?:why|how|what|whether))?[?,.]?"
    r"|could you [^,.;:?!\n]+[,.]?"
    r"|i(?:'m| am) (?:wondering|curious)[,.]?"
    r"|do you know (?:why|how|whether|if)"
    r"|what(?:'s| is) (?:the difference between|the reason (?:why|for)))\s*",
    re.I,
)

SHORT_TITLE_CAP = 60

# a cut title must not end on a dangling function word
TRAILING_FILL = re.compile(
    r"\s+(?:for|or|and|but|the|a|an|of|to|in|on|at|with|that|is|are|was|were"
    r"|it|its|as|by|from|not|vs\.?|if|then|than|so|because|when|while)$",
    re.I,
)


def derive_short_title(question):
    """A title from the first user message: openers stripped, then either the
    first short sentence or a word-boundary cut at the cap."""
    t = collapse(question).strip()
    for _ in range(3):
        t2 = OPENERS.sub("", t, count=1).strip()
        if not t2 or t2 == t:
            break
        t = t2
    m = re.match(r"^(.{10,%d}?[.?!;])(?:\s|$)" % SHORT_TITLE_CAP, t)
    if m:
        t = m.group(1)
    elif len(t) > SHORT_TITLE_CAP:
        cut = t[:SHORT_TITLE_CAP]
        t = cut[: cut.rfind(" ")] if " " in cut else cut
    t = t.strip().rstrip("?.!;:,")
    while True:
        t2 = TRAILING_FILL.sub("", t)
        if t2 == t:
            break
        t = t2
    if t:
        t = t[0].upper() + t[1:]
    return t


def slugify(title):
    s = re.sub(r"[^\w\- ]", "", title).strip().lower().replace(" ", "-")
    return s or "transcript"


def build_header(args, title, source_url, dates, n_user, n_asst):
    lines = [f"# {title}", ""]
    if args.description:
        lines += [f"> {args.description}", ">"]
    if source_url:
        shared = "/share/" in source_url
        label = "shared conversation" if shared else "conversation"
        domain = urlparse(source_url).netloc
        seg = f"> Source: [{label}]({source_url}) on {domain}"
        if dates:
            seg += f", {dates[0]}" if dates[0] == dates[-1] else f", {dates[0]} → {dates[-1]}"
        seg += (f". {n_user} question{'s' if n_user != 1 else ''}, "
                f"{n_asst} answer{'s' if n_asst != 1 else ''}.")
        seg += " The source link expires when the conversation is deleted from DeepSeek."
        lines.append(seg)
    features = []
    if stats.get("math_inline") or stats.get("math_display"):
        features.append("original LaTeX math")
    if stats.get("tables"):
        features.append("tables")
    if stats.get("cites"):
        features.append("web citations")
    if stats.get("images"):
        features.append("attached screenshots")
    flist = features[0] if features else "the conversation"
    if len(features) == 2:
        flist = " and ".join(features)
    elif len(features) > 2:
        flist = ", ".join(features[:-1]) + ", and " + features[-1]
    kind = "shared-conversation" if (source_url and "/share/" in source_url) else "chat"
    lines.append(f"> Recovered from the {kind} HTML export: {flist} preserved.")
    return "\n".join(lines)


# ---------------------------------------------------------------- index

def git_last_date(path: Path) -> str:
    """Date of the last commit touching path, as YYYY-MM-DD; today if the
    path is untracked, or git is unavailable."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path.name],
            cwd=str(path.parent), capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or date.today().isoformat()
    except Exception:
        return date.today().isoformat()


def write_index(collection_dir: Path):
    """Regenerate <collection>/README.md: an index of every note in the
    collection, at any depth — subfolder notes (README.md inside) and loose
    .md files alike — newest first, with a Topic column (the note's first
    path segment). Runs after every conversion so it never goes stale;
    --reindex refreshes it after hand edits."""
    entries = []
    for note in sorted(collection_dir.rglob("*.md")):
        if note.name == "README.md":
            if note.parent == collection_dir:
                continue  # the index itself
            p = note.parent
            fallback = p.name
            slug = p.relative_to(collection_dir).as_posix() + "/"
        else:
            p = note
            fallback = note.stem
            slug = note.relative_to(collection_dir).as_posix()
        title = fallback
        for line in note.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        rel = p.relative_to(collection_dir)
        topic = rel.parts[0] if len(rel.parts) > 1 else ""
        entries.append((git_last_date(p), title, slug, topic))
    entries.sort(key=lambda e: e[1])                 # ties: title ascending
    entries.sort(key=lambda e: e[0], reverse=True)   # then newest first

    lines = [f"# {collection_dir.name}", ""]
    if entries:
        lines += ["Notes in this collection, newest first.", "",
                  "| Last updated | Topic | Note |",
                  "| --- | --- | --- |"]
        for updated, title, slug, topic in entries:
            cell = f"[{topic}]({topic}/)" if topic else "—"
            lines.append(f"| {updated} | {cell} | [{title}]({slug}) |")
    else:
        lines += ["No notes yet."]
    (collection_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"index: {collection_dir / 'README.md'} ({len(entries)} note"
          f"{'s' if len(entries) != 1 else ''})")


def run_checks(md, src_tex, images_dir, args):
    ok = True
    match = sorted(EMITTED_TEX) == sorted(src_tex)
    print(f"check math fidelity (source vs emitted): {'MATCH' if match else 'FAIL'}")
    ok &= match
    expected = 2 * len(MATH_SLOTS)
    good = md.count("$") == expected
    print(f"check inline $ balance ({md.count('$')} == {expected}): {'OK' if good else 'FAIL'}")
    ok &= good
    odd = [i + 1 for i, l in enumerate(md.split("\n")) if l.count("$") % 2 == 1]
    good = not odd
    print(f"check per-line $ pairing: {'OK' if good else 'FAIL ' + str(odd[:5])}")
    ok &= good
    segs = md.split("```math")
    good = len(segs) - 1 == stats.get("math_display", 0) and all(s.startswith("\n") and "\n```" in s for s in segs[1:])
    print(f"check display fences ({stats.get('math_display', 0)}): {'OK' if good else 'FAIL'}")
    ok &= good
    if args.skip_images:
        print("check images: skipped (--skip-images)")
    else:
        refs = sorted(re.findall(r"!\[[^\]]*\]\(" + re.escape(args.images_dir) + r"/([^)]+)\)", md))
        files = sorted(p.name for p in images_dir.iterdir()) if images_dir.is_dir() else []
        good = refs == files
        print(f"check image refs == files on disk: {'OK' if good else 'FAIL ' + str(set(refs) ^ set(files))}")
        ok &= good
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path, nargs="?",
                    help="DeepSeek chat HTML export (shared page or app page)")
    ap.add_argument("-o", "--out-dir", type=Path, required=True,
                    help="collection folder that receives a <slug>/ subfolder per transcript, e.g. notes/")
    ap.add_argument("--reindex", action="store_true",
                    help="only regenerate the <out-dir>/README.md index; no conversion")
    ap.add_argument("--topic", help="high-level topic subfolder to file the "
                                    "transcript under, e.g. mathematics (see AGENTS.md for the scheme)")
    ap.add_argument("--title", help="transcript title (default: derived from the first user message)")
    ap.add_argument("--name", help="filename slug override (default: slugified title)")
    ap.add_argument("--description", help="one-line editorial summary shown under the title")
    ap.add_argument("--source-url", help="override the source link (default: og:url meta)")
    ap.add_argument("--images-dir", default="images", help="subfolder for attachments (default: images)")
    ap.add_argument("--skip-images", action="store_true", help="do not download attachments")
    args = ap.parse_args()

    if args.reindex:
        write_index(args.out_dir)
        return
    if args.input is None:
        ap.error("input HTML is required unless --reindex")

    soup = BeautifulSoup(args.input.read_text(encoding="utf-8"), "lxml")

    items = sorted(
        ((int(div["data-virtual-list-item-key"]), div)
         for div in soup.select("div[data-virtual-list-item-key]")),
        key=lambda t: t[0],
    )
    print(f"items in message list: {len(items)} (keys {[k for k, _ in items]})")
    if len(items) < 5:
        warn("very few message items — is this a partial (mid-scroll) capture of the app view? "
             "shared /share/ pages contain the full conversation")

    src_tex = [a.get_text().strip() for a in soup.find_all("annotation")]
    print(f"annotations in source: {len(src_tex)}")

    # pass 1: classify, collect attachments, and grab the first question —
    # it feeds the derived title, which names the subfolder before downloads land
    prepared = []
    first_question = ""
    for key, div in items:
        if key == -999:
            continue  # "generated by AI" disclaimer banner
        if div.select_one(".ds-collapsible-text"):
            if not first_question:
                first_question = collapse(
                    div.select_one(".ds-collapsible-text").get_text()).strip()
            prepared.append(("user", div, collect_attachments(div)))
        elif div.select_one(".ds-assistant-message-main-content"):
            prepared.append(("assistant", div, None))
        else:
            warn(f"item {key}: neither user nor assistant content found")

    page_title = derive_title(soup)
    if args.title:
        title, title_src = args.title, "--title flag"
    elif first_question:
        title, title_src = derive_short_title(first_question), "first user message"
    else:
        title, title_src = page_title, "page title"
    slug = slugify(args.name or title)
    print(f"title: {title!r} (from {title_src}); page title was: {page_title!r}")
    parts = [args.out_dir] + ([args.topic] if args.topic else []) + [slug]
    transcript_dir = Path(*parts)
    if not args.skip_images:
        download_attachments(transcript_dir / args.images_dir)

    # pass 2: render
    parts = []
    n_user = n_asst = 0
    for role, div, atts in prepared:
        if role == "user":
            n_user += 1
            blocks = render_user_message(div, atts, args.images_dir)
            parts.append("## User\n\n" + "\n\n".join(blocks))
        else:
            n_asst += 1
            blocks = render_blocks(div.select_one(".ds-assistant-message-main-content"))
            parts.append("## DeepSeek\n\n" + "\n\n".join(blocks))

    og_url = args.source_url
    if og_url is None:
        meta = soup.find("meta", attrs={"property": "og:url"})
        og_url = meta.get("content", "") if meta else ""
        if og_url.startswith("http://"):
            og_url = "https://" + og_url[len("http://"):]
    elif not og_url:
        og_url = ""
    alts = " ".join(a["alt"] for a in ALL_ATTS)
    dates = sorted(set(re.findall(r"20\d{2}-\d{2}-\d{2}", alts)))

    header = build_header(args, title, og_url, dates, n_user, n_asst)
    md = "\n\n---\n\n".join([header] + parts) + "\n"

    transcript_dir.mkdir(parents=True, exist_ok=True)
    out_md = transcript_dir / "README.md"
    out_md.write_text(md, encoding="utf-8")
    print(f"wrote {out_md} ({len(md.splitlines())} lines)")

    if ALL_ATTS and not args.skip_images:
        (transcript_dir / "images-manifest.json").write_text(
            json.dumps(ALL_ATTS, indent=2), encoding="utf-8")

    write_index(args.out_dir)

    print(f"user turns: {n_user}, assistant turns: {n_asst}")
    print(f"stats: {json.dumps(stats, sort_keys=True)}")
    print(f"warnings ({len(set(warnings))} unique):")
    for w in sorted(set(warnings)):
        print("  -", w)

    if not run_checks(md, src_tex, transcript_dir / args.images_dir, args):
        sys.exit(1)


if __name__ == "__main__":
    main()
