'''
A naive parser to display energy consumption information of a G-code file
with no power-gating and aggressive power-gating
'''

import re
import os
import csv

TIME_TO_PRINT = 0
FILAMENT_CONSUMPTION = 0


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



    total_movements = f_1800_extrude_count + f_7200_extrude_count + f_1800_align_count + f_7200_align_count
    if total_movements == 0:
        return


    ratio_f_1800_extrude_count = float(f_1800_extrude_count)/total_movements
    ratio_f_7200_extrude_count = float(f_7200_extrude_count)/total_movements

    ratio_f_1800_align_count = float(f_1800_align_count)/total_movements
    ratio_f_7200_align_count = float(f_7200_align_count)/total_movements


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
    electricity_cost = power_consumption_in_kWh * cost_of_electricity_for_one_kwh * time_to_print_in_hours

    cost_of_filament_per_mm = 0.000159          #Ref: http://www.3ders.org/pricecompare/
    filament_consumption = float(FILAMENT_CONSUMPTION[0])
    filament_cost = filament_consumption * cost_of_filament_per_mm

    results = []
    results.append(filename)
    results.append(time_to_print_in_hours)
    results.append(power_consumption_in_kWh)
    results.append(electricity_cost)
    results.append(filament_consumption)
    results.append(filament_cost)
    results.append(electricity_cost/filament_cost)
    results.append((electricity_cost/filament_cost)*100)

    with open('/home/jerryant/Desktop/electricity-cost-stats.csv', 'a+') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(results)

    print "Processed:", filename

def init_csv_file():
    heading = []

    heading.append('Filename')
    heading.append('Time to Print (h)')
    heading.append('Power Consumption (kWh)')
    heading.append('Electricity Cost ($)')
    heading.append('Filament Consumption (mm)')
    heading.append('Filament Cost ($)')
    heading.append('Electricity-to-Filament-cost Ratio')
    heading.append('Percentage Electricity-to-Filament-cost (%)')

    with open('/home/jerryant/Desktop/electricity-cost-stats.csv', 'w') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(heading)

if __name__ == '__main__':
    path_gcode = "/home/jerryant/Desktop/Gcode-files/"

    init_csv_file()

    for filename in os.listdir(path_gcode):
        print "Processing:", filename
        electricity_cost_calculator(path_gcode + filename)

#     #Testing
#    filename = "ybase.stl.gcode"
#    electricity_cost_calculator(path_gcode+filename)


    print "Completely Done"


