# The Django site, as it runs on the live server (see DEPLOY.md).
# Base image through Google's mirror of Docker Hub: Docker Hub has no IPv6, the server has only IPv6.
FROM mirror.gcr.io/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

# The site runs as this plain user, not root. The server gives it the data, media and logs folders.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app

# Packages first: Docker reuses this layer while requirements.txt stays the same, so deploys are faster.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Gather CSS, JS and fonts for WhiteNoise. Copying files needs no real secrets, so dummies are fine.
# static/src (the Tailwind source) is skipped: browsers only need the built site.css.
RUN SECRET_KEY=build-only ADMIN_PATH=build-only LOG_DIR=/tmp \
    python manage.py collectstatic --noinput --ignore src

USER app

# Apply database changes, then start Gunicorn on localhost only (Caddy is the only one that talks to it).
# 2 workers fit the 1 GB server; --max-requests restarts a worker now and then to keep memory flat.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi --bind 127.0.0.1:8001 --workers 2 --timeout 30 --max-requests 1000 --max-requests-jitter 100 --access-logfile -"]
