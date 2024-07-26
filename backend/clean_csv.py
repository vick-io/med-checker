import pandas as pd

# Read the CSV file
df = pd.read_csv('medications.csv')

# Convert the names to lowercase to handle case-insensitive duplicates
df['PROPRIETARYNAME'] = df['PROPRIETARYNAME'].str.lower()
df['NONPROPRIETARYNAME'] = df['NONPROPRIETARYNAME'].str.lower()

# Normalize nonproprietary_name by removing unnecessary descriptors
df['NONPROPRIETARYNAME'] = df['NONPROPRIETARYNAME'].str.replace(r'\s*\(.*?\)\s*', '', regex=True)
df['NONPROPRIETARYNAME'] = df['NONPROPRIETARYNAME'].str.replace(r'\s*tablets\s*', '', regex=True)
df['NONPROPRIETARYNAME'] = df['NONPROPRIETARYNAME'].str.replace(r'\s*capsules\s*', '', regex=True)

# Drop duplicate rows based on proprietary_name and nonproprietary_name
df_cleaned = df.drop_duplicates(subset=['PROPRIETARYNAME', 'NONPROPRIETARYNAME'])

# Save the cleaned CSV file
df_cleaned.to_csv('medications_cleaned.csv', index=False)

print(f"Original rows: {len(df)}, Cleaned rows: {len(df_cleaned)}")
