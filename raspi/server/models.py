from pydantic import BaseModel, Field, field_validator


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

    @field_validator('selectedGesture')
    @classmethod
    def supported_wake_name(cls, value):
        from gesture_engine.core.matching import gesture_display_name, SUPPORTED_GESTURES
        name = gesture_display_name(value)
        if name not in SUPPORTED_GESTURES:
            raise ValueError('Unsupported wake gesture')
        return name


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


class ContactCalibration(BaseModel):
    enabled: bool = False
    contactRatio: float = Field(default=0.25, ge=0.02, le=1, allow_inf_nan=False)
    depthRatio: float = Field(default=0.15, ge=0.01, le=1, allow_inf_nan=False)


class EngineSettings(BaseModel):
    captureWidth: int = Field(default=640, ge=160, le=3840)
    captureHeight: int = Field(default=480, ge=120, le=2160)
    captureFps: int = Field(default=30, ge=1, le=120)
    recognitionWidth: int = Field(default=640, ge=160, le=1920)
    previewWidth: int = Field(default=640, ge=160, le=1920)
    previewFps: int = Field(default=15, ge=1, le=60)
    jpegQuality: int = Field(default=80, ge=20, le=95)
    calibration: ContactCalibration = Field(default_factory=ContactCalibration)


class TestMode(BaseModel):
    enabled: bool


class ProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64, pattern=r'^[\w .-]+$')
    operation: str = Field(pattern=r'^(save|load|delete|import)$')
    configurations: list[Configuration] | None = None
