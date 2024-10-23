from dataclasses import dataclass
from random import randint
from typing import Protocol


@dataclass
class HighLevelMessage:
    target: int
    content: str
    length: int


@dataclass
class Message:
    """
    This message class is utilized by the protocol layer in order to communicate
    """
    target: int
    source: int
    sequence_number: int
    content: str
    length: int

    def get_ack(self):
        return Message(self.source, self.target, self.sequence_number, 'ack', 1)


class MACProtocol(Protocol):

    buffer: list
    backoff: int

    def generate_packet(self, message: HighLevelMessage):
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
    def __init__(self, identifier: int):
        self.id = identifier
        self.backoff = randint(1, 16)
        self.ack_await_counter = 0
        self.buffer: list[Message] = []
        self.sequence_number = 0

    def get_next_sequence_number(self):
        self.sequence_number += 1
        return self.sequence_number

    def generate_packet(self, message: HighLevelMessage):
        message = Message(message.target, self.id, self.get_next_sequence_number(), message.content, message.length)
        self.buffer.append(message)

    def receive_packet(self, message: Message) -> None:
        if message.target != self.id:
            return
        # technically a message needs a sequence number,
        # in theory a stray ack might now delete a random message in the buffer
        if self.buffer and message.source == self.buffer[0].target and message.content == 'ack':
            print(f'{self.id} received ack')
            self.ack_await_counter = 0
            del self.buffer[0]
            return

        # in all other scenarios it was a message intended for us so we push an ack to the buffer
        print(f'{self.id} pushing ack to buffer')
        self.buffer.insert(0, message.get_ack())
        self.backoff = 0

    def send_packet(self) -> Message:
        # if awaiting an ack we should pause the whole system
        if self.ack_await_counter:
            self.ack_await_counter -= 1
            return
        if not self.buffer:
            return

        self.backoff = max(0, self.backoff-1)
        if self.backoff == 0:
            self.backoff = randint(1, 16)
            self.ack_await_counter = 50
            return self.buffer[0]
