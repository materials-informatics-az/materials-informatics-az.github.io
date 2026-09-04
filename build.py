#!/usr/bin/env python3
"""
Build the Materials Informatics Lab site.

    python3 build.py            # build into site/
    python3 build.py --serve    # build, then serve on http://localhost:8000

Everything you edit day to day lives in content/. Templates live in templates/.
Generated HTML lands next to this file and is what GitHub Pages serves.
"""

from __future__ import annotations

import argparse
import datetime
import re
from xml.sax.saxutils import escape
import shutil
import sys
from pathlib import Path

# macOS still ships Python 3.9 as /usr/bin/python3, so a venv created with a
# bare `python3` can quietly land on it. python-frontmatter then fails with
# "cannot import name 'TypeGuard' from 'typing'", which arrives as an
# ImportError naming `typing` — i.e. it looks like a missing package, and
# reinstalling can never fix it. Say the real thing instead.
if sys.version_info < (3, 10):
    sys.exit(
        f"this needs Python 3.10 or newer; you are on {sys.version.split()[0]}"
        f" ({sys.executable})\n"
        "  Rebuild the venv with a newer interpreter, for example:\n"
        "    rm -rf .venv && python3.11 -m venv .venv\n"
        "    .venv/bin/pip install -r requirements.txt"
    )

try:
    import bibtexparser
    import frontmatter
    import markdown as markdown_lib
    import yaml
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError as exc:  # pragma: no cover
    # `exc.name` is the module the failing import was *from*, which is not
    # always the package you need to install — hence printing the exception too.
    sys.exit(f"missing dependency: {exc.name}\n  {exc}\n  pip install -r requirements.txt")

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
# Everything the site serves, and nothing else. The build writes straight in
# here and the deploy workflow uploads it as-is: the set of published files is
# decided in one place rather than restated as a list of `cp` lines that has to
# be kept in step with what the build actually produces.
OUT = ROOT / "_publish"

# Every page the site can produce: template, output file, and the feature flag
# that gates it (None = always built). A new page is a row here and a template.
PAGES = [
    # template            output               flag
    ("index.html", "index.html", None),
    ("research.html", "research.html", "research"),
    ("people.html", "people.html", None),
    ("tools.html", "tools.html", "tools"),
    ("publications.html", "publications.html", None),
    ("news.html", "news.html", None),
    ("studies.html", "studies.html", "studies"),
    ("teaching.html", "teaching.html", "teaching"),
    ("cv.html", "cv.html", "cv"),
    # Served by GitHub Pages for any address that does not resolve. Its links
    # are root-relative, so it works from any depth.
    ("404.html", "404.html", None),
]

def check_links(out_dir: Path) -> list[str]:
    """
    Every local href and src in the GENERATED site must resolve to a file that
    exists, and every #fragment to an id that exists. Catches a page removed by
    a feature flag, a renamed post, a missing image and a leftover [PLACEHOLDER]
    alike.

    External links are not fetched — only checked for being obviously unfinished.
    """
    # static/ ships as-is and holds third-party demo pages we do not own.
    skip_dirs = {"static"}
    problems = []
    for page in sorted(out_dir.rglob("*.html")):
        if skip_dirs & set(page.relative_to(out_dir).parts):
            continue
        rel = page.relative_to(out_dir)
        html = page.read_text(encoding="utf-8")
        for target in re.findall(r'(?:href|src)="([^"]*)"', html):
            if target.startswith(("http://", "https://", "mailto:", "data:", "#")) or not target:
                if "[" in target and "]" in target:
                    problems.append(f"{rel}: unfilled placeholder -> {target}")
                continue
            path, _, fragment = target.partition("#")
            if not path:
                continue
            # "/static/style.css" is relative to the site root, not to the
            # page — 404.html uses that form because it is served from every
            # depth. Resolving it against page.parent would look outside the
            # site entirely.
            if path.startswith("/"):
                resolved = (out_dir / path.lstrip("/")).resolve()
            else:
                resolved = (page.parent / path).resolve()
            if not resolved.exists():
                problems.append(f"{rel}: broken link -> {target}")
            elif fragment and resolved.suffix == ".html":
                if f'id="{fragment}"' not in resolved.read_text(encoding="utf-8"):
                    problems.append(f"{rel}: missing anchor -> {target}")
    return problems


