from dataclasses import dataclass
from enum import Enum

"""
`HighLevelMessage` stores the actual data message. The `send_schedule` of a node is a list of `HighLevelMessage`
"""
@dataclass
class HighLevelMessage:
    target: int
    planned_transmit_time: int
    content: str
    length: int

class MessageType(Enum):
    Data = 0,
    RTS = 1,
    CTS = 2,
    ACK = 3

"""
`Message` is used for RTS, CTS, ACK and data messages.
"""
@dataclass
class Message:
    sequence_number: int
    target: int
    source: int
    content: str
    length: int

    def get_ack(self, simulation_time: int) -> HighLevelMessage:
        return HighLevelMessage(self.source, simulation_time, "ack", 1)

    def get_type(self) -> MessageType:
        message_content_lower = self.content.lower()
        if "rts" in message_content_lower:
            return MessageType.RTS
        elif "cts" in message_content_lower:
            return MessageType.CTS
        elif "ack" in message_content_lower:
            return MessageType.ACK
        else:
            return MessageType.Data

"""
`Transmission` is a wrapper for `Message` to include planned and actual transmission times.
"""
@dataclass
class Transmission:
    transmit_time: int
    message: Message

