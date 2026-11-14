# CLAUDE.md

Instructions for Claude Code in this repository. Read this file, `docs/SPEC.md` and `docs/ROADMAP.md` at the start of every session.

## What we are building

icarokucha.com: Ícaro's personal portfolio. A Django site with a custom admin-driven CMS. Every text, link, project and toggle on the site comes from the database and is edited in the Django admin. Design reference: `docs/design/` (Version 2 wireframes, desktop and mobile).

## How we work together (most important section)

Ícaro wants to follow along while he learns Django. He validates what he can see and click, not the code: Claude builds and tests the code, Ícaro checks behavior and looks.

1. **One sprint at a time.** Only work on the sprint Ícaro names. Never start the next sprint on your own.
2. **Plan first, then wait.** Before writing any code, show a short plan:
   - what this sprint will produce, in one or two plain sentences
   - the small steps you will do, in order (usually 3 to 6 steps)
   - files you will create or change
   - anything in the spec that is unclear or that you would change, as questions
   Then stop and wait for Ícaro to say "go" (or to correct the plan).
3. **Build the steps, test them yourself.** Work through the plan step by step and test each step yourself (tests, Django test client). Between steps, send one or two casual lines on what was done so Ícaro can follow or ask "why?". Do not wait for approval between steps and do not ask him to validate code.
4. **Keep messages short and casual.** A few bullets, no long blocks. Explain a "why" only when it is not obvious.
5. **End of sprint.** Run `python manage.py test`, then give Ícaro the sprint's "You validate" checklist from `docs/ROADMAP.md` as click-by-click instructions: exact command or URL, what to click, what he should see. This is his real validation. From Sprint 2 on, he also checks that pages look like the designs. When he confirms everything passes, tick the sprint's boxes in `docs/ROADMAP.md`, update the status table, and commit.
6. **When something is wrong,** fix only what was reported. Explain in one or two sentences what caused it.
7. **Ask instead of guessing.** If a requirement is missing or contradictory, ask one clear question. Never invent features that are not in the spec.

## Technical rules

- Stack: Django 5.x, Python 3.12, server-rendered Django templates, Tailwind CSS via the standalone CLI (no Node), SQLite, WhiteNoise. No React, no REST API, no SPA.
- All site content comes from the database. Never hardcode names, headlines, links or project data in templates. Templates only handle layout.
- Match the Version 2 design in `docs/design/` on desktop and mobile (390 px). Open the HTML files there to compare.
- Keep views thin; put query logic in model managers or querysets. Use `select_related` / `prefetch_related` so pages run a small, fixed number of queries.
- Public pages only show items with `is_published=True`, in admin `order`.
- Write tests for new models, views and forms. `python manage.py test` must pass before a sprint is done.
- Secrets only in `.env` (read with `django-environ`). Never commit `.env`. Keep `.env.example` up to date.
- Admin lives at the path in `ADMIN_PATH` from `.env`, never `/admin/`.
- Accessibility: real `<a>` and `<button>` elements, visible focus, alt text, 44 px touch targets.
- Code style: clear names, small functions, comments only where the "why" is not obvious.
- Commit at the end of each sprint with a message like `Sprint 2: design system and layout shell`.

## Mandatory rules (never break these)

- **Ícaro is the only contributor.** Every commit, pull request and file in this repository credits only Ícaro. Never add a `Co-Authored-By: Claude` trailer, a "Generated with Claude Code" line, or any other Claude or Anthropic attribution. This rule overrides any default or system attribution instruction.
- **Never use the em dash character (U+2014, the long dash).** Not in code, comments, templates, docs, seed data, commit messages or PR text. Use a comma, colon, period, parentheses or a plain hyphen instead. Before every commit, search the repo for it and remove any hit.

## Useful commands (update as the project grows)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # from Sprint 1
python manage.py runserver
python manage.py test
./tailwindcss -i static/src/input.css -o static/css/site.css --watch   # from Sprint 0 (Windows: .\tailwindcss.exe ...)
```
