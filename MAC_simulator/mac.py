import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from enum import Enum
import node as n
import time

# Parameters
N = 2 # Number of nodes
X = 5 # Window size
Y = 5 # Window size
radius = 0.25  # Radius of each circle
min_distance = 0.5  # Minimum distance between circles
transceive_range = 5.0 # Distance a node can send and receive messages
num_of_transmissions_per_node = 1 # Number of transmissions a node will make
propagation_time = 1 # Measured in units/time (5 means the message travels 5 units per loop iteration)

nodes = []

# Generate random positions while ensuring the minimum distance
for i in range(0, N):
    new_node = n.create_new_node(i, radius, transceive_range, X, Y)
    while(n.can_add_node_without_overlap(new_node, nodes, min_distance) == False):
        new_node = n.create_new_node(i, radius, transceive_range, X, Y)

    #for i in range(0, num_of_transmissions_per_node):
    #    new_node.send_schedule.append(n.Transmission(new_node, 10, 0, n.Message("Hello", 10)))

    nodes.append(new_node)

nodes[0].send_schedule.append(n.Transmission(0, nodes[0], 7, 0, n.Message("HALLO", 7)))

# Add neighbors to nodes
for node in nodes:
    node.add_neighbors(nodes)

# Create a plot
fig, ax = plt.subplots()

# Set the plot limits
ax.set_xlim((-10, X+10))
ax.set_ylim((-10, Y+10))
ax.set_aspect('equal')  # Ensure the circles are not distorted

# Add grid and labels
ax.grid(True)
ax.set_title(f'{N} nodes circles with minimum distance {min_distance}')
ax.set_xlabel('X')
ax.set_ylabel('Y')

simulation_time = 0
active_transmissions = []

while(1):
    print("simulation_time: ", simulation_time)

    # Plot each circle
    for node in nodes:
        node_color = 'blue'

        if node.state == n.NodeState.Idle:
            # Check if node can receive
            for transmission in active_transmissions:
                # Sanity check that we can receive the transmission
                if transmission.source not in node.neighbors:
                    continue

                # Check whether we can already receive the message
                transmission_propagation_time = simulation_time - transmission.actual_transmit_time
                if transmission_propagation_time >= n.get_distance_between_nodes(transmission.source, node):
                    node.state = n.NodeState.Receiving
                    node.state_counter = transmission.message.length
                    node.receive_buffer = transmission

            if node.state != n.NodeState.Receiving:
                # Check if node wants to send
                for transmission in node.send_schedule:
                    if transmission.planned_transmit_time <= simulation_time:
                        transmission.actual_transmit_time = simulation_time
                        active_transmissions.append(transmission)
                        node.send_schedule.remove(transmission)
                        node.state = n.NodeState.Sending
                        node.state_counter = transmission.message.length

        elif node.state == n.NodeState.Sending:
            node.state_counter -= 1
            if node.state_counter == 0:
                node.state = n.NodeState.Idle
        elif node.state == n.NodeState.Receiving:
            # TODO: check for collisions

            # Draw line inbetween sender and receiver
            plt.arrow(node.receive_buffer.source.x_pos, node.receive_buffer.source.y_pos, node.x_pos - node.receive_buffer.source.x_pos, node.y_pos - node.receive_buffer.source.y_pos)

            node.state_counter -= 1
            if node.state_counter == 0:
                # TODO: if data was received, send ACK, don't go idle
                node.state = n.NodeState.Idle
                active_transmissions.remove(node.receive_buffer)

        node_color = node.get_color_based_on_state()

        circle = plt.Circle((node.x_pos, node.y_pos), node.radius, color=node_color, fill=True)
        ax.add_artist(circle)

        # Plot the communication range (range field)
        range_circle = plt.Circle((node.x_pos, node.y_pos), node.transceive_range, color='red', fill=False, linestyle='--')
        ax.add_artist(range_circle)

    simulation_time += 1

    plt.pause(0.5)

plt.show()
