
import os
import json
from collections import namedtuple


class ConfigReader:

    """This class is used to read the configs defined inside
    config.json file
    """

    _instance = {}

    def __init__(self, json_path="restoreconfig.json"):
        """
        json_path<str>: The file path where config.json is residing
        """
        self._config_file = json_path
        self._file_data = None
        self._configs = None

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instance:
            instance = super(ConfigReader, cls).__new__(cls)
            cls._instance[cls] = instance
        return cls._instance[cls]

    def _get_file_data(self):
        if self._file_data is None:
            with open(self._config_file, encoding='utf-8') as config_file:
                self._file_data = config_file.read()
        return self._file_data

    def reset(self):
        """Reset the data cached by the ConfigReader"""
        self._file_data = None
        self._configs = None

    def get_config(self):
        """Read the config from the config.json and cache it in memory"""
        try:
            if self._configs is None:
                self._configs = json.loads(
                    self._get_file_data(),
                    object_hook=lambda d: namedtuple('config', d.keys())(*d.values()))
            return self._configs
        except Exception as e:
            raise Exception("Unable to parse [{}], received error [{}: {}]".format(
                os.path.basename(self._config_file), type(e), str(e)))


def get_config(reset=False, json_path="restoreconfig.json"):
    """Read the config from config.json file

    Args:
        reset<bool>: Use this to drop the cached config and re-read
            from the config.json file
        json_path<str>: The file path where config.json is residing
    """
    config = ConfigReader(json_path)
    if reset:
        config.reset()
    return config.get_config()
