import sys
import os
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QDateTimeEdit,
    QComboBox,
    QProgressBar,
    QTextEdit,
)


class CSVChunkFilterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Large CSV Filter using Chunking")
        self.resize(750, 420)

        self.csv_file_path = ""
        self.chunk_size = 50000

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No CSV file selected")
        self.browse_button = QPushButton("Browse CSV")
        self.browse_button.clicked.connect(self.browse_csv)

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.browse_button)

        # Datetime column selection
        column_layout = QHBoxLayout()
        column_label = QLabel("Datetime Column:")
        self.column_combo = QComboBox()
        self.column_combo.setEnabled(False)

        column_layout.addWidget(column_label)
        column_layout.addWidget(self.column_combo)

        # Start datetime
        start_layout = QHBoxLayout()
        start_label = QLabel("Start Datetime:")
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_datetime.setDateTime(QDateTime.currentDateTime().addDays(-1))

        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_datetime)

        # End datetime
        end_layout = QHBoxLayout()
        end_label = QLabel("End Datetime:")
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_datetime.setDateTime(QDateTime.currentDateTime())

        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_datetime)

        # Generate button
        self.generate_button = QPushButton("Generate New CSV")
        self.generate_button.clicked.connect(self.generate_filtered_csv)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        main_layout.addLayout(file_layout)
        main_layout.addLayout(column_layout)
        main_layout.addLayout(start_layout)
        main_layout.addLayout(end_layout)
        main_layout.addWidget(self.generate_button)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.log_area)

        self.setLayout(main_layout)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        self.csv_file_path = file_path
        self.file_label.setText(os.path.basename(file_path))
        self.log(f"Selected file: {file_path}")

        try:
            # Read only header + small sample
            sample_df = pd.read_csv(file_path, nrows=100)
            columns = list(sample_df.columns)

            if not columns:
                raise ValueError("No columns found in CSV file.")

            self.column_combo.clear()
            self.column_combo.addItems(columns)
            self.column_combo.setEnabled(True)

            # Try to auto-select a likely datetime column
            likely_names = [
                "datetime", "timestamp", "date_time", "date", "time",
                "created_at", "updated_at", "event_time", "log_time"
            ]

            selected_index = 0
            for i, col in enumerate(columns):
                if col.strip().lower() in likely_names:
                    selected_index = i
                    break

            self.column_combo.setCurrentIndex(selected_index)
            self.log("CSV headers loaded successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV header.\n\n{str(e)}")
            self.log(f"Error while loading CSV header: {e}")

    def get_output_file_path(self):
        input_dir = os.path.dirname(self.csv_file_path)
        input_name = os.path.splitext(os.path.basename(self.csv_file_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{input_name}_filtered_{timestamp}.csv"
        return os.path.join(input_dir, output_name)

    def estimate_total_rows(self, file_path):
        """
        Rough row count for progress bar.
        Counts lines in file and subtracts 1 for header.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                total_lines = sum(1 for _ in f)
            return max(total_lines - 1, 0)
        except Exception:
            return 0

    def generate_filtered_csv(self):
        if not self.csv_file_path:
            QMessageBox.warning(self, "Warning", "Please select a CSV file first.")
            return

        if not self.column_combo.currentText():
            QMessageBox.warning(self, "Warning", "Please select a datetime column.")
            return

        start_dt = self.start_datetime.dateTime().toPyDateTime()
        end_dt = self.end_datetime.dateTime().toPyDateTime()

        if start_dt > end_dt:
            QMessageBox.warning(self, "Warning", "Start datetime must be before end datetime.")
            return

        datetime_column = self.column_combo.currentText()
        output_file = self.get_output_file_path()

        self.log(f"Filtering started on column: {datetime_column}")
        self.log(f"Start datetime: {start_dt}")
        self.log(f"End datetime: {end_dt}")
        self.log(f"Output file: {output_file}")

        try:
            total_rows = self.estimate_total_rows(self.csv_file_path)
            processed_rows = 0
            matched_rows = 0
            first_write = True

            self.progress_bar.setValue(0)

            for chunk in pd.read_csv(self.csv_file_path, chunksize=self.chunk_size):
                if datetime_column not in chunk.columns:
                    raise ValueError(f"Column '{datetime_column}' not found in chunk.")

                # Convert datetime column safely
                chunk[datetime_column] = pd.to_datetime(
                    chunk[datetime_column],
                    errors="coerce"
                )

                # Filter rows between start and end datetime
                filtered_chunk = chunk[
                    (chunk[datetime_column] >= start_dt) &
                    (chunk[datetime_column] <= end_dt)
                ]

                if not filtered_chunk.empty:
                    filtered_chunk.to_csv(
                        output_file,
                        mode="w" if first_write else "a",
                        index=False,
                        header=first_write
                    )
                    matched_rows += len(filtered_chunk)
                    first_write = False

                processed_rows += len(chunk)

                if total_rows > 0:
                    progress = int((processed_rows / total_rows) * 100)
                    self.progress_bar.setValue(min(progress, 100))

                self.log(
                    f"Processed {processed_rows} rows, matched {matched_rows} rows so far..."
                )
                QApplication.processEvents()

            self.progress_bar.setValue(100)

            if matched_rows == 0:
                self.log("No rows matched the selected datetime range.")
                QMessageBox.information(
                    self,
                    "Done",
                    "No matching rows found for the selected datetime range."
                )
                # Remove empty file if created accidentally
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except Exception:
                        pass
            else:
                self.log(f"Filtering completed. Total matched rows: {matched_rows}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"Filtered CSV created successfully.\n\nFile: {output_file}\nRows: {matched_rows}"
                )

        except Exception as e:
            self.log(f"Error during filtering: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate filtered CSV.\n\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVChunkFilterApp()
    window.show()
    sys.exit(app.exec_())
