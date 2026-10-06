from pydantic import BaseModel, Field


class PairRequest(BaseModel):
    key: str = Field(min_length=1, max_length=256)


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
    token: str | None = None


class HAPairStartRequest(BaseModel):
    handler: str


class HAPairSubmitRequest(BaseModel):
    flow_id: str
    user_input: dict


class GestureSettings(BaseModel):
    wakeEnabled: bool
    holdDurationSeconds: float = Field(ge=0, le=60, allow_inf_nan=False)
    activeWindowSeconds: float = Field(ge=0, le=3600, allow_inf_nan=False)
    selectedGesture: str


class CameraSettings(BaseModel):
    useNetwork: bool = False
    streamUrl: str = ""


class IronmanParams(BaseModel):
    enabled: bool = False
    always_track: bool = False
    gain: int = Field(default=5000, ge=1, le=20000)
    damp: int = Field(default=50, ge=1, le=1000)
    sensitivity: int = Field(default=3, ge=0, le=1000)
    steps: int = Field(default=10, ge=1, le=100)
    delay: float = Field(default=0.001, ge=0, le=0.01, allow_inf_nan=False)
    scroll: int = Field(default=10, ge=1, le=50)
    gesture_map: dict[str, str] = Field(default_factory=dict)


class VoiceSettings(BaseModel):
    enabled: bool = False
    model: str = "tiny"
    language: str = "en"
