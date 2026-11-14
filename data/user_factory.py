from data.base_factory import BaseFactory


class UserFactory:
    @staticmethod
    def default_user(**overrides) -> dict:
        payload = {
            "name": BaseFactory.realistic_name(),
            "email": BaseFactory.unique_email(),
            "gender": "male",
            "status": "active"
        }
        payload.update(overrides)#updates and overrides the payload with key and values / values from overrides
        return payload
    """
    def default_user(gender=None,status=None) -> dict:
        return {
            "name": BaseFactory.realistic_name(),
            "email": BaseFactory.unique_email(),
            "gender": gender or "male",
            "status": status or "active"
        }
    """
    """can take input from user any kind and update, user may give any no of args and it gets converted to dict by taking any no of args as kwargs from user
    but this doesnt have suggestions while user entering, also any type error in key would be updated without failure
    if we try with anything other than provided in the signature, ex stauts instead of status - it gives TypeError , its about shape of call being wrong.
    """

"""which error to use
Exception	Fits?
KeyError	❌ means a lookup failed; misleading here
ValueError	✅ conventional: right type, bad contents
TypeError	✅ matches Python’s own unexpected-kwarg behavior
"""