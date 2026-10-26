# Sam Cloutier's portfolio site: rules for any agent working here

This folder is a one-page site served by GitHub Pages at https://opensourcesam.github.io/.
Sam is a salesperson looking for an account executive or solutions engineer role at an AI company.
The page is for recruiters and hiring managers, most of them on a phone, with under two minutes.

## How the site is made
- `content.toml` holds every word, number and link on the page. Edit only this file for content.
- `build.py` turns it into `index.html`. Standard library only (Python 3.11+). It refuses to build if a
  rule in `content.toml` `[guard]` is broken, if there is an em dash or an exclamation mark, or if a link
  points to a repository marked `link_public = false`.
- `assets/site.css` holds the look (colours are the variables at the top). `assets/site.js` fills the
  timeline line as you scroll; the page works without it.
- `check.py` checks the built page (missing files, broken in-page links, and, with Playwright installed,
  console errors and sideways scrolling at 1280 and 390 px, with screenshots in `build/shots/`).
- `publish.py` uploads changed files through the GitHub CLI when `git push` is not available.

## The loop, every time
1. Edit `content.toml`.
2. `python build.py` (and `python build.py --preview` to see held items marked HOLD in `preview.html`).
3. `python check.py --links`
4. Look at `build/shots/phone.png` and `build/shots/laptop.png` before telling Sam it is done.
5. Show Sam the change as before and after, and publish only on his yes: `git push`, or `python publish.py`.

## Rules for the words (from Sam's voice pack; these are his, not style preferences)
- First person, plain verbs he would say out loud: grew, set up, built, booked, hit, took. Literal language.
- Resume wording first. If a line already exists on one of Sam's sent resumes, use that wording.
- No performance prose: no "here's the thing", no colon reveals, no dramatic one-line reveals,
  no value words with nothing behind them. No em dashes. No exclamation marks. No emoji.
- The smaller number he can defend beats a bigger one he would walk back.
- Nothing about how any job ended. No client, prospect or deal names. Nothing negative about any employer.
- `content.toml` is public. Notes in it must not hold client names or internal figures.

## Rules for the numbers
- Every number must match Sam's private file "Numbers of Record - 2026-10-26.md" in his SecondBrain
  folder (`projects/job-search/`). If a number is not there, ask Sam; do not add it.
- An item that is not settled gets `status = "hold"` with a `hold_reason`. It stays off the live page.
- `build.py` prints every number on the page after each build. Read that line.

## Rules for links
- Never link a private or missing page. A project link shows only when `link_public = true`.
- Second Sales Brain and Circe's Garden are private on GitHub as of 2026-10-26; flip their
  `link_public` to true only after each repository is public and its link opens.

## Look and layout (Sam's choices, 2026-10-26)
Light theme only, warm cream page, deep green accent; Source Serif 4 for headings, Source Sans 3 for text;
avatar beside the name; six-number Highlights grid; single-sided Experience timeline with "More" toggles
after the strongest four lines; project cards. Skills and Education are written but hidden for now.
