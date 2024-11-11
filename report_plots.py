import matplotlib.pyplot as plt
import numpy as np
import csv
import matplotlib.patches as mpatches

def calculate_avg_variance(csv_file):
    # Load the CSV data
    data = np.loadtxt(csv_file, delimiter=',', skiprows=1)  # Skipping the header row if it exists
    
    # Extract the first and second columns
    first_column = data[:, 0]
    second_column = data[:, 1]
    
    # Calculate average and variance for each column
    avg_first_column = np.mean(first_column)
    std_dev_first_column = np.sqrt(np.var(first_column))
    
    avg_second_column = np.mean(second_column)
    std_dev_second_column = np.sqrt(np.var(second_column))
    
    # Print the results
    #data_size = csv_file.split('_')[5]
    #random_interval = csv_file.split('_')[8].split('.')[0]
    #print(f"{data_size} & {random_interval} & {int(avg_second_column)} & {int(avg_first_column)} & {int(std_dev_second_column)} & {int(std_dev_first_column)} \\\\\hline")

    return (avg_first_column, std_dev_first_column, avg_second_column, std_dev_second_column)

def plot_simultaneously_transmit():
    # Replace 'your_file.csv' with the path to your CSV file
    message_lengths = np.array([5, 25, 50, 75, 100, 125, 150, 175, 200])
    optimal_time_taken = message_lengths * 29
    time_taken_avgs_rts_cts = []
    collisions_avgs_rts_cts = []
    time_taken_avgs_aloha = []
    collisions_avgs_aloha = []

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_5.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_25.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_50.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_75.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_100.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_125.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_150.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_175.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_200.csv')
    time_taken_avgs_rts_cts.append(result[0])
    collisions_avgs_rts_cts.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_5.csv')
    time_taken_avgs_aloha.append(result[0])
    collisions_avgs_aloha.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_25.csv')
    time_taken_avgs_aloha.append(result[0])
    collisions_avgs_aloha.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_50.csv')
    time_taken_avgs_aloha.append(result[0])
    collisions_avgs_aloha.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_75.csv')
    time_taken_avgs_aloha.append(result[0])
    collisions_avgs_aloha.append(result[2])

    fig, axs = plt.subplots(2,2)
    #plt.title("Time taken and # collisions over message length")
    axs[0][0].title.set_text("RTS CTS")
    axs[0][0].set_ylabel('T [Simulation ticks]')
    axs[0][0].grid()
    axs[0][0].plot(message_lengths, time_taken_avgs_rts_cts, "-o", color='tab:red', label='RTS CTS')
    axs[0][0].plot(message_lengths, optimal_time_taken, "-o", color='tab:green', label='Optimal transmissions')

    axs[1][0].set_ylabel('#Collisions')
    axs[1][0].set_xlabel('Data size')
    axs[1][0].grid()
    axs[1][0].plot(message_lengths, collisions_avgs_rts_cts, "-o", color='tab:red', label='RTS CTS')

    axs[0][1].title.set_text("ALOHA")
    axs[0][1].grid()
    axs[0][1].plot(message_lengths[0:4], time_taken_avgs_aloha, "-o", color='tab:blue', label='ALOHA')
    axs[0][1].plot(message_lengths[0:4], optimal_time_taken[0:4], "-o", color='tab:green', label='Optimal transmissions')

    axs[1][1].set_xlabel('Data size')
    axs[1][1].grid()
    axs[1][1].plot(message_lengths[0:4], collisions_avgs_aloha, "-o", color='tab:blue', label='ALOHA')

    plt.subplots_adjust(wspace=0.31, hspace=0.2)

    red_patch = mpatches.Patch(color='red', label='RTS CTS')
    blue_patch = mpatches.Patch(color='blue', label='ALOHA')
    green_patch = mpatches.Patch(color='green', label='Optimal transmission time')

    fig.legend(loc='lower center', handles=[red_patch, blue_patch, green_patch], fancybox=False, shadow=False, frameon=False, ncol=5)

    fig.subplots_adjust(bottom=0.17)
    plt.show()

