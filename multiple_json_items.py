import os
import json

def read_json_files(folder_path, keys_to_extract):
    results = []

    # Iterate through all files in folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)

            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)

                    # Extract required keys
                    extracted_data = {}
                    for key in keys_to_extract:
                        extracted_data[key] = data.get(key, None)

                    # Add filename for reference
                    extracted_data["file_name"] = file_name

                    results.append(extracted_data)

            except Exception as e:
                print(f"Error reading {file_name}: {e}")

    return results

# USAGE
if __name__ == "__main__":
    # folder_path = "path/to/your/json/folder"
    folder_path = r''

    # Keys you want to extract
    keys = ["deviceId", "temperature", "status"]

    output = read_json_files(folder_path, keys)

    # Print results
    for item in output:
        print(item)
