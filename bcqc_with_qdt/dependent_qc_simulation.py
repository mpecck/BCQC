from bcqc_with_qdt.emulators.network_emulator import app, add_routes
from bcqc_with_qdt.emulators.workcell_emulator import Workcell
from bcqc_with_qdt.emulators.workpiece_emulator import Workpiece
from bcqc_with_qdt.emulators.belt_emulator import Transporter
from bcqc_with_qdt.emulators.process_controller_emulator import ProcessController
from bcqc_with_qdt.utils import csv_functions

from datetime import datetime
from threading import Thread
import json
import os
import time
import requests
import pandas as pd

headers = {
    'Content-Type': "application/json",
}


# todo: Change these input variables
learning = False
threshold = 0.9
input_num = 1   # Input set
total_products = 3
total_workcells = 17
input_filename = f"input_{input_num}"   # Corresponding to the column in inspector_capability.csv
dt = datetime.now().strftime('%Y%m%d_%H%M%S')
output_folder = f"data/raw/{input_filename}/dependent_qc/score/{total_products}_workpiece"
ip = '127.0.0.1'
port = 4000
actual_capability_df = csv_functions.read_csv("actual_inspector_capability.csv")
estimated_capability_df = csv_functions.read_csv("estimated_inspector_capability.csv")
data_sheet = csv_functions.read_csv('Data_Sheet_qdt.csv')
time_interval = 1   # Time step for each loop

# Check if input is acceptable
if f"input_{input_num}" not in actual_capability_df:
    raise KeyError(f"Input number is not the inspector_capability.csv")

# Get capability and score list
capability_list = actual_capability_df[f"input_{input_num}"].to_list()
score_list = estimated_capability_df[f"input_{input_num}"].to_list()

# Create output path
if not os.path.exists(output_folder):
    os.makedirs(output_folder)    # Create target Directory
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")
output_filename = f"{output_folder}/{dt}_workpiece_{total_products}_input_{input_num}.csv"


