import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from enum import Enum
import node as n
import time

# Parameters
N = 2  # Number of nodes
X = 5  # Window size
Y = 5  # Window size
radius = 0.25  # Radius of each circle
min_distance = 0.5  # Minimum distance between circles
transceive_range = 5.0  # Distance a node can send and receive messages
num_of_transmissions_per_node = 1  # Number of transmissions a node will make
propagation_time = 1  # Measured in units/time (5 means the message travels 5 units per loop iteration)

nodes = []

# Generate random positions while ensuring the minimum distance
for i in range(0, N):
    new_node = n.create_new_node(i, radius, transceive_range, X, Y)
    while (n.can_add_node_without_overlap(new_node, nodes, min_distance) == False):
        new_node = n.create_new_node(i, radius, transceive_range, X, Y)

    #for i in range(0, num_of_transmissions_per_node):
    #    new_node.send_schedule.append(n.Transmission(new_node, 10, 0, n.Message("Hello", 10)))

    nodes.append(new_node)

nodes[0].send_schedule.append(n.Transmission(0, nodes[0], 7, 0, n.Message("HALLO", 7)))

# Add neighbors to nodes
for node in nodes:
    node.add_neighbors(nodes)

simulation_time = 0
active_transmissions = []


class Visualizer:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.circle_parameters = {'color': 'red', 'fill': False, 'linestyle': '--'}
        self.set_up_plot()

    def set_up_plot(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("$x_0$")
        self.ax.set_ylabel("$x_1$")
        self.ax.set_title("Template title")
        self.fig.show()

    def draw_function(self, nodes):
        x_coords = [node.x_pos for node in nodes]
        y_coords = [node.y_pos for node in nodes]
        node_circle_range = zip(zip(x_coords, y_coords), [node.transceive_range for node in nodes])
        colours = [node.get_color_based_on_state() for node in nodes]

        established_links = [
            (node.receive_buffer.source.x_pos,
             node.receive_buffer.source.y_pos,
             node.x_pos - node.receive_buffer.source.x_pos,
             node.y_pos - node.receive_buffer.source.y_pos)
            for node in nodes if node.state == n.NodeState.Receiving]

        self.ax.clear()
        self.ax.scatter(x_coords, y_coords, clip_on=False, color=colours)

        for link in established_links:
            self.ax.arrow(*link)

        for config in node_circle_range:
            self.ax.add_patch(plt.Circle(*config, **self.circle_parameters))

        self.ax.set_xlim((-10, X + 10))
        self.ax.set_ylim((-10, Y + 10))
        self.ax.set_aspect('equal')  # Ensure the circles are not distorted

        self.ax.set_title('Current network state')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        plt.pause(0.5)


vis = Visualizer()

while (1):
    print("simulation_time: ", simulation_time)

    # Plot each circle
    for node in nodes:

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

            node.state_counter -= 1
            if node.state_counter == 0:
                # TODO: if data was received, send ACK, don't go idle
                node.state = n.NodeState.Idle

                # TODO change removal to only occur when message has existed longer than diameter of network + data transmission length
                active_transmissions.remove(node.receive_buffer)

    # TODO create separate draw function.
    vis.draw_function(nodes)

    simulation_time += 1

