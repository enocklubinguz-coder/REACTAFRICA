import os
import numpy as np
import pandas as pd

# 1. Define File Paths
input_path = r'C:\Users\LUBINGU\PycharmProjects\LWANSASE\rdata\DRUGSALL.csv'
output_dir = r'C:\Users\LUBINGU\PycharmProjects\LWANSASE\cdata'
output_path = os.path.join(output_dir, 'ANTIBIOTICS_UNPIVOTED_CLEANED.csv')

os.makedirs(output_dir, exist_ok=True)

# 2. Load the dataset
df = pd.read_csv(input_path)

# 3. Combine Antibiotic & Culture 'Other' fields
for i in range(1, 6):
    # Antibiotics
    ab_col, ab_other = f'rdt_Antibiotic{i}', f'RDTOtherSpecify{i}'
    if ab_col in df.columns and ab_other in df.columns:
        df[ab_col] = np.where(
            (df[ab_col].astype(str).str.lower() == 'other')
            & (df[ab_other].notna()),
            df[ab_other],
            df[ab_col],
        )
        df.drop(columns=[ab_other], inplace=True)

    # Culture Samples
    s_col, s_other = f'rdt_Sample{i}', f'rdt_Sample{i}OtherSpecify'
    if s_col in df.columns and s_other in df.columns:
        df[s_col] = np.where(
            (df[s_col].astype(str).str.lower() == 'other')
            & (df[s_other].notna()),
            df[s_other],
            df[s_col],
        )
        df.drop(columns=[s_other], inplace=True)

# 4. Parse Dates & Calculate Patient Age
dob = pd.to_datetime(df['rdt_PatientAge'], errors='coerce')
adm_date = pd.to_datetime(df['rdt_DateOfAdmission'], errors='coerce')
report_date = pd.to_datetime(df['Event date'], errors='coerce')

ref_date = adm_date.fillna(report_date)

df['AGE'] = (ref_date.dt.year - dob.dt.year) - (
    (ref_date.dt.month < dob.dt.month)
    | ((ref_date.dt.month == dob.dt.month) & (ref_date.dt.day < dob.dt.day))
)

# Standardize binary culture flag (1/0 -> Yes/No)
if 'rdt_CultureSampleTaken' in df.columns:
    df['rdt_CultureSampleTaken'] = df['rdt_CultureSampleTaken'].replace(
        {1: 'Yes', 0: 'No'}
    )

# 5. Rename Base & Diagnostic Fields
base_rename = {
    'Organisation unit name': 'FACILITY',
    'rdt_DataStage': 'DATA STAGE',
    'Event date': 'REPORT DATE',
    'rdt_FileNumber': 'FILE NUMBER',
    'rdt_PatientGender': 'PATIENT GENDER',
    'rdt_PatientAge': 'DATE OF BIRTH',
    'rdt_DateOfAdmission': 'DATE OF ADMISSION',
    'rdt_PatientHasMalaria': 'PATIENT HAS MALARIA',
    'rdt_ThePatientHasTuberculosis?': 'PATIENT HAS TUBERCULOSIS',
    'rdt_PatientHIVStatusKnown': 'PATIENT HIV STATUS KNOWN',
    'rdt_PatientHIVstatus': 'PATIENT HIV STATUS',
    'rdt_CultureSampleTaken': 'CULTURE SAMPLE TAKEN',
    'rdt_HowManyCultureSamples': 'NUMBER OF CULTURE SAMPLES',
    'rdt_WasPatientOnAntibiotics': 'WAS PATIENT ON ANTIBIOTICS',
    'rdt_NumberOfAntibiotics': 'NUMBER OF ANTIBIOTICS',
}
df.rename(columns=base_rename, inplace=True)

# 6. Unpivot 5 Sequence Sets with Culture Fields Arranged Consecutively
ab_sets = {
    1: (
        'rdt_Antibiotic1',
        'RDTDuration1',
        'rdt_DeescalationChangeOfTreatmentDone',
        'rdt_TreatmentType',
        'rdt_Sample1',
    ),
    2: (
        'rdt_Antibiotic2',
        'RDTDuration2',
        'rdt_DeescalationChangeOfTreatmentDone1',
        'rdt_TreatmentType1',
        'rdt_Sample2',
    ),
    3: (
        'rdt_Antibiotic3',
        'RDTDuration3',
        'rdt_DeescalationChangeOfTreatmentDone2',
        'rdt_TreatmentType2',
        'rdt_Sample3',
    ),
    4: (
        'rdt_Antibiotic4',
        'RDTDuration4',
        'rdt_DeescalationChangeOfTreatmentDone3',
        'rdt_TreatmentType3',
        'rdt_Sample4',
    ),
    5: (
        'rdt_Antibiotic5',
        'RDTDuration5',
        'rdt_DeescalationChangeOfTreatmentDone4',
        'rdt_TreatmentType4',
        'rdt_Sample5',
    ),
}

long_dfs = []
for seq, (ab, dur, deesc, trt, sample) in ab_sets.items():
    sub_df = pd.DataFrame()

    # Patient Identification & Demographics
    sub_df['FACILITY'] = df['FACILITY']
    sub_df['DATA STAGE'] = df['DATA STAGE']
    sub_df['REPORT DATE'] = df['REPORT DATE']
    sub_df['FILE NUMBER'] = df['FILE NUMBER']
    sub_df['PATIENT GENDER'] = df['PATIENT GENDER']
    sub_df['DATE OF BIRTH'] = df['DATE OF BIRTH']
    sub_df['AGE'] = df['AGE']
    sub_df['DATE OF ADMISSION'] = df['DATE OF ADMISSION']

    # Diagnostics (Malaria, TB, HIV)
    sub_df['PATIENT HAS MALARIA'] = df['PATIENT HAS MALARIA']
    sub_df['PATIENT HAS TUBERCULOSIS'] = df['PATIENT HAS TUBERCULOSIS']
    sub_df['PATIENT HIV STATUS KNOWN'] = df['PATIENT HIV STATUS KNOWN']
    sub_df['PATIENT HIV STATUS'] = df['PATIENT HIV STATUS']

    # Consecutive Culture Sample Fields
    sub_df['CULTURE SAMPLE TAKEN'] = df['CULTURE SAMPLE TAKEN']
    sub_df['NUMBER OF CULTURE SAMPLES'] = df['NUMBER OF CULTURE SAMPLES']
    sub_df['CULTURE SAMPLE'] = df[sample]

    # Antibiotic Prescriptions
    sub_df['WAS PATIENT ON ANTIBIOTICS'] = df['WAS PATIENT ON ANTIBIOTICS']
    sub_df['NUMBER OF ANTIBIOTICS'] = df['NUMBER OF ANTIBIOTICS']
    sub_df['SEQUENCE NUMBER'] = seq
    sub_df['ANTIBIOTIC'] = df[ab]
    sub_df['DURATION'] = df[dur]
    sub_df['DEESCALATION CHANGE OF TREATMENT DONE'] = df[deesc]
    sub_df['TREATMENT TYPE'] = df[trt]

    long_dfs.append(sub_df)

df_final = pd.concat(long_dfs, ignore_index=True)

# Filter out empty sequence rows
df_final_clean = df_final[
    df_final['ANTIBIOTIC'].notna() | df_final['CULTURE SAMPLE'].notna()
].copy()

# 7. Save Cleaned Output
df_final_clean.to_csv(output_path, index=False)
print(f'Successfully processed and saved file to: {output_path}')
print(f'Total exported rows: {len(df_final_clean)}')
print(f'Total exported columns: {len(df_final_clean.columns)}')