from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QTabWidget, QSplitter, QMenuBar, QMenu, 
    QFileDialog, QLabel, QPlainTextEdit, QHBoxLayout, QToolBar, QStatusBar, QScrollBar, QTreeWidget,
    QTreeWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView # Se agregaron estas importaciones
)
from PyQt6.QtGui import QAction, QColor, QPainter, QTextFormat, QFontMetrics, QIcon
from PyQt6.QtCore import QRect, Qt, QSize, pyqtSlot
import sys
import os


from logic import analizador_sintactico, mostrar_ast_texto
from PyQt6.QtGui import QFont
from logic import HighlightSyntax
from logic import analizador_lexico


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.line_number_area = LineNumberArea(self)
        
        self.highlighter = HighlightSyntax(self.document())
        
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.update_cursor_position)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Establece la referencia a la ventana principal (solo una vez)
        self.main_window = parent
        
        # Conecta la señal textChanged directamente a este editor
        self.textChanged.connect(self.texto_cambiado)
        
        # Crear barras de desplazamiento literales
        self.horizontal_scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        self.vertical_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        
        # Conectar las barras de desplazamiento con el editor
        self.horizontal_scrollbar.valueChanged.connect(self.horizontal_scroll_changed)
        self.vertical_scrollbar.valueChanged.connect(self.vertical_scroll_changed)
        
        # Conectar los eventos de desplazamiento del editor a las barras
        self.horizontalScrollBar().valueChanged.connect(self.update_horizontal_scrollbar)
        self.verticalScrollBar().valueChanged.connect(self.update_vertical_scrollbar)
        
        # Para asegurar que los saltos de línea se contabilicen correctamente
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    
    def texto_cambiado(self):
        # Solo llamar a ejecutar_analisis_lexico si main_window está definido
        if self.main_window is not None:
            try:
                # Usar try/except para manejar cualquier error
                self.main_window.ejecutar_analisis_lexico(cambiar_pestaña=False)
            except Exception as e:
                print(f"Error durante el análisis léxico: {e}")

    def set_main_window(self, main_window):
        self.main_window = main_window

    def update_cursor_position(self):
        if self.main_window:
            cursor = self.textCursor()
            # Obtener el número de línea real basado en la posición del cursor
            line_number = cursor.blockNumber() + 1
            column_number = cursor.columnNumber() + 1
            self.main_window.update_line_status(line_number, column_number)
    
    def horizontal_scroll_changed(self, value):
        # Actualizar la posición de desplazamiento horizontal del editor
        self.horizontalScrollBar().setValue(value)
    
    def vertical_scroll_changed(self, value):
        # Actualizar la posición de desplazamiento vertical del editor
        self.verticalScrollBar().setValue(value)
    
    def update_horizontal_scrollbar(self, value):
        # Actualizar la barra de desplazamiento horizontal externa
        self.horizontal_scrollbar.setValue(value)
    
    def update_vertical_scrollbar(self, value):
        # Actualizar la barra de desplazamiento vertical externa
        self.vertical_scrollbar.setValue(value)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Actualizar los rangos de las barras de desplazamiento
        self.update_scrollbar_ranges()
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
    
    def update_scrollbar_ranges(self):
        # Actualizar el rango de la barra de desplazamiento horizontal
        h_scrollbar = self.horizontalScrollBar()
        self.horizontal_scrollbar.setRange(h_scrollbar.minimum(), h_scrollbar.maximum())
        self.horizontal_scrollbar.setPageStep(h_scrollbar.pageStep())
        self.horizontal_scrollbar.setSingleStep(h_scrollbar.singleStep())
        
        # Actualizar el rango de la barra de desplazamiento vertical
        v_scrollbar = self.verticalScrollBar()
        self.vertical_scrollbar.setRange(v_scrollbar.minimum(), v_scrollbar.maximum())
        self.vertical_scrollbar.setPageStep(v_scrollbar.pageStep())
        self.vertical_scrollbar.setSingleStep(v_scrollbar.singleStep())

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def highlight_current_line(self):
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#e3f5f7")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.GlobalColor.white)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.darkGray)
                painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(),
                                Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
            

    def toPlainText(self):
        return super().toPlainText()

    def setText(self, text):
        super().setPlainText(text)
        # Actualizar los rangos de las barras de desplazamiento después de establecer el texto
        self.update_scrollbar_ranges()
 
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        # Actualizar explícitamente la posición del cursor después de cada pulsación de tecla
        self.update_cursor_position()
        # Actualizar los rangos de las barras de desplazamiento
        self.update_scrollbar_ranges()

