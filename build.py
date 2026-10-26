"""Build index.html from content.toml.

    python build.py             writes index.html (only items with status = "ready")
    python build.py --preview   writes preview.html with held items shown and marked HOLD (not published)

Standard library only (Python 3.11 or newer). The build stops with a clear message if content.toml
breaks a rule in its [guard] table, uses an em dash, or links a page that is not public yet.
"""
from __future__ import annotations

import html
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FONTS = ("https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400..700"
         "&family=Source+Sans+3:wght@400;600;700&display=swap")
FIGURE = re.compile(r"(\$[\d.,]+[MK]?|\d+(?:\.\d+)?%|\d+\+)")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


class Page:
    def __init__(self, content: dict, preview: bool):
        self.c = content
        self.preview = preview
        self.site = content["site"]

    # ---------------------------------------------------------------- helpers
    def shown(self, item: dict) -> bool:
        return item.get("status", "ready") == "ready" or self.preview

    def hold_mark(self, item: dict) -> str:
        if self.preview and item.get("status") == "hold":
            return f' <span class="hold-badge" title="{esc(item.get("hold_reason", ""))}">HOLD</span>'
        return ""

    def hold_cls(self, item: dict) -> str:
        return " is-hold" if self.preview and item.get("status") == "hold" else ""

    @staticmethod
    def figures(text: str) -> str:
        """Escape a line and put its numbers in bold green. The words are unchanged."""
        return FIGURE.sub(r'<b class="fig">\1</b>', esc(text))

    @staticmethod
    def tags(items: list[str]) -> str:
        if not items:
            return ""
        return '<ul class="tags" aria-label="Tools and topics">' + "".join(f"<li>{esc(t)}</li>" for t in items) + "</ul>"

    def buttons(self) -> str:
        s = self.site
        return (f'<p class="btns"><a class="btn primary" href="mailto:{esc(s["email"])}">Email me</a>'
                f'<a class="btn" href="{esc(s["linkedin"])}">LinkedIn</a>'
                f'<a class="btn" href="{esc(s["github"])}">GitHub</a></p>')

    # ---------------------------------------------------------------- sections
    def header(self) -> str:
        s = self.site
        kicker = "".join(f"<span>{esc(k)}</span>" for k in s["kicker"])
        return f"""<header class="hero" id="top">
  <div class="nameblock">
    <img class="avatar" src="{esc(s['avatar'])}" alt="{esc(s['avatar_alt'])}" width="460" height="460">
    <h1>{esc(s['first_name'])} <em>{esc(s['last_name'])}</em></h1>
  </div>
  <p class="kicker">{kicker}</p>
  <p class="lead">{esc(s['headline'])}</p>
  <p class="sub">{esc(s['looking_for'])}</p>
  {self.buttons()}
</header>"""

    def highlights(self) -> str:
        items = [h for h in self.c.get("highlights", []) if self.shown(h)]
        if not items:
            return ""
        lis = "".join(f'<li class="{self.hold_cls(h).strip()}"><strong>{esc(h["number"])}</strong>'
                      f'<span>{esc(h["text"])}{self.hold_mark(h)}</span></li>' for h in items)
        return (f'<section aria-labelledby="results-h" style="padding-top:0"><div class="wrap">'
                f'<h2 id="results-h" class="hl-h">Highlights</h2><ul class="results n{len(items)}">{lis}</ul>'
                f'</div></section>')

    def job_card(self, job: dict) -> str:
        note = f' <span class="note">({esc(job["note"])})</span>' if job.get("note") else ""
        head = f'<h3>{esc(job["role"])}{note}{self.hold_mark(job)}</h3><p class="org">{esc(job["org"])}</p>'
        lines = [l for l in job.get("lines", []) if self.shown(l)]
        if not lines:
            return head

        def li(line: dict) -> str:
            cls = self.hold_cls(line).strip()
            attr = f' class="{cls}"' if cls else ""
            return f"<li{attr}>{self.figures(line['text'])}{self.hold_mark(line)}</li>"

        first = job.get("show_first", 0) or len(lines)
        out = head + "<ul>" + "".join(li(l) for l in lines[:first]) + "</ul>"
        rest = lines[first:]
        if rest:
            company = job["org"].split(",")[0]
            out += (f'<details class="more-lines"><summary aria-label="More about {esc(job["role"])} at {esc(company)}">'
                    f'More</summary><ul>' + "".join(li(l) for l in rest) + "</ul></details>")
        return out

    def experience(self) -> str:
        items = []
        for job in (j for j in self.c.get("jobs", []) if self.shown(j)):
            cls = "tl-item reveal" + (" compact" if job.get("compact") else "") + self.hold_cls(job)
            items.append(f'<li class="{cls}"><span class="tl-dot" aria-hidden="true"></span>'
                         f'<p class="tl-date">{esc(job["dates"])}</p><article class="tl-card">{self.job_card(job)}</article></li>')
        return (f'<section id="experience" aria-labelledby="exp-h"><div class="wrap"><h2 id="exp-h">Experience</h2>'
                f'<div class="tl" data-fill><div class="tl-line" aria-hidden="true"><div class="tl-fill"></div></div>'
                f'<ol class="tl-list">{"".join(items)}</ol></div></div></section>')

    def education(self) -> str:
        items = [e for e in self.c.get("education", []) if self.shown(e)]
        if not items:
            return ""
        lis = "".join(f'<li class="tl-item compact reveal{self.hold_cls(e)}"><span class="tl-dot" aria-hidden="true"></span>'
                      f'<p class="tl-date">{esc(e["dates"])}</p><article class="tl-card"><h3>{esc(e["school"])}{self.hold_mark(e)}</h3>'
                      f'<p class="org">{esc(e["degree"])}</p></article></li>' for e in items)
        return (f'<section id="education" aria-labelledby="edu-h"><div class="wrap"><h2 id="edu-h">Education</h2>'
                f'<div class="tl"><ol class="tl-list">{lis}</ol></div></div></section>')

    def skills(self) -> str:
        items = [s for s in self.c.get("skills", []) if self.shown(s)]
        if not items:
            return ""
        lis = "".join(f'<li class="{self.hold_cls(s).strip()}"><h3>{esc(s["title"])}{self.hold_mark(s)}</h3><p>{esc(s["text"])}</p></li>'
                      for s in items)
        return f'<section id="skills" aria-labelledby="skills-h"><div class="wrap"><h2 id="skills-h">Skills</h2><ul class="skills">{lis}</ul></div></section>'

    def visual(self, kind: str) -> str:
        if kind == "flow":
            return ('<div class="vis"><div class="viz viz-flow" aria-hidden="true"><span>Telegram</span><i>&darr;</i>'
                    '<span class="core">Claude Code agent on my Linux server</span><i>&darr;</i>'
                    '<span class="row"><em>Notion</em><em>Todoist</em><em>Google Calendar</em></span></div></div>')
        if kind == "shots":
            imgs = "".join(f'<img src="{esc(s["file"])}" alt="{esc(s["alt"])}" width="810" height="930">'
                           for s in self.c.get("shots", []))
            return f'<div class="vis"><div class="shots">{imgs}</div></div>'
        return ""

    def projects(self) -> str:
        cards = []
        for p in (p for p in self.c.get("projects", []) if self.shown(p)):
            vis = self.visual(p.get("visual", ""))
            cls = "project reveal" + (" game" if p.get("visual") == "shots" else "") + ("" if vis else " novis") + self.hold_cls(p)
            when = f'<span class="when">{esc(p["when"])}</span>' if p.get("when") else ""
            paras = "".join(f"<p>{esc(t)}</p>" for t in p.get("paragraphs", []))
            link = ""
            if p.get("link") and p.get("link_public"):
                link = f'<p class="more"><a href="{esc(p["link"])}">{esc(p["link_text"])}</a></p>'
            cards.append(f'<article class="{cls}"><div class="txt">{when}<h3>{esc(p["title"])}{self.hold_mark(p)}</h3>'
                         f'{paras}{link}{self.tags(p.get("tags", []))}</div>{vis}</article>')
        return (f'<section id="projects" aria-labelledby="proj-h"><div class="wrap"><h2 id="proj-h">Projects</h2>'
                f'<div class="projects">{"".join(cards)}</div></div></section>')

    def about(self) -> str:
        s = self.site
        paras = "".join(f"<p>{esc(t)}</p>" for t in self.c["about"]["paragraphs"])
        return (f'<section id="about" aria-labelledby="about-h"><div class="wrap"><h2 id="about-h">About</h2>'
                f'<div class="about" style="margin-top:1.5rem"><img src="{esc(s["avatar"])}" alt="{esc(s["avatar_alt"])}" '
                f'width="460" height="460"><div>{paras}</div></div></div></section>')

    def contact(self) -> str:
        s = self.site
        mail = f'<a href="mailto:{esc(s["email"])}">{esc(s["email"])}</a>'
        line = esc(self.c["contact"]["line"]).replace(esc("{email}"), mail)
        return (f'<section id="contact" aria-labelledby="contact-h"><div class="wrap"><div class="contact-box">'
                f'<h2 id="contact-h">Contact</h2><p class="contact-line">{line}</p>'
                f'<p class="contact-links"><a href="{esc(s["linkedin"])}">LinkedIn</a><a href="{esc(s["github"])}">GitHub</a></p>'
                f'</div></div></section>')

    # ---------------------------------------------------------------- page
    def render(self) -> str:
        s, sec = self.site, self.c["sections"]
        order = [("highlights", self.highlights), ("experience", self.experience), ("education", self.education),
                 ("skills", self.skills), ("projects", self.projects), ("about", self.about), ("contact", self.contact)]
        body = "\n".join(fn() for key, fn in order if sec.get(key, False) or (self.preview and key in ("education", "skills")))
        nav_items = [("experience", "Experience"), ("education", "Education"), ("skills", "Skills"),
                     ("projects", "Projects"), ("about", "About"), ("contact", "Contact")]
        nav = "".join(f'<a href="#{k}">{label}</a>' for k, label in nav_items if sec.get(k, False))
        banner = ('<p style="background:#fde68a;color:#713f12;padding:10px 16px;margin:0;font-weight:700">'
                  'PREVIEW: items marked HOLD are not on the live page.</p>') if self.preview else ""
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="light">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(s['first_name'])} {esc(s['last_name'])}</title>
<meta name="description" content="{esc(s['description'])}">
<meta property="og:title" content="{esc(s['first_name'])} {esc(s['last_name'])}">
<meta property="og:description" content="{esc(s['description'])}">
<meta property="og:image" content="{esc(s['url'])}{esc(s['avatar'])}">
<meta property="og:url" content="{esc(s['url'])}">
<meta property="og:type" content="website">
<link rel="icon" href="assets/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
{banner}<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
<div class="top"><a class="mark" href="#top">{esc(s['first_name'])} {esc(s['last_name'])}</a><nav class="nav" aria-label="Sections">{nav}</nav></div>
{self.header()}
</div>
<main id="main">
{body}
</main>
<footer><div class="wrap">Toronto. Last updated {esc(s['updated'])}.</div></footer>
<script src="assets/site.js"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- checks
def visible_text(page_html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page_html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text))


