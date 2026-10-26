# opensourcesam.github.io

Sam Cloutier's portfolio page, served by GitHub Pages from the root of this repository.

## Change the page
1. Edit `content.toml`. Every word, number and link lives there. `status = "hold"` keeps an item off the page.
2. Build: `python build.py` (Python 3.11 or newer; nothing to install).
3. Check: `python check.py --links` (the browser part needs `pip install playwright` and
   `python -m playwright install chromium` once).
4. Publish: `git push`, or `python publish.py` if git push is not available (needs the GitHub CLI, logged in).

## Files
| File | What it is |
|---|---|
| `content.toml` | All page content, section switches, and the guard list of words and numbers that must never appear |
| `build.py` | Writes `index.html` from `content.toml`; stops if a rule is broken |
| `check.py` | Checks the built page; saves laptop and phone screenshots to `build/shots/` |
| `publish.py` | Uploads changed files through the GitHub API |
| `index.html` | The built page (generated; do not edit by hand) |
| `assets/` | `site.css`, `site.js`, the favicon and images |
| `CLAUDE.md` | Rules for AI agents editing this site |

The game screenshots come from Circe's Garden, which uses Liberated Pixel Cup art; its repository credits every artist.
