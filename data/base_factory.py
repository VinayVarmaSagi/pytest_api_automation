import uuid
from framework.utils.string_utils import generate_random_email,generate_random_string
from faker import Faker

fake=Faker()


class BaseFactory:
    @staticmethod
    def unique_suffix():
        # uuid4() = random 128-bit ID → .hex gives it as 32 hex chars (no dashes)
        # [:8] keeps first 8 chars = 32 bits ≈ 4.3 billion values
        # safe for test-suite volumes; collision odds grow with count (birthday problem),
        # so use [:12] or the full .hex if generating 10k+ IDs per run
        return uuid.uuid4().hex[:8]

    @staticmethod
    def unique_email():#using this instead of generate email method created by me to avoid collision during parallel runs. this has more options than the other
        base_email = generate_random_email()          # "abc123xyz9@company.com"
        userid, domain = base_email.split('@')
        return f"{userid}_{BaseFactory.unique_suffix()}@{domain}"
        #we can use similarly fake.email() also but we want to try different approach above


    @staticmethod
    def realistic_name():
        return fake.name()

#Why static
#use a static method when the method needs nothing but its inputs. Use an instance when the object has to hold onto something between calls.
#Making instances would add nothing: UserFactory().default_user() does exactly what UserFactory.default_user() does, plus an object you throw away. That’s also why static is safe for parallel runs. With no shared mutable state, two workers can’t step on each other.
#why instance for AuthManager - 1)It holds state. The token is read once and reused, so you don’t re-read .env on every request. 2)You need more than one. Negative tests want different auth contexts side by side: valid = AuthManager() , invalid = AuthManager(token="bad_token")   # → expect 401

#why class instead of plain methods - both serve same purpose
#the class here is just acting as a namespace. Plain module-level functions (user_factory.default_user()) would work the same. The class mainly earns its keep through grouping and readability, and through consistency with other components.

##fake - It runs and caches when the module(data/base_factory.py) is imported, Every time later from data.base_factory import BaseFactory, in any test file, reuses that cached module.
#fake=Faker() is state. You’ve kept it at module level, so the methods can stay static
#Python then caches the module in sys.modules. Every later from data.base_factory import BaseFactory, in any test file, reuses that cached module. The file doesn’t run again, so fake is created once per pytest process.
#With pytest-xdist, each worker is a separate process, so each worker imports the module and gets its own fake.
#To guarantee no repeats, fake.unique keeps a list of names it has already handed out. That list lives inside the fake object.“Something has to hold that object”
#Because fake remembers things, you want one of it living somewhere, not a new one on every call. fake=Faker() has state and it remembers the state what it shared earlier, hence it doesnt give same name again
#during parallel runs - each faker instance/object gets its own fake and they may generate same fake names since the objects are different and dont know which name each of the faker object generated. but since we used uuid, it gives randomness and doesnt collide with each other durnig parallel runs
#fake gives repeated names as well, we are using this for realistic names. the reason we are using fake instance at once is loading this everytime is time consuming process. it doesnt remember what name it provided earlier. for that we have to use fake.unique() which is not needed here.

#uuid above method
#bit - 0 or 1, 128 bits is 2^128 possible values
#32hex chars - 16 symbols ie 0-9 and a-f. one hex char holds exactly 4 bits, because 2^2=16
#128 bits / 4 bits per char = 32 hex chars, Hex is compact way to write same 128 bit number
#import uuid
#u = uuid.uuid4()
#str(u)      # '3f2a9c1e-7b4d-4e8a-9f12-6c0d5e7a8b3f'   ← 36 chars: 32 hex + 4 dashes (8-4-4-4-12)
#u.hex       # '3f2a9c1e7b4d4e8a9f126c0d5e7a8b3f'       ← 32 chars, no dashes
#u.hex[:8]   # '3f2a9c1e'                               ← first 8 chars

#later read method types - static method(above example), class method, instance method(where object holds state)

#A seed only picks which random sequence you get
#Same seed on every worker:
#gw0: Faker.seed(42) → "Allison Hill", "Noah Rhodes", "Angie Henderson"...
#gw1: Faker.seed(42) → "Allison Hill", "Noah Rhodes", "Angie Henderson"...   ← exact mirror
#Every worker produces the same data in the same order, so duplicates across workers are guaranteed.
#Different seed per worker:
#gw0: Faker.seed(1000) → "Allison Hill", ...
#gw1: Faker.seed(1001) → "Mark Davis", ...
#The workers no longer mirror each other. But repeats can still happen by chance, because fake.name() never avoids repeats.
#So per-worker seeding only avoids the guaranteed mirroring that a shared seed would cause. Uniqueness still comes from your UUID.