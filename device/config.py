import json
import collections


class Configuration:
    Network = collections.namedtuple("Network", ("ssid", "key"))
    default_config_name = "default"

    def __init__(self, json_obj: dict):
        self.json_obj = json_obj

    @property
    def networks(self) -> list[Network]:
        return [
            Configuration.Network(**net) for net in self.json_obj.get("networks", [])
        ]

    @staticmethod
    def load(name: str = default_config_name) -> "Configuration":
        with open(f"configuration/{name}.json", "r") as f:
            return Configuration(json.load(f))

    def save(self, name: str = default_config_name):
        with open(f"configuration/{name}.json", "w") as f:
            json.dump(self.json_obj, f)
