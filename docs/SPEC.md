# icarokucha.com: Build Spec

Source of truth for what the site does. If something here changes, update this file first, then the code.

## 1. Overview

icarokucha.com is a Django portfolio with a custom admin-driven CMS. Every piece of text, link, project and toggle on the site comes from the database, so after launch the site is updated only through the admin, never through code.

**Goal:** one link that works for two audiences at once.

- **Recruiters and tech companies:** real projects, the stack behind each one, experience and skills.
- **Small business clients:** plain-language explanation of what Ícaro builds and an easy way to make contact.

**Design source of truth:** Version 2 wireframes in `docs/design/` (desktop and mobile).

## 2. How Django serves the site

Server-rendered Django templates, not a JSON API with a separate frontend. Each URL maps to a Django view that reads the database and returns a full HTML page. No React and no REST API: one editor (the admin), good SEO and fast first loads.

**Request flow:**

1. The browser requests a URL, for example `/projects/parkeye/`.
2. Django's URL router (`urls.py`) matches it to a view.
3. The view queries the models (only published items, in admin order).
4. The view passes that data to a template (`project_detail.html`).
5. The template renders HTML with shared partials (header, footer, cards) and Tailwind classes.
6. Django returns the HTML. Images and the resume PDF are served as media files.

The "endpoints" are the URL routes in section 6. All are `GET` pages except the contact form `POST`. The admin provides every create, edit, delete and reorder action.

**Stack decisions**

| Area | Choice | Why |
| --- | --- | --- |
| Framework | Django 5.x, Python 3.12 | Admin for free; the point of the project |
| Templates | Django templates + partials | Server-rendered, SEO-friendly |
| Styling | Tailwind CSS standalone CLI (no Node) | Matches the V2 design quickly |
| Interactivity | Native HTML (`<details>`), small vanilla JS for the mobile menu; htmx optional later for filters | Almost no JS to maintain |
| Database | SQLite | One editor, low traffic, trivial backups |
| Media | Local `media/` folder on the VPS | Free; backed up with the DB |
| Admin ordering | `django-admin-sortable2` | Drag-and-drop order |
| Images | `Pillow` + generated WebP thumbnails | Fast pages |
| Email | Resend or Brevo via SMTP (free tier) | Contact notifications |
| Spam | Honeypot + rate limit; Cloudflare Turnstile if needed | Clean inbox |
| Serving | Gunicorn + Caddy on an Oracle Cloud VPS, Docker Compose | Automatic HTTPS, subdomains later |
| Static files | WhiteNoise | Simple static serving |

## 3. Pages and features

Three public pages (Home, Project detail, About), plus shared header and footer, all matching Version 2 on desktop and mobile.

### Shared: header

- Name on the left links to Home.
- Desktop nav: Projects (Home), About, Contact (About page `#contact`), Resume (outlined pill, downloads the PDF from Site settings).
- Active page link is darker.
- Mobile (under 768 px): links collapse into a menu button with `aria-label="Open menu"`; tapping opens a full-width panel with the same links. Small vanilla JS toggle; Escape closes it.

### Shared: footer

- Left: "© Icaro Kucha · Curitiba, Brazil · Working remotely" (location line from Site settings).
- Right: Email, GitHub, LinkedIn, Resume from Site settings. Links with an empty URL are hidden.
- Mobile: links stacked above the copyright line.

### Home (`/`)

1. **Hero**
   - Status badge with green dot; text and visibility from Site settings (`status_badge_text`, `show_status_badge`).
   - Headline (H1) and subheadline from Site settings.
   - Buttons: "See my work" (scrolls to Featured projects), "Contact me" (About `#contact`).
2. **Featured projects** (eyebrow "Selected work")
   - Projects with `is_featured` and `is_published`, admin order. Recommended 3.
   - Large horizontal card: inset cover image left, text right (type tags as one uppercase line, title, pitch, tech chips, "View project →"). Whole card is one link.
   - Mobile: image on top, text below.
   - Section hidden when there are no featured projects.
