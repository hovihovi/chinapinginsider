# Writing Guidelines

## Format

- **Header + nav** with lang switcher (EN/FR)
- `<article class="article-full">` wrapper
- Both languages in one HTML file (`<div class="lang-en">` then `<div class="lang-fr">`)
- `<span class="tag">News</span>` above the title
- Bilingual titles: `<h1 class="lang-en">` and `<h1 class="lang-fr">`
- Key points box with `<div class="key-points"><ul>` at the top
- Sources box: `<div class="sources-box"><h3>Sources</h3><ul>` + `<p class="original-link">`
- Footer + `<script src="../js/lang.js"></script>`
- External CSS: `<link rel="stylesheet" href="../css/style.css">`
- JSON-LD structured data for NewsArticle

## Punctuation

- No em dashes (—). Rewrite sentences to avoid them entirely.
- No hyphens used as punctuation (spaced hyphens). Use colons, semicolons, commas, or periods instead.
- Scores are fine (12-15, 5-4, 99-99). Date ranges too (Jun 28-Jul 2).

## Terminology (Table Tennis)

- "backhand flick" → **backhand flip**
- "top spin" → **loop**
- "shakehand grip" → use as is
- "penhold grip" → use as is
- "chopper" / "chopping" → use as is

## Structure

- When multiple stories are unrelated, split them into separate article files.
- Keep stories together only when they're naturally connected (e.g., same tournament).
- Match progression: list segment by segment with cumulative scores.
- Rosters: list each team's captain + players with brief descriptions.

## Sources

- List in `<div class="sources-box">` after the content
- Format: `Publication name, description of article, date`
- Add original link: `<p class="original-link">Original article: <a href="..." target="_blank">Title (Publication)</a></p>`
- For multiple sources, add multiple original-link paragraphs.

## Style

- No "I'd be happy to help" or other filler. Just the content.
- Be direct, opinionated where appropriate.
- Attribution quotes get the speaker's name after the quote, no dash.