def plot_random_transmit():
    message_lengths = [5, 10, 15, 20, 25]
    time_taken_avg_aloha_25 = []
    time_taken_avg_aloha_50 = []
    time_taken_avg_aloha_75 = []
    time_taken_avg_aloha_100 = []
    time_taken_avg_rts_cts_25 = []
    time_taken_avg_rts_cts_50 = []
    time_taken_avg_rts_cts_75 = []
    time_taken_avg_rts_cts_100 = []
    collisions_avg_aloha_25 = []
    collisions_avg_aloha_50 = []
    collisions_avg_aloha_75 = []
    collisions_avg_aloha_100 = []
    collisions_avg_rts_cts_25 = []
    collisions_avg_rts_cts_50 = []
    collisions_avg_rts_cts_75 = []
    collisions_avg_rts_cts_100 = []
    #--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_5_random_max_25.csv')
    time_taken_avg_rts_cts_25.append(result[0])
    collisions_avg_rts_cts_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_10_random_max_25.csv')
    time_taken_avg_rts_cts_25.append(result[0])
    collisions_avg_rts_cts_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_15_random_max_25.csv')
    time_taken_avg_rts_cts_25.append(result[0])
    collisions_avg_rts_cts_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_20_random_max_25.csv')
    time_taken_avg_rts_cts_25.append(result[0])
    collisions_avg_rts_cts_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_25_random_max_25.csv')
    time_taken_avg_rts_cts_25.append(result[0])
    collisions_avg_rts_cts_25.append(result[2])
#--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_5_random_max_50.csv')
    time_taken_avg_rts_cts_50.append(result[0])
    collisions_avg_rts_cts_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_10_random_max_50.csv')
    time_taken_avg_rts_cts_50.append(result[0])
    collisions_avg_rts_cts_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_15_random_max_50.csv')
    time_taken_avg_rts_cts_50.append(result[0])
    collisions_avg_rts_cts_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_20_random_max_50.csv')
    time_taken_avg_rts_cts_50.append(result[0])
    collisions_avg_rts_cts_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_25_random_max_50.csv')
    time_taken_avg_rts_cts_50.append(result[0])
    collisions_avg_rts_cts_50.append(result[2])
#--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_5_random_max_75.csv')
    time_taken_avg_rts_cts_75.append(result[0])
    collisions_avg_rts_cts_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_10_random_max_75.csv')
    time_taken_avg_rts_cts_75.append(result[0])
    collisions_avg_rts_cts_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_15_random_max_75.csv')
    time_taken_avg_rts_cts_75.append(result[0])
    collisions_avg_rts_cts_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_20_random_max_75.csv')
    time_taken_avg_rts_cts_75.append(result[0])
    collisions_avg_rts_cts_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_25_random_max_75.csv')
    time_taken_avg_rts_cts_75.append(result[0])
    collisions_avg_rts_cts_75.append(result[2])
#--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_5_random_max_100.csv')
    time_taken_avg_rts_cts_100.append(result[0])
    collisions_avg_rts_cts_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_10_random_max_100.csv')
    time_taken_avg_rts_cts_100.append(result[0])
    collisions_avg_rts_cts_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_15_random_max_100.csv')
    time_taken_avg_rts_cts_100.append(result[0])
    collisions_avg_rts_cts_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_20_random_max_100.csv')
    time_taken_avg_rts_cts_100.append(result[0])
    collisions_avg_rts_cts_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_rts_cts_25_random_max_100.csv')
    time_taken_avg_rts_cts_100.append(result[0])
    collisions_avg_rts_cts_100.append(result[2])
#--------------------
#--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_5_random_max_25.csv')
    time_taken_avg_aloha_25.append(result[0])
    collisions_avg_aloha_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_10_random_max_25.csv')
    time_taken_avg_aloha_25.append(result[0])
    collisions_avg_aloha_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_15_random_max_25.csv')
    time_taken_avg_aloha_25.append(result[0])
    collisions_avg_aloha_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_20_random_max_25.csv')
    time_taken_avg_aloha_25.append(result[0])
    collisions_avg_aloha_25.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_25_random_max_25.csv')
    time_taken_avg_aloha_25.append(result[0])
    collisions_avg_aloha_25.append(result[2])
#--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_5_random_max_50.csv')
    time_taken_avg_aloha_50.append(result[0])
    collisions_avg_aloha_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_10_random_max_50.csv')
    time_taken_avg_aloha_50.append(result[0])
    collisions_avg_aloha_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_15_random_max_50.csv')
    time_taken_avg_aloha_50.append(result[0])
    collisions_avg_aloha_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_20_random_max_50.csv')
    time_taken_avg_aloha_50.append(result[0])
    collisions_avg_aloha_50.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_25_random_max_50.csv')
    time_taken_avg_aloha_50.append(result[0])
    collisions_avg_aloha_50.append(result[2])
