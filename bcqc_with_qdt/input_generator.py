from bcqc_with_qdt.emulators.workcell_emulator import Workcell
from bcqc_with_qdt.emulators.workpiece_emulator import Workpiece
from bcqc_with_qdt.emulators.belt_emulator import Transporter
from bcqc_with_qdt.emulators.process_controller_emulator import ProcessController
from bcqc_with_qdt.utils import csv_functions

from datetime import datetime
import time

# Input variables
input_num = 1
data_sheet = csv_functions.read_csv('Data_Sheet.csv')
filename = f"data/{datetime.now().strftime('%Y%m%d_%H%M%S')}_inputs.csv"
total_workcells = 17
actual_capability_df = csv_functions.read_csv("actual_inspector_capability.csv")
time_interval = 1

while True:
    total_products = int(input("Enter number of products to produce: "))
    if not isinstance(total_products, int) or total_products == 0:
        print("Please enter a natural number.")
    else:
        break

# Instantiate objects
print("Instantiating objects...")
score_list = actual_capability_df[f"input_{input_num}"].to_list()

workcells = {
    f"wc_{i+1}": Workcell(
        step_idx=i+1,
        id=f"wc_{i+1}",
        ip="localhost",
        port=5000,
        capability=score_list[i],
    )
    for i in range(total_workcells)
}
workpieces = {
    f"wp_{i+1}": Workpiece(id=f"wp_{i+1}")
    for i in range(total_products)
}
process_controllers = {  # each workpiece has one process controller
    f"wp_{i+1}": ProcessController(workpiece_id=f"wc_{i+1}")    # same name as workpiece
    for i in range(total_products)
}
transporter = Transporter()
print("Objects instantiated...")

# Initialize data logging
data = {
    "time_step": [],
    "workpiece_id": [],
    "step_idx": [],
    "workcell_id": [],
    "production_time": [],
    "actual_quality": [],
}
for wc_id in workcells.keys():
    data[f"qc_{wc_id}_confidence"] = []
    data[f"qc_{wc_id}_results"] = []
    data[f"qc_{wc_id}_time"] = []
df = csv_functions.create_df(data)

# Initialize time step for while loop
time_step = 0
while True:
    print(f"At {time_step},")
    for wp_id, wp_inst in workpieces.items():
        print(f"    Workpiece {wp_id}: {wp_inst.status}")
        data = dict()   # reset data dict for empty df
        if wp_inst.status == "completed":   # if completed
            continue
        # Get next production step
        elif wp_inst.status == "awaiting next step":
            pc = process_controllers[wp_id]  # Get next step
            _, step_idx, sink_id = pc.get_next_step_idx(
                wp_inst,
                workcells
            )  # based on wp pre-conditions and wc state
            pc.update_workpiece_completion(wp_inst)
            print(f"        Next step from process controller is {step_idx}...")
            # Assume already transported to production workcell
            wp_inst.location = sink_id
        # Start production
        elif wp_inst.status == "awaiting production":
            # Start production step
            wc_inst = workcells[wp_inst.location]
            wc_inst.add_to_production(wp_inst)
            if wc_inst.inspection_workpiece is not None:
                if not isinstance(wc_inst.inspection_workpiece, str):
                    if wc_inst.inspection_workpiece.status == "in inspection":  # Inspecting other workpieces
                        continue
            wc_inst.start_production(worksheet_df=data_sheet)
            print(f"        Start production for step {wp_inst.step_idx}.")
        # Still in production
        elif wp_inst.status == "in production":
            wc_id = wp_inst.location
            wc_inst = workcells[wc_id]
            if wc_inst.in_production(time_interval):  # positive count down
                continue
            else:  # negative count down
                # End production step
                production_time = wc_inst.production_time
                execution_info, actual_quality = wc_inst.end_production(data_sheet)
                # Assume already passed to quality controllers
                wp_inst.status = "awaiting inspection"
                wp_inst.count_down = 0  # reset
                wp_inst.location = None  # reset
                wc_inst.production_workpiece = None  # reset
                # Update workpiece status to process controller
                max_probability = max(probability for state, probability in actual_quality.items())
                state_list = [state for state, probability in actual_quality.items() if
                              probability == max_probability]
                pc = process_controllers[wp_id]
                pc.update_step_status(wp_inst.step_idx, state_list)
                if wp_inst.status != "in production":
                    print(f"        Production time is {production_time}.")
                    print(f"        Actual quality is {actual_quality}.")
                    # Log production information
                    data["time_step"] = [time_step - production_time]  # time_step the production starts
                    data["workpiece_id"] = [wp_id]
                    data["step_idx"] = [wp_inst.step_idx]
                    data["workcell_id"] = [wc_id]
                    data["production_time"] = [production_time]
                    data["actual_quality"] = [actual_quality]
                    # Inspect workpiece
                    for wc_id, wc_inst in workcells.items():    # get QC results and time from all workcells
                        wc_inst.inspection_workpiece = wp_inst  # temporary set it
                        state_list = wc_inst.inspect_workpiece()
                        inspection_time = wc_inst.get_inspection_time(wp_inst.step_idx, data_sheet)
                        wc_inst.inspection_workpiece = None     # reset
                        print(f"        QC time by {wc_id} is {inspection_time}.")
                        print(f"        QC results by {wc_id} is {state_list}.")
                        # Log inspection information
                        data[f"qc_{wc_id}_confidence"] = [wc_inst.capability]
                        data[f"qc_{wc_id}_results"] = [state_list]
                        data[f"qc_{wc_id}_time"] = [inspection_time]
                    # Assume finish inspection
                    wp_inst.actual_quality = None   # Reset
                    wp_inst.status = "awaiting next step"   # Reset
                # Append log data to dataframe
                df = csv_functions.append_to_df(df, data)

    time_step += time_interval
    if all(wp_inst.status == "completed" for wp_id, wp_inst in workpieces.items()):
        break
    time.sleep(.1)
# Write dataframe into csv
csv_functions.write_csv(filename, df)
