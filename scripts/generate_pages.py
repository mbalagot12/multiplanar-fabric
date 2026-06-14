#!/usr/bin/env python3
"""Generate MkDocs markdown pages from HTML files in content/html/."""

from __future__ import annotations

import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_HTML = ROOT / "content" / "html"
GENERATED = ROOT / "docs" / "generated"
ASSETS = ROOT / "docs" / "assets" / "html"
MKDOCS_YML = ROOT / "mkdocs.yml"

# Hand-maintained MkDocs pages (not generated from content/html/).
STATIC_REFERENCE_NAV: list[tuple[str, str]] = [
    ("Glossary", "glossary.md"),
    (
        "SRv6 uN uSID — Leaf/Spine Config (SONiC vs Arista)",
        "srv6-usid-leaf-spine-config.md",
    ),
]


class HeadAssetParser(HTMLParser):
    """Extract title and head assets (link/script/style) from an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.in_title = False
        self.head_assets: list[str] = []
        self.body_html = ""
        self._in_head = False
        self._in_body = False
        self._body_depth = 0
        self._capture_tag: str | None = None
        self._capture_attrs: list[tuple[str, str | None]] = []
        self._capture_data: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "head":
            self._in_head = True
            return
        if tag == "body":
            self._in_body = True
            self._body_depth = 1
            self._capture_tag = "body"
            self._capture_attrs = attrs
            self._capture_data = []
            return
        if tag == "title" and self._in_head:
            self.in_title = True
            return
        if self._in_head and tag in {"link", "script", "style"}:
            self._capture_tag = tag
            self._capture_attrs = attrs
            self._capture_data = []
            return
        if self._in_body and self._capture_tag == "body":
            self._body_depth += 1
            attrs_str = " ".join(
                f'{name}="{value}"' if value is not None else name
                for name, value in attrs
            )
            self._capture_data.append(f"<{tag}{(' ' + attrs_str) if attrs_str else ''}>")

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self._in_head = False
            return
        if tag == "title" and self._in_head:
            self.in_title = False
            return
        if self._in_head and tag in {"link", "script", "style"} and self._capture_tag == tag:
            self.head_assets.append(self._render_tag(tag, self._capture_attrs, self._capture_data))
            self._capture_tag = None
            return
        if self._in_body and self._capture_tag == "body":
            self._body_depth -= 1
            if self._body_depth == 0:
                self.body_html = "".join(self._capture_data).strip()
                self._in_body = False
                self._capture_tag = None
            else:
                self._capture_data.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        elif self._capture_tag in {"script", "style", "body"}:
            self._capture_data.append(data)

    def _render_tag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
        inner: list[str],
    ) -> str:
        attrs_str = " ".join(
            f'{name}="{value}"' if value is not None else name for name, value in attrs
        )
        if tag in {"link", "script"} and not inner:
            return f"<{tag}{(' ' + attrs_str) if attrs_str else ''}>"
        return f"<{tag}{(' ' + attrs_str) if attrs_str else ''}>{''.join(inner)}</{tag}>"


def normalize_svg_attributes(html: str) -> str:
    """Restore case-sensitive SVG attribute names mangled by HTMLParser."""
    replacements = {
        "viewbox=": "viewBox=",
        "preserveaspectratio=": "preserveAspectRatio=",
        "baseprofile=": "baseProfile=",
        "attributename=": "attributeName=",
        "attributetype=": "attributeType=",
        "gradientunits=": "gradientUnits=",
        "gradienttransform=": "gradientTransform=",
        "spreadmethod=": "spreadMethod=",
        "patternunits=": "patternUnits=",
        "patterncontentunits=": "patternContentUnits=",
        "patterntransform=": "patternTransform=",
        "clippathunits=": "clipPathUnits=",
        "maskcontentunits=": "maskContentUnits=",
        "maskunits=": "maskUnits=",
        "filterunits=": "filterUnits=",
        "primitiveunits=": "primitiveUnits=",
        "refx=": "refX=",
        "refy=": "refY=",
        "markerwidth=": "markerWidth=",
        "markerheight=": "markerHeight=",
        "markerunits=": "markerUnits=",
        "strokedasharray=": "strokeDasharray=",
        "strokedashoffset=": "strokeDashoffset=",
        "strokelinecap=": "strokeLinecap=",
        "strokelinejoin=": "strokeLinejoin=",
        "strokemiterlimit=": "strokeMiterlimit=",
        "textanchor=": "textAnchor=",
        "dominantbaseline=": "dominantBaseline=",
        "fontfamily=": "fontFamily=",
        "fontsize=": "fontSize=",
        "fontweight=": "fontWeight=",
        "fontstyle=": "fontStyle=",
    }
    for lower, proper in replacements.items():
        html = html.replace(lower, proper)
    return html


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    return slug or "page"


def rewrite_asset_paths(html: str, page_slug: str) -> str:
    """Rewrite relative asset references to docs/assets/html/<page_slug>/."""

    def repl(match: re.Match[str]) -> str:
        attr, path = match.group(1), match.group(2)
        if path.startswith(("http://", "https://", "//", "data:", "#", "/")):
            return match.group(0)
        return f'{attr}="../assets/html/{page_slug}/{path}"'

    return re.sub(
        r'(href|src)=["\']([^"\']+)["\']',
        repl,
        html,
    )


def copy_page_assets(html_path: Path, page_slug: str) -> None:
    source_dir = html_path.parent
    dest_dir = ASSETS / page_slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    for asset in source_dir.iterdir():
        if asset.is_file() and asset.suffix.lower() in {
            ".css",
            ".js",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
            ".woff",
            ".woff2",
            ".ttf",
            ".ico",
        }:
            shutil.copy2(asset, dest_dir / asset.name)


def parse_html(html_path: Path) -> tuple[str, str, str]:
    raw = html_path.read_text(encoding="utf-8")
    parser = HeadAssetParser()
    parser.feed(raw)

    title = parser.title.strip() or html_path.stem.replace("-", " ").replace("_", " ").title()
    page_slug = slugify(html_path.stem)
    body = parser.body_html or raw
    head_assets = "\n".join(parser.head_assets)

    body = normalize_svg_attributes(body)
    body = rewrite_asset_paths(body, page_slug)
    head_assets = rewrite_asset_paths(head_assets, page_slug)
    copy_page_assets(html_path, page_slug)

    return title, head_assets, body


def build_markdown(title: str, head_assets: str, body: str) -> str:
    lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        "---",
        "",
        '<div class="html-page">',
    ]
    if head_assets:
        lines.extend(["", head_assets, ""])
    lines.extend([body, "", "</div>", ""])
    return "\n".join(lines)


def collect_html_files() -> list[Path]:
    if not CONTENT_HTML.exists():
        CONTENT_HTML.mkdir(parents=True)
        return []
    return sorted(
        path
        for path in CONTENT_HTML.rglob("*.html")
        if path.is_file() and not path.name.startswith(".")
    )


def update_nav(generated_entries: list[tuple[str, str]]) -> None:
    nav_lines = ["nav:", "  - Home: index.md"]
    if STATIC_REFERENCE_NAV:
        nav_lines.append("  - Reference:")
        for title, rel_path in STATIC_REFERENCE_NAV:
            nav_lines.append(f"      - {title}: {rel_path}")
    if generated_entries:
        nav_lines.append("  - Pages:")
        for title, rel_path in generated_entries:
            nav_lines.append(f"      - {title}: {rel_path}")
    nav_block = "\n".join(nav_lines) + "\n"

    content = MKDOCS_YML.read_text(encoding="utf-8")
    if "nav:" not in content:
        MKDOCS_YML.write_text(content.rstrip() + "\n\n" + nav_block, encoding="utf-8")
        return

    updated = re.sub(r"nav:\n(?:  .+\n)*", nav_block, content)
    MKDOCS_YML.write_text(updated, encoding="utf-8")


def main() -> int:
    GENERATED.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    for old_md in GENERATED.rglob("*.md"):
        old_md.unlink()

    html_files = collect_html_files()
    nav_entries: list[tuple[str, str]] = []

    for html_path in html_files:
        rel = html_path.relative_to(CONTENT_HTML)
        page_slug = slugify(html_path.stem)
        if len(rel.parts) > 1:
            subdir = "/".join(slugify(part) for part in rel.parts[:-1])
            out_dir = GENERATED / subdir
            out_dir.mkdir(parents=True, exist_ok=True)
            md_name = f"{page_slug}.md"
            md_path = out_dir / md_name
            nav_path = f"generated/{subdir}/{md_name}"
        else:
            md_path = GENERATED / f"{page_slug}.md"
            nav_path = f"generated/{page_slug}.md"

        title, head_assets, body = parse_html(html_path)
        md_path.write_text(build_markdown(title, head_assets, body), encoding="utf-8")
        nav_entries.append((title, nav_path))
        print(f"Generated {md_path.relative_to(ROOT)}")

    update_nav(nav_entries)

    if not html_files:
        print("No HTML files found in content/html/. Add .html files and re-run make generate.")
    else:
        print(f"Generated {len(html_files)} page(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