def problems(content: dict, page_html: str) -> list[str]:
    found = []
    text = visible_text(page_html)
    guard = content.get("guard", {})
    for phrase in guard.get("never", []):
        if phrase.lower() in text.lower():
            found.append(f'"{phrase}" is on the never-use list (content.toml [guard]).')
    for word in guard.get("banned_words", []):
        if re.search(rf"\b{re.escape(word)}\b", text, flags=re.I):
            found.append(f'"{word}" is a banned word (content.toml [guard]).')
    if "—" in text:
        found.append("An em dash is on the page. Rewrite the sentence instead.")
    if "!" in text:
        found.append("An exclamation mark is on the page.")
    for p in content.get("projects", []):
        if p.get("link") and not p.get("link_public") and p["link"] in page_html:
            found.append(f'The link to {p["link"]} is on the page, but link_public is false.')
    if page_html.count("<h1") != 1:
        found.append("The page must have exactly one h1.")
    for m in re.finditer(r"<img(?![^>]*\balt=)[^>]*>", page_html):
        found.append(f"An image has no alt text: {m.group(0)[:80]}")
    for anchor in set(re.findall(r'href="#([\w-]+)"', page_html)):
        if f'id="{anchor}"' not in page_html:
            found.append(f'The link "#{anchor}" points to a section that is not on the page.')
    return found


def main() -> int:
    preview = "--preview" in sys.argv
    content = tomllib.loads((ROOT / "content.toml").read_text(encoding="utf-8"))
    page_html = Page(content, preview).render()
    issues = [] if preview else problems(content, page_html)
    if issues:
        print("Not built. Fix these in content.toml:")
        for issue in issues:
            print("  -", issue)
        return 1
    out = ROOT / ("preview.html" if preview else "index.html")
    out.write_text(page_html, encoding="utf-8")
    held = [h for h in content.get("highlights", []) if h.get("status") == "hold"]
    held += [l for j in content.get("jobs", []) for l in j.get("lines", []) if l.get("status") == "hold"]
    numbers = sorted(set(FIGURE.findall(visible_text(page_html))))
    print(f"Wrote {out.name}.")
    print(f"Numbers on the page (each must match the Numbers of Record): {', '.join(numbers)}")
    if held and not preview:
        print(f"{len(held)} item(s) on hold, not on the page. See them with: python build.py --preview")
    return 0


if __name__ == "__main__":
    sys.exit(main())