def instantiate_objects(threshold, score_list, learning):
    # Instantiate objects
    print("Instantiating objects...")
    workcells = {
        f"wc_{i+1}": Workcell(
            step_idx=i+1,
            id=f"wc_{i+1}",
            ip=ip,
            port=port,
            qc_id=f"wc_{i + 1}",
            consensus_mode="confidence",
            threshold=threshold,
            score=score_list[i],
            capability=capability_list[i],
            learning=learning
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
    return workcells, workpieces, transporter, process_controllers


def simulate(workcells, workpieces, transporter, process_controllers, ):
    quality_controllers = workcells

    # Register qc as nodes
    print("Registering nodes...")
    payload = {
        "nodes": {
            qc_id: {
                "address": qc_inst.address
            }
            for qc_id, qc_inst in quality_controllers.items()
        }
    }
    for qc_id, qc_inst in quality_controllers.items():
        res = requests.post(f"{qc_inst.address}/blockchain/registration", data=json.dumps(payload), headers=headers)
        if res.status_code == 200:
            print(f"Nodes registered at {qc_id}.")
        else:
            raise ConnectionError(f"Node {qc_id} refuse to register nodes.")

    # Initialize data logging
    data = {
        "time_step": [],
        "workpiece_id": [],
        "step_idx": [],
        "production_workcell": [],
        "actual_quality": [],
        "state": [],
        "qc": [],
        "consent": [],
        "winner_qc_list": [],
        "score": [],
        "qc_results": [],
        "production_time": [],
        "transport_time": [],
        "inspection_time": [],
        "network_time": [],
    }
    df = csv_functions.create_df(data)

    # Initialize time step for while loop
    time_step = 0
    consent = False
    while True:
        print(f"At {time_step},")
        for wp_id, wp_inst in workpieces.items():
            print(f"    Workpiece {wp_id}: {wp_inst.status}, at: {wp_inst.location}, count down: {wp_inst.count_down}")

            # Reset dict for dataframe
            data = dict()  # Reset
            execution_info = dict()  # Place holder

            # Log general data
            data["workpiece_id"] = [wp_id]
            data["step_idx"] = [wp_inst.step_idx]

            if wp_inst.sink is not None and wp_inst.source is not None:   # Workpiece needs transportation
                print(f"        Travelling from {wp_inst.source} to {wp_inst.sink}...")
                # Start travel
                if wp_inst.location is not None:    # Move workpiece out of location
                    travel_time, travel_dist, splitter = transporter.start_travel(wp_inst)
                    # Log transport data
                    data["time_step"] = [time_step]
                    data["transport_time"] = [travel_time]
                # In travel
                else:
                    if transporter.in_travel(wp_inst, time_interval):    # still can count down with time_interval
                        continue
                    else:   # End travel
                        transporter.end_travel(wp_inst)

            if wp_inst.sink is None and wp_inst.source is None:  # Workpiece does not need transportation
                # Workpiece completed, no actions needed
                if wp_inst.status == "completed":  # if completed
                    continue
                # Get next production step
                elif wp_inst.status == "awaiting next step":
                    pc = process_controllers[wp_id]      # Get next step
                    _, step_idx, sink_id = pc.get_next_step_idx(
                        wp_inst,
                        workcells
                    )  # based on wp pre-conditions and wc state
                    pc.update_workpiece_completion(wp_inst)
                    print(f"        Next step from process controller is {step_idx}...")
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
                        # Update workpiece status to process controller
                        max_probability = max(probability for state, probability in actual_quality.items())
                        state_list = [state for state, probability in actual_quality.items() if
                                      probability == max_probability]
                        pc = process_controllers[wp_id]
                        pc.update_step_status(wp_inst.step_idx, state_list)
                        if wp_inst.status != "in production":
                            # Log production data
                            data["time_step"] = [time_step - production_time]
                            data["production_workcell"] = [wc_id]
                            data["production_time"] = [production_time]
                            data["actual_quality"] = [actual_quality]
                            data["state"] = [str(state_list)]
                # Start inspection
                elif wp_inst.status == "awaiting inspection":  # Awaiting inspection
                    qc_id = wp_inst.location
                    qc_inst = quality_controllers[qc_id]
                    qc_inst.add_to_inspection(wp_inst)
                    if qc_inst.production_workpiece is not None:
                        if not isinstance(qc_inst.production_workpiece, str):
                            if qc_inst.production_workpiece.actual_quality is None:  # Producing other workpieces
                                continue
                    qc_inst.start_inspection(wp_inst.step_idx, worksheet_df=data_sheet)
                    print(f"        Inspection time will end {qc_inst.inspection_time} later.")
                # Still in inspection
                elif wp_inst.status == "in inspection":
                    qc_id = wp_inst.location
                    qc_inst = quality_controllers[qc_id]
                    if qc_inst.in_inspection(time_interval):    # positive count down
                        continue
                    else:   # negative count down
                        # End inspection (Update consent)
                        execution_info["min_qc_required"] = len(wp_inst.actual_quality) + 1
                        inspection_time, network_time, consent, winner_dict = \
                            qc_inst.end_inspection(
                                execution_info=execution_info
                            )
                        if wp_inst.status != "in inspection":
                            # Log qc data (no consent)
                            data["time_step"] = [time_step - inspection_time]
                            data["qc"] = [qc_id]
                            data["network_time"] = [network_time]
                            data["inspection_time"] = [inspection_time]
                            data["consent"] = [consent]
                            data["in_winner_counter"] = [qc_inst.in_winner_counter]
                            data["in_qc_counter"] = [qc_inst.in_qc_counter]
                            data["score_error"] = [qc_inst.get_score_error()]
                            data["qc_score"] = [qc_inst.score]
                            data["qc_capability"] = [qc_inst.capability]
                            # Log qc data (consent)
                            data["winner_qc_list"] = [winner_dict.get("winner_qc_list", None)]
                            data["score"] = [winner_dict.get("score", None)]
                            data["qc_results"] = [winner_dict.get("results", None)]
            # Append data to dataframe
            if data.get("time_step", None) is not None:
                df = csv_functions.append_to_df(df, data)
            if consent:
                # Write dataframe into csv
                csv_functions.write_csv(output_filename, df)

        # Add time interval
        time_step += time_interval
        # Termination condition
        if all(wp_inst.status == "completed" for wp_id, wp_inst in workpieces.items()):
            break

        time.sleep(.1)

    # Write dataframe into csv
    csv_functions.write_csv(output_filename, df)
    print("====================================== PROGRAM END ======================================")


if __name__ == '__main__':
    qc, wp, trans, pc = instantiate_objects(threshold, score_list, learning)
    add_routes(qc, threshold)
    t = Thread(
        target=simulate,
        args=(qc, wp, trans, pc, )
    )
    t.start()
    app.run(host='0.0.0.0', port=port)
