from typing import Literal  # Python 3.9: Literal comes from typing
from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):  # Inheritance: BaseModel gives us parsing + validation for free
    # Response model for gorest /users - only response-body validation relies on this class.
    # Status code / header checks stay in ResponseValidator.

    # strict=True  -> no type coercion: "123" for id FAILS instead of silently becoming 123
    # extra="forbid" -> any field gorest adds that we don't know about FAILS (catches contract drift)
    model_config = ConfigDict(strict=True, extra="forbid")

    id: int
    name: str
    email: EmailStr                              # format-checked, not just "any string"
    gender: Literal["male", "female"]            # only gorest's allowed values
    status: Literal["active", "inactive"]