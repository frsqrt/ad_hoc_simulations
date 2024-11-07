from dataclasses import dataclass
from enum import Enum

"""
`HighLevelMessage` stores the actual data message. The `send_schedule` of a node is a list of `HighLevelMessage`
"""
@dataclass
class HighLevelMessage:
    target: int
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

    def get_type(self) -> MessageType:
        message_content_lower = self.content.lower()[0:3]
        if "rts" == message_content_lower:
            return MessageType.RTS
        elif "cts" == message_content_lower:
            return MessageType.CTS
        elif "ack" == message_content_lower:
            return MessageType.ACK
        else:
            return MessageType.Data
        

    def get_waiting_time(self) -> int:
        if self.get_type() == MessageType.RTS or self.get_type() == MessageType.CTS:
            return int(self.content.split(" ")[1])
        else:
            return 0
    

    def get_message_length(self) -> int:
        return int(self.content.split(" ")[2])

"""
`Transmission` is a wrapper for `Message` to include planned and actual transmission times.
"""
@dataclass
class Transmission:
    transmit_time: int
    message: Message

