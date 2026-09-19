"""Design tests for the China Pinginsider Hugo site.

The suite is split in two families:

* template and build contracts, checked against a real Hugo build written to a
  temporary directory so the editorial content workflow is never touched;
* real browser checks with Playwright against that same build, covering both
  languages, populated and empty sections, taxonomy pages and one article.

Nothing here asserts fixed article copy or a fixed number of articles: the
current landing story is read back from the build itself. Cardinality 0, 1 and
many is only exercised through a throwaway fixture site in a temp directory.
"""

import http.server
import os
import re
import shutil
import subprocess
import tempfile
import threading
from functools import partial
from pathlib import Path
from urllib.request import urlopen

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
HUGO = Path(os.environ.get("HUGO_BIN", str(Path.home() / ".local" / "bin" / "hugo")))
CHROME = os.environ.get(
    "PLAYWRIGHT_CHROMIUM",
    str(Path.home() / ".cache" / "ms-playwright" / "chromium-1234" / "chrome-linux64" / "chrome"),
)
LANGS = ["en", "fr"]
WIDTHS = [360, 390, 768, 1440]

_STATE = {}


# --------------------------------------------------------------------------- #
# module setup: one temp build, one local server, one shared browser
# --------------------------------------------------------------------------- #


class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the test output clean
        pass


def _run_hugo(hugo, source, destination, extra=None):
    cmd = [str(hugo), "-s", str(source), "--destination", str(destination)]
    if extra:
        cmd.extend(extra)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def setUpModule():
    if not HUGO.exists():
        raise RuntimeError(f"Hugo binary not found at {HUGO}")
    build = Path(tempfile.mkdtemp(prefix="cpi-design-build-"))
    result = _run_hugo(HUGO, SITE, build)
    if result.returncode != 0:
        shutil.rmtree(build, ignore_errors=True)
        raise RuntimeError(f"Hugo build failed:\n{result.stdout}\n{result.stderr}")
    _STATE["build"] = build

    handler = partial(_Handler, directory=str(build))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _STATE["server"] = server
    _STATE["base"] = f"http://127.0.0.1:{server.server_address[1]}"

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(executable_path=CHROME)
    _STATE["pw"] = pw
    _STATE["browser"] = browser


def tearDownModule():
    if "browser" in _STATE:
        _STATE["browser"].close()
    if "pw" in _STATE:
        _STATE["pw"].stop()
    if "server" in _STATE:
        _STATE["server"].shutdown()
        _STATE["server"].server_close()
    if "build" in _STATE:
        shutil.rmtree(_STATE["build"], ignore_errors=True)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def build_dir():
    return _STATE["build"]


def base_url():
    return _STATE["base"]


def fetch(path):
    with urlopen(base_url() + path) as response:
        return response.status, response.read().decode("utf-8")


def built_pages():
    return list(build_dir().rglob("index.html"))


def section_dir(lang, wants_articles):
    root = build_dir() / lang
    if not root.is_dir():
        return None
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or not (entry / "index.html").exists():
            continue
        children = [c for c in entry.iterdir() if c.is_dir() and (c / "index.html").exists()]
        if bool(children) == wants_articles:
            return entry
    return None


def first_article_rel(lang):
    root = build_dir() / lang
    for section in sorted(root.iterdir()):
        if not section.is_dir():
            continue
        for article in sorted(section.iterdir()):
            if article.is_dir() and (article / "index.html").exists():
                return f"/{lang}/{section.name}/{article.name}/"
    return None


def browser_page(path, width=1440, height=900):
    page = _STATE["browser"].new_page(viewport={"width": width, "height": height})
    page.goto(base_url() + path, wait_until="networkidle")
    return page


def _new_page(path, width=1440, height=900):
    return browser_page(path, width, height)


