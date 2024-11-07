import logging
from node import Node
from dataclasses import dataclass
from transmission import HighLevelMessage, Message
from rts_cts_node import RTSCTSNode
from aloha_node import ALOHANode

@dataclass
class PlannedTransmission:
    transmit_time: int
    message: HighLevelMessage
    source_node_id: int


@dataclass
class Scenario:
    radius: float
    transceive_range: float
    nodes: list[Node]
    send_schedule: list[PlannedTransmission]
    expected_received_messages: int
    received_message_counter: int

    
    def setup(self):
        for node in self.nodes:
            node.add_neighbors(self.nodes)


    def get_node_by_id(self, id: int) -> Node | None:
        for node in self.nodes:
            if node.id == id:
                return node
        
        return None


    def send_messages(self, simulation_time: int):
        for transmission in self.send_schedule:
            if simulation_time == transmission.transmit_time:
                self.get_node_by_id(transmission.source_node_id).send(transmission.message)


    def run(self, simulation_time: int, active_transmissions: list[Message]):
        self.send_messages(simulation_time)

        for node in self.nodes:
            node.execute_state_machine(simulation_time, active_transmissions)

        for node in self.nodes:
            msg = node.receive()
            if msg:
                logging.info("Node {} received: {}".format(node.id, msg))
                self.received_message_counter += 1

                if self.received_message_counter == self.expected_received_messages:
                    logging.info("All messages received")
                    logging.info(f"simulation_time: {simulation_time}")
                    exit(0)


data_sink_rts_cts = Scenario(
    0.25, 
    5,
    [
        RTSCTSNode(0, 0.25, 5, 5, 5),
        RTSCTSNode(1, 0.25, 5, 5, 7),
        RTSCTSNode(2, 0.25, 5, 7, 5),
        RTSCTSNode(3, 0.25, 5, 5, 3),
        RTSCTSNode(4, 0.25, 5, 3, 5),
    ],
    [
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 1),
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 2),
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 3),
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 4),
    ],
    4,
    0
)

data_sink_aloha = Scenario(
    0.25, 
    5,
    [
        ALOHANode(0, 0.25, 5, 5, 5),
        ALOHANode(1, 0.25, 5, 5, 7),
        ALOHANode(2, 0.25, 5, 7, 5),
        ALOHANode(3, 0.25, 5, 5, 3),
        ALOHANode(4, 0.25, 5, 3, 5),
    ],
    [
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 1),
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 2),
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 3),
        PlannedTransmission(3, HighLevelMessage(0, "Hello from 0", 5), 4),
    ],
    4,
    0
)