import json
from pathlib import Path

DEFAULT_LOCALE = "en-US"
SUPPORTED_LOCALES = {"en-US", "pt-BR"}
LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


class LocaleManager:
    def __init__(
        self,
        default_locale: str = DEFAULT_LOCALE,
        supported_locales: set[str] | None = None,
        locales_dir: Path | None = None,
    ) -> None:
        self.default_locale = default_locale
        self.supported_locales = supported_locales or SUPPORTED_LOCALES
        self.locales_dir = locales_dir or LOCALES_DIR
        self.locales = self.load_locales()

    def resolve_locale(self, locale: str | object | None) -> str:
        if locale is None:
            return self.default_locale

        if hasattr(locale, "value"):
            locale = locale.value

        if not isinstance(locale, str):
            locale = str(locale)

        normalized = locale.replace("_", "-")
        if normalized in self.supported_locales:
            return normalized

        language_code = normalized.split("-")[0].lower()
        if language_code == "pt":
            return "pt-BR"

        return self.default_locale

    def resolve_interaction_locale(self, user_locale: str | object | None, guild_locale: str | object | None) -> str:
        user_locale_resolved = self.resolve_locale(user_locale)
        guild_locale_resolved = self.resolve_locale(guild_locale)

        if user_locale_resolved != self.default_locale or user_locale is not None:
            return user_locale_resolved

        if guild_locale is not None:
            return guild_locale_resolved

        return self.default_locale

    def _load_locale_file(self, locale_name: str) -> dict:
        locale_path = self.locales_dir / f"{locale_name}.json"
        if not locale_path.exists():
            fallback_path = self.locales_dir / f"{self.default_locale}.json"
            if not fallback_path.exists():
                return {}
            locale_path = fallback_path

        try:
            with locale_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            if locale_name != self.default_locale:
                return self._load_locale_file(self.default_locale)
            return {}

    def load_locales(self) -> dict[str, dict]:
        locales: dict[str, dict] = {}
        for locale_name in sorted(self.supported_locales):
            data = self._load_locale_file(locale_name)
            if data:
                locales[locale_name] = data
        if self.default_locale not in locales:
            locales[self.default_locale] = {}
        return locales

    def get_message(self, locale: str | None, key: str, **kwargs) -> str:
        locale_name = self.resolve_locale(locale)
        locale_data = self.locales.get(locale_name, self.locales.get(self.default_locale, {}))
        value: object = locale_data

        for part in key.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if not isinstance(value, str):
            fallback_data = self.locales.get(self.default_locale, {})
            value = fallback_data
            for part in key.split("."):
                if not isinstance(value, dict):
                    value = None
                    break
                value = value.get(part)

        if not isinstance(value, str):
            return key

        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value


locale_manager = LocaleManager()
