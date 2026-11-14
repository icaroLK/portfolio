# Roadmap: 8 sprints

Each sprint ends with something Ícaro can open and click. Do them in order. A sprint is done only when every box in its "You validate" list is ticked and `python manage.py test` passes. Commit at the end of each sprint.

## Status

| Sprint | Name | Status |
| --- | --- | --- |
| 0 | Project setup | Done |
| 1 | Models and admin | Done |
| 2 | Design system and layout shell | Not started |
| 3 | Home page | Not started |
| 4 | Project detail page | Not started |
| 5 | About page and contact form | Not started |
| 6 | SEO, performance and polish | Not started |
| 7 | Deploy and go live | Not started |

---

## Sprint 0: Project setup

**Goal in plain words:** an empty Django project that runs on your computer, with styling tools ready.

**Build:**

- Git repo with `.gitignore` (already provided) and `README.md` with run commands.
- Django 5 project named `config`, apps `portfolio` and `contact`.
- Settings split into `config/settings/base.py`, `dev.py`, `prod.py`, reading `.env` with `django-environ`. Add `.env.example`.
- `requirements.txt`.
- Tailwind standalone CLI: `static/src/input.css` → `static/css/site.css`.
- `templates/base.html` loading the fonts and CSS.
- A placeholder home view that says the site is running.

**You validate:**

- [x] `python manage.py runserver` opens a page that says the site is running, in Inter font
- [x] Changing a Tailwind class and rebuilding CSS changes the page
- [x] `.env` is ignored by git; `.env.example` is committed
- [x] README steps work on a fresh clone

## Sprint 1: Models and admin

**Goal in plain words:** the database structure and the admin panel where you will manage all content.

**Build:**

- Every model in SPEC section 4, with migrations.
- Full admin from SPEC section 5: singleton Site settings, drag-and-drop ordering, inlines, list toggles, filters, image previews, read-only inbox.
- Admin at `ADMIN_PATH` from `.env`.
- `seed_demo` management command filling placeholder content: ParkEye, Match Replay System, Barbershop WhatsApp Bot, Telegram Transcription Bot, two experiences, two education entries, four skill groups, three services. Safe to run twice.

**You validate:**

- [x] `python manage.py seed_demo` runs twice without duplicating data
- [x] Site settings opens as a single page with no Add or Delete
- [x] You can create a project with 4 features, 5 stack chips and 3 gallery images in one screen
- [x] Dragging projects changes their order; featured and published toggle from the list
- [x] A 10 MB image or a .exe upload is rejected with a clear message
- [x] `/admin/` returns 404; the custom admin path works

## Sprint 2: Design system and layout shell

**Goal in plain words:** the look of the site (colors, fonts, buttons, cards) and the header and footer that every page shares.

**Build:**

- Tailwind theme with the V2 tokens (SPEC section 8).
- Reusable template partials: buttons (primary, secondary), chips (type tag, tech, skill), eyebrow + section heading, card shell, status badge.
- Header with active link state and mobile menu (vanilla JS).
- Footer driven by Site settings.
- `/styleguide/` page (DEBUG only) showing every component.

**You validate:**

- [ ] `/styleguide/` looks like the V2 designs in `docs/design/`
- [ ] Mobile menu opens and closes by tap and by Escape, and works with the keyboard
- [ ] Editing links in Site settings changes the header and footer
- [ ] Nothing scrolls sideways at 390 px width

## Sprint 3: Home page

**Goal in plain words:** the real home page, built from the database.

**Build:**

- Hero from Site settings, badge toggle.
- Featured projects: large horizontal cards (image on top on mobile).
- More projects grid with `?type=` filter and empty state.
- Prefetched queries, published only, admin order.

**You validate:**

- [ ] Home matches `docs/design/v2-home.html` and `v2-home-mobile.html` with seed data
- [ ] Unpublishing a project removes it; toggling featured moves it between sections
- [ ] Reordering in admin reorders the page
- [ ] Each filter shows only its projects; an empty filter shows the empty state
- [ ] Turning off the badge hides it

## Sprint 4: Project detail page

**Goal in plain words:** the page that opens when someone clicks a project.

**Build:**

- Everything in SPEC section 3, Project detail: header block, conditional buttons, YouTube/Loom embed conversion, What it does, numbered Key features, Tech stack chips, How it works with optional image, gallery, Next project card, styled 404.

**You validate:**

- [ ] A fully filled project matches `docs/design/v2-project.html` and its mobile version
- [ ] A project with only title, pitch, cover and what_it_does shows no empty sections or broken buttons
- [ ] A YouTube link and a Loom link both play inline
- [ ] Next project on the last project goes to the first
- [ ] An unpublished project's URL shows the styled 404

## Sprint 5: About page and contact form

**Goal in plain words:** the About page and a working contact form that saves messages and emails you.

**Build:**

- Intro, Experience cards with `<details>` expand, Education, Skills, Services, contact card, section toggles.
- Contact form: validation, honeypot, rate limit, saved message, notification email (console backend in dev, Resend/Brevo in prod), success message after redirect.
- Inbox in admin.

**You validate:**

- [ ] About matches `docs/design/v2-about.html` and its mobile version; "Show details" works and is absent when details is empty
- [ ] Each section toggle in Site settings hides its section
- [ ] Sending the form shows the success message and the message appears in the admin inbox
- [ ] Empty or invalid fields show errors and keep your input
- [ ] A filled honeypot is silently dropped; a 4th submission in an hour is blocked
- [ ] Refreshing after sending does not resend

## Sprint 6: SEO, performance and polish

**Goal in plain words:** make the site fast, shareable on LinkedIn/WhatsApp, findable on Google and accessible.

**Build:**

- Per-page titles, descriptions, Open Graph tags.
- Sitemap, robots, `/resume/` redirect, `/healthz/`.
- WebP thumbnails, lazy loading, sizes; query count check.
- Accessibility pass (focus, alt text, contrast); custom 500 page.
- Tests for models, views and the form.
- Admin look: modern theme (for example `django-unfold`), cleaner field layout on the project and experience pages.

**You validate:**

- [ ] Lighthouse mobile: Performance 90+, Accessibility 95+, SEO 95+ on Home and one project
- [ ] Pasting a project URL into WhatsApp or LinkedIn shows its cover image and pitch
- [ ] `/resume/` downloads the current PDF; replacing it in admin changes the download
- [ ] Tabbing through every page shows a visible focus ring on every link and button
- [ ] All tests pass
- [ ] The admin looks clean and the project edit page is easy to fill in

## Sprint 7: Deploy and go live

**Goal in plain words:** put the site online at icarokucha.com, safely, with backups.

**Prerequisites (Ícaro):** Oracle VPS running with Docker; DNS `A` records for `icarokucha.com` and `www` pointing to the VPS IP; email provider account with a verified sender.

**Build:**

- `Dockerfile` and `docker-compose.yml` (web with Gunicorn, Caddy).
- Production settings; Caddyfile with HTTPS and `www` → apex redirect.
- Volumes for database and media; `collectstatic`.
- Admin login rate limiting with `django-axes`.
- Daily backup script, 14-day retention.
- `DEPLOY.md` with step-by-step deploy and update instructions.

**You validate:**

- [ ] `https://icarokucha.com` loads with a valid certificate; `www` and `http` redirect to it
- [ ] Too many wrong admin passwords lock the login for a while
- [ ] A contact message sends a real email to your inbox
- [ ] Restarting the containers keeps all content and images
- [ ] A backup file appears after the cron runs, and restoring it locally works
- [ ] Real content replaces the seed data: photo, bio, resume, experience, real projects
