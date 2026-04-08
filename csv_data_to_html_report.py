import sys
import html
import csv
import io
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QFileDialog, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt


class CsvToHtmlReportApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Text to HTML Report Generator")
        self.setGeometry(200, 120, 1000, 700)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f6f9;
            }
            QLabel {
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #cfd8dc;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                color: #1f2933;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel("Paste copied CSV data below:")
        layout.addWidget(self.label)

        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText(
            'Paste CSV content here...\nExample:\nName,Age,City\nJohn,30,Houston\nAlice,28,Dallas'
        )
        layout.addWidget(self.text_area)

        self.generate_button = QPushButton("Generate HTML Report")
        self.generate_button.clicked.connect(self.generate_html_report)
        layout.addWidget(self.generate_button, alignment=Qt.AlignRight)

        self.central_widget.setLayout(layout)

    def parse_csv_data(self, raw_text):
        """
        Parses pasted CSV text safely, including quoted fields and commas inside quotes.
        """
        csv_file = io.StringIO(raw_text)
        reader = csv.reader(csv_file)
        rows = []

        for row in reader:
            if any(cell.strip() for cell in row):
                rows.append([cell.strip() for cell in row])

        return rows

    def generate_html_report(self):
        raw_text = self.text_area.toPlainText().strip()

        if not raw_text:
            QMessageBox.warning(self, "Input Missing", "Please paste CSV data first.")
            return

        try:
            data = self.parse_csv_data(raw_text)
        except Exception as e:
            QMessageBox.critical(self, "CSV Parse Error", f"Unable to parse CSV data:\n{str(e)}")
            return

        if not data:
            QMessageBox.warning(self, "Invalid Data", "Could not parse the pasted CSV data.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML Report",
            "csv_report.html",
            "HTML Files (*.html)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".html"):
            file_path += ".html"

        try:
            html_content = self.build_html_report(data)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            QMessageBox.information(
                self,
                "Success",
                f"HTML report generated successfully.\n\nSaved to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{str(e)}")

    def build_html_report(self, data):
        max_cols = max(len(row) for row in data)
        normalized_data = [row + [""] * (max_cols - len(row)) for row in data]

        header = normalized_data[0]
        body_rows = normalized_data[1:] if len(normalized_data) > 1 else []

        table_headers = "".join(
            f"<th>{html.escape(col)}</th>" for col in header
        )

        table_body = ""
        for row in body_rows:
            row_html = "".join(f"<td>{html.escape(cell)}</td>" for cell in row)
            table_body += f"<tr>{row_html}</tr>\n"

        if not body_rows:
            row_html = "".join(f"<td>{html.escape(cell)}</td>" for cell in header)
            table_body = f"<tr>{row_html}</tr>\n"
            table_headers = "".join(
                f"<th>Column {i+1}</th>" for i in range(len(header))
            )

        generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_report = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Report</title>
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 0;
            color: #1f2937;
        }}
        .container {{
            width: 92%;
            max-width: 1300px;
            margin: 35px auto;
            background: #ffffff;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1d4ed8, #2563eb);
            color: white;
            padding: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin-top: 8px;
            font-size: 14px;
            opacity: 0.95;
        }}
        .content {{
            padding: 30px;
        }}
        .summary {{
            margin-bottom: 20px;
            padding: 16px;
            background: #f8fafc;
            border-left: 5px solid #2563eb;
            border-radius: 8px;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
            font-size: 14px;
        }}
        th {{
            background: #2563eb;
            color: white;
            text-align: left;
            padding: 12px;
            border: 1px solid #dbe2ea;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 10px 12px;
            border: 1px solid #dbe2ea;
        }}
        tr:nth-child(even) {{
            background: #f8fbff;
        }}
        tr:hover {{
            background: #eef6ff;
        }}
        .footer {{
            text-align: center;
            padding: 18px;
            font-size: 12px;
            color: #6b7280;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
        }}
        .table-wrapper {{
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CSV HTML Report</h1>
            <p>Generated on {generated_time}</p>
        </div>

        <div class="content">
            <div class="summary">
                <strong>Report Summary:</strong><br>
                Total Rows: {len(normalized_data)}<br>
                Total Columns: {max_cols}
            </div>

            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>{table_headers}</tr>
                    </thead>
                    <tbody>
                        {table_body}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            Professional HTML Report generated by PyQt5
        </div>
    </div>
</body>
</html>
"""
        return html_report


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CsvToHtmlReportApp()
    window.show()
    sys.exit(app.exec_())
