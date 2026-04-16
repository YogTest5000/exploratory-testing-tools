import sys
import json
import html
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit,
    QListWidget, QListWidgetItem, QAbstractItemView, QSplitter
)
from PyQt5.QtCore import Qt


class JsonCompareApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file1_path = ""
        self.file2_path = ""
        self.json1_data = None
        self.json2_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("JSON Compare Report Generator")
        self.resize(1200, 750)

        title = QLabel("JSON Comparison Tool with Selectable Keys")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin: 10px;")

        # File 1 controls
        self.file1_edit = QLineEdit()
        self.file1_edit.setPlaceholderText("Select first JSON file...")
        self.file1_edit.setReadOnly(True)

        browse1_btn = QPushButton("Browse JSON 1")
        browse1_btn.clicked.connect(self.browse_file1)

        file1_layout = QHBoxLayout()
        file1_layout.addWidget(QLabel("JSON File 1:"))
        file1_layout.addWidget(self.file1_edit)
        file1_layout.addWidget(browse1_btn)

        # File 2 controls
        self.file2_edit = QLineEdit()
        self.file2_edit.setPlaceholderText("Select second JSON file...")
        self.file2_edit.setReadOnly(True)

        browse2_btn = QPushButton("Browse JSON 2")
        browse2_btn.clicked.connect(self.browse_file2)

        file2_layout = QHBoxLayout()
        file2_layout.addWidget(QLabel("JSON File 2:"))
        file2_layout.addWidget(self.file2_edit)
        file2_layout.addWidget(browse2_btn)

        # Load keys button
        load_keys_btn = QPushButton("Load JSON Keys")
        load_keys_btn.clicked.connect(self.load_keys_for_selection)

        select_all_btn = QPushButton("Select All Keys")
        select_all_btn.clicked.connect(self.select_all_keys)

        clear_selection_btn = QPushButton("Clear Selection")
        clear_selection_btn.clicked.connect(self.clear_selected_keys)

        compare_btn = QPushButton("Compare Selected Keys and Generate HTML Report")
        compare_btn.setFixedHeight(42)
        compare_btn.clicked.connect(self.compare_selected_keys)

        button_layout = QHBoxLayout()
        button_layout.addWidget(load_keys_btn)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(clear_selection_btn)

        # Key selection list
        self.keys_list = QListWidget()
        self.keys_list.setSelectionMode(QAbstractItemView.MultiSelection)

        # Result summary
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Comparison summary will appear here...")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.create_group_box_widget("Available JSON Keys", self.keys_list))
        splitter.addWidget(self.create_group_box_widget("Comparison Summary", self.result_box))
        splitter.setSizes([450, 700])

        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addLayout(file1_layout)
        main_layout.addLayout(file2_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(compare_btn)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)
        self.apply_styles()

    def create_group_box_widget(self, heading, widget):
        container = QWidget()
        layout = QVBoxLayout()
        label = QLabel(heading)
        label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        layout.addWidget(label)
        layout.addWidget(widget)
        container.setLayout(layout)
        return container

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
            QLineEdit, QTextEdit, QListWidget {
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
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #bbdefb;
                color: black;
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

    def extract_json_paths(self, data, parent_key="root"):
        """
        Recursively extracts all JSON paths.
        Example:
            root.user.name
            root.user.address.city
            root.items[0].id
        """
        paths = []

        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{parent_key}.{key}"
                paths.append(new_key)
                paths.extend(self.extract_json_paths(value, new_key))
        elif isinstance(data, list):
            for index, item in enumerate(data):
                new_key = f"{parent_key}[{index}]"
                paths.append(new_key)
                paths.extend(self.extract_json_paths(item, new_key))

        return paths

    def load_keys_for_selection(self):
        if not self.file1_path or not self.file2_path:
            QMessageBox.warning(self, "Missing Files", "Please select both JSON files first.")
            return

        try:
            self.json1_data = self.load_json(self.file1_path)
            self.json2_data = self.load_json(self.file2_path)

            paths1 = set(self.extract_json_paths(self.json1_data))
            paths2 = set(self.extract_json_paths(self.json2_data))
            all_paths = sorted(paths1.union(paths2))

            self.keys_list.clear()

            if not all_paths:
                QMessageBox.information(self, "No Keys", "No JSON keys found to display.")
                return

            for path in all_paths:
                item = QListWidgetItem(path)
                self.keys_list.addItem(item)

            QMessageBox.information(
                self,
                "Keys Loaded",
                f"Loaded {len(all_paths)} keys from both JSON files."
            )

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON file.\n\nDetails:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON keys.\n\n{str(e)}")

    def select_all_keys(self):
        for i in range(self.keys_list.count()):
            self.keys_list.item(i).setSelected(True)

    def clear_selected_keys(self):
        self.keys_list.clearSelection()

    def parse_path_tokens(self, path):
        """
        Converts path like:
            root.user.address.city
            root.items[0].id
        into tokens:
            ['user', 'address', 'city']
            ['items', 0, 'id']
        """
        if path.startswith("root."):
            path = path[5:]
        elif path == "root":
            return []

        tokens = []
        parts = path.split(".")

        for part in parts:
            while "[" in part and "]" in part:
                before_bracket = part[:part.index("[")]
                if before_bracket:
                    tokens.append(before_bracket)

                index_str = part[part.index("[") + 1:part.index("]")]
                tokens.append(int(index_str))

                part = part[part.index("]") + 1:]

            if part:
                tokens.append(part)

        return tokens

    def get_value_by_path(self, data, path):
        """
        Returns:
            (exists, value)
        """
        try:
            tokens = self.parse_path_tokens(path)
            current = data

            for token in tokens:
                if isinstance(token, int):
                    if not isinstance(current, list) or token >= len(current):
                        return False, None
                    current = current[token]
                else:
                    if not isinstance(current, dict) or token not in current:
                        return False, None
                    current = current[token]

            return True, current
        except Exception:
            return False, None

    def compare_values(self, value1, value2, path="root"):
        differences = []

        if type(value1) != type(value2):
            differences.append({
                "path": path,
                "type": "Type Mismatch",
                "value1": repr(value1),
                "value2": repr(value2)
            })
            return differences

        if isinstance(value1, dict):
            keys1 = set(value1.keys())
            keys2 = set(value2.keys())

            for key in sorted(keys1 - keys2):
                differences.append({
                    "path": f"{path}.{key}",
                    "type": "Missing in File 2",
                    "value1": repr(value1[key]),
                    "value2": "Key not present"
                })

            for key in sorted(keys2 - keys1):
                differences.append({
                    "path": f"{path}.{key}",
                    "type": "Missing in File 1",
                    "value1": "Key not present",
                    "value2": repr(value2[key])
                })

            for key in sorted(keys1 & keys2):
                differences.extend(
                    self.compare_values(value1[key], value2[key], f"{path}.{key}")
                )

        elif isinstance(value1, list):
            max_len = max(len(value1), len(value2))
            for i in range(max_len):
                item_path = f"{path}[{i}]"
                if i >= len(value1):
                    differences.append({
                        "path": item_path,
                        "type": "Missing in File 1",
                        "value1": "Index not present",
                        "value2": repr(value2[i])
                    })
                elif i >= len(value2):
                    differences.append({
                        "path": item_path,
                        "type": "Missing in File 2",
                        "value1": repr(value1[i]),
                        "value2": "Index not present"
                    })
                else:
                    differences.extend(
                        self.compare_values(value1[i], value2[i], item_path)
                    )

        else:
            if value1 != value2:
                differences.append({
                    "path": path,
                    "type": "Value Mismatch",
                    "value1": repr(value1),
                    "value2": repr(value2)
                })

        return differences

    def compare_selected_keys(self):
        if not self.file1_path or not self.file2_path:
            QMessageBox.warning(self, "Missing Files", "Please select both JSON files.")
            return

        selected_items = self.keys_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Keys Selected", "Please select at least one key to compare.")
            return

        try:
            if self.json1_data is None:
                self.json1_data = self.load_json(self.file1_path)
            if self.json2_data is None:
                self.json2_data = self.load_json(self.file2_path)

            selected_paths = [item.text() for item in selected_items]
            all_differences = []

            summary_lines = []
            summary_lines.append(f"File 1: {self.file1_path}")
            summary_lines.append(f"File 2: {self.file2_path}")
            summary_lines.append(f"Selected Keys Count: {len(selected_paths)}")
            summary_lines.append("-" * 100)

            for path in selected_paths:
                exists1, value1 = self.get_value_by_path(self.json1_data, path)
                exists2, value2 = self.get_value_by_path(self.json2_data, path)

                if not exists1 and not exists2:
                    continue
                elif exists1 and not exists2:
                    all_differences.append({
                        "path": path,
                        "type": "Missing in File 2",
                        "value1": repr(value1),
                        "value2": "Key not present"
                    })
                elif not exists1 and exists2:
                    all_differences.append({
                        "path": path,
                        "type": "Missing in File 1",
                        "value1": "Key not present",
                        "value2": repr(value2)
                    })
                else:
                    diffs = self.compare_values(value1, value2, path)
                    all_differences.extend(diffs)

            summary_lines.append(f"Total Differences Found: {len(all_differences)}")
            summary_lines.append("")

            if all_differences:
                for idx, diff in enumerate(all_differences, start=1):
                    summary_lines.append(f"{idx}. Path: {diff['path']}")
                    summary_lines.append(f"   Type : {diff['type']}")
                    summary_lines.append(f"   File1: {diff['value1']}")
                    summary_lines.append(f"   File2: {diff['value2']}")
                    summary_lines.append("")
            else:
                summary_lines.append("No differences found for selected keys.")

            self.result_box.setPlainText("\n".join(summary_lines))

            report_html = self.generate_html_report(
                self.file1_path,
                self.file2_path,
                selected_paths,
                all_differences
            )

            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save HTML Report",
                "json_comparison_selected_keys_report.html",
                "HTML Files (*.html)"
            )

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(report_html)

                QMessageBox.information(
                    self,
                    "Success",
                    f"HTML report generated successfully.\n\nSaved to:\n{save_path}"
                )

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON file.\n\nDetails:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n\n{str(e)}")

    def generate_html_report(self, file1, file2, selected_paths, differences):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        selected_keys_html = "".join(
            f"<li>{html.escape(path)}</li>" for path in selected_paths
        )

        if differences:
            rows = ""
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
                    No differences found for selected keys.
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>JSON Selected Keys Comparison Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 30px;
                    background-color: #f9fbfc;
                    color: #333;
                }}
                .container {{
                    max-width: 1300px;
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
                .section-title {{
                    margin-top: 25px;
                    margin-bottom: 10px;
                    font-size: 18px;
                    color: #1565c0;
                    font-weight: bold;
                }}
                ul {{
                    background: #fafafa;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px 30px;
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
                    <div><strong>Total Selected Keys:</strong> {len(selected_paths)}</div>
                    <div><strong>Total Differences:</strong> {len(differences)}</div>
                </div>

                <div class="section-title">Selected Keys for Comparison</div>
                <ul>
                    {selected_keys_html}
                </ul>

                <div class="summary">
                    Comparison Result: {"Differences Found" if differences else "Selected keys match"}
                </div>

                <div class="section-title">Detailed Differences</div>
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JsonCompareApp()
    window.show()
    sys.exit(app.exec_())
