import json

import pytest
from starlette.requests import Request

from src.api.dependencies import get_language
from src.core import languages
from src.core.languages import get_error_detail, get_response, setup_language_system


def request_with(headers: dict[str, str] | None = None, cookies: str | None = None) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    if cookies:
        raw.append((b"cookie", cookies.encode()))
    return Request({"type": "http", "headers": raw, "query_string": b""})


# --- get_language: ?lang= > cookie > Accept-Language > MAIN_LANGUAGE ---

def test_language_priority():
    request = request_with({"Accept-Language": "en"}, cookies="language=en")
    assert get_language(request, "ES") == "es"
    assert get_language(request_with({"Accept-Language": "en"}, cookies="language=es")) == "es"
    assert get_language(request_with({"Accept-Language": "es-ES,es;q=0.9,en;q=0.8"})) == "es"


def test_language_quality_and_fallbacks():
    assert get_language(request_with({"Accept-Language": "fr;q=1, en;q=0.5, es;q=0.9"})) == "es"
    assert get_language(request_with({"Accept-Language": "es;q=0, en"})) == "en"
    assert get_language(request_with({"Accept-Language": "*, fr, es;q=bad"})) == "en"
    assert get_language(request_with(), "fr") == "en"
    assert get_language(request_with()) == "en"


# --- setup_language_system: every broken file stops the startup ---

@pytest.fixture
def translations(tmp_path, monkeypatch):
    # Points the system to a temporary src/ and restores the real translations afterwards
    real = languages.LANGUAGE_DATA
    monkeypatch.setattr(languages, "SRC_DIR", tmp_path / "src")
    monkeypatch.setattr(languages, "BASE_DIR", tmp_path)
    folder = tmp_path / "src" / "translations"
    folder.mkdir(parents=True)

    def write(data, name="test_translations.json", raw: str | None = None):
        (folder / name).write_text(raw if raw is not None else json.dumps(data), encoding="utf-8")

    yield write
    languages.LANGUAGE_DATA = real


def entry(en: dict, es: dict) -> dict:
    return {"en": en, "es": es}


def test_valid_file_loads(translations):
    translations({"HELLO": entry({"detail": "Hi %s"}, {"detail": "Hola %s"})})
    setup_language_system()

    assert get_response("HELLO", "es", {"detail": ("Ana",)}) == {"detail": "Hola Ana"}
    assert get_error_detail("HELLO", "en") == "Hi %s"


def test_extra_language_is_ignored(translations):
    translations({"HELLO": {"en": {"detail": "Hi"}, "es": {"detail": "Hola"}, "fr": {"detail": "Salut"}}})
    setup_language_system()

    assert set(languages.LANGUAGE_DATA["HELLO"]) == {"en", "es"}


@pytest.mark.parametrize("data, raw", [
    (None, "{bad json"),
    (None, '{"A": {}, "A": {}}'),
    ([], None),
    ({"A": "text"}, None),
    ({"A": {"en": {"detail": "x"}}}, None),
    ({"A": entry({"detail": "x"}, "text")}, None),
    ({"A": entry({"detail": 1}, {"detail": "x"})}, None),
    ({"A": entry({"detail": "x"}, {"other": "x"})}, None),
    ({"A": entry({"detail": "%s"}, {"detail": "x"})}, None),
    ({"A": entry({"detail": "50% %s"}, {"detail": "50% %s"})}, None),
], ids=[
    "invalid json", "repeated key", "not an object", "entry not an object", "missing language",
    "texts not an object", "text not a string", "different texts", "different placeholders", "unfillable",
])
def test_broken_file_stops_startup(translations, data, raw):
    translations(data, raw=raw)

    with pytest.raises((ValueError, TypeError)):
        setup_language_system()


def test_same_name_in_two_files_stops_startup(translations):
    translations({"A": entry({"detail": "x"}, {"detail": "x"})}, name="one_translations.json")
    translations({"A": entry({"detail": "y"}, {"detail": "y"})}, name="two_translations.json")

    with pytest.raises(ValueError):
        setup_language_system()


def test_no_files_stops_startup(translations, tmp_path):
    (tmp_path / "src" / "translations").rmdir()

    with pytest.raises(FileNotFoundError):
        setup_language_system()


def test_literal_percent_works_when_escaped(translations):
    translations({"A": entry({"detail": "50%% off for %s"}, {"detail": "50%% para %s"})})
    setup_language_system()

    assert get_error_detail("A", "en", {"detail": ("Ana",)}) == "50% off for Ana"


def test_unknown_response_and_wrong_args_fail(translations):
    translations({"A": entry({"detail": "x"}, {"detail": "x"})})
    setup_language_system()

    with pytest.raises(KeyError):
        get_response("NOPE", "en")
    with pytest.raises(TypeError):
        get_response("A", "en", {"detail": ("extra",)})
