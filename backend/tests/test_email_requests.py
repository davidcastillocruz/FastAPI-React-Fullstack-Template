from src.core.limiter import limiter
from src.modules.email_requests.services.email_request_service import PAGE_SIZE


async def create(client, email: str, **kwargs):
    return await client.post("/email-requests", json={"email": email}, **kwargs)


async def test_create_saves_and_sends_the_email(client, sent_emails):
    response = await create(client, "Ana@Test.dev")

    assert response.status_code == 201
    assert response.json() == {"message": "Done! Check your inbox in a few seconds"}
    assert response.headers["X-Request-ID"]
    # Saved and sent in lowercase
    assert sent_emails[0][1] == ["ana@test.dev"]
    assert sent_emails[0][0] == "Your test email"


async def test_create_in_spanish(client, sent_emails):
    response = await create(client, "ana@test.dev", params={"lang": "es"})

    assert response.json() == {"message": "¡Hecho! Revisa tu bandeja de entrada en unos segundos"}
    assert sent_emails[0][0] == "Tu email de prueba"


async def test_create_twice_is_a_conflict(client, sent_emails):
    await create(client, "ana@test.dev")
    response = await create(client, "ANA@test.dev")

    assert response.status_code == 409
    assert response.json() == {"detail": "This email has already received a test email"}
    # Only the first one sends an email
    assert len(sent_emails) == 1


async def test_create_with_an_invalid_email(client, sent_emails):
    response = await create(client, "not-an-email", headers={"Accept-Language": "es-ES,es;q=0.9"})

    assert response.status_code == 422
    assert response.json() == {"detail": "Revisa estos campos: email"}
    assert sent_emails == []


async def test_create_without_body(client):
    response = await client.post("/email-requests")

    assert response.status_code == 422
    assert response.json() == {"detail": "Check these fields: body"}


async def test_create_is_rate_limited(client):
    statuses = [(await create(client, f"user{i}@test.dev")).status_code for i in range(6)]

    assert statuses == [201] * 5 + [429]


async def test_list_is_empty(client):
    response = await client.get("/email-requests")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_pages_newest_first(client):
    # 12 requests, without hitting the rate limit
    for i in range(12):
        await create(client, f"user{i:02}@test.dev")
        limiter.reset()

    page_1 = (await client.get("/email-requests")).json()
    page_2 = (await client.get("/email-requests", params={"page": 2})).json()
    page_3 = (await client.get("/email-requests", params={"page": 3})).json()

    assert len(page_1) == PAGE_SIZE and len(page_2) == 2 and page_3 == []
    # Newest first, no row repeated or skipped
    emails = [row["email"] for row in page_1 + page_2]
    assert emails == [f"user{i:02}@test.dev" for i in reversed(range(12))]
    assert set(page_1[0]) == {"id", "email", "created_at"}


async def test_list_with_an_invalid_page(client):
    for page in ("0", "-1", "abc", "100001"):
        response = await client.get("/email-requests", params={"page": page, "lang": "es"})
        assert response.status_code == 422
        assert response.json() == {"detail": "Revisa estos campos: page"}
