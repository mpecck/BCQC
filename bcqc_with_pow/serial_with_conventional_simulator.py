"""
Project Title: BCQC 1.0
Program title: Serial Manufacturing with Conventional QC
This program simulates scenarios of quality control (QC) of Computer Desktops assembly during production.
QC is performed on virtual data using conventional method, which means a single inspector carries out each QC process
at pre-defined check points of the production.
Written by Shreya Sinha
"""
from random import *
import pandas
from numpy.random import choice

# Import variables needed for each step [Parts/Production Time]
scenario_number = input("Enter scenario number [only 1] ")
scenario_number = int(scenario_number)
input_filename = f'Data_Sheet_pow_scenario_{scenario_number}.csv'
output_filename = f"results/Scenario {scenario_number}.xlsx"

total_number_of_parts = input("Enter number of parts to make ")
total_number_of_parts = int(total_number_of_parts)

parts = 0
step_number = 0
total_number_of_steps = 17


# Import variables needed for each step [Parts/Production Time]
variables = pandas.read_csv(input_filename)
# Variables to conduct data analysis
good = 0
poor = 0
pri_good_status = 0
pri_poor_status = 0
sec_good_status = 0
sec_poor_status = 0
wrong_validation = 0


# *************************** FUNCTIONS *************************************************


def actual_part_status(thr):
    """
    Determines if a manufacturing process is carried out successfully or not
    :return: Step status
    :rtype: string
    """
    probability = thr
    if probability < 50:
        return 'Poor'
    else:
        return 'Good'


def get_threshold():
    """
    Determine threshold of accuracy for each iteration of production
    :return:
    :rtype:
    """
    elements = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    return choice(elements)


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


def calculate_timestamp(part, step):
    """
    Calculates the time taken to complete the production of a part
    :param part: assembly number/product
    :param step: manufacturing process being carried out
    :return: time at which production was completed
    """
    if part == 0:
        # Calculate Timestamp for current step
        if step == 0:
            time_stamp[part][step] += variables.loc[step, 'Production_Time']
            # print("Part number: ", part, " step number: ", step + 1, " Timestamp1: ",
            # time_stamp[part][step])
        else:
            time_stamp[part][step] += variables.loc[step, 'Production_Time'] + time_stamp[part][step - 1]
            # print("Part number: ", part, " step number: ", step + 1, " Timestamp2: ",
            # time_stamp[part][step])
    else:
        if step == 0:
            time_stamp[part][step] += variables.loc[step, 'Production_Time'] + time_stamp[part - 1][step]
            # print("Part number: ", part, " step number: ", step + 1, " Timestamp3: ",
            # time_stamp[part][step])
        else:  # do not add second part if it is a rework step
            time_stamp[part][step] += variables.loc[step, 'Production_Time'] + max(time_stamp[part - 1][step],
                                                                                   time_stamp[part][step - 1])
            # print("Part number: ", part, " step number: ", step + 1, " Timestamp4: ",
            # time_stamp[part][step])

    time_stamp[part][step] += variables.loc[step, 'Validation_Time']
    return


def get_validation_time(step):
    """
    Determine validation time for a step based on a given lower and upper limit
    Only human validators take extra time for validation as they can only perform one task at a time
    """
    if variables.loc[step, 'Validator_Type'] == "Human":
        time_min = variables.loc[step, 'Validation_Time_Min']
        time_max = variables.loc[step, 'Validation_Time_Max']
        validation_time = randint(time_min, time_max)
    else:
        validation_time = 0
    return validation_time


def get_step_status(thr):
    """
    Finds the actual part status of an assembly to compare with simulation results
    """
    elements = ["Pass", "Fail"]
    weights = [thr / 100, (100 - thr) / 100]
    step_status_ = choice(elements, p=weights)
    return step_status_


def calculate_good(part_number):
    good_no = 0
    for i in range(0, total_number_of_steps):
        if quality[part_number][i] == 'Good':
            good_no += 1
    return good_no


