# Scheduling Algorithms Simulator (FIFO and Round Robin)

El siguiente proyecto fue creado en base a la guía proporcionada en Sistemas Informáticos, 
Universidad Galileo, jornada vespertina, 2025. El único participante en la elaboración del mismo fue: 

Luis Diego Hernández León - 24000343

A continuación hay más información acerca de este proyecto. 

Menu.py : file that holds the entire code of the simulator
system_log.txt: Text file designated to hold new logs everytime the simulator is ran. It will clear and populate automatically. 

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

