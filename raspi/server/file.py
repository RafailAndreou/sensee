import json

def save_configure_json(configuration: dict):
    with open("raspi/server/configure.json", "w+") as f:
        content = f.write(json.dumps(configuration))
        print("✅ Configuration saved to raspi/server/configure.json")
       
        
        
