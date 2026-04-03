import json



def save_configure_json(configuration: dict):
    with open("raspi/server/configure.json", "w+") as f:
        content = f.write(json.dumps(configuration))
        print("✅ Configuration saved to raspi/server/configure.json")
       
def load_configure_json() -> list:
    try:
        with open("raspi/server/configure.json", "r") as f:
            content = f.read()
            configuration = json.loads(content)
            print("✅ Configuration loaded from raspi/server/configure.json")
            return configuration
    except FileNotFoundError:
        print("⚠️  Configuration file not found, returning empty configuration.")
        return []

loaded_config = load_configure_json()

def _is_valid_config_item(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    if str(item.get("id", "")).strip() in ("", "-1"):
        return False
    if not str(item.get("gesture", "")).strip():
        return False
    if not str(item.get("action", "")).strip():
        return False
    return True

def get_active_configs() -> list:
    return [item for item in loaded_config if _is_valid_config_item(item)]
    
if __name__ == "__main__":
    test_dictionary = {
        "setting1": True,
        "setting2": "value",
        "setting3": 42
    }
    loaded_config = load_configure_json()
    print(type(loaded_config))
    for i in loaded_config:
        if i["gesture"]=="Thumb+Index":
            print(i["action"])
            