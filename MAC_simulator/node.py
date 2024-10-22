from dataclasses import dataclass
from enum import Enum
import numpy as np
from typing import Protocol
from random import randint


class NodeState(Enum):
    Idle = 1
    Sending = 2
    Receiving = 3
    Waiting = 4


@dataclass
class Message:
    content: str
    length: int


class MACProtocol(Protocol):

    buffer: list
    backoff: int

    def generate_packet(self, message: Message):
        """
        This tells the protocol to generate a packet with the given message.
        The protocol then internally has to push the correct packet, like maybe an RTS into the sending queue

        :param message:
        :return:
        """

    def receive_packet(self, message: Message) -> None:
        """
        Parse incoming tranmission
        Checks if the transmission is relevant for this node.
        Schedules reply transmission into the send_buffer
        :return: Nothing
        """

    def send_packet(self) -> Message:
        """
        Keeps track of the back_off (gets called every idle tick), send_schedule, and buffer.
        Returns a transmission if it is time to send or as a reaction to a cts.
        Once sent the physical layer should immediately switch to a transmitting state.

        :return:
        """
        ...


class ALOHA:
    def __init__(self):
        self.backoff = 2
        self.buffer = []

    def generate_packet(self, message: Message):
        self.buffer.append(message)

    def receive_packet(self, message: Message) -> None:
        pass

    def send_packet(self) -> Message:
        if not self.buffer:
            return
        self.backoff -= 1
        if self.backoff == 0:
            self.backoff = randint(1, 16)
            return self.buffer.pop(0)


@dataclass
class Node:
    id: int
    state: NodeState
    radius: float
    transceive_range: float
    x_pos: float
    y_pos: float
    neighbors: list
    currently_receiving: object
    send_schedule: list
    state_counter: int
    protocol: MACProtocol

    def idle_state(self, simulation_time: int, active_transmissions: list['Transmission']) -> None:
        # Check if node can receive
        collision = self.has_collided(simulation_time, active_transmissions)

        if collision:
            return

        if self.state == NodeState.Idle and (packet := self.protocol.send_packet()):
            print(f'{self.id} has started sending')
            self.state = NodeState.Sending
            self.state_counter = packet.length

            transmission = Transmission(0, self, simulation_time, simulation_time, packet)
            active_transmissions.append(transmission)
            # packet.actual_transmit_time = simulation_time

    def sending_state(self):
        self.state_counter -= 1
        if self.state_counter == 0:
            self.state = NodeState.Idle

    def receiving_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        # check for collisions
        if self.has_collided(simulation_time, active_transmissions):
            return None

        print(f'{self.id} is receiving')


        self.state_counter -= 1
        if self.state_counter == 0:
            self.state = NodeState.Idle
            self.protocol.receive_packet(self.currently_receiving.message)
            self.currently_receiving = None

    def has_collided(self, simulation_time: int, active_transmissions: list['Transmission']) -> bool:
        """
        Checks if more than 2 receiving messages appear at the same time.

        Returns true in the case of a collision.
        In the case we are starting to receive the first part of a message we change state to be receiving.

        (Now in order to be sure the message was never lost the receiving
        state function will release the message once the counter reaches 0.)

        :param simulation_time:
        :param active_transmissions:
        :return:
        """

        # Get currently arriving neighbours
        def predicate_close_and_arriving(t: Transmission) -> bool:
            lb = t.actual_transmit_time + self.get_packet_travel_time(t.source)
            ub = t.actual_transmit_time + self.get_packet_travel_time(t.source) + t.message.length

            return simulation_time in list(range(lb, ub)) and t.source in self.neighbors

        current_packets: list[Transmission] = [t for t in active_transmissions if predicate_close_and_arriving(t)]

        if simulation_time == 20:
            z = 4

        match current_packets:
            case []:
                return False
            case [packet] if packet.actual_transmit_time + self.get_packet_travel_time(packet.source) == simulation_time:
                print(f'{self.id} packet arrival detected')
                self.state = NodeState.Receiving
                self.currently_receiving = packet
                self.state_counter = packet.message.length
                return False
            case [_, _, *_]:
                print("collision detected")
                self.state = NodeState.Idle
                self.state_counter = 0
                self.currently_receiving = None
                return True
        return False

    def get_packet_travel_time(self, sender) -> int:
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


def create_new_node(index: int, radius: float, transceiver_range: float, x_size: int, y_size: int) -> Node:
    x = np.random.uniform(radius, x_size - radius)
    y = np.random.uniform(radius, y_size - radius)

    return Node(index, NodeState.Idle, radius, transceiver_range, x, y, [], [], [], 0)


def can_add_node_without_overlap(new_node: Node, node_list: list, min_distance: float) -> bool:
    for node in node_list:
        distance = get_distance_between_nodes(new_node, node)
        # Check if the distance between the new node and an existing node is less than the sum of their radii plus the minimum distance
        if distance < (new_node.radius + node.radius + min_distance):
            return False  # Overlap or too close detected
    return True  # No overlap and minimum distance maintained
