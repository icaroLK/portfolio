# Infrastructure: where icarokucha.com lives

Everything that was set up outside this repository to put the site online, where it lives, and why. Set up on 2026-11-15, before Sprint 7.

No secrets are written here. The Cloudflare tunnel token lives only on the server.

## The big picture

```
visitor -> https://icarokucha.com -> Cloudflare (HTTPS, cache) -> Cloudflare Tunnel -> Google Cloud VM -> localhost:8000
```

- The server is a **free Google Cloud e2-micro** VM.
- It has **no public IPv4 address**, because that is the only part Google charges for (about US$3.65/month). It only has a free public IPv6 address.
- Visitors never connect to the server directly. A small program on the server (`cloudflared`) opens a connection **out** to Cloudflare, and Cloudflare sends visitors through it. Cloudflare also handles HTTPS.
- Result: **R$0 per month, forever**, no ports open to the internet.

### Why not the other options

| Option | Why not |
| --- | --- |
| Oracle Cloud free VPS | Original plan, but account approval would take months |
| AWS Free plan | Credits for 6 months, then the account closes |
| Azure for Students | Free only while a student, credit based |
| Railway, Render, Fly.io, Koyeb, PythonAnywhere | Not free for 24/7, sleep, wipe the disk (SQLite and uploads lost), or no custom domain on free |
| Home server | Works, but the site should live in the cloud, not at home |

## 1. Google Cloud (console.cloud.google.com)

### Project and billing

| Item | Value |
| --- | --- |
| Project name | `portfolio` |
| Project ID | `icarokucha-portfolio` |
| Budget alert | `zero-cost-alarm` in Billing > Budgets & caps |
| Budget scope | All projects on the billing account, all services |
| Budget amount | R$5/month, emails at 50%, 90%, 100% actual and 100% forecasted |

The alert does **not** block charges. It only emails. It is a safety net in case something stops being free.

### Network (VPC Network > VPC networks)

| Item | Value |
| --- | --- |
| Network | `portfolio-net`, subnet mode Custom |
| Subnet | `portfolio-subnet` |
| Region | `us-east1` (South Carolina), closest free region to Brazil |
| IP stack | IPv4 and IPv6 (dual-stack) |
| IPv4 range | `10.0.0.0/24` (internal only) |
| IPv6 access type | External (this is the free public address) |
| Private Google Access | On |
| Firewall | Only `portfolio-net-allow-ssh` (tcp:22, IPv4). Plus the built-in rules: deny all incoming, allow all outgoing. No IPv6 rules. |

SSH open to `0.0.0.0/0` is safe here: the VM has no public IPv4, so only Google's own SSH button can reach port 22.

### Virtual machine (Compute Engine > VM instances)

| Item | Value | Why |
| --- | --- | --- |
| Name | `portfolio-vm` | |
| Machine | `e2-micro` (2 shared vCPU, 1 GB RAM) | The only free machine type |
| Region / zone | `us-east1`, zone picked by Google | Free region |
| Provisioning | Standard (not Spot) | Spot can be stopped at any time |
| OS | Ubuntu 26.04 LTS Minimal, x86/64 | Familiar, light, supported until 2031 |
| Disk | 30 GB **Standard** persistent disk | The default "Balanced" disk is paid |
| Snapshots | No schedule | Automatic snapshots cost money |
| Ops Agent | Not installed | Uses RAM; not available for this OS anyway |
| External IPv4 | **None** | The only paid part, skipped on purpose |
| External IPv6 | Ephemeral | Free |
| HTTP/HTTPS firewall boxes | Unchecked | Cloudflare Tunnel handles web traffic |

The console's "Monthly estimate" shows about US$6/month for the e2-micro. That estimate ignores the free tier. On the real bill the free tier cancels it out. Check **Billing > Reports** a day after any change: net cost must be R$0.

### How to get into the server

Compute Engine > VM instances > `portfolio-vm` > **SSH**. A terminal opens in the browser (Google routes it through its own network, since there is no IPv4).

## 2. Inside the server

Everything below was run in that SSH terminal.

