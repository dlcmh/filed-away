#!/usr/bin/env python3
"""Convert a saved DeepSeek share-page HTML snapshot into GitHub-flavoured Markdown.

Standard library only -- no bs4/lxml/pandoc required.

What it does
------------
* Walks the conversation's virtual-list items in document order.  User turns come
  from ``.fbb737a4`` bubbles, assistant turns from
  ``.ds-assistant-message-main-content``.
* Replaces every KaTeX expression with the *original LaTeX* found in its
  ``<annotation encoding="application/x-tex">`` child, emitted as ``$...$``
  (inline) or ``$$...$$`` (display) so github.com renders it with MathJax.
* Maps headings, nested lists, tables, bold/italic/code, links, images and
  blockquotes onto their Markdown equivalents.
* Rewrites conversation image URLs to local files under ``images/``.

Usage
-----
    python3 tools/build_transcript.py <chat.html> [output.md]
"""

from __future__ import annotations

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Conversation images: original DeepSeek file id -> (local file, alt text).
IMAGE_MAP = {
    "a1abe922-855c-418e-810b-a9a167cc226d": (
        "images/01-mml-preface-math-gap.webp",
        "Mathematics for Machine Learning, preface: the gap between high-school "
        "mathematics and the mathematics needed to read a machine learning textbook",
    ),
    "7c2fe866-5eca-4028-9221-2f11844df1d9": (
        "images/02-mml-section-2-1-example-2-1.webp",
        "MML section 2.1 'Systems of Linear Equations' and Example 2.1, the "
        "production-plan problem phrased in terms of products N_j and resources R_i",
    ),
    "04930a3e-ec9d-4103-96ec-3a8949594877": (
        "images/03-mml-equations-2-2-2-3.webp",
        "MML equations (2.2) and (2.3): the general form of a system of linear equations",
    ),
    "d3f164d9-d783-4650-8bc3-ed897fd335ec": (
        "images/04-what-2-3-actually-says.webp",
        "Index legend explaining equation (2.3): i over resources R_i, j over products "
        "N_j, a_ij units of resource i per unit of product j, x_j decision variable, "
        "b_i resource available",
    ),
    "5d7b5fb2-6cdc-4404-a2e9-aced9a7cd06f": (
        "images/05-mml-example-2-6-2-7-free-variable.webp",
        "MML equations (2.6) and (2.7): equation (3) is redundant and x_3 = alpha is "
        "chosen as the free variable",
    ),
    "2bdf9a41-70c1-41e4-afd4-4f1452f028ae": (
        "images/06-mml-solution-set-infinitely-many.webp",
        "MML: the resulting solution set contains infinitely many solutions",
    ),
}

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

# UI chrome that must never reach the transcript.
SKIP_TAGS = {"svg", "path", "circle", "rect", "g", "defs", "clippath", "script",
             "style", "button", "textarea", "input", "noscript", "iframe"}
SKIP_CLASSES = {"katex-html", "ds-icon", "ds-button", "ds-button__background",
                "ds-button__icon", "ds-lottie-toggle-icon", "ds-focus-ring"}


# --------------------------------------------------------------------------- #
# A minimal, tolerant DOM
# --------------------------------------------------------------------------- #

class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.parent = parent

    # -- convenience -------------------------------------------------------- #
    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def has_class(self, name):
        return name in self.classes

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"<Node {self.tag} {self.attrs.get('class', '')!r} {len(self.children)}>"


class Text:
    __slots__ = ("data", "parent")

    def __init__(self, data, parent=None):
        self.data = data
        self.parent = parent


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
        # unmatched close tag: ignore

    def handle_data(self, data):
        self.stack[-1].children.append(Text(data, self.stack[-1]))


def parse(source: str) -> Node:
    builder = TreeBuilder()
    builder.feed(source)
    builder.close()
    return builder.root


