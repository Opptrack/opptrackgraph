from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from starlette.requests import Request
from fastapi import Response
import json
from app.core.logger import logger
import os
import time


class RawRequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware for logging raw request and response details in development environments."""

    def __init__(self, app, exclude_paths=None, log_responses=True, log_body=True):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]
        self.log_responses = log_responses
        self.log_body = log_body

    async def dispatch(self, request: Request, call_next):
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Start timing the request
        start_time = time.time()

        # Log request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        headers = dict(request.headers)

        # Remove sensitive information from headers
        if "authorization" in headers:
            headers["authorization"] = "[REDACTED]"

        log_entry = {
            "request": {
                "method": method,
                "path": path,
                "query_params": query_params,
                "headers": headers,
            }
        }

        # Log request body if configured
        if self.log_body:
            try:
                body = await request.body()

                # Try to parse as JSON for better formatting
                try:
                    body_str = body.decode("utf-8")
                    if body_str:
                        try:
                            body_json = json.loads(body_str)
                            log_entry["request"]["body"] = body_json
                        except json.JSONDecodeError:
                            log_entry["request"]["body"] = body_str
                except UnicodeDecodeError:
                    log_entry["request"]["body"] = "[Binary data]"
            except Exception as e:
                logger.error(f"Error reading request body: {e}")
                log_entry["request"]["body"] = "[Error reading body]"
                body = b""
        else:
            body = await request.body()

        # Rebuild the request body stream
        async def receive() -> Message:
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive=receive, send=request._send)

        # Process the request and capture the response
        response = await call_next(request)

        # Calculate request duration
        duration = time.time() - start_time
        log_entry["duration_ms"] = round(duration * 1000, 2)

        # Log response details if configured
        if self.log_responses:
            log_entry["response"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }

        # Log the entry
        logger.info(f"API Request: {json.dumps(log_entry)}")

        return response
