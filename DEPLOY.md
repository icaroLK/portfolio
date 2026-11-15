# Deploy: putting the site online

How the code on your PC becomes https://icarokucha.com. Where the server lives and why: [`docs/INFRA.md`](docs/INFRA.md).

```
visitor --> Cloudflare (HTTPS) --> tunnel --> Caddy :8000 --> Django/Gunicorn :8001
your PC --(deploy.ps1, ssh)--> Cloudflare (your login) --> same tunnel --> server SSH :22
```

The server cannot download from GitHub (GitHub has no IPv6, the server has only IPv6). So your PC packs the latest commit and copies it to the server, and the server builds and restarts the site.

## The easy way: upload one file in the browser

No setup on your PC. Every deploy:

1. Commit your changes, then run `.\deploy\pack.ps1`. It makes `portfolio-upload.tar.gz` in the project folder (the code plus `.env.production`).
2. Google Cloud > Compute Engine > VM instances > `portfolio-vm` > **SSH**.
3. In the SSH window, click **Upload file** (top right) and pick `portfolio-upload.tar.gz`.
4. Paste this line and press Enter:

   ```bash
   rm -rf /tmp/p && mkdir /tmp/p && tar -xzf ~/portfolio-upload.tar.gz -C /tmp/p && mv /tmp/p/.env.production /tmp/portfolio.env && rm ~/portfolio-upload.tar.gz && sudo bash /tmp/p/deploy/server-deploy.sh /tmp/p
   ```

   It ends with `Live: commit ... is online.`

**Only the very first time,** create your admin login right after, in the same window:

```bash
cd /opt/portfolio/app && sudo docker compose exec web python manage.py createsuperuser
```

The rest of this file is the one-command way (`deploy.ps1` through the tunnel), which needs a one-time setup.

## First time (once)

### 1. Open a way in for your PC, through the tunnel

The server has no public IPv4 and no open ports. Your PC gets in through the same Cloudflare Tunnel as the site, behind a Cloudflare login that only your email passes. Your PC already has `cloudflared` and `ssh`, so nothing new to install.

**a. The login (do this first, so the door is never open without it).** Cloudflare dashboard > Zero Trust > Access > Applications > Add an application > Self-hosted:

- Application name: `Server SSH`
- Public hostname: subdomain `ssh`, domain `icarokucha.com`
- Policy: create a new one, name `Only me`, action **Allow**, include **Emails** = your email
- Login method: One-time PIN (the default)
- Save

**b. The route.** Zero Trust > Networks > Tunnels > `portfolio-vm` > Published application routes > Add a published application route:

- Subdomain `ssh`, domain `icarokucha.com`
- Service type **SSH**, URL `localhost:22`
- Save

**c. The deploy user on the server.** Your PC has a deploy key at `%USERPROFILE%\.ssh\icarokucha_deploy` (make one with `ssh-keygen -t ed25519 -N '""' -f $HOME\.ssh\icarokucha_deploy` if it is missing). Open the browser SSH window (Compute Engine > VM instances > `portfolio-vm` > SSH) and paste this line, with the content of `icarokucha_deploy.pub` between the quotes:

```bash
KEY='ssh-ed25519 AAAA... deploy@icarokucha'; id deploy >/dev/null 2>&1 || sudo useradd -m -s /bin/bash -p '*' deploy; echo 'deploy ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/91-deploy >/dev/null; sudo chmod 440 /etc/sudoers.d/91-deploy; sudo install -d -m 700 -o deploy -g deploy /home/deploy/.ssh; echo "$KEY" | sudo tee /home/deploy/.ssh/authorized_keys >/dev/null; sudo chown deploy:deploy /home/deploy/.ssh/authorized_keys; sudo chmod 600 /home/deploy/.ssh/authorized_keys; echo 'deploy user ready'
```

It ends with `deploy user ready`. This user belongs to the server itself, so Google's console never removes its rights (unlike your browser SSH user, see `docs/INFRA.md`).

The first time a script connects, a browser tab opens with the Cloudflare login: type your email, then the code it emails you. It stays logged in for a while after that.

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

- **"Failed: uploading the code" right away:** check step 1. The tunnel must show the `ssh` route, the `Server SSH` application must exist, and the browser login must have finished.
- **"Permission denied (publickey)":** the key on the server does not match your PC. Paste the step 1c line again with the content of `icarokucha_deploy.pub`.
- **"The site did not answer":** the script prints the last log lines; the error is usually at the bottom.
- **Site down, server fine:** check the tunnel (Cloudflare > Tunnels > `portfolio-vm` must be Healthy), then the server commands above.
- More: `docs/INFRA.md`, section "If something goes wrong".
