import configparser

config = configparser.ConfigParser()
config.read("lnkshrt.ini")

default_instance_url = config["default"]["instance_url"]
if not (INSTANCE_URL := config.get("custom", "instance_url")):
    INSTANCE_URL = default_instance_url


TOKEN = config["authentication"].get("token")
