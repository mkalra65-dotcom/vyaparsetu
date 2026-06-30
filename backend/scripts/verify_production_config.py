from pathlib import Path

REQUIRED_FILES = [
    "docker-compose.prod.yml",
    "backend/Dockerfile.prod",
    "frontend/Dockerfile.prod",
    "nginx/nginx.conf",
    ".env.production.example",
    "docs/deployment.md",
    "docs/launch_checklist.md",
]


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not Path(path).exists()]
    if missing:
        raise AssertionError(f"Missing production files: {missing}")

    env_example = Path(".env.production.example").read_text()
    for key in ["SECRET_KEY", "DATABASE_URL", "BACKEND_CORS_ORIGINS", "NEXT_PUBLIC_API_BASE_URL"]:
        if key not in env_example:
            raise AssertionError(f"Missing {key} in .env.production.example")
    for forbidden in [
        "SECRET_KEY=change-this-secret-key",
        "POSTGRES_PASSWORD=vyaparsetu",
        "AI_PROVIDER=openai",
        "NEXT_PUBLIC_API_BASE_URL=http://",
    ]:
        if forbidden in env_example:
            raise AssertionError(f"Unsafe production example value found: {forbidden}")
    if "DOCUMENT_INTELLIGENCE_ENABLED=false" not in env_example:
        raise AssertionError("Production example must default document intelligence to manual review mode")

    config = Path("backend/app/core/config.py").read_text()
    for token in [
        "PRODUCTION_ENVIRONMENTS",
        "NON_PRODUCTION_ENVIRONMENTS",
        "PRODUCTION_READY_AI_PROVIDERS",
        "DOCUMENT_INTELLIGENCE_ENABLED",
        "validate_database_password",
        "DATABASE_URL password",
    ]:
        if token not in config:
            raise AssertionError(f"Missing production safety validation for {token}")

    nginx = Path("nginx/nginx.conf").read_text()
    for token in [
        "location /api/",
        "client_max_body_size",
        "ssl_certificate",
        "return 301 https://$host$request_uri",
        "Strict-Transport-Security",
        "listen 443 ssl http2",
    ]:
        if token not in nginx:
            raise AssertionError(f"Missing {token} in nginx config")
    if "SSL-ready server. Enable after certificates exist." in nginx:
        raise AssertionError("HTTPS server block must be active, not commented as a future step")

    deployment = Path("docs/deployment.md").read_text()
    for token in [
        "Production startup safety checks",
        "DOCUMENT_INTELLIGENCE_ENABLED=false",
        "manual review mode",
        "extraction jobs",
        "`DATABASE_URL` is missing, omits a password",
        "Strict-Transport-Security",
        "returns a `301` redirect to HTTPS",
    ]:
        if token not in deployment:
            raise AssertionError(f"Missing deployment documentation for {token}")

    checklist = Path("docs/launch_checklist.md").read_text()
    for token in [
        "Production startup safety checks pass",
        "`DATABASE_URL` embeds a strong non-default database password",
        "`DOCUMENT_INTELLIGENCE_ENABLED=false` for manual review mode",
        "If `DOCUMENT_INTELLIGENCE_ENABLED=true`, `AI_PROVIDER` is not `mock`",
        "If `DOCUMENT_INTELLIGENCE_ENABLED=true`, `AI_PROVIDER` is implemented and marked production-ready",
        "HTTP redirects to HTTPS",
        "HSTS header is present",
    ]:
        if token not in checklist:
            raise AssertionError(f"Missing launch checklist item for {token}")

    print("Production configuration verification passed")


if __name__ == "__main__":
    main()
