from dataclasses import dataclass
from enum import Enum
import numpy as np

class NodeState(Enum):
    Idle = 1
    Sending = 2
    Receiving = 3

@dataclass
class Message:
    content: str
    length: int

@dataclass
class Node:
    id: int
    state: NodeState
    radius: float
    transceive_range: float
    x_pos: float
    y_pos: float
    neighbors: list
    receive_buffer: object
    send_schedule: list
    state_counter: int

    def add_neighbors(self, nodes):
        for node in nodes:
            if node.id != self.id:
                distance = get_distance_between_nodes(self, node)
                # Check if the distance between the new node and an existing node is less than the sum of their radii plus the minimum distance
                if distance < (self.radius + node.radius + self.transceive_range):
                    self.neighbors.append(node)

    def get_color_based_on_state(self) -> str:
        if self.state == NodeState.Idle:
            return 'blue'
        elif self.state == NodeState.Sending:
            return 'red'
        else:
            return 'green'

@dataclass
class Transmission:
    id: int
    source: Node
    planned_transmit_time: int
    actual_transmit_time: int
    message: Message

def get_distance_between_nodes(n1: Node, n2: Node) -> float:
    return np.sqrt((n1.x_pos - n2.x_pos) ** 2 + (n1.y_pos - n2.y_pos) ** 2)

def create_new_node(index: int, radius: float, range: float, x_size: int, y_size: int) -> Node:
    x = np.random.uniform(radius, x_size - radius)
    y = np.random.uniform(radius, y_size - radius)

    return Node(index, NodeState.Idle, radius, range, x, y, [], [], [], 0)
    
def can_add_node_without_overlap(new_node: Node, node_list: list, min_distance: float) -> bool:
    for node in node_list:
        distance = get_distance_between_nodes(new_node, node)
        # Check if the distance between the new node and an existing node is less than the sum of their radii plus the minimum distance
        if distance < (new_node.radius + node.radius + min_distance):
            return False  # Overlap or too close detected
    return True  # No overlap and minimum distance maintained