def calculate_poor(part_number):
    poor_no = 0
    for i in range(0, total_number_of_steps):
        if quality[part_number][i] == 'Poor':
            poor_no += 1
    return poor_no


def count_2d(R, C):
    q = 0
    for c in range(0, C):
        if quality[R][c] == 'Good' or quality[R][c] == 'Poor':
            q += 1
    return q


def calculate_incorrect_validation(part_number):
    """
    Determining the discrepancy in secondary validation by comparing with the randomly generated actual status of
    manufacturing processes.
    :return: number of processes that have been incorrectly validated
    :rtype: integer
    """
    bf = 0  # break factor for incrementing actual row number
    act_row = 0
    incorrect_validation = 0
    for nr in range(0, part_number - 1):
        for nc in range(0, total_number_of_steps - 1):
            # print("nr", nr, "nc", nc, "act row", act_row)
            if count_2d(nr, total_number_of_steps) != 17:
                bf = 1
                # print("Count", count_2d(nr, total_number_of_steps))
                break

            if quality[nr][nc] != actual_quality[act_row][nc]:
                # print("Actual", actual_quality[act_row][nc], "Quality", quality[nr][nc], "act row", act_row)
                incorrect_validation += 1
        if bf == 0:
            act_row += 1
        else:
            bf = 0

    return incorrect_validation


def count_quality():
    """
    Determining if an assembly process is completed (all 17 steps)
    :return: number of steps completed in the assembly of a part
    :rtype: integer
    """
    proc = 0
    for xx in range(0, total_number_of_parts):
        for yy in range(0, total_number_of_steps):
            if quality[xx][yy] == 'Good' or quality[xx][yy] == 'Poor':
                proc += 1
    return proc


def write_to_excel(step, part, rework, production_time, validation_time, validator_type, timestamp, thresh,
                   cum_threshold, pri_status, stat):
    # INPUTS - step number, production time, validation time, validator type, parts, part ids, timestamp,
    # validation_status, sec_validation status, WRITER COUNTER FOR START ROW
    # how to determine row in which to add data
    # How to determine sheet in which to add data
    # Keep appending and write all at one go
    temp_dict = {'Assembly_Number': part, 'Step_Number': step, 'Rework': rework,
                 'Production_Time': production_time, 'Validation_Time': validation_time,
                 'Validator_Type': validator_type, 'Time_Stamp': timestamp, 'Threshold': thresh,
                 'Cumulative_Threshold': cum_threshold, 'Primary_Validation_Status': pri_status, 'Actual Part Status': stat}
    dictionary.append(temp_dict)
    return


# write actual part status to dataframe
# Append the Actual sec validation status to col[given=9] row where part, step has status "Good" with no header

