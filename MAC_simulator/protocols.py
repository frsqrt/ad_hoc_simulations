import logging
from dataclasses import dataclass
from random import randint
from typing import Protocol
from collections import defaultdict

from transmission import HighLevelMessage, Message, MessageType


@dataclass
class DSDVEntry:
    next: int
    distance_metric: int | float
    seq: int


class DSDVRoutingProtocol:

    def __init__(self, id: int):
        # maps the target to its respective table entry
        self.table: dict[int: DSDVEntry] = {id: DSDVEntry(id, 0, 0)}
        self.staleness: dict[int: int] = defaultdict(lambda: 0)
        self.max_share_table_backoff = 200
        self.share_table_backoff = randint(0, self.max_share_table_backoff)
        self.id = id
        self.buffer: list[HighLevelMessage] = []
        self.sequence = 0

    def get_next(self, target: int) -> int:
        return self.table[target].next

    def send(self, msg: HighLevelMessage):
        """
        Messages can only be sent if the routing algorithm is aware of them so it now becomes the primary buffer for planned transmissions.
        :param msg:
        :return:
        """
        logging.info(f'Message {msg} was added to buffer of {self.id}.')
        self.buffer.append(msg)

    def tick(self) -> HighLevelMessage | None:
        """
        Either triggers a broadcast or pushes a message to the buffer depending on if we still have something waiting on a route.
        :return:
        """
        # Check for lost connections
        self.check_staleness()

        if self.buffer:
            for msg in self.buffer:
                if msg.target in self.table and self.table[msg.target].distance_metric != float('inf'):
                    self.buffer.remove(msg)
                    return msg.configure_routing(self.table[msg.target].next, self.id)

        self.share_table_backoff -= 1
        if self.share_table_backoff <= 0:
            self.share_table_backoff = randint(0, self.max_share_table_backoff)
            self.sequence += 2
            self.table[self.id].seq = self.sequence
            return HighLevelMessage(-1, self.table, 1)

    def check_staleness(self):
        for node in self.staleness:
            self.staleness[node] += 1
            if (self.staleness[node] > 4 * self.max_share_table_backoff
                    and self.table[node].seq % 2 == 0
                    and self.table[node].next == node):
                logging.debug(f'Staleness detected for node {node}; detected by node {self.id}.')
                self.table[node].seq += 1
                self.table[node].distance_metric = float('inf')

    def reply(self, msg: Message, distance: int) -> HighLevelMessage | None:
        """
        Keeps track of routing information

        :param msg: incoming data
        :param distance: calculated based on "signal strength" by the scenario.
        :return: Either nothing or another message, be it table broadcast or to pass along a route finding messge.
        """

        self.staleness[msg.source] = 0

        if msg.get_type() == MessageType.Data:
            # takes care of an actual route that needs to be walked.
            if msg.route_target == self.id:
                logging.info(f'Received message: {msg.content}. on the other side of the route.')
            if msg.route_target != self.id and msg.route_target in self.table:
                return HighLevelMessage(self.table[msg.route_target].next, msg.content, msg.length, msg.route_target, msg.route_source)
            if msg.route_target not in self.table:
                logging.warning(f'Message from {msg.route_source} to {msg.route_target} died at {self.id}.')

        if msg.get_type() == MessageType.BROADCAST:
            self.update_tables(distance, msg)

        return self.tick()

    def update_tables(self, distance, msg):
        table: dict[int: DSDVEntry] = msg.content
        # prevent lookup errors.
        for target in table:
            if target not in self.table:
                self.table[target] = DSDVEntry(-1, float('inf'), -1)
        for target, entry in table.items():
            current_entry = self.table[target]
            adjusted_distance = entry.distance_metric + distance

            # Check staleness and distance.
            if entry.seq > current_entry.seq and current_entry.distance_metric >= adjusted_distance:
                self.table[target] = DSDVEntry(msg.source, adjusted_distance, entry.seq)

            # Check odd sequence number in case of infinite distance.
            elif entry.seq % 2 == 1 and entry.seq > current_entry.seq:
                self.table[target] = DSDVEntry(entry.next, entry.distance_metric, entry.seq)


class MACProtocol(Protocol):
    def __init__(self):
        self.backoff = 0
        self.max_backoff = 16
        self.min_backoff = 1
        self.sequence_number = 0
        self.currently_transmitting = None
        self.currently_receiving = None

    # The currently transmitted `Transmission`
    currently_receiving: Message

    # The message we are currently receiving
    receiving_message: Message

    # Stores the current back-off time
    backoff: int

    max_backoff: int
    min_backoff: int

    # Sequence number for messages
    sequence_number: int
    

    def set_backoff(self):
        self.backoff = randint(self.min_backoff, self.max_backoff)
        if self.max_backoff < 256:
            self.max_backoff *= 2


    def reset_max_backoff(self):
        self.max_backoff = 16


    def next_sequence_number(self) -> int:
        self.sequence_number += 1
        return self.sequence_number
    

    def generate_data(self, source_id: int, high_level_message: HighLevelMessage) -> Message:
        return Message(self.next_sequence_number(), high_level_message.target, source_id, high_level_message.content,
                       high_level_message.length, high_level_message.route_target, high_level_message.route_source)

    def generate_ack(self, source_id, target_id: int) -> Message:
        return Message(self.next_sequence_number(), target_id, source_id, "ack", 1)

    def generate_broadcast(self, source_id: int, high_level_message: HighLevelMessage) -> Message:
        return Message(self.next_sequence_number(), high_level_message.target, source_id, high_level_message.content,
                       high_level_message.length)


class ALOHA(MACProtocol):    
    def __init__(self):
        super().__init__()


    def set_backoff(self):
        return super().set_backoff()
    

class RTSCTSALOHA(MACProtocol): 
    def __init__(self):
        super().__init__()


    def set_backoff(self):
        return super().set_backoff()
    

    def generate_rts(self, source_id: int, target_id: int, node_distance: int, data_length: int):
        # wait for: propagation time * 3 + message length + CTS + ACK
        return Message(self.next_sequence_number(), target_id, source_id, f"rts {int(node_distance * 3 + data_length + 1 + 1)} {int(data_length)}", 1)
    
    
    def generate_cts(self, source_id: int, target_id: int, node_distance: int, data_length: int):
        # wait for: propagation time * 2 + message length + ACK
        return Message(self.next_sequence_number(), target_id, source_id, f"cts {int(node_distance * 2 + data_length + 1)}", 1)