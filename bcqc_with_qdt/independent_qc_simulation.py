from bcqc_with_qdt.emulators.network_emulator import app, add_routes
from bcqc_with_qdt.emulators.workcell_emulator import Workcell
from bcqc_with_qdt.emulators.workpiece_emulator import Workpiece
from bcqc_with_qdt.emulators.belt_emulator import Transporter
from bcqc_with_qdt.utils import csv_functions

from ast import literal_eval
from datetime import datetime
from threading import Thread
import json
import os
import requests
import time
import pandas as pd


headers = {
    'Content-Type': "application/json",
}


# todo: Change these input variables
consensus_mode = "majority"
# consensus_mode = "confidence"
score_type = "majority"
# score_type = "capability"
# score_type = "training"
# score_type = "score"
learning = True
threshold = 5   # If majority, enter a natural number, x (the minimum state group <= x <= the total_workcells)
# threshold = 0.9   # If confidence, enter a percentage of confidence level, x (0 < x < 1)
input_num = 1
total_products = 5
total_workcells = 17
input_filename = f"input_{input_num}"   # Corresponding to the column in inspector_capability.csv
dt = datetime.now().strftime('%Y%m%d_%H%M%S')
output_folder = f"data/raw/{input_filename}/independent_qc/{score_type}/{total_products}_workpiece/{dt}"
ip = '127.0.0.1'
port = 4000
actual_capability_df = csv_functions.read_csv("actual_inspector_capability.csv")
input_worksheet = csv_functions.read_csv(f'input_{total_products}_workpiece/{input_filename}.csv')
time_interval = 1   # Time step for each loop

# Check if input is acceptable
if consensus_mode == "majority":
    if score_type != "majority":  # check before proceed
        raise KeyError(f"Consensus mode majority do not have score type {score_type}")
    if not float(threshold).is_integer():  # check before proceed
        raise KeyError(f"Threshold is not whole number!")
elif consensus_mode == "confidence":
    if score_type == "majority":  # check before proceed
        raise KeyError(f"Consensus mode majority do not have score type {score_type}")
    if 0 < threshold < 1:  # check before proceed
        raise KeyError(f"Threshold is not within range of 0 to 1!")
if f"input_{input_num}" not in actual_capability_df:
    raise KeyError(f"Input number is not the inspector_capability.csv")
if total_products != len(set(input_worksheet.workpiece_id.to_list())):  # check before proceed
    raise KeyError(f"Number of workpieces is not {total_products}")

# Get score list
if consensus_mode == "majority":
    score_list = [1] * total_workcells  # initial score
elif consensus_mode == "confidence":
    if learning:
        score_list = [0.1] * total_workcells  # initial score
    else:   # not learning
        trained_folder = f'input_{total_products}_workpiece/trained/'
        trained_workpiece = 20
        trained_filename = f'independent_qc_training_{trained_workpiece}_workpiece_{input_filename}.xlsx'
        trained_df = pd.read_excel(f'{trained_folder}/{trained_filename}')
        if score_type == "score":
            score_list = [trained_df[f"wc_{i + 1}_score"].iloc[-1] for i in range(total_workcells)]
        elif score_type == "capability":
            score_list = actual_capability_df[f"input_{input_num}"].to_list()

# Create output path
if not os.path.exists(output_folder):
    os.makedirs(output_folder)    # Create target Directory
    print("Directory ", output_folder,  " Created ")
else:
    print("Directory ", output_folder,  " already exists")


def instantiate_objects(threshold, consensus_mode, score_list, learning):
    # Instantiate objects
    print("Instantiating objects...")
    # Instantiate objects
    quality_controllers = {
        f"wc_{i + 1}": Workcell(
            step_idx=i + 1,
            id=f"wc_{i + 1}",
            ip=ip,
            port=port,
            qc_id=f"wc_{i + 1}",
            consensus_mode=consensus_mode,
            threshold=threshold,
            score=1,
            learning=False
        )
        for i in range(total_workcells)
    }
    print("Completed instantiating objects")
    workpieces = {
        f"wp_{i+1}": Workpiece(id=f"wp_{i+1}")
        for i in range(total_products)
    }
    transporter = Transporter()
    print("Objects instantiated...")
    return quality_controllers, workpieces, transporter


