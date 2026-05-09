from pydantic import BaseModel


class Configuration(BaseModel):
    id: str
    connectionType: str = "ir"
    entityId: str = ""
    brand: str
    action: str
    gesture: str
    sound: str
    hand: str


class HAConfigRequest(BaseModel):
    url: str
    token: str


class HAPairStartRequest(BaseModel):
    handler: str


class HAPairSubmitRequest(BaseModel):
    flow_id: str
    user_input: dict


class GestureSettings(BaseModel):
    wakeEnabled: bool
    holdDurationSeconds: float
    activeWindowSeconds: float
    selectedGesture: str


class CameraSettings(BaseModel):
    useNetwork: bool = False
    streamUrl: str = ""


class IronmanParams(BaseModel):
    enabled: bool = False
    gain: int = 5000
    damp: int = 50
    sensitivity: int = 3
    steps: int = 10
    delay: float = 0.001
    scroll: int = 10
    gesture_map: dict = {}


class VoiceSettings(BaseModel):
    enabled: bool = False
    model: str = "tiny"
    language: str = "en"
