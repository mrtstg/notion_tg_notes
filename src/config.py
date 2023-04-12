import yaml
import os


class FileConfig:
    token: str
    tg_token: str
    db_id: str
    _path: str
    importance_values: list[str]
    remind_values: list[str]
    progress_values: list[str]
    categories_values: list[str]
    daily_notes: list[dict]

    def __init__(self, path: str):
        self._path = path
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            self.__dict__.update(**data)

    def validate_daily_notes(self):
        for note in self.daily_notes:
            assert (
                note["importance"] in self.importance_values
            ), "Значения важности заметки нет в конфиге!"
            for cat in note["category"]:
                assert cat in self.categories_values, "Неизвестная категория заметки!"
            assert len(note["title"]) > 1, "У заметки должен быть заголовок!"


def get_config() -> FileConfig:
    return FileConfig(os.environ.get("CONFIG_FILE", "config.yaml"))
