# Scheduling Algorithms Simulator (FIFO and Round Robin)

Aim of this project is to simulate the shceduling algorithms FIFO and Round Robin. 
A text interface has been created in order to represent, create, modify and delete processes. 
One can also switch between FIFO and Round Robin and adjust the quantum of the latter. 

FIFO (First-In, First-Out)
 - Non-preemptive scheduling.
 - Processes execute in arrival order, running to completion without interruption.
 - Simple but can cause delays if long processes block shorter ones.

Round Robin (RR)
 - Preemptive scheduling with fixed time slices (quantum).
 - Cycles through all processes equally, interrupting after each quantum.
 - Ensures fairness but adds overhead from frequent context switches.
