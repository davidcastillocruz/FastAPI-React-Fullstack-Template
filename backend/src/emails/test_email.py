from src.core.languages import get_response


# Test email of the demo: subject and HTML body in the user's language, no styles yet
def build_test_email(language: str) -> tuple[str, str]:
    texts = get_response("TEST_EMAIL", language)
    body = f"<h1>{texts['title']}</h1><p>{texts['text']}</p>"
    return texts["subject"], body
