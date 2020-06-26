import matplotlib.pyplot as plt
import numpy as np
import os
import re

TIME_TO_PRINT = 0
TOTAL_MOVEMENTS = 0
TOTAL_ELECTRICITY_COST = 0

time_lines = []
time_concentric = []
time_triangles = []
time_grid = []

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

    global time_concentric
    global time_grid
    global time_lines
    global time_triangles

    if 'lines' in filename:
        time_lines.append(time_to_print)
    if 'grid' in filename:
        time_grid.append(time_to_print)
    if 'concentric' in filename:
        time_concentric.append(time_to_print)
    if 'triangles' in filename:
        time_triangles.append(time_to_print)

    y_turn_off_time = (float(total_groupable_X_count)/TOTAL_MOVEMENTS) * time_to_print
    x_turn_off_time = (float(total_groupable_Y_count)/TOTAL_MOVEMENTS) * time_to_print

    time_for_actual_movements = time_to_print-y_turn_off_time-x_turn_off_time

    return (time_to_print-time_for_actual_movements)/time_to_print




if __name__ == '__main__':
    models = ['HINGE', '3DPUZZLE', 'CUP-HOLDER', 'WHISTLE', 'IPHONE5-COVER', 'GEAR']

    lines = [0.03807663410969204, 0.059867862880661364, 0.04035697376296439, 0.017202589041569943,
     0.0301880152825256, 0.10550245745481335]
    time_lines = [12143.711, 8058.672, 23994.651, 5225.92995, 6805.593, 2658.34]

    concentric = [0.0695775781820012, 0.09288956360245672, 0.022924392676282487, 0.04307007914957525,
     0.036401888592607144, 0.13146224409209661]
    time_concentric = [12100.998, 8007.063, 28084.081, 5798.09796, 6586.808, 2663.513]

    grid = [0.012092192396928323, 0.05481235146415392, 0.04015807991426182, 0.020243175779048328,
     0.02898165986559677, 0.10647814380508187]
    time_grid = [14391.641, 8809.263, 24262.268, 5410.13475, 7762.974, 2909.433]

    triangles = [0.03284880393727819, 0.06095200317334401, 0.0390270950777596, 0.013878686526108512,
     0.024475548643511157, 0.0037653916991971944]
    time_triangles = [16924.753, 9725.995, 24605.785, 5552.91333, 8857.491, 3201.16562]

    lines = [l*5 for l in lines]
    concentric = [c*5 for c in concentric]
    grid = [g*5 for g in grid]
    triangles = [t*5 for t in triangles]

    energy_lines = [l*39 for l in time_lines]
    energy_concentric = [c*39 for c in time_concentric]
    energy_grid = [g*39 for g in time_grid]
    energy_triangles = [t*39 for t in time_triangles]

    vector_lines = np.array(lines)
    vector_lines_energy = np.array(energy_lines)
    old_energy_lines = (vector_lines*vector_lines_energy) + vector_lines_energy
    old_energy_lines = [l/1000 for l in old_energy_lines]
    vector_lines_energy = [l/1000 for l in vector_lines_energy]
    vector_lines_energy = np.array(vector_lines_energy)
    old_energy_lines = np.array(old_energy_lines)
    lines_percent_savings = (old_energy_lines-vector_lines_energy)/old_energy_lines

    vector_grid = np.array(grid)
    vector_grid_energy = np.array(energy_grid)
    old_energy_grid = (vector_grid*vector_grid_energy) + vector_grid_energy
    old_energy_grid = [g/1000 for g in old_energy_grid]
    vector_grid_energy = [g/1000 for g in vector_grid_energy]
    vector_grid_energy = np.array(vector_grid_energy)
    old_energy_grid = np.array(old_energy_grid)
    grid_percent_savings = (old_energy_grid-vector_grid_energy)/old_energy_grid

    vector_concentric = np.array(concentric)
    vector_concentric_energy = np.array(energy_concentric)
    old_energy_concentric = (vector_concentric*vector_concentric_energy) + vector_concentric_energy
    old_energy_concentric = [c/1000 for c in old_energy_concentric]
    vector_concentric_energy = [c/1000 for c in vector_concentric_energy]
    vector_concentric_energy = np.array(vector_concentric_energy)
    old_energy_concentric = np.array(old_energy_concentric)
    concentric_percent_savings = (old_energy_concentric-vector_concentric_energy)/old_energy_concentric

    vector_triangles = np.array(triangles)
    vector_triangles_energy = np.array(energy_triangles)
    old_energy_triangles = (vector_triangles*vector_triangles_energy) + vector_triangles_energy
    old_energy_triangles = [t/1000 for t in old_energy_triangles]
    vector_triangles_energy = [t/1000 for t in vector_triangles_energy]
    vector_triangles_energy = np.array(vector_triangles_energy)
    old_energy_triangles = np.array(old_energy_triangles)
    triangles_percent_savings = (old_energy_triangles-vector_triangles_energy)/old_energy_triangles

    fig, ax = plt.subplots()
    plt.rc('font', family='Times New Roman Bold')
    plt.rcParams['font.size'] = 20
    plt.rcParams['font.weight'] = 'bold'
    plt.xticks(rotation=10)

    x_pos = np.arange(len(lines))

    w = 0.2

    bar1 = ax.bar(x_pos-w, old_energy_lines, width=w, color='white', clip_on='True', hatch='**')
    bar2 = ax.bar(x_pos, old_energy_concentric, width=w, color='white', clip_on='True', hatch='**')
    bar3 = ax.bar(x_pos+w, old_energy_triangles, width=w, color='white', clip_on='True', hatch='**')
    bar4 = ax.bar(x_pos+2*w, old_energy_grid, width=w, color='white', clip_on='True', hatch='**')

    #colors = ['#1D72AA', '#C44440', '#8CBB4E', '#795892']
    #colors = ['#0072BD', '#D95319', '#EDB11F', '#7E2F8E']
    #colors = ['#0072BD', '#D95319', '#EDB11F', '#7E2F8E']
    colors = ['#C44440', '#6666FF', '#A0C289', 'gold']

    ax.bar(x_pos-w, vector_lines_energy, width=w, clip_on='True', hatch='/', label='Lines', color=colors[0], )
    ax.bar(x_pos, vector_concentric_energy, width=w, clip_on='True', hatch='oo', label='Square Circles', color=colors[1])
    ax.bar(x_pos+w, vector_triangles_energy, width=w, clip_on='True', hatch='x', label='Triangles', color=colors[2])
    ax.bar(x_pos+2*w, vector_grid_energy, width=w, clip_on='True', hatch='+', label='Grid', color=colors[3])

    plt.xticks(x_pos, models, fontname="Times New Roman Bold", fontweight='bold', fontsize=15)
    plt.yticks(fontname="Times New Roman Bold", fontweight='bold')
    ax.set_ylim([0, 1320])

    ax.set_ylabel('Energy Consump. (KJ)', fontname="Times New Roman Bold", fontsize=20, fontweight='bold')
    ax.legend(loc='best', fontsize=20)

    ind = -1
    for rect in bar1:
        ind = ind + 1
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%.0f' % float(lines_percent_savings[ind]*100)+'%',
                ha='center', va='bottom', fontsize=13, fontweight='bold')

    ind = -1
    for rect in bar2:
        ind = ind + 1
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.025*height,
                '%.0f' % float(concentric_percent_savings[ind]*100)+'%',
                ha='center', va='bottom', fontsize=13, fontweight='bold')

    ind = -1
    for rect in bar3:
        ind = ind + 1
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%.0f' % float(triangles_percent_savings[ind]*100)+'%',
                ha='center', va='bottom', fontsize=13, fontweight='bold')

    ind = -1
    for rect in bar4:
        ind = ind + 1
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%.0f' % float(grid_percent_savings[ind]*100)+'%',
                ha='center', va='bottom', fontsize=13, fontweight='bold')

    plt.subplots_adjust(bottom=0.2)
    plt.show()
