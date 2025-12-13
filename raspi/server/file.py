import json

def save_configure_json(configuration: dict):
    with open("raspi/server/configure.json", "w+") as f:
        content = f.write(json.dumps(configuration))
        print("✅ Configuration saved to raspi/server/configure.json")
       
def load_configure_json() -> dict:
    try:
        with open("raspi/server/configure.json", "r") as f:
            content = f.read()
            configuration = json.loads(content)
            print("✅ Configuration loaded from raspi/server/configure.json")
            return configuration
    except FileNotFoundError:
        print("⚠️  Configuration file not found, returning empty configuration.")
        return {}