def _sample_paths():
    paths = ["/en/", "/fr/"]
    for lang in LANGS:
        populated = section_dir(lang, True)
        empty = section_dir(lang, False)
        if populated:
            paths.append(f"/{lang}/{populated.name}/")
        if empty:
            paths.append(f"/{lang}/{empty.name}/")
    article = first_article_rel("fr")
    if article:
        paths.append(article)
    return paths


# --------------------------------------------------------------------------- #
# Hugo / template contracts
# --------------------------------------------------------------------------- #


class TestBuildContracts:
    def test_build_renders_both_homes(self):
        for lang in LANGS:
            status, html = fetch(f"/{lang}/")
            assert status == 200
            assert "class=\"feature" in html or "class=\"home-lead" in html

    def test_section_pages_are_not_empty(self):
        for lang in LANGS:
            section = section_dir(lang, True)
            assert section is not None, f"no populated section for {lang}"
            status, html = fetch(f"/{lang}/{section.name}/")
            assert status == 200
            assert 'class="card"' in html
            assert len(html) > 1500

    def test_taxonomy_term_page_lists_articles(self):
        taxonomy = build_dir() / "fr" / "tags"
        if not taxonomy.is_dir():
            pytest.skip("no tags taxonomy")
        for term in sorted(taxonomy.iterdir()):
            if term.is_dir() and (term / "index.html").exists():
                _, html = fetch(f"/fr/tags/{term.name}/")
                assert 'class="card"' in html
                return
        pytest.skip("no tag term with articles")

    def test_taxonomy_index_lists_terms(self):
        _, html = fetch("/fr/tags/")
        assert 'class="term-list"' in html
        assert 'class="term-count"' in html

    def test_home_landing_story_is_a_real_page(self):
        article = first_article_rel("fr")
        assert article, "expected at least one built article"
        article_html = (build_dir() / article.strip("/") / "index.html").read_text(encoding="utf-8")
        m = re.search(r"<h1[^>]*>(.*?)</h1>", article_html, re.S)
        assert m, "article has no h1"
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        _, home = fetch("/fr/")
        assert 'class="feature' in home
        assert article in home, "home does not link to a real article"
        assert "class=\"cta\"" in home

    def test_skip_link_and_main_landmark(self):
        for path in ["/fr/", "/en/"]:
            _, html = fetch(path)
            assert 'class="skip-link" href="#main"' in html
            assert 'id="main"' in html

    def test_language_switch_exposes_both_languages(self):
        _, html = fetch("/fr/")
        assert 'class="lang-option' in html
        assert 'hreflang="en"' in html
        assert 'aria-current="true"' in html

    def test_active_section_uses_aria_current(self):
        section = section_dir("fr", True)
        _, html = fetch(f"/fr/{section.name}/")
        assert 'aria-current="page"' in html
        assert "section-link is-current" in html

    def test_no_external_render_dependencies(self):
        forbidden = ["fonts.googleapis", "fonts.gstatic", "cdn."]
        for path in _sample_paths():
            _, html = fetch(path)
            for needle in forbidden:
                assert needle not in html, f"{path} references {needle}"
            assert "<script src=" not in html
            for match in re.findall(r'(?:src|href)="(https?://[^"]+)"', html):
                # only editorial citations may point outside the site
                assert not match.endswith((".css", ".js", ".ttf", ".woff", ".woff2", ".svg", ".png")), match
        css = (build_dir() / "css" / "style.css").read_text(encoding="utf-8")
        assert "url(http" not in css
        assert "googleapis" not in css

    def test_local_assets_exist(self):
        for path in _sample_paths():
            _, html = fetch(path)
            for src in re.findall(r'src="(/[^"]+)"', html):
                target = build_dir() / src.lstrip("/")
                assert target.exists(), f"{path} references missing asset {src}"

    def test_drafts_are_not_built(self):
        assert not (build_dir() / "fr" / "tournaments" / "demo-headtohead").exists()

    def test_reading_measure_between_65_and_72ch(self):
        css = (build_dir() / "css" / "style.css").read_text(encoding="utf-8")
        for selector in [r"\.article-read", r"\.article-head", r"\.sources"]:
            m = re.search(selector + r"\s*\{[^}]*max-width:\s*(\d+)ch", css)
            assert m, f"no ch based reading measure for {selector}"
            assert 65 <= int(m.group(1)) <= 72, (selector, m.group(1))

    def test_motif_assets_are_shipped(self):
        for name in ["motif-tournaments.svg", "motif-players.svg", "motif-gear.svg", "motif-culture.svg", "logo.svg"]:
            assert (build_dir() / "img" / "design" / name).exists(), name


