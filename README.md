# MAC and Routing Protocol Simulator
The simulator is implemented in python using matplotlib for visualization. The simulator works on discrete time, with one central clock being used by every node for event management. Both protocols have been implemented as a state machine. The simulator takes propagation times and the time it takes to receive and send a packet into account.

Propagation time, the time it takes for a message to be received, is measured in clock ticks. When both sending and receiving a message, it takes a node the same number of clock ticks to send or receive a message as the message length. In this way the simulation takes into account that it takes longer to both send and receive longer messages. A message also takes the same number of clock ticks as the distance between the nodes to arrive. This allows the simulation to reflect the fact that messages take time to arrive and need to travel over the distance between nodes. 

The pathloss model used is a simple geometric model because as long as the receiving node is within the radius of the transmission range of the sender, the message will be received. The probability of a link within the circle representing the range of a node is 1.

On top of the MAC protocol DSDV routing is implemented.

# Usage
To run:
```
python3 main.py
```

To setup nodes and a sending schedule, refer to `scenarious_routing.py`. This file creates a demo scenario
```
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
```
with one source and one sink node on opposite borders of the topology and 20 randomly located nodes inbetween. The source sends one message at simulation time 2 to the sink. RTSCTS is used instead of ALOHA.

![Demo Topology](doc/routing.png)
