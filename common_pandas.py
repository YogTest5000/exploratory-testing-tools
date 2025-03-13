import pandas as pd

#View
df.head()      # First 5 rows
df.tail()      # Last 5 rows
df.info()      # Summary of DataFrame
df.describe()  # Statistics of numerical columns
df.shape       # Number of rows and columns
df.columns     # List of column names
df.dtypes      # Data types of each column

#Selecting and Filtering Data
df['Name']         # Select a single column
df[['Name', 'Age']] # Select multiple columns
df.iloc[0]          # Select first row (by index)
df.loc[0, 'Name']   # Select specific cell
df[df['Age'] > 30]  # Filter rows where Age > 30
df.query("Age > 30") # Another way to filter

#Adding a new column
df['Salary'] = [50000, 60000, 70000]
Updating values
df.loc[df['Name'] == 'Alice', 'Age'] = 26
Dropping a column
df.drop(columns=['Salary'], inplace=True)

#Sorting Data
df.sort_values(by='Age', ascending=False)

#Grouping & Aggregation
df.groupby('Age').size()               # Count rows per Age
df.groupby('Age')['Salary'].sum()      # Sum Salary per Age
df.groupby('Age').agg({'Salary': 'mean', 'Age': 'count'})

#Handling Missing Data
df.isnull().sum()   # Count missing values
df.dropna()         # Drop rows with missing values
df.fillna(0)        # Fill missing values with 0

#Concatenation
df2 = pd.DataFrame({'Name': ['David'], 'Age': [40]})
df = pd.concat([df, df2], ignore_index=True)

#Merging on a key
df1.merge(df2, on='Name', how='left')

#Exporting Data
df.to_csv('output.csv', index=False)
df.to_excel('output.xlsx', index=False)
df.to_json('output.json')
