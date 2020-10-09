import ast
import os
import pandas as pd


data_folder = "../../results"
num_of_workpiece = 20
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
workcell_list = [f"wc_{idx + 1}" for idx in range(17)]
input_filename = "input_1"
score_type = "training"
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
for idx, folder in enumerate(os.listdir(f"{input_folder}")):  # Each datetime folder
    print(folder)
    data = {
        "threshold": [],
        "qc_iteration": [],  # 1 iteration = start of inspection until reach consent
        "workpiece": [],
        "num_of_winner_qc": [],
        "MSE": [],
    }
    for i in range(17):
        data[f"wc_{i + 1}_score"] = []
        data[f"wc_{i + 1}_capability"] = []
    compiled_df = pd.DataFrame(data)

    # Fill in score and capability of first row
    filename = os.listdir(f"{input_folder}/{folder}")[0]     # Using first filename
    df = pd.read_csv(f"{input_folder}/{folder}/{filename}")
    capability_dict = dict()
    for workcell in workcell_list:
        data[f"{workcell}_score"] = 0.1
        data[f"{workcell}_capability"] = df[df["qc"] == workcell].qc_capability.iloc[0]

    # Concatenate consent_df and reset index to get iteration number
    df_list = list()
    for workpiece in workpiece_list:
        for filename in os.listdir(f"{input_folder}/{folder}"):  # Each results
            if f"{workpiece}_" in filename:
                # print(filename)
                suffix = f"_{threshold}.csv"
                if filename.endswith(suffix):
                    df = pd.read_csv(f"{input_folder}/{folder}/{filename}")
                    qc_df = df[pd.notnull(df['qc'])]
                    qc_df["workpiece"] = workpiece
                    # print(qc_df)
                    df_list.append(qc_df)
    concat_df = pd.concat(df_list)
    # print(concat_df)
    iteration = 0

    # Fill in
    for row in concat_df.itertuples():     # each row is one iteration
        # print(row)
        qc = row.qc
        data[f"{qc}_score"] = row.qc_score
        data[f"{qc}_capability"] = row.qc_capability
        if row.consent == 1:
            iteration += 1
            data["threshold"] = threshold
            data["qc_iteration"] = iteration
            data["workpiece"] = row.workpiece
            # Fill in the rest of the workcell score and capability
            for workcell in workcell_list:
                if data.get(f"{workcell}_score", None) is None:
                    data[f"{workcell}_score"] = compiled_df[f"{workcell}_score"].iloc[-1]
                    data[f"{workcell}_capability"] = compiled_df[f"{workcell}_capability"].iloc[-1]
            error_list = [
                data[f"{workcell}_score"] - data[f"{workcell}_capability"]
                for workcell in workcell_list
            ]
            se_list = [error ** 2 for error in error_list]
            data["MSE"] = sum(se_list) / len(se_list)
            winner_qc_list = row.winner_qc_list
            winner_qc_list = ast.literal_eval(winner_qc_list)
            data["num_of_winner_qc"] = len(winner_qc_list)
            # print(data)
            compiled_df = compiled_df.append(data, ignore_index=True)
            data = dict()
    # Write to excel sheet
    compiled_df.to_excel(writer, sheet_name=folder, index=False)
    # break
# Save
writer.save()
writer.close()

