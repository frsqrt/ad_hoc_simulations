import matplotlib.pyplot as plt

from node import State, get_node_by_id
from aloha_node import ALOHANode
from rts_cts_node import RTSCTSNode
from transmission import HighLevelMessage

# Parameters

# Generate random positions while ensuring the minimum distance
"""
for i in range(0, N):
    new_node = n.create_new_node(i, radius, transceive_range, X, Y)
    while (n.can_add_node_without_overlap(new_node, nodes, min_distance) == False):
        new_node = n.create_new_node(i, radius, transceive_range, X, Y)

    #for i in range(0, num_of_transmissions_per_node):
    #    new_node.send_schedule.append(n.Transmission(new_node, 10, 0, n.Message("Hello", 10)))

    nodes.append(new_node)

nodes[0].send_schedule.append(n.Transmission(0, nodes[0], 7, 0, n.Message("HALLO", 7)))
"""

class Visualizer:
    def __init__(self, x: int, y: int):
        self.fig = None
        self.ax = None
        self.x = x
        self.y = y
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
        colours = ['red' for node in nodes]

        established_links = [
            (get_node_by_id(nodes, node.protocol.currently_receiving.source).x_pos,
             get_node_by_id(nodes, node.protocol.currently_receiving.source).y_pos,
             node.x_pos - get_node_by_id(nodes, node.protocol.currently_receiving.source).x_pos,
             node.y_pos - get_node_by_id(nodes, node.protocol.currently_receiving.source).y_pos)
            for node in nodes if node.state == State.Receiving]

        self.ax.clear()
        self.ax.scatter(x_coords, y_coords, clip_on=False, color=colours)

        for link in established_links:
            self.ax.arrow(*link)

        for config in node_circle_range:
            self.ax.add_patch(plt.Circle(*config, **self.circle_parameters))

        self.ax.set_xlim((0, self.x))
        self.ax.set_ylim((0, self.y))
        self.ax.set_aspect('equal')  # Ensure the circles are not distorted

        self.ax.set_title('Current network state')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        plt.pause(0.2)
        #input()


def main():
    N = 2  # Number of nodes
    X = 10  # Window size
    Y = 10  # Window size
    radius = 0.25  # Radius of each circle
    min_distance = 0.5  # Minimum distance between circles
    transceive_range = 5.0  # Distance a node can send and receive messages
    num_of_transmissions_per_node = 1  # Number of transmissions a node will make
    propagation_time = 1  # Measured in units/time (5 means the message travels 5 units per loop iteration)

    # nodes = [
    #     ALOHANode(0, radius, transceive_range, 1, 1),
    #     ALOHANode(1, radius, transceive_range, 1, 6),
    #     ALOHANode(2, radius, transceive_range, 1, 2)
    # ]

    nodes = [
        RTSCTSNode(0, radius, transceive_range, 1, 1),
        RTSCTSNode(1, radius, transceive_range, 2, 2),
        RTSCTSNode(2, radius, transceive_range, 4, 4)
    ]

    for node in nodes:
        node.add_neighbors(nodes)

    simulation_time = 0
    active_transmissions = []

    vis = Visualizer(X, Y)

    while True:
        print("simulation_time: ", simulation_time)

        if simulation_time == 3:
            nodes[0].send(HighLevelMessage(1, "Hallo", 5))
            nodes[2].send(HighLevelMessage(0, "Hallo, im ignored", 5))


        # if simulation_time == 25:
        #     nodes[0].send(HighLevelMessage(2, "Hi2", 3))

        # if simulation_time == 50:
        #     nodes[1].send(HighLevelMessage(0, "Grueße!", 5))

        for node in nodes:
            node.execute_state_machine(simulation_time, active_transmissions)

        for node in nodes:
            msg = node.receive()
            if msg:
                print("****\nNode {} received: {}\n****".format(node.id, msg))


        vis.draw_function(nodes)
        simulation_time += 1

if __name__ == '__main__':
    main()
