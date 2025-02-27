from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QTabWidget, QSplitter, QMenuBar, QMenu, 
    QFileDialog, QLabel, QPlainTextEdit, QHBoxLayout
)
from PyQt6.QtGui import QAction, QColor, QPainter, QTextFormat, QFontMetrics
from PyQt6.QtCore import QRect, Qt, QSize, pyqtSlot
import sys

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
        self.setWindowTitle("Compilador")
        self.setGeometry(100, 100, 900, 600)
        self.current_file = None  # Almacena el archivo actual
        
        self.initUI()
    
    def initUI(self):
        # Crear barra de menú
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Archivo")
        
        new_action = QAction("Nuevo", self)
        open_action = QAction("Abrir", self)
        save_action = QAction("Guardar", self)
        save_as_action = QAction("Guardar como", self)
        close_action = QAction("Cerrar", self)
        
        new_action.triggered.connect(self.new_file)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        save_as_action.triggered.connect(self.save_file_as)
        close_action.triggered.connect(self.close_file)
        
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addAction(close_action)
        
        # Contenedor inicial vacío
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        # Leyenda de estado
        self.status_label = QLabel("", self)
        self.statusBar().addWidget(self.status_label)
    
    def load_editor(self):
        self.text_edit = CodeEditor()  # Using our custom CodeEditor instead of QTextEdit
        
        self.tabs = QTabWidget()
        self.tabs.addTab(QTextEdit(), "Léxico")
        self.tabs.addTab(QTextEdit(), "Sintáctico")
        self.tabs.addTab(QTextEdit(), "Semántico")
        self.tabs.addTab(QTextEdit(), "Hash Table")
        self.tabs.addTab(QTextEdit(), "Código Intermedio")
        
        self.errors_tabs = QTabWidget()
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
    
    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        if file_name:
            self.load_editor()
            with open(file_name, "r", encoding="utf-8") as file:
                self.text_edit.setText(file.read())
            self.current_file = file_name
    
    def save_file(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.text_edit.toPlainText())
            self.status_label.setText("Guardado")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Archivo", "", "Archivos de Texto (*.txt);;Todos los Archivos (*)")
        if file_name:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(self.text_edit.toPlainText())
            self.current_file = file_name
            self.status_label.setText("Guardado")
    
    def close_file(self):
        self.setCentralWidget(QWidget())
        self.current_file = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerIDE()
    window.show()
    sys.exit(app.exec())