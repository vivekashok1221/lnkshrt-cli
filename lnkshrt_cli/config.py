from tomlkit import load

SETTINGS_FILE = "settings.toml"

with open(SETTINGS_FILE, "r") as f:
    config = load(f)

default_instance_url = config["default"]["instance_url"]

INSTANCE_URL = config["custom"]["instance_url"] or default_instance_url
TOKEN = config["authentication"].get("token")
