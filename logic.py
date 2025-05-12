from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression
import re

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

        # Formato para comentarios de una línea (// ...)
        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(QColor("#a2a9a5"))
        self.highlightingRules.append((QRegularExpression(r'//[^\n]*'), singleLineCommentFormat))

        # Comentarios de múltiples líneas (/* ... */)
        self.multiLineCommentFormat = QTextCharFormat()
        self.multiLineCommentFormat.setForeground(QColor("#a2a9a5"))
        # Usamos patternOptions para permitir que el punto coincida con saltos de línea
        self.commentStartExpression = QRegularExpression(r"/\*")
        self.commentEndExpression = QRegularExpression(r"\*/")

    def highlightBlock(self, text: str):
        # Primero aplicamos reglas para comentarios multilínea, para que tengan prioridad
        self.highlightMultilineComments(text)
        
        # Luego aplicamos el resto de reglas
        for pattern, format in self.highlightingRules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
    
    def highlightMultilineComments(self, text: str):
        # Resaltado de comentarios multilínea
        self.setCurrentBlockState(0)  # Estado normal por defecto
        
        # Si venimos de un bloque con comentario abierto
        if self.previousBlockState() == 1:
            endIndex = -1
            endMatch = self.commentEndExpression.match(text)
            
            if endMatch.hasMatch():
                endIndex = endMatch.capturedEnd()
                self.setFormat(0, endIndex, self.multiLineCommentFormat)
                self.setCurrentBlockState(0)  # Ya no estamos en un comentario
            else:
                # Todo el bloque es parte del comentario
                self.setFormat(0, len(text), self.multiLineCommentFormat)
                self.setCurrentBlockState(1)  # Seguimos en un comentario
                return
        else:
            endIndex = 0  # No venimos de un comentario abierto
        
        # Buscar nuevos comentarios en este bloque
        startIndex = endIndex
        while startIndex < len(text):
            startMatch = self.commentStartExpression.match(text, startIndex)
            
            if not startMatch.hasMatch():
                break
            
            startIndex = startMatch.capturedStart()
            endMatch = self.commentEndExpression.match(text, startIndex + 2)  # +2 para saltar "/*"
            
            if endMatch.hasMatch():
                endIndex = endMatch.capturedEnd()
                commentLength = endIndex - startIndex
                self.setFormat(startIndex, commentLength, self.multiLineCommentFormat)
                startIndex = endIndex  # Continuar desde el final de este comentario
            else:
                # El comentario continúa en el siguiente bloque
                self.setFormat(startIndex, len(text) - startIndex, self.multiLineCommentFormat)
                self.setCurrentBlockState(1)  # Marcar que estamos en un comentario
                break
            
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

            
    def highlightBlock(self, text):
        for pattern, fmt in self.highlightingRules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna

    #def __repr__(self):
    #    return f"{self.tipo}('{self.valor}') en línea {self.linea}, columna {self.columna}"
    
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
            if not cerrado:
                tokens.append(Token('ERROR', 'Comentario no cerrado', linea, columna))
            continue

        # Identificadores
        if char.isalpha():
            inicio = i
            while i < longitud and (texto[i].isalnum() or texto[i] == '_'):
                avanzar()
            valor = texto[inicio:i]
            
            keywords = ["if", "else", "end", "do", "while", "for", "switch", "case", "break", "int", "float", "string", "main", "cin", "cout", "def", "class", "import", "from", "return",]
            
            if valor in keywords: 
                tokens.append(Token('PALABRA RESERVADA', valor, linea, inicio_col))
            else:
                tokens.append(Token('IDENTIFICADOR', valor, linea, inicio_col))
            continue    

        if texto[i] in ['+', '-', '*', '/', '%', '^']:
            inicio_col = columna
            actual = texto[i]

            # Procesar una secuencia de operadores aritméticos (como +++ o ***)
            while i < longitud and texto[i] == actual:
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