import json
import logging
from pathlib import Path

from src.core import settings

logger = logging.getLogger(__name__)


# Every *_translations.json inside src/: core/translations has the shared ones,
# modules/<module>/translations the ones of each module, one file per service
LANGUAGE_DATA: dict[str, dict[str, dict[str, str]]] = {}


# Reads one translations file, stops startup if it can't be read or isn't a JSON object
def _read_translations_file(file: Path) -> dict:
    path = file.relative_to(settings.BASE_DIR).as_posix()

    try:
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)

    except json.JSONDecodeError as exc:
        logger.critical(
            "Invalid JSON in translations file: %s",
            exc.msg,
            extra={"path": path, "line": exc.lineno, "column": exc.colno}
        )
        raise

    except UnicodeDecodeError:
        logger.critical("Translations file is not valid UTF-8", extra={"path": path})
        raise

    except OSError:
        # Permission denied, file is a directory, disk errors...
        logger.exception("Could not read translations file", extra={"path": path})
        raise

    if not isinstance(data, dict):
        logger.critical(
            "Translations file must contain a JSON object",
            extra={"path": path, "type": type(data).__name__}
        )
        raise TypeError(f"Expected a dict in {path}, got {type(data).__name__}")

    return data


def setup_language_system() -> None:
    global LANGUAGE_DATA

    files = sorted(settings.SRC_DIR.rglob("translations/*_translations.json"))
    if not files:
        logger.critical("No translations files found", extra={"path": settings.SRC_DIR.relative_to(settings.BASE_DIR).as_posix()})
        raise FileNotFoundError(f"No translations/*_translations.json files in {settings.SRC_DIR}")

    available = set(settings.AVAILABLE_LANGUAGES)
    data: dict[str, dict[str, dict[str, str]]] = {}
    # File of each response, to report where a repeated name is
    sources: dict[str, str] = {}

    for file in files:
        path = file.relative_to(settings.BASE_DIR).as_posix()

        for name, languages in _read_translations_file(file).items():
            # Same name in two files: one would silently replace the other -> stop startup
            if name in sources:
                logger.critical(
                    "Response defined in two translations files",
                    extra={"entry": name, "files": [sources[name], path]}
                )
                raise ValueError(f"Response '{name}' is in {sources[name]} and {path}")

            if not isinstance(languages, dict):
                logger.critical(
                    "Invalid response entry, languages must be an object",
                    extra={"path": path, "entry": name, "type": type(languages).__name__}
                )
                raise TypeError(f"Expected a dict in {path} [{name}], got {type(languages).__name__}")

            # Missing languages: the response can't be served -> stop startup
            missing = available - set(languages)
            if missing:
                logger.critical(
                    "Response is missing available languages",
                    extra={"path": path, "entry": name, "missing": sorted(missing)}
                )
                raise ValueError(f"Response '{name}' in {path} is missing languages: {sorted(missing)}")

            for language, texts in languages.items():
                # Extra languages: harmless, just never used
                if language not in available:
                    logger.warning(
                        "Response has a language not in AVAILABLE_LANGUAGES, it will be ignored",
                        extra={"path": path, "entry": name, "language": language}
                    )
                    continue

                if not isinstance(texts, dict):
                    logger.critical(
                        "Invalid translation, texts must be an object",
                        extra={"path": path, "entry": name, "language": language, "type": type(texts).__name__}
                    )
                    raise TypeError(f"Expected a dict in {path} [{name}][{language}], got {type(texts).__name__}")

            # Same texts in every language (detail, message...), or asking for one of them would fail later
            texts_by_language = {language: sorted(languages[language]) for language in sorted(available)}
            if len({tuple(texts) for texts in texts_by_language.values()}) > 1:
                logger.critical(
                    "Response has different texts in each language",
                    extra={"path": path, "entry": name, "texts": texts_by_language}
                )
                raise ValueError(f"Response '{name}' in {path} has different texts in each language: {texts_by_language}")

            data[name] = languages
            sources[name] = path

    LANGUAGE_DATA = data
    logger.info(
        "Language system loaded",
        extra={"files": len(files), "responses": len(LANGUAGE_DATA), "languages": sorted(available)}
    )


# Texts of a response in the given language
# args fills the %s of each text: {"detail": ("ana@test.dev",)}. Texts without args are returned as they are,
# so a literal % only needs to be written %% in texts that take args
def get_response(name: str, language: str, args: dict[str, tuple] | None = None) -> dict[str, str]:
    args = args or {}

    try:
        texts = LANGUAGE_DATA[name][language]
        return {key: text % args[key] if key in args else text for key, text in texts.items()}

    except KeyError:
        logger.error("Response not found", extra={"entry": name, "language": language})
        raise

    except TypeError:
        # Wrong number/type of placeholder args
        logger.error("Invalid arguments for response", extra={"entry": name, "language": language, "format_args": args})
        raise


# The "detail" text of an error response, fails if the entry has no "detail"
def get_error_detail(name: str, language: str, args: dict[str, tuple] | None = None) -> str:
    return get_response(name, language, args)["detail"]
