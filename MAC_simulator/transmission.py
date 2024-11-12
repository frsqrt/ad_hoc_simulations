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
    route_target: int = None
    route_source: int = None

    def configure_routing(self, next, origin):
        return HighLevelMessage(next, self.content, self.length, self.target, origin)


class MessageType(Enum):
    Data = 0,
    RTS = 1,
    CTS = 2,
    ACK = 3,
    BROADCAST = 4

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
    route_target: int
    route_source: int

    def __init__(self, sequence_number: int, target: int, source: int,
                 content: str, length: int, route_target: int = None, route_source: int = None):
        self.sequence_number: int = sequence_number
        self.target: int = target
        self.source: int = source
        self.content: str = content
        self.length: int = length
        if route_target is None:
            self.route_target = self.target
        else:
            self.route_target = route_target
        if route_source is None:
            self.route_source = self.source
        else:
            self.route_source = route_source


    def get_type(self) -> MessageType:
        if self.target == -1:
            return MessageType.BROADCAST
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

    def __repr__(self):
        return (f'Message(sequence_number={self.sequence_number},'
                f'target={self.target}, source={self.source},'
                f'content={str(self.content)[:10]},'
                f'length={self.length},'
                f'route_target={self.route_target},'
                f'route_source={self.route_source})')
    

    def get_message_length(self) -> int:
        return int(self.content.split(" ")[2])

"""
`Transmission` is a wrapper for `Message` to include planned and actual transmission times.
"""
@dataclass
class Transmission:
    transmit_time: int
    message: Message

