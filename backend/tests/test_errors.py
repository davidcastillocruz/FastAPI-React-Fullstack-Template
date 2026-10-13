import pytest
from fastapi import HTTPException

from src.main import app


async def test_unknown_route_is_translated(client):
    response = await client.get("/nope", headers={"Accept-Language": "es"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Esta página o recurso no existe"}


async def test_wrong_method_keeps_the_allow_header(client):
    response = await client.delete("/email-requests")

    assert response.status_code == 405
    assert response.json() == {"detail": "This action isn't allowed here"}
    # Starlette lists the methods of the first route with that path
    assert response.headers["allow"]


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
