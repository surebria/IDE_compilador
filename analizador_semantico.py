"""
Analizador Semántico - Fase 3 del Compilador
Adaptado para trabajar con NodoAST de logic.py
"""

class ErrorSemantico:
    """Representa un error semántico."""
    def __init__(self, tipo, descripcion, linea, columna, fatal=False):
        self.tipo = tipo
        self.descripcion = descripcion
        self.linea = linea
        self.columna = columna
        self.fatal = fatal
    
    def __str__(self):
        fatal_str = " [FATAL]" if self.fatal else ""
        return f"{self.tipo}: {self.descripcion} (Línea {self.linea}, Columna {self.columna}){fatal_str}"
    
    def to_dict(self):
        return {
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "linea": self.linea,
            "columna": self.columna,
            "fatal": self.fatal
        }


class Simbolo:
    """Representa un símbolo en la tabla de símbolos."""
    def __init__(self, nombre, tipo, valor=None, linea=0, columna=0, ambito='global'):
        self.nombre = nombre
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
        self.ambito = ambito
        self.ubicaciones = [(linea, columna)]  # Lista de usos
    
    def agregar_uso(self, linea, columna):
        """Registra un nuevo uso de la variable."""
        self.ubicaciones.append((linea, columna))

    def agregar_ubicacion(self, linea, columna):
        """Agrega una nueva ubicación (línea, columna) de uso del símbolo."""
        if (linea, columna) not in self.ubicaciones:
            self.ubicaciones.append((linea, columna))
    
    def get_ubicaciones_str(self):
        """Retorna las ubicaciones como string."""
        return "; ".join([f"{l}:{c}" for l, c in self.ubicaciones])

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "tipo": self.tipo,
            "valor": self.valor,
            "linea": self.linea, # Línea de declaración (original)
            "columna": self.columna, # Columna de declaración (original)
            "ambito": self.ambito,
            # Formatea las ubicaciones: (Línea, Columna) -> "L:C, L:C, ..."
            "ubicaciones_str": ", ".join([f"{l}:{c}" for l, c in self.ubicaciones])
        }
    def __str__(self):
        return f"Simbolo({self.nombre}, {self.tipo}, valor={self.valor}, ámbito={self.ambito})"


class TablaSimbolos:
    """Tabla de símbolos con soporte para ámbitos."""
    def __init__(self):
        self.tabla = {}
        self.pila_ambitos = ['global']
    
    def get_ambito_actual(self):
        """Retorna el ámbito actual."""
        return self.pila_ambitos[-1]
    
    def enter_scope(self, nombre_ambito):
        """Entra en un nuevo ámbito."""
        nuevo_ambito = f"{self.get_ambito_actual()}.{nombre_ambito}"
        self.pila_ambitos.append(nuevo_ambito)
    
    def exit_scope(self):
        """Sale del ámbito actual."""
        if len(self.pila_ambitos) > 1:
            self.pila_ambitos.pop()
    
    def declare(self, nombre, tipo, linea, columna):
        """
        Declara una nueva variable en el ámbito actual.
        Retorna (success, mensaje).
        """
        ambito = self.get_ambito_actual()
        clave = f"{ambito}_{nombre}"
        
        if clave in self.tabla:
            return False, f"Variable '{nombre}' ya declarada en el ámbito {ambito}"
        
        simbolo = Simbolo(nombre, tipo, None, linea, columna, ambito)
        self.tabla[clave] = simbolo
        return True, None
    
    def lookup(self, nombre, linea, columna):
        """
        Busca una variable, primero en el ámbito actual y luego en ámbitos padres.
        Registra el uso de la variable.
        Retorna (simbolo, mensaje_error).
        """
        # Buscar en ámbito actual y padres
        for i in range(len(self.pila_ambitos) - 1, -1, -1):
            ambito = self.pila_ambitos[i]
            clave = f"{ambito}_{nombre}"
            if clave in self.tabla:
                simbolo = self.tabla[clave]
                simbolo.agregar_uso(linea, columna)
                return simbolo, None
        
        return None, f"Variable '{nombre}' no declarada"
    
    def actualizar_valor(self, nombre, valor):
        """Actualiza el valor de una variable."""
        simbolo, _ = self.lookup(nombre, 0, 0)
        if simbolo:
            simbolo.valor = valor
    
    def get_all_entries(self):
        """Retorna todas las entradas de la tabla."""
        return list(self.tabla.values())
    
    def listar_simbolos(self):
        """Alias para compatibilidad."""
        return self.get_all_entries()


