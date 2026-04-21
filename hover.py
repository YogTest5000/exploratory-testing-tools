import os
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox
)
from PyQt5.QtCore import Qt


class FileBrowserApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder File Browser")
        self.resize(600, 400)

        self.selected_folder = ""

        self.init_ui()

    def init_ui(self):
        # Button
        self.browse_button = QPushButton("Browse Folder")
        self.browse_button.clicked.connect(self.browse_folder)

        # Label to show selected/hovered file
        self.file_label = QLabel("Selected file name will appear here")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet("""
            QLabel {
                border: 1px solid #999;
                padding: 8px;
                font-size: 14px;
                background-color: #f5f5f5;
            }
        """)

        # List widget to display files
        self.file_list = QListWidget()
        self.file_list.setMouseTracking(True)  # enables hover tracking
        self.file_list.itemEntered.connect(self.on_item_hovered)
        self.file_list.itemClicked.connect(self.on_item_clicked)

        # Layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.browse_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.file_list)
        main_layout.addWidget(self.file_label)

        self.setLayout(main_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.selected_folder = folder
        self.load_files(folder)

    def load_files(self, folder):
        self.file_list.clear()

        try:
            files = [
                f for f in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, f))
            ]

            if not files:
                QMessageBox.information(self, "No Files", "No files found in selected folder.")
                self.file_label.setText("No files found")
                return

            for file_name in files:
                item = QListWidgetItem(file_name)
                self.file_list.addItem(item)

            self.file_label.setText("Hover or click a file to print its name")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load files:\n{str(e)}")

    def on_item_hovered(self, item):
        file_name = item.text()
        self.file_label.setText(f"Hovered file: {file_name}")
        print("hello")
        print(f"Hovered file: {file_name}")

    def on_item_clicked(self, item):
        file_name = item.text()
        self.file_label.setText(f"Selected file: {file_name}")
        print(f"Selected file: {file_name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileBrowserApp()
    window.show()
    sys.exit(app.exec_())
