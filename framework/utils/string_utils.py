import string
import random
import re

def is_empty(value):#has length zero
    return value is None or value == ''
    #value variable never assigned a value or if value is str - its empty string returns true else false

def is_blank(value):#contains only white space char
    # Safety Check: If it is a number or boolean, it has data and isn't a blank string
    if isinstance(value, (int, float, bool)):
        return False
    # Returns True if value is None or if stripping all whitespace leaves an empty string
    return value is None or str(value).strip() == ''

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
    #return randstring

def generate_random_email():
    allowed_chars = string.ascii_lowercase+string.digits#includes both alphabets and digits
    userid = ''.join(random.choice(allowed_chars) for _ in range(10))
    return userid+'@'+'company.com'

def mask_sensitive_data(value, visible_chars=4):
    value=str(value)#if input is given in integer
    if len(value)<=visible_chars:#mask everything if we get visible chars greater than or equal to total chars
        return ('*' * len(value))
        #if len(value)>visible_chars:
        #1234567890 to ******7890
    hidden_chars_len = len(value)-visible_chars
    actual_visible_chars=value[hidden_chars_len:]#covers from hidden_Chars_len till end
    return (hidden_chars_len * '*' + actual_visible_chars)

def normalize_whitespace(value):
    return " ".join(value.split())#splits into list and concatenates again with " " in between
    #if no arguments in split - it splits based on white space by default

def remove_special_characters(value):
    #return re.sub(r'[^0-9a-zA-Z ]','',value)#space also we dont want to remove from actual word
    return ''.join(char for char in value if char.isalnum() or char==' ')

"""def to_snake_case(value):
    # Replace dashes and spaces with a single space first
    value = value.replace('-', ' ')
    result = []
    for char in value:
        # If it's capital and not the very first letter, add an underscore
        if char.isupper() and result:
          result.append('_')
          result.append(char)

        # Join everything, remove spaces, and convert to lowercase
        return "".join(result).replace(' ', '').lower()"""

print(is_empty(None))
print(is_empty(''))
print(is_empty('abc'))
print(generate_random_string(10))
print(generate_random_email())
print(mask_sensitive_data('1234567890'))
print(normalize_whitespace("Helloooo   world"))
print(remove_special_characters("Helloo$3%^& world"))
#print(to_snake_case("Hellooo world prog"))

#util file for reusability, maintainability, consistency and separation of concerns