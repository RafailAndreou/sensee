"""Home Assistant service and domain mapping helpers."""

from __future__ import annotations


def parse_action_to_service(action: str) -> str:
    """Map a Sensee action label to a Home Assistant service name."""
    service = {
        'turn on':'turn_on', 'turn off':'turn_off', 'toggle':'toggle',
        'increase volume':'volume_up', 'volume up':'volume_up',
        'decrease volume':'volume_down', 'volume down':'volume_down',
    }.get(action.lower().strip())
    if service is None:
        raise ValueError(f'Unsupported Home Assistant action: {action}')
    return service


def get_domain_from_entity(entity_id: str) -> str:
    """Return the Home Assistant domain for an entity id."""
    if "." in entity_id:
        return entity_id.split(".")[0]
    return "homeassistant"


def action_service_data(entity_id, action):
    """Validate the domain and parse bounded numeric action parameters."""
    import math
    import re
    domain = get_domain_from_entity(entity_id)
    label = action.lower().strip()
    data = {'entity_id': entity_id}
    numeric = re.fullmatch(r'(brightness|fan speed|temperature)\s+(-?\d+(?:\.\d+)?)', label)
    if numeric:
        kind, raw = numeric.groups()
        value = float(raw)
        expected, service, field, low, high = {
            'brightness': ('light', 'turn_on', 'brightness_pct', 0, 100),
            'fan speed': ('fan', 'set_percentage', 'percentage', 0, 100),
            'temperature': ('climate', 'set_temperature', 'temperature', -50, 120),
        }[kind]
        if domain != expected or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'Invalid {kind} for {domain}')
        data[field] = value
        return domain, service, data
    if label == 'activate' and domain in ('scene', 'script'):
        return domain, 'turn_on', data
    service = parse_action_to_service(action)
    allowed = {
        'media_player': {'turn_on', 'turn_off', 'toggle', 'volume_up', 'volume_down'},
        'light': {'turn_on', 'turn_off', 'toggle'}, 'switch': {'turn_on', 'turn_off', 'toggle'},
        'fan': {'turn_on', 'turn_off', 'toggle'}, 'climate': {'turn_on', 'turn_off'},
        'scene': {'turn_on'}, 'script': {'turn_on', 'turn_off'},
    }
    if service not in allowed.get(domain, set()):
        raise ValueError(f'Action {action} is unsupported for domain {domain}')
    return domain, service, data


def available_actions(domain, attributes=None):
    attrs = attributes or {}
    actions = {
        'media_player': ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
        'light': ['Turn on', 'Turn off', 'Toggle'], 'switch': ['Turn on', 'Turn off', 'Toggle'],
        'fan': ['Turn on', 'Turn off'], 'climate': ['Turn on', 'Turn off'],
        'scene': ['Activate'], 'script': ['Activate'],
    }.get(domain, [])[:]
    features = int(attrs.get('supported_features', 0))
    if domain == 'light' and any(m != 'onoff' for m in attrs.get('supported_color_modes', [])):
        actions += ['Brightness 25', 'Brightness 50', 'Brightness 100']
    if domain == 'fan' and features & 1:
        actions += ['Fan speed 25', 'Fan speed 50', 'Fan speed 100']
    if domain == 'climate' and features & 1:
        low, high = attrs.get('min_temp', 7), attrs.get('max_temp', 35)
        presets = (64, 68, 72, 76) if low > 35 or attrs.get('temperature_unit') == '°F' else (18, 20, 22, 24)
        temperatures = [n for n in presets if low <= n <= high]
        if not temperatures and low <= high:
            temperatures = [round((low+high)/2, 1)]
        actions += [f'Temperature {n}' for n in temperatures]
    return actions
