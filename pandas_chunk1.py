import sys
import os
import pandas as pd

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QGridLayout, QFrame
)


class CSVChunkWorker(QThread):
    progress_changed = pyqtSignal(int)
    log_message = pyqtSignal(str)
    stats_ready = pyqtSignal(dict)
    finished_processing = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path, chunk_size=1000):
        super().__init__()
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        try:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError("Selected file does not exist.")

            total_rows = self.count_rows(self.file_path)
            if total_rows == 0:
                raise ValueError("CSV file is empty.")

            processed_rows = 0
            total_chunks = 0

            # Example dashboard metrics
            total_records = 0
            high_temp_count = 0
            avg_temp_sum = 0
            avg_temp_count = 0
            unique_zones = set()

            self.log_message.emit(f"Started processing: {self.file_path}")
            self.log_message.emit(f"Total rows detected: {total_rows}")

            for chunk in pd.read_csv(self.file_path, chunksize=self.chunk_size):
                if not self.is_running:
                    self.log_message.emit("Processing stopped by user.")
                    return

                total_chunks += 1
                chunk_rows = len(chunk)
                processed_rows += chunk_rows
                total_records += chunk_rows

                self.log_message.emit(f"Processing chunk {total_chunks} with {chunk_rows} rows")

                # Example processing logic
                # Expected columns: timestamp, zone, temperature
                if "temperature" in chunk.columns:
                    high_temp_count += (chunk["temperature"] > 30).sum()
                    avg_temp_sum += chunk["temperature"].sum()
                    avg_temp_count += chunk["temperature"].count()

                if "zone" in chunk.columns:
                    unique_zones.update(chunk["zone"].dropna().astype(str).unique())

                percent = int((processed_rows / total_rows) * 100)
                self.progress_changed.emit(percent)

            avg_temperature = round(avg_temp_sum / avg_temp_count, 2) if avg_temp_count > 0 else 0

            stats = {
                "total_records": total_records,
                "total_chunks": total_chunks,
                "high_temp_count": int(high_temp_count),
                "avg_temperature": avg_temperature,
                "unique_zone_count": len(unique_zones),
                "zones": ", ".join(sorted(unique_zones)) if unique_zones else "N/A"
            }

            self.stats_ready.emit(stats)
            self.log_message.emit("Processing completed successfully.")
            self.finished_processing.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def count_rows(self, file_path):
        # Count data rows excluding header
        with open(file_path, "r", encoding="utf-8") as f:
            row_count = sum(1 for _ in f) - 1
        return max(row_count, 0)


class DashboardCard(QFrame):
    def __init__(self, title, value="0"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #bbbbbb; font-size: 14px;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_value(self, value):
        self.value_label.setText(str(value))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt CSV Chunk Dashboard")
        self.setGeometry(200, 100, 900, 650)

        self.file_path = ""
        self.worker = None

        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Top controls
        controls_layout = QHBoxLayout()

        self.file_label = QLabel("No file selected")
        self.browse_button = QPushButton("Browse CSV")
        self.start_button = QPushButton("Start Processing")
        self.stop_button = QPushButton("Stop")

        self.browse_button.clicked.connect(self.browse_file)
        self.start_button.clicked.connect(self.start_processing)
        self.stop_button.clicked.connect(self.stop_processing)

        controls_layout.addWidget(self.file_label)
        controls_layout.addWidget(self.browse_button)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Dashboard cards
        cards_layout = QGridLayout()
        self.total_records_card = DashboardCard("Total Records", "0")
        self.total_chunks_card = DashboardCard("Total Chunks", "0")
        self.high_temp_card = DashboardCard("Temp > 30", "0")
        self.avg_temp_card = DashboardCard("Avg Temperature", "0")
        self.unique_zone_card = DashboardCard("Unique Zones", "0")

        cards_layout.addWidget(self.total_records_card, 0, 0)
        cards_layout.addWidget(self.total_chunks_card, 0, 1)
        cards_layout.addWidget(self.high_temp_card, 0, 2)
        cards_layout.addWidget(self.avg_temp_card, 1, 0)
        cards_layout.addWidget(self.unique_zone_card, 1, 1)

        # Zone display
        self.zone_label = QLabel("Zones: N/A")
        self.zone_label.setStyleSheet("font-size: 14px; padding: 8px;")

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(cards_layout)
        main_layout.addWidget(self.zone_label)
        main_layout.addWidget(QLabel("Processing Log"))
        main_layout.addWidget(self.log_area)

        central_widget.setLayout(main_layout)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: white;
                font-family: Arial;
            }
            QPushButton {
                background-color: #3c6e71;
                color: white;
                border: none;
                padding: 10px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4c7f82;
            }
            QLabel {
                color: white;
            }
            QTextEdit {
                background-color: #252526;
                color: #dcdcdc;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 6px;
                text-align: center;
                background-color: #252526;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #3c6e71;
            }
        """)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )
        if file_path:
            self.file_path = file_path
            self.file_label.setText(file_path)
            self.log_area.append(f"Selected file: {file_path}")

    def start_processing(self):
        if not self.file_path:
            QMessageBox.warning(self, "Warning", "Please select a CSV file first.")
            return

        self.progress_bar.setValue(0)
        self.log_area.clear()
        self.reset_dashboard()

        self.worker = CSVChunkWorker(self.file_path, chunk_size=1000)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self.log_area.append)
        self.worker.stats_ready.connect(self.update_dashboard)
        self.worker.finished_processing.connect(self.processing_finished)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

        self.log_area.append("Worker thread started.")

    def stop_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log_area.append("Stopping worker...")

    def reset_dashboard(self):
        self.total_records_card.set_value("0")
        self.total_chunks_card.set_value("0")
        self.high_temp_card.set_value("0")
        self.avg_temp_card.set_value("0")
        self.unique_zone_card.set_value("0")
        self.zone_label.setText("Zones: N/A")

    def update_dashboard(self, stats):
        self.total_records_card.set_value(stats["total_records"])
        self.total_chunks_card.set_value(stats["total_chunks"])
        self.high_temp_card.set_value(stats["high_temp_count"])
        self.avg_temp_card.set_value(stats["avg_temperature"])
        self.unique_zone_card.set_value(stats["unique_zone_count"])
        self.zone_label.setText(f"Zones: {stats['zones']}")

    def processing_finished(self):
        self.log_area.append("All chunks processed.")
        QMessageBox.information(self, "Done", "CSV chunk processing completed.")

    def show_error(self, error_message):
        self.log_area.append(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