class TestI18n:
    def _load(self, lang):
        return yaml.safe_load((SITE / "i18n" / f"{lang}.yaml").read_text(encoding="utf-8"))

    def test_new_labels_exist_in_both_languages(self):
        en = self._load("en")
        fr = self._load("fr")
        required = [
            "skipToContent",
            "mainNav",
            "breadcrumb",
            "featured",
            "alsoFeatured",
            "readStory",
            "browseSections",
            "deskLabel",
            "languageLabel",
            "taxonomyLabel",
            "related",
            "inSection",
            "bylineBy",
            "tagsTitle",
            "categoriesTitle",
            "latestStories",
        ]
        for key in required:
            assert key in en, f"en missing {key}"
            assert key in fr, f"fr missing {key}"

    def test_french_labels_are_accented(self):
        fr = self._load("fr")
        for key in ["featured", "alsoFeatured", "related", "taxonomyLabel", "categoriesTitle"]:
            assert any(ch in fr[key] for ch in "àâäéèêëîïôöùûüçÀÂÉÈÊÎÔÙÛÇ"), (key, fr[key])

    def test_ui_labels_have_no_dash(self):
        for lang in LANGS:
            values = self._load(lang)
            for key, value in values.items():
                if isinstance(value, str):
                    assert "\u2014" not in value, (lang, key)
                    assert "\u2013" not in value, (lang, key)


class TestHomeCardinality:
    """Cardinality 0 / 1 / many, exercised on a throwaway fixture site."""

    def _build_fixture(self, count):
        root = Path(tempfile.mkdtemp(prefix="cpi-design-fixture-"))
        for part in ["layouts", "i18n", "data"]:
            shutil.copytree(SITE / part, root / part)
        (root / "static").mkdir()
        (root / "content" / "en").mkdir(parents=True)
        section = root / "content" / "fr" / "tournaments"
        section.mkdir(parents=True)
        (section / "_index.md").write_text(
            "---\ntitle: Tournois\ntranslationKey: section-tournaments\n---\n", encoding="utf-8"
        )
        for i in range(count):
            day = 10 + i
            content = (
                "---\n"
                f"title: 'Story {i}'\n"
                f"date: '2026-09-{day:02d}T07:00:00+02:00'\n"
                "section: tournaments\n"
                f"dek: Dek for story {i}.\n"
                "keyPoints:\n"
                "  - one\n"
                "sources:\n"
                "  - publisher: Example\n"
                "    headline: h\n"
                "    url: https://example.com/\n"
                "---\n\n"
                "## Body\n\nText.\n"
            )
            (section / f"story-{i}.md").write_text(content, encoding="utf-8")
        shutil.copy(SITE / "hugo.toml", root / "hugo.toml")
        out = root / "out"
        result = _run_hugo(HUGO, root, out)
        assert result.returncode == 0, result.stderr
        return out

    def test_zero_articles(self):
        home = (self._build_fixture(0) / "fr" / "index.html").read_text(encoding="utf-8")
        assert "feature--empty" in home
        assert 'class="card"' not in home
        assert "tile--empty" in home

    def test_one_article(self):
        home = (self._build_fixture(1) / "fr" / "index.html").read_text(encoding="utf-8")
        assert 'class="feature"' in home
        assert "feature--empty" not in home
        assert "rail-story" not in home
        assert "intro-card" in home
        assert 'class="card"' not in home

    def test_many_articles(self):
        home = (self._build_fixture(4) / "fr" / "index.html").read_text(encoding="utf-8")
        assert 'class="feature"' in home
        assert "rail-story" in home
        assert 'class="cards"' in home
        assert home.count('class="card"') == 2  # the four stories minus lead and secondary


