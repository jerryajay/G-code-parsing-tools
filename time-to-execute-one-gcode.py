'''
    Script to identify execution time of one gcode.
    PURPOSE:
        To ensure the fact that the motor start-up latency is minimal compared to the execution time of the gcode.
'''

import re
import csv
import os


def g_code_stats_calculator(filename):

    results = []

    results.append(filename)

    number_of_gcodes = 0
    time_to_print = 0

    with open(filename) as f:
        for line in f:
            number_of_gcodes += 1
            if ';TIME_ELAPSED' in line:
                time_to_print = float(re.findall("\d+\.\d+", line)[0])

    if time_to_print == 0:
        return

    time_for_one_gcode = time_to_print/number_of_gcodes

    results.append(number_of_gcodes)
    results.append(time_to_print)
    results.append(time_for_one_gcode)

    with open('/home/jerryant/Desktop/single-gcode-execution-stats.csv', 'a+') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(results)

    print "Processed:", filename



def init_csv_file():
    heading = []

    heading.append('Filename')
    heading.append('Total G-codes')
    heading.append('Time to print (s)')
    heading.append('Time to execute one G-code (s)')

    with open('/home/jerryant/Desktop/single-gcode-execution-stats.csv', 'w') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(heading)

if __name__ == "__main__":

    path_gcode = "/home/jerryant/Desktop/Gcode-files/"

    init_csv_file()

    for filename in os.listdir(path_gcode):
        print "Processing:", filename
        g_code_stats_calculator(path_gcode+filename)

    print "Completely Done."