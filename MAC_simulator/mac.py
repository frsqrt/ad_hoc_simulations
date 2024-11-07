import matplotlib.pyplot as plt
import logging

from node import State, get_node_by_id
from aloha_node import ALOHANode
from rts_cts_node import RTSCTSNode
from transmission import HighLevelMessage

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
        colours = [node.get_color_based_on_state() for node in nodes]

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

        #plt.pause(0.1)
        input()


def main():
    N = 2  # Number of nodes
    X = 10  # Window size
    Y = 10  # Window size
    radius = 0.25  # Radius of each circle
    min_distance = 0.5  # Minimum distance between circles
    transceive_range = 5.0  # Distance a node can send and receive messages

    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    nodes = [
        RTSCTSNode(0, radius, transceive_range, 1, 1),
        RTSCTSNode(1, radius, transceive_range, 1, 4),
        RTSCTSNode(2, radius, transceive_range, 1, 2),
        RTSCTSNode(3, radius, transceive_range, 1, 3),
        RTSCTSNode(4, radius, transceive_range, 2, 1),
        RTSCTSNode(5, radius, transceive_range, 3, 4),
    ]

    for node in nodes:
        node.add_neighbors(nodes)

    simulation_time = 0
    active_transmissions = []

    vis = Visualizer(X, Y)

    while True:
        logging.debug("simulation_time: {}".format(simulation_time))

        if simulation_time == 3:
            nodes[0].send(HighLevelMessage(5, "Hallo from 0", 5))
            nodes[1].send(HighLevelMessage(4, "Hallo from 1", 20))
            nodes[2].send(HighLevelMessage(3, "Hallo from 2", 7))
            nodes[3].send(HighLevelMessage(2, "Hallo from 3", 2))
            nodes[4].send(HighLevelMessage(1, "Hallo from 4", 30))
            nodes[5].send(HighLevelMessage(0, "Hallo from 5", 4))



        for node in nodes:
            node.execute_state_machine(simulation_time, active_transmissions)

        for node in nodes:
            msg = node.receive()
            if msg:
                logging.info("Node {} received: {}".format(node.id, msg))

        # 353, 378
        vis.draw_function(nodes)
        simulation_time += 1

if __name__ == '__main__':
    main()
