import logging
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("vyaparsetu.requests")
rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", uuid4().hex)
        start = time.time()
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra={"request_id": request_id, "path": request.url.path, "method": request.method},
            )
            raise
        duration_ms = round((time.time() - start) * 1000, 2)
        response.headers["x-request-id"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/health/db"}:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = rate_limit_buckets[client]
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= settings.RATE_LIMIT_PER_MINUTE:
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )
        bucket.append(now)
        return await call_next(request)
