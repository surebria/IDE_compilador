class CodigoIntermedioGenerator:

    def __init__(self):
        self.temp_count = 0
        self.code = []   # lista de cuádruplas
        self.label_count = 0

    # -------- UTILIDADES -------- #

    def nuevo_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def nueva_etiqueta(self):
        self.label_count += 1
        return f"L{self.label_count}"

    # -------- FUNCIÓN PRINCIPAL -------- #

    def generar(self, nodo_raiz):
        self.code = []
        self._recorrer(nodo_raiz)
        return [f"({op}, {a1}, {a2}, {res})" for (op, a1, a2, res) in self.code]

    # ============================================================
    #                    VISITOR GENERAL
    # ============================================================

    def _recorrer(self, nodo):
        if nodo is None:
            return None
        
        tipo = nodo.tipo
        valor = nodo.valor
        hijos = nodo.hijos

        # DEBUG opcional
        # print("VISIT:", tipo, valor)

        # --------- DISPATCHER ---------

        if tipo == "programa":
            return self._recorrer(hijos[0])  # main

        if tipo == "main":
            for h in hijos:
                self._recorrer(h)
            return
        
        if tipo == "condicion":
            return self._recorrer(hijos[0])

        if tipo == "declaracion_variable":
            return  # no genera código

        if tipo == "asignacion":
            return self._asignacion(nodo)

        if tipo == "suma_op":
            return self._suma(nodo)

        if tipo == "mult_op":
            return self._mult(nodo)

        if tipo == "rel_op":
            return self._rel(nodo)

        if tipo == "log_op":
            return self._log(nodo)

        if tipo == "expresion_simple":
            return self._recorrer(hijos[0])

        if tipo == "numero":
            return valor

        if tipo == "id":
            return valor

        if tipo == "seleccion":
            return self._if_else(nodo)

        if tipo == "repeticion":
            return self._do_until(nodo)

        if tipo == "iteracion":
            return self._while(nodo)

        if tipo == "sent_in":
            return self._cin(nodo)

        if tipo == "sent_out":
            return self._cout(nodo)

        if tipo == "lista_sentencias":
            for h in hijos:
                self._recorrer(h)
            return

        return None

    # ============================================================
    #               GENERADORES PARA EXPRESIONES
    # ============================================================

    def _asignacion(self, nodo):
        nombre_var = nodo.valor     # ejemplo: x
        expr = nodo.hijos[0]

        val = self._recorrer(expr)

        # asignación final
        self.code.append(("=", val, "-", nombre_var))
        return nombre_var

    def _suma(self, nodo):
        izq = self._recorrer(nodo.hijos[0])
        der = self._recorrer(nodo.hijos[1])
        t = self.nuevo_temp()
        self.code.append(("+", izq, der, t))
        return t

    def _mult(self, nodo):
        izq = self._recorrer(nodo.hijos[0])
        der = self._recorrer(nodo.hijos[1])
        t = self.nuevo_temp()
        self.code.append(("*", izq, der, t))
        return t

    def _rel(self, nodo):
        op = nodo.valor
        izq = self._recorrer(nodo.hijos[0])
        der = self._recorrer(nodo.hijos[1])
        t = self.nuevo_temp()
        self.code.append((op, izq, der, t))
        return t

    def _log(self, nodo):
        op = nodo.valor   # &&, ||
        izq = self._recorrer(nodo.hijos[0])
        der = self._recorrer(nodo.hijos[1])
        t = self.nuevo_temp()
        self.code.append((op, izq, der, t))
        return t

    # ============================================================
    #                 IF / ELSE
    # ============================================================

    def _if_else(self, nodo):
        cond = nodo.hijos[0]
        bloque_if = nodo.hijos[1]
        bloque_else = nodo.hijos[2]

        # condición
        t_cond = self._recorrer(cond)

        L_else = self.nueva_etiqueta()
        L_fin = self.nueva_etiqueta()

        # salto si no cumple
        self.code.append(("ifFalse", t_cond, "-", L_else))

        # bloque if
        self._recorrer(bloque_if)

        # saltar el else
        self.code.append(("goto", "-", "-", L_fin))

        # etiqueta else
        self.code.append(("label", "-", "-", L_else))
        self._recorrer(bloque_else)

        # fin
        self.code.append(("label", "-", "-", L_fin))

    # ============================================================
    #                 WHILE
    # ============================================================

    def _while(self, nodo):
        cond = nodo.hijos[0]
        bloque = nodo.hijos[1]

        L_inicio = self.nueva_etiqueta()
        L_fin = self.nueva_etiqueta()

        self.code.append(("label", "-", "-", L_inicio))

        t_cond = self._recorrer(cond)

        self.code.append(("ifFalse", t_cond, "-", L_fin))

        self._recorrer(bloque)

        self.code.append(("goto", "-", "-", L_inicio))
        self.code.append(("label", "-", "-", L_fin))

    # ============================================================
    #                 DO – UNTIL
    # ============================================================

    def _do_until(self, nodo):
        bloque_do = nodo.hijos[0]
        cond = nodo.hijos[1]

        L_ini = self.nueva_etiqueta()
        self.code.append(("label", "-", "-", L_ini))

        self._recorrer(bloque_do)

        t_cond = self._recorrer(cond)

        # repetir mientras NO se cumpla
        self.code.append(("ifFalse", t_cond, "-", L_ini))

    # ============================================================
    #             CIN / COUT
    # ============================================================

    def _cin(self, nodo):
        var = nodo.hijos[0].valor
        self.code.append(("cin", "-", "-", var))

    def _cout(self, nodo):
        expr = self._recorrer(nodo.hijos[0])
        self.code.append(("cout", expr, "-", "-"))
