# interprete.py
# Intérprete de Código Intermedio basado en Cuádruplas
# Ejecuta el código de 3 direcciones generado por CodigoIntermedioGenerator

class InterpreteCI:
    """Intérprete que ejecuta código intermedio representado como cuádruplas."""
    
    def __init__(self):
        self.memoria = {}  # Memoria para variables y temporales
        self.pc = 0        # Program Counter (índice de cuádruple actual)
        self.cuadruplas = []
        self.etiquetas = {}  # Mapeo de etiquetas a índices de cuádruplas
        self.salida = []   # Buffer de salida para print/write
        self.entrada_buffer = []  # Buffer de entrada para read
        self.ejecutando = False
        
    def cargar_cuadruplas(self, cuadruplas):
        """Carga las cuádruplas y construye la tabla de etiquetas.
        
        Args:
            cuadruplas: Lista de objetos Cuadrupla o lista de tuplas (op, addr1, addr2, addr3)
        """
        self.cuadruplas = []
        self.etiquetas = {}
        self.pc = 0
        
        # Convertir a tuplas si es necesario
        for i, cuad in enumerate(cuadruplas):
            if hasattr(cuad, 'to_tuple'):
                tupla = cuad.to_tuple()
            else:
                tupla = cuad
            
            self.cuadruplas.append(tupla)
            
            # Registrar etiquetas
            if tupla[0] == 'lab':
                etiqueta = tupla[1]
                self.etiquetas[etiqueta] = i
    
    def reset(self):
        """Reinicia el estado del intérprete."""
        self.memoria = {}
        self.pc = 0
        self.salida = []
        self.ejecutando = False
    
    def set_entrada(self, valores):
        """Establece valores de entrada para operaciones READ.
        
        Args:
            valores: Lista de valores a leer
        """
        self.entrada_buffer = list(valores)
    
    def obtener_salida(self):
        """Retorna toda la salida generada por operaciones WRITE."""
        return self.salida.copy()
    
    def ejecutar(self, cuadruplas=None, entrada=None, max_steps=10000):
        """Ejecuta el programa completo.
        
        Args:
            cuadruplas: Opcional, cuádruplas a ejecutar
            entrada: Opcional, valores de entrada para READ
            max_steps: Límite de instrucciones para evitar loops infinitos
            
        Returns:
            dict con 'salida', 'memoria', 'steps'
        """
        if cuadruplas is not None:
            self.cargar_cuadruplas(cuadruplas)
        
        if entrada is not None:
            self.set_entrada(entrada)
        
        self.reset()
        self.ejecutando = True
        steps = 0
        
        try:
            while self.ejecutando and self.pc < len(self.cuadruplas) and steps < max_steps:
                self.ejecutar_paso()
                steps += 1
            
            if steps >= max_steps:
                raise RuntimeError(f"Límite de ejecución alcanzado ({max_steps} pasos). Posible loop infinito.")
            
            return {
                'salida': self.salida.copy(),
                'memoria': self.memoria.copy(),
                'steps': steps,
                'completado': not self.ejecutando or self.pc >= len(self.cuadruplas)
            }
            
        except Exception as e:
            raise RuntimeError(f"Error en ejecución (PC={self.pc}): {str(e)}")
    
    def ejecutar_paso(self):
        """Ejecuta una sola cuádruple (paso de ejecución)."""
        if self.pc >= len(self.cuadruplas):
            self.ejecutando = False
            return
        
        op, addr1, addr2, addr3 = self.cuadruplas[self.pc]
        
        # Ejecutar según la operación
        if op == 'asn':
            self._ejecutar_asignacion(addr1, addr2)
        elif op in ('add', 'sub', 'mul', 'div', 'mod'):
            self._ejecutar_aritmetica(op, addr1, addr2, addr3)
        elif op in ('gt', 'lt', 'ge', 'le', 'eq', 'ne'):
            self._ejecutar_relacional(op, addr1, addr2, addr3)
        elif op in ('and', 'or', 'not'):
            self._ejecutar_logico(op, addr1, addr2, addr3)
        elif op == 'neg':
            self._ejecutar_negacion(addr1, addr3)
        elif op == 'if_t':
            self._ejecutar_if_true(addr1, addr2)
        elif op == 'if_f':
            self._ejecutar_if_false(addr1, addr2)
        elif op == 'goto':
            self._ejecutar_goto(addr1)
        elif op == 'lab':
            # Las etiquetas no hacen nada en ejecución
            self.pc += 1
        elif op == 'rd':
            self._ejecutar_read(addr1)
        elif op == 'wri':
            self._ejecutar_write(addr1)
        elif op == 'halt':
            self.ejecutando = False
        else:
            raise ValueError(f"Operación desconocida: {op}")
    
    def _obtener_valor(self, addr):
        """Obtiene el valor de una dirección (variable, temporal o literal)."""
        if addr is None or addr == '_':
            return None
        
        # Si es un número literal
        try:
            # Intentar convertir a float primero (maneja int y float)
            if '.' in str(addr):
                return float(addr)
            else:
                return int(addr)
        except (ValueError, TypeError):
            pass
        
        # Si es una cadena literal (entre comillas)
        addr_str = str(addr)
        if addr_str.startswith('"') and addr_str.endswith('"'):
            return addr_str[1:-1]  # Remover comillas
        
        # Es una variable o temporal
        if addr_str not in self.memoria:
            # Inicializar en 0 si no existe
            self.memoria[addr_str] = 0
        
        return self.memoria[addr_str]
    
    def _ejecutar_asignacion(self, origen, destino):
        """Ejecuta una asignación: destino = origen"""
        valor = self._obtener_valor(origen)
        self.memoria[str(destino)] = valor
        self.pc += 1
    
    def _ejecutar_aritmetica(self, op, addr1, addr2, addr3):
        """Ejecuta operaciones aritméticas: addr3 = addr1 op addr2"""
        val1 = self._obtener_valor(addr1)
        val2 = self._obtener_valor(addr2)
        
        if op == 'add':
            resultado = val1 + val2
        elif op == 'sub':
            resultado = val1 - val2
        elif op == 'mul':
            resultado = val1 * val2
        elif op == 'div':
            if val2 == 0:
                raise ZeroDivisionError("División por cero")
            resultado = val1 / val2
        elif op == 'mod':
            resultado = val1 % val2
        else:
            raise ValueError(f"Operación aritmética desconocida: {op}")
        
        self.memoria[str(addr3)] = resultado
        self.pc += 1
    
    def _ejecutar_relacional(self, op, addr1, addr2, addr3):
        """Ejecuta operaciones relacionales: addr3 = addr1 op addr2"""
        val1 = self._obtener_valor(addr1)
        val2 = self._obtener_valor(addr2)
        
        if op == 'gt':
            resultado = val1 > val2
        elif op == 'lt':
            resultado = val1 < val2
        elif op == 'ge':
            resultado = val1 >= val2
        elif op == 'le':
            resultado = val1 <= val2
        elif op == 'eq':
            resultado = val1 == val2
        elif op == 'ne':
            resultado = val1 != val2
        else:
            raise ValueError(f"Operación relacional desconocida: {op}")
        
        # Convertir booleano a entero (1 o 0)
        self.memoria[str(addr3)] = 1 if resultado else 0
        self.pc += 1
    
    def _ejecutar_logico(self, op, addr1, addr2, addr3):
        """Ejecuta operaciones lógicas: addr3 = addr1 op addr2"""
        val1 = self._obtener_valor(addr1)
        
        if op == 'not':
            resultado = not val1
        else:
            val2 = self._obtener_valor(addr2)
            if op == 'and':
                resultado = val1 and val2
            elif op == 'or':
                resultado = val1 or val2
            else:
                raise ValueError(f"Operación lógica desconocida: {op}")
        
        # Convertir booleano a entero
        self.memoria[str(addr3)] = 1 if resultado else 0
        self.pc += 1
    
    def _ejecutar_negacion(self, addr1, addr3):
        """Ejecuta negación unaria: addr3 = -addr1"""
        valor = self._obtener_valor(addr1)
        self.memoria[str(addr3)] = -valor
        self.pc += 1
    
    def _ejecutar_if_true(self, condicion, etiqueta):
        """Salta a etiqueta si condición es verdadera"""
        valor = self._obtener_valor(condicion)
        if valor:  # Si es verdadero (diferente de 0)
            if etiqueta in self.etiquetas:
                self.pc = self.etiquetas[etiqueta]
            else:
                raise ValueError(f"Etiqueta no encontrada: {etiqueta}")
        else:
            self.pc += 1
    
    def _ejecutar_if_false(self, condicion, etiqueta):
        """Salta a etiqueta si condición es falsa"""
        valor = self._obtener_valor(condicion)
        if not valor:  # Si es falso (0)
            if etiqueta in self.etiquetas:
                self.pc = self.etiquetas[etiqueta]
            else:
                raise ValueError(f"Etiqueta no encontrada: {etiqueta}")
        else:
            self.pc += 1
    
    def _ejecutar_goto(self, etiqueta):
        """Salta incondicionalmente a una etiqueta"""
        if etiqueta in self.etiquetas:
            self.pc = self.etiquetas[etiqueta]
        else:
            raise ValueError(f"Etiqueta no encontrada: {etiqueta}")
    
    def _ejecutar_read(self, variable):
        """Lee un valor de entrada y lo almacena en la variable"""
        
        if not self.entrada_buffer:
            # Si no hay entrada, solicitar al usuario
            try:
                valor = input(f"Ingrese valor para {variable}: ")
            except EOFError:
                valor = 0
        else:
            valor = self.entrada_buffer.pop(0)

        # Intentar convertir automáticamente
        try:
            valor = float(valor) if '.' in str(valor) else int(valor)
        except:
            pass

        self.memoria[str(variable)] = valor
        self.pc += 1

    
    def _ejecutar_write(self, addr):
        """Escribe un valor a la salida"""
        valor = self._obtener_valor(addr)
        self.salida.append(valor)
        print(valor)  # También imprimir en consola
        self.pc += 1
    
    def imprimir_estado(self):
        """Imprime el estado actual del intérprete (útil para debugging)."""
        print(f"\n=== Estado del Intérprete ===")
        print(f"PC: {self.pc}")
        print(f"Memoria: {self.memoria}")
        print(f"Salida: {self.salida}")
        if self.pc < len(self.cuadruplas):
            print(f"Próxima instrucción: {self.cuadruplas[self.pc]}")
        print("=" * 30 + "\n")