class NodoAnotado:
    """Nodo del AST con anotaciones semánticas."""
    def __init__(self, tipo, valor=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = []
        self.tipo_dato = None
        self.valor_calculado = None
        self.linea = None
        self.columna = None
        self.nodo_original = None
    
    def agregar_hijo(self, hijo):
        if hijo:
            self.hijos.append(hijo)
    
    def __str__(self):
        return f"NodoAnotado({self.tipo}, {self.valor}, tipo={self.tipo_dato}, valor={self.valor_calculado})"


class AnalizadorSemantico:
    """Analizador semántico que recorre el AST y verifica reglas semánticas."""
    
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.errores = []
        self.should_stop = False
    
    def report_error(self, tipo, descripcion, linea, columna, fatal=False):
        """Reporta un error semántico."""
        error = ErrorSemantico(tipo, descripcion, linea, columna, fatal)
        self.errores.append(error)
        if fatal:
            self.should_stop = True
        return error
    
    def infer_type_from_literal(self, valor_str):
        """Infiere el tipo de un literal."""
        if valor_str in ('true', 'false'):
            return 'bool'
        try:
            if '.' in str(valor_str):
                float(valor_str)
                return 'float'
            else:
                int(valor_str)
                return 'int'
        except (ValueError, TypeError):
            return None
    
    def check_type_compatibility(self, tipo_dest, tipo_src, linea, columna, contexto="asignación"):
        """Verifica compatibilidad de tipos."""
        if tipo_dest == tipo_src:
            return True, None
        
        # Promoción int -> float permitida
        if tipo_dest == 'float' and tipo_src == 'int':
            return True, None
        
        # Otras incompatibilidades
        if tipo_dest == 'int' and tipo_src == 'float':
            return False, f"No se puede asignar float a int"
        
        if tipo_dest == 'bool' or tipo_src == 'bool':
            return False, f"Incompatibilidad de tipos: bool no es compatible con {tipo_src if tipo_dest == 'bool' else tipo_dest}"
        
        return False, f"Tipos incompatibles en {contexto}: {tipo_dest} vs {tipo_src}"
    
    def analizar(self, ast_root):
        """
        Analiza el AST completo.
        Retorna (ast_anotado, tabla_simbolos, errores).
        """
        if not ast_root:
            self.report_error("AST_INVALIDO", "El AST está vacío", 0, 0, fatal=True)
            return None, self.tabla_simbolos, self.errores
        
        # Anotar el AST completo
        ast_anotado = self.anotar_nodo(ast_root)
        
        return ast_anotado, self.tabla_simbolos, self.errores
    
    def anotar_nodo(self, nodo):
        """Anota un nodo del AST con información semántica."""
        if nodo is None:
            return None
        
        # Crear nodo anotado
        nodo_anotado = NodoAnotado(nodo.tipo, nodo.valor)
        nodo_anotado.linea = getattr(nodo, 'linea', 0) or 0
        nodo_anotado.columna = getattr(nodo, 'columna', 0) or 0
        nodo_anotado.nodo_original = nodo
            
        # Procesar según tipo de nodo
        if nodo.tipo == "programa":
            self.procesar_programa(nodo, nodo_anotado)
        
        elif nodo.tipo == "main":
            self.procesar_main(nodo, nodo_anotado)
        
        elif nodo.tipo == "declaracion_variable":
            self.procesar_declaracion(nodo, nodo_anotado)
        
        elif nodo.tipo == "asignacion":
            self.procesar_asignacion(nodo, nodo_anotado)
        
        elif nodo.tipo == "seleccion":
            self.procesar_seleccion(nodo, nodo_anotado)
        
        elif nodo.tipo == "iteracion":
            self.procesar_iteracion(nodo, nodo_anotado)
        
        elif nodo.tipo == "repeticion":
            self.procesar_repeticion(nodo, nodo_anotado)
        
        elif nodo.tipo == "sent_in":
            self.procesar_entrada(nodo, nodo_anotado)
        
        elif nodo.tipo == "sent_out":
            self.procesar_salida(nodo, nodo_anotado)
        
        else:
            # Para otros nodos, anotar hijos recursivamente
            for hijo in nodo.hijos:
                hijo_anotado = self.anotar_nodo(hijo)
                if hijo_anotado:
                    nodo_anotado.agregar_hijo(hijo_anotado)
        
        return nodo_anotado
    
    def procesar_programa(self, nodo, nodo_anotado):
        """Procesa el nodo programa."""
        for hijo in nodo.hijos:
            hijo_anotado = self.anotar_nodo(hijo)
            if hijo_anotado:
                nodo_anotado.agregar_hijo(hijo_anotado)
    
    def procesar_main(self, nodo, nodo_anotado):
        """Procesa el bloque main."""
        for hijo in nodo.hijos:
            hijo_anotado = self.anotar_nodo(hijo)
            if hijo_anotado:
                nodo_anotado.agregar_hijo(hijo_anotado)
    
    def procesar_declaracion(self, nodo, nodo_anotado):
        """Procesa declaración de variables."""
        tipo_dato = None
        
        # Obtener tipo de dato
        for hijo in nodo.hijos:
            if hijo.tipo == "tipo":
                tipo_dato = hijo.valor
                hijo_anotado = NodoAnotado("tipo", hijo.valor)
                hijo_anotado.tipo_dato = tipo_dato
                nodo_anotado.agregar_hijo(hijo_anotado)
                break
        
        # Procesar identificadores
        for hijo in nodo.hijos:
            if hijo.tipo == "identificador":
                for id_hijo in hijo.hijos:
                    if id_hijo.tipo == "id":
                        nombre_var = id_hijo.valor
                        linea = getattr(id_hijo, 'linea', 0) or getattr(nodo, 'linea', 0) or 0
                        columna = getattr(id_hijo, 'columna', 0) or getattr(nodo, 'columna', 0) or 0
                    
                    
                        # Declarar en tabla de símbolos
                        success, error_msg = self.tabla_simbolos.declare(
                            nombre_var, tipo_dato, linea, columna
                        )
                        
                        if not success:
                            self.report_error("DUPLICIDAD_DECLARACION", error_msg, linea, columna)
                        
                        # Anotar nodo
                        id_anotado = NodoAnotado("id", nombre_var)
                        id_anotado.tipo_dato = tipo_dato
                        id_anotado.valor_calculado = None
                        id_anotado.linea = linea
                        id_anotado.columna = columna
                        nodo_anotado.agregar_hijo(id_anotado)
        
        nodo_anotado.tipo_dato = tipo_dato
    
    def procesar_asignacion(self, nodo, nodo_anotado):
        """Procesa asignación con verificación de tipos."""
        nombre_var = nodo.valor
        linea = getattr(nodo, 'linea', 0) or 0
        columna = getattr(nodo, 'columna', 0) or 0
        
        # Verificar que la variable esté declarada
        simbolo, error_msg = self.tabla_simbolos.lookup(nombre_var, linea, columna)
        
        if not simbolo:
            self.report_error("VARIABLE_NO_DECLARADA", error_msg, linea, columna)
            nodo_anotado.tipo_dato = "desconocido"
            nodo_anotado.valor_calculado = None
            return
        
        # Evaluar expresión del lado derecho
        if nodo.hijos:
            expr_anotada = self.evaluar_expresion(nodo.hijos[0])
            nodo_anotado.agregar_hijo(expr_anotada)
            
            # Verificar compatibilidad de tipos
            if expr_anotada.tipo_dato and simbolo.tipo:
                es_compatible, mensaje = self.check_type_compatibility(
                    simbolo.tipo, expr_anotada.tipo_dato, linea, columna
                )
                if not es_compatible:
                    self.report_error("TIPO_INCOMPATIBLE", mensaje, linea, columna)
            
            # Actualizar valor en tabla de símbolos
            if expr_anotada.valor_calculado is not None:
                self.tabla_simbolos.actualizar_valor(nombre_var, expr_anotada.valor_calculado)
            
            nodo_anotado.tipo_dato = simbolo.tipo
            nodo_anotado.valor_calculado = expr_anotada.valor_calculado
        else:
            nodo_anotado.tipo_dato = simbolo.tipo
            nodo_anotado.valor_calculado = None
    
    def evaluar_expresion(self, nodo):
        """Evalúa una expresión y retorna nodo anotado con tipo y valor."""
        if nodo is None:
            nodo_error = NodoAnotado("error", None)
            nodo_error.tipo_dato = "desconocido"
            nodo_error.valor_calculado = None
            return nodo_error
        
        nodo_anotado = NodoAnotado(nodo.tipo, nodo.valor)
        nodo_anotado.linea = getattr(nodo, 'linea', 0)
        nodo_anotado.columna = getattr(nodo, 'columna', 0)
        
        # Número
        if nodo.tipo == "numero":
            tipo = self.infer_type_from_literal(nodo.valor)
            nodo_anotado.tipo_dato = tipo
            try:
                if tipo == "float":
                    nodo_anotado.valor_calculado = float(nodo.valor)
                else:
                    nodo_anotado.valor_calculado = int(nodo.valor)
            except (ValueError, TypeError):
                nodo_anotado.valor_calculado = None
        
        # Identificador
        elif nodo.tipo == "id":
            simbolo, error_msg = self.tabla_simbolos.lookup(
                nodo.valor,
                getattr(nodo, 'linea', 0),
                getattr(nodo, 'columna', 0)
            )
            if simbolo:
                nodo_anotado.tipo_dato = simbolo.tipo
                nodo_anotado.valor_calculado = simbolo.valor
            else:
                self.report_error("VARIABLE_NO_DECLARADA", error_msg, 
                                getattr(nodo, 'linea', 0), getattr(nodo, 'columna', 0))
                nodo_anotado.tipo_dato = "desconocido"
                nodo_anotado.valor_calculado = None
        
        # Booleano
        elif nodo.tipo == "bool":
            nodo_anotado.tipo_dato = "bool"
            nodo_anotado.valor_calculado = nodo.valor == "true"
        
        # Operadores suma/resta
        elif nodo.tipo == "suma_op":
            self.evaluar_operacion_aritmetica(nodo, nodo_anotado)
        
        # Operadores multiplicación/división
        elif nodo.tipo == "mult_op":
            self.evaluar_operacion_aritmetica(nodo, nodo_anotado)
        
        # Operador potencia
        elif nodo.tipo == "pot_op":
            self.evaluar_operacion_aritmetica(nodo, nodo_anotado)
        
        # Operadores relacionales
        elif nodo.tipo == "rel_op":
            self.evaluar_operacion_relacional(nodo, nodo_anotado)
        
        # Operadores lógicos
        elif nodo.tipo == "log_op":
            self.evaluar_operacion_logica(nodo, nodo_anotado)
        
        # Expresiones compuestas
        elif nodo.tipo in ["expresion_simple", "expresion_logica", "expresion_relacional", "expresion"]:
            if len(nodo.hijos) == 1:
                return self.evaluar_expresion(nodo.hijos[0])
            else:
                for hijo in nodo.hijos:
                    hijo_anotado = self.evaluar_expresion(hijo)
                    nodo_anotado.agregar_hijo(hijo_anotado)
                
                if nodo_anotado.hijos:
                    ultimo = nodo_anotado.hijos[-1]
                    nodo_anotado.tipo_dato = ultimo.tipo_dato
                    nodo_anotado.valor_calculado = ultimo.valor_calculado
        
        else:
            # Otros nodos: procesar hijos
            for hijo in nodo.hijos:
                hijo_anotado = self.evaluar_expresion(hijo)
                nodo_anotado.agregar_hijo(hijo_anotado)
            
            if nodo_anotado.hijos:
                ultimo = nodo_anotado.hijos[-1]
                nodo_anotado.tipo_dato = ultimo.tipo_dato
                nodo_anotado.valor_calculado = ultimo.valor_calculado
        
        return nodo_anotado
    
    def evaluar_operacion_aritmetica(self, nodo, nodo_anotado):
        """Evalúa operaciones aritméticas."""
        if len(nodo.hijos) < 2:
            nodo_anotado.tipo_dato = "desconocido"
            nodo_anotado.valor_calculado = None
            return
        
        izq = self.evaluar_expresion(nodo.hijos[0])
        der = self.evaluar_expresion(nodo.hijos[1])
        
        nodo_anotado.agregar_hijo(izq)
        nodo_anotado.agregar_hijo(der)
        
        if not izq.tipo_dato or not der.tipo_dato:
            nodo_anotado.tipo_dato = None
            nodo_anotado.valor_calculado = None
            return
        
        # Verificar que sean numéricos
        if izq.tipo_dato == 'bool' or der.tipo_dato == 'bool':
            self.report_error("TIPO_INCOMPATIBLE",
                            f"Operador aritmético no puede usarse con bool",
                            getattr(nodo, 'linea', 0), getattr(nodo, 'columna', 0))
            nodo_anotado.tipo_dato = None
            return
        
        # Inferir tipo resultado
        tipo_resultado = 'float' if (izq.tipo_dato == 'float' or der.tipo_dato == 'float') else 'int'
        nodo_anotado.tipo_dato = tipo_resultado
        
        # Calcular valor
        if izq.valor_calculado is not None and der.valor_calculado is not None:
            try:
                val_izq = float(izq.valor_calculado) if tipo_resultado == 'float' else int(izq.valor_calculado)
                val_der = float(der.valor_calculado) if tipo_resultado == 'float' else int(der.valor_calculado)
                
                if nodo.valor == '+':
                    resultado = val_izq + val_der
                elif nodo.valor == '-':
                    resultado = val_izq - val_der
                elif nodo.valor == '*':
                    resultado = val_izq * val_der
                elif nodo.valor == '/':
                    if val_der == 0:
                        self.report_error("DIVISION_POR_CERO", "División por cero",
                                        getattr(nodo, 'linea', 0), getattr(nodo, 'columna', 0))
                        resultado = None
                    else:
                        resultado = val_izq / val_der
                elif nodo.valor == '%':
                    resultado = val_izq % val_der
                elif nodo.valor == '^':
                    resultado = val_izq ** val_der
                else:
                    resultado = None
                
                if resultado is not None:
                    nodo_anotado.valor_calculado = int(resultado) if tipo_resultado == 'int' else float(resultado)
            except:
                nodo_anotado.valor_calculado = None
    
    def evaluar_operacion_relacional(self, nodo, nodo_anotado):
        """Evalúa operaciones relacionales."""
        if len(nodo.hijos) < 2:
            nodo_anotado.tipo_dato = "bool"
            nodo_anotado.valor_calculado = None
            return
        
        izq = self.evaluar_expresion(nodo.hijos[0])
        der = self.evaluar_expresion(nodo.hijos[1])
        
        nodo_anotado.agregar_hijo(izq)
        nodo_anotado.agregar_hijo(der)
        nodo_anotado.tipo_dato = "bool"
        
        if not izq.tipo_dato or not der.tipo_dato:
            nodo_anotado.valor_calculado = None
            return
        
        # Calcular valor
        if izq.valor_calculado is not None and der.valor_calculado is not None:
            try:
                val_izq = float(izq.valor_calculado)
                val_der = float(der.valor_calculado)
                
                if nodo.valor == '<':
                    resultado = val_izq < val_der
                elif nodo.valor == '>':
                    resultado = val_izq > val_der
                elif nodo.valor == '<=':
                    resultado = val_izq <= val_der
                elif nodo.valor == '>=':
                    resultado = val_izq >= val_der
                elif nodo.valor == '==':
                    resultado = val_izq == val_der
                elif nodo.valor == '!=':
                    resultado = val_izq != val_der
                else:
                    resultado = None
                
                nodo_anotado.valor_calculado = resultado
            except:
                nodo_anotado.valor_calculado = None
    
    def evaluar_operacion_logica(self, nodo, nodo_anotado):
        """Evalúa operaciones lógicas."""
        if len(nodo.hijos) < 2:
            nodo_anotado.tipo_dato = "bool"
            nodo_anotado.valor_calculado = None
            return
        
        izq = self.evaluar_expresion(nodo.hijos[0])
        der = self.evaluar_expresion(nodo.hijos[1])
        
        nodo_anotado.agregar_hijo(izq)
        nodo_anotado.agregar_hijo(der)
        nodo_anotado.tipo_dato = "bool"
        
        if not izq.tipo_dato or not der.tipo_dato:
            nodo_anotado.valor_calculado = None
            return
        
        # Verificar que sean bool
        if izq.tipo_dato != 'bool' or der.tipo_dato != 'bool':
            self.report_error("TIPO_INCOMPATIBLE",
                            "Operadores lógicos requieren operandos bool",
                            getattr(nodo, 'linea', 0), getattr(nodo, 'columna', 0))
            return
        
        # Calcular valor
        if izq.valor_calculado is not None and der.valor_calculado is not None:
            try:
                val_izq = bool(izq.valor_calculado)
                val_der = bool(der.valor_calculado)
                
                if nodo.valor == '&&':
                    nodo_anotado.valor_calculado = val_izq and val_der
                elif nodo.valor == '||':
                    nodo_anotado.valor_calculado = val_izq or val_der
            except:
                nodo_anotado.valor_calculado = None
    
    def procesar_seleccion(self, nodo, nodo_anotado):
        """Procesa estructura if-then-else."""
        for hijo in nodo.hijos:
            hijo_anotado = self.anotar_nodo(hijo)
            if hijo_anotado:
                nodo_anotado.agregar_hijo(hijo_anotado)
    
    def procesar_iteracion(self, nodo, nodo_anotado):
        """Procesa estructura while."""
        for hijo in nodo.hijos:
            hijo_anotado = self.anotar_nodo(hijo)
            if hijo_anotado:
                nodo_anotado.agregar_hijo(hijo_anotado)
    
    def procesar_repeticion(self, nodo, nodo_anotado):
        """Procesa estructura do-while/until."""
        for hijo in nodo.hijos:
            hijo_anotado = self.anotar_nodo(hijo)
            if hijo_anotado:
                nodo_anotado.agregar_hijo(hijo_anotado)
    
    def procesar_entrada(self, nodo, nodo_anotado):
        """Procesa sentencia cin."""
        for hijo in nodo.hijos:
            if hijo.tipo == "id":
                nombre_var = hijo.valor
                # Capturar línea y columna del nodo hijo, o del nodo padre si no está disponible
                linea = getattr(hijo, 'linea', None)
                columna = getattr(hijo, 'columna', None)
                
                # Si el hijo no tiene posición, intentar con el nodo padre
                if linea is None or linea == 0:
                    linea = getattr(nodo, 'linea', 0)
                if columna is None or columna == 0:
                    columna = getattr(nodo, 'columna', 0)
                
                # Si aún no hay posición válida, usar valores por defecto
                if linea is None:
                    linea = 0
                if columna is None:
                    columna = 0
                
                simbolo, error_msg = self.tabla_simbolos.lookup(nombre_var, linea, columna)
                
                if not simbolo:
                    self.report_error("VARIABLE_NO_DECLARADA", error_msg, linea, columna)
                
                id_anotado = NodoAnotado("id", nombre_var)
                id_anotado.tipo_dato = simbolo.tipo if simbolo else "desconocido"
                id_anotado.linea = linea
                id_anotado.columna = columna
                nodo_anotado.agregar_hijo(id_anotado)

    def procesar_id(self, nodo, nodo_anotado):
        """Procesa un identificador (variable) en una expresión o asignación."""
        nombre_var = nodo.valor
        
        # Obtener la posición del nodo hijo (ID) o usar la del padre si no está disponible
        # (Esto ya lo tienes, pero asegúrate de que 'linea' y 'columna' sean las del USO actual)
        
        linea = getattr(nodo, 'linea', 0)
        columna = getattr(nodo, 'columna', 0)
        
        # ... (Tu lógica de ajuste de línea/columna si es necesario)
        
        simbolo, error_msg = self.tabla_simbolos.lookup(nombre_var, linea, columna)
        
        if not simbolo:
            self.report_error("VARIABLE_NO_DECLARADA", error_msg, linea, columna)
        else:
            # 🚨 ¡NUEVO! Registrar la ubicación de USO (línea/columna actual)
            simbolo.agregar_ubicacion(linea, columna)
            
        id_anotado = NodoAnotado("id", nombre_var)
        id_anotado.tipo_dato = simbolo.tipo if simbolo else "desconocido"
        id_anotado.linea = linea
        id_anotada.columna = columna
        nodo_anotado.agregar_hijo(id_anotado)
    
    def procesar_salida(self, nodo, nodo_anotado):
        """Procesa sentencia cout."""
        for hijo in nodo.hijos:
            hijo_anotado = self.evaluar_expresion(hijo)
            nodo_anotado.agregar_hijo(hijo_anotado)


def ejecutar_analisis_semantico(ast):
    """Función principal para ejecutar el análisis semántico."""
    analizador = AnalizadorSemantico()
    return analizador.analizar(ast)