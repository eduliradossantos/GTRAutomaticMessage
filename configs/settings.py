import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

def load_settings():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    return config

def save_settings(settings_dict):
    config = configparser.ConfigParser()
    config["SETTINGS"] = settings_dict
    
    with open(CONFIG_PATH, "w") as configfile:
        config.write(configfile)
