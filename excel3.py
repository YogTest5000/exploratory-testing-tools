def eq(values):
    # Step 1: Check if sum is zero
    if sum(values) == 0:
        return 0

    # Step 2: Filter out zeros
    non_zero_values = [v for v in values if v != 0]

    # Step 3: Return smallest non-zero value
    return min(non_zero_values) if non_zero_values else 0


# Example usage (equivalent to H6:H8)
data = [5, 0, 3]
result = eq(data)
print(result)

# second
result = min([v for v in data if v != 0], default=0) if sum(data) != 0 else 0

# third
import pandas as pd
values = pd.read_excel("file.xlsx")["H6":"H8"].values.flatten()
result = excel_equivalent(values)
