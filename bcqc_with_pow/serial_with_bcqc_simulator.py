"""
Project Title: BCQC 1.0
Program title: Serial Manufacturing with BCQC
This program simulates scenarios of quality control (QC) of Computer Desktops assembly during production.
QC is performed on virtual data in peer-to-peer manner using blockchain and Proof of Work (PoW). The assembly process
is conducted in pre-defined serial sequence, which means each product can only take the step that was pre-defined
without options.
Written by Shreya Sinha
"""
import pandas
from random import *
import requests
from flask import Flask, jsonify, request

# Import variables needed for each step [Parts/Production Time]
scenario_number = input("Enter scenario number [only 2/3/4]")
scenario_number = int(scenario_number)
input_filename = f'Data_Sheet_pow_scenario_{scenario_number}.csv'
output_filename = f"results/Scenario {scenario_number}.xlsx"

application = Flask(__name__)
variables = pandas.read_csv(input_filename)
# Import Part UID used in each step
part_id = pandas.read_csv('PartUID_Sheet.csv')
# Keeps track of Part Number used from csv file
part_id_counter = []
part_id_counter.extend([0] * 30)
# Part List
part_list = ['Cover', 'Intrusion_Switch', 'WLAN_Card', 'Front_Bezel', 'Expansion_Card', 'Memory_Card',
             'CoinCell_Battery', 'Hard_Drive', 'Optical_Drive', 'Power_Supply', 'Heat_Sink_Assembly', 'Processor',
             'Processor_Socket', 'System_Fan', 'Thermal_Sensor', 'Power_Switch', 'IO_Panel', 'System_Board', 'Screws',
             'Grommets', 'Power_Cable', 'Data_Cable', 'WLAN_Cable', '4pin_Power_Cable', '8pin_Power_Cable', 'Fan_Cable',
             'Captive_Screws', 'Thermal_Sensor_Cable', 'USB_Cable', 'N_A']
total_number_of_steps = 17

# HTTP Transfer over Blockchain
Post_Transaction = 'http://localhost:5000/transactions/new'
Mine_Transaction = 'http://localhost:5000/mine'

total_number_of_parts = input("Enter number of parts to make ")
total_number_of_parts = int(total_number_of_parts)


# *************************** FUNCTIONS *************************************************
# Create a block function - parameters: part names, part ids, timestamp,

def get_step_status(thr):
    """
    Determines if a manufacturing process is carried out successfully or not
    :return: Step status
    :rtype: string
    """
    probability = thr
    if probability < 50:
        return 'Fail'
    else:
        return 'Pass'


def get_threshold():
    """
    Determine threshold of accuracy for each iteration of production
    :return:
    :rtype:
    """
    from numpy.random import choice
    elements = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    for R in range(0, total_number_of_parts):
        for C in range(0, total_number_of_steps):
            threshold_array[R][C] = choice(elements)
    return


def get_new_threshold(part, step):
    from numpy.random import choice
    elements = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    threshold_array[part][step] = choice(elements)
    return