def simulate(quality_controllers, workpieces, transporter):
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

    # Each workpiece
    for wp_id, wp_inst in workpieces.items():
        print(f"For workpiece {wp_id},")
        workpiece_df = input_worksheet.loc[input_worksheet['workpiece_id'] == wp_id]  # Rows of that wp id

        # Initialize data logging for each workpiece
        data = {
            "production_index": [],
            "step_idx": [],
            "production_workcell": [],
            "qc": [],
            "consent": [],
            "winner_qc_list": [],
            "score": [],
            "production_time": [],
            "transport_time": [],
            "inspection_time": [],
            "network_time": [],
            "qc_results": [],
            "actual_quality": [],
        }
        df = csv_functions.create_df(data)
        output_filename = f"{output_folder}/{wp_id}_qc_{score_type}_{threshold}.csv"

        # Each production step
        for row in workpiece_df.itertuples():  # workpiece_df haven't reached last production step
            print(f"    Row {row.Index}: at step {row.step_idx}")
            data = dict()    # Reset
            transport_time = list()      # Reset
            wc_time = list()
            bc_time = list()      # Reset
            qc_time = list()      # Reset
            score_list = list()     # Reset
            error_list = list()     # Reset
            in_winner_counter_list = list()     # Reset
            in_qc_counter_list = list()     # Reset
            qc_list = list()      # Reset
            capability_list = list()      # Reset
            winner_qc_list = list()     # Reset
            winner_score_list = list()     # Reset
            winner_results_list = list()     # Reset
            consent_list = list()     # Reset
            consent = False  # Reset
            # Extract actual quality
            actual_quality_dict = literal_eval(row.actual_quality)
            actual_quality = max(actual_quality_dict, key=actual_quality_dict.get)  # Key with max value in dict
            execution_info = {
                "production_time": row.production_time,
                "produced_by": row.workcell_id,
                "min_qc_required": len(actual_quality_dict) + 1
            }
            # Log production information
            data["production_index"] = row.Index
            data["step_idx"] = row.step_idx
            data["production_workcell"] = row.workcell_id
            data["actual_quality"] = actual_quality
            # Do quality control
            while not consent:  # Until consent is achieved for each production step
                production_time = None  # Place holder
                travel_time = None  # Place holder
                network_time = None  # Place holder
                inspection_time = None  # Place holder
                qc_id = None  # Place holder
                score = None  # Place holder
                score_error = None  # Place holder
                in_winner_counter = None  # Place holder
                in_qc_counter = None  # Place holder
                actual_capability = None  # Place holder
                winner_dict = dict()  # Place holder

                if wp_inst.sink is not None and wp_inst.source is not None:  # Workpiece needs transportation
                    print(f"        Travelling from {wp_inst.source} to {wp_inst.sink}...")
                    # Start travel
                    if wp_inst.location is not None:  # Move workpiece out of location
                        travel_time, travel_dist, splitter = transporter.start_travel(wp_inst)
                    # In travel
                    else:
                        if transporter.in_travel(wp_inst, time_interval):  # still can count down with time_interval
                            continue
                        else:  # End travel
                            transporter.end_travel(wp_inst)

                if wp_inst.sink is None and wp_inst.source is None:  # Workpiece does not need transportation
                    # Get next production step
                    if wp_inst.status == "awaiting next step":
                        wc_inst = quality_controllers[row.workcell_id]
                        wp_inst.step_idx = row.step_idx
                        wp_inst.source = wp_inst.location
                        wp_inst.sink = row.workcell_id
                        wp_inst.status = "awaiting production"
                        wc_inst.production_workpiece = wp_id
                    elif wp_inst.status == "awaiting production":
                        # Start production
                        print(f"        Production.")
                        current_wc_inst = quality_controllers[row.workcell_id]
                        current_wc_inst.production_workpiece = wp_inst
                        # Assume done production
                        wp_inst.status = "awaiting inspection"
                        current_wc_inst.pass_to_quality_controller(execution_info)
                        production_time = row.production_time
                    elif wp_inst.status == "awaiting inspection":     # Awaiting inspection
                        # Start inspection
                        qc_id = wp_inst.location
                        qc_inst = quality_controllers[qc_id]
                        qc_inst.add_to_inspection(wp_inst)
                        qc_inst.start_inspection(row.step_idx, inspection_time=getattr(row, f"qc_{qc_id}_time"))
                        print(f"        Inspection time will end {getattr(row, f'qc_{qc_id}_time')} later.")
                        continue    # Don't log info
                    elif wp_inst.status == "in inspection":   # Still in inspection
                        qc_id = wp_inst.location
                        qc_inst = quality_controllers[qc_id]
                        if qc_inst.in_inspection(time_interval):    # Still can count down with time_interval
                            continue
                        else:   # Count down is negative, need to stop inspection
                            # End inspection
                            inspection_results = literal_eval(getattr(row, f"qc_{qc_id}_results"))
                            inspection_time, network_time, consent, winner_dict = \
                                qc_inst.end_inspection(
                                    inspection_results=inspection_results,
                                    execution_info=execution_info
                                )
                            # Prepare qc data (no consent)
                            score = qc_inst.score
                            score_error = qc_inst.get_score_error()
                            in_winner_counter = qc_inst.in_winner_counter
                            in_qc_counter = qc_inst.in_qc_counter
                            actual_capability = getattr(row, f"qc_{qc_id}_confidence")
                            if consent:
                                print(f"        Production time: {wc_time}")
                                print(f"        Transport time: {transport_time}")
                                print(f"        Network time: {bc_time}")
                                print(f"        Inspection time: {qc_time}")
                                print(f"        Sequence of qc: {winner_dict['qc_list']}")
                                print(f"        Winners: {winner_dict['winner_qc_list']}")
                                print(f"        Score: {winner_dict['score']}")
                                print(f"        Results: {winner_dict['results']}")
                                # Log qc data (no consent)
                                data["qc_score"] = score_list
                                data["score_error"] = error_list
                                data["in_winner_counter"] = in_winner_counter_list
                                data["in_qc_counter"] = in_qc_counter_list
                                data["qc_capability"] = capability_list
                                # Log qc data (consent)
                                data["production_time"] = wc_time
                                data["transport_time"] = transport_time
                                data["network_time"] = bc_time
                                data["inspection_time"] = qc_time
                                data["qc"] = qc_list
                                data["consent"] = consent_list
                                data["winner_qc_list"] = winner_qc_list
                                data["score"] = winner_score_list
                                data["qc_results"] = winner_results_list

                # Append each qc data into respective list
                transport_time.append(travel_time)
                wc_time.append(production_time)
                bc_time.append(network_time)
                qc_time.append(inspection_time)
                score_list.append(score)
                error_list.append(score_error)
                in_winner_counter_list.append(in_winner_counter)
                in_qc_counter_list.append(in_qc_counter)
                capability_list.append(actual_capability)
                qc_list.append(qc_id)
                winner_qc_list.append(winner_dict.get("winner_qc_list", None))
                winner_score_list.append(winner_dict.get("score", None))
                winner_results_list.append(winner_dict.get("results", None))
                consent_list.append(consent)
                time.sleep(.1)
            # Consent achieved for that row
            # Append log data to dataframe
            df = csv_functions.append_to_df(df, data)
            # print(df)
        # Write dataframe into csv
        csv_functions.write_csv(output_filename, df)
    print("====================================== PROGRAM END ======================================")


if __name__ == '__main__':
    qc, wp, trans = instantiate_objects(threshold, consensus_mode, score_list, learning)
    add_routes(qc, threshold)
    t = Thread(
        target=simulate,
        args=(qc, wp, trans, )
    )
    t.start()
    app.run(host='0.0.0.0', port=port)
