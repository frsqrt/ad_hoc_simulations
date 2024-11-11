import logging
import csv
import random
from node import Node, get_node_by_id
from dataclasses import dataclass

from protocols import DSDVRoutingProtocol
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
    name: str
    radius: float
    transceive_range: float
    nodes: list[Node]
    send_schedule: list[PlannedTransmission]

    def get_collision_count(self):
        cnt = 0
        #for node in self.nodes:
        cnt += self.nodes[0].collision_counter

        return cnt


    def report(self, simulation_time: int):
        with open(f"./data/{self.name}.csv", mode='a+', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([simulation_time, self.get_collision_count()])


    def setup(self):
        for node in self.nodes:
            node.add_neighbors(self.nodes)
            node.routing_protocol = DSDVRoutingProtocol(node.id)


    def get_node_by_id(self, id: int) -> Node | None:
        for node in self.nodes:
            if node.id == id:
                return node

        return None


    def send_messages(self, simulation_time: int):
        for transmission in self.send_schedule:
            if simulation_time == transmission.transmit_time:
                self.get_node_by_id(transmission.source_node_id).routing_protocol.send(transmission.message)


    def run(self, simulation_time: int, active_transmissions: list[Message]):
        self.send_messages(simulation_time)

        for node in self.nodes:
            node.execute_state_machine(simulation_time, active_transmissions)

        for node in self.nodes:
            msg = node.receive()
            if msg:
                logging.info("Node {} received: {}".format(node.id, msg))
                reply = node.routing_protocol.reply(msg, node.get_packet_travel_time(get_node_by_id(self.nodes, msg.source)))
            else:
                reply = node.routing_protocol.tick()
            if reply:
                logging.info("Node {} wants to send: {}".format(node.id, reply))
                node.send(reply)

        # for node in self.nodes:
        #     msg = node.receive()
        #     if msg:
        #         self.received_message_counter += 1
        #
        #         if self.received_message_counter == self.expected_received_messages:
        #             self.report(simulation_time)
        #             exit(0)



Routing_1_aloha = Scenario(
    "Routing_1_aloha",
    0.25,
    3,
    [
        ALOHANode(0, 0.25, 3, 1, 5), # sink
        ALOHANode(1, 0.25, 3, 2, 7),
        ALOHANode(2, 0.25, 3, 3, 3),
        ALOHANode(3, 0.25, 3, 4, 7),
        ALOHANode(4, 0.25, 3, 5, 3),
        ALOHANode(5, 0.25, 3, 6, 5)  # source
    ],
    [
        PlannedTransmission(2, HighLevelMessage(0, "Hello from 5", 5), 5)
    ]
)

