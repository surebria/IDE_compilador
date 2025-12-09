# generador_codigo_intermedio.py
# Generador de Código Intermedio (TAC - Cuádruplas)
# Compatible con NodoAST / NodoAnotado

class CodigoIntermedioGenerator:

    def __init__(self):
        self.temp_count = 0
        self.code = []   # lista de cuádruplas (op, arg1, arg2, res)
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

    def emitir(self, op, a1="-", a2="-", res="-"):
        """Agrega una cuádrupla al código."""
        self.code.append((op, a1, a2, res))

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
        return [f"({op}, {a1}, {a2}, {res})" for (op, a1, a2, res) in self.code]

    def obtener_cuadruplas(self):
        """Retorna las cuádruplas como lista de tuplas."""
        return self.code.copy()

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

        # Expresiones
        if tipo in ("suma_op", "SUMA", "suma", "expresion_simple"):
            return self._suma(nodo)

        if tipo in ("mult_op", "MULT", "mult"):
            return self._mult(nodo)

        if tipo in ("rel_op", "REL", "relacional"):
            return self._rel(nodo)

        if tipo == "log_op":
            return self._log(nodo)

        if tipo in ("numero", "NUM", "FLOAT"):
            return str(valor)

        if tipo in ("id", "ID", "identificador"):
            return str(valor)

        # Por defecto, recorrer hijos
        for h in hijos:
            res = self._recorrer(h)
            if isinstance(res, str):
                return res

        return None

    # ============================================================
    #          GENERADORES PARA EXPRESIONES / SENTENCIAS
    # ============================================================

    def _asignacion(self, nodo):
        """Genera código para una asignación. Nodo.valor = nombre var, hijo[0] = expr."""
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

        self.emitir("=", val, "-", nombre_var)
        return nombre_var

    def _post_inc_dec(self, nodo):
        """Genera código para post-incremento y post-decremento (a++ / c--)."""
        hijos = getattr(nodo, "hijos", []) or []
        if not hijos:
            return None
            
        idn = hijos[0]
        nombre = getattr(idn, "valor", None) or self._recorrer(idn)
        if nombre is None:
            return None

        # Generar temporal previo
        tmp = self.nuevo_temp()
        self.emitir("=", nombre, "-", tmp)
        
        # Actualizar variable
        if nodo.tipo in ("post_dec", "post_decrement", "decremento", "c--", "dec"):
            self.emitir("-", nombre, "1", nombre)
        else:
            self.emitir("+", nombre, "1", nombre)
            
        return tmp

    def _operacion_binaria(self, nodo, op_default):
        """Método genérico para operaciones binarias."""
        op = getattr(nodo, "valor", op_default)
        left = nodo.hijos[0] if len(nodo.hijos) > 0 else None
        right = nodo.hijos[1] if len(nodo.hijos) > 1 else None

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
        self.emitir(op, l, r, t)
        return t

    def _suma(self, nodo):
        """Suma / resta binaria."""
        return self._operacion_binaria(nodo, "+")

    def _mult(self, nodo):
        """Multiplicación / división binaria."""
        return self._operacion_binaria(nodo, "*")

    def _rel(self, nodo):
        """Relacionales: >, <, ==, etc."""
        return self._operacion_binaria(nodo, "==")

    def _log(self, nodo):
        """Operadores lógicos (&&, ||)."""
        return self._operacion_binaria(nodo, "&&")

    # ============================================================
    #                 IF / ELSE
    # ============================================================

    def _if_else(self, nodo):
        """Genera código para if ... then ... else ... end"""
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

        self.emitir("IFFALSE", t_cond, "-", L_else)

        if bloque_if:
            self._recorrer(bloque_if)

        self.emitir("GOTO", "-", "-", L_fin)
        self.emitir("LABEL", "-", "-", L_else)

        if bloque_else:
            self._recorrer(bloque_else)

        self.emitir("LABEL", "-", "-", L_fin)
        return None

    # ============================================================
    #                 WHILE
    # ============================================================

    def _while(self, nodo):
        """Genera código para while ... do ... end"""
        hijos = getattr(nodo, "hijos", []) or []
        cond_node = hijos[0] if len(hijos) > 0 else None
        bloque = hijos[1] if len(hijos) > 1 else None

        L_inicio = self.nueva_etiqueta()
        L_fin = self.nueva_etiqueta()

        self.emitir("LABEL", "-", "-", L_inicio)

        t_cond = self._recorrer(cond_node)
        
        if t_cond is None:
            if bloque:
                self._recorrer(bloque)
            self.emitir("LABEL", "-", "-", L_fin)
            return None

        self.emitir("IFFALSE", t_cond, "-", L_fin)
        
        if bloque:
            self._recorrer(bloque)
            
        self.emitir("GOTO", "-", "-", L_inicio)
        self.emitir("LABEL", "-", "-", L_fin)
        return None

    # ============================================================
    #                 DO – UNTIL
    # ============================================================

    def _do_until(self, nodo):
        """Genera código para do ... until"""
        hijos = getattr(nodo, "hijos", []) or []
        bloque_do = hijos[0] if len(hijos) > 0 else None
        cond_node = hijos[1] if len(hijos) > 1 else None

        L_ini = self.nueva_etiqueta()
        L_fin = self.nueva_etiqueta()

        self.emitir("LABEL", "-", "-", L_ini)
        
        if bloque_do:
            self._recorrer(bloque_do)

        t_cond = self._recorrer(cond_node)
        
        if t_cond is None:
            self.emitir("LABEL", "-", "-", L_fin)
            return None

        # do ... until: repetir mientras NO se cumpla
        self.emitir("IFFALSE", t_cond, "-", L_ini)
        self.emitir("LABEL", "-", "-", L_fin)
        return None

    # ============================================================
    #             CIN / COUT
    # ============================================================

    def _cin(self, nodo):
        """Genera código para entrada (cin/read)."""
        hijos = getattr(nodo, "hijos", []) or []
        if not hijos:
            return None
            
        var_node = hijos[0]
        nombre = getattr(var_node, "valor", None) or self._recorrer(var_node)
        
        if nombre is None:
            return None
            
        self.emitir("READ", "-", "-", nombre)
        return None

    def _cout(self, nodo):
        """Genera código para salida (cout/write)."""
        hijos = getattr(nodo, "hijos", []) or []
        if not hijos:
            return None
            
        salida = self._recorrer(hijos[0])
        
        if salida is None:
            salida = getattr(hijos[0], "valor", None)
            if salida is None:
                return None
            salida = str(salida)
            
        self.emitir("WRITE", salida, "-", "-")
        return None