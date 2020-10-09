import os
import pandas as pd
import matplotlib.pyplot as plt

data_folder = "../data"
input_filename = "../actual_inspector_capability.csv"
input_dict = {f"input_{i+1}": i + 1 for i in range(20)}
output_folder = f"{data_folder}/postprocessed"
if not os.path.exists(output_folder):
    # Create target Directory
    os.makedirs(output_folder)
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")

# compiled_df = pd.DataFrame(header)
compiled_df = pd.read_csv(input_filename)
compiled_df.rename(columns=input_dict, inplace=True)
# Output box plot
bp = compiled_df.boxplot(
    grid=False,
    fontsize=12,
    return_type='dict'
)
# Style box plot
[item.set_color('k') for item in bp['boxes']]
[item.set_color('k') for item in bp['fliers']]
[item.set_color('k') for item in bp['medians']]
[item.set_color('k') for item in bp['whiskers']]
# Adjust axis
ax = plt.gca()
ax.set_ylabel('QC Capability', fontsize=15)
ax.set_xlabel('Input', fontsize=15)
# Show plot
plt.show()
