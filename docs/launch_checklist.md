# VyaparSetu Launch Checklist

## Environment

- [ ] `.env.production` created from `.env.production.example`
- [ ] Strong `SECRET_KEY` configured
- [ ] Strong PostgreSQL password configured
- [ ] `DATABASE_URL` embeds a strong non-default database password
- [ ] Production startup safety checks pass with `ENVIRONMENT=production`
- [ ] `DOCUMENT_INTELLIGENCE_ENABLED=false` for manual review mode, or production AI provider is approved
- [ ] If `DOCUMENT_INTELLIGENCE_ENABLED=true`, `AI_PROVIDER` is not `mock`
- [ ] If `DOCUMENT_INTELLIGENCE_ENABLED=true`, `AI_PROVIDER` is implemented and marked production-ready
- [ ] Required provider secrets are configured when document intelligence is enabled
- [ ] `BACKEND_CORS_ORIGINS` restricted to production domain
- [ ] `BACKEND_CORS_ORIGINS` contains only HTTPS origins and no localhost origins
- [ ] `NEXT_PUBLIC_API_BASE_URL` points to production HTTPS API
- [ ] Pricing values configured
- [ ] `ADMIN_NOTIFICATION_EMAIL` configured
- [ ] Real notification provider intentionally disabled or configured

## Security Review

- [ ] JWT secret is not committed
- [ ] JWT expiry is acceptable for production
- [ ] Admin routes require admin role
- [ ] Customer APIs enforce owner access
- [ ] Upload validation allows only PDF/JPG/JPEG/PNG
- [ ] Upload max size is 10MB
- [ ] Nginx `client_max_body_size` allows uploads but remains bounded
- [ ] CORS is restricted
- [ ] Rate limiting is enabled
- [ ] `.env.production` excluded from git
- [ ] No government portal automation enabled

## Database

- [ ] PostgreSQL volume configured
- [ ] Connection pool settings reviewed
- [ ] `alembic heads` returns one head
- [ ] `alembic upgrade head` completed
- [ ] Backup created before launch
- [ ] Restore process tested on staging

## Docker

- [ ] `docker compose -f docker-compose.prod.yml config` passes
- [ ] Backend image builds
- [ ] Frontend image builds
- [ ] Nginx config mounted
- [ ] Upload volume mounted
- [ ] Services restart automatically

## SSL And Domain

- [ ] DNS points to VPS
- [ ] HTTP challenge path works
- [ ] SSL certificate issued
- [ ] HTTPS server block uses the production domain and certificate paths
- [ ] HTTP redirects to HTTPS except `/.well-known/acme-challenge/`
- [ ] HSTS header is present on HTTPS responses
- [ ] Certificate renewal scheduled

## Product Smoke Tests

- [ ] Landing page loads
- [ ] Lead capture works
- [ ] Customer register/login works
- [ ] Application creation works
- [ ] Document upload works
- [ ] AI mock extraction runs
- [ ] Customer notifications display
- [ ] Admin login works
- [ ] Admin application review works
- [ ] Admin lead management works
- [ ] Admin analytics renders
- [ ] `/health` passes
- [ ] `/health/db` passes
- [ ] `/metrics` returns status

## Monitoring

- [ ] Docker logs available
- [ ] Disk usage alert configured
- [ ] 5xx alert configured
- [ ] DB health alert configured
- [ ] Backup alert configured
