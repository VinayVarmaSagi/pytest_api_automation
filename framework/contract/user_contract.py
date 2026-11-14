"""
Consumer contract for the gorest User resource.

Why this lives separately from models/user.py:
- models/user.py describes the FULL response gorest sends back.
- This contract describes only what OUR tests (the consumer) actually depend on.
  If gorest adds, renames or drops a field we never read, this contract
  should not care. If it changes a field we DO read, this contract must fail.
Keeping the two apart is what lets the provider evolve freely without
breaking us, and tells us exactly what "breaking" means for our side.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserContract(BaseModel):
    # Extra fields: "ignore" (tolerant reader).
    # A provider adding a new field (e.g. "phone") is a backward-compatible
    # change, so it must NOT fail our contract. "forbid" would turn every
    # additive change on gorest's side into a false alarm for us.
    # Trade-off: we won't notice new fields, which is fine because we don't use them.
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    email: str
    gender: Literal["male", "female"]
    status: Literal["active", "inactive"]