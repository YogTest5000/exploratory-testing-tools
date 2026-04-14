import sys
import os
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QTextBrowser,
    QFrame, QSizePolicy, QStatusBar
)


class ExcelHtmlDashboardGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.excel_file = ""
        self.excel_data = {}
        self.generated_html = ""

        self.setWindowTitle("Excel → HTML Dashboard Generator")
        self.resize(1300, 850)

        self.setStyleSheet(self.get_stylesheet())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = QFrame()
        header.setObjectName("headerCard")
        header_layout = QVBoxLayout(header)

        title = QLabel("Excel → HTML Dashboard Generator")
        title.setObjectName("titleLabel")

        subtitle = QLabel(
            "Load an Excel workbook, choose a sheet, preview a clean HTML dashboard, and save it as a report."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        # Controls
        controls = QFrame()
        controls.setObjectName("card")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setSpacing(10)

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("infoLabel")
        self.file_label.setWordWrap(True)
        self.file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.browse_button = QPushButton("Browse Excel File")
        self.browse_button.clicked.connect(self.browse_excel)

        self.sheet_combo = QComboBox()
        self.sheet_combo.setMinimumWidth(220)
        self.sheet_combo.setEnabled(False)

        self.generate_button = QPushButton("Generate HTML Dashboard")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self.generate_dashboard)

        self.save_button = QPushButton("Save HTML")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_html)

        controls_layout.addWidget(self.browse_button)
        controls_layout.addWidget(QLabel("Sheet:"))
        controls_layout.addWidget(self.sheet_combo)
        controls_layout.addWidget(self.generate_button)
        controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(self.file_label, 1)

        # Preview
        preview_card = QFrame()
        preview_card.setObjectName("card")
        preview_layout = QVBoxLayout(preview_card)

        preview_label = QLabel("HTML Preview")
        preview_label.setObjectName("sectionLabel")

        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(True)

        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_browser)

        main_layout.addWidget(header)
        main_layout.addWidget(controls)
        main_layout.addWidget(preview_card, 1)

        self.central_widget.setLayout(main_layout)

    def browse_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx *.xlsm *.xltx *.xltm)"
        )

        if not file_path:
            return

        try:
            excel_obj = pd.ExcelFile(file_path, engine="openpyxl")
            self.excel_data.clear()
            self.sheet_combo.clear()

            for sheet_name in excel_obj.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
                self.excel_data[sheet_name] = df
                self.sheet_combo.addItem(sheet_name)

            self.excel_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.sheet_combo.setEnabled(True)
            self.generate_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.preview_browser.clear()
            self.generated_html = ""

            self.status_bar.showMessage(f"Loaded workbook: {os.path.basename(file_path)}", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read Excel file.\n\nDetails:\n{str(e)}")
            self.status_bar.showMessage("Failed to load Excel file", 5000)

    def generate_dashboard(self):
        if not self.excel_file:
            QMessageBox.warning(self, "Warning", "Please select an Excel file first.")
            return

        sheet_name = self.sheet_combo.currentText()
        if not sheet_name:
            QMessageBox.warning(self, "Warning", "Please select a sheet.")
            return

        try:
            df = self.excel_data.get(sheet_name, pd.DataFrame()).copy()

            if df.empty:
                html_table = "<p class='empty-msg'>The selected sheet is empty.</p>"
                row_count = 0
                col_count = 0
                null_count = 0
            else:
                # Fill NaN for better HTML readability
                display_df = df.fillna("")
                html_table = display_df.to_html(
                    index=False,
                    classes="data-table",
                    border=0,
                    justify="left"
                )
                row_count = len(display_df)
                col_count = len(display_df.columns)
                null_count = int(df.isna().sum().sum())

            generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_name = os.path.basename(self.excel_file)

            self.generated_html = self.build_html(
                file_name=file_name,
                sheet_name=sheet_name,
                row_count=row_count,
                col_count=col_count,
                null_count=null_count,
                generated_time=generated_time,
                table_html=html_table
            )

            self.preview_browser.setHtml(self.generated_html)
            self.save_button.setEnabled(True)
            self.status_bar.showMessage(f"Dashboard generated for sheet: {sheet_name}", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate dashboard.\n\nDetails:\n{str(e)}")
            self.status_bar.showMessage("Failed to generate dashboard", 5000)

    def save_html(self):
        if not self.generated_html:
            QMessageBox.warning(self, "Warning", "Please generate the dashboard first.")
            return

        default_name = "excel_dashboard_report.html"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML Report",
            default_name,
            "HTML Files (*.html)"
        )

        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.generated_html)

            QMessageBox.information(self, "Success", f"HTML report saved successfully.\n\n{save_path}")
            self.status_bar.showMessage(f"Saved HTML report: {save_path}", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save HTML report.\n\nDetails:\n{str(e)}")
            self.status_bar.showMessage("Failed to save HTML report", 5000)

    def build_html(self, file_name, sheet_name, row_count, col_count, null_count, generated_time, table_html):
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excel Dashboard Report</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #f4f7fb;
            color: #1f2937;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }}

        .hero {{
            background: linear-gradient(135deg, #1f4e79, #2b6cb0);
            color: white;
            padding: 28px;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            margin-bottom: 24px;
        }}

        .hero h1 {{
            margin: 0 0 8px 0;
            font-size: 32px;
        }}

        .hero p {{
            margin: 4px 0;
            font-size: 15px;
            opacity: 0.96;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .card {{
            background: white;
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
            border-left: 6px solid #2b6cb0;
        }}

        .card-title {{
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .card-value {{
            font-size: 28px;
            font-weight: bold;
            color: #111827;
        }}

        .section {{
            background: white;
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        }}

        .section h2 {{
            margin-top: 0;
            margin-bottom: 16px;
            color: #1f4e79;
        }}

        .table-wrapper {{
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
        }}

        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 700px;
            background: white;
        }}

        table.data-table thead th {{
            position: sticky;
            top: 0;
            background: #1f4e79;
            color: white;
            text-align: left;
            padding: 12px;
            font-size: 14px;
            border: 1px solid #d1d5db;
        }}

        table.data-table tbody td {{
            padding: 10px 12px;
            border: 1px solid #e5e7eb;
            font-size: 14px;
            color: #111827;
            vertical-align: top;
        }}

        table.data-table tbody tr:nth-child(even) {{
            background: #f9fafb;
        }}

        table.data-table tbody tr:hover {{
            background: #eef6ff;
        }}

        .footer {{
            text-align: center;
            margin-top: 22px;
            color: #6b7280;
            font-size: 13px;
        }}

        .empty-msg {{
            padding: 16px;
            background: #fff7ed;
            border: 1px solid #fdba74;
            border-radius: 10px;
            color: #9a3412;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>Excel Dashboard Report</h1>
            <p><strong>Workbook:</strong> {file_name}</p>
            <p><strong>Sheet:</strong> {sheet_name}</p>
            <p><strong>Generated:</strong> {generated_time}</p>
        </div>

        <div class="meta-grid">
            <div class="card">
                <div class="card-title">Rows</div>
                <div class="card-value">{row_count}</div>
            </div>

            <div class="card">
                <div class="card-title">Columns</div>
                <div class="card-value">{col_count}</div>
            </div>

            <div class="card">
                <div class="card-title">Missing Values</div>
                <div class="card-value">{null_count}</div>
            </div>

            <div class="card">
                <div class="card-title">Active Sheet</div>
                <div class="card-value" style="font-size:20px;">{sheet_name}</div>
            </div>
        </div>

        <div class="section">
            <h2>Sheet Data</h2>
            <div class="table-wrapper">
                {table_html}
            </div>
        </div>

        <div class="footer">
            Generated by PyQt Excel → HTML Dashboard Generator
        </div>
    </div>
</body>
</html>
"""

    def get_stylesheet(self):
        return """
        QMainWindow {
            background-color: #0f172a;
        }

        QWidget {
            color: #e5e7eb;
            font-size: 14px;
        }

        QFrame#headerCard, QFrame#card {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 14px;
        }

        QLabel#titleLabel {
            font-size: 26px;
            font-weight: bold;
            color: #f9fafb;
        }

        QLabel#subtitleLabel {
            font-size: 14px;
            color: #9ca3af;
        }

        QLabel#sectionLabel {
            font-size: 18px;
            font-weight: bold;
            color: #f3f4f6;
            padding-bottom: 4px;
        }

        QLabel#infoLabel {
            color: #cbd5e1;
            padding-left: 8px;
        }

        QPushButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton:disabled {
            background-color: #475569;
            color: #cbd5e1;
        }

        QComboBox {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 8px;
            color: white;
        }

        QTextBrowser {
            background-color: #f8fafc;
            color: #111827;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 8px;
        }

        QStatusBar {
            background-color: #111827;
            color: #cbd5e1;
        }
        """


def main():
    app = QApplication(sys.argv)
    window = ExcelHtmlDashboardGenerator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
