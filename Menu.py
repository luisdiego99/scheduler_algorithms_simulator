import uuid
import datetime
import os
import time
import platform
from collections import deque
import random

class OperatingSystemSimulator:
    def __init__(self):
        self.process_table = []
        self.ready_queue = deque()
        self.executing_queue = deque(maxlen=1)
        self.blocked_queue = deque()
        self.current_process = None
        self.PROCESS_STATES = ["Listo", "Ejecutando", "Bloqueado", "Terminado"]
        self.NON_EXECUTING_STATES = ["Listo", "Bloqueado", "Terminado"]
        self.SCHEDULING_ALGORITHMS = ["FIFO", "Round Robin"]
        self.current_algorithm = "FIFO"
        self.time_quantum = 2
        self.log_file = "system_log.txt"
        self.clear_terminal()
        self.initialize_log_file()

    def clear_terminal(self):
        # Limpia la terminal
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    def initialize_log_file(self):
        # Inicializa el log file 
        with open(self.log_file, "w") as f:
            self.log_action("Sistema iniciado")

    def log_action(self, action):
        # Guarda los logs con fecha y tiempo (timestamp)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {action}\n")

    def show_menu(self):
        #Muestra el menú principal
        print("\n===== SISTEMA OPERATIVO SIMULADO =====")
        print("1. Crear proceso")
        print("2. Mostrar procesos")
        print("3. Modificar estado de un proceso")
        print("4. Eliminar proceso")
        print("5. Mostrar logs")
        print(f"6. Ejecutar planificador: {self.current_algorithm}")
        print("7. Configurar algoritmo de planificación")
        print("8. Salir")

    def create_process(self):
        '''Opcion 1: Crea un nuevo proceso. uuid truncado para solo recuperar los primeros 4 digitos, con fines de testeo'''
        process_id = str(uuid.uuid4())[:4]
        state = "Listo"
        burst_time = random.randint(1, 15)  # Random burst time entre  1 -10  segundos
        remaining_time = burst_time 
        try:
            priority = int(input("Ingrese la prioridad del proceso (1-10): "))
            if not 1 <= priority <= 10:
                raise ValueError
        except ValueError:
            print("\nPrioridad no válida. Debe ser un número entre 1-10.")
            self.log_action(f"Intento de creación fallido: Prioridad inválida")
            return

        process = {
            "PID": process_id,
            "Estado": state,
            "Prioridad": priority,
            "Burst_Time": burst_time,
            "Remaining_Time": remaining_time,
        }
        self.process_table.append(process)
        self.ready_queue.append(process)
        print(f"\nProceso {process_id} creado exitosamente con estado '{state}'.")
        self.log_action(f"Proceso creado: PID={process_id}, Prioridad={priority}, Burst_Time={burst_time}, Remaining_Time{remaining_time}")

    def show_processes(self):
        '''Opcion 2: Muestra los procesos existentes'''
        self.clear_terminal()
        if not self.process_table:
            print("\nNo hay procesos existentes")
            self.log_action("Consulta de tabla de procesos vacía")
            return
        
        print("\n===== TABLA DE PROCESOS =====")
        print(f"{'PID':<10} {'Estado':<12} {'Prioridad':<10} {'Burst_Time':<12} {'Remaining_Time':<15}")
        print("-" * 62)
        for process in self.process_table:
            print(f"{process['PID']:<10}{process['Estado']:<18}{process['Prioridad']:<12}{process['Burst_Time']:<15}{process['Remaining_Time']:<12}")
        self.log_action("Tabla de procesos mostrada")

    def modify_process_state(self):
        '''Opcion 3: Modifica el estado de un proceso'''
        self.clear_terminal()
        self.show_processes()
            
        pid = input("Ingrese el PID del proceso a modificar: ")
        for process in self.process_table:
            if process["PID"] == pid:
                current_state = process["Estado"]
                # La lista de estados cambia de forma dinamica
                available_states = [s for s in self.PROCESS_STATES if s != current_state]
                if self.executing_queue:
                    available_states = [s for s in available_states if s != "Ejecutando"]
                print(f"\nEstado actual: {current_state}")
                print("Estados disponibles:", ", ".join(available_states))
                
                new_state = input("Ingrese el nuevo estado: ")
                
                if new_state in available_states: 
                    old_state = process["Estado"]
                    # Actualizando la cola ready
                    if new_state == "Listo":
                        if process not in self.ready_queue:
                            process["Estado"] = new_state
                            self.ready_queue.append(process)
                            print(f"\nEstado del proceso {pid} actualizado de '{old_state}' a '{new_state}'.")
                            self.log_action(f"Estado modificado: PID={pid} {old_state}->{new_state}") 
                    elif old_state == "Listo" and process in self.ready_queue:
                        self.ready_queue.remove(process)
                        
                    # Actualizando la cola executing
                    if new_state == "Ejecutando":
                        if self.executing_queue:  #Si ya existe un proceso ejecutandose...
                            print(f"Advertencia: El proceso {self.executing_queue[0]['PID']} se encuentra en ejecución.\nEl estado de {pid} permanece como '{process['Estado']}'")
                        else:
                            process["Estado"] = new_state
                            self.executing_queue.append(process)
                            print(f"\nEstado del proceso {pid} actualizado de '{old_state}' a '{new_state}'.") 
                            self.log_action(f"Estado modificado: PID={pid} {old_state}->{new_state}")

                    # Actualizando la cola blocked   
                    if new_state == "Bloqueado":
                        process["Estado"] = new_state
                        self.blocked_queue.append(process)
                        print(f"\nEstado del proceso {pid} actualizado de '{old_state}' a '{new_state}'.")
                        self.log_action(f"Estado modificado: PID={pid} {old_state}->{new_state}") 
                    elif old_state == "Bloqueado" and process in self.blocked_queue:
                        self.blocked_queue.remove(process)

                    #Cambiando el estado a Terminado y removiendolo de cualquier queue
                    if new_state == "Terminado":
                        process["Estado"] = new_state
                        print(f"\nEstado del proceso {pid} actualizado de '{old_state}' a '{new_state}'.")
                        self.log_action(f"Estado modificado: PID={pid} {old_state}->{new_state}") 
                        if old_state == "Bloqueado" and process in self.blocked_queue:
                            self.blocked_queue.remove(process)
                        elif old_state == "Listo" and process in self.ready_queue:
                            self.ready_queue.remove(process)
                        elif old_state == "Ejecutando" and process in self.executing_queue:
                            self.executing_queue.remove(process)
                else:
                    print("\nError: Estado no válido o igual al actual.")
                    self.log_action(f"Intento de modificación fallido: Estado inválido {current_state}->{new_state}")
                return
                
        print("\nPID no encontrado.")
        self.log_action(f"Intento de modificación fallido: PID={pid} no encontrado")

    def delete_process(self):
        #Elimina un proceso
        self.clear_terminal()
        self.show_processes()
        if not self.process_table:
            print("\nNo hay procesos existentes")
            return
            
        pid = input("Ingrese el PID del proceso a eliminar: ")
        for i, process in enumerate(self.process_table):
            if process["PID"] == pid:
                #Elimina de las tablas de proceso y on queue
                del self.process_table[i]
                if process in self.ready_queue:
                    self.ready_queue.remove(process)
                print(f"\nProceso {pid} eliminado.")
                self.log_action(f"Proceso eliminado: PID={pid}")
                return
                
        print(f"\nEl proceso con ID {pid} no existe.")
        self.log_action(f"Intento de eliminación fallido: PID={pid} no encontrado")

    def print_logs(self):
        #Muestra los logs del sistema
        self.clear_terminal()
        print("\n===== HISTORIAL DE LOGS =====")
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    print(line.strip())
        except FileNotFoundError:
            print("El archivo de logs no existe.")

    def set_scheduling_algorithm(self):
        #Configuracion del scheduler 
        self.clear_terminal()
        
        while True:
            print("\n=== CONFIGURACIÓN DEL PLANIFICADOR ===")
            print(f"Algoritmo actual: {self.current_algorithm}")
            if self.current_algorithm == "Round Robin":
                print(f"Quantum actual: {self.time_quantum}s")
            
            print("\nOpciones disponibles:")
            print("1. Cambiar a FIFO" if self.current_algorithm == "Round Robin" 
                else "1. Cambiar a Round Robin")
            print("2. Mantener algoritmo actual")
            print("3. Configurar quantum (solo Round Robin)")
            print("4. Volver al menú principal")
            
            try:
                choice = int(input("\nSeleccione una opción: "))
            except ValueError:
                print("\n¡Error! Ingrese un número válido.")
                time.sleep(1)
                self.clear_terminal()
                continue
                
            if choice == 1:  #Cambiar algoritmo
                new_algo = "FIFO" if self.current_algorithm == "Round Robin" else "Round Robin"
                confirm = input(f"\n¿Cambiar de {self.current_algorithm} a {new_algo}? (s/n): ").lower()
                if confirm == 's':
                    self.current_algorithm = new_algo
                    self.log_action(f"Algoritmo cambiado a {new_algo}")
                    print(f"\nAlgoritmo actualizado a {new_algo}")
                    if new_algo == "Round Robin" and self.time_quantum <= 0:
                        self.time_quantum = 2  #Resetea al quantum por default 
                else:
                    print("\nCambio cancelado.")
                time.sleep(1)
                self.clear_terminal()
                
            elif choice == 2:  #Mantener el algoritmo actual
                print("\nManteniendo algoritmo actual.")
                time.sleep(1)
                self.clear_terminal()
                break
                
            elif choice == 3 and self.current_algorithm == "Round Robin":  #Setear quantum
                try:
                    new_quantum = int(input("\nIngrese nuevo quantum (segundos): "))
                    if new_quantum > 0:
                        self.time_quantum = new_quantum
                        self.log_action(f"Quantum actualizado a {new_quantum}s")
                        print(f"\nQuantum actualizado a {new_quantum}s")
                    else:
                        print("\nEl quantum debe ser mayor que 0.")
                except ValueError:
                    print("\n¡Debe ingresar un número válido!")
                time.sleep(1)
                self.clear_terminal()
                
            elif choice == 4:  #Volver al menu principal
                self.clear_terminal()
                break
                
            else:
                print("\nNo se puede asignar quantum a FIFO. Intente nuevamente.")
                time.sleep(3)
                self.clear_terminal()

    def run_scheduler(self):
        #Ejecutar el scheduler
        self.clear_terminal()
        if not self.process_table:
            print("\nNo hay procesos para ejecutar")
            return
            
        #Inicializa la cola si esta vacia
        if not self.ready_queue:
            self.ready_queue.extend([p for p in self.process_table if p["Estado"] == "Listo"])
            
        if not self.ready_queue:
            print("\nNo hay procesos en estado 'Listo' para ejecutar")
             #Creo que hay que borrar esta parte, ya que primero se deben identificar los que esta en ejecucion
            
        print(f"\nEjecutando planificador ({self.current_algorithm})...")
        
        if self.current_algorithm == "FIFO":
            self.fifo_scheduler()
        elif self.current_algorithm == "Round Robin":
            self.round_robin_scheduler()

    def fifo_scheduler(self):
        """Calendarizador FIFO con manejo adecuado de procesos bloqueados"""
        self.clear_terminal()
        self.show_processes()

        def _execute_process(process):
            if process["Estado"] == "Ejecutando":
                print(f"\nReanudando ejecución de {process['PID']} (FIFO)...")
            else:
                print(f"\nProceso {process['PID']} iniciando ejecución (FIFO)")
            self.log_action(f"Proceso {process['PID']} comenzó ejecución (FIFO)")
            
            time.sleep(3)
            process["Estado"] = "Terminado"
            print(f"Proceso {process['PID']} completado después de {process['Burst_Time']}s")
            self.log_action(f"Proceso {process['PID']} terminado")

        # Primero ejecuta el proceso en estado Ejecutando si existe
        if self.executing_queue:
            current_process = self.executing_queue.popleft()
            _execute_process(current_process)

        # Crear lista ordenada de IDs según orden de llegada (excluyendo terminados y ejecutando)
        ordered_processes = [
            p["PID"] for p in self.process_table 
            if p["Estado"] in ["Listo", "Bloqueado"]
        ]

        # Procesar en orden FIFO estricto
        for pid in ordered_processes:
            # Buscar el proceso correspondiente
            process = next(p for p in self.process_table if p["PID"] == pid)
            
            if process["Estado"] == "Listo":
                if process in self.ready_queue:
                    self.ready_queue.remove(process)
                _execute_process(process)
            elif process["Estado"] == "Bloqueado":
                if process in self.blocked_queue:
                    self.blocked_queue.remove(process)
                print(f"\nProceso {pid} se encuentra bloqueado")
                print("Espere.Será ejecutado una vez desbloqueado")
                time.sleep(2)
                print("El proceso {pid} se ha desbloqueado!")
                self.log_action(f"Proceso {pid} omitido (bloqueado)")
                
                # Marcar como listo y ejecutar
                process["Estado"] = "Listo"
                _execute_process(process)

        print("\nTodos los procesos han sido completados (FIFO)")


        self.current_process = None
        print("\nTodos los procesos han sido completados")

    def _handle_blocked_processes(self):
        """Mueve procesos bloqueados a la cola ready en RR"""
        while self.blocked_queue:
            process = self.blocked_queue.popleft()
            process["Estado"] = "Listo"
            print(f"El proceso {process['PID']} ha sido desbloqueado y agregado a la cola.")
            self.ready_queue.append(process)
            self.log_action(f"Proceso {process['PID']} desbloqueado")
    
    def round_robin_scheduler(self):
        """Algoritmo Round Robin basado en ciclos segun prioridad de los procesos"""
        self.clear_terminal()
        self.show_processes()
        
        while True:
            #Remover los procesos terminados 
            self._clean_queues()
            
            #Checquear si ya se terminaron todos los procesos
            if not (self.executing_queue or self.ready_queue or self.blocked_queue):
                break
                
            #Recopilar todos los procesos, de todas las colas, basados en su prioridad (menor numero --> mayor prioridad)
            active_processes = []
            if self.executing_queue:
                active_processes.append(self.executing_queue[0])
            active_processes.extend(sorted(self.ready_queue, key=lambda x: x["Prioridad"]))
            
            if not active_processes:
                # Despues del primer ciclo, los procesos bloqueados comienzan a desbloquearse, por orden de prioridad
                if self.blocked_queue:
                    highest_priority_blocked = min(self.blocked_queue, key=lambda x: x["Prioridad"])
                    print(f"\nProceso {highest_priority_blocked['PID']} (Prioridad {highest_priority_blocked['Prioridad']}) es el único bloqueado - desbloqueando")
                    highest_priority_blocked["Estado"] = "Listo"
                    self.ready_queue.append(highest_priority_blocked)
                    self.blocked_queue.remove(highest_priority_blocked)
                continue
                
            #Se ejcuta cada proceso por lo equivalente a un quantum
            for process in list(active_processes):
                # Salta el proceso si fue terminado en una iteracion anterior
                if process["Estado"] == "Terminado" or process["Estado"] == "Bloqueado":
                    continue
                    
                # Remueve el procesos de su cola actual 
                if process in self.executing_queue:
                    self.executing_queue.remove(process)
                elif process in self.ready_queue:
                    self.ready_queue.remove(process)
                    
                # Ejecuta el quantum
                print(f"\nProceso {process['PID']} (Prioridad {process['Prioridad']}) en ejecución (RR, quantum: {self.time_quantum}s)")
                execution_time = min(self.time_quantum, process["Remaining_Time"])
                time.sleep(execution_time)
                process["Remaining_Time"] -= execution_time
                
                if process["Remaining_Time"] <= 0:
                    process["Estado"] = "Terminado"
                    print(f"Proceso {process['PID']} completado")
                else:
                    process["Estado"] = "Listo"
                    self.ready_queue.append(process)
                    print(f"Proceso {process['PID']} pausado, {process['Remaining_Time']}s restantes")
            
            # Maneja los procesos bloqueados (solo se desbloquean una vez pasan a ser la mayor prioridad)
            self._handle_blocked_processes()

        print("\nTodos los procesos han sido completados (RR)")

    def _clean_queues(self):
        """Remueve los procesos terminados de todas las colas"""
        for queue in [self.executing_queue, self.ready_queue, self.blocked_queue]:
            #Crea un nuevo deque sin estados terminados
            new_queue = deque(p for p in queue if p.get("Estado") != "Terminado")
            queue.clear()
            queue.extend(new_queue)

    def run(self):
        """Main execution loop"""
        while True:
            self.show_menu()
            choice = input("\nSeleccione una opción: ")

            if choice == "1":
                self.clear_terminal()
                self.create_process()
            elif choice == "2":
                self.show_processes()
            elif choice == "3":
                self.modify_process_state()
            elif choice == "4":
                self.delete_process()
            elif choice == "5":
                self.print_logs()
            elif choice == "6":
                self.run_scheduler()
            elif choice == "7":
                self.set_scheduling_algorithm()
            elif choice == "8":
                print("\nSaliendo del sistema operativo simulado. ¡Adiós!")
                self.log_action("Sistema terminado")
                break
            else:
                print("\nOpción no válida. Intente nuevamente.")
                time.sleep(1)
                self.clear_terminal()

if __name__ == "__main__":
    simulator = OperatingSystemSimulator()
    simulator.run()