def walk(node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from walk(child)


def descendants(node):
    yield from walk(node)


def find_all(node, predicate):
    return [n for n in descendants(node) if predicate(n)]


def raw_text(node) -> str:
    out = []
    for child in node.children:
        if isinstance(child, Text):
            out.append(child.data)
        else:
            out.append(raw_text(child))
    return "".join(out)


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# --------------------------------------------------------------------------- #
# Inline rendering
# --------------------------------------------------------------------------- #

def escape_text(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for ch in ("\\", "`", "*", "_", "[", "]"):
        text = text.replace(ch, "\\" + ch)
    return text


def latex_of(node):
    """Return the original LaTeX for a KaTeX node, or None."""
    for child in descendants(node):
        if child.tag == "annotation" and "tex" in (child.attrs.get("encoding") or ""):
            return raw_text(child).strip()
    return None


def is_skipped(node: Node) -> bool:
    if node.tag in SKIP_TAGS:
        return True
    classes = node.classes
    if classes & SKIP_CLASSES:
        return True
    style = (node.attrs.get("style") or "").replace(" ", "")
    if "opacity:0" in style or "display:none" in style:
        return True
    return False


def image_markdown(node: Node):
    src = html.unescape(node.attrs.get("src") or "")
    for file_id, (path, alt) in IMAGE_MAP.items():
        if file_id in src:
            return f"![{alt}]({path})"
    return None


def render_inline_node(node: Node) -> str:
    """Render a single element as inline Markdown."""
    if is_skipped(node):
        return ""
    tag = node.tag
    classes = node.classes

    if "katex-display" in classes:
        tex = latex_of(node)
        return f"\n\n$$\n{tex}\n$$\n\n" if tex else ""
    if "katex" in classes:
        tex = latex_of(node)
        return f"${tex}$" if tex else escape_text(collapse(raw_text(node)))

    if tag in ("strong", "b"):
        return f"**{render_inline(node).strip()}**"
    if tag in ("em", "i"):
        inner = render_inline(node).strip()
        # github.com's math scanner does not fire inside `*emphasis*`, but it does
        # fire inside inline HTML <i>...</i>, so use that whenever math is nested.
        if "$" in inner:
            return f"<i>{inner}</i>"
        return f"*{inner}*"
    if tag == "code":
        return f"`{raw_text(node)}`"
    if tag == "a":
        href = html.unescape(node.attrs.get("href") or "").replace(" ", "%20")
        label = render_inline(node).strip() or href
        return f"[{label}]({href})"
    if tag == "img":
        return image_markdown(node) or ""
    if tag == "br":
        return "\n"
    if tag in ("p", "ul", "ol", "table", "blockquote", "pre") or tag in HEADINGS:
        return render_block(node)
    return render_inline(node)


def render_inline(node: Node) -> str:
    """Render an element's children as inline Markdown."""
    out = []
    for child in node.children:
        if isinstance(child, Text):
            out.append(escape_text(collapse(child.data)))
        else:
            out.append(render_inline_node(child))
    return "".join(out)


# --------------------------------------------------------------------------- #
# Block rendering
# --------------------------------------------------------------------------- #

def render_list(node: Node, depth: int = 0) -> str:
    ordered = node.tag == "ol"
    try:
        index = int(node.attrs.get("start") or 1)
    except ValueError:
        index = 1
    lines = []
    for li in node.children:
        if not isinstance(li, Node) or li.tag != "li":
            continue
        inline_html = []
        nested = []
        for child in li.children:
            if isinstance(child, Node) and child.tag in ("ul", "ol"):
                nested.append(child)
            else:
                inline_html.append(child)
        holder = Node("li", {}, None)
        holder.children = inline_html
        text = render_inline(holder).strip()
        text = re.sub(r"\n{2,}", "\n", text)
        marker = f"{index}. " if ordered else "- "
        indent = " " * len(marker)
        parts = text.split("\n") if text else [""]
        lines.append(marker + parts[0])
        for extra in parts[1:]:
            lines.append(indent + extra)
        for sub in nested:
            sub_md = render_list(sub)
            lines.extend(indent + line for line in sub_md.split("\n"))
        index += 1
    return "\n".join(lines)


def render_table(node: Node) -> str:
    rows = []
    for tr in find_all(node, lambda n: n.tag == "tr"):
        cells = [c for c in tr.children if isinstance(c, Node) and c.tag in ("td", "th")]
        if not cells:
            continue
        rendered = []
        for cell in cells:
            value = render_inline(cell).strip()
            value = re.sub(r"\s*\n\s*", "<br>", value)
            value = value.replace("|", "\\|")
            rendered.append(value or " ")
        rows.append(rendered)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [" "] * (width - len(r)) for r in rows]
    header, body = rows[0], rows[1:]
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join("---" for _ in range(width)) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)


