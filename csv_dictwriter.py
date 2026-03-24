import csv

# Data to write (list of dictionaries)
data = [
    {"name": "John", "age": 30, "city": "New York"},
    {"name": "Alice", "age": 25, "city": "Los Angeles"},
    {"name": "Bob", "age": 35, "city": "Chicago"}
]

# CSV file name
file_name = "output.csv"

# Field names (CSV headers)
fieldnames = ["name", "age", "city"]

# Write to CSV
with open(file_name, mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()   # Write header row
    writer.writerows(data) # Write multiple rows

print("CSV file written successfully!")
