from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QMenuBar, QMenu, QVBoxLayout, 
    QWidget, QPushButton, QFileDialog, QTabWidget
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
        # Editor de texto
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Escriba aquí...")
        
        # Crear Tabs para fases del compilador
        self.tabs = QTabWidget()
        self.tabs.addTab(QTextEdit(), "Léxico")
        self.tabs.addTab(QTextEdit(), "Sintáctico")
        self.tabs.addTab(QTextEdit(), "Semántico")
        self.tabs.addTab(QTextEdit(), "Código Intermedio")
        self.tabs.addTab(QTextEdit(), "Ejecución")
        
        # Botones de acción
        self.compile_button = QPushButton("Compilar")
        self.lexical_button = QPushButton("Análisis Léxico")
        self.syntax_button = QPushButton("Análisis Sintáctico")
        self.semantic_button = QPushButton("Análisis Semántico")
        self.intermediate_button = QPushButton("Código Intermedio")
        self.execute_button = QPushButton("Ejecutar")
        
        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.tabs)
        layout.addWidget(self.compile_button)
        layout.addWidget(self.lexical_button)
        layout.addWidget(self.syntax_button)
        layout.addWidget(self.semantic_button)
        layout.addWidget(self.intermediate_button)
        layout.addWidget(self.execute_button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Menú
        self.createMenu()
    
    def createMenu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        compile_menu = menu_bar.addMenu("Compilar")
        
        # Acciones del menú
        open_action = QAction("Abrir", self)
        save_action = QAction("Guardar", self)
        save_as_action = QAction("Guardar como", self)
        close_action = QAction("Cerrar", self)
        
        lex_action = QAction("Análisis Léxico", self)
        syn_action = QAction("Análisis Sintáctico", self)
        sem_action = QAction("Análisis Semántico", self)
        int_action = QAction("Código Intermedio", self)
        exe_action = QAction("Ejecutar", self)
        
        # Agregar acciones al menú
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addAction(close_action)
        
        compile_menu.addAction(lex_action)
        compile_menu.addAction(syn_action)
        compile_menu.addAction(sem_action)
        compile_menu.addAction(int_action)
        compile_menu.addAction(exe_action)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerIDE()
    window.show()
    sys.exit(app.exec())