3. **More projects** (eyebrow "Archive")
   - Published, non-featured projects, admin order. Uniform grid: 3 columns desktop, 2 tablet, compact rows with a 96 px thumbnail on mobile.
   - Segmented filter: "All" plus one button per TypeTag that has at least one published project. Uses `?type=<slug>` (works without JS).
   - Empty state text when a filter has no projects.

### Project detail (`/projects/<slug>/`)

- "← All projects" back link.
- Type tags line, title (H1), pitch, meta line (role · period), buttons "Live demo ↗" and "GitHub repo ↗" (each only if its URL exists; open in new tab with `rel="noopener"`).
- Video embed (YouTube or Loom) if `video_url` is set; converted to the embed URL server-side.
- **What it does:** plain-language paragraph.
- **Key features:** numbered rows 01, 02, 03 from ProjectFeature. Hidden if none.
- **Tech stack:** compact chips, each = tech name + short purpose (ProjectTech).
- **How it works:** technical text, labeled "For technical readers". Image below only if `architecture_image` is uploaded. Section hidden if empty.
- **Gallery:** 3-column grid desktop, horizontal swipe strip mobile. Images open full size (new tab in v1, lightbox optional later).
- **Next project** card to the next published project in order (wraps to the first).
- Missing or unpublished slug returns the styled 404.

### About (`/about/`)

1. **Intro:** circular photo, "Hi, I'm Icaro." heading, bio, buttons "Download resume" and "Contact me".
2. **Experience** (eyebrow "Work"): card per entry with logo, role, company + location, dates, summary, tech chips. A native `<details>` reveals the long description and bullets; the toggle appears only when `details` is filled.
3. **Education** (eyebrow "Studies"): two-column cards (logo, degree, school + city, dates).
4. **Skills** (eyebrow "Toolbox"): one row per SkillGroup, name left, chips right (stacked on mobile).
5. **What I can build for you** (eyebrow "Services"): numbered Service cards.
6. **Contact** (`id="contact"`): card with "Let's work together.", direct links and the form.

Each section can be hidden from Site settings (`show_experience`, `show_education`, `show_skills`, `show_services`, `show_contact_form`).

### Contact form

- Fields: name (required), email (required, validated), topic (Job opportunity / Website or system for my business / Other), message (required, 10 to 5000 chars), hidden honeypot.
- Submit: validate, check honeypot, rate limit (max 3 per IP per hour), save ContactMessage, send notification email, redirect to `/about/?sent=1#contact` with a success message (POST/redirect/GET).
- Errors: re-render with field errors and input kept.
- Email provider failure: message still saved, error logged.

### Global

- Custom 404 and 500 pages in the site style.
- Every page sets its own `<title>`, meta description and Open Graph tags (project pages use the cover image as `og:image`).

## 4. Data model

Thirteen models in two apps: `portfolio` (site content) and `contact` (inbox). List models have `order` and, where useful, `is_published`. All models have `created_at` / `updated_at`.

### portfolio app

**SiteSettings** (singleton: one row, cannot be deleted)

| Field | Type | Notes |
| --- | --- | --- |
| site_name | Char(80) | "Icaro Kucha" in header and titles |
| headline | Char(200) | Home H1 |
| subheadline | Char(300) | Under the H1 |
| status_badge_text | Char(80) | "Open to work · Available for freelance" |
| show_status_badge | Bool | |
| about_bio | Text | About intro |
| profile_photo | Image | Circular photo |
| resume_pdf | File (.pdf) | Header pill, About button, footer, `/resume/` |
| email | Email | |
| github_url, linkedin_url | URL | |
| location_line | Char(120) | Footer |
| meta_description | Char(160) | Default SEO description |
| og_image | Image | Default share image |
| show_experience, show_education, show_skills, show_services, show_contact_form | Bool | About section toggles |

