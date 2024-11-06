from node import *

class RTSCTSNode(Node):
    def __init__(self, id: int, radius: float, transceive_range: float, x_pos: float, y_pos: float):
        self.id = id
        self.radius = radius
        self.transceive_range = transceive_range
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.protocol = RTSCTSALOHA()

        # State counters - every state has its own counter, 
        # so we can e.g. still count down `wait_for_answer_counter` while being in the receiving state
        self.sending_state_counter = 0
        self.receiving_state_counter = 0
        self.wait_for_cts_counter = 0
        self.wait_for_ack_counter = 0
        self.wait_for_data_counter = 0
        self.received_rts_cts_backoff_state_counter = 0
        # the backoff counter is inside `protocol`

        super().__init__()


    def transition_to_idle(self):
        self.state = State.Idle
        self.sending_state_counter = 0
        self.receiving_state_counter = 0
        self.wait_for_ack_counter = 0
        self.wait_for_cts_counter = 0
        self.wait_for_data_counter = 0
        self.protocol.backoff = 0
        self.protocol.currently_receiving = None
        self.protocol.currently_transmitting = None
        print("\tTransition to {}".format(self.state))

    
    # Only one of the parameters is allowed to be != 0
    def transition_to_wait_for_answer(self, wait_for_ack_counter: int, wait_for_cts_counter: int, wait_for_data_counter: int):
        if wait_for_data_counter != 0:
            assert(wait_for_ack_counter == 0 and wait_for_cts_counter == 0)
        elif wait_for_ack_counter != 0:
            assert(wait_for_cts_counter == 0 and wait_for_data_counter == 0)
        elif wait_for_cts_counter != 0:
            assert(wait_for_ack_counter == 0 and wait_for_data_counter == 0)

        self.state = State.WaitingForAnswer
        self.wait_for_ack_counter = wait_for_ack_counter
        self.wait_for_cts_counter = wait_for_cts_counter
        self.wait_for_data_counter = wait_for_data_counter
        print("\tTransition to {}".format(self.state))


    def transition_to_received_rts_cts_backoff(self, wait_counter):
        self.state = State.ReceivedCTSRTSBackoff
        self.received_rts_cts_backoff_state_counter = wait_counter
        print("\tTransition to {}".format(self.state))


    def transition_to_sending(self, simulation_time: int, message_to_send: Message, active_transmissions: list[Transmission]):
        self.state = State.Sending
        self.sending_state_counter = message_to_send.length
        self.protocol.currently_transmitting = message_to_send

        active_transmissions.append(Transmission(simulation_time, message_to_send))
        print("\tWants to send [{}], transition to {}".format(message_to_send, self.state.name))


    def transition_to_receiving(self, message: Message):
        self.protocol.currently_receiving = message
        self.state = State.Receiving
        self.receiving_state_counter = message.length
        print("\tReceiving: [{}], Transition to {}".format(message, self.state.name))


    def transition_to_backoff(self):
        self.state = State.BackingOff
        self.protocol.set_backoff()
        print("\tTransition to {} with backoff={}".format(self.state, self.protocol.backoff))


    def execute_state_machine(self, simulation_time: int, active_transmissions: list[Transmission]):
        print("node {} - [State: {}]".format(self.id, self.state.name))
        if self.state == State.Idle:
            self.idle_state(simulation_time, active_transmissions)
        elif self.state == State.Receiving:
            self.receiving_state(simulation_time, active_transmissions)
        elif self.state == State.Sending:
            self.sending_state(simulation_time)   
        elif self.state == State.BackingOff:
            self.backing_off_state(simulation_time, active_transmissions)   
        elif self.state == State.WaitingForAnswer:
            self.waiting_for_answer_state(simulation_time, active_transmissions)
        elif self.state == State.ReceivedCTSRTSBackoff:
            self.received_rts_cts_backoff_state(simulation_time)


    #################################################################################################################################
    #################################################################################################################################
    #                                                   Begin state implementations
    #################################################################################################################################
    #################################################################################################################################


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
            message_to_send = self.protocol.generate_rts(self.id, self.send_schedule[0].target)
            self.transition_to_sending(simulation_time, message_to_send, active_transmissions)
            return


    def sending_state(self, simulation_time: int):
        self.sending_state_counter -= 1
        print("\tstate_counter: {}".format(self.sending_state_counter))
        if self.sending_state_counter <= 0:
            # Message is fully sent
            message_type = self.protocol.currently_transmitting.get_type()

            print("\tFinished sending [{}]".format(self.protocol.currently_transmitting))

            if message_type == MessageType.Data:
                self.transition_to_wait_for_answer(50, 0, 0)
            elif message_type == MessageType.RTS:
                self.transition_to_wait_for_answer(0, 50, 0)
            elif message_type == MessageType.CTS:
                self.transition_to_wait_for_answer(0, 0, 50)
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


    def process_received_message(self, received_message: Message, simulation_time: int, active_transmissions: list[Transmission]):
        self.protocol.currently_receiving = None
        print("\tFinished receiving [{}]".format(received_message))

        if self.wait_for_ack_counter > 0:
            # Waiting for ack
            if received_message.target != self.id:
                self.transition_to_wait_for_answer(self.wait_for_ack_counter - received_message.length, 0, 0)
            else:
                if received_message.get_type() == MessageType.ACK:
                    # Remove `HighLevelMessage` from `send_schedule` since it was successfully transmitted and we do not want 
                    # to try to retransmit the message at any point
                    self.send_schedule.pop(0)
                    # Copy the `receive_buffer` into `received_message`
                    get_node_by_id(self.neighbors, received_message.source).received_message = get_node_by_id(self.neighbors, received_message.source).receive_buffer
                    self.transition_to_idle()
                else:
                    # Should only be RTS' that could fall in this branch
                    print("\tReceived message meant for us while waiting for another packet, ignore it")
                    self.transition_to_wait_for_answer(self.wait_for_ack_counter - received_message.length, 0, 0)
        elif self.wait_for_cts_counter > 0:
            # Waiting for cts
            if received_message.target != self.id:
                self.transition_to_wait_for_answer(0, self.wait_for_cts_counter - received_message.length, 0)
            else:
                if received_message.get_type() == MessageType.CTS:
                    self.transition_to_sending(simulation_time, self.protocol.generate_data(self.id, self.send_schedule[0]), active_transmissions)
                else:
                    # Should only be RTS' that could fall in this branch
                    print("\tReceived message meant for us while waiting for another packet, ignore it")
                    self.transition_to_wait_for_answer(0, self.wait_for_cts_counter - received_message.length, 0)
        elif self.wait_for_data_counter > 0:
            # Waiting for data
            if received_message.target != self.id:
                self.transition_to_wait_for_answer(0, 0, self.wait_for_data_counter - received_message.length)
            else:
                if received_message.get_type() == MessageType.Data:
                    self.receive_buffer = received_message # Store the received data message to later consume it in `receive`
                    self.transition_to_sending(simulation_time, self.protocol.generate_ack(self.id, received_message.source), active_transmissions)
                else:
                    # Should only be RTS' that could fall in this branch
                    print("\tReceived message meant for us while waiting for another packet, ignore it")
                    self.transition_to_wait_for_answer(0, 0, self.wait_for_data_counter - received_message.length)
        elif self.protocol.backoff > 0:
            # Receiving something while backing off still works if it is a RTS meant for us
            if received_message.target == self.id and received_message.get_type() == MessageType.RTS:
                self.transition_to_sending(simulation_time, self.protocol.generate_cts(self.id, received_message.source), active_transmissions)
            else:
                self.protocol.backoff -= received_message.length
                self.state = State.BackingOff
        else:
            # Waiting for rts
            if received_message.target != self.id:
                message_type = received_message.get_type()
                if message_type == MessageType.RTS:
                    print("\tReceived RTS not meant for me, going to wait...")
                    self.transition_to_received_rts_cts_backoff(25)
                    return
                elif message_type == MessageType.CTS:
                    print("\tReceived CTS not meant for me, going to wait...")
                    self.transition_to_received_rts_cts_backoff(50)
                    return

                # Received either Data or an ACK that were not meant for us, go back to Idle
                self.transition_to_idle()
            else:
                if received_message.get_type() == MessageType.RTS:
                    self.transition_to_sending(simulation_time, self.protocol.generate_cts(self.id, received_message.source), active_transmissions)
                else:
                    print("\tReceived message meant for us while in Idle state which is not a RTS, ignoring it")
                    self.transition_to_idle()


    def waiting_for_answer_state(self, simulation_time: int, active_transmissions: list['Transmission']):
        state_count = 0
        if self.wait_for_data_counter != 0:
            self.wait_for_data_counter -= 1
            state_count = self.wait_for_data_counter
        elif self.wait_for_ack_counter != 0:
            self.wait_for_ack_counter -= 1
            state_count = self.wait_for_ack_counter
        elif self.wait_for_cts_counter != 0:
            self.wait_for_cts_counter -= 1
            state_count = self.wait_for_cts_counter

        print("\tstate_counter: {}".format(state_count))

        if state_count <= 0:
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
                

    def received_rts_cts_backoff_state(self, simulation_time: int):
        self.received_rts_cts_backoff_state_counter -= 1
        print("\tstate_counter: {}".format(self.received_rts_cts_backoff_state_counter))
        if self.received_rts_cts_backoff_state_counter == 0:
            self.transition_to_idle()


    def backing_off_state(self, simulation_time: int, active_transmissions: list[HighLevelMessage]):
        self.protocol.backoff -= 1
        print("\tbackoff {}".format(self.protocol.backoff))
        if self.protocol.backoff == 0:
            self.transition_to_idle()

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

        