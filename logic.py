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
            return f"{self.tipo}('{self.valor}') en línea {self.linea}, columna {self.columna}"

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
            
            keywords = ["if", "else", "end", "do", "while", "for", "switch", "case", "break", "int", "float", "string", "main", "cin", "cout", "def", "class", "import", "from", "return", "then"]
            
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

        # Operadores Relacionales y de E/S (<, >, <=, >=, !=, ==, <<, >>)
        if texto[i] in ['<', '>', '!', '=']:
            inicio_col = columna
            actual = texto[i]
            avanzar()

            # Verificar operadores dobles
            if i < longitud and texto[i] == '=':
                # <=, >=, !=, ==
                operador = actual + texto[i]
                avanzar()
                tokens.append(Token('OPERADOR_RELACIONAL', operador, linea, inicio_col))
            elif i < longitud and texto[i] == actual and actual in ['<', '>']:
                # << o >>
                operador = actual + texto[i]
                avanzar()
                tokens.append(Token('OPERADOR_RELACIONAL', operador, linea, inicio_col))  # Mantener como OPERADOR_RELACIONAL
            else:
                # Operadores simples
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
class ErrorSintactico:
    def __init__(self, mensaje, linea, columna):
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
    
    def __str__(self):
        return f"Error: {self.mensaje} en línea {self.linea}, columna {self.columna}"