**TypeTag:** name ("Computer Vision"), slug, order. Drives Home filters.

**Tech:** name ("Django"), slug.

**Project**

| Field | Type | Notes |
| --- | --- | --- |
| title | Char(120) | |
| slug | Slug, unique | Auto from title, editable |
| pitch | Char(200) | Plain-language line for cards and hero |
| type_tags | M2M TypeTag | Shown as "Computer Vision · System" |
| role | Char(80) | "Solo project", "Client project" |
| period | Char(40) | Free text, "Nov 2026" |
| cover_image | Image | Required; thumbnails generated |
| video_url | URL, optional | YouTube or Loom |
| live_url, repo_url | URL, optional | Buttons hide when empty |
| what_it_does | Text | Plain language |
| how_it_works | Text, optional | Technical; simple Markdown |
| architecture_image | Image, optional | Shown only if uploaded |
| is_featured | Bool | |
| is_published | Bool | |
| order | PositiveInt | Drag-and-drop |
| seo_description | Char(160), optional | Falls back to pitch |

**ProjectFeature** (inline): project FK, text Char(200), order.

**ProjectTech** (inline, stack chips): project FK, tech FK, purpose Char(40) ("car detection"), order.

**ProjectImage** (inline, gallery): project FK, image, caption Char(120) optional, order.

**Experience**

| Field | Type | Notes |
| --- | --- | --- |
| role | Char(120) | |
| company | Char(120) | |
| location | Char(120) | "Remote (US)" |
| logo | Image, optional | Placeholder when empty |
| start_date | Date | |
| end_date | Date, optional | Empty = "Present"; display "Mar 2025 – Present" |
| summary | Char(300) | Always visible |
| details | Text, optional | Long description + bullets (simple Markdown); "Show details" only when filled |
| techs | M2M Tech | Chips |
| is_published, order | Bool, PositiveInt | |

**Education:** degree, school, city, logo (optional), start_date, end_date (optional), period_label (optional free text, e.g. "Erasmus semester, 2026"), is_published, order.

**SkillGroup:** name ("Automation & AI"), order. **Skill** (inline in SkillGroup): group FK, name, order.

**Service:** title, description Char(200), is_published, order. Display number (01, 02, 03) generated from order.

### contact app

**ContactMessage**

| Field | Type | Notes |
| --- | --- | --- |
| name | Char(120) | |
| email | Email | |
| topic | Choice | job / business / other |
| message | Text | |
| ip_address | GenericIP | Rate limiting |
| user_agent | Char(300) | Spam review |
| is_read | Bool | |
| is_spam | Bool | |
| email_sent | Bool | Notification delivered or not |
| created_at | DateTime | |

## 5. Admin requirements

- **Private URL** from `ADMIN_PATH` in `.env` (for example `/painel-8x2k/`), never `/admin/`.
- **Login security:** strong password and login rate limiting with `django-axes` (no 2FA: one admin user).
- **Site settings:** a single edit page, no Add or Delete. Fieldsets: Hero, About, Links & resume, SEO, Section toggles.
- **Projects list:** cover thumbnail, title, type tags, featured, published, order. `is_featured` and `is_published` editable in the list. Drag-and-drop ordering. Filters: type tag, featured, published. Search by title.
- **Project edit page:** fieldsets Basics, Media, Content, Links, SEO. Sortable inlines for Key features, Stack, Gallery. Image previews. "View on site" button.
- **Experience, Education, Services, Skill groups:** drag-and-drop order, published toggle in the list. Skills inline in their group.
- **Tags and Techs:** simple lists, slug auto-filled.
- **Contact inbox:** date, name, email, topic, read, spam; newest first; unread count visible; bulk "Mark as read" and "Mark as spam"; messages read-only.
- **Uploads:** images max 5 MB (jpg, png, webp), resume PDF max 5 MB; anything else rejected with a clear message.
- **Branding:** site name in the admin header instead of "Django administration".
- **Look and layout (Sprint 6):** a modern admin theme (for example `django-unfold`), related fields side by side, rarely used sections (SEO, links) collapsed, clear labels and help text.

