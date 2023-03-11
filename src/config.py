import yaml


class FileConfig:
    token: str
    tg_token: str
    db_id: str
    _path: str

    def __init__(self, path: str):
        self._path = path
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            self.__dict__.update(**data)
