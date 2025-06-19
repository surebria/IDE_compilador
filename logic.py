from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression 
from PyQt6.QtCore import QRegularExpression as QtRegex
import re
import os


class HighlightSyntax(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        # Números enteros y reales
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor("#9c7692"))
        numberPattern = QRegularExpression(r"\b\d+(\.\d+)?(?=\D|\b)")
        self.highlightingRules.append((numberPattern, numberFormat))

        # Identificadores (letras y dígitos que no empiezan por dígito o _)
        identifierFormat = QTextCharFormat()
        identifierFormat.setForeground(QColor("#da9f40"))
        identifierPattern = QRegularExpression(r"[a-zA-Z][a-zA-Z0-9_]*")
        self.highlightingRules.append((identifierPattern, identifierFormat))

        # Palabras Reservadas
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#7e8def"))
        keywords = ["if", "else", "end", "do", "while", "for", "switch", "case", "break", 
                    "int", "float", "string", "main", "cin", "cout", "def", "class", 
                    "import", "from", "return", "then", "until", "real"]

        for word in keywords: 
            pattern = QRegularExpression(r"\b" + word + r"\b")
            self.highlightingRules.append((pattern, keywordFormat))

        #Operadores aritméticos
        arithmeticFormat= QTextCharFormat()
        arithmeticFormat.setForeground(QColor("#70a483"))
        arithmeticPattern = QRegularExpression(r"(\+\+|\-\-|\+|\-|\*|\/|\%|\^)")
        self.highlightingRules.append((arithmeticPattern, arithmeticFormat))

        #Simbolo de igual
        self.highlightingRules.append((QRegularExpression(r"=(?!=)"), QColor("#065710")))

        #Operadores relacionales
        relationalFormat = QTextCharFormat()
        relationalFormat.setForeground(QColor("#bb776f"))
        relationalPattern = QRegularExpression(r"(<=|>=|==|!=|<|>|\|\||&&|!(?!=))")
        self.highlightingRules.append((relationalPattern, relationalFormat))

        #Simbolos
        self.highlightingRules.append((QRegularExpression(r"[\(\)\{\},;.]"), QColor("#0d6b4a")))

         # Formato para comentarios de una línea (// ...)
        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(QColor("#a2a9a5"))
        self.highlightingRules.append((QRegularExpression(r'//[^\n]*'), singleLineCommentFormat))
        
        # Define format for multiline comments
        self.multiLineCommentFormat = QTextCharFormat()
        self.multiLineCommentFormat.setForeground(QColor("#a2a9a5"))
        
        # Compile regular expressions
        self.multiLineCommentStartExpression = QtRegex(r'/\*')
        self.multiLineCommentEndExpression = QtRegex(r'\*/')
        
    # highlightBlock override
    def highlightBlock(self, text):
        # Apply single-line highlighting rules
        for pattern, format in self.highlightingRules:
            expression = QtRegex(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        
        # Handle multiline comments
        self.setCurrentBlockState(0)
        
        startIndex = 0
        if self.previousBlockState() != 1:
            startMatch = self.multiLineCommentStartExpression.match(text)
            if startMatch.hasMatch():
                startIndex = startMatch.capturedStart()
            else:
                startIndex = -1
        
        while startIndex >= 0:
            endMatch = self.multiLineCommentEndExpression.match(text, startIndex)
            if endMatch.hasMatch():
                endIndex = endMatch.capturedEnd()
                commentLength = endIndex - startIndex
                self.setFormat(startIndex, commentLength, self.multiLineCommentFormat)
                
                # Busca el siguiente comentario multilinea
                nextStartMatch = self.multiLineCommentStartExpression.match(text, endIndex)
                startIndex = nextStartMatch.capturedStart() if nextStartMatch.hasMatch() else -1
            else:
                self.setFormat(startIndex, len(text) - startIndex, self.multiLineCommentFormat)
                self.setCurrentBlockState(1)
                startIndex = -1

class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"Token({self.tipo}, '{self.valor}', L{self.linea}:C{self.columna})"
    
    def __repr__(self):
        if self.tipo == 'ERROR':
            return f"{self.tipo}('{self.valor}') en línea {self.linea}, columna {self.columna}"
        else:
            return f"{self.tipo}('{self.valor}')"

def analizador_lexico(texto):
    tokens = []
    i = 0
    linea = 1
    columna = 1
    longitud = len(texto)

    def avanzar():
        nonlocal i, columna
        i += 1
        columna += 1

    while i < longitud:
        char = texto[i]

        if char in ' \t':
            avanzar()
            continue

        if char == '\n':
            linea += 1
            columna = 1
            i += 1
            continue

        inicio_col = columna

        # Comentario de una línea
        if char == '/' and i + 1 < longitud and texto[i + 1] == '/':
            i += 2
            columna += 2
            while i < longitud and texto[i] != '\n':
                i += 1
                columna += 1
            continue

        # Comentario de múltiples líneas
        if char == '/' and i + 1 < longitud and texto[i + 1] == '*':
            i += 2
            columna += 2
            cerrado = False
            while i < longitud:
                if texto[i] == '*' and i + 1 < longitud and texto[i + 1] == '/':
                    i += 2
                    columna += 2
                    cerrado = True
                    break
                if texto[i] == '\n':
                    linea += 1
                    columna = 1
                    i += 1
                else:
                    i += 1
                    columna += 1
            # if not cerrado:
            #     tokens.append(Token('ERROR', 'Comentario no cerrado', linea, columna))
            continue

        # Identificadores
        if char.isalpha():
            inicio = i
            while i < longitud and (texto[i].isalnum() or texto[i] == '_'):
                avanzar()
            valor = texto[inicio:i]
            
            keywords = ["if", "else", "end", "do", "while", "for", "switch", "case", "break", "int", "float", "string", "main", "cin", "cout", "def", "class", "import", "from", "return",]
            
            if valor in keywords: 
                tokens.append(Token('PALABRA_RESERVADA', valor, linea, inicio_col))
            else:
                tokens.append(Token('IDENTIFICADOR', valor, linea, inicio_col))
            continue    

        if texto[i] in ['+', '-', '*', '/', '%', '^']:
            inicio_col = columna
            actual = texto[i]

            # Verificar si es '++' o '--' (operadores dobles)
            if i + 1 < longitud and texto[i + 1] == actual and actual in ['+', '-']:
                tokens.append(Token('OPERADOR_ARITMETICO', texto[i] + texto[i + 1], linea, columna))
                avanzar()  # avanzar por el primer carácter
                avanzar()  # avanzar por el segundo carácter
                columna += 2
            else:
                # Operador aritmético simple
                tokens.append(Token('OPERADOR_ARITMETICO', texto[i], linea, columna))
                avanzar()
                columna += 1
            continue


        if texto[i].isdigit():
            inicio_col = columna
            inicio = i
            
            while i < longitud and texto[i].isdigit():
                avanzar()
            
            if i < longitud and texto[i] == '.':
                avanzar()
                
                if i < longitud and texto[i].isdigit():
                    while i < longitud and texto[i].isdigit():
                        avanzar()
                    valor = texto[inicio:i]
                    tokens.append(Token('NUMERO_REAL', valor, linea, inicio_col))
                else:
                    tokens.append(Token('ERROR', texto[inicio:i], linea, inicio_col))
            else:
                valor = texto[inicio:i]
                tokens.append(Token('NUMERO_ENTERO', valor, linea, inicio_col))
            continue


        # Operadores Relacionales (<, >, <=, >=, !=, ==)
        if texto[i] in ['<', '>', '!', '=']:
            inicio_col = columna
            actual = texto[i]
            avanzar()

            # Si es <=, >=, !=, ==
            if i < longitud and texto[i] == '=' and actual in ['<', '>', '!', '=']:
                operador = actual + texto[i]
                avanzar()
                tokens.append(Token('OPERADOR_RELACIONAL', operador, linea, inicio_col))
            else:
                if actual == '=':
                    tokens.append(Token('OPERADOR_ASIGNACION', actual, linea, inicio_col))
                else:
                    tokens.append(Token('OPERADOR_RELACIONAL', actual, linea, inicio_col))
            continue

       # Operadores Lógicos (&&, ||)
        if texto[i] == '&':
            inicio_col = columna
            avanzar()
            count = 1
            while i < longitud and texto[i] == '&':
                count += 1
                avanzar()

            if count >= 2:
                for _ in range(count // 2):
                    tokens.append(Token('OPERADOR_LOGICO', '&&', linea, inicio_col))
               
                if count % 2 != 0:
                    tokens.append(Token('ESPECIAL', '&', linea, inicio_col))
            continue

        if texto[i] == '|':
            inicio_col = columna
            avanzar()

            count = 1
            while i < longitud and texto[i] == '|':
                count += 1
                avanzar()

            if count >= 2:
                for _ in range(count // 2):
                    tokens.append(Token('OPERADOR_LOGICO', '||', linea, inicio_col))
                if count % 2 != 0:
                    tokens.append(Token('ESPECIAL', '|', linea, inicio_col))
            continue

        # Caracteres especiales
        if texto[i] in ['(', ')', '{', '}', '[', ']', ';', ',', ':', '%', '&', '|', '°', "'", '"']:
            tokens.append(Token('ESPECIAL', texto[i], linea, inicio_col))
            avanzar()
            continue

        # Error: carácter no reconocido
        tokens.append(Token('ERROR', char, linea, columna))
        avanzar()
        

    return tokens

########################################A PARTIR DE ESTO ES LO NUEVO QUE SE AGREGO#######################

class NodoAST:
    """Clase base para todos los nodos del AST"""
    def __init__(self, tipo, valor=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = []
        self.linea = None
        self.columna = None
    
    def agregar_hijo(self, hijo):
        if hijo is not None:
            self.hijos.append(hijo)
    
    def __repr__(self):
        return f"{self.tipo}({self.valor})"

class ErrorSintactico:
    def __init__(self, mensaje, linea, columna):
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
    
    def __str__(self):
        return f"Error Sintáctico: {self.mensaje} en línea {self.linea}, columna {self.columna}"

class AnalizadorSintactico:
    """Analizador sintáctico descendente recursivo con mejor manejo de errores"""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.errores = []
        self.ast = None
        self.en_modo_panico = False
        # Tokens de sincronización definidos en __init__
        self.tokens_sync_declaracion = [';', 'int', 'float', 'bool', '}']
        self.tokens_sync_sentencia = [';', 'if', 'while', 'do', 'cin', 'cout', '}']
    
    def token_actual(self):
        """Retorna el token actual o None si se acabaron los tokens"""
        if self.posicion < len(self.tokens):
            return self.tokens[self.posicion]
        return None
    
    def token_siguiente(self):
        """Retorna el siguiente token sin avanzar"""
        if self.posicion + 1 < len(self.tokens):
            return self.tokens[self.posicion + 1]
        return None
    
    def avanzar(self):
        """Avanza al siguiente token"""
        if self.posicion < len(self.tokens):
            self.posicion += 1
    
    def obtener_token_anterior(self):
        """Obtiene el token anterior si existe"""
        if self.posicion > 0:
            return self.tokens[self.posicion - 1]
        return None
    
    def coincidir(self, tipo_o_valor):
        """Verifica si el token actual coincide con el tipo o valor esperado"""
        token = self.token_actual()
        if token is None:
            return False
        
        # Verificar por tipo
        if token.tipo == tipo_o_valor:
            return True
        
        # Verificar por valor para palabras reservadas y símbolos
        if token.valor == tipo_o_valor:
            return True
        
        return False
    
    def consumir(self, tipo_o_valor, mensaje_error=None):
        """
        Consume un token si coincide, sino genera error
        """
        token = self.token_actual()
        
        if token is None:
            if mensaje_error:
                self.agregar_error(mensaje_error, self.obtener_ultima_posicion_valida())
            else:
                self.agregar_error(
                    f"Se esperaba '{tipo_o_valor}' pero se alcanzó el final del archivo",
                    self.obtener_ultima_posicion_valida()
                )
            return None
        
        if self.coincidir(tipo_o_valor):
            self.avanzar()
            return token
        else:
            if mensaje_error:
                self.agregar_error(mensaje_error, (token.linea, token.columna))
            else:
                self.agregar_error(
                    f"Se esperaba '{tipo_o_valor}' pero se encontró '{token.valor}' ({token.tipo})",
                    (token.linea, token.columna)
                )
            return None
    
    def agregar_error(self, mensaje, posicion):
        """Agrega un error a la lista de errores"""
        if isinstance(posicion, tuple):
            linea, columna = posicion
        else:
            linea, columna = posicion, 1
        
        error = ErrorSintactico(mensaje, linea, columna)
        self.errores.append(error)
        print(f"Error agregado: {error}")
    
    def obtener_ultima_posicion_valida(self):
        """Obtiene la última posición válida conocida"""
        if self.posicion > 0:
            token_anterior = self.tokens[self.posicion - 1]
            return (token_anterior.linea, token_anterior.columna + len(str(token_anterior.valor)))
        return (1, 1)
    
    def sincronizar_hasta(self, tokens_objetivo):
        """Sincroniza hasta encontrar uno de los tokens objetivo"""
        print(f"Sincronizando hasta encontrar: {tokens_objetivo}")
        posicion_inicial = self.posicion
        
        while self.token_actual():
            token = self.token_actual()
            
            # Verificar si encontramos un token objetivo
            for objetivo in tokens_objetivo:
                if self.coincidir(objetivo):
                    print(f"Sincronización completada en: {token}")
                    # Si es punto y coma, lo consumimos para evitar bucles
                    if objetivo == ';':
                        self.avanzar()
                    return
            
            print(f"Saltando token durante sincronización: {token}")
            self.avanzar()
            
            # Protección contra bucles infinitos
            if self.posicion - posicion_inicial > 50:
                print("Sincronización interrumpida: demasiados tokens saltados")
                break
        
        print("Sincronización completada: final de archivo")
    
    def sincronizar(self):
        """Función de sincronización para recuperación de errores"""
        self.en_modo_panico = True
        sincron_tokens = [';', '}', '{']
        sincron_palabras = ['int', 'float', 'bool', 'if', 'while', 'do', 'cout', 'cin', 'main']
        
        while self.token_actual() and self.en_modo_panico:
            t = self.token_actual()
            
            # Si encontramos un token de sincronización, detenernos
            if (t.tipo == 'ESPECIAL' and t.valor in sincron_tokens) or \
               (t.tipo == 'PALABRA_RESERVADA' and t.valor in sincron_palabras):
                self.en_modo_panico = False
                break
            
            self.avanzar()
    
    def programa(self):
        """programa → main { lista_declaracion }"""
        print("Analizando programa...")
        nodo = NodoAST("programa")
        
        # Esperar 'main'
        if not self.consumir('main', "Se esperaba 'main' al inicio del programa"):
            self.sincronizar_hasta(['{'])
        
        # Esperar '{'
        if not self.consumir('{', "Se esperaba '{' después de 'main'"):
            self.sincronizar_hasta(['int', 'float', 'bool', 'IDENTIFICADOR'])
        
        # Analizar lista de declaraciones
        lista_decl = self.lista_declaracion()
        if lista_decl:
            nodo.agregar_hijo(lista_decl)
        
        # Esperar '}'
        if not self.consumir('}', "Se esperaba '}' al final del programa"):
            pass  # Error ya reportado
        
        return nodo

    def lista_declaracion(self):
        """lista_declaracion → lista_declaracion declaracion | declaracion"""
        print("Analizando lista de declaraciones...")
        nodo = NodoAST("lista_declaracion")
        elementos_procesados = 0
        contador_intentos = 0
        
        while self.token_actual() and not self.coincidir('}'):
            token = self.token_actual()
            print(f"Procesando token: {token}")
            posicion_inicial = self.posicion
            contador_intentos += 1
            
            # Protección contra bucles infinitos
            if contador_intentos > 100:
                print("Demasiados intentos, saliendo del bucle")
                break
            
            declaracion_procesada = False
            
            # Intentar declaración de variable
            if self.coincidir('int') or self.coincidir('float') or self.coincidir('bool'):
                decl = self.declaracion_variable()
                if decl:
                    nodo.agregar_hijo(decl)
                    elementos_procesados += 1
                    declaracion_procesada = True
            
            # Intentar sentencias de control
            elif self.coincidir('if'):
                sent = self.seleccion()
                if sent:
                    nodo.agregar_hijo(sent)
                    elementos_procesados += 1
                    declaracion_procesada = True
            
            elif self.coincidir('while'):
                sent = self.iteracion()
                if sent:
                    nodo.agregar_hijo(sent)
                    elementos_procesados += 1
                    declaracion_procesada = True
            
            elif self.coincidir('do'):
                sent = self.repeticion()
                if sent:
                    nodo.agregar_hijo(sent)
                    elementos_procesados += 1
                    declaracion_procesada = True
            
            elif self.coincidir('cin'):
                sent = self.sent_in()
                if sent:
                    nodo.agregar_hijo(sent)
                    elementos_procesados += 1
                    declaracion_procesada = True
            
            elif self.coincidir('cout'):
                sent = self.sent_out()
                if sent:
                    nodo.agregar_hijo(sent)
                    elementos_procesados += 1
                    declaracion_procesada = True
            
            # Intentar asignación o incremento/decremento
            elif self.coincidir('IDENTIFICADOR'):
                siguiente = self.token_siguiente()
                if siguiente and (siguiente.valor == '++' or siguiente.valor == '--'):
                    sent = self.incremento_decremento()
                else:
                    sent = self.sentencia_asignacion()
                
                if sent:
                    nodo.agregar_hijo(sent)
                    elementos_procesados += 1
                    declaracion_procesada = True
            
            # Token problemático - punto y coma aislado u otros
            elif self.coincidir(';'):
                print("Encontrado punto y coma aislado, saltándolo")
                self.agregar_error(
                    f"Punto y coma inesperado (posiblemente parte de una declaración incompleta)",
                    (token.linea, token.columna)
                )
                self.avanzar()  # Consumir el punto y coma
                declaracion_procesada = True
            
            # Token no reconocido
            else:
                self.agregar_error(
                    f"Declaración o sentencia inválida. Token inesperado '{token.valor}' ({token.tipo})",
                    (token.linea, token.columna)
                )
                
                # Avanzar un token para evitar bucle infinito
                self.avanzar()
                declaracion_procesada = True
            
            # Verificar progreso para evitar bucles infinitos
            if self.posicion == posicion_inicial and not declaracion_procesada:
                print(f"Avanzando forzadamente desde token: {token}")
                self.avanzar()
        
        print(f"Lista de declaraciones procesada. Elementos: {elementos_procesados}")
        return nodo if nodo.hijos else None

    def declaracion_variable(self):
        """declaracion_variable → tipo identificador ;"""
        print("Analizando declaración de variable...")
        nodo = NodoAST("declaracion_variable")
        
        # Consumir tipo
        token_tipo = self.token_actual()
        if not self.coincidir('int') and not self.coincidir('float') and not self.coincidir('bool'):
            return None
        
        self.avanzar()  # Consumir el tipo
        nodo_tipo = NodoAST("tipo", token_tipo.valor)
        nodo.agregar_hijo(nodo_tipo)
        
        # Procesar lista de identificadores separados por comas
        while True:
            # Consumir identificador
            token_id = self.consumir('IDENTIFICADOR', 
                                    f"Se esperaba identificador después de '{token_tipo.valor}'")
            if token_id:
                nodo_id = NodoAST("identificador", token_id.valor)
                nodo.agregar_hijo(nodo_id)
            else:
                self.sincronizar_hasta([';'])
                break
            
            # Verificar si hay coma para continuar con más identificadores
            if self.coincidir(','):
                self.avanzar()  # Consumir la coma
                continue
            else:
                break  # No hay más identificadores
        
        # Consumir punto y coma
        if not self.consumir(';', "Se esperaba ';' después de la declaración"):
            self.sincronizar_hasta(self.tokens_sync_declaracion)
        
        return nodo
    
    def sentencia_asignacion(self):
        """asignacion → id = sent_expresion"""
        print("Analizando sentencia de asignación...")
        nodo = NodoAST("asignacion")
        
        # Consumir identificador
        token_id = self.consumir('IDENTIFICADOR')
        if token_id:
            nodo_id = NodoAST("identificador", token_id.valor)
            nodo.agregar_hijo(nodo_id)
        
        # Consumir '='
        if not self.consumir('=', "Se esperaba '=' después del identificador"):
            self.sincronizar_hasta([';'])
            return nodo
        
        # Consumir expresión
        expr = self.sent_expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        return nodo
    
    def sent_expresion(self):
        """sent_expresion → expresion ; | ;"""
        print("Analizando sentencia de expresión...")
        
        # Si encontramos directamente ';', es una expresión vacía
        if self.coincidir(';'):
            self.avanzar()
            return NodoAST("expresion_vacia")
        
        # Sino, debería haber una expresión seguida de ';'
        nodo = self.expresion()
        
        if not self.consumir(';', "Se esperaba ';' después de la expresión"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
        
        return nodo
    
    def expresion(self):
        """expresion → expresion_simple [ rel_op expresion_simple ]"""
        print("Analizando expresión...")
        
        expr_izq = self.expresion_simple()
        if not expr_izq:
            return None
        
        # Verificar si hay operador relacional
        if self.token_actual() and self.token_actual().tipo == 'OPERADOR_RELACIONAL':
            nodo = NodoAST("expresion_relacional")
            nodo.agregar_hijo(expr_izq)
            
            # Consumir operador relacional
            op_token = self.token_actual()
            self.avanzar()
            nodo_op = NodoAST("operador_relacional", op_token.valor)
            nodo.agregar_hijo(nodo_op)
            
            # Consumir segunda expresión simple
            expr_der = self.expresion_simple()
            if expr_der:
                nodo.agregar_hijo(expr_der)
            
            return nodo
        
        return expr_izq
    ####1
    def expresion_simple(self):
        """expresion_simple → expresion_simple suma_op termino | termino"""
        print("Analizando expresión simple...")
        
        termino_izq = self.termino()
        if not termino_izq:
            return None
        
        # Si solo hay un término, devolverlo directamente
        if not (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and 
                self.token_actual().valor in ['+', '-']):
            return termino_izq
        
        # Crear nodo para expresión con operadores
        nodo = NodoAST("expresion_simple")
        nodo.agregar_hijo(termino_izq)
        
        # Procesar operadores y términos adicionales
        while (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and 
            self.token_actual().valor in ['+', '-']):
            
            op_token = self.token_actual()
            self.avanzar()  # Consumir el operador
            
            # Crear nodo para el operador
            op_nodo = NodoAST("operador_suma", op_token.valor)
            nodo.agregar_hijo(op_nodo)
            
            # Procesar siguiente término
            termino_der = self.termino()
            if termino_der:
                nodo.agregar_hijo(termino_der)
            else:
                self.agregar_error(
                    f"Se esperaba un término después del operador '{op_token.valor}'",
                    (op_token.linea, op_token.columna)
                )
                break
        
        return nodo
    


    def termino(self):
        """termino → termino mult_op factor | factor"""
        print("Analizando término...")
        
        factor_izq = self.factor()
        if not factor_izq:
            return None
        
        # Si no hay operadores de multiplicación, devolver el factor directamente
        if not (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and 
                self.token_actual().valor in ['*', '/', '%']):
            return factor_izq
        
        # Crear nodo para término con operadores
        nodo = NodoAST("termino")
        nodo.agregar_hijo(factor_izq)
        
        # Procesar operadores y factores adicionales
        while (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and 
            self.token_actual().valor in ['*', '/', '%']):
            
            op_token = self.token_actual()
            self.avanzar()  # Consumir el operador
            
            # Crear nodo para el operador
            op_nodo = NodoAST("operador_mult", op_token.valor)
            nodo.agregar_hijo(op_nodo)
            
            # Procesar siguiente factor
            factor_der = self.factor()
            if factor_der:
                nodo.agregar_hijo(factor_der)
            else:
                self.agregar_error(
                    f"Se esperaba un factor después del operador '{op_token.valor}'",
                    (op_token.linea, op_token.columna)
                )
                break
        
        return nodo

    def factor(self):
        """factor → factor pot_op componente | componente"""
        print("Analizando factor...")
        return self.componente()  # Simplificado por ahora

    def componente(self):
        """componente → ( expresion ) | número | id | bool | op_logico componente"""
        print("Analizando componente...")
        token = self.token_actual()
        
        if not token:
            self.agregar_error("Se esperaba una expresión", self.obtener_ultima_posicion_valida())
            return None
        
        # Expresión entre paréntesis
        if self.coincidir('('):
            self.avanzar()  # Consumir '('
            expr = self.expresion()
            if not self.consumir(')', "Se esperaba ')' después de la expresión"):
                self.sincronizar_hasta([';'])
            return expr
        
        # Números, identificadores, booleanos
        if token.tipo in ['NUMERO_ENTERO', 'NUMERO_DECIMAL', 'IDENTIFICADOR']:
            nodo = NodoAST("componente", token.valor)
            nodo.linea = token.linea
            nodo.columna = token.columna
            self.avanzar()
            return nodo
        
        # Valores booleanos
        if token.valor in ['true', 'false']:
            nodo = NodoAST("booleano", token.valor)
            nodo.linea = token.linea
            nodo.columna = token.columna
            self.avanzar()
            return nodo
        
        self.agregar_error(
            f"Se esperaba número, identificador o expresión entre paréntesis, se encontró '{token.valor}' ({token.tipo})", 
            (token.linea, token.columna)
        )
        return None
    
    def sentencia(self):
        """Placeholder para otras sentencias"""
        token = self.token_actual()
        if token:
            self.avanzar()
            return NodoAST("sentencia", token.valor)
        return None
    
    
    def lista_sentencias(self):
        """lista_sentencias → lista_sentencias sentencia | ε"""
        print("Analizando lista de sentencias...")
        nodo = NodoAST("lista_sentencias")
        
        while (self.token_actual() and 
            not self.coincidir('}') and not self.coincidir('end') and 
            not self.coincidir('else') and not self.coincidir('until')):
            
            sent = None
            token = self.token_actual()
            
            if self.coincidir('if'):
                sent = self.seleccion()
            elif self.coincidir('while'):
                sent = self.iteracion()
            elif self.coincidir('do'):
                sent = self.repeticion()
            elif self.coincidir('cin'):
                sent = self.sent_in()
            elif self.coincidir('cout'):
                sent = self.sent_out()
            elif self.coincidir('IDENTIFICADOR'):
                # Verificar si es asignación o incremento/decremento
                siguiente = self.token_siguiente()
                if siguiente and (siguiente.valor == '++' or siguiente.valor == '--'):
                    sent = self.incremento_decremento()
                else:
                    sent = self.sentencia_asignacion()
            else:
                # Token no reconocido, salir del bucle
                break
            
            if sent:
                nodo.agregar_hijo(sent)
            else:
                # Si no se pudo procesar la sentencia, avanzar para evitar bucle infinito
                self.avanzar()
        
        return nodo if nodo.hijos else None

    def seleccion(self):
        """seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end"""
        print("Analizando selección (if)...")
        nodo = NodoAST("seleccion")
        
        # Consumir 'if'
        self.consumir('if')
        
        # Consumir expresión de condición
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        # Consumir 'then'
        if not self.consumir('then', "Se esperaba 'then' después de la condición"):
            self.sincronizar_hasta(['end', 'else'])
        
        # Consumir lista de sentencias del if
        lista_if = self.lista_sentencias()
        if lista_if:
            nodo.agregar_hijo(lista_if)
        
        # Verificar si hay 'else'
        if self.coincidir('else'):
            self.avanzar()  # Consumir 'else'
            lista_else = self.lista_sentencias()
            if lista_else:
                nodo_else = NodoAST("else")
                nodo_else.agregar_hijo(lista_else)
                nodo.agregar_hijo(nodo_else)
        
        # Consumir 'end'
        if not self.consumir('end', "Se esperaba 'end' para cerrar el if"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
        
        return nodo

    def iteracion(self):
        """iteracion → while expresion lista_sentencias end"""
        print("Analizando iteración (while)...")
        nodo = NodoAST("iteracion")
        
        # Consumir 'while'
        self.consumir('while')
        
        # Consumir expresión de condición
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        # Consumir lista de sentencias
        lista = self.lista_sentencias()
        if lista:
            nodo.agregar_hijo(lista)
        
        # Consumir 'end'
        if not self.consumir('end', "Se esperaba 'end' para cerrar el while"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
        
        return nodo

    def repeticion(self):
        """repeticion → do lista_sentencias while expresion"""
        print("Analizando repetición (do-while)...")
        nodo = NodoAST("repeticion")
        
        # Consumir 'do'
        self.consumir('do')
        
        # Consumir lista de sentencias
        lista = self.lista_sentencias()
        if lista:
            nodo.agregar_hijo(lista)
        
        # Consumir 'until' (según tu código de prueba)
        if not self.consumir('until', "Se esperaba 'until' después del bloque do"):
            self.sincronizar_hasta([';'])
        
        # Consumir expresión de condición
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        return nodo

    def sent_in(self):
        """sent_in → cin >> id ;"""
        print("Analizando sentencia de entrada (cin)...")
        nodo = NodoAST("sent_in")
        
        # Consumir 'cin'
        self.consumir('cin')
        
        # Consumir '>>'
        if not self.consumir('>>', "Se esperaba '>>' después de cin"):
            self.sincronizar_hasta([';'])
            return nodo
        
        # Consumir identificador
        token_id = self.consumir('IDENTIFICADOR', "Se esperaba identificador después de '>>'")
        if token_id:
            nodo_id = NodoAST("identificador", token_id.valor)
            nodo.agregar_hijo(nodo_id)
        
        # Consumir ';'
        if not self.consumir(';', "Se esperaba ';' después de la sentencia cin"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
        
        return nodo

    def sent_out(self):
        """sent_out → cout << salida"""
        print("Analizando sentencia de salida (cout)...")
        nodo = NodoAST("sent_out")
        
        # Consumir 'cout'
        self.consumir('cout')
        
        # Consumir '<<'
        if not self.consumir('<<', "Se esperaba '<<' después de cout"):
            self.sincronizar_hasta([';'])
            return nodo
        
        # Consumir salida (expresión o cadena)
        salida = self.salida()
        if salida:
            nodo.agregar_hijo(salida)
        
        # Consumir ';' opcional
        if self.coincidir(';'):
            self.avanzar()
        
        return nodo

    def salida(self):
        """salida → cadena | expresion | cadena << expresion | expresion << cadena"""
        print("Analizando salida...")
        nodo = NodoAST("salida")
        
        # Intentar procesar como expresión primero
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        return nodo

    def incremento_decremento(self):
        """Maneja operadores ++ y --"""
        print("Analizando incremento/decremento...")
        nodo = NodoAST("incremento_decremento")
        
        # Consumir identificador
        token_id = self.consumir('IDENTIFICADOR')
        if token_id:
            nodo_id = NodoAST("identificador", token_id.valor)
            nodo.agregar_hijo(nodo_id)
        
        # Consumir operador ++ o --
        if self.coincidir('++'):
            self.avanzar()
            nodo_op = NodoAST("operador", "++")
            nodo.agregar_hijo(nodo_op)
        elif self.coincidir('--'):
            self.avanzar()
            nodo_op = NodoAST("operador", "--")
            nodo.agregar_hijo(nodo_op)
        
        # Consumir ';'
        if not self.consumir(';', "Se esperaba ';' después del operador"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
        
        return nodo
    
    def analizar(self):
        """Inicia el análisis sintáctico"""
        try:
            print("Iniciando análisis sintáctico...")
            print(f"Tokens a analizar: {len(self.tokens)}")
            
            if not self.tokens:
                self.agregar_error("No hay tokens para analizar", (1, 1))
                return None, self.errores
            
            self.ast = self.programa()
            
            # Verificar que no sobren tokens
            if self.token_actual():
                token = self.token_actual()
                self.agregar_error(
                    f"Token inesperado después del final del programa: '{token.valor}' ({token.tipo})",
                    (token.linea, token.columna)
                )
            
            print(f"Análisis completado. Errores encontrados: {len(self.errores)}")
            return self.ast, self.errores
            
        except Exception as e:
            print(f"Error interno del analizador: {str(e)}")
            import traceback
            traceback.print_exc()
            self.agregar_error(f"Error interno del analizador: {str(e)}", self.obtener_ultima_posicion_valida())
            return None, self.errores

# Funciones auxiliares
def leer_tokens_desde_archivo(nombre_archivo="tokens.txt"):
    """
    Lee tokens desde un archivo de texto generado por el analizador léxico
    """
    tokens = []
    
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            contenido = archivo.read().strip()
            
        if not contenido:
            print("Advertencia: El archivo de tokens está vacío")
            return tokens
            
        # Dividir por líneas y procesar cada línea
        lineas = contenido.split('\n')
        
        for num_linea, linea_texto in enumerate(lineas, 1):
            linea_texto = linea_texto.strip()
            if not linea_texto or linea_texto.startswith('Tokens') or linea_texto.startswith('==='):
                continue
            
            try:
                token_parseado = None
                
                # Formato principal: TIPO('valor') en línea X, columna Y
                patron_con_posicion = r"(\w+)\('([^']*)'\)\s+en\s+línea\s+(\d+),\s+columna\s+(\d+)"
                match_con_posicion = re.match(patron_con_posicion, linea_texto)
                if match_con_posicion:
                    tipo, valor, linea, columna = match_con_posicion.groups()
                    # Mapear nombres de tokens del analizador léxico a los esperados por el sintáctico
                    tipo_mapeado = mapear_tipo_token(tipo)
                    token_parseado = Token(tipo_mapeado, valor, int(linea), int(columna))
                
                # Formato simple: TIPO('valor') sin posición
                else:
                    patron_simple = r"(\w+)\('([^']*)'\)"
                    match_simple = re.match(patron_simple, linea_texto)
                    if match_simple:
                        tipo, valor = match_simple.groups()
                        tipo_mapeado = mapear_tipo_token(tipo)
                        # Usar número de línea del archivo como posición por defecto
                        token_parseado = Token(tipo_mapeado, valor, num_linea, 1)
                
                # Si se parseó correctamente, agregarlo
                if token_parseado:
                    tokens.append(token_parseado)
                    print(f"Token parseado: {token_parseado}")
                else:
                    print(f"No se pudo parsear la línea {num_linea}: {linea_texto}")
                    
            except Exception as e:
                print(f"Error al procesar línea {num_linea}: {linea_texto} - {e}")
                continue
    
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo {nombre_archivo}")
        return []
    except Exception as e:
        print(f"Error al leer el archivo de tokens: {e}")
        return []
    
    print(f"Total de tokens leídos: {len(tokens)}")
    return tokens

def mapear_tipo_token(tipo_lexico):
    """
    Mapea los tipos de tokens del analizador léxico a los esperados por el sintáctico
    """
    mapeo = {
        'PALABRA_RESERVADA': 'PALABRA_RESERVADA',
        'IDENTIFICADOR': 'IDENTIFICADOR',
        'NUMERO_ENTERO': 'NUMERO_ENTERO',
        'NUMERO_REAL': 'NUMERO_DECIMAL',
        'OPERADOR_ARITMETICO': 'OPERADOR_ARITMETICO',
        'OPERADOR_RELACIONAL': 'OPERADOR_RELACIONAL',
        'OPERADOR_LOGICO': 'OPERADOR_LOGICO',
        'OPERADOR_ASIGNACION': 'OPERADOR_ASIGNACION',
        'ESPECIAL': 'ESPECIAL',
        'ERROR': 'ERROR'
    }
    
    return mapeo.get(tipo_lexico, tipo_lexico)

def analizador_sintactico(archivo_tokens="tokens.txt"):
    """
    Función principal del analizador sintáctico
    """
    print(f"Iniciando análisis sintáctico desde archivo: {archivo_tokens}")
    
    # Leer tokens desde archivo
    tokens = leer_tokens_desde_archivo(archivo_tokens)
    
    if not tokens:
        return None, [ErrorSintactico("No se pudieron cargar los tokens del archivo", 1, 1)]
    
    # Filtrar tokens que no necesita el analizador sintáctico
    tokens_validos = []
    for token in tokens:
        if token.tipo not in ['ERROR']:
            tokens_validos.append(token)
    
    if not tokens_validos:
        return None, [ErrorSintactico("No se encontraron tokens válidos para analizar", 1, 1)]
    
    print(f"Tokens válidos para análisis: {len(tokens_validos)}")
    for i, token in enumerate(tokens_validos):
        print(f"  {i}: {token}")
    
    # Crear analizador y ejecutar análisis
    analizador = AnalizadorSintactico(tokens_validos)
    ast, errores = analizador.analizar()
    
    return ast, errores

def mostrar_ast_texto(nodo, nivel=0):
    """Muestra el AST en formato de texto con indentación"""
    if nodo is None:
        return ""
    
    indentacion = "  " * nivel
    resultado = f"{indentacion}{nodo.tipo}"
    
    if nodo.valor:
        resultado += f": {nodo.valor}"
    
    if nodo.linea and nodo.columna:
        resultado += f" (L{nodo.linea}:C{nodo.columna})"
    
    resultado += "\n"
    
    for hijo in nodo.hijos:
        resultado += mostrar_ast_texto(hijo, nivel + 1)
    
    return resultado