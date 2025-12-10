# generador_codigo_intermedio.py
# Generador de Código Intermedio (TAC - Cuádruplas)
# Representación mediante cuádruplas de 4 campos: (op, addr1, addr2, addr3)

class Cuadrupla:
    """Representa una instrucción de código de 3 direcciones como cuádruple."""
    
    def __init__(self, op, addr1=None, addr2=None, addr3=None):
        self.op = op
        self.addr1 = addr1
        self.addr2 = addr2
        self.addr3 = addr3
    
    def __repr__(self):
        """Representación legible de la cuádruple."""
        a1 = self.addr1 if self.addr1 is not None else "_"
        a2 = self.addr2 if self.addr2 is not None else "_"
        a3 = self.addr3 if self.addr3 is not None else "_"
        return f"({self.op}, {a1}, {a2}, {a3})"
    
    def __str__(self):
        return self.__repr__()
    
    def to_tuple(self):
        """Retorna la cuádruple como tupla."""
        return (self.op, self.addr1, self.addr2, self.addr3)


class CodigoIntermedioGenerator:

    def __init__(self):
        self.temp_count = 0
        self.code = []   # lista de objetos Cuadrupla
        self.label_count = 0

    # -------- UTILIDADES -------- #

    def nuevo_temp(self):
        """Genera un nuevo temporal."""
        self.temp_count += 1
        return f"t{self.temp_count}"

    def nueva_etiqueta(self):
        """Genera una nueva etiqueta con formato uniforme L1, L2, L3..."""
        self.label_count += 1
        return f"L{self.label_count}"

    def emitir(self, op, addr1=None, addr2=None, addr3=None):
        """Agrega una cuádrupla al código.
        
        Args:
            op: Operación (str)
            addr1: Primera dirección (str o None)
            addr2: Segunda dirección (str o None)
            addr3: Tercera dirección (str o None)
        """
        cuadrupla = Cuadrupla(op, addr1, addr2, addr3)
        self.code.append(cuadrupla)

    def reset(self):
        """Reinicia los contadores y el código generado."""
        self.temp_count = 0
        self.label_count = 0
        self.code = []

    # -------- FUNCIÓN PRINCIPAL -------- #

    def generar(self, nodo_raiz):
        """Genera y retorna la lista de strings con las cuádruplas."""
        self.reset()
        self._recorrer(nodo_raiz)
        return [str(cuad) for cuad in self.code]

    def obtener_cuadruplas(self):
        """Retorna las cuádruplas como lista de objetos Cuadrupla."""
        return self.code.copy()
    
    def obtener_tuplas(self):
        """Retorna las cuádruplas como lista de tuplas."""
        return [cuad.to_tuple() for cuad in self.code]

    # ============================================================
    #                    VISITOR GENERAL
    # ============================================================

    def _recorrer(self, nodo):
        """Dispatcher principal: recibe un NodoAST/NodoAnotado y devuelve
        un temporal o literal (string) para expresiones, o None para sentencias."""
        if nodo is None:
            return None

        tipo = getattr(nodo, "tipo", None)
        valor = getattr(nodo, "valor", None)
        hijos = getattr(nodo, "hijos", []) or []

        # Manejar envoltorios comunes (no generan código directo)
        if tipo in ("lista_sentencias", "bloque", "bloque_if", "bloque_else", 
                    "bloque_do", "bloque_while"):
            for h in hijos:
                self._recorrer(h)
            return None

        # Nodos estructurales
        if tipo == "programa":
            if hijos:
                return self._recorrer(hijos[0])
            return None

        if tipo == "main":
            for h in hijos:
                self._recorrer(h)
            return None

        if tipo == "condicion":
            return self._recorrer(hijos[0]) if hijos else None

        if tipo == "declaracion_variable":
            return None

        # Sentencias
        if tipo == "asignacion":
            return self._asignacion(nodo)

        if tipo in ("post_inc", "post_increment", "post_dec", "post_decrement", 
                    "incremento", "decremento"):
            return self._post_inc_dec(nodo)

        if tipo == "seleccion":
            return self._if_else(nodo)

        if tipo in ("iteracion", "while"):
            return self._while(nodo)

        if tipo in ("repeticion", "do"):
            return self._do_until(nodo)

        if tipo in ("sent_in", "cin", "INPUT"):
            return self._cin(nodo)

        if tipo in ("sent_out", "cout", "OUTPUT"):
            return self._cout(nodo)

        # Expresiones unarias (negación, not)
        if tipo in ("negacion", "neg", "unario", "menos_unario", "-u", "operador_unario"):
            return self._negacion(nodo)

        # Expresiones aritméticas
        if tipo in ("suma_op", "SUMA", "suma", "expresion_simple", "expresion_aditiva", 
                    "termino", "expresion", "exp", "exp_simple"):
            # Si tiene operador, es una operación binaria
            if valor in ("+", "-") and len(hijos) >= 2:
                return self._suma(nodo)
            # Si solo tiene un hijo, delegar
            elif len(hijos) == 1:
                return self._recorrer(hijos[0])
            # Si tiene 2+ hijos sin operador explícito, asumir suma
            elif len(hijos) >= 2:
                return self._suma(nodo)
            return None

        if tipo in ("mult_op", "MULT", "mult", "factor", "expresion_multiplicativa", "term"):
            # Si tiene operador, es una operación binaria
            if valor in ("*", "/", "%") and len(hijos) >= 2:
                return self._mult(nodo)
            # Si solo tiene un hijo, delegar
            elif len(hijos) == 1:
                return self._recorrer(hijos[0])
            # Si tiene 2+ hijos sin operador explícito, asumir multiplicación
            elif len(hijos) >= 2:
                return self._mult(nodo)
            return None

        # Expresiones relacionales y lógicas
        if tipo in ("rel_op", "REL", "relacional", "comparacion"):
            return self._rel(nodo)

        if tipo in ("log_op", "AND", "OR", "logico"):
            return self._log(nodo)

        # Literales e identificadores
        if tipo in ("numero", "NUM", "FLOAT", "INT", "entero", "flotante"):
            return str(valor)

        if tipo in ("id", "ID", "identificador", "variable"):
            return str(valor)

        # Expresión entre paréntesis - procesar el contenido
        if tipo in ("expresion_paren", "parentesis", "paren"):
            if hijos:
                return self._recorrer(hijos[0])
            return None

        # Por defecto, recorrer hijos buscando expresiones
        resultado = None
        for h in hijos:
            res = self._recorrer(h)
            if res is not None:
                resultado = res
        
        return resultado

    # ============================================================
    #          GENERADORES PARA EXPRESIONES / SENTENCIAS
    # ============================================================

    def _asignacion(self, nodo):
        """Genera código para una asignación.
        Formato: (asn, valor, variable, _)
        """
        nombre_var = getattr(nodo, "valor", None)
        if not nombre_var:
            return None
            
        expr = nodo.hijos[0] if nodo.hijos else None
        val = self._recorrer(expr)

        if val is None:
            return None

        # Evitar asignaciones redundantes (a = a)
        if isinstance(val, str) and val == nombre_var:
            return nombre_var

        self.emitir("asn", val, nombre_var, None)
        return nombre_var

    def _post_inc_dec(self, nodo):
        """Genera código para post-incremento y post-decremento.
        Formato: (add/sub, variable, 1, temp) y (asn, temp, variable, _)
        """
        hijos = getattr(nodo, "hijos", []) or []
        if not hijos:
            return None
            
        idn = hijos[0]
        nombre = getattr(idn, "valor", None) or self._recorrer(idn)
        if nombre is None:
            return None

        # Generar temporal previo
        tmp = self.nuevo_temp()
        self.emitir("asn", nombre, tmp, None)
        
        # Actualizar variable
        if nodo.tipo in ("post_dec", "post_decrement", "decremento", "c--", "dec"):
            self.emitir("sub", nombre, "1", nombre)
        else:
            self.emitir("add", nombre, "1", nombre)
            
        return tmp

    def _operacion_binaria(self, nodo, op_default):
        """Método genérico para operaciones binarias.
        Formato: (op, operando1, operando2, resultado)
        """
        # Si el nodo tiene un valor específico de operador, usarlo
        op = getattr(nodo, "valor", None)
        if op is None:
            op = op_default
            
        hijos = getattr(nodo, "hijos", []) or []
        
        # Si no hay hijos, este nodo no es una operación válida
        if len(hijos) == 0:
            return None
            
        # Si solo hay un hijo, delegar el procesamiento a ese hijo
        if len(hijos) == 1:
            return self._recorrer(hijos[0])
        
        # Procesar operandos
        left = hijos[0] if len(hijos) > 0 else None
        right = hijos[1] if len(hijos) > 1 else None

        l = self._recorrer(left)
        r = self._recorrer(right)

        # Fallback: intentar obtener valor del nodo directamente
        if l is None and left is not None:
            l = getattr(left, "valor", None)
            if l is not None:
                l = str(l)
                
        if r is None and right is not None:
            r = getattr(right, "valor", None)
            if r is not None:
                r = str(r)

        if l is None or r is None:
            return None

        t = self.nuevo_temp()
        
        # Mapear operadores a formato estándar
        op_map = {
            "+": "add",
            "-": "sub",
            "*": "mul",
            "/": "div",
            "%": "mod",
            ">": "gt",
            "<": "lt",
            ">=": "ge",
            "<=": "le",
            "==": "eq",
            "!=": "ne",
            "&&": "and",
            "||": "or"
        }
        
        op_mapped = op_map.get(op, op)
        self.emitir(op_mapped, l, r, t)
        return t

    def _suma(self, nodo):
        """Suma / resta binaria."""
        hijos = getattr(nodo, "hijos", []) or []
        
        # Si solo hay un hijo, no es realmente una suma, delegar
        if len(hijos) == 1:
            return self._recorrer(hijos[0])
        
        # Si no hay hijos, retornar None
        if len(hijos) == 0:
            return None
            
        return self._operacion_binaria(nodo, "add")

    def _mult(self, nodo):
        """Multiplicación / división binaria."""
        hijos = getattr(nodo, "hijos", []) or []
        
        # Si solo hay un hijo, no es realmente una multiplicación, delegar
        if len(hijos) == 1:
            return self._recorrer(hijos[0])
        
        # Si no hay hijos, retornar None
        if len(hijos) == 0:
            return None
            
        return self._operacion_binaria(nodo, "mul")

    def _rel(self, nodo):
        """Relacionales: >, <, ==, etc."""
        return self._operacion_binaria(nodo, "eq")

    def _log(self, nodo):
        """Operadores lógicos (&&, ||)."""
        return self._operacion_binaria(nodo, "and")

    def _negacion(self, nodo):
        """Operador unario de negación (-expr) o positivo (+expr).
        Formato: (neg, operando, _, resultado)
        """
        hijos = getattr(nodo, "hijos", []) or []
        if not hijos:
            return None
        
        operando = self._recorrer(hijos[0])
        
        if operando is None:
            return None
        
        # Obtener el operador (+ o -)
        operador = getattr(nodo, "valor", "-")
        
        # Si el operador es +, simplemente retornar el operando sin modificar
        if operador == '+':
            return operando
        
        # Si es -, generar la negación
        t = self.nuevo_temp()
        self.emitir("neg", operando, None, t)
        return t

    # ============================================================
    #                 IF / ELSE
    # ============================================================

    def _if_else(self, nodo):
        """Genera código para if ... then ... else ... end
        Formato: (if_t, condicion, etiqueta_then, _)
                 (goto, etiqueta_fin, _, _)
                 (lab, etiqueta_else, _, _)
        """
        hijos = getattr(nodo, "hijos", []) or []
        cond_node = hijos[0] if len(hijos) > 0 else None
        bloque_if = hijos[1] if len(hijos) > 1 else None
        bloque_else = hijos[2] if len(hijos) > 2 else None

        t_cond = self._recorrer(cond_node)
        
        if t_cond is None:
            # Recorrer bloques aunque la condición sea inválida
            if bloque_if:
                self._recorrer(bloque_if)
            if bloque_else:
                self._recorrer(bloque_else)
            return None

        L_else = self.nueva_etiqueta()
        L_fin = self.nueva_etiqueta()

        # Si la condición es falsa, saltar al else
        self.emitir("if_f", t_cond, L_else, None)

        # Código del bloque if
        if bloque_if:
            self._recorrer(bloque_if)

        # Saltar al fin después del bloque if
        self.emitir("goto", L_fin, None, None)
        
        # Etiqueta del bloque else
        self.emitir("lab", L_else, None, None)

        # Código del bloque else
        if bloque_else:
            self._recorrer(bloque_else)

        # Etiqueta de fin
        self.emitir("lab", L_fin, None, None)
        return None

    # ============================================================
    #                 WHILE
    # ============================================================

    def _while(self, nodo):
        """Genera código para while ... do ... end
        Formato: (lab, etiqueta_inicio, _, _)
                 (if_f, condicion, etiqueta_fin, _)
                 (goto, etiqueta_inicio, _, _)
        """
        hijos = getattr(nodo, "hijos", []) or []
        cond_node = hijos[0] if len(hijos) > 0 else None
        bloque = hijos[1] if len(hijos) > 1 else None

        L_inicio = self.nueva_etiqueta()
        L_fin = self.nueva_etiqueta()

        # Etiqueta de inicio del ciclo
        self.emitir("lab", L_inicio, None, None)

        # Evaluar condición
        t_cond = self._recorrer(cond_node)
        
        if t_cond is None:
            if bloque:
                self._recorrer(bloque)
            self.emitir("lab", L_fin, None, None)
            return None

        # Si la condición es falsa, salir del ciclo
        self.emitir("if_f", t_cond, L_fin, None)
        
        # Código del bloque
        if bloque:
            self._recorrer(bloque)
            
        # Regresar al inicio
        self.emitir("goto", L_inicio, None, None)
        
        # Etiqueta de fin
        self.emitir("lab", L_fin, None, None)
        return None

    # ============================================================
    #                 DO – UNTIL
    # ============================================================

    def _do_until(self, nodo):
        """Genera código para do ... until
        Formato: (lab, etiqueta_inicio, _, _)
                 (if_f, condicion, etiqueta_inicio, _)
        """
        hijos = getattr(nodo, "hijos", []) or []
        bloque_do = hijos[0] if len(hijos) > 0 else None
        cond_node = hijos[1] if len(hijos) > 1 else None

        L_ini = self.nueva_etiqueta()
        L_fin = self.nueva_etiqueta()

        # Etiqueta de inicio
        self.emitir("lab", L_ini, None, None)
        
        # Código del bloque
        if bloque_do:
            self._recorrer(bloque_do)

        # Evaluar condición
        t_cond = self._recorrer(cond_node)
        
        if t_cond is None:
            self.emitir("lab", L_fin, None, None)
            return None

        # do ... until: repetir mientras NO se cumpla (si es falso, regresar)
        self.emitir("if_f", t_cond, L_ini, None)
        
        # Etiqueta de fin
        self.emitir("lab", L_fin, None, None)
        return None

    # ============================================================
    #             CIN / COUT
    # ============================================================

    def _cin(self, nodo):
        """Genera código para entrada (cin/read).
        Formato: (rd, variable, _, _)
        """
        hijos = getattr(nodo, "hijos", []) or []
        if not hijos:
            return None
            
        var_node = hijos[0]
        nombre = getattr(var_node, "valor", None) or self._recorrer(var_node)
        
        if nombre is None:
            return None
            
        self.emitir("rd", nombre, None, None)
        return None

    def _cout(self, nodo):
        """Genera código para salida (cout/write).
        Formato: (wri, variable/expresion, _, _)
        """
        hijos = getattr(nodo, "hijos", []) or []
        if not hijos:
            return None
            
        salida = self._recorrer(hijos[0])
        
        if salida is None:
            salida = getattr(hijos[0], "valor", None)
            if salida is None:
                return None
            salida = str(salida)
            
        self.emitir("wri", salida, None, None)
        return None