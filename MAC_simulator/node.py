from dataclasses import dataclass
import numpy as np
import logging
from enum import Enum
from transmission import HighLevelMessage, Message, Transmission, MessageType
from protocols import MACProtocol, ALOHA, RTSCTSALOHA

class State(Enum):
    Idle = 0,
    Sending = 1,
    Receiving = 2,
    BackingOff = 3,
    WaitingForAnswer = 4,
    ReceivedCTSRTSBackoff = 5


@dataclass
class Node:
    id: int
    radius: float
    transceive_range: float
    x_pos: float
    y_pos: float
    neighbors: list['Node']

    # Stores the HighLevelMessages that the node wants to send
    send_schedule: list[HighLevelMessage]

    # Stores the last received non-meta Message 
    receive_buffer: Message

    # `receive_buffer` gets copied into `received_message` as soon as the sender receives the ACK
    # gets consumed using `receive`
    received_message: Message

    state: State

    protocol: MACProtocol

    def __init__(self):
        self.send_schedule = []
        self.state = State.Idle
        self.neighbors = []
        self.receive_buffer = None
        self.received_message = None


    def send(self, message_to_send: HighLevelMessage):
        self.send_schedule.append(message_to_send)


    def receive(self) -> Message | None:
        received_message_ret = self.received_message
        self.received_message = None
        return received_message_ret


    def execute_state_machine(self, simulation_time: int, active_transmissions: list[Transmission]):
        """
        Executes one state machine cycle.

        :param simulation_time: current time of the simulation
        """


    def idle_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        """
        Sends or receives messages.
        """


    def sending_state(self, simulation_time: int):
        """
        The protocol is in this state while sending a message. Stays in this state till `state_counter` is 0.

        :param simulation_time: current time of the simulation
        """


    def receiving_state(self, simulation_time: int):
        """
        The protocol is in this state while receiving a message. Stays in this state till `state_counter` is 0.

        :param simulation_time: current time of the simulation
        """


    def backing_off_state(self, simulation_time: int, active_transmissions: list[HighLevelMessage]):
        """
        The protocol is in this state after not receiving an ACK.

        :param simulation_time: current time of the simulation
        """


    def waiting_for_answer_state(self, simulation_time: int, active_transmissions: list[Transmission]):
        """
        The protocol is in this state while waiting for an answer after sending a message.

        :param simulation_time: current time of the simulation
        """


    def transition_to_receiving(self, message: Message):
        """
        Transition to Receiving
        """

    def transition_to_sending(self, simulation_time: int, message_to_send: Message, active_transmissions: list[Transmission]):
        """
        Transition to Sending
        """


    def transition_to_wait_for_answer(self, wait_for_ack_counter: int, wait_for_cts_counter: int, wait_for_data_counter: int):
        """
        Transition to WaitingForAnswer
        """


    def transition_to_idle(self):
        """
        Transition to Idle
        """


    def transition_to_backoff(self):
        """
        Transition to Backoff
        """


    """
    Return all messages the node can currently receive. If more than one gets returned, a collision occured.
    """
    def get_receivable_messages(self, simulation_time: int, active_transmissions: list[Transmission]) -> list[Message]:
        def predicate_close_and_arriving(t: Transmission) -> bool:
            lb = t.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, t.message.source))
            ub = t.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, t.message.source)) + t.message.length

            return simulation_time in list(range(lb, ub))

        receivable_packets = []
        for transmission in active_transmissions:
            # Check whether the message was sent by one of the nodes neighbors
            if get_node_by_id(self.neighbors, transmission.message.source):
                # Check whether the message can already be received
                if predicate_close_and_arriving(transmission):
                    receivable_packets.append(transmission)

        return receivable_packets


    def get_packet_travel_time(self, sender) -> int:
        return int(get_distance_between_nodes(self, sender))


    def add_neighbors(self, nodes):
        for node in nodes:
            if node.id != self.id:
                distance = get_distance_between_nodes(self, node)
                # Check if the distance between the new node and an existing node is less than the sum of their radii plus the minimum distance
                if distance < (self.radius + node.radius + self.transceive_range):
                    self.neighbors.append(node)

    

def get_distance_between_nodes(n1: Node, n2: Node) -> float:
    return np.sqrt((n1.x_pos - n2.x_pos) ** 2 + (n1.y_pos - n2.y_pos) ** 2)

def get_node_by_id(nodes: list[Node], id: int) -> Node:
    for node in nodes:
        if node.id == id:
            return node

    return None

"""
def create_new_node(index: int, radius: float, transceiver_range: float, x_size: int, y_size: int) -> Node:
    x = np.random.uniform(radius, x_size - radius)
    y = np.random.uniform(radius, y_size - radius)

    return Node(index, NodeState.Idle, radius, transceiver_range, x, y, [], [], [], 0)

def can_add_node_without_overlap(new_node: Node, node_list: list, min_distance: float) -> bool:
    for node in node_list:
        distance = get_distance_between_nodes(new_node, node)
        if distance < (new_node.radius + node.radius + min_distance):
            return False 
    return True
"""