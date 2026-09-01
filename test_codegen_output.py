"""
Test del código generado por BNX codegen (target=python/pandas)
Simula exactamente lo que genera _generate_pandas()
"""
import pandas as pd
import os

print("[*] BNX Python Job Started")

# [+] SOURCE: Input_File
Input_File_df = pd.read_csv("data/input_file.csv")
print(f"[>] SOURCE Input_File: {len(Input_File_df)} rows")

# [-] FILTER: Filter_by_Expression
Input_File_df = Input_File_df.reset_index(drop=True)
Input_File_df["_seq"] = Input_File_df.index + 1
Filter_by_Expression_df = Input_File_df.query("_seq > 1").drop(columns=["_seq"])
print(f"[~] FILTER Filter_by_Expression: {len(Filter_by_Expression_df)} rows")

# [.] TRANSFORM: Reformat
Reformat_df = Filter_by_Expression_df.copy()
print(f"[~] TRANSFORM Reformat: {len(Reformat_df)} rows")

# [.] TRANSFORM: Rollup
Rollup_df = Reformat_df.groupby(['id', 'nombre']).agg(monto=('monto', 'sum')).reset_index()
print(f"[~] TRANSFORM Rollup: {len(Rollup_df)} rows")

# [*] SINK: Output_File
os.makedirs("output", exist_ok=True)
Rollup_df.to_csv("output/output_file.csv", index=False)
print(f"[>] SINK Output_File: {len(Rollup_df)} rows -> output/output_file.csv")

print("[ok] BNX Python Job Finished")
