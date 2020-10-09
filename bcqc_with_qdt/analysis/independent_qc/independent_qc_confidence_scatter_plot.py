import pandas as pd
import matplotlib.pyplot as plt


data_folder = "../../results"
idata_folder = "../../data"
num_of_workpiece = 5
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
input_filename = "input_1"
threshold = 0.9
capability_folder = f"{idata_folder}/postprocessed/independent_qc/capability/{num_of_workpiece}_workpiece/per_input"
score_folder = f"{data_folder}/postprocessed/independent_qc/score/{num_of_workpiece}_workpiece/per_input"
category_folder = f"{data_folder}/postprocessed/independent_qc/majority/{num_of_workpiece}_workpiece/per_input"

capability_df = pd.read_excel(f"{capability_folder}/independent_qc_capability_{num_of_workpiece}_workpiece_{input_filename}.xlsx")
score_df = pd.read_excel(f"{score_folder}/independent_qc_score_{num_of_workpiece}_workpiece_{input_filename}.xlsx")
fig = plt.figure()
ax1 = fig.add_subplot(111)
sc1 = plt.scatter(
    x=capability_df.f1_et_threshold,
    y=capability_df.time_et_threshold,
    facecolors='none',
    edgecolors='black',
    # c='gray',
    marker="o",
    label="True capability",
    s=100,
)
sc2 = plt.scatter(
    x=score_df.f1_et_threshold,
    y=score_df.time_et_threshold,
    c='black',
    marker="x",
    label="Estimated capability",
    s=100,
)
y = [0, 12]
x = [0, 12]
ax1.set_ylabel('QC Time', fontsize=15)
ax1.set_xlabel('F1', fontsize=15)
ax1.set_ylim(y)
ax1.set_xlim(x)
ax1.set_yticks(range(1, 13, 2))
ax1.set_xticks(range(1, 13, 2))
ax1.set_yticklabels(['<3', '3', '5', '7', '9', '>9'])
ax1.set_xticklabels(['<3', '3', '5', '7', '9', '>9'])
leg = plt.legend(loc='upper left')
ax1.plot(x, y, linestyle='dashed', dashes=(20, 20), color="black", linewidth=0.5)   # Place behind legend to be excluded
plt.show()

