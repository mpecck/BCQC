import os
import pandas as pd


data_folder = "../../results"
sim_num = 1
num_of_workpiece = 5
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
score_type = "majority"
threshold_list = [3, 5, 7, 9, 11, 13, 15, 17]
input_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_input"
output_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_simulation"
if not os.path.exists(output_folder):
    # Create target Directory
    os.makedirs(output_folder)
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")

header = dict()
for threshold in threshold_list:
    header[threshold] = list()
writer = pd.ExcelWriter(f"{output_folder}/independent_qc_{score_type}_{num_of_workpiece}_workpiece_simulation_{sim_num}.xlsx", mode="w")
f1_df = pd.DataFrame(header)
transport_df = pd.DataFrame(header)
inspection_df = pd.DataFrame(header)
for filename in os.listdir(input_folder):   # Each results for each trial
    print(filename)
    if os.path.isfile(f"{input_folder}/{filename}"):
        df = pd.read_excel(f"{input_folder}/{filename}", sheet_name="average")
        # F1 sheet
        data = dict()
        for threshold in threshold_list:
            print(threshold)
            print(df.loc[df["threshold"] == threshold]["F1"])
            data[threshold] = df.loc[df["threshold"] == threshold]["F1"].values[0]
        f1_df = f1_df.append(data, ignore_index=True)
        # transport_time_norm sheet
        data = dict()
        for threshold in threshold_list:
            data[threshold] = df.loc[df["threshold"] == threshold]["transport_time_norm"].values[0]
        transport_df = transport_df.append(data, ignore_index=True)
        # inspection_time_norm sheet
        data = dict()
        for threshold in threshold_list:
            data[threshold] = df.loc[df["threshold"] == threshold]["inspection_time_norm"].values[0]
        inspection_df = inspection_df.append(data, ignore_index=True)
f1_df.to_excel(writer, sheet_name="F1", index=False)
print(f1_df)
transport_df.to_excel(writer, sheet_name="transport_time_norm", index=False)
print(transport_df)
inspection_df.to_excel(writer, sheet_name="inspection_time_norm", index=False)
print(inspection_df)
writer.save()
writer.close()