#--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_5_random_max_75.csv')
    time_taken_avg_aloha_75.append(result[0])
    collisions_avg_aloha_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_10_random_max_75.csv')
    time_taken_avg_aloha_75.append(result[0])
    collisions_avg_aloha_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_15_random_max_75.csv')
    time_taken_avg_aloha_75.append(result[0])
    collisions_avg_aloha_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_20_random_max_75.csv')
    time_taken_avg_aloha_75.append(result[0])
    collisions_avg_aloha_75.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_25_random_max_75.csv')
    time_taken_avg_aloha_75.append(result[0])
    collisions_avg_aloha_75.append(result[2])
#--------------------
    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_5_random_max_100.csv')
    time_taken_avg_aloha_100.append(result[0])
    collisions_avg_aloha_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_10_random_max_100.csv')
    time_taken_avg_aloha_100.append(result[0])
    collisions_avg_aloha_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_15_random_max_100.csv')
    time_taken_avg_aloha_100.append(result[0])
    collisions_avg_aloha_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_20_random_max_100.csv')
    time_taken_avg_aloha_100.append(result[0])
    collisions_avg_aloha_100.append(result[2])

    result = calculate_avg_variance('./MAC_simulator/data/data_sink_aloha_25_random_max_100.csv')
    time_taken_avg_aloha_100.append(result[0])
    collisions_avg_aloha_100.append(result[2])
#--------------------

    fig, axs = plt.subplots(2,2)
    axs[0][0].title.set_text('RTS CTS')
    axs[0][0].set_ylabel('T [Simulation ticks]')
    axs[0][0].grid()
    axs[0][0].plot(message_lengths, time_taken_avg_rts_cts_25, "-o", color='tab:red', label='25')
    axs[0][0].plot(message_lengths, time_taken_avg_rts_cts_50, "-o", color='tab:green', label='50')
    axs[0][0].plot(message_lengths, time_taken_avg_rts_cts_75, "-o", color='tab:blue', label='75')
    axs[0][0].plot(message_lengths, time_taken_avg_rts_cts_100, "-o", color='tab:orange', label='100')

    axs[0][1].title.set_text('ALOHA')
    axs[0][1].grid()
    axs[0][1].plot(message_lengths, time_taken_avg_aloha_25, "-o", color='tab:red', label='25')
    axs[0][1].plot(message_lengths, time_taken_avg_aloha_50, "-o", color='tab:green', label='50')
    axs[0][1].plot(message_lengths, time_taken_avg_aloha_75, "-o", color='tab:blue', label='75')
    axs[0][1].plot(message_lengths, time_taken_avg_aloha_100, "-o", color='tab:orange', label='100')

    axs[1][0].set_ylabel('#Collisions')
    axs[1][0].grid()
    axs[1][0].plot(message_lengths, collisions_avg_rts_cts_25, "-o", color='tab:red', label='25')
    axs[1][0].plot(message_lengths, collisions_avg_rts_cts_50, "-o", color='tab:green', label='50')
    axs[1][0].plot(message_lengths, collisions_avg_rts_cts_75, "-o", color='tab:blue', label='75')
    axs[1][0].plot(message_lengths, collisions_avg_rts_cts_100, "-o", color='tab:orange', label='100')
    axs[1][0].set_xlabel('Data size')

    axs[1][1].grid()
    axs[1][1].plot(message_lengths, collisions_avg_aloha_25, "-o", color='tab:red', label='25')
    axs[1][1].plot(message_lengths, collisions_avg_aloha_50, "-o", color='tab:green', label='50')
    axs[1][1].plot(message_lengths, collisions_avg_aloha_75, "-o", color='tab:blue', label='75')
    axs[1][1].plot(message_lengths, collisions_avg_aloha_100, "-o", color='tab:orange', label='100')
    axs[1][1].set_xlabel('Data size')

    plt.subplots_adjust(wspace=0.31, hspace=0.2)

    opaque_patch = mpatches.Patch(color='red', alpha=0., label='Random intervals:')
    red_patch = mpatches.Patch(color='red', label='25')
    green_patch = mpatches.Patch(color='green', label='50')
    blue_patch = mpatches.Patch(color='blue', label='75')
    orange_patch = mpatches.Patch(color='orange', label='100')

    fig.legend(loc='lower center', handles=[opaque_patch, red_patch, green_patch, blue_patch, orange_patch], fancybox=False, shadow=False, frameon=False, ncol=5)

    fig.subplots_adjust(bottom=0.17) # or whatever
    #plt.title("Time taken and # collisions over message length and random interval")
    plt.show()


#plot_simultaneously_transmit()
plot_random_transmit()
