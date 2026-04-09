def parse_action_to_service(action: str) -> str:
    """Convert Sensee UI actions into Home Assistant service names."""
    action_lower = action.lower().strip()
    if "turn on" in action_lower:
        return "turn_on"
    if "turn off" in action_lower:
        return "turn_off"
    if "increase volume" in action_lower or "volume up" in action_lower:
        return "volume_up"
    if "decrease volume" in action_lower or "volume down" in action_lower:
        return "volume_down"
    if "toggle" in action_lower:
        return "toggle"
    return "turn_on"


def get_domain_from_entity(entity_id: str) -> str:
    """Extract domain (for example, 'light' from 'light.bedroom')."""
    if "." in entity_id:
        return entity_id.split(".")[0]
    return "homeassistant"