from dataclasses import dataclass
from enum import Enum
import numpy as np
from typing import Protocol


#
# class MAC_protocol(Protocol):
#     def receive_packet(self, simulation_time: int, transmission: "Transmission") -> None:
#         """
#         Parse incoming tranmission
#         Checks if the transmission is relevant for this node.
#         Schedules reply transmission into the send_schedule
#         :return: Nothing
#         """
#
#     def send_packet(self) -> "Transmission" | None:
#         """
#         Keeps track of the back_off, send_schedule, and buffer.
#         Returns a transmission if it is time to send or as a reaction to a cts.
#
#         :return:
#         """
#         ...
#
#
# class ALOHA:
#     ...


class NodeState(Enum):
    Idle = 1
    Sending = 2
    Receiving = 3
    Waiting = 4

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
    # protocol: MAC_protocol

    def get_packet_arrival_time(self, sender) -> int:
        return int(get_distance_between_nodes(self, sender))

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
    return True # No overlap and minimum distance maintained


def idle_state(simulation_time: int, node: Node, active_transmissions: list[Transmission]) -> None | Transmission:
    # Check if node can receive
    for transmission in active_transmissions:
        # Sanity check that we can receive the transmission
        if transmission.source not in node.neighbors:
            continue

        # Check whether we can already receive the message
        transmission_propagation_time = simulation_time - transmission.actual_transmit_time
        if transmission_propagation_time == node.get_packet_arrival_time(transmission.source):
            # Check whether the node was able to receive a message in a previous iteration. If so -> collision
            if node.state == NodeState.Receiving:
                print("collision in idle state")
                node.state = NodeState.Idle
                node.receive_buffer = None
                node.state_counter = 0
                return

            node.state = NodeState.Receiving
            node.state_counter = transmission.message.length
            node.receive_buffer = transmission
            

    # Check if node wants to send
    for transmission in node.send_schedule:
        if transmission.planned_transmit_time <= simulation_time:
            transmission.actual_transmit_time = simulation_time
            active_transmissions.append(transmission)
            node.send_schedule.remove(transmission)
            node.state = NodeState.Sending
            node.state_counter = transmission.message.length


def sending_state(node: Node):
    node.state_counter -= 1
    if node.state_counter == 0:
        node.state = NodeState.Idle


def receiving_state(simulation_time: int, node: Node, active_transmissions: list[Transmission]):
    # Check for collisions
    for transmission in active_transmissions:
        # Sanity check that we can receive the transmission
        if transmission.source not in node.neighbors:
            continue

        if transmission == node.receive_buffer:
            continue

        # Check whether we can already receive the message
        transmission_propagation_time = simulation_time - transmission.actual_transmit_time
        if transmission_propagation_time == node.get_packet_arrival_time(transmission.source):
            print("collision in receive state")
            node.state = NodeState.Idle
            node.state_counter = 0
            node.receive_buffer = None
            return

    node.state_counter -= 1
    if node.state_counter == 0:
        # TODO: if data was received, send ACK, don't go idle
        node.state = NodeState.Idle
        # active_transmissions.remove(node.receive_buffer)