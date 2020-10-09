import ast
import os
import pandas as pd


data_folder = "../../results"
sim_num = 1
num_of_workpiece = 5
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
score_type = "score"
threshold = 0.9
input_folder = f"{data_folder}/postprocessed/dependent_qc/{score_type}/{num_of_workpiece}_workpiece/per_input"
output_folder = f"{data_folder}/postprocessed/dependent_qc/{score_type}/{num_of_workpiece}_workpiece/per_simulation"
if not os.path.exists(output_folder):
    # Create target Directory
    os.makedirs(output_folder)
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")

writer = pd.ExcelWriter(f"{output_folder}/dependent_qc_{score_type}_{num_of_workpiece}_workpiece_simulation_{sim_num}.xlsx", mode="w")
df_list = list()
for filename in os.listdir(input_folder):
    if filename.startswith("~"):
        continue
    print(filename)
    temp_df = pd.read_excel(f"{input_folder}/{filename}", sheet_name="processed")
    df_list.append(temp_df)
df = pd.concat(df_list)
df.to_excel(writer, sheet_name="processed", index=False)
writer.save()
writer.close()


