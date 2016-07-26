'''
A naive parser to display energy consumption information of a G-code file
with aggressive power-gating
'''

import re
import os
import csv

TIME_TO_PRINT = 0
FILAMENT_CONSUMPTION = 0

TOTAL_MOVEMENTS = 0

TOTAL_ELECTRICITY_COST = 0

def preprocess_lines(f):
    for l in f:
        line = l.rstrip()
        if line:
            yield_line = True
            # Cleaning the input
            if ';TIME_ELAPSED' in line:
                global TIME_TO_PRINT
                TIME_TO_PRINT = re.findall("\d+\.\d+", line)
                yield_line = False
            if 'G1' in line:
                global FILAMENT_CONSUMPTION
                FILAMENT_CONSUMPTION = re.findall("\d+\.\d+$", line)
            if 'M1' in line or ';' in line:
                yield_line = False
            if 'F' in line:         #Processing only most popular Feedrate
                if 'F1800' not in line and 'F7200' not in line:
                    yield_line = False
            if yield_line:
                yield line

def electricity_cost_calculator(filename):
    f_1800_extrude_count = 0
    f_7200_extrude_count = 0

    f_1800_align_count = 0
    f_7200_align_count = 0

    is_in_printing = False
    is_in_f1800_flag = False

    with open(filename) as f:
        for line in preprocess_lines(f):

            if 'G0' in line:
                is_in_printing = False

            if 'G1' in line:
                is_in_printing = True

            if is_in_printing:
                if is_in_f1800_flag:
                    f_1800_extrude_count += 1
                else:
                    f_7200_extrude_count += 1

                if 'F1800' in line:
                    is_in_f1800_flag = True
                elif 'F7200' in line:
                    is_in_f1800_flag = False

            else:
                if is_in_f1800_flag:
                    f_1800_align_count += 1
                else:
                    f_7200_align_count += 1

                if 'F1800' in line:
                    is_in_f1800_flag = True
                elif 'F7200' in line:
                    is_in_f1800_flag = False


    global TOTAL_MOVEMENTS
    TOTAL_MOVEMENTS = f_1800_extrude_count + f_7200_extrude_count + f_1800_align_count + f_7200_align_count
    if TOTAL_MOVEMENTS == 0:
        return


    ratio_f_1800_extrude_count = float(f_1800_extrude_count)/TOTAL_MOVEMENTS
    ratio_f_7200_extrude_count = float(f_7200_extrude_count)/TOTAL_MOVEMENTS

    ratio_f_1800_align_count = float(f_1800_align_count)/TOTAL_MOVEMENTS
    ratio_f_7200_align_count = float(f_7200_align_count)/TOTAL_MOVEMENTS


    power_f_1800_extrude = 24.53
    power_f_7200_extrude = 24.71

    power_f_1800_align = 19.10
    power_f_7200_align = 19.22

    time_to_print_in_hours = float(TIME_TO_PRINT[0])/(60*60)

    power_consumption_in_kWh = ((
                                   (ratio_f_1800_extrude_count*power_f_1800_extrude)+
                                   (ratio_f_7200_extrude_count*power_f_7200_extrude)+
                                   (ratio_f_1800_align_count*power_f_1800_align)+
                                   (ratio_f_7200_align_count*power_f_7200_align)
                               ) * time_to_print_in_hours) /1000


    cost_of_electricity_for_one_kwh = 0.15
    global TOTAL_ELECTRICITY_COST
    TOTAL_ELECTRICITY_COST = power_consumption_in_kWh * cost_of_electricity_for_one_kwh * time_to_print_in_hours



def init_csv_file():
    heading = []

    heading.append('Filename')
    heading.append('Original Electricity Cost ($)')
    heading.append('Aggressive Electricity Cost ($)')
    heading.append('Percentage savings')

    with open('/home/jerryant/Desktop/electricity-cost-aggressive-stats.csv', 'w') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(heading)