def render_block(node: Node) -> str:
    tag = node.tag
    classes = node.classes

    if "katex-display" in classes:
        tex = latex_of(node)
        return f"$$\n{tex}\n$$" if tex else ""

    if tag in HEADINGS:
        level = min(HEADINGS[tag] + 1, 6)  # demote: keeps turn markers at `##`
        # strip the leading "#" numbering the source used for h3s? keep as-is
        text = render_inline(node).strip()
        return f"{'#' * level} {text}" if text else ""

    if tag == "p":
        return re.sub(r"\n{3,}", "\n\n", render_inline(node)).strip()

    if tag in ("ul", "ol"):
        return render_list(node)

    if tag == "table":
        return render_table(node)

    if tag == "blockquote":
        inner = render_blocks(node.children)
        return "\n".join("> " + line if line else ">" for line in inner.split("\n"))

    if tag == "hr":
        return "---"

    if tag == "pre":
        return "```\n" + raw_text(node).strip("\n") + "\n```"

    if tag == "br":
        return ""

    if tag == "img":
        return image_markdown(node) or ""

    # container elements: recurse
    return render_blocks(node.children)


def is_block_node(node: Node) -> bool:
    if node.tag in ("p", "ul", "ol", "table", "blockquote", "pre", "hr",
                    "h1", "h2", "h3", "h4", "h5", "h6", "br", "img"):
        return True
    if "katex-display" in node.classes:
        return True
    # an attachment wrapper: a div holding only image(s) gets its own paragraph
    if node.tag in ("div", "figure") and not collapse(raw_text(node)).strip():
        if any(n.tag == "img" for n in descendants(node)):
            return True
    return False


def render_blocks(children) -> str:
    blocks = []
    buffer = []

    def flush():
        text = "".join(buffer).strip()
        buffer.clear()
        if text:
            blocks.append(text)

    for child in children:
        if isinstance(child, Text):
            text = escape_text(collapse(child.data))
            if text.strip():
                buffer.append(text)
            continue
        if is_skipped(child):
            continue
        if is_block_node(child):
            flush()
            rendered = render_block(child).strip()
            if rendered:
                blocks.append(rendered)
        else:
            buffer.append(render_inline_node(child))
    flush()
    text = "\n\n".join(blocks)
    # tidy the doubled spaces the source leaves around inline formatting
    text = re.sub(r"(?<=\S) {2,}", " ", text)
    return text


# --------------------------------------------------------------------------- #
# Conversation assembly
# --------------------------------------------------------------------------- #

def item_of(node):
    """Return the enclosing virtual-list key of a node, if any."""
    current = node
    while current is not None:
        if "data-virtual-list-item-key" in current.attrs:
            return current.attrs["data-virtual-list-item-key"]
        current = current.parent
    return None


def search_marker(item: Node):
    spans = find_all(item, lambda n: n.tag == "span" and n.has_class("_769d943"))
    for span in spans:
        text = collapse(raw_text(span)).strip()
        found = re.match(r"Found\s+(\d+)\s+web pages?", text)
        if found:
            return f"> \U0001f50e *Searched the web \u2014 found {found.group(1)} pages.*"
    return None


def user_content(item: Node):
    """Render a user turn: its attachments (if any) plus the text bubble.

    The message container holds the attachment strip and the ``.fbb737a4`` text
    bubble; the action buttons live in a sibling outside ``.ds-message``, so
    rendering the container's children keeps the chrome out.
    """
    message = next((n for n in descendants(item)
                    if n.tag == "div" and n.has_class("ds-message")), None)
    if message is None:
        return None
    if not any(n.has_class("fbb737a4") for n in descendants(message)):
        return None
    return render_blocks(message.children)


