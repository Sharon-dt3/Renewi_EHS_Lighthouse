"""S13 local-only inference API. Start from the application root with backend.app:app."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.models import ErrorResult, HealthResult, InferResult
from backend.service import InferenceService, load_settings
from backend.security import (ENV_AUDIT_LOG, SecurityMiddleware, SecuritySettings, configure_audit_file, install_redaction,
                              load_security)

MULTIPART_OVERHEAD = 64 * 1024


# PUBLIC_INTERFACE
class BoundedBodyMiddleware:
    """Cap actual ASGI body bytes before multipart parsing, including chunked bodies."""

    def __init__(self, app, limit):
        """Wrap an ASGI app with a callable per-request byte limit."""
        self.app, self.limit = app, limit

    # PUBLIC_INTERFACE
    async def __call__(self, scope, receive, send):
        """Reject oversized inference bodies without trusting Content-Length."""
        if scope["type"] != "http" or scope["path"] != "/infer":
            await self.app(scope, receive, send)
            return
        limit = self.limit()
        for key, value in scope.get("headers", []):
            if key.lower() == b"content-length":
                try:
                    length = int(value)
                    if length < 0:
                        raise ValueError
                except ValueError:
                    await JSONResponse({"detail": "Invalid Content-Length"}, 400)(scope, receive, send)
                    return
                if length > limit:
                    await JSONResponse({"detail": "Request exceeds size limit"}, 413)(scope, receive, send)
                    return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > limit:
                await JSONResponse({"detail": "Request exceeds size limit"}, 413)(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay, send)


ERROR_RESPONSES = {
    code: {"model": ErrorResult, "description": description}
    for code, description in {
        400: "Malformed multipart request or Content-Length.",
        413: "Request, image bytes, dimensions or pixel count exceeds limits.",
        415: "Unsupported request or image media type.",
        422: "Invalid fields, clip identifier, image or clip dimensions.",
        500: "Sanitized unexpected inference failure.",
        503: "Model/configuration unavailable or inference worker busy.",
    }.items()
}

INFER_BODY = {
    "requestBody": {
        "required": True,
        "content": {"multipart/form-data": {"schema": {
            "type": "object", "additionalProperties": False,
            "required": ["clip_id", "image"],
            "properties": {
                "clip_id": {"type": "string", "minLength": 1, "maxLength": 64,
                            "pattern": "^[A-Za-z0-9_-]+$",
                            "description": "Server registry key, never a path, URL or configuration."},
                "image": {"type": "string", "format": "binary",
                          "description": "Single non-animated JPEG or PNG image."},
            },
        }}},
    },
}


# PUBLIC_INTERFACE
def create_app(service: InferenceService | None = None, security: SecuritySettings | None = None) -> FastAPI:
    """Create the application; optional service and security injection support model-free tests.

    Security settings are mandatory: when none are injected they are read from the environment at startup, and a missing
    or weak configuration raises, so the service never starts unprotected (fail closed).
    """

    @asynccontextmanager
    async def lifespan(application):
        application.state.security = security or load_security()          # raises SecurityConfigError: startup aborts
        install_redaction(application.state.security.secrets())
        configure_audit_file(os.environ.get(ENV_AUDIT_LOG))
        if service is None:
            try:
                settings = load_settings()
                application.state.body_limit = settings.max_file_bytes + MULTIPART_OVERHEAD
                application.state.service = await run_in_threadpool(InferenceService, settings)
            except Exception:
                # Fail closed, but keep /health available; do not expose paths or checkpoint details.
                application.state.service = None
        yield
        application.state.service = None

    application = FastAPI(
        title="Renewi PPE Inference API", version="1.0.0",
        description=(
            "S13 / G1, ADR-003: bounded multipart image inference using the same "
            "S11 FrameAnalyzer as the CLI. Server-owned clip registry only; no URLs "
            "or paths from clients. No raw-frame retention or tracking. Immediate "
            "observations are not smoothed/persisted incidents. S14 authentication "
            "S14: every route requires an allow-listed socket peer and HTTP Basic credentials; uploads are "
            "supervisor-only. HTTPS is required beyond localhost."
        ),
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Inference", "description": "Frame-local PPE and optional zone analysis."},
            {"name": "Health", "description": "Application liveness and model readiness."},
        ],
    )
    application.state.service = service
    application.state.body_limit = (
        service.settings.max_file_bytes + MULTIPART_OVERHEAD
        if service else 5 * 1024 * 1024 + MULTIPART_OVERHEAD
    )
    application.add_middleware(BoundedBodyMiddleware, limit=lambda: application.state.body_limit)
    application.state.security = None                                      # set at startup; None means refuse everything (503)
    application.add_middleware(SecurityMiddleware, settings=lambda: application.state.security)   # outermost: runs first

    @application.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse({"detail": "Invalid request fields"}, status_code=422)

    # PUBLIC_INTERFACE
    @application.get("/health", response_model=HealthResult, tags=["Health"],
                     operation_id="getHealth", summary="Check liveness and inference readiness",
                     description="Returns 200 only when the registered model and server configuration are loaded.",
                     responses={503: {"model": HealthResult, "description": "Alive, but inference unavailable."}})
    async def health():
        """Accept no parameters; return liveness and model/configuration readiness."""
        ready = application.state.service is not None
        return JSONResponse({"status": "ready" if ready else "not_ready", "ready": ready},
                            status_code=200 if ready else 503)

    # PUBLIC_INTERFACE
    @application.post("/infer", response_model=InferResult, tags=["Inference"],
                      operation_id="inferImage", summary="Analyze a bounded uploaded image",
                      description=(
                          "Upload exactly image and clip_id as multipart/form-data. JPEG/PNG only. "
                          "Defaults: 5 MiB file, 4096 px per dimension, 12 million pixels; server "
                          "configuration can tighten or adjust within hard bounds. Envelope overhead "
                          "is capped at 64 KiB. Unknown clips and zone dimension mismatches are rejected. "
                          "Boxes remain in original image pixels. No client model, thresholds, zones, "
                          "paths or URLs. Only one model execution at a time; busy requests receive 503."
                      ),
                      responses=ERROR_RESPONSES, openapi_extra=INFER_BODY)
    async def infer(request: Request):
        """Accept multipart image/clip_id; return unchanged S11 analysis with server provenance."""
        current = application.state.service
        if current is None:
            raise HTTPException(503, "Inference service is not ready")
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "multipart/form-data":
            raise HTTPException(415, "Expected multipart/form-data")
        try:
            async with request.form(max_files=1, max_fields=1, max_part_size=1024) as form:
                # Reject duplicate and extra fields; never use the uploaded filename as a path.
                pairs = list(form.multi_items())
                if len(pairs) != 2 or {key for key, _ in pairs} != {"image", "clip_id"}:
                    raise HTTPException(422, "Expected exactly image and clip_id")
                image, clip_id = form["image"], form["clip_id"]
                if not isinstance(image, UploadFile) or not isinstance(clip_id, str):
                    raise HTTPException(422, "Invalid image or clip_id field")
                if clip_id not in current.settings.clips:
                    raise HTTPException(422, "Unknown clip_id")
                if image.content_type not in {"image/jpeg", "image/png"}:
                    raise HTTPException(415, "Only JPEG and PNG images are supported")
                data = await image.read(current.settings.max_file_bytes + 1)
                return await run_in_threadpool(current.infer, clip_id, data)
        except HTTPException:
            raise
        except StarletteHTTPException as error:
            raise HTTPException(error.status_code, "Malformed multipart request") from error
        except Exception as error:
            raise HTTPException(500, "Inference failed") from error

    base_openapi = application.openapi

    def secured_openapi():
        """Published contract with the S14 security scheme and the 401/403 responses on every operation."""
        if application.openapi_schema:
            return application.openapi_schema
        schema = base_openapi()
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["basicAuth"] = {
            "type": "http", "scheme": "basic",
            "description": "HTTP Basic with named users. Two roles: supervisor (may upload) and read-only (may not). HTTPS is required beyond localhost.",
        }
        schema["security"] = [{"basicAuth": []}]
        for operations in schema["paths"].values():
            for operation in operations.values():
                operation["security"] = [{"basicAuth": []}]
                operation["responses"]["401"] = {
                    "description": "Missing or invalid credentials. Includes a WWW-Authenticate: Basic challenge.",
                    "headers": {"WWW-Authenticate": {"schema": {"type": "string"}}},
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResult"}}},
                }
                operation["responses"]["403"] = {
                    "description": "Peer address not allow-listed, or the credential's role may not perform this operation.",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResult"}}},
                }
                operation["responses"]["429"] = {
                    "description": "Too many failed logins from this peer; retry after the Retry-After seconds.",
                    "headers": {"Retry-After": {"schema": {"type": "integer"}}},
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResult"}}},
                }
                operation["responses"].setdefault("503", {"description": "Security or model not ready."})
        application.openapi_schema = schema
        return schema

    application.openapi = secured_openapi
    return application


app = create_app()
