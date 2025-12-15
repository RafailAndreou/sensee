

from raspi.server import file


def add_connection(String action,String gesture,String sound):
    new_connection={
        "actions":actions,
        "gestures":gestures,
        "sound":sound
        ]
    file.loaded_config.append(new_connection)
    file.save_configure_json(file.loaded_config)
    return {"status": "added", "connection": new_connection}

    

    

    