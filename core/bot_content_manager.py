import yaml
import logging
import random


class BotContentManager:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lexicon_data = self._load_yaml_file()

    def _load_yaml_file(self) -> dict:
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
                logging.info(f"Файл контента '{self.filepath}' успешно загружен.")
                return data or {}
        except FileNotFoundError:
            logging.error(f"Критическая ошибка: Файл '{self.filepath}' не найден!")
            return {}
        except yaml.YAMLError as error:
            logging.error(f"Ошибка чтения YAML структуры: {error}")
            return {}

    def get_screen_data(self, screen_name: str) -> dict:
        try:
            return self.lexicon_data["screens"][screen_name]
        except KeyError:
            logging.warning(f"Экран '{screen_name}' не найден в словаре.")
            return {}

    def get_screen_text(self, screen_name: str, **format_values) -> str:
        screen_data = self.get_screen_data(screen_name)
        text_template = screen_data.get("text", "Текст временно недоступен.")

        try:
            return text_template.format(**format_values)
        except KeyError as error:
            logging.warning(
                f"Для экрана '{screen_name}' не хватило значения для шаблона: {error}"
            )
            return text_template

    def get_screen_buttons(self, screen_name: str) -> list[dict]:
        screen_data = self.get_screen_data(screen_name)
        return screen_data.get("buttons", [])

    def get_cancel_button(self, screen_name: str) -> dict | None:
        screen_data = self.get_screen_data(screen_name)
        return screen_data.get("cancel_button")

    def get_easter_egg_text(self, easter_egg_key: str) -> str:
        easter_eggs = self.lexicon_data.get("easter_eggs", {})
        return easter_eggs.get(easter_egg_key, "")

    def get_default_first_vault_screen_quote(self) -> str:
        vault_screen_quotes = self.lexicon_data.get("vault_screen_quotes", {})
        return vault_screen_quotes.get(
            "default_first_quote",
            "Кря! Главное держать хранилище под контролем."
        )

    def get_random_financial_literacy_quote_for_vault_screen(self) -> str:
        vault_screen_quotes = self.lexicon_data.get("vault_screen_quotes", {})
        random_financial_literacy_quotes = vault_screen_quotes.get(
            "random_financial_literacy_quotes",
            []
        )

        if not random_financial_literacy_quotes:
            return self.get_default_first_vault_screen_quote()

        return random.choice(random_financial_literacy_quotes)

    def get_vault_screen_image_path_by_image_key(self, vault_image_key: str) -> str:
        vault_screen_image_paths = self.lexicon_data.get(
            "vault_screen_image_paths",
            {}
        )

        return vault_screen_image_paths.get(vault_image_key, "")

    def get_screen_image_path(self, screen_name: str) -> str:
        screen_data = self.get_screen_data(screen_name)
        return screen_data.get("image_path", "")