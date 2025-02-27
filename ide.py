from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QTabWidget, QSplitter, QMenuBar, QMenu, 
    QFileDialog, QLabel, QPlainTextEdit, QHBoxLayout, QToolBar, QStatusBar
)
from PyQt6.QtGui import QAction, QColor, QPainter, QTextFormat, QFontMetrics, QIcon
from PyQt6.QtCore import QRect, Qt, QSize, pyqtSlot
import sys
import os

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Setting placeholder text
        self.setPlaceholderText("Escriba aquí...")

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.lightGray).lighter(130)
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


class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilador IDE")
        self.setGeometry(100, 100, 1000, 700)
        self.current_file = None  # Almacena el archivo actual
        
        self.initUI()
    
    def initUI(self):
        # Configurar barra de estado con mejor diseño
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_label = QLabel("Listo")
        status_bar.addWidget(self.status_label, 1)
        
        # Crear barra de menú con estilo
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("QMenuBar { background-color: #f0f0f0; }")
        
        # Menú Archivo
        file_menu = menu_bar.addMenu("Archivo")
        file_menu.setStyleSheet("QMenu { background-color: #ffffff; border: 1px solid #cccccc; }")
        
        # Crear acciones para Archivo
        self.new_action = QAction("Nuevo", self)
        self.open_action = QAction("Abrir", self)
        self.save_action = QAction("Guardar", self)
        self.save_as_action = QAction("Guardar como", self)
        self.close_action = QAction("Cerrar", self)
        self.exit_action = QAction("Salir", self)
        
        # Asignar iconos solo para la barra de herramientas
        icon_path = "icons/"  # Cambia esto a la ruta real donde están tus iconos
        
        # Crear copias de las acciones sin iconos para los menús
        self.new_action_toolbar = QAction(QIcon(os.path.join(icon_path, "new.png")), "Nuevo", self)
        self.open_action_toolbar = QAction(QIcon(os.path.join(icon_path, "open.png")), "Abrir", self)
        self.save_action_toolbar = QAction(QIcon(os.path.join(icon_path, "save.png")), "Guardar", self)
        self.save_as_action_toolbar = QAction(QIcon(os.path.join(icon_path, "save_as.png")), "Guardar como", self)
        self.close_action_toolbar = QAction(QIcon(os.path.join(icon_path, "close.png")), "Cerrar", self)
        
        # Conectar acciones del menú con funciones
        self.new_action.triggered.connect(self.new_file)
        self.open_action.triggered.connect(self.open_file)
        self.save_action.triggered.connect(self.save_file)
        self.save_as_action.triggered.connect(self.save_file_as)
        self.close_action.triggered.connect(self.close_file)
        self.exit_action.triggered.connect(self.close)
        
        # Conectar acciones de la barra de herramientas con funciones
        self.new_action_toolbar.triggered.connect(self.new_file)
        self.open_action_toolbar.triggered.connect(self.open_file)
        self.save_action_toolbar.triggered.connect(self.save_file)
        self.save_as_action_toolbar.triggered.connect(self.save_file_as)
        self.close_action_toolbar.triggered.connect(self.close_file)
        
        # Agregar acciones al menú Archivo con separadores
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
        
        # Crear menús adicionales
        lexico_menu = menu_bar.addMenu("Léxico")
        sintactico_menu = menu_bar.addMenu("Sintáctico")
        semantico_menu = menu_bar.addMenu("Semántico")
        
        # Menú Léxico
        analizar_lexico_action = QAction("Analizar", self)
        ver_tokens_action = QAction("Ver Tokens", self)
        lexico_menu.addAction(analizar_lexico_action)
        lexico_menu.addSeparator()
        lexico_menu.addAction(ver_tokens_action)
        
        # Menú Sintáctico
        analizar_sintactico_action = QAction("Analizar", self)
        ver_ast_action = QAction("Ver Árbol Sintáctico", self)
        sintactico_menu.addAction(analizar_sintactico_action)
        sintactico_menu.addSeparator()
        sintactico_menu.addAction(ver_ast_action)
        
        # Menú Semántico
        analizar_semantico_action = QAction("Analizar", self)
        ver_tabla_simbolos_action = QAction("Ver Tabla de Símbolos", self)
        semantico_menu.addAction(analizar_semantico_action)
        semantico_menu.addSeparator()
        semantico_menu.addAction(ver_tabla_simbolos_action)
        
        # Menú Compilar
        compilar_menu = menu_bar.addMenu("Compilar")
        compilar_action = QAction("Compilar", self)
        compilar_todo_action = QAction("Compilar Todo", self)
        ver_codigo_intermedio_action = QAction("Ver Código Intermedio", self)
        compilar_menu.addAction(compilar_action)
        compilar_menu.addAction(compilar_todo_action)
        compilar_menu.addSeparator()
        compilar_menu.addAction(ver_codigo_intermedio_action)
        
        # Menú Ejecutar
        ejecutar_menu = menu_bar.addMenu("Ejecutar")
        ejecutar_action = QAction("Ejecutar", self)
        ejecutar_paso_a_paso_action = QAction("Ejecutar Paso a Paso", self)
        ejecutar_menu.addAction(ejecutar_action)
        ejecutar_menu.addSeparator()
        ejecutar_menu.addAction(ejecutar_paso_a_paso_action)
        
        # Crear barra de herramientas con estilo
        self.toolbar = QToolBar("Barra de Herramientas")
        self.toolbar.setStyleSheet("QToolBar { background-color: #e0e0e0; border: 1px solid #cccccc; spacing: 3px; }")
        self.toolbar.setMovable(False)  
        self.toolbar.setIconSize(QSize(24, 24))  
        self.addToolBar(self.toolbar)
        
        # Agregar acciones a la barra de herramientas
        self.toolbar.addAction(self.new_action_toolbar)
        self.toolbar.addAction(self.open_action_toolbar)
        self.toolbar.addAction(self.save_action_toolbar)
        self.toolbar.addAction(self.save_as_action_toolbar)
        self.toolbar.addAction(self.close_action_toolbar)
        self.toolbar.addSeparator()
        
        # Añadir acciones de compilar y ejecutar a la barra de herramientas
        compile_icon = QIcon(os.path.join(icon_path, "compiler.png")) if os.path.exists(os.path.join(icon_path, "compiler.png")) else QIcon()
        execute_icon = QIcon(os.path.join(icon_path, "execute.png")) if os.path.exists(os.path.join(icon_path, "execute.png")) else QIcon()
        
        compile_action_toolbar = QAction(compile_icon, "Compilar", self)
        execute_action_toolbar = QAction(execute_icon, "Ejecutar", self)
        
        compile_action_toolbar.triggered.connect(lambda: self.status_label.setText("Compilando..."))
        execute_action_toolbar.triggered.connect(lambda: self.status_label.setText("Ejecutando..."))
        
        self.toolbar.addAction(compile_action_toolbar)
        self.toolbar.addAction(execute_action_toolbar)
        
        # Contenedor inicial vacío
        self.container = QWidget()
        self.setCentralWidget(self.container)
    
    def load_editor(self):
        self.text_edit = CodeEditor()  
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #cccccc; } QTabBar::tab { background-color: #e0e0e0; padding: 5px; } QTabBar::tab:selected { background-color: #f0f0f0; }")
        self.tabs.addTab(QTextEdit(), "Léxico")
        self.tabs.addTab(QTextEdit(), "Sintáctico")
        self.tabs.addTab(QTextEdit(), "Semántico")
        self.tabs.addTab(QTextEdit(), "Hash Table")
        self.tabs.addTab(QTextEdit(), "Código Intermedio")
        
        self.errors_tabs = QTabWidget()
        self.errors_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #cccccc; } QTabBar::tab { background-color: #e0e0e0; padding: 5px; } QTabBar::tab:selected { background-color: #f0f0f0; }")
        self.errors_tabs.addTab(QTextEdit(), "Errores Léxicos")
        self.errors_tabs.addTab(QTextEdit(), "Errores Sintácticos")
        self.errors_tabs.addTab(QTextEdit(), "Errores Semánticos")
        self.errors_tabs.addTab(QTextEdit(), "Resultados")
        
        splitter = QSplitter()
        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.tabs)
        splitter.setSizes([300, 600])
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.errors_tabs)
        
        self.container = QWidget()
        self.container.setLayout(main_layout)
        self.setCentralWidget(self.container)
    
    def new_file(self):
        self.load_editor()
        self.text_edit.clear()
        self.current_file = None
        self.status_label.setText("Nuevo archivo creado")
    
    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        if file_name:
            self.load_editor()
            with open(file_name, "r", encoding="utf-8") as file:
                self.text_edit.setText(file.read())
            self.current_file = file_name
            self.status_label.setText(f"Archivo abierto: {os.path.basename(file_name)}")
    
    def save_file(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.text_edit.toPlainText())
            self.status_label.setText(f"Guardado: {os.path.basename(self.current_file)}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Archivo", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        if file_name:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(self.text_edit.toPlainText())
            self.current_file = file_name
            self.status_label.setText(f"Guardado como: {os.path.basename(file_name)}")
    
    def close_file(self):
        self.setCentralWidget(QWidget())
        self.current_file = None
        self.status_label.setText("Archivo cerrado")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  
    window = CompilerIDE()
    window.show()
    sys.exit(app.exec())