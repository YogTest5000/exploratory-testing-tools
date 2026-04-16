import sys
import json
import html
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt


class JsonCompareApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file1_path = ""
        self.file2_path = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("JSON Compare Report Generator")
        self.resize(900, 650)

        title = QLabel("JSON Comparison Tool")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin: 10px;")

        # File 1
        self.file1_edit = QLineEdit()
        self.file1_edit.setPlaceholderText("Select first JSON file...")
        self.file1_edit.setReadOnly(True)

        browse1_btn = QPushButton("Browse JSON 1")
        browse1_btn.clicked.connect(self.browse_file1)

        file1_layout = QHBoxLayout()
        file1_layout.addWidget(QLabel("JSON File 1:"))
        file1_layout.addWidget(self.file1_edit)
        file1_layout.addWidget(browse1_btn)

        # File 2
        self.file2_edit = QLineEdit()
        self.file2_edit.setPlaceholderText("Select second JSON file...")
        self.file2_edit.setReadOnly(True)

        browse2_btn = QPushButton("Browse JSON 2")
        browse2_btn.clicked.connect(self.browse_file2)

        file2_layout = QHBoxLayout()
        file2_layout.addWidget(QLabel("JSON File 2:"))
        file2_layout.addWidget(self.file2_edit)
        file2_layout.addWidget(browse2_btn)

        # Compare button
        compare_btn = QPushButton("Compare and Generate HTML Report")
        compare_btn.setFixedHeight(40)
        compare_btn.clicked.connect(self.compare_json_files)

        # Log / result preview
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Comparison summary will appear here...")

        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addLayout(file1_layout)
        main_layout.addLayout(file2_layout)
        main_layout.addWidget(compare_btn)
        main_layout.addWidget(QLabel("Comparison Summary:"))
        main_layout.addWidget(self.result_box)

        self.setLayout(main_layout)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f8;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
            }
            QLineEdit, QTextEdit {
                background-color: white;
                border: 1px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)

    def browse_file1(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select First JSON File", "", "JSON Files (*.json)"
        )
        if file_path:
            self.file1_path = file_path
            self.file1_edit.setText(file_path)

    def browse_file2(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Second JSON File", "", "JSON Files (*.json)"
        )
        if file_path:
            self.file2_path = file_path
            self.file2_edit.setText(file_path)

    def load_json(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def compare_json(self, json1, json2, path="root"):
        differences = []

        if type(json1) != type(json2):
            differences.append({
                "path": path,
                "type": "Type Mismatch",
                "value1": repr(json1),
                "value2": repr(json2)
            })
            return differences

        if isinstance(json1, dict):
            keys1 = set(json1.keys())
            keys2 = set(json2.keys())

            for key in sorted(keys1 - keys2):
                differences.append({
                    "path": f"{path}.{key}",
                    "type": "Missing in File 2",
                    "value1": repr(json1[key]),
                    "value2": "Key not present"
                })

            for key in sorted(keys2 - keys1):
                differences.append({
                    "path": f"{path}.{key}",
                    "type": "Missing in File 1",
                    "value1": "Key not present",
                    "value2": repr(json2[key])
                })

            for key in sorted(keys1 & keys2):
                differences.extend(
                    self.compare_json(json1[key], json2[key], f"{path}.{key}")
                )

        elif isinstance(json1, list):
            max_len = max(len(json1), len(json2))
            for i in range(max_len):
                current_path = f"{path}[{i}]"
                if i >= len(json1):
                    differences.append({
                        "path": current_path,
                        "type": "Missing in File 1",
                        "value1": "Index not present",
                        "value2": repr(json2[i])
                    })
                elif i >= len(json2):
                    differences.append({
                        "path": current_path,
                        "type": "Missing in File 2",
                        "value1": repr(json1[i]),
                        "value2": "Index not present"
                    })
                else:
                    differences.extend(
                        self.compare_json(json1[i], json2[i], current_path)
                    )

        else:
            if json1 != json2:
                differences.append({
                    "path": path,
                    "type": "Value Mismatch",
                    "value1": repr(json1),
                    "value2": repr(json2)
                })

        return differences

    def generate_html_report(self, file1, file2, differences):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rows = ""
        if differences:
            for diff in differences:
                rows += f"""
                <tr>
                    <td>{html.escape(diff['path'])}</td>
                    <td>{html.escape(diff['type'])}</td>
                    <td>{html.escape(str(diff['value1']))}</td>
                    <td>{html.escape(str(diff['value2']))}</td>
                </tr>
                """
        else:
            rows = """
            <tr>
                <td colspan="4" style="text-align:center; color:green; font-weight:bold;">
                    No differences found. Both JSON files match.
                </td>
            </tr>
            """

        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>JSON Comparison Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 30px;
                    background-color: #f9fbfc;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: auto;
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                }}
                h1 {{
                    color: #1976d2;
                    text-align: center;
                }}
                .meta {{
                    margin-bottom: 20px;
                    line-height: 1.8;
                    background: #f4f8fb;
                    padding: 15px;
                    border-radius: 8px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #d0d7de;
                    padding: 10px;
                    text-align: left;
                    vertical-align: top;
                    word-break: break-word;
                }}
                th {{
                    background-color: #1976d2;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f7f9fb;
                }}
                .summary {{
                    margin-top: 20px;
                    font-size: 16px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>JSON Comparison Report</h1>

                <div class="meta">
                    <div><strong>Generated On:</strong> {html.escape(timestamp)}</div>
                    <div><strong>File 1:</strong> {html.escape(file1)}</div>
                    <div><strong>File 2:</strong> {html.escape(file2)}</div>
                    <div><strong>Total Differences:</strong> {len(differences)}</div>
                </div>

                <div class="summary">
                    Comparison Result: {"Differences Found" if differences else "Files Match"}
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>JSON Path</th>
                            <th>Difference Type</th>
                            <th>File 1 Value</th>
                            <th>File 2 Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        return html_report

    def compare_json_files(self):
        if not self.file1_path or not self.file2_path:
            QMessageBox.warning(self, "Missing Files", "Please select both JSON files.")
            return

        try:
            json1 = self.load_json(self.file1_path)
            json2 = self.load_json(self.file2_path)

            differences = self.compare_json(json1, json2)

            summary_text = []
            summary_text.append(f"File 1: {self.file1_path}")
            summary_text.append(f"File 2: {self.file2_path}")
            summary_text.append(f"Total differences found: {len(differences)}")
            summary_text.append("-" * 80)

            if differences:
                for idx, diff in enumerate(differences, start=1):
                    summary_text.append(
                        f"{idx}. Path: {diff['path']}\n"
                        f"   Type: {diff['type']}\n"
                        f"   File1: {diff['value1']}\n"
                        f"   File2: {diff['value2']}\n"
                    )
            else:
                summary_text.append("No differences found. Both JSON files are identical.")

            self.result_box.setPlainText("\n".join(summary_text))

            report_html = self.generate_html_report(
                self.file1_path, self.file2_path, differences
            )

            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save HTML Report", "json_comparison_report.html", "HTML Files (*.html)"
            )

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(report_html)

                QMessageBox.information(
                    self,
                    "Success",
                    f"HTML comparison report generated successfully.\n\nSaved to:\n{save_path}"
                )

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON file.\n\nDetails:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JsonCompareApp()
    window.show()
    sys.exit(app.exec_())
