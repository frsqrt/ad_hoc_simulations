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
        logging.debug("\tTransition to {}".format(self.state))

    
    # Only one of the parameters is allowed to be != 0
    def transition_to_wait_for_answer(self, wait_for_ack_counter: int, wait_for_cts_counter: int, wait_for_data_counter: int):
        if wait_for_data_counter != 0:
            assert(wait_for_ack_counter == 0 and wait_for_cts_counter == 0)
        elif wait_for_ack_counter != 0:
            assert(wait_for_cts_counter == 0 and wait_for_data_counter == 0)
        elif wait_for_cts_counter != 0:
            assert(wait_for_ack_counter == 0 and wait_for_data_counter == 0)

        self.state = State.WaitingForAnswer
        self.protocol.currently_receiving = None
        self.protocol.currently_transmitting = None
        self.receiving_state_counter = 0
        self.wait_for_ack_counter = wait_for_ack_counter
        self.wait_for_cts_counter = wait_for_cts_counter
        self.wait_for_data_counter = wait_for_data_counter
        logging.debug("\tTransition to {}".format(self.state))


    def transition_to_received_rts_cts_backoff(self, wait_counter):
        self.state = State.ReceivedCTSRTSBackoff
        self.received_rts_cts_backoff_state_counter = wait_counter
        logging.debug("\tTransition to {}".format(self.state))


    def transition_to_sending(self, simulation_time: int, message_to_send: Message, active_transmissions: list[Transmission]):
        self.state = State.Sending
        self.protocol.backoff = 0
        self.sending_state_counter = message_to_send.length
        self.protocol.currently_transmitting = message_to_send

        active_transmissions.append(Transmission(simulation_time + 1, message_to_send))
        logging.debug("\tWants to send [{}], transition to {}".format(message_to_send, self.state.name))


    def transition_to_receiving(self, message: Message):
        self.protocol.currently_receiving = message
        self.state = State.Receiving
        self.receiving_state_counter = message.length
        logging.debug("\tReceiving: [{}], Transition to {}".format(message, self.state.name))


    def transition_to_backoff(self, new_backoff: int | None = None):
        self.state = State.BackingOff
        self.protocol.currently_receiving = None
        self.waiting_for_answer_state_counter = 0
        self.receiving_state_counter = 0
        if new_backoff == None:
            self.protocol.set_backoff()
        else:
            self.protocol.backoff = new_backoff
        logging.debug("\tTransition to {} with backoff={}".format(self.state, self.protocol.backoff))


    def execute_state_machine(self, simulation_time: int, active_transmissions: list[Transmission]):
        logging.debug("node {} - [State: {}]".format(self.id, self.state.name))
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
            self.received_rts_cts_backoff_state(simulation_time, active_transmissions)


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
                    logging.debug("\tCollision, received more than one Message at the same time.")
                    self.transition_to_idle()
                    return
            
        # Anything to send?
        message_to_send = self.send_schedule[0] if self.send_schedule else None
        if message_to_send:
            # Just assume every node is as far away from each other as possible -> node_distance = self.transceive_range
            message_to_send = self.protocol.generate_rts(self.id, self.send_schedule[0].target, self.transceive_range, self.send_schedule[0].length)
            self.transition_to_sending(simulation_time, message_to_send, active_transmissions)
            return


    def sending_state(self, simulation_time: int):
        self.sending_state_counter -= 1
        logging.debug("\tstate_counter: {}".format(self.sending_state_counter))
        if self.sending_state_counter <= 0:
            # Message is fully sent
            message_type = self.protocol.currently_transmitting.get_type()

            logging.debug("\tFinished sending [{}]".format(self.protocol.currently_transmitting))

            if message_type == MessageType.Data:
                self.transition_to_wait_for_answer(int(self.transceive_range + self.protocol.currently_transmitting.length) * 2, 0, 0)
            elif message_type == MessageType.RTS:
                self.transition_to_wait_for_answer(0, int(self.transceive_range + self.protocol.currently_transmitting.length) * 2, 0)
            elif message_type == MessageType.CTS:
                # Add +10 buffer since we will receive the data packet and that might be larger (this might be completely unnessecary, but it shouldn't do any harm)
                self.transition_to_wait_for_answer(0, 0, int(self.transceive_range + self.protocol.currently_transmitting.length + 10) * 2)
            elif message_type == MessageType.ACK:
                self.transition_to_idle()


    def receiving_state(self, simulation_time: int, active_transmissions: list[Transmission]):
        # Check for collisions
        if transmissions := self.get_receivable_messages(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    if transmission.message != self.protocol.currently_receiving:
                        logging.debug("\tCollision with [{}]".format(transmission.message))

                        # If we were waiting for a message, return to waiting
                        if self.wait_for_ack_counter > 0:
                            new_wait_for_answer_state_counter = self.wait_for_ack_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                            self.transition_to_wait_for_answer(new_wait_for_answer_state_counter, 0, 0)
                            return
                        elif self.wait_for_cts_counter > 0:
                            new_wait_for_answer_state_counter = self.wait_for_cts_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                            self.transition_to_wait_for_answer(0, new_wait_for_answer_state_counter, 0)
                            return
                        elif self.wait_for_data_counter > 0:
                            new_wait_for_answer_state_counter = self.wait_for_data_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                            self.transition_to_wait_for_answer(0, 0, new_wait_for_answer_state_counter)
                            return
                        
                        # Just go back in case of collision
                        if self.received_rts_cts_backoff_state_counter > 0:
                            self.transition_to_received_rts_cts_backoff(self.received_rts_cts_backoff_state_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter))
                            return
                        
                        # If we were backing off, return to backoff
                        if self.protocol.backoff > 0:
                            new_backoff = self.protocol.backoff - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                            self.transition_to_backoff(new_backoff)
                            return

                        self.transition_to_idle()
                        return
                case [_, _, *_]:
                    logging.debug("\tCollision, received more than one Message at the same time.")

                    # If we were waiting for a message, return to waiting
                    if self.wait_for_ack_counter > 0:
                        new_wait_for_answer_state_counter = self.wait_for_ack_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                        self.transition_to_wait_for_answer(new_wait_for_answer_state_counter, 0, 0)
                        return
                    elif self.wait_for_cts_counter > 0:
                        new_wait_for_answer_state_counter = self.wait_for_cts_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                        self.transition_to_wait_for_answer(0, new_wait_for_answer_state_counter, 0)
                        return
                    elif self.wait_for_data_counter > 0:
                        new_wait_for_answer_state_counter = self.wait_for_data_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                        self.transition_to_wait_for_answer(0, 0, new_wait_for_answer_state_counter)
                        return
                    
                    # Just go back in case of collision
                    if self.received_rts_cts_backoff_state_counter > 0:
                        self.transition_to_received_rts_cts_backoff(self.received_rts_cts_backoff_state_counter - (self.protocol.currently_receiving.length - self.receiving_state_counter))
                        return

                    # If we were backing off, return to backoff
                    if self.protocol.backoff > 0:
                        new_backoff = self.protocol.backoff - (self.protocol.currently_receiving.length - self.receiving_state_counter)
                        self.transition_to_backoff(new_backoff)
                        return

                    self.transition_to_idle()
                    return

        self.receiving_state_counter -= 1
        logging.debug("\tstate_counter: {}".format(self.receiving_state_counter))
        if self.receiving_state_counter <= 0:
            self.process_received_message(self.protocol.currently_receiving, simulation_time, active_transmissions)


    def process_received_message(self, received_message: Message, simulation_time: int, active_transmissions: list[Transmission]):
        self.protocol.currently_receiving = None
        logging.debug("\tFinished receiving [{}]".format(received_message))

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
                    logging.debug("\tReceived message meant for us while waiting for another packet, ignore it")
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
                    logging.debug("\tReceived message meant for us while waiting for another packet, ignore it")
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
                    logging.debug("\tReceived message meant for us while waiting for another packet, ignore it")
                    self.transition_to_wait_for_answer(0, 0, self.wait_for_data_counter - received_message.length)
        elif self.received_rts_cts_backoff_state_counter > 0:
            message_type = received_message.get_type()
            if message_type == MessageType.RTS:
                new_waiting_time = received_message.get_waiting_time() if received_message.get_waiting_time() > self.received_rts_cts_backoff_state_counter else self.received_rts_cts_backoff_state_counter - received_message.length
                self.transition_to_received_rts_cts_backoff(new_waiting_time)
            elif message_type == MessageType.CTS:
                new_waiting_time = received_message.get_waiting_time() if received_message.get_waiting_time() > self.received_rts_cts_backoff_state_counter else self.received_rts_cts_backoff_state_counter - received_message.length
                self.transition_to_received_rts_cts_backoff(new_waiting_time)
            else:
                self.transition_to_received_rts_cts_backoff(self.received_rts_cts_backoff_state_counter - received_message.length)
            
            return
        elif self.protocol.backoff > 0:
            if received_message.target != self.id:
                # Backoff gets paused, we wait till `State.ReceivedCTSRTSBackoff` expires, then we continue our backoff
                message_type = received_message.get_type()
                if message_type == MessageType.RTS:
                    logging.debug("\tReceived RTS not meant for me, going to wait...")
                    self.transition_to_received_rts_cts_backoff(received_message.get_waiting_time())
                elif message_type == MessageType.CTS:
                    logging.debug("\tReceived CTS not meant for me, going to wait...")
                    self.transition_to_received_rts_cts_backoff(received_message.get_waiting_time())
                else:
                    self.transition_to_backoff(self.protocol.backoff - received_message.length)
            else:
                # Message was meant for us
                if received_message.get_type() == MessageType.RTS:
                    self.transition_to_sending(simulation_time, self.protocol.generate_cts(self.id, received_message.source, self.transceive_range, received_message.get_message_length()), active_transmissions)
        else:
            # Waiting for rts
            if received_message.target != self.id:
                # Message was not meant for us
                message_type = received_message.get_type()
                if message_type == MessageType.RTS:
                    logging.debug("\tReceived RTS not meant for me, going to wait...")
                    self.transition_to_received_rts_cts_backoff(received_message.get_waiting_time())
                elif message_type == MessageType.CTS:
                    logging.debug("\tReceived CTS not meant for me, going to wait...")
                    self.transition_to_received_rts_cts_backoff(received_message.get_waiting_time())
                else:
                    # Received either Data or an ACK that were not meant for us, go back to Idle
                    self.transition_to_idle()
            else:
                if received_message.get_type() == MessageType.RTS:
                    self.transition_to_sending(simulation_time, self.protocol.generate_cts(self.id, received_message.source, self.transceive_range, received_message.get_message_length()), active_transmissions)
                else:
                    logging.debug("\tReceived message meant for us while in Idle state which is not a RTS, ignoring it")
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

        logging.debug("\tstate_counter: {}".format(state_count))

        if state_count <= 0:
            self.transition_to_backoff()
            return

        # Anything to receive?
        if transmissions := self.get_receivable_messages(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    self.transition_to_receiving(transmission.message)
                case [_, _, *_]:
                    logging.debug("\tCollision, received more than one Message at the same time.")
                

    def received_rts_cts_backoff_state(self, simulation_time: int, active_transmissions: list[HighLevelMessage]):
        self.received_rts_cts_backoff_state_counter -= 1
        logging.debug("\tstate_counter: {}".format(self.received_rts_cts_backoff_state_counter))
        if self.received_rts_cts_backoff_state_counter == 0:
            if self.protocol.backoff > 0:
                self.transition_to_backoff(self.protocol.backoff)
            else:
                self.transition_to_idle()

        # Anything to receive?
        if transmissions := self.get_receivable_messages(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    self.transition_to_receiving(transmission.message)
                case [_, _, *_]:
                    logging.debug("\tCollision, received more than one Message at the same time.")



    def backing_off_state(self, simulation_time: int, active_transmissions: list[HighLevelMessage]):
        self.protocol.backoff -= 1
        logging.debug("\tbackoff {}".format(self.protocol.backoff))
        if self.protocol.backoff <= 0:
            self.transition_to_idle()

        # Anything to receive?
        if transmissions := self.get_receivable_messages(simulation_time, active_transmissions):
            match transmissions:
                case [transmission] if transmission.transmit_time + self.get_packet_travel_time(get_node_by_id(self.neighbors, transmission.message.source)) == simulation_time:
                    self.transition_to_receiving(transmission.message)
                case [_, _, *_]:
                    logging.debug("\tCollision, received more than one Message at the same time.")

        