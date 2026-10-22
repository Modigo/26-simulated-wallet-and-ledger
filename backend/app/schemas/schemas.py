from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
import re
class RegisterIn(BaseModel):
    display_name: str = Field(min_length=2,max_length=100)
    username: str = Field(min_length=3,max_length=40)
    email: str = Field(min_length=5,max_length=255)
    phone: str | None = None
    password: str = Field(min_length=8,max_length=128)
    @field_validator("username")
    @classmethod
    def uname(cls,v):
        v=v.strip().lower()
        if not re.fullmatch(r"[a-z0-9_.-]+",v): raise ValueError("Username may contain letters, numbers, underscore, dot or hyphen")
        return v
    @field_validator("email")
    @classmethod
    def mail(cls,v):
        v=v.strip().lower()
        if "@" not in v or "." not in v.rsplit("@",1)[-1]: raise ValueError("Enter a valid email address")
        return v
    @field_validator("password")
    @classmethod
    def pw(cls,v):
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)): raise ValueError("Password must contain a letter and a number")
        return v
class LoginIn(BaseModel): identifier: str; password: str
class DemoSessionIn(BaseModel): user_id: str
class TransferIn(BaseModel):
    recipient_identifier: str = Field(min_length=1,max_length=255)
    amount: Decimal
    description: str | None = Field(default=None,max_length=200)
    idempotency_key: str = Field(min_length=8,max_length=100)
    @field_validator("amount")
    @classmethod
    def amt(cls,v):
        if v is None or v!=v or v in (Decimal("Infinity"),Decimal("-Infinity")): raise ValueError("Invalid amount")
        if v.as_tuple().exponent < -2: raise ValueError("Amount may have at most 2 decimal places")
        return v
class UserOut(BaseModel):
    id:str; username:str; display_name:str; email:str; phone:str|None=None; is_demo:bool; wallet_id:str|None=None; balance:Decimal|None=None; currency:str="NGN"
