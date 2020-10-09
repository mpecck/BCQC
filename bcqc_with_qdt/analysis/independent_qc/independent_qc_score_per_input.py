import ast
import os
import pandas as pd


data_folder = "../../results"
num_of_workpiece = 5
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
score_type = "score"
input_filename = "input_1"
threshold = 0.9
input_folder = f"{data_folder}/raw/{input_filename}/independent_qc/{score_type}/{num_of_workpiece}_workpiece"
output_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_input"
if not os.path.exists(output_folder):
    # Create target Directory
    os.makedirs(output_folder)
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")

writer = pd.ExcelWriter(f"{output_folder}/independent_qc_{score_type}_{num_of_workpiece}_workpiece_{input_filename}.xlsx", mode="w")
for workpiece in workpiece_list:
    prefix = f"{workpiece}_"
    data = {
        "folder": [],
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
    compiled_df = pd.DataFrame(data)
    suffix = f"_{threshold}.csv"
    for folder in os.listdir(f"{input_folder}/"):     # Each datetime folder
        print(folder)
        for filename in os.listdir(f"{input_folder}/{folder}"):  # Each results
            print(filename)
            data = dict()
            if filename.startswith(prefix) and filename.endswith(suffix):
                df = pd.read_csv(f"{input_folder}/{folder}/{filename}")
                consent_df = df[df["consent"] == 1]
                # Compile qc score through row by row iteration
                for row in consent_df.itertuples():
                    print(row)
                    winner_qc_list = row.winner_qc_list
                    winner_qc_list = ast.literal_eval(winner_qc_list)
                    for qc, score in winner_qc_list:
                        data[qc] = score    # Keep overwriting the score until the last time the qc appear
                # Get confusion matrix data
                tp_df = consent_df[(consent_df["actual_quality"] == "Fail") & (consent_df["qc_results"] == "['Fail']")]
                tn_df = consent_df[(consent_df["actual_quality"] == "Pass") & (consent_df["qc_results"] == "['Pass']")]
                fp_df = consent_df[(consent_df["actual_quality"] == "Fail") & (consent_df["qc_results"] == "['Pass']")]
                fn_df = consent_df[(consent_df["actual_quality"] == "Pass") & (consent_df["qc_results"] == "['Fail']")]
                data["folder"] = folder
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
                print(data)
                compiled_df = compiled_df.append(data, ignore_index=True)
    compiled_df.to_excel(writer, sheet_name=workpiece, index=False)
writer.save()
writer.close()
