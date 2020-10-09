import ast
import os
import pandas as pd


data_folder = "../../results"
num_of_workpiece = 5
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
score_type = "majority"
input_filename = "input_1"
threshold_list = [3, 5, 7, 9, 11, 13, 15, 17]
input_folder = f"{data_folder}/raw/{input_filename}/independent_qc/{score_type}/{num_of_workpiece}_workpiece"
output_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_input"
if not os.path.exists(output_folder):
    # Create target Directory
    os.makedirs(output_folder)
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")

header = {
    "threshold": [],
    "TP": [],
    "TN": [],
    "FP": [],
    "FN": [],
    "production_time": [],
    "transport_time": [],
    "inspection_time": [],
    "network_time": [],
}
temp = header.copy()
writer = pd.ExcelWriter(
    f"{output_folder}/independent_qc_{score_type}_{num_of_workpiece}_workpiece_{input_filename}.xlsx", mode="w")
for workpiece in workpiece_list:
    prefix = f"{workpiece}_"
    compiled_df = pd.DataFrame(temp)
    for threshold in threshold_list:
        suffix = f"_{threshold}.csv"
        for folder in os.listdir(f"{input_folder}"):     # Each datetime folder
            print(folder)
            for filename in os.listdir(f"{input_folder}/{folder}"):  # Each results
                print(filename)
                data = dict()
                if filename.startswith(prefix) and filename.endswith(suffix):
                    df = pd.read_csv(f"{input_folder}/{folder}/{filename}")
                    consent_df = df[df["consent"] == 1]
                    # Compile qc score through row by row iteration
                    for row in consent_df.itertuples():
                        # print(row)
                        winner_qc_list = row.winner_qc_list
                        winner_qc_list = ast.literal_eval(winner_qc_list)
                        for qc, score in winner_qc_list:
                            data[qc] = score    # Keep overwriting the score until the last time the qc appear
                    # Get confusion matrix data
                    tp_df = consent_df[(consent_df["actual_quality"] == "Fail") & (consent_df["qc_results"] == "['Fail']")]
                    tn_df = consent_df[(consent_df["actual_quality"] == "Pass") & (consent_df["qc_results"] == "['Pass']")]
                    fp_df = consent_df[(consent_df["actual_quality"] == "Fail") & (consent_df["qc_results"] == "['Pass']")]
                    fn_df = consent_df[(consent_df["actual_quality"] == "Pass") & (consent_df["qc_results"] == "['Fail']")]
                    data["threshold"] = threshold
                    data["TP"] = len(tp_df)
                    data["TN"] = len(tn_df)
                    data["FP"] = len(fp_df)
                    data["FN"] = len(fn_df)
                    data["production_time"] = df.production_time.sum()
                    data["transport_time"] = df.transport_time.sum()
                    data["inspection_time"] = df.inspection_time.sum()
                    # Normalizing network time, which is elapsed time per RESTapi request
                    network_time_unit = df.loc[df["network_time"].first_valid_index()]["network_time"] # first value
                    data["network_time"] = df.network_time.sum()/network_time_unit * 0.003  # each unit is 0.003 s
                    compiled_df = compiled_df.append(data, ignore_index=True)
    compiled_df.to_excel(writer, sheet_name=workpiece, index=False)
writer.save()

# Write into average sheet for all workpieces
additional_header = {
    "F1": [],
    "transport_time_norm": [],
    "inspection_time_norm": [],
    "network_time_norm": [],
}
temp = header.copy()
temp.update(additional_header)
compiled_df = pd.DataFrame(temp)
sheets_dict = pd.read_excel(f"{output_folder}/independent_qc_{score_type}_{num_of_workpiece}_workpiece_{input_filename}.xlsx", sheet_name=None)
df = pd.concat(sheets_dict.values())
for threshold in threshold_list:
    data = dict()
    filtered_df = df[df["threshold"] == threshold]
    data["threshold"] = threshold
    data["TP"] = filtered_df["TP"].sum()
    data["TN"] = filtered_df["TN"].sum()
    data["FP"] = filtered_df["FP"].sum()
    data["FN"] = filtered_df["FN"].sum()
    data["production_time"] = filtered_df.production_time.sum()
    data["transport_time"] = filtered_df.transport_time.sum()
    data["inspection_time"] = filtered_df.inspection_time.sum()
    data["network_time"] = filtered_df.network_time.sum()
    # Get confusion matrix
    data["accuracy"] = (data["TP"] + data["TN"]) / (data["TP"] + data["TN"] + data["FP"] + data["FN"])
    data['miss'] = data["FN"] / (data["TP"] + data["FN"])
    data['precision'] = data["TP"] / (data["TP"] + data["FP"])
    data['recall'] = data["TP"] / (data["TP"] + data["FN"])
    data['F1'] = 2 * data["TP"] / (2 * data["TP"] + data["FP"] + data["FN"])
    # Get normalized time
    data["transport_time_norm"] = data["transport_time"] / data["production_time"]
    data["inspection_time_norm"] = data["inspection_time"] / data["production_time"]
    data["network_time_norm"] = data["network_time"] / data["production_time"]
    compiled_df = compiled_df.append(data, ignore_index=True)
print(compiled_df)
compiled_df.to_excel(writer, sheet_name="average", index=False)
writer.save()
writer.close()
