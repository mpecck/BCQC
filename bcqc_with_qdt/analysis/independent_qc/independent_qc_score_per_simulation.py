import os
import pandas as pd


data_folder = "../../results"
sim_num = 1
num_of_workpiece = 5
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
score_type = "score"
threshold = 0.9
input_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_input"
output_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_simulation"
category_folder = f"{data_folder}/postprocessed/independent_qc/majority/{num_of_workpiece}_workpiece/per_input"
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
    "accuracy": [],
    "miss": [],
    "precision": [],
    "recall": [],
    "F1": [],
    "transport_time_norm": [],
    "inspection_time_norm": [],
    "network_time_norm": [],
    "total_time_norm": [],
    "f1_et_threshold": [],
    "ttn_et_threshold": [],
    "itn_et_threshold": [],
    "ntn_et_threshold": [],
    "time_et_threshold": [],
}
writer = pd.ExcelWriter(f"{output_folder}/independent_qc_{score_type}_{num_of_workpiece}_workpiece_simulation_{sim_num}.xlsx", mode="w")
additional_header = {
    f"wc_{i+1}": []
    for i in range(17)
}
temp = header.copy()
temp.update(additional_header)
compiled_df = pd.DataFrame(temp)
for filename in os.listdir(input_folder):   # Each results for each input
    sheets_dict = pd.read_excel(f"{input_folder}/{filename}", sheet_name=None)
    df = pd.concat(sheets_dict.values())
    folder_list = [filename]
    print(folder_list)
    for folder in folder_list:
        data = dict()
        filtered_df = df
        # filtered_df = df[df["folder"] == folder]
        input_filename_with_xlsx = filename[len(f"independent_qc_{score_type}_{num_of_workpiece}_workpiece_"):]
        input_filename = input_filename_with_xlsx[:(len(input_filename_with_xlsx)-len(".xlsx"))]
        data["input_filename"] = input_filename
        data["threshold"] = threshold
        data["TP"] = filtered_df["TP"].sum()
        data["TN"] = filtered_df["TN"].sum()
        data["FP"] = filtered_df["FP"].sum()
        data["FN"] = filtered_df["FN"].sum()
        data["production_time"] = filtered_df.production_time.sum()
        data["transport_time"] = filtered_df.transport_time.sum()
        data["inspection_time"] = filtered_df.inspection_time.sum()
        data["network_time"] = filtered_df.network_time.sum()
        for key in additional_header.keys():
            data[key] = filtered_df[filtered_df[key].notnull()][key].values[-1]
        data["accuracy"] = (data["TP"] + data["TN"]) / (data["TP"] + data["TN"] + data["FP"] + data["FN"])
        data['miss'] = data["FN"] / (data["TP"] + data["FN"])
        data['precision'] = data["TP"] / (data["TP"] + data["FP"])
        data['recall'] = data["TP"] / (data["TP"] + data["FN"])
        data['F1'] = 2 * data["TP"] / (2 * data["TP"] + data["FP"] + data["FN"])
        data["transport_time_norm"] = data["transport_time"]/data["production_time"]
        data["inspection_time_norm"] = data["inspection_time"]/data["production_time"]
        data["total_time_norm"] = data["transport_time_norm"] + data["inspection_time_norm"]
        data["network_time_norm"] = data["network_time"]/data["production_time"]

        # Get category from majority
        print(input_filename_with_xlsx)
        category_filename = f"independent_qc_majority_{num_of_workpiece}_workpiece_{input_filename}.xlsx"
        category_df = pd.read_excel(f"{category_folder}/{category_filename}", sheet_name="average")
        category_df = category_df.loc[category_df["threshold"] <= 9]
        category_df["total_time_norm"] = category_df["transport_time_norm"] + category_df["inspection_time_norm"]
        param_list = [
            ("F1", "f1_et_threshold", data['F1']),
            ("transport_time_norm", "ttn_et_threshold", data["transport_time_norm"]),
            ("inspection_time_norm", "itn_et_threshold", data["inspection_time_norm"]),
            ("total_time_norm", "time_et_threshold", data["total_time_norm"]),
            ("network_time_norm", "ntn_et_threshold", data["network_time_norm"])
        ]
        for param in param_list:
            threshold_lower = None  # place holder
            threshold_upper = None  # place holder
            lower = 0  # place holder
            upper = 0  # place holder
            interp_threshold = 1  # place holder
            threshold_lower_range = category_df.loc[
                round(category_df[param[0]], 2) <= round(param[2], 2)]  # find lower range
            if len(threshold_lower_range) != 0:
                threshold_lower = threshold_lower_range.iloc[-1].threshold  # find lower boundary
                lower = round(threshold_lower_range.iloc[-1][param[0]], 2)  # find lower boundary
            else:
                interp_threshold = 1
            threshold_upper_range = category_df.loc[
                round(category_df[param[0]], 2) >= round(param[2], 2)]  # find lower range
            if len(threshold_upper_range) != 0:
                threshold_upper = threshold_upper_range.iloc[0].threshold  # find lower boundary
                upper = round(threshold_upper_range.iloc[0][param[0]], 2)  # find lower boundary
            else:
                interp_threshold = 11
            if threshold_lower is not None and threshold_upper is not None:
                if lower != upper:  # value is within range
                    ratio = (param[2] - lower) / (upper - lower)
                    interp_threshold = ratio * (threshold_upper - threshold_lower) + threshold_lower
                else:
                    interp_threshold = min(threshold_lower, threshold_upper)  # get min threshold
            data[param[1]] = interp_threshold

        # Append to df
        compiled_df = compiled_df.append(data, ignore_index=True)
    # print(compiled_df)
    compiled_df.to_excel(writer, index=False)
writer.save()
writer.close()


