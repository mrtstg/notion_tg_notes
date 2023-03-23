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

    def __init__(self, path: str):
        self._path = path
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            self.__dict__.update(**data)


def get_config() -> FileConfig:
    return FileConfig(os.environ.get("CONFIG_FILE", "config.yaml"))