def post_blockchain_data(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    """
    Creates a JSON file format payload to send over the HTTP network and complete addition of a valid block to chain
    """
    step_text = str(step)
    part1_text = str(part1)
    partid1_text = str(partid1)
    part2_text = str(part2)
    partid2_text = str(partid2)
    part3_text = str(part3)
    partid3_text = str(partid3)
    part4_text = str(part4)
    partid4_text = str(partid4)
    status_text = str(status)
    payload = "{\n    \"step_number\":\"" + step_text + "\", \"part1\":\"" + part1_text + "\",\"partid1\":\"" + partid1_text + "\", \"part2\":\"" + part2_text + "\", \"partid2\":\"" + partid2_text + "\", \"part3\":\"" + part3_text + "\", \"partid3\":\"" + partid3_text + "\", \"part4\":\"" + part4_text + "\", \"partid4\":\"" + partid4_text + "\", \"status\":\"" + status_text + "\"}"
    headers = {
        'Content-Type': "application/json",
    }
    response = requests.request("POST", Post_Transaction, data=payload, headers=headers)
    print(response.text)
    return


def get_production_time(step):
    """
    Determines the production time for a step between the given upper and lower bound in the excel for a given step
    :param step: manufacturing process
    :return: production time
    """
    time_min = variables.loc[step, 'Production_Time_Min']
    time_max = variables.loc[step, 'Production_Time_Max']
    production_time = randint(time_min, time_max)
    return production_time


def get_validator_type():
    """
    Gather all unique validator type.
    """
    validator_type = set(variables['Validator_Type'].values)
    return validator_type


def get_validation_time(step):
    """
    Determine validation time for a step based on a given lower and upper limit
    Only human validators take extra time for validation as they can only perform one task at a time
    """
    if "Human" in variables['Validator_Type'].values:
        time_min = variables.loc[step, 'Validation_Time_Min']
        time_max = variables.loc[step, 'Validation_Time_Max']
        validation_time = randint(time_min, time_max)
    else:
        validation_time = 0
    return validation_time


def secondary_validation(thr):
    """
    Determines the part quality of a part/step that has completed production and determines if all the other validators
    in the network agree with the primary validator.
    """

    elements = ["Good", "Poor"]
    weights = [thr / 100, (100 - thr) / 100]
    from numpy.random import choice
    for i in range(len(quality_array)):
        quay = choice(elements, p=weights)
        # quality_number[i] = quay
        quality_array[i] = quay
    number_good = quality_array.count("Good")

    # greater than 50% of validators give a pass status
    # sec_validation_correctness(quality_array, quality_number)
    if number_good > 8:
        return "Good"
    else:
        return "Poor"


def sec_validation_correctness():
    """
    Determine the actual status of each process to compare with simulation results and understand the accuracy of
    multiple blockchain validations
    """
    # Each validator has 50% accuracy of correct secondary validation
    # Array that tabulates validation status of each validator for each process
    correctness = [0]*17
    count = 0
    for xx in range(0, total_number_of_parts):
        for yy in range(0, total_number_of_steps):
            for quality in range(0, len(correctness)):
                # Find the probabilities that each validator gives an erroneous validation
                correctness[quality] = randint(1, 100)
                if correctness[quality] < 50:
                    # 50% chance that validation is incorrect
                    count += 1
            print("Count ", count)
            if count > 7:
                # More than 50% of validators validated incorrectly
                actual_sec_validation[xx][yy] = 'Poor'
            else:
                actual_sec_validation[xx][yy] = 'Good'
            correctness = [0]*17
            count = 0
    return


def calculate_waste_percentage():
    """
    Calculating waste percentage of producing n assemblies based on reworks
    :return:
    :rtype:
    """
    re = 0
    for aa in range(0, total_number_of_parts):
        for bb in range(0, total_number_of_steps):
            re += rework[aa][bb]
    print(re)
    waste_p = re/(total_number_of_steps*total_number_of_parts)
    return waste_p


def write_to_excel(step, part, production_time, validation_time, validator_type, time_delay, part1, partuid1, part2,
                   partuid2,
                   part3, partuid3, part4, partuid4, timestamp, thr, act_status, qual, sec_status, sec_correctness):
    # INPUTS - step number, production time, validation time, validator type, parts, part ids, timestamp,
    # validation_status, sec_validation status, WRITER COUNTER FOR START ROW
    # how to determine row in which to add data
    # How to determine sheet in which to add data
    # Keep appending and write all at one go
    temp_dict = {'Assembly_Number': part, 'Step_Number': step,
                 'Production_Time': production_time, 'Validation_Time': validation_time,
                 'Validator_Type': validator_type, 'Delay': time_delay, 'Part1': part1,
                 'Part1_ID': partuid1, 'Part2': part2, 'Part2_ID': partuid2, 'Part3': part3, 'Part3_ID': partuid3,
                 'Part4': part4, 'Part4_ID': partuid4, 'Time_Stamp': timestamp, 'Threshold': thr,
                 'Actual_Part_Status': act_status, 'Sec Validator Responses': qual,
                 'Secondary_Validation_Status': sec_status}
    dictionary.append(temp_dict)

# Check step 1 function for all n steps - checks correct part used, checks ID of part, checks status,
# checks timestamp and hash
def check_step_1(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 1 and part1 == 'System_Board' and part2 == 'Screws' and status == 'Pass':
        return "Valid"
    else:
        return "Invalid"


def check_step_2(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 2 and part1 == 'IO_Panel' and part2 == 'Screws' and part3 == 'USB_Cable' and part4 == 'Data_Cable' and \
            status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_3(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 3 and part1 == 'Power_Switch' and part2 == 'Power_Cable' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_4(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 4 and part1 == 'Thermal_Sensor' and part2 == 'Thermal_Sensor_Cable' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_5(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 5 and part1 == 'System_Fan' and part2 == 'Grommets' and part3 == 'Fan_Cable' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_6(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 6 and part1 == 'Processor' and part2 == 'Processor_Socket' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_7(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 7 and part1 == 'Captive_Screws' and part2 == 'Heat_Sink_Assembly' and part3 == 'Fan_Cable' and \
            status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_8(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 8 and part1 == 'Power_Supply' and part2 == '4pin_Power_Cable' and part3 == '8pin_Power_Cable' and part4 == 'Screws' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_9(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 9 and part1 == 'Optical_Drive' and part2 == 'Power_Cable' and part3 == 'Data_Cable' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_10(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 10 and part1 == 'Hard_Drive' and part2 == 'Power_Cable' and part3 == 'Data_Cable' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_11(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 11 and part1 == 'CoinCell_Battery' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_12(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 12 and part1 == 'Memory_Card' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_13(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 13 and part1 == 'Expansion_Card' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_14(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 14 and part1 == 'Front_Bezel' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_15(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 15 and part1 == 'WLAN_Card' and part2 == 'WLAN_Cable' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_16(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 16 and part1 == 'Intrusion_Switch' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def check_step_17(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    if step == 17 and part1 == 'Cover' and status == 'Pass':
        return 'Valid'
    else:
        return 'Invalid'


def smart_contract_validation(step, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status):
    switcher = {
        0: check_step_1(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        1: check_step_2(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        2: check_step_3(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        3: check_step_4(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        4: check_step_5(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        5: check_step_6(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        6: check_step_7(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        7: check_step_8(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        8: check_step_9(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        9: check_step_10(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        10: check_step_11(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        11: check_step_12(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        12: check_step_13(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        13: check_step_14(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        14: check_step_15(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        15: check_step_16(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status),
        16: check_step_17(step + 1, part1, partid1, part2, partid2, part3, partid3, part4, partid4, status)
    }
    return switcher.get(step, "NOT VALID")


# ******************************* MAIN **************************************************


# Initialise variables needed
# Time to complete production of a single part
time_stamp = 0
step_number = 0
parts = 0
delay = 0
# Data analysis parameters
failed_pri_validation = 0
failed_sec_validation = 0
rows, cols = (total_number_of_parts, total_number_of_steps)
rework = [[0 for i in range(cols)] for j in range(rows)]
quality_array = [""] * total_number_of_steps
sec_validation_array = [[0 for i in range(cols)] for j in range(rows)]
actual_sec_validation = [['' for i in range(cols)] for j in range(rows)]
writer = pandas.ExcelWriter(output_filename, engine='xlsxwriter')
dictionary = []
write_counter = 1
# Stores the accuracy percentage for that iteration
threshold = 0
threshold_array = [[0 for i in range(cols)] for j in range(rows)]
# sec_validation_correctness()
get_threshold()
print(threshold_array)
while parts < total_number_of_parts:
    print('Part Number:')
    print(parts)

    while step_number < total_number_of_steps:
        # print("Step ", step_number)
        # Index 1 is the name of Part 1
        index1 = variables.loc[step_number, 'Part1']
        # Gives the index of Part List in part_id_counter array
        w = part_list.index(index1)
        index2 = variables.loc[step_number, 'Part2']
        x = part_list.index(index2)
        index3 = variables.loc[step_number, 'Part3']
        y = part_list.index(index3)
        index4 = variables.loc[step_number, 'Part4']
        z = part_list.index(index4)
        # find index of this part in the Parts List array and increment counter in part_id_counter for this index
        # instead of 1, the first variable is the part_id_counter of index1
        # need to increment part_id_counter[x] each time a part is used
        uid1 = part_id.loc[part_id_counter[w], index1]
        uid2 = part_id.loc[part_id_counter[x], index2]
        uid3 = part_id.loc[part_id_counter[y], index3]
        uid4 = part_id.loc[part_id_counter[z], index4]
        # Get accuracy rate for this step and use it to calculate step status
        threshold = threshold_array[parts][step_number]
        # print("Threshold", threshold)
        step_status = get_step_status(threshold)
        variables.loc[step_number, 'Production_Time'] = get_production_time(step_number)
        variables.loc[step_number, 'Validation_Time'] = get_validation_time(step_number)
        # Calculations for time taken to produce a part accounting for bottlenecks
        if step_number == 0:
            if step_status == 'Pass':
                time_stamp += (parts + 1) * variables.loc[step_number, 'Production_Time']
                variables.loc[step_number, 'Projected_Next_Production_Time'] = time_stamp
                # print("Here 1", time_stamp)

            else:
                time_stamp += variables.loc[step_number, 'Production_Time']
                variables.loc[step_number, 'Projected_Next_Production_Time'] = time_stamp
                # time_stamp += variables.loc[step_number, 'Validation_Time']
                # print("Here 2", time_stamp)

        else:

            if time_stamp < variables.loc[step_number, 'Projected_Next_Production_Time']:
                # Moving from a fast to slow step gives a bottleneck, this affects future part production for that step
                delay = variables.loc[step_number, 'Projected_Next_Production_Time'] - variables.loc[
                    step_number - 1, 'Projected_Next_Production_Time']
                variables.loc[step_number, 'Projected_Next_Production_Time'] = max(
                    variables.loc[step_number - 1, 'Projected_Next_Production_Time'],
                    variables.loc[step_number, 'Projected_Next_Production_Time']) + variables.loc[
                                                                                   step_number, "Production_Time"]
                print("Delay ", step_number, " ", delay)
                time_stamp += delay + variables.loc[step_number, 'Production_Time']
                # print("Here 3", time_stamp)

            else:
                # If there is no bottleneck the workcell is free when part arrives and only production time is needed
                variables.loc[step_number, 'Projected_Next_Production_Time'] = max(
                    variables.loc[step_number - 1, 'Projected_Next_Production_Time'],
                    variables.loc[step_number, 'Projected_Next_Production_Time']) + variables.loc[
                                                                                   step_number, "Production_Time"]
                time_stamp += variables.loc[step_number, 'Production_Time']
                # print("Here 4", time_stamp)
        time_stamp += variables.loc[step_number, 'Validation_Time']
        print("After Validation ", time_stamp)
        # Create block for posting to all other nodes
        # post_blockchain_data(step_number, index1, uid1, index2, uid2, index3, uid3, index4, uid4, step_status)
        # Check the data in the bloc using helper functions [Smart Contract simulation]
        # Primary Validation
        block_status = smart_contract_validation(step_number, index1, uid1, index2, uid2, index3, uid3, index4, uid4,
                                                 step_status)
        # Secondary Validation
        sec_validation_status = secondary_validation(threshold)
        sec_validation_array[parts][step_number] = sec_validation_status
        validator_type = get_validator_type()

        # Save all data generated to excel sheet for data analysis
        write_to_excel(step_number, parts, variables.loc[step_number, 'Production_Time'],
                       variables.loc[step_number, 'Validation_Time'],
                       validator_type, delay, index1, uid1, index2, uid2, index3, uid3,
                       index4, uid4, time_stamp, threshold, step_status, quality_array, sec_validation_status,
                       actual_sec_validation[parts][step_number])

        if step_status == 'Fail': # randomize parameters in case of rework
            get_new_threshold(parts, step_number)
            variables.loc[step_number, 'Production_Time'] = get_production_time(step_number)
            variables.loc[step_number, 'Validation_Time'] = get_validation_time(step_number)

        print("Time Stamp " + str(time_stamp))
        # Mine transaction if block is validated, else return to previous step [step--]
        if block_status == 'Valid' and sec_validation_status == 'Good':
            # h = requests.get(url=Mine_Transaction)
            print("Step ", (step_number + 1), " is successful " + "Time at addition of block ", time_stamp)

        else:
            # Rework array tracks the number of times secondary validation fails on a part
            rework[parts][step_number] += 1
            print("Step ", (step_number + 1), " is unsuccessful ")
            step_number = step_number - 1
            if sec_validation_status == "Poor":
                print("Part Quality poor by Secondary Validation")

        # Increment all variables for next iteration - Even if step is unsuccessful previous parts cannot be reused
        part_id_counter[w] = part_id_counter[w] + 1
        part_id_counter[x] = part_id_counter[x] + 1
        part_id_counter[y] = part_id_counter[y] + 1
        part_id_counter[z] = part_id_counter[z] + 1
        step_number = step_number + 1   # Change to step_number = next_step when parallel scenario implemented
        quality_array = [""] * (total_number_of_steps - 1)

        # Calculation for data analysis - parts that fail primary/secondary validation from blockchain consensus
        if step_status == "Fail":
            failed_pri_validation += 1
        if step_status == 'Pass' and sec_validation_status == 'Poor':
            failed_sec_validation += 1

            # Waste percentage calculation - for each part that fails secondary validation, add number of
            # sub-components in that step that are re-worked
    parts = parts + 1
    time_stamp = 0  # do not make timestamp 0 for parallel scenario
    step_number = 0

df = pandas.DataFrame(dictionary)
df.to_excel(writer, sheet_name='Test1')
writer.save()
print("Failed Primary Validation ", failed_pri_validation)
print("Failed Secondary Validation ", failed_sec_validation)
print("Rework array", rework)
print("Number of total reworks", sum(sum(rework, [])))
print(sec_validation_array)
print(actual_sec_validation)
print("Waste Percentage", calculate_waste_percentage())
