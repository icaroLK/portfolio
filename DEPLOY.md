# Deploy: putting the site online

How the code on your PC becomes https://icarokucha.com. Where the server lives and why: [`docs/INFRA.md`](docs/INFRA.md).

```
your PC --(deploy.ps1, through Google's IAP tunnel)--> portfolio-vm
visitor --> Cloudflare (HTTPS) --> tunnel --> Caddy :8000 --> Django/Gunicorn :8001
```

The server cannot download from GitHub (GitHub has no IPv6, the server has only IPv6). So your PC packs the latest commit and copies it to the server, and the server builds and restarts the site.

## First time (once)

### 1. Install the Google Cloud CLI on your PC

1. Download and run the installer: https://cloud.google.com/sdk/docs/install (Windows tab, `GoogleCloudSDKInstaller.exe`). Keep the default options.
2. At the end it opens a terminal and asks you to log in: pick your Google account in the browser.
3. When it asks for a project, choose `icarokucha-portfolio`.
4. Open a **new** PowerShell in the project folder and check:

   ```powershell
   gcloud compute instances list
   ```

   You should see `portfolio-vm` with status `RUNNING`.

The first deploy also creates an SSH key for you. If a window asks for a passphrase, press Enter twice (no passphrase).

### 2. Cloudflare: route www too

Cloudflare dashboard > Zero Trust > Networks > Tunnels > `portfolio-vm` > Published application routes > Add: subdomain `www`, domain `icarokucha.com`, service `HTTP` `localhost:8000`. Django sends `www` visitors to the main address.

### 3. Resend: contact emails

1. Sign up at https://resend.com (free plan: 3,000 emails a month, 100 a day).
2. Domains > Add domain > `icarokucha.com`. Choose the automatic Cloudflare setup (or copy the DNS records it shows into Cloudflare > DNS). Wait until the domain says **Verified**.
3. API Keys > Create API key, permission "Sending access". Copy the key (starts with `re_`).
4. Open `.env.production` in the project folder and paste it after `RESEND_API_KEY=`.

You can deploy before this step: contact messages are still saved in the admin inbox, the email is just not sent until the key is there.

### 4. `.env.production`

This file on your PC holds the live server's settings and secrets. It is never committed, and `deploy.ps1` copies it to the server on every deploy. It already has a secret key and a private admin path. Your live admin address is `https://icarokucha.com/<ADMIN_PATH>/`, with the value from that file.

### 5. Deploy

```powershell
.\deploy\deploy.ps1
```

The first time takes a few minutes (the server downloads Python and the packages). It ends with `Live: commit ... is online.` and `Done`.

### 6. Create your admin login

```powershell
.\deploy\manage.ps1 createsuperuser
```

Then log in at your admin address, fill **Site settings** (including the notification email that receives contact messages) and add your projects.

## Every update after that

1. Change things on your PC, test them with `python manage.py runserver`.
2. Commit (and push to GitHub as usual).
3. `.\deploy\deploy.ps1`

Content (projects, texts, images) is never deployed: you edit it in the live admin, and it stays on the server.

## Useful commands

| What | Command (PowerShell, project folder) |
| --- | --- |
| Deploy the latest commit | `.\deploy\deploy.ps1` |
| Unlock the admin after 5 wrong passwords | `.\deploy\manage.ps1 axes_reset` |
| Change your admin password | `.\deploy\manage.ps1 changepassword <username>` |
| Download the newest backup | `.\deploy\get-backup.ps1` |

On the server (Compute Engine > VM instances > `portfolio-vm` > SSH):

| What | Command |
| --- | --- |
| Are the containers running? | `cd /opt/portfolio/app && sudo docker compose ps` |
| Last log lines | `cd /opt/portfolio/app && sudo docker compose logs --tail 50 web` |
| Django error log | `sudo tail -50 /opt/portfolio/logs/django.log` |
| Restart the site | `cd /opt/portfolio/app && sudo docker compose restart` |
| Run a backup now | `sudo systemctl start portfolio-backup` |
| List backups | `ls -lh /opt/portfolio/backups` |
| Which commit is live | `cat /opt/portfolio/app/REVISION` |

## Where things live on the server

| Folder | What |
| --- | --- |
| `/opt/portfolio/app` | Code of the live commit (replaced on every deploy; the previous one is in `app.previous`) |
| `/opt/portfolio/.env` | Settings and secrets (copy of your `.env.production`) |
| `/opt/portfolio/data` | `db.sqlite3`, the database |
| `/opt/portfolio/media` | Uploaded images and the resume PDF |
| `/opt/portfolio/logs` | Django error log |
| `/opt/portfolio/backups` | Nightly backups, last 14 days |

Restarting the containers or the whole server keeps everything: data, media and backups are folders on the server's disk, not inside the containers.

## Backups

Every night at 00:30 (Brasilia time), the server saves the database and all uploads into `/opt/portfolio/backups/portfolio-<date>.tar.gz` and deletes backups older than 14 days. They stay on the server. Download one to your PC whenever you want a copy elsewhere.

### Restore a backup on your PC

1. `.\deploy\get-backup.ps1` (saves it in `backups\`)
2. Stop `runserver`. If your local database matters, copy `db.sqlite3` somewhere first: the next step replaces it.
3. In the project folder:

   ```powershell
   tar -xzf backups\portfolio-<date>.tar.gz
   ```

   This replaces `db.sqlite3` and `media\` with the server's.
4. `python manage.py runserver`: your PC now shows the live content.

## Go back to the previous version

If a deploy breaks something, deploy an older commit:

```powershell
git checkout <older commit>
.\deploy\deploy.ps1
git checkout main
```

## If something goes wrong

- **`deploy.ps1` says gcloud is not installed:** step 1, then open a new PowerShell.
- **"Could not find portfolio-vm":** run `gcloud auth login` and `gcloud config set project icarokucha-portfolio`.
- **"The site did not answer":** the script prints the last log lines; the error is usually at the bottom.
- **Site down, server fine:** check the tunnel (Cloudflare > Tunnels > `portfolio-vm` must be Healthy), then the server commands above.
- More: `docs/INFRA.md`, section "If something goes wrong".
