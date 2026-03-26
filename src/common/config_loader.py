from src.common.io_utils import read_yaml
from src.common.paths import CONFIG_DIR


def load_config(name: str):
    path = CONFIG_DIR / name
    return read_yaml(path)
