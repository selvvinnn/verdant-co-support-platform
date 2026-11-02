from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic import BaseModel, EmailStr, Field


class CustomerMessageCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    brand_id: str = Field(default="verdant-co")
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=10000)

class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str
    phone: str


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str
    text: str


class WebhookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=255)
    type: Literal["message.received"]
    brand_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    customer: Customer
    message: Message



class AgentRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    invite_code: str