from dataclasses import dataclass
from random import randint
from typing import Protocol
from enum import Enum
from transmission import HighLevelMessage, Message


class MACProtocol(Protocol):
    def __init__(self):
        self.backoff = 0
        self.sequence_number = 0
        self.currently_transmitting = None
        self.currently_receiving = None

    # The currently transmitted `Transmission`
    currently_receiving: Message

    # The message we are currently receiving
    receiving_message: Message

    # Stores the current back-off time
    backoff: int

    # Sequence number for messages
    sequence_number: int
    
    """ 
    Sets the backoff

    :return: Nothing
    """
    def set_backoff(self):
        self.backoff = randint(1, 16)


    """ 
    Increase sequence number by one

    :return: sequence number
    """
    def next_sequence_number(self) -> int:
        self.sequence_number += 1
        return self.sequence_number
    
    def generate_message(self, source_node: int, message: HighLevelMessage) -> Message:
        """ 
        Sets the backoff

        :return: Nothing
        """

class ALOHA(MACProtocol):    
    def __init__(self):
        super().__init__()

    def set_backoff(self):
        return super().set_backoff()
    
    def generate_message(self, source_node_id: int, message: HighLevelMessage) -> Message:
        return Message(self.next_sequence_number(), message.target, source_node_id, message.content, message.length)


class RTSCTSALOHA(MACProtocol):
    def __init__(self):
        super().__init__()

    def set_backoff(self):
        return super().set_backoff()




















"""
class RTC_CTS_ALOHA:
    def __init__(self, identifier: int):
        self.id = identifier
        self.backoff = randint(1, 16)
        self.ack_await_counter = 0
        self.buffer: list[Message] = []
        self.message_buffer: dict[int: Message] = {}
        self.sequence_number = 0
        self.rts_lock = False

    def get_next_sequence_number(self):
        self.sequence_number += 1
        return self.sequence_number

    def generate_packet(self, message: HighLevelMessage):
        sequence = self.get_next_sequence_number()

        rts = Message(message.target, self.id, sequence, f'rts {message.length}', 1)
        self.buffer.append(rts)

        formatted_message = Message(message.target, self.id, sequence, message.content, message.length)
        self.message_buffer[sequence] = formatted_message

    def receive_packet(self, message: Message) -> None:

        # TODO still need to increase the backoff /
        # ignoring by this, note that back-off is already paused due to node state machine
        if message.target != self.id:
            return
        # technically a message needs a sequence number,
        # in theory a stray ack might now delete a random message in the buffer

        # whilst awaiting a reply we ignore all incoming rts requests.
        if 'rts' in message.content and not self.ack_await_counter and not self.rts_lock:
            print(f'{self.id} received an rts from {message.source}')
            self.backoff = 0
            self.buffer.insert(0, Message(message.source, message.target, message.sequence_number, f'cts {message.length}', 1))
            self.rts_lock = True
            return

        if 'rts' in message.content:
            print(f'{self.id} received an rts but ignored it')
            return

        # TODO match that this is corresponding to the currently outgoing rts in the buffer
        if 'cts' in message.content:
            print(f'{self.id} received a cts')
            # while technically not an ack it is an ack towards the last sent rts message.
            self.ack_await_counter = 0
            self.backoff = 0
            self.buffer.insert(0, self.message_buffer[message.sequence_number])
            return

        if self.buffer and message.source == self.buffer[0].target and message.content == 'ack' and message.sequence_number == self.buffer[0].sequence_number:
            print(f'{self.id} received ack')
            self.ack_await_counter = 0
            del self.buffer[0]  # deletes the RTS message from the buffer.
            return

        # in all other scenarios it was a message intended for us so we push an ack to the buffer
        if 'cts' not in message.content and 'rts' not in message.content and 'ack' not in message.content:
            # this now just assumes that we got a data packet and we reply with an ack.
            print(f'{self.id} pushing ack to buffer')
            self.buffer.insert(0, message.get_ack())
            self.ack_await_counter = 0
            self.backoff = 0
            return

        print(f'stray and ignored packet arrived at {self.id}')

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

            # no packet should be stored in the buffer apart from rts packets which will trigger new packets in the buffer.
            # so we delete this from the buffer upon transmission
            transmission = self.buffer[0]
            if 'rts' not in transmission.content:
                del self.buffer[0]
            if 'cts' in transmission.content:
                self.rts_lock = False

            if 'ack' in transmission.content:
                self.ack_await_counter = 0  # after an ack we do not await anything anymore.

            return transmission
"""


"""
class ALOHA:
    def __init__(self):
        self.state = State.Idle
        self.buffer = []
        self.backoff = 0
        self.state_counter = 0

    def execute_state_machine(self, simulation_time: int):
        if self.state == State.Idle:
            self.idle_state(simulation_time)
        elif self.state == State.Receiving:
            self.receiving_state(simulation_time)
        elif self.state == State.Sending:
            self.sending_state(simulation_time)
        elif self.state == State.BackingOff:
            self.backing_off_state(simulation_time)

    def idle_state(self, simulation_time: int):
        pass

    def sending_state(self, simulation_time: int):
        pass

    def receiving_state(self, simulation_time: int):
        pass

    def backing_off_state(self, simulation_time: int):
        pass

    # def __init__(self, identifier: int):
    #     self.id = identifier
    #     self.backoff = randint(1, 16)
    #     self.ack_await_counter = 0
    #     self.buffer: list[Message] = []
    #     self.sequence_number = 0

    # def get_next_sequence_number(self):
    #     self.sequence_number += 1
    #     return self.sequence_number

    # def generate_packet(self, message: HighLevelMessage):
    #     message = Message(message.target, self.id, self.get_next_sequence_number(), message.content, message.length)
    #     self.buffer.append(message)

    # def receive_packet(self, message: Message) -> None:
    #     if message.target != self.id:
    #         return
    #     # technically a message needs a sequence number,
    #     # in theory a stray ack might now delete a random message in the buffer
    #     if self.buffer and message.source == self.buffer[0].target and message.content == 'ack' and message.sequence_number == self.buffer[0].sequence_number:
    #         print(f'{self.id} received ack')
    #         self.ack_await_counter = 0
    #         del self.buffer[0]
    #         return

    #     # in all other scenarios it was a message intended for us so we push an ack to the buffer
    #     print(f'{self.id} pushing ack to buffer')
    #     self.buffer.insert(0, message.get_ack())
    #     self.backoff = 0

    # def send_packet(self) -> Message:
    #     # if awaiting an ack we should pause the whole system
    #     if self.ack_await_counter:
    #         self.ack_await_counter -= 1
    #         return
    #     if not self.buffer:
    #         return

    #     self.backoff = max(0, self.backoff-1)
    #     if self.backoff == 0:
    #         self.backoff = randint(1, 16)
    #         self.ack_await_counter = 50
    #         return self.buffer[0]
"""
