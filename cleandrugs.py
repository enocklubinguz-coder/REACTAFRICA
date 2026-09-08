import os
import numpy as np
import pandas as pd

# 1. Define File Paths
input_path = r'C:\Users\LUBINGU\PycharmProjects\LWANSASE\rdata\ANTIBIOTICS.csv'
output_dir = r'C:\Users\LUBINGU\PycharmProjects\LWANSASE\cdata'
output_path = os.path.join(output_dir, 'ANTIBIOTICS_UNPIVOTED_CLEANED.csv')

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# 2. Load the dataset
df = pd.read_csv(input_path)

# 3. Merge 'Other Specify' fields into their respective Antibiotic columns
for i in range(1, 6):
    ab_col = f'rdt_Antibiotic{i}'
    other_col = f'RDTOtherSpecify{i}'

    df[ab_col] = np.where(
        (df[ab_col].str.lower() == 'other') & (df[other_col].notna()),
        df[other_col],
        df[ab_col],
    )
    df.drop(columns=[other_col], inplace=True)

# 4. Parse Dates & Calculate Patient Age
dob = pd.to_datetime(df['rdt_PatientAge'], errors='coerce')
adm_date = pd.to_datetime(df['rdt_DateOfAdmission'], errors='coerce')
report_date = pd.to_datetime(df['Event date'], errors='coerce')

# Fallback: Use admission date first; if missing, use report date
ref_date = adm_date.fillna(report_date)

# Exact age calculation in full years
df['AGE'] = (ref_date.dt.year - dob.dt.year) - (
    (ref_date.dt.month < dob.dt.month)
    | ((ref_date.dt.month == dob.dt.month) & (ref_date.dt.day < dob.dt.day))
)

# 5. Rename Base Fields
base_rename = {
    'Organisation unit name': 'FACILITY',
    'rdt_DataStage': 'DATA STAGE',
    'Event date': 'REPORT DATE',
    'rdt_FileNumber': 'FILE NUMBER',
    'rdt_PatientGender': 'PATIENT GENDER',
    'rdt_PatientAge': 'DATE OF BIRTH',
    'rdt_DateOfAdmission': 'DATE OF ADMISSION',
    'rdt_WasPatientOnAntibiotics': 'WAS PATIENT ON ANTIBIOTICS',
    'rdt_NumberOfAntibiotics': 'NUMBER OF ANTIBIOTICS',
}
df.rename(columns=base_rename, inplace=True)

# 6. Column Order with AGE next to DATE OF BIRTH
patient_cols = [
    'FACILITY',
    'DATA STAGE',
    'REPORT DATE',
    'FILE NUMBER',
    'PATIENT GENDER',
    'DATE OF BIRTH',
    'AGE',
    'DATE OF ADMISSION',
    'WAS PATIENT ON ANTIBIOTICS',
    'NUMBER OF ANTIBIOTICS',
]

# 7. Unpivot (Reshape) the 5 Wide Antibiotic Sets into Long Format
antibiotic_sets = {
    1: (
        'rdt_Antibiotic1',
        'RDTDuration1',
        'rdt_DeescalationChangeOfTreatmentDone',
        'rdt_TreatmentType',
    ),
    2: (
        'rdt_Antibiotic2',
        'RDTDuration2',
        'rdt_DeescalationChangeOfTreatmentDone1',
        'rdt_TreatmentType1',
    ),
    3: (
        'rdt_Antibiotic3',
        'RDTDuration3',
        'rdt_DeescalationChangeOfTreatmentDone2',
        'rdt_TreatmentType2',
    ),
    4: (
        'rdt_Antibiotic4',
        'RDTDuration4',
        'rdt_DeescalationChangeOfTreatmentDone3',
        'rdt_TreatmentType3',
    ),
    5: (
        'rdt_Antibiotic5',
        'RDTDuration5',
        'rdt_DeescalationChangeOfTreatmentDone4',
        'rdt_TreatmentType4',
    ),
}

long_dfs = []
for seq, (ab, dur, deesc, trt) in antibiotic_sets.items():
    sub_df = df[patient_cols].copy()
    sub_df['ANTIBIOTIC SEQUENCE'] = seq
    sub_df['ANTIBIOTIC'] = df[ab]
    sub_df['DURATION'] = df[dur]
    sub_df['DEESCALATION CHANGE OF TREATMENT DONE'] = df[deesc]
    sub_df['TREATMENT TYPE'] = df[trt]
    long_dfs.append(sub_df)

# Combine all rows into one final dataset
df_final = pd.concat(long_dfs, ignore_index=True)

# Remove rows where no antibiotic was given for that slot
df_final_clean = df_final[df_final['ANTIBIOTIC'].notna()].copy()

# 8. Export Cleaned File to Target Directory
df_final_clean.to_csv(output_path, index=False)
print(f'Successfully processed and saved file to: {output_path}')