import logging

import pytest
from fastapi import HTTPException

from src.core.logger import RequestContextFilter
from src.main import app


async def test_unknown_route_is_translated(client):
    response = await client.get("/nope", headers={"Accept-Language": "es"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Esta página o recurso no existe"}


async def test_wrong_method_lists_every_allowed_method(client):
    response = await client.delete("/email-requests")

    assert response.status_code == 405
    assert response.json() == {"detail": "This action isn't allowed here"}
    # GET and POST are two functions on the same path, both are listed
    assert response.headers["allow"] == "GET, POST"


async def test_malformed_json(client):
    response = await client.post(
        "/email-requests", content="{bad json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Check these fields: body"}


@pytest.fixture
def error_routes():
    async def boom():
        raise RuntimeError("unexpected")

    async def own_404():
        raise HTTPException(404, detail="Custom text")

    app.add_api_route("/test-boom", boom)
    app.add_api_route("/test-own-404", own_404)
    yield
    app.router.routes = [r for r in app.router.routes if getattr(r, "path", "") not in ("/test-boom", "/test-own-404")]


async def test_unhandled_error_is_a_translated_500(client, error_routes):
    response = await client.get("/test-boom", params={"lang": "es"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Algo ha fallado en el servidor, inténtalo más tarde"}
    assert response.headers["X-Request-ID"]


async def test_500_has_cors_headers(client, error_routes):
    response = await client.get("/test-boom", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


async def test_every_request_is_logged_with_its_level(client, error_routes, caplog):
    with caplog.at_level(logging.INFO, logger="src.main"):
        await client.get("/email-requests")
        await client.get("/nope")
        await client.get("/test-boom")

    records = {record.getMessage(): record for record in caplog.records if record.name == "src.main"}
    assert records["GET /email-requests 200"].levelno == logging.INFO
    assert records["GET /nope 404"].levelno == logging.WARNING
    # The 500 goes with its traceback
    assert records["GET /test-boom 500"].levelno == logging.ERROR
    assert records["GET /test-boom 500"].exc_info is not None


async def test_request_logs_carry_its_id_and_ip(client, caplog):
    # The filter of the app's handler, caplog has its own handler
    caplog.handler.addFilter(RequestContextFilter())
    with caplog.at_level(logging.INFO, logger="src.main"):
        response = await client.get("/email-requests")

    record = next(record for record in caplog.records if record.getMessage() == "GET /email-requests 200")
    assert record.request_id == response.headers["X-Request-ID"]
    assert record.client_ip == "127.0.0.1"


async def test_own_http_exception_keeps_its_text(client, error_routes):
    response = await client.get("/test-own-404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Custom text"}


async def test_cors(client):
    allowed = await client.get("/email-requests", headers={"Origin": "http://localhost:5173"})
    other = await client.get("/email-requests", headers={"Origin": "http://evil.com"})

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "X-Request-ID" in allowed.headers["access-control-expose-headers"]
    assert "access-control-allow-origin" not in other.headers


async def test_docs_only_show_real_schemas(client):
    schema = (await client.get("/openapi")).json()

    assert set(schema["components"]["schemas"]) == {
        "EmailRequestCreate", "EmailRequestResponse", "MessageResponse", "ErrorResponse"
    }
    for operation in schema["paths"]["/email-requests"].values():
        assert operation["responses"]["422"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponse"
        }
