# VyaparSetu Deployment Guide

This guide prepares a production deployment on a VPS using Docker Compose, PostgreSQL, Nginx, and SSL.

## VPS Setup

1. Provision an Ubuntu LTS VPS with at least 2 CPU cores, 4 GB RAM, and 40 GB disk.
2. Create a non-root deploy user and add it to the Docker group.
3. Install Docker Engine and Docker Compose Plugin.
4. Open firewall ports:
   - `22` for SSH
   - `80` for HTTP
   - `443` for HTTPS
5. Clone the repository into `/opt/vyaparsetu`.

## Domain Setup

1. Create DNS records:
   - `A your-domain.com -> VPS_PUBLIC_IP`
   - `A www.your-domain.com -> VPS_PUBLIC_IP`
2. Wait for DNS propagation.
3. Replace `your-domain.com` and `www.your-domain.com` in `nginx/nginx.conf` with the final domain before starting production Nginx.

## Secrets

Copy `.env.production.example` to `.env.production` and replace every placeholder.

Required secrets:
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `SECRET_KEY`
- `BACKEND_CORS_ORIGINS`
- `NEXT_PUBLIC_API_BASE_URL`
- credentials for the selected production-ready AI provider when `DOCUMENT_INTELLIGENCE_ENABLED=true`
- `ADMIN_NOTIFICATION_EMAIL`

Generate `SECRET_KEY` with:

```bash
openssl rand -hex 32
```

Never commit `.env.production`.

Production startup safety checks are enforced by the backend. With `ENVIRONMENT=production`, the backend exits during startup if:
- `SECRET_KEY` is default, placeholder, missing, or shorter than 32 characters.
- `POSTGRES_PASSWORD` is default, placeholder, missing, or shorter than 12 characters.
- `DATABASE_URL` is missing, omits a password, or embeds a default, placeholder, or shorter-than-12-character password.
- `DOCUMENT_INTELLIGENCE_ENABLED=true` and `AI_PROVIDER=mock`.
- `DOCUMENT_INTELLIGENCE_ENABLED=true` and `AI_PROVIDER` is unsupported, unimplemented, or not marked production-ready by the application.
- `BACKEND_CORS_ORIGINS` is empty, contains localhost, or uses non-HTTPS origins.
- `NEXT_PUBLIC_API_BASE_URL` is missing, points to localhost, or uses non-HTTPS.
- `ADMIN_NOTIFICATION_EMAIL` is missing.
- `ENVIRONMENT` is not a recognized value. `production`, `prod`, and `live` all enable production checks.

Do not bypass these checks for production. If startup fails, correct the environment instead of changing application code.

Document intelligence is optional. Production can start safely with `DOCUMENT_INTELLIGENCE_ENABLED=false`, which puts document handling into manual review mode, skips extraction jobs, and logs a startup warning. If document intelligence is enabled in production, a real implemented provider must be marked production-ready first. The mock provider remains development-only.

## PostgreSQL Setup

PostgreSQL runs as the `db` service in `docker-compose.prod.yml`.

Connection pooling is configured in backend settings:
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT`
- `DB_POOL_RECYCLE`

For higher traffic, move PostgreSQL to a managed database and set `DATABASE_URL` accordingly.

## Docker Deployment

Before starting production services, make sure certificates exist under:

```text
certbot/conf/live/your-domain.com/fullchain.pem
certbot/conf/live/your-domain.com/privkey.pem
```

Build and start production services:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Run migrations:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend alembic upgrade head
```

Seed optional demo data only on staging:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend python -m app.cli seed-demo-data
```

Check services:

```bash
docker compose -f docker-compose.prod.yml ps
curl https://your-domain.com/health
curl https://your-domain.com/health/db
curl -I http://your-domain.com/
curl -I https://your-domain.com/
```

Expected results:
- `http://your-domain.com/` returns a `301` redirect to HTTPS.
- `https://your-domain.com/` includes `Strict-Transport-Security`.

## SSL Setup

Recommended: Certbot with webroot. The production Nginx config keeps `/.well-known/acme-challenge/` available over HTTP and redirects all other HTTP traffic to HTTPS. The HTTPS server block is active by default, so certificates must exist before production Nginx starts successfully.

1. Replace `your-domain.com` in `nginx/nginx.conf`.
2. Issue certificates before the first production Nginx start. One option is a temporary standalone Certbot run while port 80 is free:

```bash
docker run --rm \
  -p 80:80 \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certonly \
  --standalone \
  -d your-domain.com \
  -d www.your-domain.com
```

3. For renewals, use the webroot challenge:

```bash
docker run --rm \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d your-domain.com \
  -d www.your-domain.com
```

4. Reload Nginx after renewals:

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

Renew certificates via cron:

```bash
docker run --rm \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot renew
```

## Migration Deployment Checklist

Before migration:
- Confirm latest backup exists.
- Confirm app image builds.
- Confirm `.env.production` points to the intended DB.
- Run `alembic heads` and verify one head.

Migration:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

After migration:
- Check `/health/db`.
- Smoke test login, lead creation, application creation, upload, admin review.

## Backup Procedure

Create a database backup:

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump \
  -U "$POSTGRES_USER" "$POSTGRES_DB" \
  > backups/vyaparsetu-$(date +%Y%m%d-%H%M%S).sql
```

Upload backups to off-server storage daily.

Restore backup:

```bash
cat backups/backup.sql | docker compose -f docker-compose.prod.yml exec -T db psql \
  -U "$POSTGRES_USER" "$POSTGRES_DB"
```

Back up uploaded documents:

```bash
docker run --rm -v vyaparsetu_backend_uploads:/data -v "$(pwd)/backups:/backups" alpine \
  tar czf /backups/uploads-$(date +%Y%m%d-%H%M%S).tar.gz /data
```

## Rollback Procedure

1. Stop traffic at Nginx or put the app in maintenance mode.
2. Restore the previous app image or checkout the previous release tag.
3. If migrations are reversible and safe:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

4. If data shape changed materially, restore from the verified backup.
5. Restart services and smoke test.

## Monitoring

Endpoints:
- `/health`
- `/health/db`
- `/metrics`

Log aggregation should capture Docker stdout/stderr for:
- `backend`
- `frontend`
- `nginx`
- `db`

Set alerts for:
- HTTP 5xx spikes
- `/health/db` failure
- disk usage above 80%
- database backup failure
- SSL certificate expiry under 14 days
