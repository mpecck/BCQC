import matplotlib.pyplot as plt
import os
import pandas as pd

data_folder = "../../results"
num_of_workpiece = 20
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
workcell_list = [f"wc_{idx + 1}" for idx in range(17)]
input_filename = "input_20"
score_type = "training"
threshold = 0.9
input_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_input"
output_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/graph/"
if not os.path.exists(output_folder):
    # Create target Directory
    os.makedirs(output_folder)
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")

# Plot individual MSE curve
df = pd.read_excel(f"{input_folder}/independent_qc_{score_type}_{num_of_workpiece}_workpiece_{input_filename}.xlsx")
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.plot(df.qc_iteration, df.MSE, color="black")
ax1.set_ylabel('MSE', fontsize=15)
ax1.set_xlabel('QC Iteration', fontsize=15)
ax1.set_ylim([0, 0.5])
ax1.set_xlim([0, 800])
plt.show()
