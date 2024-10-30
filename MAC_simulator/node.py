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
    send_schedule: list[HighLevelMessage]

    state: State
    state_counter: int
    protocol: MACProtocol

    def __init__(self):
        self.send_schedule = []
        self.state = State.Idle
        self.state_counter = 0
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

    def get_receivable_message(self, simulation_time: int, active_transmissions: list[Transmission]) -> list[Message]:
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

        super().__init__()


    def idle_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        # Anything to receive?
        if transmissions := self.get_receivable_message(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    # Transition to `State.Receiving`
                    self.protocol.currently_receiving = transmission.message
                    self.state = State.Receiving
                    self.state_counter = transmission.message.length
                    print("\tReceiving: [{}], Transition to {}".format(transmission.message, self.state.name))
                    return
                case [_, _, *_]:
                    print(f'has_collided (id: {self.id}): Collision')
                    self.state = State.Idle
                    self.state_counter = 0
                    self.currently_receiving = None
                    return True
            
        # Anything to send?
        for high_level_message in self.send_schedule:
            if high_level_message.planned_transmit_time <= simulation_time:
                # Generate message to send
                message_to_send = self.protocol.generate_message(self.id, high_level_message)

                # Transition to `State.Sending`
                self.state = State.Sending
                self.state_counter = message_to_send.length
                self.protocol.currently_transmitting = message_to_send

                # Put message on the air                
                active_transmissions.append(Transmission(simulation_time, message_to_send))
                print("\tWants to send [{}], transition to {}".format(message_to_send, self.state.name))
                return


    def sending_state(self, simulation_time: int):
        self.state_counter -= 1
        print("\tstate_counter: {}".format(self.state_counter))
        if self.state_counter == 0:
            # Message is fully sent
            message_type = self.protocol.currently_transmitting.get_type()

            print("\tFinished sending [{}]".format(self.protocol.currently_transmitting))

            # Check whether we sent Data or an ACK
            if message_type == MessageType.Data:
                self.state = State.WaitingForAnswer
                self.state_counter = 50
                print("\tTransition to {}".format(self.state))
            elif message_type == MessageType.ACK:
                self.state = State.Idle
                print("\tTransition to {}".format(self.state))


    def receiving_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        if transmissions := self.get_receivable_message(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    print("\tCollision with [{}]".format(transmission))

                    # Transition to `State.Receiving`
                    self.protocol.currently_receiving = transmission.message
                    self.state = State.Receiving
                    self.state_counter = transmission.message.length
                    print("\tTransition to {}".format(self.state.name))
                case [_, _, *_]:
                    print(f'has_collided (id: {self.id}): Collision')
                    self.state = State.Idle
                    self.state_counter = 0
                    self.currently_receiving = None
                    return

        self.state_counter -= 1
        print("\tstate_counter: {}".format(self.state_counter))
        if self.state_counter == 0:
            message_type = self.protocol.currently_receiving.get_type()
            print("\tFinished receiving [{}]".format(self.protocol.currently_receiving))
            if message_type == MessageType.Data:
                # Generate ACK message
                message_to_send = self.protocol.generate_message(self.id, self.protocol.currently_receiving.get_ack(simulation_time))

                # Transition to `State.Sending`
                self.state = State.Sending
                self.state_counter = message_to_send.length
                self.protocol.currently_transmitting = message_to_send

                # Put message on the air                
                active_transmissions.append(Transmission(simulation_time, message_to_send))
                print("\tTransition to {}".format(self.state))
            elif message_type == MessageType.ACK:
                self.state = State.Idle
                self.state_counter = 0
                self.protocol.currently_receiving = None

                # Remove `HighLevelMessage` from `send_schedule` since it was successfully transmitted and we do not want to try to retransmit the message
                # at any point
                self.send_schedule.pop(0)
                print("\tTransition to {}".format(self.state))


    def backing_off_state(self, simulation_time: int):
        self.protocol.backoff -= 1
        print("\tbackoff {}".format(self.protocol.backoff))
        if self.protocol.backoff == 0:
            self.state = State.Idle
            print("\tTransition to {}".format(self.state))


    def waiting_for_answer_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        self.state_counter -= 1

        # Anything to receive?
        if transmissions := self.get_receivable_message(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    if transmission.message.target == self.id and transmission.message.get_type() == MessageType.ACK:
                        # Transition to `State.Receiving`
                        self.protocol.currently_receiving = transmission.message
                        self.state = State.Receiving
                        self.state_counter = transmission.message.length
                        print("\tReceiving: [{}], Transition to {}".format(transmission.message, self.state.name))
                case [_, _, *_]:
                    print(f'has_collided (id: {self.id}): Collision')
                    self.state = State.Idle
                    self.state_counter = 0
                    self.currently_receiving = None

            return

        print("\tstate_counter: {}".format(self.state_counter))
        if self.state_counter == 0:
            self.state = State.BackingOff
            self.protocol.set_backoff()
            print("\tTransition to {} with backoff={}".format(self.state, self.protocol.backoff))
            return
                        
        
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