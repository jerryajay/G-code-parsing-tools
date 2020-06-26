import matplotlib.pyplot as plt
import numpy as np
from operator import add

if __name__ == "__main__":
    models = ['HINGE', '3DPUZZLE', 'CUP-HOLDER', 'WHISTLE', 'IPHONE5-COVER', 'GEAR']
    time_to_print = [12143.711, 8058.672, 23994.651, 5225.92995, 6805.593, 2658.34]
    power_gating_additional_time = [0, 0, 0, 0, 0, 0]

    new_time_to_print = map(add, time_to_print, power_gating_additional_time)

    fig, ax = plt.subplots()
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    plt.rc('font', family='Times New Roman Bold')
    plt.rcParams['font.size'] = 20
    plt.rcParams['font.weight'] = 'bold'
    plt.xticks(rotation=30)

    w = 0.2

    x_pos = np.arange(len(models))

    bar1 = ax.bar(x_pos, time_to_print, width=w, color='#6666FF', clip_on='True', hatch='x',
                  label='Time to Print')
    bar2 = ax.bar(x_pos + w, new_time_to_print, width=w, color='gold', clip_on='True', hatch='++', label='Extended Time to Print')

    plt.ylabel('Time to Print (Second)', fontweight='bold', fontsize=25, fontname='Nimbus Roman No9 L')
    plt.xticks(x_pos, models, fontsize=15, fontweight='bold', fontname='Times New Roman Bold')
    plt.yticks(fontweight='bold', fontname='Times New Roman Bold')
    plt.legend(loc='best', frameon=False, fontsize=15)
    plt.show()
