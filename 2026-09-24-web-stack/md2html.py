"""Render the CDK lesson markdown to a self-contained HTML page with a TOC."""
import html
import re
import sys

from markdown_it import MarkdownIt

src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()

md = MarkdownIt('commonmark', {'html': False}).enable('table')
tokens = md.parse(text)


def slug(s):
    s = re.sub(r'[^\w\s-]', '', s.lower())
    return re.sub(r'\s', '-', s.strip())


toc = []
title = 'CDK lesson'
for i, tok in enumerate(tokens):
    if tok.type == 'heading_open':
        inline = tokens[i + 1]
        plain = ''.join(c.content for c in inline.children if c.type in ('text', 'code_inline'))
        hid = slug(plain)
        tok.attrSet('id', hid)
        if tok.tag == 'h1':
            title = plain
        elif tok.tag == 'h2':
            toc.append((hid, plain, inline))

body = md.renderer.render(tokens, md.options, {})
# Wrap tables so they scroll instead of widening the page.
body = body.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')

toc_html = '\n'.join(
    f'<li><a href="#{hid}">{md.renderer.renderInline(inline.children, md.options, {})}</a></li>'
    for hid, _, inline in toc
)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CDK Execution Trace</title>
<style>
:root {{
  --bg: #fbfbfa; --fg: #1d1f21; --muted: #5f6368; --accent: #b3541e;
  --code-bg: #f1f0ec; --border: #deddd8; --quote: #f6efe7;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #17181a; --fg: #e4e4e2; --muted: #a0a3a8; --accent: #f0a167;
    --code-bg: #222427; --border: #34373b; --quote: #2a241e;
  }}
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; scroll-padding-top: 16px; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}}
.layout {{ display: grid; grid-template-columns: 1fr; max-width: 1180px; margin: 0 auto; }}
nav {{ padding: 16px; border-bottom: 1px solid var(--border); font-size: 14px; }}
nav h2 {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 0 0 8px; }}
nav ol {{ margin: 0; padding-left: 20px; }}
nav li {{ margin: 3px 0; }}
nav a {{ color: var(--fg); text-decoration: none; }}
nav a:hover {{ color: var(--accent); }}
main {{ padding: 16px; min-width: 0; }}
@media (min-width: 960px) {{
  .layout {{ grid-template-columns: 260px 1fr; }}
  nav {{ position: sticky; top: 0; align-self: start; max-height: 100vh; overflow-y: auto;
         border-bottom: 0; border-right: 1px solid var(--border); padding: 32px 20px; }}
  main {{ padding: 32px 48px; }}
}}
main > * {{ max-width: 820px; }}
h1 {{ font-size: 2rem; line-height: 1.25; margin-top: 0; }}
h2 {{ margin-top: 2.5em; padding-bottom: .3em; border-bottom: 1px solid var(--border); }}
h3 {{ margin-top: 1.8em; }}
a {{ color: var(--accent); }}
hr {{ border: 0; border-top: 1px solid var(--border); margin: 2.5em 0; }}
code {{ font: .88em/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        background: var(--code-bg); padding: .12em .35em; border-radius: 4px; }}
pre {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px;
       padding: 14px 16px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; font-size: .85em; }}
blockquote {{ margin: 1.2em 0; padding: .6em 1em; background: var(--quote);
              border-left: 4px solid var(--accent); border-radius: 0 6px 6px 0; }}
blockquote p {{ margin: .3em 0; }}
.table-wrap {{ overflow-x: auto; margin: 1em 0; }}
table {{ border-collapse: collapse; font-size: .93em; }}
th, td {{ border: 1px solid var(--border); padding: 6px 10px; text-align: left; vertical-align: top; }}
th {{ background: var(--code-bg); }}
</style>
</head>
<body>
<div class="layout">
<nav aria-label="Contents">
<h2>Contents</h2>
<ol>
{toc_html}
</ol>
</nav>
<main>
{body}
</main>
</div>
</body>
</html>
"""
open(dst, 'w', encoding='utf-8').write(page)
print(f'wrote {dst}: {len(toc)} sections, title {html.escape(title)!r}')
