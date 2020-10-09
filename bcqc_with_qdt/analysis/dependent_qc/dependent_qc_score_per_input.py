import ast
import os
import pandas as pd


data_folder = "../../results"
num_of_workpiece = 10
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
input_filename = "input_1"
score_type = "score"
threshold = 0.9
input_folder = f"{data_folder}/raw/{input_filename}/dependent_qc/{score_type}/{num_of_workpiece}_workpiece"
output_folder = f"{data_folder}/postprocessed/dependent_qc/{score_type}/{num_of_workpiece}_workpiece/per_input"
if not os.path.exists(output_folder):
    # Create target Directory
    os.makedirs(output_folder)
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")

header = {
    "input_filename": [],
    "threshold": [],
    "TP": [],
    "TN": [],
    "FP": [],
    "FN": [],
    "production_time": [],
    "transport_time": [],
    "inspection_time": [],
    "network_time": [],
    "total_time": [],
    "accuracy": [],
    "miss": [],
    "precision": [],
    "recall": [],
    "F1": [],
    "transport_time_norm": [],
    "inspection_time_norm": [],
    "network_time_norm": [],
    "total_time_norm": [],
}
writer = pd.ExcelWriter(f"{output_folder}/dependent_qc_{score_type}_{num_of_workpiece}_workpiece_{input_filename}.xlsx", mode="w")
for filename in os.listdir(input_folder):   # Each results
    if f"{input_filename}" in filename:
        additional_header = {
            f"wc_{i + 1}": []
            for i in range(17)
        }
        temp = header.copy()
        temp.update(additional_header)
        compiled_df = pd.DataFrame(temp)
        df = pd.read_csv(f"{input_folder}/{filename}")
        df = df.sort_values(by=['workpiece_id', 'time_step'])
        print(df.head())
        df.loc[:, 'actual_quality'] = df.loc[:, 'actual_quality'].ffill()
        df.loc[:, 'state'] = df.loc[:, 'state'].ffill()
        data = dict()
        consent_df = df[df["consent"] == 1]
        # Compile qc score through row by row iteration
        for row in consent_df.itertuples():
            winner_qc_list = row.winner_qc_list
            winner_qc_list = ast.literal_eval(winner_qc_list)
            for qc, score in winner_qc_list:
                data[qc] = score  # Keep overwriting the score until the last time the qc appear
        # Get confusion matrix data
        tp_df = consent_df[(consent_df["state"].isin(["['Fail']", "['Pass', 'Fail']"]))
                           & (consent_df["qc_results"] == "['Fail']")]
        tn_df = consent_df[(consent_df["state"] == "['Pass']") & (consent_df["qc_results"] == "['Pass']")]
        fp_df = consent_df[(consent_df["state"] == "['Fail']") & (consent_df["qc_results"] == "['Pass']")]
        fn_df = consent_df[(consent_df["state"] == "['Pass']") & (consent_df["qc_results"] == "['Fail']")]
        data["input_filename"] = input_filename
        data["threshold"] = threshold
        data["TP"] = len(tp_df)
        data["TN"] = len(tn_df)
        data["FP"] = len(fp_df)
        data["FN"] = len(fn_df)
        data["production_time"] = df.production_time.sum()
        data["transport_time"] = df.transport_time.sum()
        data["inspection_time"] = df.inspection_time.sum()
        max_time_step = df.time_step.max()  # v the last step must be inspection.
        data["total_time"] = max_time_step + df[df.time_step == max_time_step].inspection_time.values[0]
        # Normalizing network time, which is elapsed time per RESTapi request
        network_time_unit = df.loc[df["network_time"].first_valid_index()]["network_time"]  # first value
        data["network_time"] = df.network_time.sum() / network_time_unit * 0.003  # each unit is 0.003 s
        # Get confusion matrix and norm time
        data["accuracy"] = (data["TP"] + data["TN"]) / (data["TP"] + data["TN"] + data["FP"] + data["FN"])
        data['miss'] = data["FN"] / (data["TP"] + data["FN"])
        data['precision'] = data["TP"] / (data["TP"] + data["FP"])
        data['recall'] = data["TP"] / (data["TP"] + data["FN"])
        data['F1'] = 2 * data["TP"] / (2 * data["TP"] + data["FP"] + data["FN"])
        data["transport_time_norm"] = data["transport_time"] / data["production_time"]
        data["inspection_time_norm"] = data["inspection_time"] / data["production_time"]
        data["network_time_norm"] = data["network_time"] / data["production_time"]
        data["total_time_norm"] = data["total_time"] / data["production_time"]
        # print(data)
        compiled_df = compiled_df.append(data, ignore_index=True)
        # print(compiled_df)
        df.to_excel(writer, sheet_name="raw", index=False)
        compiled_df.to_excel(writer, sheet_name="processed", index=False)
writer.save()
writer.close()


