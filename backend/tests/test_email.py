from src.core.email import _mask_email


def test_mask_email():
    assert _mask_email("ana@test.dev") == "a***@test.dev"
    assert _mask_email("@test.dev") == "***@test.dev"
    assert _mask_email("not-an-email") == "***"
