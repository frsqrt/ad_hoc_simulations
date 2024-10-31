from dataclasses import dataclass
import numpy as np
from enum import Enum
from transmission import HighLevelMessage, Message, Transmission, MessageType
from protocols import MACProtocol, ALOHA

class State(Enum):
    Idle = 0,
    Sending = 1,
    Receiving = 2,
    BackingOff = 3,
    WaitingForAnswer = 4

@dataclass
class Node:
    id: int
    radius: float
    transceive_range: float
    x_pos: float
    y_pos: float

    neighbors: list['Node']
    # Stores the HighLevelMessages and the node wants to send
    send_schedule: list[HighLevelMessage]
    state: State

    protocol: MACProtocol

    def __init__(self):
        self.send_schedule = []
        self.state = State.Idle
        self.neighbors = []

    """
    Executes one state machine cycle.

    :param simulation_time: current time of the simulation
    """
    def execute_state_machine(self, simulation_time: int, active_transmissions: list[Transmission]):
        print("node {} - [State: {}]".format(self.id, self.state.name))
        if self.state == State.Idle:
            self.idle_state(simulation_time, active_transmissions)
        elif self.state == State.Receiving:
            self.receiving_state(simulation_time, active_transmissions)
        elif self.state == State.Sending:
            self.sending_state(simulation_time)   
        elif self.state == State.BackingOff:
            self.backing_off_state(simulation_time)   
        elif self.state == State.WaitingForAnswer:
            self.waiting_for_answer_state(simulation_time, active_transmissions)   

    def idle_state(self, simulation_time: int, active_transmissions: list[Transmission]):
        """
        This is the starting state of every protocol.

        :param simulation_time: current time of the simulation
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

    def backing_off_state(self, simulation_time: int):
        """
        The protocol is in this state after not receiving an ACK.

        :param simulation_time: current time of the simulation
        """

    def waiting_for_answer_state(self, simulation_time: int, active_transmissions: list[Transmission]):
        """
        The protocol is in this state while waiting for an answer after sending a message.

        :param simulation_time: current time of the simulation
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
            if get_node_by_id(self.neighbors, transmission.message.source):
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