def aggressive_power_gating_calculator(filename):


    global TOTAL_MOVEMENTS
    if TOTAL_MOVEMENTS == 0:
        return

    results = []
    g_code_contents = []

    results.append(filename)

    with open(filename) as f:
        for line in preprocess_lines(f):
            g_code_contents.append(line)

    extrution = [s for s in g_code_contents if "G1" in s]

    total_extrution = len(extrution)

    if total_extrution == 0:
        return

    neighborhood_threshold = 0.5        #Setting a value of 0.5 because granularity of printing is 1mm

    X_in_extrution = [s for s in extrution if "X" in s]
    X_terms_in_extrution = []
    for line in X_in_extrution:
        X_term_list = re.search("(X)([-]?[\d]+[\.][\d]+)", line)
        X_terms_in_extrution.append(float(X_term_list.group(2)))

    X_groups = []
    transient_X_value = X_terms_in_extrution[1]

    group = []
    for value in X_terms_in_extrution:
        if (transient_X_value-neighborhood_threshold) <= value <= (transient_X_value+neighborhood_threshold):
            transient_X_value = value
            group.append(value)
        else:
            if not group:
                continue
            else:
                X_groups.append(group)
                transient_X_value = value
                group = []


    X_groups = [x_group for x_group in X_groups if len(x_group)>=2]


    Y_in_extrution = [s for s in extrution if "Y" in s]
    Y_terms_in_extrution = []
    for line in Y_in_extrution:
        Y_term_list = re.search("(Y)([-]?[\d]+[\.][\d]+)", line)
        Y_terms_in_extrution.append(float(Y_term_list.group(2)))

    Y_groups = []
    transient_Y_value = Y_terms_in_extrution[1]

    group = []
    for value in Y_terms_in_extrution:
        if (transient_Y_value - neighborhood_threshold) <= value <= (transient_Y_value + neighborhood_threshold):
            transient_Y_value = value
            group.append(value)
        else:
            if not group:
                continue
            else:
                Y_groups.append(group)
                transient_Y_value = value
                group = []

    Y_groups = [y_group for y_group in Y_groups if len(y_group)>=2]

    total_groupable_X_count = 0
    total_groupable_Y_count = 0
    for group in X_groups:
        total_groupable_X_count += len(group)
    for group in Y_groups:
        total_groupable_Y_count += len(group)

    time_to_print = float(TIME_TO_PRINT[0])

    y_turn_off_time = (float(total_groupable_X_count)/TOTAL_MOVEMENTS) * time_to_print
    x_turn_off_time = (float(total_groupable_Y_count)/TOTAL_MOVEMENTS) * time_to_print

    time_for_actual_movements = time_to_print-y_turn_off_time-x_turn_off_time
    time_for_actual_movements = time_for_actual_movements/(60*60)       #Converting to hours

    calculate_electricity_cost(filename, time_for_actual_movements)


def calculate_electricity_cost(filename, time_for_actual_movements):
    global TOTAL_ELECTRICITY_COST
    global TIME_TO_PRINT

    time_to_print = float(TIME_TO_PRINT[0])/(60*60)
    cost_of_electricity_for_one_kwh = 0.15
    single_motor_power_f_1800_extrude = 12.53

    power_consumption_in_time_difference = single_motor_power_f_1800_extrude * (time_to_print-time_for_actual_movements)   #Units in Wh
    power_consumption_in_time_difference_in_kwh = power_consumption_in_time_difference / 1000
    electricity_cost_during_the_difference_time = (cost_of_electricity_for_one_kwh * power_consumption_in_time_difference_in_kwh)

    electricity_cost_after_power_gating = TOTAL_ELECTRICITY_COST-electricity_cost_during_the_difference_time

    percentage_savings_in_electricity = ((TOTAL_ELECTRICITY_COST-electricity_cost_after_power_gating)/TOTAL_ELECTRICITY_COST)*100


    results = []
    results.append(filename)
    results.append(TOTAL_ELECTRICITY_COST)
    results.append(electricity_cost_after_power_gating)
    results.append(percentage_savings_in_electricity)


    with open('/home/jerryant/Desktop/electricity-cost-aggressive-stats.csv', 'a+') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(results)

if __name__ == '__main__':

    path_gcode = "/home/jerryant/Desktop/Gcode-files/"

    init_csv_file()

    for filename in os.listdir(path_gcode):
        print "Processing:", filename
        electricity_cost_calculator(path_gcode+filename)
        aggressive_power_gating_calculator(path_gcode+filename)

    print "Completely Done."
