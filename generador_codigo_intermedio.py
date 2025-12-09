"""
generador_codigo_intermedio.py

Generador de Código Intermedio (TAC - Cuádruplas)
Compatible con el AST/NodoAnotado que usas en tu analizador semántico.

"""

class CodigoIntermedioGenerator:
    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0
        self.codigo = []  # lista de tuplas (op, arg1, arg2, res)

    # -----------------------
    # Helpers
    # -----------------------
    def nuevo_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def nueva_etiqueta(self, pref="L"):
        self.label_counter += 1
        return f"{pref}{self.label_counter}"

    def emitir(self, op, arg1="-", arg2="-", res="-"):
        """Agrega una cuádrupla al código."""
        self.codigo.append((op, arg1, arg2, res))

    # -----------------------
    # API pública
    # -----------------------
    def generar(self, nodo_raiz):
        """Punto de entrada. Limpia estado, recorre el AST y devuelve lista de strings TAC."""
        self.temp_counter = 0
        self.label_counter = 0
        self.codigo = []

        # Si el nodo raíz es 'programa' o similar, recorrer sus hijos
        if nodo_raiz is None:
            return []

        self._recorrer(nodo_raiz)
        # Formatear a strings legibles
        return [f"({op}, {a1}, {a2}, {res})" for op, a1, a2, res in self.codigo]

    # -----------------------
    # Recorrido principal
    # -----------------------
    def _recorrer(self, nodo):
        if nodo is None:
            return None

        tipo = getattr(nodo, "tipo", None)
        valor = getattr(nodo, "valor", None)
        hijos = getattr(nodo, "hijos", []) or []

        # ---------- Nodos estructurales ----------
        if tipo in ("programa",):
            # normalmente tiene children: main u otros
            for h in hijos:
                self._recorrer(h)
            return None

        if tipo in ("main",):
            for h in hijos:
                self._recorrer(h)
            return None

        if tipo in ("lista_sentencias", "BLOQUE", "bloque_if", "bloque_else", "bloque_do", "bloque_while"):
            for h in hijos:
                self._recorrer(h)
            return None

        if tipo in ("declaracion_variable",):
            # estructura: tipo, lista identificadores
            # No generamos cuádruplas por la declaración en sí (puedes agregar inicializaciones si quieres)
            # Recorrer hijos por si hay initializers (dependiendo de tu AST)
            for h in hijos:
                self._recorrer(h)
            return None

        # ---------- Asignación ----------
        # Observé tu AST: asignacion: <id>  (child(0) = id node), child(1) = expr node (a veces directo numero)
        if tipo in ("asignacion", "ASIGNACION"):
            # primer hijo suele ser el id, el siguiente la expresión
            if len(hijos) == 0:
                return None
            id_nodo = hijos[0]
            expr_nodo = hijos[1] if len(hijos) > 1 else None

            destino = getattr(id_nodo, "valor", None) or self._recorrer(id_nodo)
            fuente = self._recorrer(expr_nodo) if expr_nodo is not None else None

            # si la expresión devolvió None es posible que fuera literal manejado en _recorrer
            if fuente is None:
                fuente = getattr(expr_nodo, "valor", None) or "-"

            # emitir asignación
            self.emitir("=", fuente, "-", destino)
            return destino

        # ---------- Literales y IDs ----------
        if tipo in ("numero", "NUM", "FLOAT"):
            # devolver literal como string (se usa directamente)
            return str(valor)

        if tipo in ("id", "ID", "identificador"):
            return str(valor)

        # ---------- Expresiones binarias ----------
        # suma_op, mult_op, expresion_simple, suma_op anidada, mult_op anidada
        if tipo in ("suma_op", "SUMA", "suma", "expresion_simple"):
            # operador puede estar en nodo.valor, si no, intentar inferir por hijos
            op_sym = valor if valor in ("+", "-") else "+"
            left = self._recorrer(hijos[0]) if len(hijos) > 0 else None
            right = self._recorrer(hijos[1]) if len(hijos) > 1 else None

            # si left/right son nodos literales/devueltos como None, extraer valor
            left = left if left is not None else (getattr(hijos[0], "valor", None) if len(hijos) > 0 else None)
            right = right if right is not None else (getattr(hijos[1], "valor", None) if len(hijos) > 1 else None)

            tmp = self.nuevo_temp()
            self.emitir(op_sym, left, right, tmp)
            return tmp

        if tipo in ("mult_op", "MULT", "mult"):
            op_sym = valor if valor in ("*", "/") else "*"
            left = self._recorrer(hijos[0]) if len(hijos) > 0 else None
            right = self._recorrer(hijos[1]) if len(hijos) > 1 else None
            left = left if left is not None else (getattr(hijos[0], "valor", None) if len(hijos) > 0 else None)
            right = right if right is not None else (getattr(hijos[1], "valor", None) if len(hijos) > 1 else None)
            tmp = self.nuevo_temp()
            self.emitir(op_sym, left, right, tmp)
            return tmp

        # relacionales: >, <, >=, <=, ==, !=
        if tipo in ("rel_op", "REL", "relacional"):
            op_sym = valor if valor in (">", "<", ">=", "<=", "==", "!=") else "=="
            left = self._recorrer(hijos[0]) if len(hijos) > 0 else None
            right = self._recorrer(hijos[1]) if len(hijos) > 1 else None
            left = left if left is not None else (getattr(hijos[0], "valor", None) if len(hijos) > 0 else None)
            right = right if right is not None else (getattr(hijos[1], "valor", None) if len(hijos) > 1 else None)
            tmp = self.nuevo_temp()
            self.emitir(op_sym, left, right, tmp)
            return tmp

        # log_op (&&, ||, !). Implementación simple: generar resultado booleano en temp.
        if tipo in ("log_op",):
            op_sym = valor if valor in ("&&", "||", "!") else "&&"
            if op_sym == "!":
                operand = self._recorrer(hijos[0])
                tmp = self.nuevo_temp()
                self.emitir("NOT", operand, "-", tmp)
                return tmp
            else:
                left = self._recorrer(hijos[0])
                right = self._recorrer(hijos[1])
                tmp = self.nuevo_temp()
                self.emitir(op_sym, left, right, tmp)
                return tmp

        # ---------- Selección IF / IF-ELSE ----------
        # Tu AST usa 'seleccion' con hijos: condicion, bloque_if, (opcional) bloque_else
        if tipo in ("seleccion", "if", "SELECCION"):
            # condicion produce un temp booleano (o literal)
            condicion_nodo = hijos[0] if len(hijos) > 0 else None
            bloque_if = hijos[1] if len(hijos) > 1 else None
            bloque_else = hijos[2] if len(hijos) > 2 else None

            cond_temp = self._recorrer(condicion_nodo)
            # si condicion devolvió literal, usarlo tal cual
            cond_temp = cond_temp if cond_temp is not None else getattr(condicion_nodo, "valor", None)

            label_false = self.nueva_etiqueta("Lf")
            label_end = self.nueva_etiqueta("Le")

            # Si condición es un temp booleano, hacer IF_FALSE cond -> label_false
            self.emitir("IF_FALSE", cond_temp, "-", label_false)

            # cuerpo verdadero
            self._recorrer(bloque_if)

            # salto al final
            self.emitir("GOTO", "-", "-", label_end)

            # etiqueta falso
            self.emitir("LABEL", "-", "-", label_false)

            # else
            if bloque_else:
                self._recorrer(bloque_else)

            # etiqueta final
            self.emitir("LABEL", "-", "-", label_end)
            return None

        # ---------- Iteración: while ----------
        # nodo tipo 'iteracion' o 'while' con hijos: condicion, bloque_while
        if tipo in ("iteracion", "while", "WHILE"):
            condicion_nodo = hijos[0] if len(hijos) > 0 else None
            bloque = hijos[1] if len(hijos) > 1 else None

            label_start = self.nueva_etiqueta("Ls")
            label_end = self.nueva_etiqueta("Le")

            self.emitir("LABEL", "-", "-", label_start)
            cond_temp = self._recorrer(condicion_nodo)
            cond_temp = cond_temp if cond_temp is not None else getattr(condicion_nodo, "valor", None)
            self.emitir("IF_FALSE", cond_temp, "-", label_end)

            # cuerpo
            self._recorrer(bloque)

            # goto inicio
            self.emitir("GOTO", "-", "-", label_start)
            self.emitir("LABEL", "-", "-", label_end)
            return None

        # ---------- Repetición do ... until (tu 'repeticion: do') ----------
        # en tu AST: repeticion -> bloque_do, condicion: until
        if tipo in ("repeticion", "do", "DO"):
            # asumo hijos: bloque_do, condicion
            bloque_do = None
            condicion_nodo = None
            # detectar por tipo de hijos
            if len(hijos) >= 1:
                bloque_do = hijos[0]
            if len(hijos) >= 2:
                condicion_nodo = hijos[1]
            # implementamos do { ... } while(cond) equivalencia do-until
            label_start = self.nueva_etiqueta("Ld")
            label_end = self.nueva_etiqueta("Le")

            self.emitir("LABEL", "-", "-", label_start)
            if bloque_do:
                self._recorrer(bloque_do)
            # condicion es del tipo 'condicion' con operador 'until' -> queremos repetir mientras !condicion
            if condicion_nodo:
                cond_temp = self._recorrer(condicion_nodo)
                cond_temp = cond_temp if cond_temp is not None else getattr(condicion_nodo, "valor", None)
                # repetir si condición es false -> if_false goto start
                self.emitir("IF_FALSE", cond_temp, "-", label_start)
            self.emitir("LABEL", "-", "-", label_end)
            return None

        # ---------- Entrada / Salida ----------
        if tipo in ("sent_in", "cin", "INPUT"):
            # hijo esperado: id node
            if len(hijos) > 0:
                idn = hijos[0]
                nombre = getattr(idn, "valor", None) or self._recorrer(idn)
                self.emitir("READ", "-", "-", nombre)
            return None

        if tipo in ("sent_out", "cout", "OUTPUT"):
            # hijo esperado: salida (puede ser id o expr)
            if len(hijos) > 0:
                salida = self._recorrer(hijos[0])
                salida = salida if salida is not None else getattr(hijos[0], "valor", None)
                self.emitir("WRITE", salida, "-", "-")
            return None

        # ---------- Default: si no se reconoce el nodo, intentar recorrer hijos ----------
        # (esto evita perder subárboles)
        handled = False
        for h in hijos:
            self._recorrer(h)
            handled = True

        if not handled:
            # advertencia ligera para debug
            # print(f"[WARN IR] Nodo no manejado: {tipo}")
            pass

        return None
