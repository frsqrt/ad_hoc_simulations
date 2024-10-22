import matplotlib.pyplot as plt
from node import Transmission, Message, Node, NodeState

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
        colours = [node.get_color_based_on_state() for node in nodes]

        established_links = [
            (node.receive_buffer.source.x_pos,
             node.receive_buffer.source.y_pos,
             node.x_pos - node.receive_buffer.source.x_pos,
             node.y_pos - node.receive_buffer.source.y_pos)
            for node in nodes if node.state == NodeState.Receiving]

        self.ax.clear()
        self.ax.scatter(x_coords, y_coords, clip_on=False, color=colours)

        for link in established_links:
            self.ax.arrow(*link)

        for config in node_circle_range:
            self.ax.add_patch(plt.Circle(*config, **self.circle_parameters))

        self.ax.set_xlim((-10, self.x + 10))
        self.ax.set_ylim((-10, self.y + 10))
        self.ax.set_aspect('equal')  # Ensure the circles are not distorted

        self.ax.set_title('Current network state')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        plt.pause(0.5)


def main():
    N = 2  # Number of nodes
    X = 5  # Window size
    Y = 5  # Window size
    radius = 0.25  # Radius of each circle
    min_distance = 0.5  # Minimum distance between circles
    transceive_range = 5.0  # Distance a node can send and receive messages
    num_of_transmissions_per_node = 1  # Number of transmissions a node will make
    propagation_time = 1  # Measured in units/time (5 means the message travels 5 units per loop iteration)

    nodes = [Node(0, NodeState.Idle, radius, transceive_range, 1, 1, [], None, [], 0),
             Node(1, NodeState.Idle, radius, transceive_range, 1, 2, [], None, [], 0),
             Node(2, NodeState.Idle, radius, transceive_range, 1, 4, [], None, [], 0)]

    nodes[0].send_schedule.append(Transmission(0, nodes[0], 3, 0, Message("hello", 5)))
    nodes[2].send_schedule.append(Transmission(0, nodes[2], 4, 0, Message("hello", 5)))

    # Add neighbors to nodes
    for node in nodes:
        node.add_neighbors(nodes)

    simulation_time = 0
    active_transmissions = []

    vis = Visualizer(X, Y)

    while True:
        print("simulation_time: ", simulation_time)

        # Plot each circle
        for node in nodes:
            if node.state == NodeState.Idle:
                node.idle_state(simulation_time, active_transmissions)
            elif node.state == NodeState.Sending:
                node.sending_state()
            elif node.state == NodeState.Receiving:
                node.receiving_state(simulation_time, active_transmissions)

        vis.draw_function(nodes)

        simulation_time += 1


if __name__ == '__main__':
    main()
