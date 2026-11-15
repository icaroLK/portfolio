# Start here (for Ícaro)

This folder is the starting point for icarokucha.com. You don't need to read everything. Here's what's in it and how to use it.

## What each file is

| File | What it is | Who reads it |
| --- | --- | --- |
| `CLAUDE.md` | Rules for Claude Code: work one sprint at a time, plan first, small steps, explain everything simply, wait for your OK | Claude Code (automatically, every session) |
| `docs/SPEC.md` | Full description of the site: pages, features, database models, admin, URLs, requirements, design colors | Claude Code, and you when you want details |
| `docs/ROADMAP.md` | The 8 sprints, each with what gets built and a checklist for you to validate | You and Claude Code |
| `docs/design/` | The Version 2 wireframes as HTML files. Double-click to open them in your browser | Both, to compare the real site with the design |
| `docs/INFRA.md` | Where the live site runs: Google Cloud server, Cloudflare Tunnel and domain, and why | You, when you need to touch the server |
| `.gitignore` | Keeps secrets, the database and uploads out of GitHub | Git |

## Setup (once)

1. Unzip this into your project folder (for example `icarokucha-site`).
2. Open a terminal in that folder and run:
   ```bash
   git init
   git add .
   git commit -m "Docs: spec, roadmap and design"
   ```
3. Create an empty repo on GitHub (no README), then:
   ```bash
   git remote add origin https://github.com/icaroLK/icarokucha-site.git
   git branch -M main
   git push -u origin main
   ```
4. Open Claude Code in that folder.

## How each sprint goes

1. Start a **new** Claude Code session and paste:

   > We are on Sprint 0 of docs/ROADMAP.md. Read CLAUDE.md, docs/SPEC.md and docs/ROADMAP.md first. Show me your plan before writing code.

   (Change the number for each sprint.)

2. Claude Code shows a plan. Read it, ask questions, then say **"go"**.
3. It builds **one small step**, then stops and explains:
   - what it did, in simple words
   - why
   - which files changed
   - how you can check it
4. You run what it says and look. Say **"ok, next"** or describe what's wrong.
5. At the end it gives you the sprint's checklist. Go through every item yourself.
6. When everything passes, say **"validated"**. It ticks the boxes in `ROADMAP.md` and commits.
7. Push to GitHub: `git push`.

## Tips

- One sprint per session, so old context doesn't confuse it.
- If you don't understand something, ask "explain that like I'm new to Django". It's supposed to.
- If you change your mind about a feature, ask Claude Code to update `docs/SPEC.md` first, then build.
- Keep real content (photos, bio, project write-ups) for Sprint 7; the demo data is enough until then.
- Before Sprint 7 you need: the Google Cloud server and Cloudflare Tunnel from `docs/INFRA.md` (already done), and an email provider account (Resend or Brevo).
