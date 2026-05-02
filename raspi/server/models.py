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
