# generador_codigo_intermedio.py
# Generador de Código Intermedio (TAC - Cuádruplas)
# Compatible con tu NodoAST / NodoAnotado

class CodigoIntermedioGenerator:

    def __init__(self):
        self.temp_count = 0
        self.code = []   # lista de cuádruplas (op, arg1, arg2, res)
        self.label_count = 0

    # -------- UTILIDADES -------- #

    def nuevo_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def nueva_etiqueta(self, pref="L"):
        self.label_count += 1
        return f"{pref}{self.label_count}"

    def emitir(self, op, a1="-", a2="-", res="-"):
        """Agrega una cuádrupla al código."""
        self.code.append((op, a1, a2, res))

    # -------- FUNCIÓN PRINCIPAL -------- #

    def generar(self, nodo_raiz):
        """Genera y retorna la lista de strings con las cuádruplas."""
        self.temp_count = 0
        self.label_count = 0
        self.code = []
        self._recorrer(nodo_raiz)
        return [f"({op}, {a1}, {a2}, {res})" for (op, a1, a2, res) in self.code]

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

        # manejar envoltorios comunes (no generan código directo)
        if tipo in ("lista_sentencias", "bloque", "bloque_if", "bloque_else", "bloque_do", "bloque_while"):
            for h in hijos:
                self._recorrer(h)
            return None

        # nodos estructurales
        if tipo == "programa":
            # asumo que primer hijo es main u equivalente
            if hijos:
                return self._recorrer(hijos[0])
            return None

        if tipo == "main":
            for h in hijos:
                self._recorrer(h)
            return None

        if tipo == "condicion":
            # condicion envuelve la expresion rel_op/log_op/... -> delegar
            return self._recorrer(hijos[0]) if hijos else None

        if tipo == "declaracion_variable":
            # no generamos TAC para declaración simple
            return None

        # sentencias
        if tipo == "asignacion":
            return self._asignacion(nodo)

        if tipo in ("post_inc", "post_increment", "post_dec", "post_decrement", "incremento", "decremento"):
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

        # expresiones
        if tipo in ("suma_op", "SUMA", "suma", "expresion_simple"):
            return self._suma(nodo)

        if tipo in ("mult_op", "MULT", "mult"):
            return self._mult(nodo)

        if tipo in ("rel_op", "REL", "relacional"):
            return self._rel(nodo)

        if tipo == "log_op":
            return self._log(nodo)

        if tipo in ("numero", "NUM", "FLOAT"):
            # retorno literal en string tal cual
            return str(valor)

        if tipo in ("id", "ID", "identificador"):
            return str(valor)

        # por defecto, intentar recorrer hijos (evita perder subárboles)
        for h in hijos:
            res = self._recorrer(h)
            # si obtenemos un temporal/literal útil, retornarlo
            if isinstance(res, str):
                return res

        return None

    # ============================================================
    #               GENERADORES PARA EXPRESIONES / SENTENCIAS
    # ============================================================

    def _asignacion(self, nodo):
        """Genera código para una asignación. Nodo.valor = nombre var, hijo[0] = expr."""
        nombre_var = getattr(nodo, "valor", None)
        expr = nodo.hijos[0] if nodo.hijos else None

        val = self._recorrer(expr)

        # si no hay expresión válida, no generar asignación basura
        if val is None:
            # puede ser un caso de post-inc/dec transformado previamente; simplemente ignorar
            return None

        # si la val es el mismo nombre (p.e. 'a') y no procede de una expresión, evitar (a = a)
        if isinstance(val, str) and val == nombre_var:
            return nombre_var

        # emitir asignación
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

        # generar temporal previo
        tmp = self.nuevo_temp()
        self.emitir("=", nombre, "-", tmp)
        # actualizar variable
        if nodo.tipo in ("post_dec", "post_decrement", "decremento", "c--", "dec"):
            self.emitir("-", nombre, "1", nombre)
        else:
            # post_inc cases
            self.emitir("+", nombre, "1", nombre)
        return tmp

    def _suma(self, nodo):
        """Suma / resta binaria. nodo.valor contiene '+' o '-' generalmente."""
        op = getattr(nodo, "valor", "+")
        left = nodo.hijos[0] if len(nodo.hijos) > 0 else None
        right = nodo.hijos[1] if len(nodo.hijos) > 1 else None

        l = self._recorrer(left)
        r = self._recorrer(right)

        # intentos fallback: si alguno es None pero el nodo hijo contiene valor literal o id
        if l is None and left is not None:
            l = getattr(left, "valor", None)
            if l is not None:
                l = str(l)
        if r is None and right is not None:
            r = getattr(right, "valor", None)
            if r is not None:
                r = str(r)

        # si aún falta un operando, no generar la operación
        if l is None or r is None:
            return None

        t = self.nuevo_temp()
        self.emitir(op, l, r, t)
        return t

    def _mult(self, nodo):
        """Multiplicación / división binaria."""
        op = getattr(nodo, "valor", "*")
        left = nodo.hijos[0] if len(nodo.hijos) > 0 else None
        right = nodo.hijos[1] if len(nodo.hijos) > 1 else None

        l = self._recorrer(left)
        r = self._recorrer(right)

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

    def _rel(self, nodo):
        """Relacionales: >, <, ==, etc."""
        op = getattr(nodo, "valor", "==")
        left = nodo.hijos[0] if len(nodo.hijos) > 0 else None
        right = nodo.hijos[1] if len(nodo.hijos) > 1 else None

        l = self._recorrer(left)
        r = self._recorrer(right)

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

    def _log(self, nodo):
        """Operadores lógicos simples (&&, ||)."""
        op = getattr(nodo, "valor", "&&")
        left = nodo.hijos[0] if len(nodo.hijos) > 0 else None
        right = nodo.hijos[1] if len(nodo.hijos) > 1 else None

        l = self._recorrer(left)
        r = self._recorrer(right)

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
        # si no hay condición válida, no generar control
        if t_cond is None:
            # recorrer bloques para no perder código interno (aunque cond inválida)
            if bloque_if:
                self._recorrer(bloque_if)
            if bloque_else:
                self._recorrer(bloque_else)
            return None

        L_else = self.nueva_etiqueta("Lf")
        L_fin = self.nueva_etiqueta("Le")

        self.emitir("ifFalse", t_cond, "-", L_else)

        if bloque_if:
            self._recorrer(bloque_if)

        self.emitir("goto", "-", "-", L_fin)
        self.emitir("label", "-", "-", L_else)

        if bloque_else:
            self._recorrer(bloque_else)

        self.emitir("label", "-", "-", L_fin)
        return None

    # ============================================================
    #                 WHILE
    # ============================================================

    def _while(self, nodo):
        hijos = getattr(nodo, "hijos", []) or []
        cond_node = hijos[0] if len(hijos) > 0 else None
        bloque = hijos[1] if len(hijos) > 1 else None

        L_inicio = self.nueva_etiqueta("Ls")
        L_fin = self.nueva_etiqueta("Le")

        self.emitir("label", "-", "-", L_inicio)

        t_cond = self._recorrer(cond_node)
        if t_cond is None:
            # si condicion inválida, no hacer loop infinito; recorrer cuerpo y salir
            if bloque:
                self._recorrer(bloque)
            self.emitir("label", "-", "-", L_fin)
            return None

        self.emitir("ifFalse", t_cond, "-", L_fin)
        if bloque:
            self._recorrer(bloque)
        self.emitir("goto", "-", "-", L_inicio)
        self.emitir("label", "-", "-", L_fin)
        return None

    # ============================================================
    #                 DO – UNTIL
    # ============================================================

    def _do_until(self, nodo):
        hijos = getattr(nodo, "hijos", []) or []
        bloque_do = hijos[0] if len(hijos) > 0 else None
        cond_node = hijos[1] if len(hijos) > 1 else None

        L_ini = self.nueva_etiqueta("Ld")
        L_fin = self.nueva_etiqueta("Le")

        self.emitir("label", "-", "-", L_ini)
        if bloque_do:
            self._recorrer(bloque_do)

        t_cond = self._recorrer(cond_node)
        if t_cond is None:
            # si no hay condición, cerramos la etiqueta y salimos
            self.emitir("label", "-", "-", L_fin)
            return None

        # do ... until: repetir mientras NO se cumpla -> ifFalse cond goto inicio
        self.emitir("ifFalse", t_cond, "-", L_ini)
        self.emitir("label", "-", "-", L_fin)
        return None

    # ============================================================
    #             CIN / COUT
    # ============================================================

    def _cin(self, nodo):
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