# ============================================================
#                    EJEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    # Ejemplo: Ejecutar código intermedio
    
    # Código intermedio de ejemplo (factorial simplificado)
    cuadruplas_ejemplo = [
        ('asn', 5, 'n', None),      # n = 5
        ('asn', 1, 'fact', None),   # fact = 1
        ('asn', 1, 'i', None),      # i = 1
        ('lab', 'L1', None, None),  # etiqueta inicio loop
        ('gt', 'i', 'n', 't1'),     # t1 = i > n
        ('if_t', 't1', 'L2', None), # if t1 goto L2 (salir)
        ('mul', 'fact', 'i', 't2'), # t2 = fact * i
        ('asn', 't2', 'fact', None),# fact = t2
        ('add', 'i', 1, 't3'),      # t3 = i + 1
        ('asn', 't3', 'i', None),   # i = t3
        ('goto', 'L1', None, None), # goto L1 (loop)
        ('lab', 'L2', None, None),  # etiqueta fin
        ('wri', 'fact', None, None),# write fact
    ]
    
    print("Ejecutando código intermedio...")
    print("Cuádruplas:")
    for i, cuad in enumerate(cuadruplas_ejemplo):
        print(f"  {i}: {cuad}")
    print()
    
    interprete = InterpreteCI()
    resultado = interprete.ejecutar(cuadruplas_ejemplo)
    
    print(f"\nEjecución completada en {resultado['steps']} pasos")
    print(f"Salida: {resultado['salida']}")
    print(f"Estado final de memoria: {resultado['memoria']}")