def image_size(path: Path) -> tuple[int, int] | None:
    """
    (width, height) of a PNG or JPEG, read from its header. Pure stdlib — the
    site has no image dependency and does not need one for two integers.

    These become the `width`/`height` attributes on the <img>, which is how the
    browser reserves the right amount of space before the file arrives. Hard-
    coding them means every re-crop silently desyncs them and the page jumps on
    load, so they are read from the actual file instead.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None

    if data[:8] == b"\x89PNG\r\n\x1a\n":
        # IHDR is always the first chunk: width and height are big-endian
        # 4-byte ints at offsets 16 and 20.
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")

    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            # SOF0-SOF15, excluding the four that are not frame headers.
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                return (
                    int.from_bytes(data[i + 7 : i + 9], "big"),
                    int.from_bytes(data[i + 5 : i + 7], "big"),
                )
            i += 2 + int.from_bytes(data[i + 2 : i + 4], "big")
    return None


def with_size(figure: dict) -> dict:
    """A figure dict with `width`/`height` filled in from the file it names."""
    figure = dict(figure or {})
    src = figure.get("src")
    if src:
        size = image_size(ROOT / src)
        if size:
            figure["width"], figure["height"] = size
    return figure


def load_yaml(name: str) -> dict:
    """Read content/<name>.yml. Returns {} when the file does not exist yet."""
    path = CONTENT / f"{name}.yml"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# BibTeX braces protect capitalisation; they are noise once rendered.
_BRACES = str.maketrans("", "", "{}")

# LaTeX writes dashes as runs of hyphens, and Zotero exports them that way:
# "Microstructure--Property" is an en dash, not two hyphens, and a browser shows
# it literally. Display only — render_bibtex reads the raw entry and keeps the
# hyphens, since that is what makes the copied entry valid BibTeX.
_LATEX_DASHES = (("---", "\u2014"), ("--", "\u2013"))


def _clean(value: str) -> str:
    text = " ".join(str(value or "").translate(_BRACES).split())
    for latex, dash in _LATEX_DASHES:
        text = text.replace(latex, dash)
    return text


def _authors(raw: str) -> str:
    """'Hu, Guangyu and I. Latypov, Marat' -> 'G. Hu, M. I. Latypov'."""
    names = []
    for part in _clean(raw).split(" and "):
        part = part.strip()
        if not part:
            continue
        if "," in part:
            last, first = (p.strip() for p in part.split(",", 1))
            # Hyphenated given names keep both initials: I-Tzu -> I.-T.
            initials = " ".join(
                "-".join(f"{seg[0]}." for seg in w.split("-") if seg and seg[0].isalpha())
                for w in first.split()
                if w and w[0].isalpha()
            )
            names.append(f"{initials} {last}".strip())
        else:
            names.append(part)
    return ", ".join(names)


# The fields a copied citation should carry, in the order a reader expects to
# see them. Everything else in the bib — `abstract`, `file`, `keywords`,
# `urldate`, `langid`, and our own `selected`/`tool` — is local bookkeeping and
# only makes the pasted entry harder to read.
CITE_FIELDS = (
    "author",
    "title",
    "journal",
    "booktitle",
    "publisher",
    "year",
    "month",
    "volume",
    "number",
    "pages",
    "doi",
    "url",
    "eprint",
    "archiveprefix",
    "primaryclass",
    "issn",
)


# bibtexparser expands the `mar` macro to "March". BibTeX's own convention is
# the unbraced three-letter macro, which is also what Zotero exports, so put it
# back rather than shipping a copied entry that differs from the source.
_MONTH_MACROS = {
    m: m[:3].lower()
    for m in (
        "January February March April May June "
        "July August September October November December"
    ).split()
}


def render_bibtex(entry: dict) -> str:
    """
    Re-emit one entry as the BibTeX a reader would want pasted into their
    manager. Values keep their {braces} — those protect capitalisation and are
    the whole reason a copied entry beats a retyped one — but are collapsed onto
    a single line, since a bib exported from Zotero wraps them arbitrarily.
    """
    lines = []
    for field in CITE_FIELDS:
        value = " ".join(str(entry.get(field, "")).split())
        if not value:
            continue
        if field == "month" and value.capitalize() in _MONTH_MACROS:
            lines.append(f"  month = {_MONTH_MACROS[value.capitalize()]}")
        else:
            lines.append(f"  {field} = {{{value}}}")
    if not lines:
        return ""
    return (
        f"@{entry.get('ENTRYTYPE', 'article')}{{{entry.get('ID', '')},\n"
        + ",\n".join(lines)
        + "\n}\n"
    )


def load_papers() -> list[dict]:
    """
    Read content/papers.bib into render-ready entries, newest first.

    `selected` and `tool` are our own fields, not standard BibTeX — every other
    tool ignores them, and they are what drive the landing page block and the
    "Interactive" chips.
    """
    path = CONTENT / "papers.bib"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        db = bibtexparser.load(fh)

    papers = []
    for entry in db.entries:
        venue = entry.get("journal") or entry.get("booktitle") or entry.get("publisher") or ""
        if not venue and entry.get("ENTRYTYPE") == "misc":
            venue = "preprint"
        doi = entry.get("doi", "").strip()
        papers.append(
            {
                "key": entry.get("ID", ""),
                "year": _clean(entry.get("year", "")),
                "title": _clean(entry.get("title", "")),
                "authors": _authors(entry.get("author", "")),
                "venue": _clean(venue),
                "href": f"https://doi.org/{doi}" if doi else entry.get("url", "").strip(),
                "selected": _clean(entry.get("selected", "")).lower() == "true",
                "tool": _clean(entry.get("tool", "")) or None,
                "bibtex": render_bibtex(entry),
            }
        )
    # Newest year first, then alphabetical within the year. Sorting the pair in
    # one reversed pass ran the titles Z->A, which is neither chronological nor
    # alphabetical. Python's sort is stable, so two passes give both orders.
    papers.sort(key=lambda p: p["title"])
    papers.sort(key=lambda p: p["year"], reverse=True)
    return papers


def group_by_year(papers: list[dict]) -> list[dict]:
    """[{year, papers}], newest year first — the shape publications.html renders."""
    years: dict[str, list[dict]] = {}
    for paper in papers:
        years.setdefault(paper["year"], []).append(paper)
    return [{"year": y, "papers": years[y]} for y in sorted(years, reverse=True)]


def load_posts() -> list[dict]:
    """
    content/posts/*.md -> rendered posts, newest first.

    The body is plain Markdown. `tables`, `fenced_code` and `codehilite` are the
    three extensions the existing posts actually need — they use a table and a
    code fence and nothing else.
    """
    posts_dir = CONTENT / "posts"
    if not posts_dir.is_dir():
        return []

    md = markdown_lib.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "smarty"],
        # codehilite defaults to class="codehilite"; the stylesheet (and every
        # Pygments theme) targets .highlight.
        extension_configs={"codehilite": {"css_class": "highlight", "guess_lang": False}},
    )
    posts = []
    for path in sorted(posts_dir.glob("*.md")):
        doc = frontmatter.load(path)
        raw_date = str(doc.get("date", ""))[:10]
        try:
            date = datetime.date.fromisoformat(raw_date)
        except ValueError:
            date = datetime.date.min
        # 2025-09-01-vit.md -> vit
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        posts.append(
            {
                "slug": slug,
                "href": f"studies/{slug}.html",
                "title": doc.get("title", slug),
                "description": doc.get("description", ""),
                "authors": doc.get("authors", ""),
                "tags": doc.get("tags", []) or [],
                "date": date,
                "display_date": date.strftime("%d %b %Y") if date != datetime.date.min else raw_date,
                "iso_date": raw_date,
                "html": md.reset().convert(doc.content),
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render_feed(posts: list[dict], site: dict) -> str:
    """A minimal RSS 2.0 feed. `site.url` still in [brackets] yields relative links."""
    base = str(site.get("url", "")).rstrip("/")
    if is_placeholder(base):
        base = ""
    items = []
    for post in posts:
        link = f"{base}/{post['href']}" if base else post["href"]
        stamp = post["date"].strftime("%a, %d %b %Y 00:00:00 +0000")
        items.append(
            "    <item>\n"
            f"      <title>{escape(post['title'])}</title>\n"
            f"      <link>{escape(link)}</link>\n"
            f"      <guid isPermaLink=\"false\">{escape(post['slug'])}</guid>\n"
            f"      <pubDate>{stamp}</pubDate>\n"
            f"      <description>{escape(post['description'])}</description>\n"
            "    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n  <channel>\n'
        f"    <title>{escape(site.get('title', ''))}</title>\n"
        f"    <link>{escape(base or '/')}</link>\n"
        f"    <description>{escape(site.get('tagline', ''))}</description>\n"
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )


def render_sitemap(locations: list[str]) -> str:
    """A minimal urlset. Search engines want absolute URLs, so this is only
    written when site.url is set."""
    urls = "\n".join(f"  <url><loc>{escape(loc)}</loc></url>" for loc in locations)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )


def render_news(items: list[dict]) -> list[dict]:
    """`text` is Markdown so a news line can carry a link. Render it once here."""
    inline = markdown_lib.Markdown(extensions=[])
    out = []
    for item in items:
        item = dict(item)
        item["html"] = inline.reset().convert(str(item.get("text", ""))).replace("<p>", "").replace("</p>", "")
        raw = str(item.get("date", ""))
        item["display_date"] = raw
        try:
            item["display_date"] = datetime.date.fromisoformat(raw).strftime("%d %b %Y")
        except ValueError:
            pass
        out.append(item)
    return out


def resolve_tool_links(items: list[dict], tools: list[dict], features: dict) -> list[dict]:
    """
    Attach `tool_url` to any item carrying a `tool` id, so templates can render
    the "Interactive" chip without knowing about tools.yml. When the tools
    feature is off, no item gets a link and every chip disappears with it.
    """
    if not features.get("tools"):
        return [{k: v for k, v in item.items() if k != "tool"} for item in items]
    by_id = {t["id"]: t for t in tools}
    out = []
    for item in items:
        item = dict(item)
        tool = by_id.get(item.get("tool"))
        # A tool whose url is still [URL] gets no chip: a chip is a link, and
        # there is nothing to link to yet.
        if tool and not is_placeholder(tool.get("url")):
            item["tool_url"] = tool["url"]
        else:
            item.pop("tool", None)
        out.append(item)
    return out


def normalise_links(raw: dict, disabled_pages: set[str] | None = None) -> list[dict]:
    """
    label -> address becomes [{label, href, unset}]. `email` gains its mailto:.
    A value still in [brackets] is marked unset so the template renders muted
    text instead of a link that goes nowhere.
    """
    disabled_pages = disabled_pages or set()
    out = []
    for label, value in (raw or {}).items():
        value = str(value).strip()
        # An internal link to a page a feature flag removed would 404.
        if value in disabled_pages:
            continue
        unset = is_placeholder(value)
        href = "" if unset else (f"mailto:{value}" if label == "email" else value)
        out.append({"label": label, "href": href, "unset": unset})
    return out


# Pillar accents in the order they are handed out. A fifth pillar reuses the
# first colour — three or four is the point at which a reader stops treating a
# colour as an identifier anyway.
PILLAR_ACCENTS = ["accent-1", "accent-2", "accent-3"]

# The tint behind a chip, keyed by the accent its role or pillar is assigned.
# Keyed by the RAW accent (`accent-3`, not `accent-3-text`): the substitution
# that keeps purple readable applies to text, and this is a 14-16% fill, which
# is the one place the brand purple is used directly.
ACCENT_BG = {
    "accent-1": "rgba(0, 139, 255, 0.14)",
    "accent-2": "rgba(255, 0, 127, 0.14)",
    "accent-3": "rgba(154, 123, 255, 0.16)",
}


def label(value, fallback: str = "not set yet") -> dict:
    """
    Render-ready text for a field that may still be a [BRACKET] placeholder.
    Templates show `unset` ones as struck-through text rather than linking to
    an address that does not exist.
    """
    text = str(value or "").strip()
    if not text or is_placeholder(text):
        return {"text": text or fallback, "unset": True}
    return {"text": text, "unset": False}


def prepare_tools(tools: list[dict], pillars: list[dict]) -> list[dict]:
    """Attach the accent, pillar name and render-ready meta fields for tools.html."""
    pillar_by_id = {p["id"]: p for p in pillars}
    out = []
    for tool in tools:
        tool = dict(tool)
        pillar = pillar_by_id.get(tool.get("pillar"))
        raw_accent = pillar["accent"] if pillar else "accent-1"
        tool["accent"] = "accent-3-text" if raw_accent == "accent-3" else raw_accent
        tool["accent_bg"] = ACCENT_BG[raw_accent]
        tool["pillar_title"] = pillar.get("card_title") or pillar["title"] if pillar else None

        url = str(tool.get("url") or "").strip()
        tool["url_unset"] = is_placeholder(url) or not url

        paper = tool.get("paper", {})
        venue = paper.get("venue", "")
        tool["paper_label"] = label(
            f"{paper.get('title', '')} · {venue}" if not is_placeholder(venue) else paper.get("title", "")
        )
        tool["paper_href"] = None if is_placeholder(paper.get("href")) else paper.get("href")
        tool["built_by_label"] = label(tool.get("built_by"))
        tool["repo_label"] = label(tool.get("repo"), "repository not linked yet")
        tool["repo_href"] = None if tool["repo_label"]["unset"] else tool.get("repo")
        tool["host_label"] = label(
            url.replace("https://", "").rstrip("/") if not tool["url_unset"] else url,
            "no public address yet",
        )
        tool["host_href"] = None if tool["url_unset"] else url
        out.append(tool)
    return out


def is_placeholder(value) -> bool:
    """
    A field still carrying a [BRACKET] stand-in — either whole ("[URL]") or
    embedded ("https://[YOUR-DOMAIN]"). Either way it is not usable as an
    address, so nothing should link to it.
    """
    value = str(value or "").strip()
    return "[" in value and "]" in value


def fellowship_awards(entries) -> list[dict]:
    """
    The fellowships band, as written in people.yml. `holders` may be a list of
    names — joined with the same separator throughout — or a single string, for
    a line that is a sentence rather than a roster.

    This used to be derived from `members[].fellowship` so the band and the card
    badges could not disagree. It is written by hand now, which means an award
    that is on a card and not in this list (or the reverse) is possible: the two
    are independent, and keeping them in step is a manual job.
    """
    awards = []
    for entry in entries or []:
        award = dict(entry)
        holders = award.get("holders")
        if isinstance(holders, (list, tuple)):
            award["holders"] = " · ".join(str(h).strip() for h in holders if str(h).strip())
        awards.append(award)
    return awards


def roster_summary(members: list[dict]) -> str:
    """"2 postdocs · 4 doctoral researchers · 1 undergraduate", built from the roles
    actually present so it can never drift out of step with the cards."""
    counts = {}
    for m in members:
        counts[m["role"]] = counts.get(m["role"], 0) + 1
    parts = []
    for role, n in counts.items():
        label = role.lower()
        if n > 1:
            label = label.replace("researcher", "researchers")
        parts.append(f"{n} {label}")
    return " · ".join(parts)


def canonical_for(base_url: str, output_name: str) -> str | None:
    """Absolute address of a built page, or None while site.url is unset."""
    if not base_url:
        return None
    return f"{base_url}/" if output_name == "index.html" else f"{base_url}/{output_name}"


def enabled(item: dict, features: dict) -> bool:
    """A nav item shows unless its `flag` names a feature that is switched off."""
    flag = item.get("flag")
    return True if flag is None else bool(features.get(flag))


def prepare_out() -> None:
    """
    Rebuild the output directory from scratch, then copy `static/` into it.

    Starting empty is what makes a feature flag real: a page that is no longer
    built cannot linger from a previous run, because nothing survives.
    """
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    shutil.copytree(
        ROOT / "static",
        OUT / "static",
        ignore=shutil.ignore_patterns(".DS_Store"),
    )


def build() -> int:
    site = load_yaml("site")
    if not site:
        sys.exit("content/site.yml is missing or empty")

    features = site.get("features", {})
    nav = [i for i in site.get("nav", []) if enabled(i, features)]
    footer_nav = [i for i in site.get("footer_nav", []) if enabled(i, features)]

    research = load_yaml("research")
    people = load_yaml("people")
    disabled_pages = {out for _, out, flag in PAGES if flag and not features.get(flag)}

    pi = dict(people.get("pi", {}))
    pi["links"] = normalise_links(pi.get("links"), disabled_pages)
    # One string with " · " between entries — the same shape as site.recognition,
    # so split it the same way and let the template mark the first entry.
    pi["honours"] = [h.strip() for h in str(pi.get("honours") or "").split("·") if h.strip()]
    members = []
    for member in people.get("members", []):
        member = dict(member)
        member["links"] = normalise_links(member.get("links"), disabled_pages)
        # A [BRACKET] stand-in is not an award or a year. Drop it here, once, so
        # the badge on the card and the fellowships band below can never
        # disagree about what is filled in — the band used to guard against this
        # and the badge's tooltip did not, which put "Herbold Fellowship, [YEAR]"
        # on screen.
        for field in ("fellowship", "fellowship_year"):
            if is_placeholder(member.get(field)):
                member.pop(field, None)
        members.append(member)
    tools_doc = load_yaml("tools")
    # A tool with enabled: false is invisible everywhere — landing band,
    # research embeds, publication chips and the tools page alike.
    tools = [t for t in tools_doc.get("tools", []) if t.get("enabled", True)]
    news = render_news(load_yaml("news").get("news", []))
    posts = load_posts() if features.get("studies") else []
    papers = load_papers()
    selected_papers = resolve_tool_links([p for p in papers if p["selected"]], tools, features)
    papers_by_year = [
        {"year": g["year"], "papers": resolve_tool_links(g["papers"], tools, features)}
        for g in group_by_year(papers)
    ]
    # Pillars cite papers by BibTeX key; the metadata is read from the bib so it
    # exists in exactly one place. An unknown key is skipped and reported.
    papers_by_key = {p["key"]: p for p in papers}
    missing_keys = []

    # A tool with no usable url cannot be embedded or linked, so it is dropped
    # from the landing band and the research embeds. tools.html still lists it.
    openable = [t for t in tools if not is_placeholder(t.get("url")) and t.get("url")]
    openable_by_id = {t["id"]: t for t in openable}

    tools_page = prepare_tools(tools, research.get("pillars", []))

    # Attach each pillar's tool entries so templates never touch tools.yml.
    # With the tools feature off, no pillar gets any, and every embed and
    # "live tool" marker disappears with them.
    by_id = {t["id"]: t for t in tools}
    pillars = []
    for index, pillar in enumerate(research.get("pillars", [])):
        pillar = dict(pillar)
        # Number and accent follow position unless the pillar names its own, so
        # adding a fourth pillar needs no renumbering and no colour decision.
        pillar.setdefault("number", f"{index + 1:02d}")
        pillar.setdefault("accent", PILLAR_ACCENTS[index % len(PILLAR_ACCENTS)])
        ids = pillar.get("tools", []) if features.get("tools") else []
        pillar["tool_objs"] = [openable_by_id[i] for i in ids if i in openable_by_id]

        resolved = []
        for key in pillar.get("papers", []) or []:
            paper = papers_by_key.get(key)
            if paper is None:
                missing_keys.append((pillar["id"], key))
                continue
            resolved.append(paper)
        pillar["papers"] = resolved
        pillars.append(pillar)


    landing = site.get("landing", {})
    show_tools_band = features.get("tools") and landing.get("tools_band", True)
    featured_tool = next((t for t in tools if t.get("featured")), None) if show_tools_band else None

    # The landing band lists at most `tool_rows`, featured first, and marks any
    # entry whose url is still a placeholder so it is not rendered as a link.
    landing_tools = sorted(openable, key=lambda t: not t.get("featured"))[
        : landing.get("tool_rows", 3)
    ]

    base_url = "" if is_placeholder(site.get("url")) else str(site.get("url", "")).rstrip("/")
    hero = research.get("hero_figure", {}).get("src", "")
    og_image = f"{base_url}/{hero}" if base_url and hero else None

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,  # a typo in a template is an error, not a blank
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
    )

    prepare_out()

    written = 0
    skipped = []
    published: list[str] = []
    for template_name, output_name, flag in PAGES:
        if flag is not None and not features.get(flag):
            skipped.append(output_name)
            continue
        template = env.get_template(template_name)
        html = template.render(
            site=site,
            features=features,
            analytics=site.get("analytics") or {},
            nav=nav,
            footer_nav=footer_nav,
            socials=site.get("socials", []),
            page_href=output_name,
            # 404.html is served from every depth, so its links have to be
            # root-relative rather than relative to where it happens to sit.
            asset_prefix="/" if output_name == "404.html" else "",
            # The landing page's address is the bare root; "/index.html" is a
            # second URL for the same page, which is what canonical exists to
            # prevent. A 404 gets none: it is not a page to link to or index.
            canonical=None if output_name == "404.html" else canonical_for(base_url, output_name),
            og_image=og_image,
            pillars=pillars[: landing.get("pillar_count")] if output_name == "index.html" and landing.get("pillar_count") else pillars,
            hero_figure=with_size(research.get("hero_figure", {})),
            tools=tools_page if output_name == "tools.html" else tools,
            featured_tool=featured_tool,
            tools_intro=tools_doc.get("intro", ""),
            tools_aside=tools_doc.get("aside", ""),
            news=news,
            landing_tools=landing_tools if show_tools_band else [],
            landing_news_count=landing.get("news_count", 3),
            tool_total=len(tools),
            selected_papers=selected_papers,
            papers_by_year=papers_by_year,
            paper_count=len(papers),
            posts=posts,
            cv=load_yaml("cv"),
            teaching=load_yaml("teaching"),
            support=research.get("support", ""),
            pi=pi,
            members=members,
            fellowships=fellowship_awards(people.get("fellowships", {}).get("awards")),
            fellowships_intro=people.get("fellowships", {}).get("intro"),
            fellowship_badges=people.get("fellowships", {}).get("badges", True),
            join=people.get("join", {}),
            group_photo=people.get("group_photo", {}),
            alumni=people.get("alumni", []),
            roster_summary=roster_summary(members),
            accent_bg=ACCENT_BG,
        )
        (OUT / output_name).write_text(html, encoding="utf-8")
        written += 1
        # 404 is a fallback, not an address — it does not belong in a sitemap.
        if output_name != "404.html":
            published.append(output_name)

    if posts:
        post_template = env.get_template("post.html")
        posts_dir = OUT / "studies"
        posts_dir.mkdir(exist_ok=True)
        for post in posts:
            html = post_template.render(
                site=site, features=features, nav=nav, footer_nav=footer_nav,
                analytics=site.get("analytics") or {},
                socials=site.get("socials", []), page_href="studies.html", post=post,
                asset_prefix="../",
                canonical=f"{base_url}/{post['href']}" if base_url else None,
                og_image=og_image,
            )
            (posts_dir / f"{post['slug']}.html").write_text(html, encoding="utf-8")
        (OUT / "feed.xml").write_text(render_feed(posts, site), encoding="utf-8")
        written += len(posts) + 1

    # Both need absolute URLs, so both wait until site.url is filled in. When it
    # is not, any stale copies are removed rather than left pointing nowhere.
    sitemap_path = OUT / "sitemap.xml"
    robots_path = OUT / "robots.txt"
    if base_url:
        locations = [canonical_for(base_url, name) for name in published]
        locations += [f"{base_url}/{post['href']}" for post in posts]
        sitemap_path.write_text(render_sitemap(locations), encoding="utf-8")
        robots_path.write_text(
            f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n",
            encoding="utf-8",
        )
        written += 2
    elif robots_path.exists():
        robots_path.unlink()

    print(f"built {written} page{'s' if written != 1 else ''}")
    if skipped:
        print(f"skipped (feature off): {', '.join(skipped)}")
    problems = check_links(OUT)
    if problems:
        print(f"  {len(problems)} link problem(s):")
        for problem in problems:
            print(f"    {problem}")
    else:
        print("  links: all internal targets and anchors resolve")

    for pillar_id, key in missing_keys:
        print(f"  warning: pillar '{pillar_id}' cites '{key}', which is not in papers.bib")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="serve on localhost:8000 after building")
    args = parser.parse_args()

    build()

    if args.serve:
        import http.server
        import socketserver

        handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(OUT), **kw)
        with socketserver.TCPServer(("", 8123), handler) as httpd:
            print("serving http://localhost:8123  (ctrl-c to stop)")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print()


if __name__ == "__main__":
    main()
