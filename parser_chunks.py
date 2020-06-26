'''
    Script to identify the optimium chunk size to maximize the motor turn-off time.
'''

import re
import csv
import os

TIME_TO_PRINT = 0
FILAMENT_CONSUMPTION = 0

CHUNK_SIZE = 10             # This value is iterated from 4 to 20 in function 'chunk_size_optimization_calculator'
NEIGHBORHOOD_THRESHOLD = 0.5

def preprocess_lines(f):
    for l in f:
        line = l.rstrip()
        if line:
            yield_line = True
            # Cleaning the input
            if ';TIME_ELAPSED' in line:
                global TIME_TO_PRINT
                TIME_TO_PRINT = float(re.findall("\d+\.\d+", line)[0])
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

def chunk_size_optimization_calculator(filename):
    global CHUNK_SIZE
    results = []
    results.append(filename)

    for CHUNK_SIZE in range(4, 21):
        chunks = []
        chunk = []
        counter = 0
        with open(filename) as f:
            for line in preprocess_lines(f):
                if counter == CHUNK_SIZE:
                    chunk.append(line)
                    chunks.append(chunk)
                    counter = 0
                    chunk = []
                else:
                    chunk.append(line)
                counter += 1

        power_gating_stats = []

        for chunk in chunks:
            power_gating_stats.append(process_chunk(chunk))

        # Processing power_gating_stats
        total_chunks_where_only_single_motor_on = process_power_gating_stats(power_gating_stats)
        safe_chunk_size_to_assume_both_motors_off = total_chunks_where_only_single_motor_on/2
        total_chunks = len(chunks)

        # Error control
        if total_chunks == 0:
            break

        ratio_of_optimization = float(safe_chunk_size_to_assume_both_motors_off)/total_chunks
        percentage_of_turn_off_time = ratio_of_optimization * 100
        results.append(percentage_of_turn_off_time)

    with open('/home/jerryant/Desktop/g-code-varying-chunk-size-stats.csv', 'a+') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(results)

    print "Processed:", filename


def process_power_gating_stats(power_gating_stats):
    X_off_time = 0
    Y_off_time = 0

    for entry in power_gating_stats:
        if entry[0]:
            X_off_time += 1
        if entry[1]:
            Y_off_time += 1

    return X_off_time +Y_off_time


def process_chunk(chunk):
    X_term_list = []
    Y_term_list = []

    for gcode in chunk:
        try:
            X_term_list.append(float((re.findall("(X)([-]?[\d]+[\.][\d]+)", gcode)[0])[1]))
            Y_term_list.append(float((re.findall("(Y)([-]?[\d]+[\.][\d]+)", gcode)[0])[1]))
        except:
            continue

    return powergating_in_chunks(X_term_list, Y_term_list)


def powergating_in_chunks(X_list, Y_list):
    global NEIGHBORHOOD_THRESHOLD

    # Processing X-list
    try:
        transient_value = X_list[1]
    except:
        return

    can_Y_be_power_gated = True

    for value in X_list:
        if (transient_value-NEIGHBORHOOD_THRESHOLD) <= value <= (transient_value+NEIGHBORHOOD_THRESHOLD):
            transient_value =value
        else:
            can_Y_be_power_gated = False


    # Processing Y-list
    transient_value = Y_list[1]
    can_X_be_power_gated = True

    for value in Y_list:
        if (transient_value-NEIGHBORHOOD_THRESHOLD) <= value <= (transient_value+NEIGHBORHOOD_THRESHOLD):
            transient_value =value
        else:
            can_X_be_power_gated = False

    result = []
    result.append(can_X_be_power_gated)
    result.append(can_Y_be_power_gated)

    return result


def init_csv_file():
    heading = []
    heading.append('Filename')
    heading.append('4')
    heading.append('5')
    heading.append('6')
    heading.append('7')
    heading.append('8')
    heading.append('9')
    heading.append('10')
    heading.append('11')
    heading.append('12')
    heading.append('13')
    heading.append('14')
    heading.append('15')
    heading.append('16')
    heading.append('17')
    heading.append('18')
    heading.append('19')
    heading.append('20')

    with open('/home/jerryant/Desktop/g-code-varying-chunk-size-stats.csv', 'w') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(heading)

if __name__ == "__main__":
    path_gcode = "/home/jerryant/Desktop/Gcode-files/"
    init_csv_file()

    for filename in os.listdir(path_gcode):
        print "Processing:", filename
        chunk_size_optimization_calculator(path_gcode+filename)

    print "Completely Done."
