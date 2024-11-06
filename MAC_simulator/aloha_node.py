from node import *

class ALOHANode(Node):
    def __init__(self, id: int, radius: float, transceive_range: float, x_pos: float, y_pos: float):
        self.id = id
        self.radius = radius
        self.transceive_range = transceive_range
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.protocol = ALOHA()

        # State counters - every state has its own counter, 
        # so we can e.g. still count down `wait_for_answer_counter` while being in the receiving state
        self.sending_state_counter = 0
        self.receiving_state_counter = 0
        self.waiting_for_answer_state_counter = 0
        # the backoff counter is inside `protocol`

        super().__init__()

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


    def transition_to_receiving(self, message: Message):
        self.protocol.currently_receiving = message
        self.state = State.Receiving
        self.receiving_state_counter = message.length
        print("\tReceiving: [{}], Transition to {}".format(message, self.state.name))


    def transition_to_sending(self, simulation_time: int, message_to_send: Message, active_transmissions: list[Transmission]):
        self.state = State.Sending
        self.sending_state_counter = message_to_send.length
        self.protocol.currently_transmitting = message_to_send

        active_transmissions.append(Transmission(simulation_time, message_to_send))
        print("\tWants to send [{}], transition to {}".format(message_to_send, self.state.name))


    def transition_to_wait_for_answer(self, new_wait_for_answer_counter: int, wait_for_cts_counter: int, wait_for_data_counter: int):
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
                self.transition_to_wait_for_answer(self.waiting_for_answer_state_counter - received_message.length, 0, 0)
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
                self.transition_to_wait_for_answer(self.waiting_for_answer_state_counter, 0, 0)
                return
            
            self.receive_buffer = received_message # Store the received message into the receive_buffer
            message_to_send = self.protocol.generate_ack(self.id, received_message.source)
            self.transition_to_sending(simulation_time, message_to_send, active_transmissions)
        elif message_type == MessageType.ACK:
            # Remove `HighLevelMessage` from `send_schedule` since it was successfully transmitted and we do not want 
            # to try to retransmit the message at any point
            self.send_schedule.pop(0)

            # Copy the `receive_buffer` into `received_message`
            get_node_by_id(self.neighbors, received_message.source).received_message = get_node_by_id(self.neighbors, received_message.source).receive_buffer

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
        message_to_send = self.send_schedule[0] if self.send_schedule else None
        if message_to_send:
            message_to_send = self.protocol.generate_data(self.id, self.send_schedule[0])
            self.transition_to_sending(simulation_time, message_to_send, active_transmissions)
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
                self.transition_to_wait_for_answer(50, 0, 0)
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


    def backing_off_state(self, simulation_time: int, active_transmissions: list[HighLevelMessage]):
        self.protocol.backoff -= 1
        print("\tbackoff {}".format(self.protocol.backoff))
        if self.protocol.backoff == 0:
            self.transition_to_idle()