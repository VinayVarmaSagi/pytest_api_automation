import json
import re

data = {
    "name": "Vinay",
    "age": 32
}
print(type(data))

json_string = '{"name": "Vinay", "age": 32}'
print(type(json_string))

response = {
    "users": [
        {"id": 101, "name": "John"},
        {"id": 102, "name": "Mike"}
    ]
}

actual_response = {
    "id": 123,
    "name": "John",
    "status": "ACTIVE",
    "role": "ADMIN"
}

expected_response= {
    "name": "John",
    "status": "ACTIVE"
}


#JSON Serialization
def object_to_json(data):
    json_response=json.dumps(data,indent=4)
    print('type is', type(json_response))#json will be in str data type
    return json_response

#JSON Deserialization
def json_to_object(json_string):
    object_response=json.loads(json_string)
    print('type is', type(object_response))
    return object_response

#Get Nested Value
def get_nested_value(data, path):
    current=data
    keys=path.split(".")#splits into users[1] and name list
    try :
        for key in keys:#iterating through list which
            key_match=re.match(r'(\w+)\[(\d+)\]',key)#comparing if the element has this pattern
            #() to group as we want to use them below later
            #\w+ one or more alpha numeric chars and underscore included
            #\d+ one or more digits
            if key_match:#if matches above pattern group(0) takes entire value ie users[1]
                current_key=key_match.group(1)#takes value users
                current_value=int(key_match.group(2))#takes value 1
                current=current[current_key][current_value]#users[1]= current now
            else:
                current=current[key]#if doesnt match users[1] patter, current simply is users, and in next iteration its name
    except (KeyError,IndexError,TypeError):
        #KeyError - if asked for users.age , age key doesnt exist
        #IndexError - if asked for users[100], 100 index doesnt exist
        #TypeError - if asked for users[1].name.age, name is string, string doesnt have anything of age
        #if these errors are thrown - it returns None and goes out of this condition , it doesnt fail
        #later during assertion if these doesnt match with expected, then it will fail
        return None#returns None
    return current  # return final value at the end

def compare_two_json(actual, expected):
    if actual is None or expected is None:
        return  False

    for key,value in expected.items():
        if key not in actual:
            return False
        if actual[key]!=value:
            return False

    return True


print(object_to_json(data))
print(json_to_object(json_string))
print(get_nested_value(response,"users[11].name"))
print(get_nested_value(response,"users[1].name"))
print(compare_two_json(actual_response,expected_response))