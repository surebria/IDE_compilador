
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QTabWidget, QSplitter, QMenuBar, QMenu, 
    QFileDialog, QLabel, QPlainTextEdit, QHBoxLayout, QToolBar, QStatusBar, QScrollBar
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
        
        self.initUI()

    def ejecutar_analisis_lexico(self, cambiar_pestaña=False):
        if not hasattr(self, 'text_edit') or self.text_edit is None:
            return
            
        texto = self.text_edit.toPlainText()
        tokens = analizador_lexico(texto)
        
        salida = ""
        salida_errores = ""
        
        for token in tokens:
            if token.tipo == 'ERROR':
                salida_errores += f"{token}\n"
            else:
                salida += f"{token}\n"
        
        self.lexico_output.setPlainText(salida)
        self.error_lexico.setPlainText(salida_errores)

        # Guardar en archivos de texto
        try:
            with open("tokens.txt", "w", encoding="utf-8") as f_tokens:
                f_tokens.write(salida)
            
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
        self.close_action.triggered.connect(self.close_file)
        self.exit_action.triggered.connect(self.close)
        
        self.new_action_toolbar.triggered.connect(self.new_file)
        self.open_action_toolbar.triggered.connect(self.open_file)
        self.save_action_toolbar.triggered.connect(self.save_file)
        self.save_as_action_toolbar.triggered.connect(self.save_file_as)
        self.close_action_toolbar.triggered.connect(self.close_file)
        
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
        ver_ast_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.sintactico_output))
        
        sintactico_menu.addAction(analizar_sintactico_action)
        sintactico_menu.addSeparator()
        sintactico_menu.addAction(ver_ast_action)
        ###
        analizar_semantico_action = QAction("Analizar", self)
        ver_tabla_simbolos_action = QAction("Ver Tabla de Símbolos", self)
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
        #self.setCentralWidget(self.text_edit)
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
        
        self.tabs = QTabWidget()
        #self.tabs.addTab(QLabel("Salida Léxica"), "Léxico")
        self.lexico_output = QTextEdit()
        self.lexico_output.setReadOnly(True)
        self.tabs.addTab(self.lexico_output, "Léxico")

        #self.tabs.addTab(QLabel("Salida Sintáctica"), "Sintáctico")

        ##esto es el reemplazo 
        self.sintactico_output = QTextEdit()
        self.sintactico_output.setReadOnly(True)
        self.tabs.addTab(self.sintactico_output, "Sintáctico")


        self.tabs.addTab(QLabel("Salida Semántica"), "Semántico")
        self.tabs.addTab(QLabel("Hash Table Resultados"), "Hash Table")
        self.tabs.addTab(QLabel("Código Intermedio Resultados"), "Código Intermedio")

        for i in range(self.tabs.count()):
            label = self.tabs.widget(i)
            label.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.errors_tabs = QTabWidget()

        self.error_lexico = QTextEdit()
        self.error_lexico.setReadOnly(True)
        self.errors_tabs.addTab(self.error_lexico, "Errores Léxicos")

        #self.errors_tabs.addTab(QLabel("Errores Léxicos"), "Errores Léxicos")
        #self.errors_tabs.addTab(QLabel("Errores Sintácticos"), "Errores Sintácticos")
        ##lo de abajo es el reemplazo
        self.error_sintactico = QTextEdit()
        self.error_sintactico.setReadOnly(True)
        self.errors_tabs.addTab(self.error_sintactico, "Errores Sintácticos")


        self.errors_tabs.addTab(QLabel("Errores Semánticos"), "Errores Semánticos")
        self.errors_tabs.addTab(QLabel("Resultados"), "Resultados")
        
        for i in range(self.errors_tabs.count()):
            label = self.errors_tabs.widget(i)
            label.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(editor_container)  # Usar el contenedor del editor en lugar de text_edit directamente
        top_splitter.addWidget(self.tabs)
        top_splitter.setSizes([600, 600])

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.errors_tabs)
        main_splitter.setSizes([400, 250]) 

        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)

        self.container = QWidget()
        self.container.setLayout(main_layout)
        self.setCentralWidget(self.container)
        
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
            # Ejecutar análisis sintáctico
            ast, errores = analizador_sintactico("tokens.txt")
            
            # Mostrar resultados del AST
            if ast:
                ast_texto = mostrar_ast_texto(ast)
                self.sintactico_output.setPlainText(ast_texto)
            else:
                self.sintactico_output.setPlainText("No se pudo generar el AST debido a errores sintácticos")
            
            # Mostrar errores sintácticos
            if errores:
                errores_texto = "ERRORES SINTÁCTICOS ENCONTRADOS:\n\n"
                for i, error in enumerate(errores, 1):
                    errores_texto += f"Error {i}: {error}\n"
                self.error_sintactico.setPlainText(errores_texto)
            else:
                self.error_sintactico.setPlainText("✓ No se encontraron errores sintácticos")
            
            # Guardar resultados en archivos
            try:
                with open("ast.txt", "w", encoding="utf-8") as f_ast:
                    if ast:
                        f_ast.write(ast_texto)
                    else:
                        f_ast.write("No se pudo generar el AST debido a errores sintácticos")
                
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
                self.tabs.setCurrentWidget(self.sintactico_output)
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
            self.sintactico_output.setPlainText(error_msg)
            self.error_sintactico.setPlainText(error_msg)
            self.status_label.setText("Error en análisis sintáctico")
            print(error_msg)
            import traceback
            traceback.print_exc()

#################################TERMINA############################
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
    