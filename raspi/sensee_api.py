from typing import List, Dict
from pydantic import BaseModel
from raspi.server import file 

# --- 1. THE MENU (Data for the App) ---
class ApiCommand(BaseModel):
    name: str          
    endpoint: str      
    description: str

# The Registry: This list tells the App what buttons to show
command_registry: List[ApiCommand] = []

def register_command(cmd: ApiCommand):
    command_registry.append(cmd)

# --- 2. THE LOGIC (What happens when they click save) ---
def add_connection_logic(action: str, gesture: str, sound: str):
    # This DOES change the server, because the Pi needs to remember the mapping
    current_config = file.load_configure_json()
    new_connection = {"action": action, "gesture": gesture, "sound": sound}
    current_config.append(new_connection)
    file.save_configure_json(current_config)
    return new_connection

# Register the "Add Connection" tool so the App sees it
register_command(ApiCommand(
    name="Add Connection",
    endpoint="/connect", # The App will POST to this url
    description="Link a gesture to an action"
))