import sys
import os
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QDateTimeEdit, QLineEdit
)
from PyQt5.QtCore import QDateTime


class LargeCSVFilterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Large CSV DateTime Filter")
        self.setGeometry(200, 200, 700, 300)

        self.csv_path = ""

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        self.file_label = QLabel("No CSV file selected")

        browse_btn = QPushButton("Browse CSV File")
        browse_btn.clicked.connect(self.browse_csv)

        datetime_col_layout = QHBoxLayout()
        datetime_col_layout.addWidget(QLabel("DateTime Column Name:"))

        self.datetime_column_input = QLineEdit()
        self.datetime_column_input.setPlaceholderText("Example: timestamp")
        datetime_col_layout.addWidget(self.datetime_column_input)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start DateTime:"))

        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDateTime(QDateTime.currentDateTime())
        self.start_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        start_layout.addWidget(self.start_datetime)

        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End DateTime:"))

        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setDateTime(QDateTime.currentDateTime())
        self.end_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        end_layout.addWidget(self.end_datetime)

        filter_btn = QPushButton("Filter CSV and Save")
        filter_btn.clicked.connect(self.filter_large_csv)

        self.status_label = QLabel("Ready")

        main_layout.addWidget(browse_btn)
        main_layout.addWidget(self.file_label)
        main_layout.addLayout(datetime_col_layout)
        main_layout.addLayout(start_layout)
        main_layout.addLayout(end_layout)
        main_layout.addWidget(filter_btn)
        main_layout.addWidget(self.status_label)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )

        if file_path:
            self.csv_path = file_path
            self.file_label.setText(file_path)
            self.status_label.setText("CSV file selected")

    def filter_large_csv(self):
        if not self.csv_path:
            QMessageBox.warning(self, "Missing File", "Please select a CSV file.")
            return

        datetime_column = self.datetime_column_input.text().strip()

        if not datetime_column:
            QMessageBox.warning(
                self,
                "Missing Column",
                "Please enter the datetime column name."
            )
            return

        start_dt = self.start_datetime.dateTime().toPyDateTime()
        end_dt = self.end_datetime.dateTime().toPyDateTime()

        if start_dt > end_dt:
            QMessageBox.warning(
                self,
                "Invalid Range",
                "Start datetime cannot be greater than end datetime."
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Filtered CSV",
            "filtered_output.csv",
            "CSV Files (*.csv)"
        )

        if not output_path:
            return

        try:
            chunk_size = 100000
            first_chunk = True
            total_rows = 0
            filtered_rows = 0

            for chunk in pd.read_csv(self.csv_path, chunksize=chunk_size):
                total_rows += len(chunk)

                if datetime_column not in chunk.columns:
                    QMessageBox.critical(
                        self,
                        "Column Error",
                        f"Column '{datetime_column}' not found in CSV."
                    )
                    return

                chunk[datetime_column] = pd.to_datetime(
                    chunk[datetime_column],
                    errors="coerce"
                )

                filtered_chunk = chunk[
                    (chunk[datetime_column] >= start_dt) &
                    (chunk[datetime_column] <= end_dt)
                ]

                filtered_rows += len(filtered_chunk)

                filtered_chunk.to_csv(
                    output_path,
                    mode="w" if first_chunk else "a",
                    header=first_chunk,
                    index=False
                )

                first_chunk = False

                self.status_label.setText(
                    f"Processed rows: {total_rows}, Filtered rows: {filtered_rows}"
                )
                QApplication.processEvents()

            QMessageBox.information(
                self,
                "Success",
                f"Filtering completed.\n\nSaved file:\n{output_path}\n\n"
                f"Total rows processed: {total_rows}\n"
                f"Filtered rows saved: {filtered_rows}"
            )

            self.status_label.setText("Filtering completed successfully")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LargeCSVFilterApp()
    window.show()
    sys.exit(app.exec_())
