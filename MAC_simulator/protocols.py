from dataclasses import dataclass
from random import randint
from typing import Protocol
from enum import Enum
from transmission import HighLevelMessage, Message


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
        if self.max_backoff < 1024:
            self.max_backoff *= 2


    def reset_max_backoff(self):
        self.max_backoff = 16


    def next_sequence_number(self) -> int:
        self.sequence_number += 1
        return self.sequence_number
    

    def generate_data(self, source_id: int, high_level_message: HighLevelMessage) -> Message:
        return Message(self.next_sequence_number(), high_level_message.target, source_id, high_level_message.content, high_level_message.length)
    

    def generate_ack(self, source_id, target_id: int) -> Message:
        return Message(self.next_sequence_number(), target_id, source_id, "ack", 1)


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