class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilador IDE")
        self.setGeometry(100, 100, 1000, 700)
        self.current_file = None
        
        # Inicializar atributos que se crean dinámicamente o se acceden antes de load_editor
        self.semantico_widget = None
        self.tree_semantico = None
        self.hash_table_widget = None
        self.tabla_simbolos_widget = None
        self.error_semantico = None # Se inicializa en load_editor.
        
        self.initUI()


    def ejecutar_analisis_lexico(self, cambiar_pestaña=False):
        if not hasattr(self, 'text_edit') or self.text_edit is None:
            return
            
        texto = self.text_edit.toPlainText()
        tokens = analizador_lexico(texto)
        
        salida = ""
        salida_simple = ""
        salida_errores = ""
        
        for token in tokens:
            if token.tipo == 'ERROR':
                salida_errores += f"{token}\n"
            else:
                salida += f"{token}\n"  # para tokens2.txt
                salida_simple += f"{token.tipo}('{token.valor}')\n"  # para tokens.txt

        self.lexico_output.setPlainText(salida_simple)
        self.error_lexico.setPlainText(salida_errores)

        # Guardar en archivos de texto
        try:
            with open("tokens.txt", "w", encoding="utf-8") as f_tokens:
                f_tokens.write(salida)  # Solo tipo y valor

            with open("errores.txt", "w", encoding="utf-8") as f_errores:
                f_errores.write(salida_errores)
        except Exception as e:
            print(f"Error al guardar los archivos: {e}")
        
        # Solo cambia a la pestaña si se solicita explícitamente
        if cambiar_pestaña:
            self.tabs.setCurrentWidget(self.lexico_output)
            self.errors_tabs.setCurrentWidget(self.error_lexico)

    def initUI(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_label = QLabel("Listo")
        status_bar.addWidget(self.status_label, 1)
    
        self.cursor_position_label = QLabel("Línea: 0    Columna: 0")
        status_bar.addPermanentWidget(self.cursor_position_label)
        
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("QMenuBar { background-color: #f0f0f0; }")

        file_menu = menu_bar.addMenu("Archivo")
        #file_menu.setStyleSheet("QMenu { background-color: #ffffff; border: 1px solid #cccccc; }")

        self.new_action = QAction("Nuevo", self)
        self.open_action = QAction("Abrir", self)
        self.save_action = QAction("Guardar", self)
        self.save_as_action = QAction("Guardar como", self)
        self.close_action = QAction("Cerrar", self)
        self.exit_action = QAction("Salir", self)
        
        icon_path = "icons/" 
   
        self.new_action_toolbar = QAction(QIcon(os.path.join(icon_path, "new.png")), "Nuevo", self)
        self.open_action_toolbar = QAction(QIcon(os.path.join(icon_path, "open.png")), "Abrir", self)
        self.save_action_toolbar = QAction(QIcon(os.path.join(icon_path, "save.png")), "Guardar", self)
        self.save_as_action_toolbar = QAction(QIcon(os.path.join(icon_path, "save_as.png")), "Guardar como", self)
        self.close_action_toolbar = QAction(QIcon(os.path.join(icon_path, "close.png")), "Cerrar", self)
        
        self.new_action.triggered.connect(self.new_file)
        self.open_action.triggered.connect(self.open_file)
        self.save_action.triggered.connect(self.save_file)
        self.save_as_action.triggered.connect(self.save_file_as)
        self.close_action.triggered.connect(self.close_file) # La conexión ahora funcionará
        self.exit_action.triggered.connect(self.close)
        
        self.new_action_toolbar.triggered.connect(self.new_file)
        self.open_action_toolbar.triggered.connect(self.open_file)
        self.save_action_toolbar.triggered.connect(self.save_file)
        self.save_as_action_toolbar.triggered.connect(self.save_file_as)
        self.close_action_toolbar.triggered.connect(self.close_file) # La conexión ahora funcionará
        
        file_menu.addAction(self.new_action)
        file_menu.addSeparator()
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        lexico_menu = menu_bar.addMenu("Léxico")
        sintactico_menu = menu_bar.addMenu("Sintáctico")
        semantico_menu = menu_bar.addMenu("Semántico")

        # analizar_lexico_action = QAction("Analizar", self)
        # analizar_lexico_action.triggered.connect(self.ejecutar_analisis_lexico)


        analizar_lexico_action = QAction("Analizar", self)
        analizar_lexico_action.triggered.connect(lambda: self.ejecutar_analisis_lexico(cambiar_pestaña=True))

        #analizar_lexico_action = QAction("Analizar", self)
        ver_tokens_action = QAction("Ver Tokens", self)
        lexico_menu.addAction(analizar_lexico_action)

        lexico_menu.addSeparator()
        lexico_menu.addAction(ver_tokens_action)
        
        #analizar_sintactico_action = QAction("Analizar", self)
        #ver_ast_action = QAction("Ver Árbol Sintáctico", self)
        #sintactico_menu.addAction(analizar_sintactico_action)
        #sintactico_menu.addSeparator()
        #sintactico_menu.addAction(ver_ast_action)

        analizar_sintactico_action = QAction("Analizar", self)
        analizar_sintactico_action.triggered.connect(lambda: self.ejecutar_analisis_sintactico(cambiar_pestaña=True))
        
        ver_ast_action = QAction("Ver Árbol Sintáctico", self)
        ver_ast_action.triggered.connect(lambda: self.ejecutar_analisis_sintactico(cambiar_pestaña=True))
        
        sintactico_menu.addAction(analizar_sintactico_action)
        sintactico_menu.addSeparator()
        sintactico_menu.addAction(ver_ast_action)
        ###
        analizar_semantico_action = QAction("Analizar", self)
        analizar_semantico_action.triggered.connect(lambda: self.ejecutar_analisis_semantico(cambiar_pestaña=True)) # Conexión a nuevo método
        
        ver_tabla_simbolos_action = QAction("Ver Tabla de Símbolos", self)
        ver_tabla_simbolos_action.triggered.connect(lambda: self.ejecutar_analisis_semantico(cambiar_pestaña=True)) # Conexión a nuevo método
        
        semantico_menu.addAction(analizar_semantico_action)
        semantico_menu.addSeparator()
        semantico_menu.addAction(ver_tabla_simbolos_action)
  
        compilar_menu = menu_bar.addMenu("Compilar")
        compilar_action = QAction("Compilar", self)

        compilar_todo_action = QAction("Compilar Todo", self)
        ver_codigo_intermedio_action = QAction("Ver Código Intermedio", self)
        compilar_menu.addAction(compilar_action)
        compilar_menu.addAction(compilar_todo_action)
        compilar_menu.addSeparator()
        compilar_menu.addAction(ver_codigo_intermedio_action)
    
        ejecutar_menu = menu_bar.addMenu("Ejecutar")
        ejecutar_action = QAction("Ejecutar", self)
        ejecutar_paso_a_paso_action = QAction("Ejecutar Paso a Paso", self)
        ejecutar_menu.addAction(ejecutar_action)
        ejecutar_menu.addSeparator()
        ejecutar_menu.addAction(ejecutar_paso_a_paso_action)
        
        self.toolbar = QToolBar("Barra de Herramientas")
        self.toolbar.setStyleSheet("QToolBar { background-color: #e0e0e0; border: 1px solid #cccccc; spacing: 3px; }")
        self.toolbar.setMovable(False)  
        self.toolbar.setIconSize(QSize(24, 24))  
        self.addToolBar(self.toolbar)
  
        self.toolbar.addAction(self.new_action_toolbar)
        self.toolbar.addAction(self.open_action_toolbar)
        self.toolbar.addAction(self.save_action_toolbar)
        self.toolbar.addAction(self.save_as_action_toolbar)
        self.toolbar.addAction(self.close_action_toolbar)
        self.toolbar.addSeparator()
  
        compile_icon = QIcon(os.path.join(icon_path, "compiler.png")) if os.path.exists(os.path.join(icon_path, "compiler.png")) else QIcon()
        execute_icon = QIcon(os.path.join(icon_path, "execute.png")) if os.path.exists(os.path.join(icon_path, "execute.png")) else QIcon()
        
        compile_action_toolbar = QAction(compile_icon, "Compilar", self)
        execute_action_toolbar = QAction(execute_icon, "Ejecutar", self)
        
        compile_action_toolbar.triggered.connect(lambda: self.status_label.setText("Compilando..."))
        execute_action_toolbar.triggered.connect(lambda: self.status_label.setText("Ejecutando..."))
        
        self.toolbar.addAction(compile_action_toolbar)
        self.toolbar.addAction(execute_action_toolbar)
        
  
        self.container = QWidget()
        self.setCentralWidget(self.container)
    
    def update_line_status(self, line, column):
        self.cursor_position_label.setText(f"Línea: {line}   Columna: {column}")
    
    def load_editor(self):
        self.text_edit = CodeEditor()
        self.text_edit.set_main_window(self)  # Set reference to main window
        
        # Crear un contenedor para el editor y las barras de desplazamiento
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        # Añadir el layout horizontal para el editor y la barra vertical
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        h_layout.addWidget(self.text_edit)
        h_layout.addWidget(self.text_edit.vertical_scrollbar)
        
        editor_layout.addLayout(h_layout)
        editor_layout.addWidget(self.text_edit.horizontal_scrollbar)
        
        # Configurar las barras de desplazamiento
        self.text_edit.vertical_scrollbar.setStyleSheet("QScrollBar { width: 16px; }")
        self.text_edit.horizontal_scrollbar.setStyleSheet("QScrollBar { height: 16px; }")
        
        # Ocultar las barras de desplazamiento nativas del QPlainTextEdit
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Inicializar los rangos de las barras de desplazamiento
        self.text_edit.update_scrollbar_ranges()
        
        # Crear las pestañas principales
        self.tabs = QTabWidget()
        
        # Pestaña Léxico
        self.lexico_output = QTextEdit()
        self.lexico_output.setReadOnly(True)
        self.tabs.addTab(self.lexico_output, "Léxico")

        # Pestaña Sintáctico - CREAR SOLO UNA VEZ con el TreeWidget
        self.sintactico_widget = QWidget()
        sintactico_layout = QVBoxLayout(self.sintactico_widget)
        
        # Crear el TreeWidget para el AST
        self.tree_ast = QTreeWidget()
        self.tree_ast.setHeaderLabels(["Árbol de Sintaxis Abstracta (AST)"])
        sintactico_layout.addWidget(self.tree_ast)
        
        # Agregar la pestaña sintáctico con el widget que contiene el TreeWidget
        self.tabs.addTab(self.sintactico_widget, "Sintáctico")

        # Pestañas que serán creadas por los métodos crear_pestana_...
        # Se agregan marcadores de posición temporal o se confía en la creación dinámica
        # Para evitar problemas de orden al inicio, se agregan placeholders o se remueven después
        # Ya que los métodos crear_pestana_... reemplazarán estas pestañas.
        self.tabs.addTab(QLabel("Inicializando Pestaña Semántico..."), "Semántico")
        self.tabs.addTab(QLabel("Inicializando Pestaña Hash Table..."), "Hash Table")
        
        self.tabs.addTab(QLabel("Código Intermedio Resultados"), "Código Intermedio")

        # Alinear labels de pestañas vacías
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, QLabel):
                widget.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Crear las pestañas de errores
        self.errors_tabs = QTabWidget()

        # Errores Léxicos
        self.error_lexico = QTextEdit()
        self.error_lexico.setReadOnly(True)
        self.errors_tabs.addTab(self.error_lexico, "Errores Léxicos")

        # Errores Sintácticos
        self.error_sintactico = QTextEdit()
        self.error_sintactico.setReadOnly(True)
        self.errors_tabs.addTab(self.error_sintactico, "Errores Sintácticos")

        # Inicializar el widget de errores semánticos para que exista al inicio
        self.error_semantico = QTextEdit()
        self.error_semantico.setReadOnly(True)
        self.errors_tabs.addTab(self.error_semantico, "Errores Semánticos") # Añadido correctamente

        self.errors_tabs.addTab(QLabel("Resultados"), "Resultados")
        
        # Alinear labels de pestañas vacías
        for i in range(self.errors_tabs.count()):
            widget = self.errors_tabs.widget(i)
            if isinstance(widget, QLabel):
                widget.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Crear los splitters
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(editor_container)
        top_splitter.addWidget(self.tabs)
        top_splitter.setSizes([600, 600])

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.errors_tabs)
        main_splitter.setSizes([400, 250]) 

        # Crear el layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)

        # Crear el contenedor principal SOLO UNA VEZ
        self.container = QWidget()
        self.container.setLayout(main_layout)
        
        # Establecer como central widget SOLO UNA VEZ
        self.setCentralWidget(self.container)
        
        # Inicializar las pestañas dinámicas para que existan
        self.crear_pestana_semantico()
        self.crear_pestana_hash_table()
        self.crear_pestana_errores_semanticos()


        # Initialize cursor position
        self.text_edit.update_cursor_position()
    
    def new_file(self):
        self.load_editor()
        self.text_edit.clear()
        self.current_file = None
        self.status_label.setText("Nuevo archivo creado")
    
    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        if file_name:
            self.load_editor()
            with open(file_name, "r", encoding="utf-8", errors="replace") as file:
                self.text_edit.setText(file.read())
            self.current_file = file_name
            self.status_label.setText(f"Archivo abierto: {os.path.basename(file_name)}")
    
    def save_file(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8", errors="replace") as file:
                file.write(self.text_edit.toPlainText())
            self.status_label.setText(f"Guardado: {os.path.basename(self.current_file)}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Archivo", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        if file_name:
            with open(file_name, "w", encoding="utf-8", errors="replace") as file:
                file.write(self.text_edit.toPlainText())
            self.current_file = file_name
            self.status_label.setText(f"Guardado como: {os.path.basename(file_name)}")
    
    #########################NUEVO ANALISIS SINTACTICO###########################3
    def ejecutar_analisis_sintactico(self, cambiar_pestaña=False):
        try:
            # Verificar que el TreeWidget existe
            if not hasattr(self, 'tree_ast') or self.tree_ast is None:
                self.status_label.setText("Error: TreeWidget no disponible")
                return
                
            # Ejecutar análisis sintáctico
            ast, errores = analizador_sintactico("tokens.txt")
            
            # Limpiar el árbol antes de agregar nuevos elementos
            self.tree_ast.clear()
            
            # Mostrar resultados del AST
            if ast:
                def agregar_nodo(nodo_ast, padre_item):
                    try:
                        if nodo_ast.valor:
                            texto = f"{nodo_ast.tipo}: {nodo_ast.valor}"
                        else:
                            texto = f"{nodo_ast.tipo}"


                        item = QTreeWidgetItem([texto])
                        if padre_item:
                            padre_item.addChild(item)
                        else:
                            self.tree_ast.addTopLevelItem(item)

                        for hijo in nodo_ast.hijos:
                            agregar_nodo(hijo, item)
                            
                    except Exception as e:
                        print(f"Error al agregar nodo al árbol: {e}")

                agregar_nodo(ast, None)
                self.tree_ast.expandAll()
            else:
                self.tree_ast.addTopLevelItem(QTreeWidgetItem(["No se pudo generar el AST"]))

            # Mostrar errores sintácticos
            if errores:
                errores_texto = ""
                for i, error in enumerate(errores, 1):
                    errores_texto += f"{error}\n"
                self.error_sintactico.setPlainText(errores_texto)
            else:
                self.error_sintactico.setPlainText(" No se encontraron errores sintácticos")
            

            ast_texto = mostrar_ast_texto(ast) if ast else "No se pudo generar el AST debido a errores sintácticos"

            try:
                with open("ast.txt", "w", encoding="utf-8") as f_ast:
                    f_ast.write(ast_texto)
                
                with open("errores_sintacticos.txt", "w", encoding="utf-8") as f_errores:
                    if errores:
                        for error in errores:
                            f_errores.write(f"{error}\n")
                    else:
                        f_errores.write("No se encontraron errores sintácticos")
                        
                print("Archivos del análisis sintáctico guardados: ast.txt y errores_sintacticos.txt")

            except Exception as e:
                print(f"Error al guardar archivos del análisis sintáctico: {e}")

                        
            # Cambiar a la pestaña si se solicita
            if cambiar_pestaña:
                self.tabs.setCurrentWidget(self.sintactico_widget)  # Cambiar a sintactico_widget
                self.errors_tabs.setCurrentWidget(self.error_sintactico)
            
            # Actualizar status
            if errores:
                self.status_label.setText(f"Análisis sintáctico completado con {len(errores)} errores")
            else:
                self.status_label.setText("Análisis sintáctico completado exitosamente")
            
            # Mostrar resumen en consola
            print(f"Análisis sintáctico completado:")
            print(f"- AST generado: {'Sí' if ast else 'No'}")
            print(f"- Errores encontrados: {len(errores)}")
            
        except Exception as e:
            error_msg = f"Error durante el análisis sintáctico: {str(e)}"
            # Verificar que los widgets existen antes de usarlos
            if hasattr(self, 'error_sintactico') and self.error_sintactico is not None:
                self.error_sintactico.setPlainText(error_msg)
            if hasattr(self, 'tree_ast') and self.tree_ast is not None:
                self.tree_ast.clear()
                self.tree_ast.addTopLevelItem(QTreeWidgetItem([error_msg]))
            self.status_label.setText("Error en análisis sintáctico")
            print(error_msg)
            import traceback
            traceback.print_exc()

    #################################MÉTODOS DEL ANÁLISIS SEMÁNTICO############################

    def ejecutar_analisis_semantico(self, cambiar_pestaña=False):
        """Ejecuta el análisis semántico completo"""
        try:
            # Primero ejecutar análisis sintáctico para obtener el AST
            ast, errores_sint = analizador_sintactico("tokens.txt")
            
            if not ast:
                self.status_label.setText("No se puede ejecutar análisis semántico sin AST válido")
                # Mostrar errores sintácticos si hay
                if errores_sint:
                    errores_texto = "\n".join(errores_sint)
                    self.error_sintactico.setPlainText(errores_texto)
                    self.errors_tabs.setCurrentWidget(self.error_sintactico)
                return
            
            # Importar el analizador semántico
            try:
                from analizador_semantico import ejecutar_analisis_semantico, NodoAnotado
            except ImportError:
                self.status_label.setText("Error: No se encontró 'analizador_semantico.py'")
                return
            
            # Ejecutar análisis semántico
            ast_anotado, tabla_simbolos, errores_sem = ejecutar_analisis_semantico(ast)
            
            # Crear pestañas si no existen (ya se llamaron en load_editor, pero se verifica)
            if not hasattr(self, 'tree_semantico') or self.tree_semantico is None:
                self.crear_pestana_semantico()
            if not hasattr(self, 'tabla_simbolos_widget') or self.tabla_simbolos_widget is None:
                self.crear_pestana_hash_table()
            if not hasattr(self, 'error_semantico') or self.error_semantico is None:
                self.crear_pestana_errores_semanticos()

            # ===== MOSTRAR ÁRBOL ANOTADO EN PESTAÑA SEMÁNTICO =====
            self.tree_semantico.clear()
            
            if ast_anotado:
                def agregar_nodo_anotado(nodo_ast, padre_item):
                    try:
                        # Construir texto del nodo
                        texto = f"{nodo_ast.tipo}"
                        if nodo_ast.valor:
                            texto += f": {nodo_ast.valor}"
                        
                        # Agregar tipo de dato si existe
                        if hasattr(nodo_ast, 'tipo_dato') and nodo_ast.tipo_dato:
                            texto += f" | Tipo: {nodo_ast.tipo_dato}"
                        
                        # Agregar valor calculado si existe
                        if hasattr(nodo_ast, 'valor_calculado') and nodo_ast.valor_calculado is not None:
                            texto += f" | Valor: {nodo_ast.valor_calculado}"
                        
                        item = QTreeWidgetItem([texto])
                        
                        if padre_item:
                            padre_item.addChild(item)
                        else:
                            self.tree_semantico.addTopLevelItem(item)
                        
                        for hijo in nodo_ast.hijos:
                            agregar_nodo_anotado(hijo, item)
                            
                    except Exception as e:
                        print(f"Error al agregar nodo anotado: {e}")
                
                agregar_nodo_anotado(ast_anotado, None)
                self.tree_semantico.expandAll()
            else:
                self.tree_semantico.addTopLevelItem(QTreeWidgetItem(["No se pudo generar el AST anotado"]))
            
            # ===== MOSTRAR TABLA DE SÍMBOLOS EN PESTAÑA HASH TABLE =====
            self.tabla_simbolos_widget.setRowCount(0)
            
            simbolos = tabla_simbolos.listar_simbolos()
            if simbolos:
                self.tabla_simbolos_widget.setRowCount(len(simbolos))
                
                for i, simbolo in enumerate(simbolos):
                    # Nombre
                    self.tabla_simbolos_widget.setItem(i, 0, QTableWidgetItem(simbolo.nombre))
                    
                    # Tipo
                    self.tabla_simbolos_widget.setItem(i, 1, QTableWidgetItem(simbolo.tipo or ""))
                    
                    
                    
                    # Ámbito
                    self.tabla_simbolos_widget.setItem(i, 2, QTableWidgetItem(simbolo.ambito))
                    
                    # Línea
                    linea_columna_str = f"{simbolo.linea}:{simbolo.columna}"
                    self.tabla_simbolos_widget.setItem(i, 3, QTableWidgetItem(linea_columna_str))
                    
            # ===== MOSTRAR ERRORES SEMÁNTICOS =====
            if errores_sem:
                errores_texto = ""
                for error in errores_sem:
                    # CAMBIO AQUÍ: Los errores ya tienen formato correcto con línea y columna
                    errores_texto += f"{error}\n"
                self.error_semantico.setPlainText(errores_texto)
            else:
                self.error_semantico.setPlainText("No se encontraron errores semánticos")
        
            
            # Guardar resultados en archivos
            try:
                # Guardar AST anotado
                with open("ast_anotado.txt", "w", encoding="utf-8") as f:
                    f.write(self.generar_texto_ast_anotado(ast_anotado))
                
                # Guardar tabla de símbolos
                # Guardar tabla de símbolos
                with open("tabla_simbolos.txt", "w", encoding="utf-8") as f:
                    f.write("TABLA DE SÍMBOLOS\n")
                    f.write("="*100 + "\n")
                    f.write(f"{'SCOPE':<10} {'LVL':<5} {'NAME':<15} {'TYPE':<10} {'OFFSET':<10} {'COUNT':<7} {'LINES':<30}\n")
                    f.write("-"*100 + "\n")

                    offset_counter = 0  # 🚀 OFFSET desde 0

                    for simbolo in simbolos:
                        scope = "block"
                        lvl = 1
                        name = simbolo.nombre
                        tipo = simbolo.tipo
                        offset = offset_counter
                        count = len(simbolo.ubicaciones)
                        lines = ", ".join([str(l) for l, c in simbolo.ubicaciones])

                        f.write(
                            f"{scope:<10} {lvl:<5} {name:<15} {tipo:<10} "
                            f"{offset:<10} {count:<7} {lines:<30}\n"
                        )

                        offset_counter += 1

                # Guardar errores semánticos
                with open("errores_semanticos.txt", "w", encoding="utf-8") as f:
                    if errores_sem:
                        for error in errores_sem:
                            f.write(f"{error}\n")
                    else:
                        f.write("No se encontraron errores semánticos\n")
                
                print("Archivos del análisis semántico guardados exitosamente")
            
            except Exception as e:
                print(f"Error al guardar archivos del análisis semántico: {e}")
            
            # Cambiar a pestañas si se solicita
            if cambiar_pestaña:
                self.tabs.setCurrentWidget(self.semantico_widget)
                self.errors_tabs.setCurrentWidget(self.error_semantico)
            
            # Actualizar status
            if errores_sem:
                self.status_label.setText(f"Análisis semántico completado con {len(errores_sem)} errores")
            else:
                self.status_label.setText("Análisis semántico completado exitosamente")
            
            
        except Exception as e:
            error_msg = f"Error durante el análisis semántico: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.status_label.setText("Error en análisis semántico")


    def crear_pestana_semantico(self):
        """Crea la pestaña de semántico con el TreeWidget para AST anotado"""
        self.semantico_widget = QWidget()
        semantico_layout = QVBoxLayout(self.semantico_widget)
        
        self.tree_semantico = QTreeWidget()
        self.tree_semantico.setHeaderLabels(["Árbol de Sintaxis Abstracta Anotado (con Tipos y Valores)"])
        semantico_layout.addWidget(self.tree_semantico)
        
        # Reemplazar la pestaña existente
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Semántico":
                self.tabs.removeTab(i)
                break
        
        self.tabs.insertTab(2, self.semantico_widget, "Semántico")


    def crear_pestana_hash_table(self):
        """Crea la pestaña de tabla de símbolos (hash table)"""
        # Se eliminó la importación local ya que se agregó a las importaciones principales
        
        self.hash_table_widget = QWidget()
        hash_layout = QVBoxLayout(self.hash_table_widget)
        
        # Crear tabla
        self.tabla_simbolos_widget = QTableWidget()
        self.tabla_simbolos_widget.setColumnCount(4)
        self.tabla_simbolos_widget.setHorizontalHeaderLabels(["Nombre", "Tipo", "Ámbito", "Línea"])
        
        # Ajustar tamaño de columnas
        header = self.tabla_simbolos_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        hash_layout.addWidget(self.tabla_simbolos_widget)
        
        # Reemplazar la pestaña existente
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Hash Table":
                self.tabs.removeTab(i)
                break
        
        self.tabs.insertTab(3, self.hash_table_widget, "Hash Table")


    def crear_pestana_errores_semanticos(self):
        """Crea la pestaña de errores semánticos"""
        if not hasattr(self, 'error_semantico') or self.error_semantico is None:
            self.error_semantico = QTextEdit()
            self.error_semantico.setReadOnly(True)
        
        # Reemplazar la pestaña existente
        for i in range(self.errors_tabs.count()):
            if self.errors_tabs.tabText(i) == "Errores Semánticos":
                self.errors_tabs.removeTab(i)
                break
        
        self.errors_tabs.insertTab(2, self.error_semantico, "Errores Semánticos")


    def generar_texto_ast_anotado(self, nodo, nivel=0):
        """Genera representación en texto del AST anotado"""
        if nodo is None:
            return ""
        
        indentacion = "  " * nivel
        resultado = f"{indentacion}{nodo.tipo}"
        
        if hasattr(nodo, 'valor') and nodo.valor:
            resultado += f": {nodo.valor}"
        
        if hasattr(nodo, 'tipo_dato') and nodo.tipo_dato:
            resultado += f" | Tipo: {nodo.tipo_dato}"
        
        if hasattr(nodo, 'valor_calculado') and nodo.valor_calculado is not None:
            resultado += f" | Valor: {nodo.valor_calculado}"
        
        resultado += "\n"
        
        for hijo in nodo.hijos:
            resultado += self.generar_texto_ast_anotado(hijo, nivel + 1)
        
        return resultado
    
    #################################FIN MÉTODOS SEMÁNTICO############################

    def close_file(self):
        self.setCentralWidget(QWidget())
        self.current_file = None
        self.status_label.setText("Archivo cerrado")
        self.cursor_position_label.setText("Línea: 1     Columna: 1")

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Courier New", 11)
    app.setStyleSheet("""
        QLabel {
            background-color: white;
            font-family: Courier New;
            font-size:10pt;
        }
        QPlainTextEdit{
            font-family: Consolas;
            font-size:12pt;
        }
        QScrollBar:vertical {
            border: 1px solid #999999;
            background: white;
            width: 16px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar:horizontal {
            border: 1px solid #999999;
            background: white;
            height: 16px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #c1c1c1;
            min-height: 20px;
            border-radius: 2px;
        }
        QScrollBar::handle:horizontal {
            background: #c1c1c1;
            min-width: 20px;
            border-radius: 2px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
    """)

    app.setFont(font)

    window = CompilerIDE()
    window.show()
    sys.exit(app.exec())