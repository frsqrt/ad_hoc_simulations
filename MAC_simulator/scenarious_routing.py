import logging
import csv
import random
from node import Node, get_node_by_id
from dataclasses import dataclass
import numpy as np

from protocols import DSDVRoutingProtocol
from transmission import HighLevelMessage, Message, MessageType
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
        self.hops = 0
        self.established_time = -1
        self.resulting_time = -1
        for node in self.nodes:
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

        if simulation_time >= 10_000:
            return (self.established_time, self.resulting_time, self.hops)

        source_node = self.nodes[-2]
        target_node = self.nodes[-1]

        if target_node.id in source_node.routing_protocol.table:
            self.established_time = simulation_time

        for node in self.nodes:
            # node.move()
            node.add_neighbors(self.nodes)

        for node in self.nodes:
            node.execute_state_machine(simulation_time, active_transmissions)

        for node in self.nodes:
            msg = node.receive()
            if msg:
                # if msg.get_type() == MessageType.Data:
                if 'Hello' in msg.content:
                    self.hops += 1
                    if msg.route_target == msg.target:
                        self.resulting_time = simulation_time
                        return (self.established_time, self.resulting_time, self.hops)

                if 'cts' in msg.content:
                    logging.info("Node {} received: {}".format(node.id, msg))
                reply = node.routing_protocol.reply(msg, node.get_packet_travel_time(get_node_by_id(self.nodes, msg.source)))
            else:
                reply = node.routing_protocol.tick()
            if reply:
                logging.debug("Node {} wants to send: {}".format(node.id, reply))
                node.send(reply)


        # if simulation_time == 250:
        #     logging.info('Removing node 3 as sender from the network')
        #     self.nodes[3]._shadow = self.nodes[3].send
        #     self.nodes[3].send = lambda _: None
        #
        # if simulation_time == 550:
        #     logging.info(f'{self.nodes[0].routing_protocol.table}')
        #     self.nodes[3].send = self.nodes[3]._shadow
        #     logging.info('Adding node 3 as sender to the network')
        #
        # if simulation_time == 750:
        #     logging.info(f'{self.nodes[0].routing_protocol.table}')


        # for node in self.nodes:
        #     msg = node.receive()
        #     if msg:
        #         self.received_message_counter += 1
        #
        #         if self.received_message_counter == self.expected_received_messages:
        #             self.report(simulation_time)
        #             exit(0)

np.random.seed(42)

Routing_1_aloha = Scenario(
    "Routing_1_aloha",
    0.25,
    3,
    [RTSCTSNode(i, 0.25, 3, np.random.uniform(0, 10), np.random.uniform(0, 10)) for i in range(1, 20)] +
    [RTSCTSNode(0, 0.25, 3, 0, 0),  # source
     RTSCTSNode(100, 0.25, 3, 10, 10)],  # sink

    [
        PlannedTransmission(2, HighLevelMessage(100, "Hello message", 5), 0)
    ]
)