# Initialise a 2D array to store all timestamps
rows, cols = (total_number_of_parts, total_number_of_steps)
time_stamp = [[0 for i in range(cols)] for j in range(rows)]
# 2D Array to store actual part quality
actual_quality = ['' for i in range(cols)]
# 2D Array to store the part status after each step simulation
quality = [['' for i in range(cols)] for j in range(rows)]
# 0 - part cannot be reworked. 1 part can be reworked
checkpoint = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
writer = pandas.ExcelWriter(output_filename, engine='xlsxwriter')
dictionary = []
write_counter = 1
delay = 0
rew = 0  # to prevent double counting in timestamp calculations
prev_re = 0  # if the previous round was a rework then current timestamp does not depend on timestamp of prev step
# Simulation Start
cum_threshold = 0
cum_actual_quality = "Good"
log_actual_quality = None
while parts < total_number_of_parts:
    # print('Part Number:')
    # print(parts)
    # Calculate the actual part statuses before starting simulation
    while step_number < total_number_of_steps:
        # Determine step pass/fail
        threshold = get_threshold()
        actual_quality = actual_part_status(threshold)
        if actual_quality == "Poor":
            cum_actual_quality = "Poor"
        if cum_threshold != 0:
            cum_threshold = (cum_threshold + threshold)/2   # Find median
        else:
            cum_threshold = threshold
        rework = None
        # Determine Production Time
        variables.loc[step_number, 'Production_Time'] = get_production_time(step_number)
        # Validate workpiece
        if checkpoint[step_number] == 1:
            step_status = get_step_status(cum_threshold)
            variables.loc[step_number, 'Validation_Time'] = get_validation_time(step_number)
        else:
            step_status = None
            variables.loc[step_number, 'Validation_Time'] = 0
        # print("Production time ", variables.loc[step_number, 'Production_Time'])
        # print("Validation time ", variables.loc[step_number, 'Validation_Time'])
        # print("Step Status :", step_status)

        # Primary Validation status
        if step_status is not None:
            log_actual_quality = cum_actual_quality
            if step_status == 'Pass':
                part_quality = 'Good'
                pri_good_status += 1
            else:
                # rework = choice([True, False])
                if cum_threshold < 25:
                    rework = False
                else:
                    rework = True
                part_quality = 'Poor'
                pri_poor_status += 1
        else:
            log_actual_quality = None
        if rew == 0 and prev_re == 0:
            calculate_timestamp(parts, step_number)
        if prev_re == 1:
            time_stamp[parts][step_number] += variables.loc[step_number, 'Production_Time']
            time_stamp[parts][step_number] += variables.loc[step_number, 'Validation_Time']
            prev_re = 0
            # print(parts, " ", step_number)
        # Save all data generated to excel sheet for data analysis
        write_to_excel(step_number, parts, rework, variables.loc[step_number, 'Production_Time'],
                       variables.loc[step_number, 'Validation_Time'],
                       variables.loc[step_number, 'Validator_Type'], time_stamp[parts][step_number], threshold,
                       cum_threshold, step_status, log_actual_quality)

        # Check if part needs to be reworked or move to next step
        if step_status is not None:  # Validation step
            cum_threshold = 0
            cum_actual_quality = "Good"
            if step_status == 'Pass':
                quality[parts][step_number] = step_status
                step_number += 1
                rew = 0
            else:
                if rework:
                    # This part can be reworked
                    quality[parts][step_number] = 'Good'
                    print("Before", time_stamp[parts][step_number])
                    print("Production Time added",  variables.loc[step_number, 'Production_Time'])
                    print("Validation Time added", variables.loc[step_number, 'Validation_Time'])
                    time_stamp[parts][step_number] += variables.loc[step_number, 'Production_Time']
                    time_stamp[parts][step_number] += variables.loc[step_number, 'Validation_Time']
                    print("After rework timestamp", time_stamp[parts][step_number])
                    rew = 1
                    prev_re = 1
                    good += 1
                    step_number = step_number
                else:
                    # This part has been scrapped and a new part must be made
                    total_number_of_parts += 1
                    # Copy previous part's timestamps into the array for scrapped part to calculate subsequent timestamp
                    """
                    if parts != 0:
                        for i in range(step_number + 1, total_number_of_steps):
                            time_stamp[parts][i] = time_stamp[parts - 1][i]
                    """

                    # Append a row to the timestamp array for the new part
                    rew = 0
                    row = []
                    row.extend([0] * total_number_of_steps)
                    time_stamp = numpy.vstack([time_stamp, row])
                    # Add part quality to the array for secondary validation
                    quality[parts][step_number] = step_status
                    row = []
                    row.extend([''] * total_number_of_steps)
                    quality = numpy.vstack([quality, row])
                    step_number = 0
                    break
        else:
            step_number += 1
            rew = 0
    cum_threshold = 0
    step_number = 0
    parts += 1
    delay = 0
df = pandas.DataFrame(dictionary)
df.to_excel(writer, sheet_name='Test1')
writer.save()
print(time_stamp)
# print(quality)
# print("Parts", parts)
# # wrong_validation = calculate_incorrect_validation(parts)
# # print("Incorrect Validation:", wrong_validation)
# print("Count quality", count_quality())
# print("Good: ", good, "Pri_Good: ", pri_good_status, "Poor: ", poor, "Pri_Poor", pri_poor_status)


