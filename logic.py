from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression
import re

class HighlightSyntax(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor("#9c7692"))
        numberPattern = QRegularExpression(r"(?<![0-9)])[+-]?\d+(\.\d+)?")
        self.highlightingRules.append((numberPattern, numberFormat))

        # Identificadores (letras y dígitos que no empiezan por dígito o _)
        identifierFormat = QTextCharFormat()
        identifierFormat.setForeground(QColor("#da9f40"))
        identifierPattern = QRegularExpression(r"[a-zA-Z][a-zA-Z0-9_]*")
        self.highlightingRules.append((identifierPattern, identifierFormat))

        # Comentarios de una línea estilo C
        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(QColor("#a2a9a5"))
        singleLineCommentPattern = QRegularExpression(r"//[^\n]*")
        self.highlightingRules.append((singleLineCommentPattern, singleLineCommentFormat))

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
        arithmeticPattern = QRegularExpression(
            r"(?<=\s|\()(\+\+|\-\-|\+|\-|\*|\/|\%|\^)(?=\s|\)|$)|"
            r"(?<!\w)(\+\+|\-\-)(?=\w)|"
            r"(?<=\w)(\+\+|\-\-)|"
            r"(?<=\d)(\+|\-|\*|\/|\%|\^)(?=\d)"
        )
        self.highlightingRules.append((arithmeticPattern, arithmeticFormat))

        #Simbolo de igual
        self.highlightingRules.append((QRegularExpression(r"=(?!=)"), QColor("#753476")))

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

        # Modificar la lógica para determinar si + o - es un operador o el signo de un número
        # Primero, procesamos los operadores aritméticos
        if texto[i] in ['+', '-', '*', '/', '%', '^']:
            inicio_col = columna
            actual = texto[i]
            
            # Verificar si es un signo de número o un operador
            es_signo_numero = False
            if actual in ['+', '-']:
                # Es un signo de número si:
                # 1. Está al inicio del texto, o después de un espacio, paréntesis abierto o después de un operador
                # 2. Va seguido de un dígito
                if (i + 1 < longitud and texto[i + 1].isdigit() and 
                    (i == 0 or texto[i-1] in ' \t\n([{=+-*/^%<>!')):
                    es_signo_numero = True
            
            if es_signo_numero:
                # Procesar como un número con signo
                inicio = i
                avanzar()  # Avanzar después del signo
                
                # Leer la parte entera
                while i < longitud and texto[i].isdigit():
                    avanzar()
                
                # Verificar si hay punto decimal
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
            else:
                # Procesar como un operador aritmético
                avanzar()
                
                # Detectar operadores incremento/decremento (++ o --)
                if actual in ['+', '-'] and i < longitud and texto[i] == actual:
                    operador = actual + actual
                    avanzar()
                    
                    # Verificar si hay más símbolos repetidos (error)
                    if i < longitud and texto[i] == actual:
                        error_operador = operador + texto[i]
                        avanzar()
                        
                        # Seguir capturando caracteres repetidos
                        while i < longitud and texto[i] == actual:
                            error_operador += texto[i]
                            avanzar()
                        tokens.append(Token('ERROR', error_operador, linea, inicio_col))
                    else:
                        tokens.append(Token('OPERADOR_ARITMETICO', operador, linea, inicio_col))
                
                elif i < longitud and texto[i] == actual:
                    error_operador = actual + texto[i]
                    avanzar()
                    
                    while i < longitud and texto[i] == actual:
                        error_operador += texto[i]
                        avanzar()
                    tokens.append(Token('ERROR', error_operador, linea, inicio_col))
                else:
                    tokens.append(Token('OPERADOR_ARITMETICO', actual, linea, inicio_col))
            continue

        # Números (solo para los que no tienen signo o ya fueron procesados arriba)
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

        # Comentario de una línea
        if char == '/' and i + 1 < longitud and texto[i + 1] == '/':
            while i < longitud and texto[i] != '\n':
                avanzar()
            continue

        # Comentario de múltiples líneas
        if char == '/' and i + 1 < longitud and texto[i + 1] == '*':
            avanzar()
            avanzar()
            cerrado = False
            while i < longitud:
                if texto[i] == '*' and i + 1 < longitud and texto[i + 1] == '/':
                    avanzar()
                    avanzar()
                    cerrado = True
                    break
                if texto[i] == '\n':
                    linea += 1
                    columna = 1
                    i += 1
                else:
                    avanzar()
            if not cerrado:
                tokens.append(Token('ERROR', 'Comentario no cerrado', linea, columna))
            continue

        #Asignacion

        # Operadores Relacionales (<, >, <=, >=, !=)
        if texto[i] in ['<', '>', '!', '=']:
            inicio_col = columna
            actual = texto[i]
            avanzar()
            
            # Verificar posibles operadores válidos de dos caracteres o inválidos
            if i < longitud:
                # Caso 1: Es un operador válido de dos caracteres seguido por más operadores (error)
                if texto[i] == '=' and actual in ['<', '>', '!', '=']:
                    operador = actual + texto[i]
                    avanzar()
                    
                    # Comprobar si hay más operadores después (sería un error)
                    if i < longitud and (texto[i] in ['<', '>', '!', '=', '?']):
                        error_operador = operador + texto[i]
                        avanzar()
                        
                        # Seguir capturando caracteres de operador
                        while i < longitud and (texto[i] in ['<', '>', '!', '=', '?']):
                            error_operador += texto[i]
                            avanzar()
                        
                        tokens.append(Token('ERROR', error_operador, linea, inicio_col))
                    else:
                        # Es un operador válido de dos caracteres sin errores
                        tokens.append(Token('OPERADOR_RELACIONAL', operador, linea, inicio_col))
                # Caso 2: Comienza con un operador y es seguido por otro operador (incluido '?')
                elif texto[i] in ['<', '>', '!', '=', '?']:
                    error_operador = actual + texto[i]
                    avanzar()
                    
                    # Capturar todos los caracteres de operador seguidos
                    while i < longitud and (texto[i] in ['<', '>', '!', '=', '?']):
                        error_operador += texto[i]
                        avanzar()
                    tokens.append(Token('ERROR', error_operador, linea, inicio_col))
                else:
                    # Es un operador simple
                    if actual == '=':
                        tokens.append(Token('OPERADOR_ASIGNACION', actual, linea, inicio_col))
                    else:
                        tokens.append(Token('OPERADOR_RELACIONAL', actual, linea, inicio_col))
            else:
                # Último carácter del texto
                if actual == '=':
                    tokens.append(Token('OPERADOR_ASIGNACION', actual, linea, inicio_col))
                else:
                    tokens.append(Token('OPERADOR_RELACIONAL', actual, linea, inicio_col))
            continue


         # Operadores Lógicos (&&, ||, ==, <=, >=, !=)
        if texto[i] == '&':
            inicio_col = columna
            avanzar()
            if i < longitud and texto[i] == '&':
                avanzar()
                
                # Comprobar si hay más caracteres '&' (sería un error)
                if i < longitud and texto[i] == '&':
                    error_operador = "&&" + texto[i]
                    avanzar()
                    
                    # Seguir capturando caracteres '&' adicionales
                    while i < longitud and texto[i] == '&':
                        error_operador += texto[i]
                        avanzar()
                    
                    tokens.append(Token('ERROR', error_operador, linea, inicio_col))
                else:
                    # Es un operador lógico AND válido
                    tokens.append(Token('OPERADOR_LOGICO', '&&', linea, inicio_col))
            else:
                tokens.append(Token('ERROR', '&', linea, inicio_col))
            continue

        if texto[i] == '|':
            inicio_col = columna
            avanzar()
            if i < longitud and texto[i] == '|':
                avanzar()
                
                if i < longitud and texto[i] == '|':
                    error_operador = "||" + texto[i]
                    avanzar()
                    
                    while i < longitud and texto[i] == '|':
                        error_operador += texto[i]
                        avanzar()
                    
                    tokens.append(Token('ERROR', error_operador, linea, inicio_col))
                else:
                   
                    tokens.append(Token('OPERADOR_LOGICO', '||', linea, inicio_col))
            else:
                tokens.append(Token('ERROR', '|', linea, inicio_col))
            continue

        if char in ['(', ')', '{', '}', '[', ']', ';', ',', ':', '%']:
            tokens.append(Token('ESPECIAL', char, linea, inicio_col))
            avanzar()
            continue

        tokens.append(Token('ERROR', char, linea, columna))
        avanzar()

    return tokens