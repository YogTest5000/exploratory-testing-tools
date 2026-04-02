import pandas as pd

# Read CSV in chunks of 1000 rows
chunk_size = 1000

for chunk in pd.read_csv("large_file.csv", chunksize=chunk_size):
    print(chunk.head())  # process each chunk

# 
import pandas as pd

total = 0

for chunk in pd.read_csv("sales.csv", chunksize=500):
    total += chunk["revenue"].sum()

print("Total Revenue:", total)

# 

import pandas as pd

filtered_data = []

for chunk in pd.read_csv("data.csv", chunksize=1000):
    filtered = chunk[chunk["temperature"] > 30]
    filtered_data.append(filtered)

result = pd.concat(filtered_data)
print(result)

# 

import pandas as pd

output_file = "output.csv"

for i, chunk in enumerate(pd.read_csv("large.csv", chunksize=1000)):
    processed = chunk[chunk["value"] > 50]
    
    if i == 0:
        processed.to_csv(output_file, index=False, mode='w')
    else:
        processed.to_csv(output_file, index=False, mode='a', header=False)

  
