import yaml
import logging


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

    def get_screen_text(self, screen_name: str, **format_values) -> str:
        try:
            text_template = self.lexicon_data["screens"][screen_name]["text"]
        except KeyError:
            logging.warning(f"Текст для экрана '{screen_name}' не найден в словаре.")
            return "Текст временно недоступен."

        try:
            return text_template.format(**format_values)
        except KeyError as error:
            logging.warning(
                f"Для экрана '{screen_name}' не хватило значения для шаблона: {error}"
            )
            return text_template