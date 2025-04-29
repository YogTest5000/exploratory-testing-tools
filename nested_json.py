import json

# Example of a nested JSON
nested_json = '''
{
    "user": {
        "id": 1,
        "name": "Alice",
        "address": {
            "street": "123 Main St",
            "city": "Wonderland",
            "coordinates": {
                "lat": 52.5163,
                "long": 13.3777
            }
        },
        "hobbies": ["reading", "cycling", "traveling"]
    }
}
'''

# Load JSON string into Python dictionary
data = json.loads(nested_json)

# Function to recursively print nested keys and values
def print_nested_json(data, indent=0):
    if isinstance(data, dict):
        for key, value in data.items():
            print('  ' * indent + str(key) + ':')
            print_nested_json(value, indent + 1)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            print('  ' * indent + f"[{index}]:")
            print_nested_json(item, indent + 1)
    else:
        print('  ' * indent + str(data))

# Call the function
print("Printing nested JSON structure:")
print_nested_json(data)

# Example: Accessing nested elements safely
def get_nested_value(d, keys):
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key)
        elif isinstance(d, list) and isinstance(key, int) and key < len(d):
            d = d[key]
        else:
            return None
    return d

# Usage: Access latitude
lat_value = get_nested_value(data, ["user", "address", "coordinates", "lat"])
print("\nLatitude:", lat_value)

# Usage: Access first hobby
first_hobby = get_nested_value(data, ["user", "hobbies", 0])
print("First Hobby:", first_hobby)