## 6. URL routes

Eight public GET routes, one form POST and the private admin. Every page route returns HTML.

| Method | URL | View | Returns |
| --- | --- | --- | --- |
| GET | `/` | `home` | Hero, featured, more projects; optional `?type=<slug>` |
| GET | `/projects/<slug>/` | `project_detail` | Project page; 404 if missing or unpublished |
| GET | `/about/` | `about` | All About sections; `?sent=1` shows success |
| POST | `/contact/` | `contact_submit` | Save + redirect to `/about/?sent=1#contact`; errors re-render About |
| GET | `/resume/` | `resume_download` | Redirect to the current resume PDF |
| GET | `/sitemap.xml` | Django sitemaps | Home, About, published projects |
| GET | `/robots.txt` | template view | Allow all, sitemap link, block admin path |
| GET | `/healthz/` | `healthz` | "ok" for uptime checks |
| GET | `/media/...`, `/static/...` | Caddy / WhiteNoise | Uploads, CSS, JS |
| GET/POST | `/<ADMIN_PATH>/` | Django admin | Private CMS, rate-limited login |

`/resume/` gives a stable link for LinkedIn and applications that always serves the latest uploaded PDF.

## 7. Non-functional requirements

These are acceptance criteria for every sprint.

**Performance**

- Lighthouse mobile Performance 90+ on Home and a project page.
- Resized WebP thumbnails (card 640 px, featured 1200 px, gallery 1600 px), `loading="lazy"` below the fold, explicit width/height.
- `select_related` / `prefetch_related`: no query per card.
- Inter and Inter Tight, weights 400/500/600 only, `display=swap`.

**SEO and sharing**

- Unique title and meta description per page; Open Graph and Twitter tags; canonical URLs; sitemap; robots.
- One H1 per page, headings in order.

**Security**

- `DEBUG=False` in production; secrets only in env vars.
- HTTPS (Caddy), HSTS, secure + HttpOnly cookies, CSRF on the form.
- Admin on secret path with rate-limited login.
- Uploads restricted by type and size; randomized filenames.

**Accessibility**

- Real links and buttons, visible focus, `aria-label` on icon-only buttons.
- Text contrast 4.5:1+ (V2 grays pass), touch targets 44 px+.
- Alt text on every image (cover alt defaults to the project title).

**Responsive**

- Mobile under 768 px, tablet 768 to 1023 px, desktop 1024 px+. Mobile follows the V2 mobile designs.

**Operations**

- Daily backup of `db.sqlite3` and `media/` (cron + tarball, keep 14 days, copy off the VPS).
- Errors logged to a file; optional Sentry later.
- Tests for models, views (status codes, published filtering) and the contact form (valid, invalid, honeypot, rate limit).

## 8. Design tokens (Version 2)

| Token | Value |
| --- | --- |
| Background | `#F7F7F5` |
| Card surface | `#FFFFFF` |
| Ink (headings, buttons) | `#111111` |
| Body text | `#3A3A38`, `#4A4A47` |
| Secondary text | `#5F5F5C`, `#6B6B68` |
| Faint numbers (01, 02) | `#9A9A96` |
| Borders | `#E7E7E4` (cards), `#D9D9D5` (secondary buttons), `#E2E2DE` (inputs) |
| Chip / soft fill | `#F3F3F0`, `#EEEEEB` (filter track) |
| Image placeholder | `#EDEDEA` |
| Status dot | `#1F9D55` |
| Fonts | Inter Tight 600 for headings (letter-spacing about -0.02 to -0.035em), Inter 400/500/600 for body |
| Radii | 10 px buttons/inputs, 12 px inner images, 16 to 20 px cards, 999 px pills |
| Eyebrow labels | 12 px, 600, uppercase, letter-spacing 0.12em, `#6B6B68` |
