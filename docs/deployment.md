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
3. Update `nginx/nginx.conf` SSL server block with the final domain before enabling HTTPS.

## Secrets

Copy `.env.production.example` to `.env.production` and replace every placeholder.

Required secrets:
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `SECRET_KEY`
- `BACKEND_CORS_ORIGINS`
- `NEXT_PUBLIC_API_BASE_URL`
- `ADMIN_NOTIFICATION_EMAIL`

Generate `SECRET_KEY` with:

```bash
openssl rand -hex 32
```

Never commit `.env.production`.

## PostgreSQL Setup

PostgreSQL runs as the `db` service in `docker-compose.prod.yml`.

Connection pooling is configured in backend settings:
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT`
- `DB_POOL_RECYCLE`

For higher traffic, move PostgreSQL to a managed database and set `DATABASE_URL` accordingly.

## Docker Deployment

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
```

## SSL Setup

Recommended: Certbot with webroot.

1. Start Nginx on port 80.
2. Issue certificates:

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

3. Enable the HTTPS server block in `nginx/nginx.conf`.
4. Reload Nginx:

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
