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

    nginx = Path("nginx/nginx.conf").read_text()
    for token in ["location /api/", "location /", "client_max_body_size", "ssl_certificate"]:
        if token not in nginx:
            raise AssertionError(f"Missing {token} in nginx config")

    print("Production configuration verification passed")


if __name__ == "__main__":
    main()
