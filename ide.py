from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QTabWidget, QSplitter, QMenuBar, QMenu, 
    QFileDialog, QLabel, QPlainTextEdit, QHBoxLayout, QToolBar, QStatusBar
)
from PyQt6.QtGui import QAction, QColor, QPainter, QTextFormat, QFontMetrics, QIcon
from PyQt6.QtCore import QRect, Qt, QSize, pyqtSlot
import sys
import os


from PyQt6.QtGui import QFont

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


class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilador IDE")
        self.setGeometry(100, 100, 1000, 700)
        self.current_file = None
        
        self.initUI()
    
    def initUI(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_label = QLabel("Listo")
        status_bar.addWidget(self.status_label, 1)
        
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("QMenuBar { background-color: #f0f0f0; }")
        
        file_menu = menu_bar.addMenu("Archivo")
        file_menu.setStyleSheet("QMenu { background-color: #ffffff; border: 1px solid #cccccc; }")
        
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
        
        analizar_lexico_action = QAction("Analizar", self)
        ver_tokens_action = QAction("Ver Tokens", self)
        lexico_menu.addAction(analizar_lexico_action)
        lexico_menu.addSeparator()
        lexico_menu.addAction(ver_tokens_action)
        
        analizar_sintactico_action = QAction("Analizar", self)
        ver_ast_action = QAction("Ver Árbol Sintáctico", self)
        sintactico_menu.addAction(analizar_sintactico_action)
        sintactico_menu.addSeparator()
        sintactico_menu.addAction(ver_ast_action)
        
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
    
    def load_editor(self):
        self.text_edit = CodeEditor()  
        self.tabs = QTabWidget()
        self.tabs.addTab(QLabel("Salida Léxica"), "Léxico")
        self.tabs.addTab(QLabel("Salida Sintáctica"), "Sintáctico")
        self.tabs.addTab(QLabel("Salida Semántica"), "Semántico")
        self.tabs.addTab(QLabel("Hash Table Resultados"), "Hash Table")
        self.tabs.addTab(QLabel("Código Intermedio Resultados"), "Código Intermedio")

        for i in range(self.tabs.count()):
            label = self.tabs.widget(i)
            label.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.errors_tabs = QTabWidget()
        self.errors_tabs.addTab(QLabel("Errores Léxicos"), "Errores Léxicos")
        self.errors_tabs.addTab(QLabel("Errores Sintácticos"), "Errores Sintácticos")
        self.errors_tabs.addTab(QLabel("Errores Semánticos"), "Errores Semánticos")
        self.errors_tabs.addTab(QLabel("Resultados"), "Resultados")
        
        for i in range(self.errors_tabs.count()):
            label = self.errors_tabs.widget(i)
            label.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.text_edit)
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
    """)
    app.setFont(font)

    window = CompilerIDE()
    window.show()
    sys.exit(app.exec())


    