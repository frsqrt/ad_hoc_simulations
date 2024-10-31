* When in `State.BackingOff` a node neither receives nor sends. 
* When detecting a collision in `State.WaitingForAnswer` we will transition to `State.Idle`. Meaning the sending node will definitely have to backoff.
* When waiting for an ACK, the node discards all received messages which are not the expected ACK, even if they were meant for him.