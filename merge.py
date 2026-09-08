import os
import pandas as pd

# 1. Define Updated File Paths
input_dir = r'C:\Users\LUBINGU\PycharmProjects\LWANSASE\rdata\merge'
output_dir = r'C:\Users\LUBINGU\PycharmProjects\LWANSASE\cdata'

csv_path = os.path.join(input_dir, 'ANTIBIOTICS_UNPIVOTED_CLEANED.csv')
excel_path = os.path.join(input_dir, 'GROUPED DIAGNOSIS.xlsx')

os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'ANTIBIOTICS_WITH_DIAGNOSIS.csv')

print(f'Loading CSV from: {csv_path}')
print(f'Loading Excel from: {excel_path}')

# 2. Load Datasets
df_antibiotics = pd.read_csv(csv_path)
df_diagnosis = pd.read_excel(excel_path)

# 3. Normalize FILE NUMBER to string/text to prevent key type mismatches
df_antibiotics['FILE NUMBER'] = (
    df_antibiotics['FILE NUMBER'].astype(str).str.strip()
)
df_diagnosis['FILE NUMBER'] = (
    df_diagnosis['FILE NUMBER'].astype(str).str.strip()
)

# 4. Deduplicate Diagnosis Entries on FILE NUMBER
diagnosis_cols = [
    'FILE NUMBER',
    'DEFINITIVE DIAGNOSIS',
    'WORKING DIAGNOSIS',
    'DIAGNOSIS',
]
avail_cols = [c for c in diagnosis_cols if c in df_diagnosis.columns]
df_diagnosis_unique = df_diagnosis[avail_cols].drop_duplicates(
    subset=['FILE NUMBER']
)

# 5. Merge Datasets on FILE NUMBER
df_merged = pd.merge(
    df_antibiotics, df_diagnosis_unique, on='FILE NUMBER', how='left'
)

# 6. Export Merged Dataset
try:
  df_merged.to_csv(output_path, index=False)
  print(f'Successfully merged and saved file to: {output_path}')
except PermissionError:
  alt_output = os.path.join(output_dir, 'ANTIBIOTICS_WITH_DIAGNOSIS_NEW.csv')
  df_merged.to_csv(alt_output, index=False)
  print(
      f'[WARNING] File locked by another process. Saved fallback to:'
      f' {alt_output}'
  )

print(f'Total Rows: {len(df_merged)}')
print(f'Total Columns: {len(df_merged.columns)}')