# --------------------------------------------------------------------------- #
# real browser checks
# --------------------------------------------------------------------------- #


class TestBrowser:
    def test_no_console_errors_or_failed_assets(self):
        for path in _sample_paths():
            page = _new_page(path)
            errors = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            failed = []
            page.on(
                "response",
                lambda r: failed.append(f"{r.status} {r.url}")
                if r.status >= 400 and "favicon.ico" not in r.url
                else None,
            )
            page.reload(wait_until="networkidle")
            page.close()
            assert not errors, (path, errors)
            assert not failed, (path, failed)

    def test_no_horizontal_overflow_across_widths(self):
        for path in _sample_paths():
            for width in WIDTHS:
                page = _new_page(path, width=width, height=900)
                scroll = page.evaluate("Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)")
                inner = page.evaluate("window.innerWidth")
                page.close()
                assert scroll <= inner + 1, (path, width, scroll, inner)

    def test_headings_are_not_truncated(self):
        for path in _sample_paths():
            page = _new_page(path)
            bad = page.evaluate(
                """() => Array.from(document.querySelectorAll('h1,h2,h3'))
                    .filter(h => {
                        const s = getComputedStyle(h);
                        const clipped = s.overflow === 'hidden' || s.overflowX === 'hidden' || s.overflowY === 'hidden';
                        return clipped && (h.scrollHeight > h.clientHeight + 1 || h.scrollWidth > h.clientWidth + 1);
                    })
                    .map(h => h.textContent.trim().slice(0, 60))"""
            )
            page.close()
            assert not bad, (path, bad)

    def test_skip_link_is_first_focus_and_visible(self):
        page = _new_page("/fr/")
        page.keyboard.press("Tab")
        info = page.evaluate(
            """() => {
                const el = document.activeElement;
                return { cls: el.className, href: el.getAttribute('href'),
                         outline: getComputedStyle(el).outlineStyle,
                         width: getComputedStyle(el).outlineWidth };
            }"""
        )
        page.close()
        assert info["cls"] == "skip-link"
        assert info["href"] == "#main"
        assert info["outline"] != "none" and info["width"] != "0px"

    def test_language_switch_navigates(self):
        page = _new_page("/fr/")
        page.click('.lang-option[hreflang="en"]')
        page.wait_for_load_state("networkidle")
        assert "/en/" in page.url
        page.close()

    def test_language_switch_on_article_keeps_story(self):
        article = first_article_rel("fr")
        page = _new_page(article)
        page.click('.lang-option[hreflang="en"]')
        page.wait_for_load_state("networkidle")
        assert "/en/" in page.url
        assert page.locator("article.article").count() == 1
        page.close()

    def test_lead_story_above_the_fold(self):
        page = _new_page("/fr/", width=1440, height=900)
        title = page.locator(".feature-title").first
        cta = page.locator(".cta").first
        assert title.bounding_box()["y"] < 900
        assert cta.bounding_box()["y"] < 900
        page.close()

    def test_article_structure_and_breadcrumb(self):
        page = _new_page(first_article_rel("fr"))
        assert page.locator(".article-head h1").count() == 1
        assert page.locator(".crumbs").count() == 1
        assert page.locator(".prose").count() == 1
        assert page.locator(".sources").count() == 1
        assert page.locator(".keypoints").count() == 1
        page.close()

    def test_top_level_nav_has_44px_targets(self):
        page = _new_page("/fr/")
        heights = page.evaluate(
            "() => Array.from(document.querySelectorAll('.section-link,.lang-option,.cta')).map(a => a.getBoundingClientRect().height)"
        )
        page.close()
        assert heights
        assert min(heights) >= 44
