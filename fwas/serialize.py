from datetime import datetime
from typing import Optional
from uuid import UUID

from geoalchemy2.types import Raster
from pydantic import BaseModel, EmailStr

from fwas import models


class Token(BaseModel):
    token: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str


class BlacklistTokenInDb(BaseModel):
    id: int
    token: str


class UserRequest(BaseModel):
    user_id: int


class UserError(BaseModel):
    message: str


class UserIn(BaseModel):
    email: EmailStr
    username: str
    password: str
    phone: str


class UserInDb(BaseModel):
    id: int
    email: str
    username: str
    password: str
    is_active: bool
    phone: Optional[str]
    role: models.Roles
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    phone: Optional[str]
    token: Optional[str] = ""
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    status: str
    message: str
    auth_token: Optional[str]


class LoginParameter(BaseModel):
    email: str
    password: str


class LoginStatusData(BaseModel):
    user_id: str
    email: EmailStr
    admin: bool
    created_at: datetime


class LoginStatusResult(BaseModel):
    status: str
    data: LoginStatusData


class AlertInDb(BaseModel):
    id: int
    uuid: UUID
    user_id: int
    name: str
    latitude: float
    longitude: float
    geom: str
    radius: float
    timezone: str
    expires_at: datetime = None
    temperature_limit: float
    relative_humidity_limit: float
    wind_limit: float
    precipitation_limit: float
    check_thunderstorms: Optional[bool]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AlertCreationSuccess(BaseModel):
    status: str
    message: str
    alert_id: int
    alert_uuid: UUID


class AlertShareSuccess(BaseModel):
    status: str
    message: str


class AlertDetailsParameters(BaseModel):
    since: datetime


class AlertIn(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius: float
    timezone: Optional[str] = None
    expires_at: Optional[datetime] = None

    temperature_limit: Optional[float] = None
    relative_humidity_limit: Optional[float] = None
    wind_limit: Optional[float] = None
    precipitation_limit: Optional[float] = None


class NotificationIn(BaseModel):
    user_id: int
    alert_id: int
    message: str
    sent_at: datetime
    violates_at: datetime
    violated_on: str
    temperature_violated: bool
    temperature_violated_at: datetime
    relative_humidity_violated: bool
    relative_humidity_violated_at: datetime
    wind_violated: bool
    wind_violated_at: datetime
    wind_value: float
    precipiation_violated: bool
    precipiation_violated_at: datetime
    precipiation_value: float


class NotificationInDb(NotificationIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class NotificationOut(NotificationInDb):
    pass


class WeatherRasterInDb(BaseModel):
    id: int
    rast: Raster
    filename: str
    source: str
    forecasted_at: datetime
    forecast_time: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


class Error(BaseModel):
    status: str
    message: str


class InternalError(Error):
    """Represents internal errors (i.e. HTTP 5xx)"""


class RequestError(Error):
    """Represents request errors (i.e. HTTP 4xx)"""


class AlertShareError(Error):
    """Represents errors with subscribing a user to an alert."""
