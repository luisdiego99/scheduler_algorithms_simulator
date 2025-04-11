import uuid
import datetime
import os
import time
import math
import platform
from collections import deque
import random
import threading

class OperatingSystemSimulator:
    def __init__(self):
        # Tabla de procesos y colas
        self.process_table = []
        self.ready_queue = deque()
        self.executing_queue = deque(maxlen=1)
        self.blocked_queue = deque()
        self.unblocking_queue = deque()  # Nueva cola para procesos en espera de desbloqueo
        self.current_process = None
        
        # Estados y algoritmos disponibles
        self.PROCESS_STATES = ["Listo", "Ejecutando", "Bloqueado", "Terminado"]
        self.NON_EXECUTING_STATES = ["Listo", "Bloqueado", "Terminado"]
        self.SCHEDULING_ALGORITHMS = ["FIFO", "Round Robin"]
        self.current_algorithm = "FIFO"
        self.time_quantum = 2
        
        # Configuración del sistema
        self.log_file = "system_log.txt"
        
        # Mecanismos para productor-consumidor
        self.buffer_used = 0  # Buffer compartido inicial
        self.buffer_size = 500  # Tamaño máximo del buffer
        self.mutex = threading.Semaphore(1)  # Semaforo para exclusión mutua
        self.empty = threading.Semaphore(self.buffer_size)  # Semaforo para slots vacíos
        self.full = threading.Semaphore(0)  # Semaforo para slots llenos
        
        # Gestión de memoria para multiprogramación
        self.memory = {"total": 1024, "available": 1024}  # Memoria simulada en KB
        self.memory_used = self.memory['total'] - self.memory['available'] # Memoria utilizada inicial
        self.loaded_processes = []  # Procesos cargados en memoria
        
        # Inicialización del sistema
        self.clear_terminal()
        self.initialize_log_file()

    def clear_terminal(self):
        """Limpia la terminal según el sistema operativo"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    def initialize_log_file(self):
        """Inicializa el archivo de logs"""
        with open(self.log_file, "w") as f:
            self.log_action("Sistema iniciado")

    def log_action(self, action):
        """Registra una acción en el log con timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {action}\n")

    def show_menu(self):
        """Muestra el menú principal"""
        print("\n===== SISTEMA OPERATIVO SIMULADO =====")
        print("1. Crear proceso normal")
        print("2. Crear proceso productor")
        print("3. Crear proceso consumidor")
        print("4. Mostrar procesos")
        print("5. Modificar estado de un proceso")
        print("6. Eliminar proceso")
        print("7. Mostrar logs")
        print(f"8. Ejecutar planificador: {self.current_algorithm}")
        print("9. Configurar algoritmo de planificación")
        print("10. Mostrar estado de memoria")
        print("11. Salir")

    def create_process(self, process_type="Normal"):
        """Crea un nuevo proceso con tipo especificado (sin cargarlo aún en memoria o buffer)"""
        process_id = str(uuid.uuid4())[:4]
        state = "Listo"
        burst_time = random.randint(1, 15)
        remaining_time = burst_time

        try:
            priority = int(input("Ingrese la prioridad del proceso (1-10): "))
            if not 1 <= priority <= 10:
                raise ValueError
        except ValueError:
            print("\nPrioridad no válida. Debe ser un número entre 1-10.")
            self.log_action(f"Intento de creación fallido: Prioridad inválida")
            return

        memory_req = random.randint(64, 256)  # Requerimiento de memoria aleatorio

        process = {
            "PID": process_id,
            "Estado": state,
            "Prioridad": priority,
            "Burst_Time": burst_time,
            "Remaining_Time": remaining_time,
            "Memory": memory_req,
            "InMemory": False,
            "Type": process_type
        }

        self.ready_queue.append(process)
        self.process_table.append(process)

        print(f"\nProceso {process_id} ({process_type}) creado exitosamente")
        print(f"  - Memoria requerida: {memory_req}KB")
        self.log_action(f"Proceso creado: PID={process_id}, Tipo={process_type}")
        # Intentar cargar el proceso a memoria
        if self.load_into_memory(process):
            print(f"Proceso {process_id} cargado en memoria.")
        else:
            print(f"Memoria insuficiente para cargar el proceso {process_id}. Marcado como BLOQUEADO.")
            process["Estado"] = "Bloqueado"
            self.blocked_queue.append(process)

    def create_producer_process(self):
        """Crea un proceso productor especial"""
        self.create_process("Productor")

    def create_consumer_process(self):
        """Crea un proceso consumidor especial"""
        self.create_process("Consumidor")

    def verify_available_memory(self):
        """Revisa si procesos bloqueados por memoria ahora pueden ser cargados"""
        for process in list(self.blocked_queue):  # Hacemos copia para evitar modificar lista mientras se itera
            if not process["InMemory"]:
                if self.load_into_memory(process):
                    print(f"\n→ Proceso {process['PID']} cargado en memoria desde cola de bloqueados.")
                    process["Estado"] = "Listo"
                    self.ready_queue.append(process)
                    self.blocked_queue.remove(process)
    
    def load_into_memory(self, process):
        """Carga un proceso en memoria si hay espacio disponible. Retorna True si se cargó."""
        if process["Memory"] <= self.memory["available"]:
            self.memory["available"] -= process["Memory"]
            process["InMemory"] = True
            if process not in self.loaded_processes:
                self.loaded_processes.append(process)

            # Asegura que el estado esté bien definido
            if process["Estado"] != "Bloqueado":
                process["Estado"] = "Listo"
            return True
        return False


    def unload_from_memory(self, process):
        """Libera la memoria ocupada por un proceso."""
        if process["InMemory"]:
            self.memory["available"] += process["Memory"]
            process["InMemory"] = False
            if process in self.loaded_processes:
                self.loaded_processes.remove(process)

            if process["Estado"] != "Terminado":
                process["Estado"] = "Listo"

            # Verificar si ahora hay espacio para procesos bloqueados
            self.verify_available_memory()



    def check_unblocking_processes(self):
        """Verifica si los procesos bloqueados pueden ser desbloqueados"""
        desbloqueados = []

        for process in list(self.blocked_queue):
            pid = process["PID"]
            tipo = process["Type"]

            if tipo == "Productor":
                if self.buffer_used + process["Memory"] <= self.buffer_size:
                    print(f"Hay espacio en el buffer. Productor {pid} añadido a la cola.")
                    process["Estado"] = "Listo"
                    self.ready_queue.append(process)
                    desbloqueados.append(process)

            elif tipo == "Consumidor":
                if self.buffer_used >= process["Memory"]:
                    print(f"Hay datos en el buffer. Consumidor {pid} añadido a la cola.")
                    process["Estado"] = "Listo"
                    self.ready_queue.append(process)
                    desbloqueados.append(process)

            elif tipo == "Normal":
                # Esto debería tener una condición si aplica. Si no, podrías omitirlo.
                print(f"Proceso normal {pid} desbloqueado por condición externa.")
                process["Estado"] = "Listo"
                self.ready_queue.append(process)
                desbloqueados.append(process)

        # Eliminar desbloqueados de la cola bloqueada
        for p in desbloqueados:
            self.blocked_queue.remove(p)


                
    def show_processes(self):
        """Muestra todos los procesos en el sistema"""
        self.clear_terminal()
        if not self.process_table:
            print("\nNo hay procesos existentes")
            self.log_action("Consulta de tabla de procesos vacía")
            return False  

        print("\n===== TABLA DE PROCESOS =====")
        print(f"{'PID':<10} {'Tipo':<10} {'Estado':<12} {'Prioridad':<10} {'Memoria':<8} {'Burst':<6} {'Restante':<9}")
        print("-" * 70)
        for process in self.process_table:
            print(f"{process['PID']:<10} {process.get('Type','Normal'):<10} {process['Estado']:<12} {process['Prioridad']:<10} {process['Memory']:<8} {process['Burst_Time']:<6} {process['Remaining_Time']:<9}")
        self.log_action("Tabla de procesos mostrada")
        return True  #La tabla se muestra


    def modify_process_state(self):
        """Permite modificar el estado de un proceso existente"""
        self.clear_terminal()
        self.show_processes()
        
        if not self.process_table:
            self.log_action("Consulta de tabla de procesos vacía")
            return False  

        pid = input("\nIngrese el PID del proceso a modificar: ")
        for process in self.process_table:
            if process["PID"] == pid:
                current_state = process["Estado"]
                available_states = [s for s in self.PROCESS_STATES if s != current_state]
                if self.executing_queue:
                    available_states = [s for s in available_states if s != "Ejecutando"]
                
                print(f"\nEstado actual: {current_state}")
                print("Estados disponibles:", ", ".join(available_states))
                
                new_state = input("Ingrese el nuevo estado: ")
                
                if new_state in available_states: 
                    old_state = process["Estado"]
                    process["Estado"] = new_state
                    
                    # Actualización de colas según nuevo estado
                    if new_state == "Listo":
                        if process not in self.ready_queue:
                            self.ready_queue.append(process)
                    elif old_state == "Listo" and process in self.ready_queue:
                        self.ready_queue.remove(process)
                        
                    if new_state == "Ejecutando":
                        if self.executing_queue:
                            print(f"Advertencia: Proceso {self.executing_queue[0]['PID']} en ejecución.")
                        else:
                            self.executing_queue.append(process)
                    elif old_state == "Ejecutando" and process in self.executing_queue:
                        self.executing_queue.remove(process)
                        
                    if new_state == "Bloqueado":
                        self.blocked_queue.append(process)
                    elif old_state == "Bloqueado" and process in self.blocked_queue:
                        self.blocked_queue.remove(process)
                        
                    if new_state == "Terminado":
                        self.unload_from_memory(process)
                        if old_state == "Bloqueado" and process in self.blocked_queue:
                            self.blocked_queue.remove(process)
                        elif old_state == "Listo" and process in self.ready_queue:
                            self.ready_queue.remove(process)
                        elif old_state == "Ejecutando" and process in self.executing_queue:
                            self.executing_queue.remove(process)
                    
                    print(f"\nEstado del proceso {pid} actualizado de '{old_state}' a '{new_state}'.")
                    self.log_action(f"Estado modificado: PID={pid} {old_state}->{new_state}")
                    return
                
                print("\nError: Estado no válido o igual al actual.")
                self.log_action(f"Intento de modificación fallido: Estado inválido {current_state}->{new_state}")
                return
                
        print("\nPID no encontrado.")
        self.log_action(f"Intento de modificación fallido: PID={pid} no encontrado")

    def delete_process(self):
        """Elimina un proceso del sistema"""
        self.clear_terminal()
        self.show_processes()

        if not self.process_table:
            return

        print("\nOpciones disponibles:")
        print("- Ingrese el PID de un proceso específico")
        print("- Escriba 'all' para eliminar todos los procesos")
        print("- Escriba 'terminated' para eliminar solo los procesos terminados")

        pid = input("\nIngrese su elección: ").strip().lower()

        if pid == "all":
            self.process_table.clear()
            self.ready_queue.clear()
            self.blocked_queue.clear()
            #Desctivar si se quiere mantener el buffer usado aunque los procesos ya no existan
            self.buffer_used = 0
            print("\nTodos los procesos han sido eliminados.")
            self.log_action("Todos los procesos eliminados del sistema.")
            return

        if pid == "terminated":
            terminated = [p for p in self.process_table if p["Estado"] == "Terminado"]
            if not terminated:
                print("\nNo hay procesos terminados para eliminar.")
                self.log_action("No se encontraron procesos terminados para eliminar.")
                return
            for p in terminated:
                self.unload_from_memory(p)
                if p in self.ready_queue:
                    self.ready_queue.remove(p)
                if p in self.blocked_queue:
                    self.blocked_queue.remove(p)
                # Aqui el buffer permanece aunque el proceso haya terminado
                # if p in self.buffer:
                #     self.buffer.remove(p)
                self.process_table.remove(p)
            print(f"\n{len(terminated)} proceso(s) terminado(s) eliminado(s).")
            self.log_action(f"{len(terminated)} proceso(s) terminado(s) eliminado(s).")
            return

        # Busca y elimina un proceso individual
        for i, process in enumerate(self.process_table):
            if process["PID"] == pid:
                self.unload_from_memory(process)
                del self.process_table[i]
                if process in self.ready_queue:
                    self.ready_queue.remove(process)
                if process in self.blocked_queue:
                    self.blocked_queue.remove(process)
                # En teoria si el proceso es borado, no afectaria el buffer si es que ya se añadieron datos. 
                # if process in self.buffer:
                #     self.buffer.remove(process)
                print(f"\nProceso {pid} eliminado.")
                self.log_action(f"Proceso eliminado: PID={pid}")
                return

        print(f"\nEl proceso con ID {pid} no existe.")
        self.log_action(f"Intento de eliminación fallido: PID={pid} no encontrado")


    def print_logs(self):
        """Muestra el historial de logs del sistema"""
        self.clear_terminal()
        print("\n===== HISTORIAL DE LOGS =====")
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    print(line.strip())
        except FileNotFoundError:
            print("El archivo de logs no existe.")

    def show_memory_status(self):
        """Muestra el estado actual de la memoria"""
        self.clear_terminal()
        
        # Título
        print("\n===== ESTADO DE MEMORIA =====")
        print(f"Total: {self.memory['total']} KB")
        print(f"Disponible: {self.memory['available']} KB")

        # Filtra solo procesos en memoria
        in_memory_processes = [p for p in self.process_table if p["InMemory"] and p["Estado"] != "Terminado"]
        
        print(f"En uso: {len(in_memory_processes)} procesos")

        print("\nProcesos en memoria:")
        if in_memory_processes:
            for p in in_memory_processes:
                print(f"{p['PID']} - {p['Memory']} KB (Prioridad: {p['Prioridad']}, Estado: {p['Estado']})")
        else:
            print("No hay procesos en memoria actualmente.")

        # Buffer
        print("\n==== Buffer Compartido ====")
        print(f"Tamaño máximo: {self.buffer_size} KB")
        print(f"Tamaño usado: {self.buffer_used:.2f} KB / {self.buffer_size} KB")
        if self.buffer_used > 0:
            print("Contenido: Memoria ocupada por procesos productores.")
        else:
            print("Contenido: Vacío")

            

    def set_scheduling_algorithm(self):
        """Configura el algoritmo de planificación"""
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
                
            if choice == 1:
                new_algo = "FIFO" if self.current_algorithm == "Round Robin" else "Round Robin"
                confirm = input(f"\n¿Cambiar de {self.current_algorithm} a {new_algo}? (s/n): ").lower()
                if confirm == 's':
                    self.current_algorithm = new_algo
                    self.log_action(f"Algoritmo cambiado a {new_algo}")
                    print(f"\nAlgoritmo actualizado a {new_algo}")
                    if new_algo == "Round Robin" and self.time_quantum <= 0:
                        self.time_quantum = 2
                else:
                    print("\nCambio cancelado.")
                time.sleep(1)
                self.clear_terminal()
                
            elif choice == 2:
                print("\nManteniendo algoritmo actual.")
                time.sleep(1)
                self.clear_terminal()
                break
                
            elif choice == 3 and self.current_algorithm == "Round Robin":
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
                
            elif choice == 4:
                self.clear_terminal()
                break
                
            else:
                print("\nOpción no válida. Intente nuevamente.")
                time.sleep(1)
                self.clear_terminal()

    def run_scheduler(self):
        """Ejecuta el planificador con gestión de memoria y desbloqueo"""
        self.clear_terminal()

        if not self.process_table:
            print("\nNo hay procesos para ejecutar")
            return

        # 1. Cargar procesos en memoria si están en estado "Listo" y no están en RAM
        for process in [p for p in self.process_table if p["Estado"] == "Listo" and not p["InMemory"]]:
            if not self.load_into_memory(process):
                process["Estado"] = "Bloqueado"
                self.blocked_queue.append(process)
                print(f"Proceso {process['PID']} bloqueado por falta de memoria")
        
        # 2. Verificar procesos bloqueados para desbloquear (memoria o buffer)
        self.check_unblocking_processes()
        
        # 3. Ejecutar el planificador según el algoritmo
        if self.current_algorithm == "FIFO":
            self.fifo_scheduler()
        elif self.current_algorithm == "Round Robin":
            self.round_robin_scheduler()

    def fifo_scheduler(self):
        """Planificador FIFO (First In, First Out) con interacciones con el buffer"""
        self.clear_terminal()
        self.show_processes()

        def _execute_process(process):
            """Función auxiliar para ejecutar un proceso"""
            if process["Estado"] == "Ejecutando":
                print(f"\nReanudando ejecución de {process['PID']} (FIFO)...")
            else:
                print(f"\nProceso {process['PID']} iniciando ejecución (FIFO)")
            self.log_action(f"Proceso {process['PID']} comenzó ejecución (FIFO)")

            # Verificar si es un productor o consumidor y manejar el buffer
            if process.get("Type") == "Productor":
                if self.buffer_used + process['Memory'] > self.buffer_size:
                    # El buffer está lleno, bloqueamos el productor
                    print(f"\nProceso Productor {process['PID']} ({process['Memory']}) BLOQUEADO - No queda suficiente espacio en el Buffer")
                    process["Estado"] = "Bloqueado"
                    self.blocked_queue.append(process)
                    time.sleep(1)
                    return
                else:
                    # El productor agrega al buffer
                    print(f"Proceso Productor {process['PID']} añadiendo {process['Memory']}KB al buffer...")
                    self.buffer_used += process['Memory']
                    time.sleep(1)

            elif process.get("Type") == "Consumidor":
                if self.buffer_used == 0:
                    # El buffer está vacío, bloqueamos el consumidor
                    print(f"\nProceso Consumidor {process['PID']} BLOQUEADO - Buffer vacío")
                    process["Estado"] = "Bloqueado"
                    self.blocked_queue.append(process)
                    time.sleep(1)
                    return
                else:
                    # El consumidor consume de los datos en el buffer
                    if self.buffer_used - process['Memory'] < 0:
                        print(f"\nProceso Consumidor {process['PID']} BLOQUEADO - No hay suficiente memoria para consumir")
                        process["Estado"] = "Bloqueado"
                        self.blocked_queue.append(process)
                        return
                    else:
                        print(f"Proceso Consumidor {process['PID']} consumiendo {process['Memory']}/{self.buffer_used}KB del buffer...")
                        self.buffer_used -= process['Memory']             
                        time.sleep(1)

            time.sleep(4)  # Simulación de tiempo de ejecución
            process["Remaining_Time"] = 0
            process["Estado"] = "Terminado"
            print(f"Proceso {process['PID']} completado después de {process['Burst_Time']}s")
            self.log_action(f"Proceso {process['PID']} terminado")
            self.unload_from_memory(process)

        # Ejecutar proceso actual si existe
        if self.executing_queue:
            current_process = self.executing_queue.popleft()
            _execute_process(current_process)

        # Procesar en orden FIFO
        for process in [p for p in self.process_table if p["Estado"] in ["Listo", "Bloqueado"]]:
            if process["Estado"] == "Listo":
                if process in self.ready_queue:
                    self.ready_queue.remove(process)
                _execute_process(process)
            elif process["Estado"] == "Bloqueado":
                print(f"\nProceso {process['PID']} se encuentra bloqueado...")
                time.sleep(1)

        # Loop para desbloquear procesos y continuar la ejecución
        previous_blocked_queue_len = len(self.blocked_queue)
        iterations = 0  # Counter to track the number of iterations without change

        while True:
            before_check = len(self.ready_queue)
            self.check_unblocking_processes()
            after_check = len(self.ready_queue)

            # Check if the length of blocked queue has not changed after the iteration
            if len(self.blocked_queue) == previous_blocked_queue_len:
                iterations += 1
                if iterations >= 2:
                    print("\nNo hay más progreso. Los procesos bloqueados no se desbloquearán con el entorno actual.")
                    break
            else:
                previous_blocked_queue_len = len(self.blocked_queue)
                iterations = 0  # Reset the counter if the blocked processes changed

            if after_check == before_check:  # Si no se logró desbloquear ninguno
                break

            # Check for special exit conditions (only one consumer or producer left with an issue)
            if len(self.ready_queue) == 1:
                last_process = self.ready_queue[0]
                if last_process["Type"] == "Productor":
                    remaining_space = self.buffer_size - self.buffer_used
                    if remaining_space < last_process["Memory"]:
                        print(f"\nProceso Productor {last_process['PID']} BLOQUEADO - No hay suficiente espacio en el buffer para producir")
                        break
                elif last_process["Type"] == "Consumidor" and sum(p['Memory'] for p in self.buffer) == 0:
                    print(f"\nProceso Consumidor {last_process['PID']} BLOQUEADO - Buffer vacío, no puede consumir más")
                    break

            for process in [p for p in self.ready_queue if p["Estado"] == "Listo"]:
                self.ready_queue.remove(process)
                _execute_process(process)

        print("\nTodos los procesos han sido completados (FIFO)")

    def round_robin_scheduler(self):
        """Planificador Round Robin con terminación precisa de productores/consumidores"""
        self.clear_terminal()
        self.show_processes()

        max_idle_cycles = 3
        idle_cycles = 0

        while True:
            self._clean_queues()

            # Verificar si todos terminaron
            if all(p["Estado"] == "Terminado" for p in self.process_table):
                print("\nTodos los procesos completados exitosamente")
                print(f"Estado final del buffer: {self.buffer_used:.2f}/{self.buffer_size} KB")
                break

            # Intentar desbloquear procesos
            ready_before = len(self.ready_queue)
            self.check_unblocking_processes()
            ready_after = len(self.ready_queue)

            # Si no hay progreso
            if not self.executing_queue and not self.ready_queue:
                if self._is_deadlocked():
                    print("\nDeadlock detectado. Terminando planificación.")
                    print(f"Estado final del buffer: {self.buffer_used:.2f}/{self.buffer_size} KB")
                    break
                idle_cycles += 1
                if idle_cycles >= max_idle_cycles:
                    print("\nNo hay progreso después de varios intentos. Terminando.")
                    print(f"Estado final del buffer: {self.buffer_used:.2f}/{self.buffer_size} KB")
                    break
                time.sleep(1)
                continue

            # Reset idle counter si hubo progreso
            if ready_after > ready_before:
                idle_cycles = 0

            # Ejecutar procesos en orden de prioridad
            current_process = None
            
            # 1. Proceso en ejecución actual (si existe)
            if self.executing_queue:
                current_process = self.executing_queue.popleft()
            
            # 2. O el siguiente proceso de mayor prioridad
            if not current_process and self.ready_queue:
                current_process = min(self.ready_queue, key=lambda x: x["Prioridad"])
                self.ready_queue.remove(current_process)

            if current_process:
                self.run_process(current_process)
                
                # Re-encolar si no terminó ni se bloqueó
                if current_process["Estado"] == "Listo":
                    if current_process in self.ready_queue:
                        self.ready_queue.remove(current_process)
                    self.ready_queue.append(current_process)

    def _is_deadlocked(self):
        """Verifica deadlock solo si TODOS los procesos están bloqueados sin posibilidad"""
        # Solo considerar procesos no terminados
        active_processes = [p for p in self.process_table if p["Estado"] != "Terminado"]
        
        if not active_processes:
            return False
            
        # Si hay algún proceso listo o ejecutando, no hay deadlock
        if any(p["Estado"] in ["Listo", "Ejecutando"] for p in active_processes):
            return False
        
        # Verificar si al menos un proceso bloqueado podría desbloquearse
        for process in self.blocked_queue:
            if process["Estado"] != "Bloqueado":
                continue
                
            if process["Type"] == "Productor":
                if self.buffer_used + process["Memory"] <= self.buffer_size:
                    return False
            elif process["Type"] == "Consumidor":
                if self.buffer_used >= process["Memory"]:
                    return False
            elif process["Type"] == "Normal":
                if self.memory["available"] >= process["Memory"]:
                    return False
        
        # Solo declarar deadlock si TODOS los procesos activos están bloqueados sin salida
        print("\nVerificación de deadlock:")
        for p in self.blocked_queue:
            print(f"Proceso {p['PID']} ({p['Type']}) - ", end="")
            if p["Type"] == "Productor":
                print(f"Buffer: {self.buffer_used}/{self.buffer_size} (necesita {p['Memory']})")
            elif p["Type"] == "Consumidor":
                print(f"Buffer: {self.buffer_used} (necesita {p['Memory']})")
        
        return True


    def execute_producer(self, process):
        """Ejecuta un proceso productor"""
        if not process["InMemory"]:
            print(f"Productor {process['PID']} no puede ejecutarse: falta memoria")
            process["Estado"] = "Bloqueado"
            self.blocked_queue.append(process)
            return
        
        print(f"\nProductor {process['PID']} intentando producir...")
  
        self.mutex.acquire()
        
        # Sección crítica - agregar al buffer
        item = f"Item-{random.randint(100,999)}"
        self.buffer_used += item
        print(f"Productor {process['PID']} agregó {item}. Buffer Utilizado: {self.buffer_used}")
        self.log_action(f"Productor {process['PID']} produjo {item}")
        
        self.mutex.release()
        self.full.release()
        
        # Actualizar estado del proceso
        process["Remaining_Time"] -= 1
        if process["Remaining_Time"] <= 0:
            process["Estado"] = "Terminado"
            self.unload_from_memory(process)
        else:
            process["Estado"] = "Listo"
            self.ready_queue.append(process)

    def execute_consumer(self, process):
        """Ejecuta un proceso consumidor"""
        if not process["InMemory"]:
            print(f"Consumidor {process['PID']} no puede ejecutarse: falta memoria")
            process["Estado"] = "Bloqueado"
            self.blocked_queue.append(process)
            return
        
        print(f"\nConsumidor {process['PID']} intentando consumir...")
            
        self.mutex.acquire()
        
        # Sección crítica - remover del buffer
        item = self.buffer_used - process['Memory']
        self.buffer_used -=process['Memory']
        print(f"Consumidor {process['PID']} consumió {item}. Buffer: {self.buffer_used}")
        self.log_action(f"Consumidor {process['PID']} consumió {item}")
        
        self.mutex.release()
        self.empty.release()
        
        # Actualizar estado del proceso
        process["Remaining_Time"] -= 1
        if process["Remaining_Time"] <= 0:
            process["Estado"] = "Terminado"
            self.unload_from_memory(process)
        else:
            process["Estado"] = "Listo"
            self.ready_queue.append(process)

    def run_process(self, process):
        """Ejecuta un proceso con terminación precisa según su tamaño y burst time"""
        if process["Estado"] == "Terminado":
            return

        print(f"\nProceso {process['PID']} ({process['Type']}) ejecutando quantum de {self.time_quantum}s")

        if process["Type"] == "Productor":
            # Calcular cuánto debe producir en cada quantum
            total_cycles = process["Burst_Time"] / self.time_quantum
            produce_per_quantum = process["Memory"] / total_cycles

            if self.buffer_used + produce_per_quantum > self.buffer_size:
                print(f"Productor {process['PID']} BLOQUEADO - Buffer lleno")
                process["Estado"] = "Bloqueado"
                self.blocked_queue.append(process)
                return

            self.buffer_used += produce_per_quantum
            process["Remaining_Time"] -= self.time_quantum
            
            print(f"Productor añadió {produce_per_quantum:.2f}KB (Total buffer: {self.buffer_used:.2f}/{self.buffer_size}KB)")
            
            if process["Remaining_Time"] <= 0:
                process["Estado"] = "Terminado"
                print(f"Productor {process['PID']} completó su producción")
            else:
                process["Estado"] = "Listo"

        elif process["Type"] == "Consumidor":
            # Calcular cuánto debe consumir en cada quantum
            total_cycles = process["Burst_Time"] / self.time_quantum
            consume_per_quantum = process["Memory"] / total_cycles

            if self.buffer_used < consume_per_quantum:
                print(f"Consumidor {process['PID']} BLOQUEADO - Buffer insuficiente")
                process["Estado"] = "Bloqueado"
                self.blocked_queue.append(process)
                return

            self.buffer_used -= consume_per_quantum
            process["Remaining_Time"] -= self.time_quantum
            
            print(f"Consumidor quitó {consume_per_quantum:.2f}KB (Total buffer: {self.buffer_used:.2f}/{self.buffer_size}KB)")
            
            if process["Remaining_Time"] <= 0:
                process["Estado"] = "Terminado"
                print(f"Consumidor {process['PID']} completó su consumo")
            else:
                process["Estado"] = "Listo"

        else:  # Proceso normal
            memory_per_second = process["Memory"] / process["Burst_Time"]
            memory_this_turn = memory_per_second * min(self.time_quantum, process["Remaining_Time"])

            if self.memory_used + memory_this_turn > self.memory['total']:
                print(f"Proceso {process['PID']} BLOQUEADO - Memoria insuficiente")
                process["Estado"] = "Bloqueado"
                self.blocked_queue.append(process)
                return

            self.memory_used += memory_this_turn
            process["Remaining_Time"] -= self.time_quantum
            
            print(f"Proceso normal usó {memory_this_turn:.2f}KB de memoria")
            
            if process["Remaining_Time"] <= 0:
                process["Estado"] = "Terminado"
                self.memory_used -= process["Memory"]
                print(f"Proceso normal {process['PID']} completado")
            else:
                process["Estado"] = "Listo"
                self.memory_used -= memory_this_turn

        time.sleep(1)

    def _clean_queues(self):
        """Limpia las colas de procesos terminados"""
        for queue in [self.executing_queue, self.ready_queue, self.blocked_queue]:
            new_queue = deque(p for p in queue if p.get("Estado") != "Terminado")
            queue.clear()
            queue.extend(new_queue)

    def run(self):
        """Bucle principal del sistema operativo simulado"""
        while True:
            self.show_menu()
            choice = input("\nSeleccione una opción: ")

            if choice == "1":
                self.clear_terminal()
                self.create_process()
            elif choice == "2":
                self.clear_terminal()
                self.create_producer_process()
            elif choice == "3":
                self.clear_terminal()
                self.create_consumer_process()
            elif choice == "4":
                self.show_processes()
            elif choice == "5":
                self.modify_process_state()
            elif choice == "6":
                self.delete_process()
            elif choice == "7":
                self.print_logs()
            elif choice == "8":
                self.run_scheduler()
            elif choice == "9":
                self.set_scheduling_algorithm()
            elif choice == "10":
                self.show_memory_status()
            elif choice == "11":
                choice = input("¿Desea salir del programa? (s/n)")
                if choice == "s": 
                    print("\nSaliendo del sistema operativo simulado. ¡Adiós!")
                    self.log_action("Sistema terminado")
                    break
                else: 
                    self.clear_terminal()
                    continue
            else:
                print("\nOpción no válida. Intente nuevamente.")
                time.sleep(1)
                self.clear_terminal()

if __name__ == "__main__":
    simulator = OperatingSystemSimulator()
    simulator.run()
