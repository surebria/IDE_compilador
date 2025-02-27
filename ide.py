from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton, QTabWidget, QSplitter, QToolBar
)
from PyQt6.QtGui import QAction
import sys

class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilador")
        self.setGeometry(100, 100, 900, 600)
        
        self.initUI()
    
    def initUI(self):
        # Crear barra de herramientas
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Archivo")
        
        new_action = QAction("Nuevo", self)
        open_action = QAction("Abrir", self)
        save_action = QAction("Guardar", self)
        save_as_action = QAction("Guardar como", self)
        
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        
        # Editor de texto
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Escriba aquí...")
        
        # Sección de análisis del compilador
        self.tabs = QTabWidget()
        self.tabs.addTab(QTextEdit(), "Léxico")
        self.tabs.addTab(QTextEdit(), "Sintáctico")
        self.tabs.addTab(QTextEdit(), "Semántico")
        self.tabs.addTab(QTextEdit(), "Hash Table")
        self.tabs.addTab(QTextEdit(), "Código Intermedio")
        
        # Consola de errores y resultados
        self.errors_tabs = QTabWidget()
        self.errors_tabs.addTab(QTextEdit(), "Errores Léxicos")
        self.errors_tabs.addTab(QTextEdit(), "Errores Sintácticos")
        self.errors_tabs.addTab(QTextEdit(), "Errores Semánticos")
        self.errors_tabs.addTab(QTextEdit(), "Resultados")
        
        # Layout con QSplitter
        splitter = QSplitter()
        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.tabs)
        splitter.setSizes([300, 600])
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.errors_tabs)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerIDE()
    window.show()
    sys.exit(app.exec())
