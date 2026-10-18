from src.core.email import _mask_email
from src.emails.test_email import build_test_email


def test_mask_email():
    assert _mask_email("ana@test.dev") == "a***@test.dev"
    assert _mask_email("@test.dev") == "***@test.dev"
    assert _mask_email("not-an-email") == "***"


def test_test_email_in_each_language():
    subject, body = build_test_email("es")

    assert subject == "Tu email de prueba"
    assert '<html lang="es">' in body and "¡Funciona!" in body
    # The status of the board, one flap per letter
    assert all(f">{letter}</td>" in body for letter in "ENTREGADO")
    assert build_test_email("en")[0] == "Your test email"
