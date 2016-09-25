import matplotlib.pyplot as plt
import numpy as np
from operator import add

import os
import re

TIME_TO_PRINT = 0
TOTAL_MOVEMENTS = 0
TOTAL_ELECTRICITY_COST = 0


original_g_code_size = []


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


def aggressive_power_gating_calculator(filename):


    global TOTAL_MOVEMENTS
    global original_g_code_size
#    if TOTAL_MOVEMENTS == 0:
#        return

    original_g_code_size.append(TOTAL_MOVEMENTS)

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

    return (total_groupable_X_count+total_groupable_Y_count)*2

#    global time_concentric
#    global time_grid
#    global time_lines
#    global time_triangles
#
#    if 'lines' in filename:
#        time_lines.append(time_to_print)
#    if 'grid' in filename:
#        time_grid.append(time_to_print)
#    if 'concentric' in filename:
#        time_concentric.append(time_to_print)
#    if 'triangles' in filename:
#        time_triangles.append(time_to_print)
#
#
#    y_turn_off_time = (float(total_groupable_X_count)/TOTAL_MOVEMENTS) * time_to_print
#    x_turn_off_time = (float(total_groupable_Y_count)/TOTAL_MOVEMENTS) * time_to_print
#
#    time_for_actual_movements = time_to_print-y_turn_off_time-x_turn_off_time
#    #time_for_actual_movements = time_for_actual_movements/(60*60)       #Converting to hours
#
#    return (time_to_print-time_for_actual_movements)/time_to_print

    #calculate_electricity_cost(filename, time_for_actual_movements)


if __name__ == '__main__':


    models = []
    power_gating_additional_code = []

    path_gcode = "/home/jerryant/Desktop/G-code-impact/"

    idx = 1

    for filename in os.listdir(path_gcode):
        idx = idx +1
        if idx == 100:
            break
        else:
            models.append(filename)
            electricity_cost_calculator(path_gcode+filename)
            power_gating_additional_code.append(aggressive_power_gating_calculator(path_gcode+filename))

    global original_g_code_size
    print original_g_code_size
    print models
    print power_gating_additional_code

    f = open("/home/jerryant/Desktop/Collection/original_g_code.csv", 'w')
    for item in original_g_code_size:
        f.write("%s\n" % item)
    f = open("/home/jerryant/Desktop/Collection/models.csv", 'w')
    for item in models:
        f.write("%s\n" % item)
    f = open("/home/jerryant/Desktop/Collection/power_gating_addition.csv", 'w')
    for item in power_gating_additional_code:
        f.write("%s\n" % item)



#    models = ['HINGE', '3DPUZZLE', 'CUP-HOLDER', 'WHISTLE', 'IPHONE5-COVER', 'GEAR']
#    original_g_code_size = [166375, 110794, 559705, 57782, 119352, 62463]
#    power_gating_additional_code =  [12670, 13266, 45176, 1988, 7206, 13180]
#
#    new_gcode_size = map(add, original_g_code_size, power_gating_additional_code)
#
#    fig, ax = plt.subplots()
#
#    ax.spines['right'].set_visible(False)
#    ax.spines['top'].set_visible(False)
#
#
#    ax.yaxis.set_ticks_position('left')
#    ax.xaxis.set_ticks_position('bottom')
#
#    plt.rc('font', family='Times New Roman Bold')
#    plt.rcParams['font.size'] = 20
#    plt.rcParams['font.weight'] = 'bold'
#    plt.xticks(rotation=20)
#
#    w = 0.2
#
#    x_pos = np.arange(len(models))
#
#    bar1 = ax.bar(x_pos, original_g_code_size, width=w, color='#C44440', clip_on='True', hatch='/', label='Original File Size')
#    bar2 = ax.bar(x_pos+w, new_gcode_size, width=w, color='#6666FF', clip_on='True', hatch='++', label='Extended File Size')
#
#    plt.ylabel('# of instrs. in G-code file', fontname='Times New Roman Bold', fontweight='bold', fontsize=23)
#
#    plt.xticks(x_pos, models, fontsize=15, fontweight='bold', fontname='Times New Roman Bold')
#    plt.yticks(fontweight='bold', fontname='Times New Roman Bold')
#
#    plt.legend(frameon=False, fontsize=20)
#
#    plt.show()