class ALOHANode(Node):
    def __init__(self, id: int, radius: float, transceive_range: float, x_pos: float, y_pos: float):
        self.id = id
        self.radius = radius
        self.transceive_range = transceive_range
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.protocol = ALOHA()

        # State counters - every state has its own counter, 
        # so we can e.g. still count down `wait_for_answer_counter` while being in thereceiving state
        self.sending_state_counter = 0
        self.receiving_state_counter = 0
        self.waiting_for_answer_state_counter = 0
        # the backoff counter is inside the protocol

        super().__init__()

    def transition_to_receiving(self, message: Message):
        self.protocol.currently_receiving = message
        self.state = State.Receiving
        self.receiving_state_counter = message.length
        print("\tReceiving: [{}], Transition to {}".format(message, self.state.name))


    def transition_to_sending(self, simulation_time: int, high_level_message: HighLevelMessage, active_transmissions: list[Transmission]):
        message_to_send = self.protocol.generate_message(self.id, high_level_message)

        self.state = State.Sending
        self.sending_state_counter = message_to_send.length
        self.protocol.currently_transmitting = message_to_send

        active_transmissions.append(Transmission(simulation_time, message_to_send))
        print("\tWants to send [{}], transition to {}".format(message_to_send, self.state.name))


    def transition_to_wait_for_answer(self, new_wait_for_answer_counter: int):
        self.state = State.WaitingForAnswer
        self.waiting_for_answer_state_counter = new_wait_for_answer_counter
        print("\tTransition to {}".format(self.state))


    def transition_to_idle(self):
        self.state = State.Idle
        self.sending_state_counter = 0
        self.receiving_state_counter = 0
        self.waiting_for_answer_state_counter = 0
        self.protocol.backoff = 0
        self.protocol.currently_receiving = None
        self.protocol.currently_transmitting = None
        print("\tTransition to {}".format(self.state))


    def transition_to_backoff(self):
        self.state = State.BackingOff
        self.protocol.set_backoff()
        print("\tTransition to {} with backoff={}".format(self.state, self.protocol.backoff))


    def process_received_message(self, received_message: Message, simulation_time: int, active_transmissions: list[Transmission]):
        self.protocol.currently_receiving = None
        print("\tFinished receiving [{}]".format(received_message))

        # Check whether the message was meant for us
        if received_message.target != self.id:
            # Either return to `State.Idle` or `State.WaitingForAnswer`
            if self.waiting_for_answer_state_counter > 0:
                # We were in `State.Receiving` for `received_message.length` ticks, so decrease `self.waiting_for_answer_state_counter`
                # by that amount.
                self.waiting_for_answer_state_counter -= received_message.length
                self.transition_to_wait_for_answer(self.waiting_for_answer_state_counter)
            else:
                self.transition_to_idle()

            return

        # The message was meant for us
        message_type = received_message.get_type()
        if message_type == MessageType.Data:
            # In case we were waiting for an ACK, we discard the data message and go back into `State.WaitingForAnswer`
            if self.waiting_for_answer_state_counter > 0:
                # We were in `State.Receiving` for `received_message.length` ticks, so decrease `self.waiting_for_answer_state_counter`
                # by that amount.
                self.waiting_for_answer_state_counter -= received_message.length
                self.transition_to_wait_for_answer(self.waiting_for_answer_state_counter)
                return
            
            self.transition_to_sending(simulation_time, received_message.get_ack(simulation_time), active_transmissions)
        elif message_type == MessageType.ACK:
            # Remove `HighLevelMessage` from `send_schedule` since it was successfully transmitted and we do not want 
            # to try to retransmit the message at any point
            self.send_schedule.pop(0)
            self.transition_to_idle()


    def idle_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        # Anything to receive?
        if transmissions := self.get_receivable_messages(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    self.transition_to_receiving(transmission.message)
                    return
                case [_, _, *_]:
                    print("\tCollision, received more than one Message at the same time.")
                    self.transition_to_idle()
                    return
            
        # Anything to send?
        for high_level_message in self.send_schedule:
            if high_level_message.planned_transmit_time <= simulation_time:
                self.transition_to_sending(simulation_time, high_level_message, active_transmissions)
                return


    def sending_state(self, simulation_time: int):
        self.sending_state_counter -= 1
        print("\tstate_counter: {}".format(self.sending_state_counter))
        if self.sending_state_counter <= 0:
            # Message is fully sent
            message_type = self.protocol.currently_transmitting.get_type()

            print("\tFinished sending [{}]".format(self.protocol.currently_transmitting))

            # Check whether we sent Data or an ACK
            if message_type == MessageType.Data:
                self.transition_to_wait_for_answer(50)
            elif message_type == MessageType.ACK:
                self.transition_to_idle()


    def receiving_state(self, simulation_time: int, active_transmissions: list[Transmission]):
        # Check for collisions
        if transmissions := self.get_receivable_messages(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    if transmission.message != self.protocol.currently_receiving:
                        print("\tCollision with [{}]".format(transmission.message))
                        self.transition_to_idle()
                        return
                case [_, _, *_]:
                    print("\tCollision, received more than one Message at the same time.")
                    self.transition_to_idle()
                    return

        self.receiving_state_counter -= 1
        print("\tstate_counter: {}".format(self.receiving_state_counter))
        if self.receiving_state_counter <= 0:
            self.process_received_message(self.protocol.currently_receiving, simulation_time, active_transmissions)


    def waiting_for_answer_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        self.waiting_for_answer_state_counter -= 1
        print("\tstate_counter: {}".format(self.waiting_for_answer_state_counter))

        if self.waiting_for_answer_state_counter <= 0:
            self.transition_to_backoff()
            return

        # Anything to receive?
        if transmissions := self.get_receivable_messages(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    self.transition_to_receiving(transmission.message)
                    return
                case [_, _, *_]:
                    print("\tCollision, received more than one Message at the same time.")
                    self.transition_to_idle()
                    return


    def backing_off_state(self, simulation_time: int):
        self.protocol.backoff -= 1
        print("\tbackoff {}".format(self.protocol.backoff))
        if self.protocol.backoff == 0:
            self.transition_to_idle()
        

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