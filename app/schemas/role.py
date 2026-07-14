from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class RoleResponse(RoleBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)