class NodoAST:
    def __init__(self, tipo, valor=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = []
        self.linea = None
        self.columna = None
    
    def agregar_hijo(self, hijo):
        if hijo:
            self.hijos.append(hijo)
    
    def set_posicion(self, linea, columna):
        """Establece la posición del nodo"""
        self.linea = linea
        self.columna = columna
        return self
    
    def __str__(self):
        return f"NodoAST({self.tipo}, {self.valor})"

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
        """Retorna el siguiente token sin avanzar la posición"""
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
    

    def calcular_columna_real_del_token(self, token):
        """Calcula columna aproximada"""
        return 1  # Por simplicidad, siempre columna 1

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
                    # CAMBIO: No consumir automáticamente el token objetivo
                    # Dejar que el método llamador decida
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
    
    # def programa(self):
    #     """programa → main { lista_declaracion }"""
    #     print("Analizando programa...")
    #     nodo_programa = NodoAST("programa")

    #     # Consumir 'main'
    #     if not self.consumir('main', "Se esperaba 'main' al inicio del programa"):
    #         self.sincronizar_hasta(['{'])
    #         return nodo_programa

    #     # Crear nodo 'main'
    #     nodo_main = NodoAST("main")

    #     # Consumir '{'
    #     if not self.consumir('{', "Se esperaba '{' después de 'main'"):
    #         self.sincronizar_hasta(['int', 'float', 'bool', 'IDENTIFICADOR'])

    #     # Analizar lista de declaraciones
    #     lista_decl = self.lista_declaracion()
    #     if lista_decl:
    #         for hijo in lista_decl.hijos:
    #             nodo_main.agregar_hijo(hijo)

    #     # Consumir '}'
    #     if not self.consumir('}', "Se esperaba '}' al final del programa"):
    #         pass  # Error ya reportado

    #     # Agregar el bloque main al programa
    #     nodo_programa.agregar_hijo(nodo_main)

    #     return nodo_programa

    def programa(self):
        """programa → main { lista_declaracion }"""
        print("Analizando programa...")
        nodo_programa = NodoAST("programa")

        # Consumir 'main'
        if not self.consumir('main', "Se esperaba 'main' al inicio del programa"):
            self.sincronizar_hasta(['{'])
            return nodo_programa

        # Crear nodo 'main'
        nodo_main = NodoAST("main")

        # Consumir '{'
        if not self.consumir('{', "Se esperaba '{' después de 'main'"):
            self.sincronizar_hasta(['int', 'float', 'bool', 'IDENTIFICADOR'])

        # Analizar lista de declaraciones
        lista_decl = self.lista_declaracion()
        if lista_decl:
            for hijo in lista_decl.hijos:
                nodo_main.agregar_hijo(hijo)

        # Consumir '}'
        if not self.consumir('}', "Se esperaba '}' al final del programa"):
            pass  # Error ya reportado

        # Agregar el bloque main al programa
        nodo_programa.agregar_hijo(nodo_main)

        return nodo_programa

    def lista_declaracion(self):
        """lista_declaracion → { declaracion_variable } lista_sentencias"""
        print("Analizando lista de declaraciones...")
        
        # Si solo hay declaraciones y sentencias, no debe encapsularse todo en un nodo contenedor.
        nodos = []

        # Declaraciones de variables (cero o más)
        while self.token_actual() and (self.coincidir('int') or self.coincidir('float') or self.coincidir('bool')):
            decl = self.declaracion_variable()
            if decl:
                nodos.append(decl)
            else:
                self.sincronizar_hasta(self.tokens_sync_declaracion)
        
        # Sentencias (también pueden ser cero o más)
        lista_sent = self.lista_sentencias()
        if lista_sent:
            for hijo in lista_sent.hijos:
                nodos.append(hijo)

        # Si hay más de un nodo, empaquetamos en un solo nodo contenedor
        if len(nodos) == 1:
            return nodos[0]
        elif len(nodos) > 1:
            nodo_lista = NodoAST("bloque")  # Puedes llamarlo "programa" o similar si lo prefieres
            for n in nodos:
                nodo_lista.agregar_hijo(n)
            return nodo_lista

        return None
    
    def declaracion_variable(self):
        """declaracion_variable → tipo identificador ;"""
        print("Analizando declaración de variable...")
        
        # Capturar el token tipo
        token_tipo = self.token_actual()
        if not self.coincidir('int') and not self.coincidir('float') and not self.coincidir('bool'):
            return None
        
        nodo = NodoAST("declaracion_variable")
        # Establecer posición del nodo
        if token_tipo:
            nodo.set_posicion(token_tipo.linea, token_tipo.columna)
        
        self.avanzar()  # Consumir el tipo
        nodo_tipo = NodoAST("tipo", token_tipo.valor)
        if token_tipo:
            nodo_tipo.set_posicion(token_tipo.linea, token_tipo.columna)
        nodo.agregar_hijo(nodo_tipo)
        
        # Procesar identificadores según gramática
        nodo_identificador = self.identificador()
        if nodo_identificador:
            nodo.agregar_hijo(nodo_identificador)
        
        # Consumir punto y coma
        if not self.consumir(';', "Se esperaba ';' después de la declaración"):
            self.sincronizar_hasta(self.tokens_sync_declaracion)
        
        return nodo
        
    def identificador(self):
        """identificador → id | identificador , id"""
        print("Analizando identificador...")
        nodo = NodoAST("identificador")
        
        # Primer identificador
        token_id = self.token_actual()
        if not self.coincidir('IDENTIFICADOR'):
            return None
        
        # Establecer posición
        if token_id:
            nodo.set_posicion(token_id.linea, token_id.columna)
        
        self.avanzar()
        nodo_id = NodoAST("id", token_id.valor)
        # Establecer posición del nodo hijo
        if token_id:
            nodo_id.set_posicion(token_id.linea, token_id.columna)
        nodo.agregar_hijo(nodo_id)
        
        # Identificadores adicionales separados por comas
        while self.coincidir(','):
            self.avanzar()  # Consumir la coma
            token_id = self.token_actual()
            if not self.coincidir('IDENTIFICADOR'):
                break
            self.avanzar()
            nodo_id = NodoAST("id", token_id.valor)
            # Establecer posición
            if token_id:
                nodo_id.set_posicion(token_id.linea, token_id.columna)
            nodo.agregar_hijo(nodo_id)
        
        return nodo
        
    def lista_sentencias(self):
        """lista_sentencias → lista_sentencias sentencia | ε"""
        print("Analizando lista de sentencias...")
        nodo = NodoAST("lista_sentencias")

        while (self.token_actual() and
            not self.coincidir('}') and not self.coincidir('end') and
            not self.coincidir('else') and not self.coincidir('until')):

            # VALIDACIÓN: Si encontramos un ';' al inicio, es un error
            if self.token_actual().valor == ';':
                self.agregar_error(f"';' inesperado. No se esperaba punto y coma aquí",
                                (self.token_actual().linea, self.token_actual().columna))
                self.avanzar()  # Saltar el ';' problemático
                continue

            # Guardar posición antes de intentar procesar sentencia
            posicion_antes = self.posicion
            sent = self.sentencia()
            
            if sent:
                nodo.agregar_hijo(sent)
            else:
                # Si no se pudo procesar la sentencia
                if self.token_actual():
                    # Si la posición no cambió, significa que sentencia() no consumió el token
                    if self.posicion == posicion_antes:
                        print(f"Token no procesado por sentencia(): {self.token_actual()}")
                        # Sincronizar hasta encontrar un punto de recuperación
                        self.sincronizar_hasta(self.tokens_sync_sentencia)
                        
                        # Si seguimos en la misma posición después de sincronizar, salir
                        if self.posicion == posicion_antes:
                            print("No se pudo sincronizar, saltando token problemático")
                            self.avanzar()
                            # Verificar si ahora podemos continuar
                            if (self.token_actual() and 
                                (self.coincidir('}') or self.coincidir('end') or 
                                self.coincidir('else') or self.coincidir('until'))):
                                break
                    else:
                        # sentencia() consumió algunos tokens pero falló, continuar
                        print("Sentencia parcialmente procesada, continuando...")
                else:
                    break

        return nodo if nodo.hijos else None

    def sentencia(self):
        """sentencia → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion"""
        print("Analizando sentencia...")
        token = self.token_actual()
        
        if not token:
            return None
            
        if self.coincidir('if'):
            return self.seleccion()
        elif self.coincidir('while'):
            return self.iteracion()
        elif self.coincidir('do'):
            return self.repeticion()
        elif self.coincidir('cin'):
            return self.sent_in()
        elif self.coincidir('cout'):
            return self.sent_out()
        elif self.coincidir('IDENTIFICADOR'):
            siguiente = self.token_siguiente()
            if siguiente and siguiente.valor == '=':
                return self.asignacion()
            elif siguiente and (siguiente.valor == '++' or siguiente.valor == '--'):
                return self.incremento_decremento()
            else:
                # Error: identificador sin asignación válida
                self.agregar_error(
                    f"Se esperaba '=' después del identificador '{token.valor}'",
                    (token.linea, token.columna)
                )
                self.avanzar()  # Saltar el token problemático
                return None
        else:
            # CAMBIO CRÍTICO: Reportar error específico para token no reconocido
            self.agregar_error(
                f"Token inesperado '{token.valor}' ({token.tipo}). Se esperaba una sentencia válida",
                (token.linea, token.columna)
            )
            # NO avanzar aquí, dejar que lista_sentencias maneje la sincronización
            return None


    def asignacion(self):
        """asignacion → id = sent_expresion"""
        print("Analizando asignación...")
        
        # Capturar identificador
        token_id = self.token_actual()
        if not self.coincidir('IDENTIFICADOR'):
            self.agregar_error("Se esperaba un identificador al inicio de la asignación",
                            self.obtener_ultima_posicion_valida())
            return None
        
        nodo = NodoAST("asignacion", token_id.valor)
        # Establecer posición
        if token_id:
            nodo.set_posicion(token_id.linea, token_id.columna)
        
        self.avanzar()
        
        # Consumir '='
        if not self.consumir('=', "Se esperaba '=' después del identificador"):
            self.sincronizar_hasta([';'])
            return nodo
        
        # Consumir sent_expresion
        expr = self.sent_expresion()
        if expr:
            nodo.agregar_hijo(expr)
        else:
            self.agregar_error("Se esperaba una expresión después del '='",
                            self.obtener_ultima_posicion_valida())
        
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
        """expresion → expresion_logica"""
        print("Analizando expresión...")
        return self.expresion_logica()


    def expresion_logica(self):
        """expresion_logica → expresion_relacional { OPERADOR_LOGICO expresion_relacional }"""
        print("Analizando expresión lógica...")

        nodo_izq = self.expresion_relacional()
        if not nodo_izq:
            return None

        while self.token_actual() and self.token_actual().tipo == 'OPERADOR_LOGICO':
            op_token = self.token_actual()
            self.avanzar()

            nodo_der = self.expresion_relacional()
            if not nodo_der:
                self.agregar_error("Se esperaba expresión después del operador lógico",
                                self.obtener_ultima_posicion_valida())
                return nodo_izq

            nuevo_nodo = NodoAST("log_op", op_token.valor)
            nuevo_nodo.agregar_hijo(nodo_izq)
            nuevo_nodo.agregar_hijo(nodo_der)

            nodo_izq = nuevo_nodo

        return nodo_izq


    # def expresion_relacional(self):
    #     """expresion_relacional → expresion_simple [ OPERADOR_RELACIONAL expresion_simple ]"""
    #     print("Analizando expresión relacional...")
        
    #     expr_izq = self.expresion_simple()
    #     if not expr_izq:
    #         return None
        
    #     # Verificar si hay operador relacional (>, <, ==, !=, >=, <=)
    #     if self.token_actual() and self.token_actual().tipo == 'OPERADOR_RELACIONAL':
    #         nodo = NodoAST("expresion_relacional")
    #         nodo.agregar_hijo(expr_izq)
            
    #         # Consumir operador relacional
    #         op_token = self.token_actual()
    #         self.avanzar()
    #         nodo_op = NodoAST("rel_op", op_token.valor)
    #         nodo.agregar_hijo(nodo_op)
            
    #         # Consumir segunda expresión simple
    #         expr_der = self.expresion_simple()
    #         if expr_der:
    #             nodo.agregar_hijo(expr_der)
    #         else:
    #             self.agregar_error("Se esperaba expresión después del operador relacional",
    #                             self.obtener_ultima_posicion_valida())
    #             return None
            
    #         return nodo
        
    #     return expr_izq

    def expresion_relacional(self):
        """expresion_relacional → expresion_simple [ OPERADOR_RELACIONAL expresion_simple ]"""
        print("Analizando expresión relacional...")

        nodo_izq = self.expresion_simple()
        if not nodo_izq:
            return None

        if self.token_actual() and self.token_actual().tipo == 'OPERADOR_RELACIONAL':
            op_token = self.token_actual()
            self.avanzar()

            nodo_der = self.expresion_simple()
            if not nodo_der:
                self.agregar_error("Se esperaba expresión después del operador relacional",
                                self.obtener_ultima_posicion_valida())
                return nodo_izq

            nodo_op = NodoAST("rel_op", op_token.valor)
            nodo_op.agregar_hijo(nodo_izq)
            nodo_op.agregar_hijo(nodo_der)

            return nodo_op

        return nodo_izq


    # def expresion_simple(self):
    #     """expresion_simple → expresion_simple suma_op termino | termino"""
    #     print("Analizando expresión simple...")
    
    #     termino_izq = self.termino()
    #     if not termino_izq:
    #         return None
    
    #     # Si solo hay un término, devolverlo directamente
    #     if not (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and
    #             self.token_actual().valor in ['+', '-']):
    #         return termino_izq
    
    #     # Crear nodo para expresión con operadores
    #     nodo = NodoAST("expresion_simple")
    #     nodo.agregar_hijo(termino_izq)
    
    #     # Procesar operadores y términos adicionales
    #     while (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and
    #         self.token_actual().valor in ['+', '-']):
        
    #         op_token = self.token_actual()
    #         self.avanzar()  # Consumir el operador
        
    #         # Crear nodo para el operador
    #         op_nodo = NodoAST("suma_op", op_token.valor)
    #         nodo.agregar_hijo(op_nodo)
        
    #         # Procesar siguiente término
    #         termino_der = self.termino()
    #         if termino_der:
    #             nodo.agregar_hijo(termino_der)
    #         else:
    #             self.agregar_error(
    #                 f"Se esperaba un término después del operador '{op_token.valor}'",
    #                 (op_token.linea, op_token.columna)
    #             )
    #             break
    
    #     return nodo
        
    def expresion_simple(self):
        """expresion_simple → termino { suma_op termino }"""
        print("Analizando expresión simple...")

        nodo_izq = self.termino()
        if not nodo_izq:
            return None

        while (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and 
            self.token_actual().valor in ['+', '-']):
            
            op_token = self.token_actual()
            self.avanzar()

            nodo_der = self.termino()
            if not nodo_der:
                self.agregar_error(
                    f"Se esperaba un término después del operador '{op_token.valor}'",
                    (op_token.linea, op_token.columna)
                )
                return nodo_izq  # Retornar lo que se pudo analizar

            # Crear nuevo nodo raíz con el operador
            nuevo_nodo = NodoAST("suma_op", op_token.valor)
            nuevo_nodo.agregar_hijo(nodo_izq)
            nuevo_nodo.agregar_hijo(nodo_der)

            # El nuevo nodo se convierte en el nodo izquierdo para el siguiente operador
            nodo_izq = nuevo_nodo

        return nodo_izq


    def termino(self):
        """termino → factor { mult_op factor }"""
        print("Analizando término...")

        nodo_izq = self.factor()
        if not nodo_izq:
            return None

        while (self.token_actual() and self.token_actual().tipo == 'OPERADOR_ARITMETICO' and 
            self.token_actual().valor in ['*', '/', '%']):

            op_token = self.token_actual()
            self.avanzar()  # Consumir el operador

            nodo_der = self.factor()
            if not nodo_der:
                self.agregar_error(
                    f"Se esperaba un factor después del operador '{op_token.valor}'",
                    (op_token.linea, op_token.columna)
                )
                return nodo_izq  # Retornar lo que se pudo construir

            # Crear nuevo nodo raíz con el operador
            nuevo_nodo = NodoAST("mult_op", op_token.valor)
            nuevo_nodo.agregar_hijo(nodo_izq)
            nuevo_nodo.agregar_hijo(nodo_der)

            nodo_izq = nuevo_nodo  # Este pasa a ser el nodo base para el siguiente operador
        return nodo_izq

    def factor(self):
        """factor → componente { '^' componente }"""
        print("Analizando factor...")

        nodo_izq = self.componente()
        if not nodo_izq:
            return None

        while self.token_actual() and self.token_actual().valor == '^':
            op_token = self.token_actual()
            self.avanzar()  # Consumir '^'

            nodo_der = self.componente()
            if not nodo_der:
                self.agregar_error(
                    f"Se esperaba un componente después del operador '^'",
                    (op_token.linea, op_token.columna)
                )
                return nodo_izq

            # En la potencia el operador es **asociativo a la derecha** (por convención)
            nuevo_nodo = NodoAST("pot_op", op_token.valor)
            nuevo_nodo.agregar_hijo(nodo_izq)
            nuevo_nodo.agregar_hijo(nodo_der)

            nodo_izq = nuevo_nodo

        return nodo_izq


    # def componente(self):
    #     """componente → ( expresion ) | número | id | bool | op_logico componente"""
    #     print("Analizando componente...")
    #     token = self.token_actual()
        
    #     if not token:
    #         self.agregar_error("Se esperaba una expresión", self.obtener_ultima_posicion_valida())
    #         return None
        
    #     # Operador lógico unario
    #     if token.tipo == 'OPERADOR_LOGICO' and token.valor in ['!']:
    #         nodo = NodoAST("componente_logico")
    #         op_nodo = NodoAST("op_logico", token.valor)
    #         nodo.agregar_hijo(op_nodo)
    #         self.avanzar()  # Consumir operador lógico
            
    #         comp = self.componente()
    #         if comp:
    #             nodo.agregar_hijo(comp)
    #         return nodo
        
    #     # Expresión entre paréntesis
    #     if self.coincidir('('):
    #         self.avanzar()  # Consumir '('
    #         expr = self.expresion()
    #         if not self.consumir(')', "Se esperaba ')' después de la expresión"):
    #             self.sincronizar_hasta([';'])
    #         return expr
        
    #     # Números, identificadores
    #     if token.tipo in ['NUMERO_ENTERO', 'NUMERO_DECIMAL', 'NUMERO_REAL', 'IDENTIFICADOR']:
    #         nodo = NodoAST("componente", token.valor)
    #         nodo.linea = token.linea
    #         nodo.columna = token.columna
    #         self.avanzar()
    #         return nodo
        
    #     # Valores booleanos
    #     if token.tipo == 'IDENTIFICADOR' and token.valor in ['true', 'false']:
    #         nodo = NodoAST("bool", token.valor)
    #         nodo.linea = token.linea
    #         nodo.columna = token.columna
    #         self.avanzar()
    #         return nodo
        
    #     self.agregar_error(
    #         f"Se esperaba número, identificador o expresión entre paréntesis, se encontró '{token.valor}' ({token.tipo})", 
    #         (token.linea, token.columna)
    #     )
    #     return None


    def componente(self):
        """componente → ( expresion ) | número | id | bool | op_logico componente"""
        print("Analizando componente...")
        token = self.token_actual()

        if not token:
            self.agregar_error("Se esperaba una expresión", self.obtener_ultima_posicion_valida())
            return None

        # Operador lógico unario
        if token.tipo == 'OPERADOR_LOGICO' and token.valor == '!':
            nodo = NodoAST("componente_logico")
            op_nodo = NodoAST("op_logico", token.valor)
            nodo.agregar_hijo(op_nodo)
            self.avanzar()
            comp = self.componente()
            if comp:
                nodo.agregar_hijo(comp)
            return nodo

        # Paréntesis
        if self.coincidir('('):
            self.avanzar()
            expr = self.expresion()
            if not self.consumir(')', "Se esperaba ')' después de la expresión"):
                self.sincronizar_hasta([';'])
            return expr  

        # Números o identificadores
        if token.tipo in ['NUMERO_ENTERO', 'NUMERO_DECIMAL', 'NUMERO_REAL']:
            nodo = NodoAST("numero", token.valor)
            self.avanzar()
            return nodo

        if token.tipo == 'IDENTIFICADOR':
            # Validar si es booleano
            if token.valor in ['true', 'false']:
                nodo = NodoAST("bool", token.valor)
            else:
                nodo = NodoAST("id", token.valor)
            self.avanzar()
            return nodo

        self.agregar_error(
            f"Se esperaba número, identificador o expresión entre paréntesis, se encontró '{token.valor}' ({token.tipo})",
            (token.linea, token.columna)
        )
        return None

    def seleccion(self):
        """seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end"""
        print("Analizando selección (if)...")
        nodo = NodoAST("seleccion")
    
        # Consumir 'if'
        if not self.consumir('if'):
            return None
    
        # Consumir expresión de condición
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        else:
            self.agregar_error("Se esperaba una expresión de condición después de 'if'",
                            self.obtener_ultima_posicion_valida())
            return None
    
        # Consumir 'then'
        if not self.consumir('then', "Se esperaba 'then' después de la condición en el 'if'"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
            return None
        
        # VALIDACIÓN: Verificar que no haya ';' después de 'then'
        if self.token_actual() and self.token_actual().valor == ';':
            self.agregar_error("No se esperaba ';' después de 'then'", 
                            (self.token_actual().linea, self.token_actual().columna))
            return None
    
        # Consumir lista de sentencias del if
        lista_if = self.lista_sentencias()
        if lista_if:
            nodo.agregar_hijo(lista_if)
    
        # Verificar si hay 'else'
        if self.coincidir('else'):
            self.avanzar()  # Consumir 'else'
            
            # VALIDACIÓN: Verificar que no haya ';' después de 'else'
            if self.token_actual() and self.token_actual().valor == ';':
                self.agregar_error("No se esperaba ';' después de 'else'", 
                                (self.token_actual().linea, self.token_actual().columna))
                return None
            
            lista_else = self.lista_sentencias()
            if lista_else:
                nodo_else = NodoAST("else")
                nodo_else.agregar_hijo(lista_else)
                nodo.agregar_hijo(nodo_else)
    
        # Consumir 'end'
        if not self.consumir('end', "Se esperaba 'end' para cerrar el if"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
            return None
    
        return nodo

    
    def iteracion(self):
        """iteracion → while expresion lista_sentencias end"""
        print("Analizando iteración (while)...")
        nodo = NodoAST("iteracion")

        if not self.consumir('while', "Se esperaba 'while' para iniciar la iteración"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
            return None

        expr = self.expresion()
        if expr:
            nodo_cond = NodoAST("condicion")
            nodo_cond.agregar_hijo(expr)
            nodo.agregar_hijo(nodo_cond)
        else:
            self.agregar_error("Se esperaba una condición después de 'while'", self.obtener_ultima_posicion_valida())
            return None

        lista = self.lista_sentencias()
        if lista:
            nodo_lista = NodoAST("lista_sentencias")
            for hijo in lista.hijos:
                nodo_lista.agregar_hijo(hijo)
            nodo.agregar_hijo(nodo_lista)

        if not self.consumir('end', "Se esperaba 'end' para cerrar el while"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)

        return nodo


    def repeticion(self):
        """repeticion → do lista_sentencias (while|until) expresion"""
        print("Analizando repetición (do-while/do-until)…")
        # Creamos el nodo padre con un valor genérico o guardando el tipo:
        nodo = NodoAST("repeticion")

        # Consumir 'do'
        if not self.consumir('do', "Se esperaba 'do' al inicio de la repetición"):
            return None

        # Primero el cuerpo del bucle
        lista = self.lista_sentencias()
        if lista:
            nodo.agregar_hijo(lista)

        # Ahora detectamos si es while o until
        if self.coincidir('while') or self.coincidir('until'):
            tipo = self.token_actual().valor  # "while" o "until"
            self.avanzar()  # consumimos la palabra clave

            # La expresión de condición
            expr = self.expresion()
            if not expr:
                self.agregar_error(f"Se esperaba una expresión después de '{tipo}'",
                                self.obtener_ultima_posicion_valida())
            else:
                # Creamos el mismo subnodo 'condicion' que en tu iteración normal
                nodo_cond = NodoAST("condicion", tipo)
                nodo_cond.agregar_hijo(expr)
                nodo.agregar_hijo(nodo_cond)
        else:
            self.agregar_error("Se esperaba 'while' o 'until' después del bloque 'do'",
                            self.obtener_ultima_posicion_valida())

        return nodo

    def sent_in(self):
        """sent_in → cin >> id ;"""
        print("Analizando sentencia de entrada (cin)...")
        
        # Capturar el token 'cin' para obtener su posición
        token_cin = self.token_actual()
        nodo = NodoAST("sent_in")
        
        # Establecer la posición del nodo sent_in
        if token_cin:
            nodo.set_posicion(token_cin.linea, token_cin.columna)
        
        # Consumir 'cin'
        self.consumir('cin')
        
        # Consumir >>
        if not self.consumir('>>', "Se esperaba '>>' después de cin"):
            self.sincronizar_hasta([';'])
            return nodo
        
        # Consumir identificador
        token_id = self.token_actual()
        if not self.coincidir('IDENTIFICADOR'):
            self.agregar_error("Se esperaba identificador después de cin >>", 
                            self.obtener_ultima_posicion_valida())
            self.sincronizar_hasta([';'])
            return nodo
        
        # Crear nodo para el identificador
        nodo_id = NodoAST("id", token_id.valor)
        # Establecer la posición del identificador
        if token_id:
            nodo_id.set_posicion(token_id.linea, token_id.columna)
        
        nodo.agregar_hijo(nodo_id)
        self.avanzar()  # Consumir el identificador
        
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
        
        # CORRECCIÓN: Consumir << como un solo token
        if not self.consumir('<<', "Se esperaba '<<' después de cout"):
            self.sincronizar_hasta([';'])
            return nodo
        
        # Consumir salida
        salida = self.salida()
        if salida:
            nodo.agregar_hijo(salida)
        
        # Consumir ';'
        if not self.consumir(';', "Se esperaba ';' después de la sentencia cout"):
            self.sincronizar_hasta(self.tokens_sync_sentencia)
        
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

    # def incremento_decremento(self):
    #     """Maneja operadores ++ y --"""
    #     print("Analizando incremento/decremento...")
    #     nodo = NodoAST("incremento_decremento")
        
    #     # Consumir identificador
    #     token_id = self.consumir('IDENTIFICADOR')
    #     if token_id:
    #         nodo_id = NodoAST("identificador", token_id.valor)
    #         nodo.agregar_hijo(nodo_id)
        
    #     # Consumir operador ++ o --
    #     if self.coincidir('++'):
    #         self.avanzar()
    #         nodo_op = NodoAST("operador", "++")
    #         nodo.agregar_hijo(nodo_op)
    #     elif self.coincidir('--'):
    #         self.avanzar()
    #         nodo_op = NodoAST("operador", "--")
    #         nodo.agregar_hijo(nodo_op)
        
    #     # Consumir ';'
    #     if not self.consumir(';', "Se esperaba ';' después del operador"):
    #         self.sincronizar_hasta(self.tokens_sync_sentencia)
        
    #     return nodo

    def incremento_decremento(self):
        """Maneja operadores ++ y -- como asignaciones implícitas"""
        print("Analizando incremento/decremento...")

        # Consumir identificador
        token_id = self.consumir('IDENTIFICADOR')
        if not token_id:
            self.agregar_error("Se esperaba un identificador antes del operador de incremento/decremento",
                            self.obtener_ultima_posicion_valida())
            return None

        # Verificar operador ++ o --
        if self.coincidir('++') or self.coincidir('--'):
            operador = self.token_actual().valor  # Guardar el operador ("++" o "--")
            self.avanzar()

            # Crear nodo de asignación: asignacion: a
            nodo_asignacion = NodoAST("asignacion", token_id.valor)

            # Crear nodo expresion_simple: +
            op = '+' if operador == '++' else '-'
            nodo_expr = NodoAST("expresion_simple", op)

            # Hijos: id: a y numero: 1
            nodo_id = NodoAST("id", token_id.valor)
            nodo_num = NodoAST("numero", "1")

            nodo_expr.agregar_hijo(nodo_id)
            nodo_expr.agregar_hijo(nodo_num)

            nodo_asignacion.agregar_hijo(nodo_expr)

            # Consumir ';'
            if not self.consumir(';', "Se esperaba ';' después del incremento/decremento"):
                self.sincronizar_hasta(self.tokens_sync_sentencia)

            return nodo_asignacion

        # Si no hay ++ o --
        self.agregar_error("Se esperaba operador '++' o '--' después del identificador",
                        self.obtener_ultima_posicion_valida())
        self.sincronizar_hasta(self.tokens_sync_sentencia)
        return None

    
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

    def procesar_declaracion(self, nodo, nodo_anotado):
        """Procesa declaración de variables."""
        tipo_dato = None
        
        # AGREGAR: Capturar posición del nodo de declaración
        linea_decl = getattr(nodo, 'linea', 0)
        columna_decl = getattr(nodo, 'columna', 0)
        
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
                        # CAMBIO: Usar la posición del id_hijo o del nodo padre
                        linea = getattr(id_hijo, 'linea', None) or linea_decl or 0
                        columna = getattr(id_hijo, 'columna', None) or columna_decl or 0
                        
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
# lectura Lexico
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
        
    resultado += "\n"
    
    for hijo in nodo.hijos:
        resultado += mostrar_ast_texto(hijo, nivel + 1)
    
    return resultado