from server import file


def add_connection(action: str, gesture: str, sound: str) -> dict:
    new_connection = {
        "action": action,
        "gesture": gesture,
        "sound": sound,
    }
    file.loaded_config.append(new_connection)
    file.save_configure_json(file.loaded_config)
    return {"status": "added", "connection": new_connection}
