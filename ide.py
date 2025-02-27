from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QTabWidget, QSplitter, QMenuBar, QMenu, QFileDialog, QLabel
)
from PyQt6.QtGui import QAction
import sys

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
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Escriba aquí...")
        
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