| What | Command or file | Why |
| --- | --- | --- |
| System update | `sudo apt update && sudo apt upgrade -y` | Fresh security fixes |
| 2 GB swap | `/swapfile`, listed in `/etc/fstab` | Safety net for the 1 GB RAM, survives reboots |
| Permanent sudo | `/etc/sudoers.d/90-icaro` | The console SSH key expires after a while and Google removes the admin group mid-session ("I'm sorry ... I'm afraid I can't do that"). This file keeps admin rights for the user. |
| Docker | `sudo apt install -y docker.io docker-compose-v2` | Runs the site in containers |
| Docker image mirror | `/etc/docker/daemon.json` with `"registry-mirrors": ["https://mirror.gcr.io"]` | Docker Hub has no IPv6. Google's mirror of Docker Hub does. |
| cloudflared | Installed from `pkg.cloudflare.com` (apt repo) | The tunnel program |
| cloudflared service | `sudo cloudflared service install <token>` | Starts the tunnel on every boot |
| cloudflared over IPv6 | `/etc/systemd/system/cloudflared.service.d/ipv6.conf` with `Environment=TUNNEL_EDGE_IP_VERSION=6` | By default cloudflared tries IPv4, which the server does not have |
| Test page | Docker container `test-page` (`nginx:alpine`) on `127.0.0.1:8000` | Placeholder to prove the path works. The first deploy removes it. |

### Things that work and don't work without IPv4

| Works (has IPv6) | Does not work (IPv4 only) |
| --- | --- |
| Ubuntu `apt` | **GitHub** (no `git clone` / `git pull` on the server) |
| Python packages (PyPI) | Docker Hub directly (use the mirror) |
| Docker via `mirror.gcr.io` | Email SMTP (Resend, Brevo): the site uses Resend's HTTP API instead |
| Cloudflare, Google | |

Inside Docker containers, outgoing internet also needs IPv6. The site's containers use host networking for that (`docker-compose.yml`). How the site is deployed and run: `DEPLOY.md`.

### Useful commands

```bash
free -h                                          # RAM and swap
sudo docker ps                                   # running containers
sudo systemctl status cloudflared --no-pager     # tunnel service
sudo journalctl -u cloudflared -n 30 --no-pager  # tunnel logs ("Registered tunnel connection" = good)
```

## 3. Cloudflare (dash.cloudflare.com)

| Item | Value |
| --- | --- |
| Domain | `icarokucha.com`, bought on Cloudflare, Free plan. DNS was already on Cloudflare, no nameserver change needed. |
| Tunnel | `portfolio-vm` (Zero Trust > Networks > Tunnels), type cloudflared, status Healthy |
| Route | Published application: `icarokucha.com` -> `http://localhost:8000` |
| DNS record | `CNAME icarokucha.com -> <tunnel-id>.cfargotunnel.com`, created automatically by the route |
| Still to add | Same route for `www.icarokucha.com` |

The account also has two old tunnels (`n8n-digitalocean`, `tunel-kucha-cloudflare`), both down. They are unrelated to this site.

## 4. Status on 2026-11-15

- [x] Google Cloud project, budget alert, network and VM
- [x] Swap, permanent sudo, Docker with the Google mirror
- [x] Cloudflare Tunnel connected over IPv6 (Healthy)
- [x] `https://icarokucha.com` shows the nginx test page
- [ ] `www` route in Cloudflare
- [ ] Billing > Reports shows R$0 net cost after a full day
- [ ] Sprint 7: the real Django site replaces the test page (see `docs/ROADMAP.md`)

## 5. If something goes wrong

- **Bill is not R$0:** open Billing > Reports, group by SKU, find the line. If unsure, stop the VM (Compute Engine > VM instances > Stop) and ask.
- **Site down:** SSH in, check `sudo docker ps` and the cloudflared logs above. The Cloudflare tunnel page also shows Healthy or Down.
- **"I'm sorry ... I'm afraid I can't do that" on sudo:** `/etc/sudoers.d/90-icaro` is missing. Close the SSH window, open it again, and recreate the file right away.
