"""
Backward compatibility tests for the consumer contract. No network.

Each case simulates a change gorest (the provider) might ship, applied to a
known-good payload, and asserts whether OUR contract should still accept it.
If one of these starts behaving differently, the contract itself changed.
"""

import copy

import pytest

from framework.contract.user_contract import UserContract
from framework.validators.response_validator import ResponseValidator

# A known-good gorest user, the "before" state of the provider
BASELINE_USER = {
    "id": 8640717,
    "name": "Asha Rao",
    "email": "asha.rao@example.com",
    "gender": "female",
    "status": "active",
}


def add_field(payload):
    payload["phone"] = "555-1234"


def remove_email(payload):
    del payload["email"]


def id_to_non_numeric_string(payload):
    payload["id"] = "usr_8640717"


def id_to_numeric_string(payload):
    payload["id"] = "8640717"


def status_new_enum_value(payload):
    payload["status"] = "suspended"


def name_to_null(payload):
    payload["name"] = None


# (provider change, should the contract still pass?)
CASES = [
    # Additive change: extra="ignore" (tolerant reader) means we don't care
    pytest.param(add_field, True, id="new_field_added"),
    # Removing a field we depend on is always breaking
    pytest.param(remove_email, False, id="required_field_removed"),
    # Type change int -> non-numeric string: breaking
    pytest.param(id_to_non_numeric_string, False, id="id_type_changed"),
    # Gotcha: Pydantic's default "lax" mode coerces "8640717" -> 8640717,
    # so this type change slips through. Use StrictInt on id if that matters.
    pytest.param(id_to_numeric_string, True, id="id_numeric_string_coerced"),
    # Enum EXPANSION breaks a strict Literal consumer, even though the
    # provider would call it an additive change. Classic interview point.
    pytest.param(status_new_enum_value, False, id="status_enum_expanded"),
    # Required field now nullable: breaking for a non-Optional field
    pytest.param(name_to_null, False, id="required_field_nullable"),
]


@pytest.mark.contract
def test_baseline_payload_honors_contract():
    # Sanity check: if this fails, every case below is meaningless
    ResponseValidator.validate_contract(BASELINE_USER, UserContract)


@pytest.mark.contract
@pytest.mark.parametrize("provider_change, should_pass", CASES)
def test_backward_compatibility(provider_change, should_pass):
    # deepcopy so one case's mutation never leaks into another
    payload = copy.deepcopy(BASELINE_USER)
    provider_change(payload)

    if should_pass:
        ResponseValidator.validate_contract(payload, UserContract)
    else:
        with pytest.raises(AssertionError, match="Contract violation"):
            ResponseValidator.validate_contract(payload, UserContract)