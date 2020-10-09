import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


data_folder = "../../results"
num_of_workpiece = 5
workpiece_list = [f"wp_{idx + 1}" for idx in range(num_of_workpiece)]
score_type = "majority"
threshold_list = [3, 5, 7, 9, 11, 13, 15, 17]
input_folder = f"{data_folder}/postprocessed/independent_qc/{score_type}/{num_of_workpiece}_workpiece/per_simulation"

for filename in os.listdir(f"{input_folder}"):  # Each datetime folder
    f1_df = pd.read_excel(f"{input_folder}/{filename}", sheet_name="F1")
    transport_df = pd.read_excel(f"{input_folder}/{filename}", sheet_name="transport_time_norm")
    inspection_df = pd.read_excel(f"{input_folder}/{filename}", sheet_name="inspection_time_norm")

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # Output stacked plot
    mean_inspection_list = inspection_df.mean().to_list()
    mean_transport_list = transport_df.mean().to_list()
    x = threshold_list
    y = [mean_transport_list, mean_inspection_list, ]
    sp = plt.stackplot(x, y, labels=['Transport', 'Inspection'], colors=['#89a0b0', '#d8dcd6'], alpha=0.5)
    ax.plot(x, y[0], color="black")
    ax.plot(x, [sum(i) for i in zip(y[0], y[1])], color="black")
    # Adjust axis
    ax.set_ylabel('Factor of Production Time', fontsize=15)
    ax.set_xlabel('Threshold', fontsize=15)
    patches = [
        Patch(facecolor='#d8dcd6', edgecolor='k', label='Normalized inspection time'),
        Patch(facecolor='#89a0b0', edgecolor='k', label='Normalized transport time'),
    ]
    leg = plt.legend(loc='lower right', handles=patches)

    # Output box plot
    ax2 = ax.twinx()
    bp = f1_df.boxplot(
        column=threshold_list,
        grid=False,
        fontsize=12,
        ax=ax2,
        return_type='dict',
        positions=threshold_list
    )

    # Style box plot
    [item.set_color('k') for item in bp['boxes']]
    [item.set_color('k') for item in bp['fliers']]
    [item.set_color('k') for item in bp['medians']]
    [item.set_color('k') for item in bp['whiskers']]

    # Adjust axis
    ax2.set_ylim([0.6, 1])
    ax2.set_ylabel('F1', fontsize=15)
    # Show plot
    plt.show()