def assistant_content(item: Node):
    body = next((n for n in descendants(item)
                 if n.has_class("ds-assistant-message-main-content")), None)
    if body is None:
        return None
    return render_blocks(body.children)


def build_transcript(source: str):
    tree = parse(source)
    items = [n for n in walk(tree) if "data-virtual-list-item-key" in n.attrs]

    turns = []
    search_count = 0
    for item in items:
        user = user_content(item)
        if user is not None:
            turns.append({"user": user, "assistant": None, "search": None})
            continue
        assistant = assistant_content(item)
        if assistant is None:
            continue
        if not turns:
            turns.append({"user": None, "assistant": None, "search": None})
        marker = search_marker(item)
        if marker:
            search_count += 1
        turns[-1].update(assistant=assistant, search=marker)
    return turns, search_count


HEADER = """\
# {title}

A full, readable transcript of a DeepSeek conversation about working through
*Mathematics for Machine Learning* (MML) with a management-accounting (MRP/ACCA)
background -- covering the high-school-to-ML maths gap, systems of linear
equations, linearity, change of basis, embeddings, free variables, regularisation
and the places where the textbook's abstractions suddenly connect to machine
learning.

|  |  |
| --- | --- |
| **Source** | <{share_url}> |
| **Model / mode** | DeepSeek, DeepThink reasoning with web search enabled |
| **App build** | `{commit_id}` |
| **Turns** | {user_turns} user / {assistant_turns} assistant |
| **Images** | {image_count} conversation images, mirrored in [`images/`](images) |

Math is rendered from the original LaTeX (`$...$` inline, `$$...$$` display), so
it typesets on github.com. Conversation images were downloaded and committed to
this repository because the original links are signed, expiring URLs.

> AI-generated conversation, reproduced for reference only.

---
"""

APPENDIX = """
---

## Source images

The original signed URLs are not stable, so each image is mirrored in
[`images/`](images):

| Local file | DeepSeek file id |
| --- | --- |
{rows}
"""


def render_markdown(turns, search_count, meta):
    parts = [HEADER.format(**meta)]
    turn_no = 0
    user_turns = assistant_turns = 0
    for turn in turns:
        if turn["user"] is not None:
            turn_no += 1
            user_turns += 1
            parts.append(f"## {turn_no}. You\n\n{turn['user']}\n")
        if turn["assistant"] is not None:
            assistant_turns += 1
            block = []
            if turn["search"]:
                block.append(turn["search"])
                block.append("")
            block.append(turn["assistant"])
            heading = f"## {turn_no}. DeepSeek" if turn_no else "## DeepSeek"
            parts.append(heading + "\n\n" + "\n".join(block).strip() + "\n")
    rows = "\n".join(f"| [`{path}`]({path}) | `{file_id}` |"
                     for file_id, (path, _alt) in IMAGE_MAP.items())
    parts.append(APPENDIX.format(rows=rows))
    return "\n".join(parts), user_turns, assistant_turns


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = Path(argv[1])
    out = Path(argv[2]) if len(argv) > 2 else REPO_ROOT / "README.md"
    source = src.read_text(encoding="utf-8", errors="replace")

    turns, search_count = build_transcript(source)
    commit_id = re.search(r'name="commit-id" content="([^"]+)"', source)
    share = re.search(r'property="og:url" content="([^"]+)"', source)

    meta = {
        "title": "HS Math Gap: CS vs ML",
        "share_url": html.unescape(share.group(1)) if share else "https://chat.deepseek.com",
        "commit_id": commit_id.group(1) if commit_id else "unknown",
        "user_turns": sum(1 for t in turns if t["user"] is not None),
        "assistant_turns": sum(1 for t in turns if t["assistant"] is not None),
        "image_count": len(IMAGE_MAP),
    }
    markdown, users, assistants = render_markdown(turns, search_count, meta)

    out.write_text(markdown, encoding="utf-8")

    print(f"wrote {out} ({len(markdown):,} chars, {markdown.count(chr(10)) + 1:,} lines)")
    print(f"user turns      : {users}")
    print(f"assistant turns : {assistants}")
    print(f"search markers  : {search_count}")
    print(f"images referenced: {markdown.count('![', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
