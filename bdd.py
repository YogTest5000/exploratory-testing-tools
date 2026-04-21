import sys
import os
import html
import webbrowser
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QAbstractItemView,
)


class BDDReportGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BDD + Test Case HTML Report Generator")
        self.resize(1400, 900)
        self.current_file_path = ""
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        header = QLabel("BDD + Test Case HTML Report Generator")
        header.setObjectName("titleLabel")
        root.addWidget(header)

        subtitle = QLabel(
            "Create a professional HTML report that shows the behavior layer (Scenario Outline) and the execution layer (test cases)."
        )
        subtitle.setObjectName("subtitleLabel")
        root.addWidget(subtitle)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.design_tab = QWidget()
        self.execution_tab = QWidget()
        self.preview_tab = QWidget()

        self.tabs.addTab(self.design_tab, "BDD Design")
        self.tabs.addTab(self.execution_tab, "Test Cases")
        self.tabs.addTab(self.preview_tab, "Report Actions")

        self._build_design_tab()
        self._build_execution_tab()
        self._build_preview_tab()

        self.statusBar().showMessage("Ready")

    def _build_design_tab(self):
        layout = QVBoxLayout(self.design_tab)
        layout.setSpacing(10)

        meta_group = QGroupBox("Scenario Metadata")
        meta_layout = QGridLayout(meta_group)

        self.feature_input = QLineEdit("Heat Pump Control Logic")
        self.scenario_title_input = QLineEdit("Heat Pump activation in heat mode")
        self.requirement_id_input = QLineEdit("REQ-HVAC-001")
        self.author_input = QLineEdit("QA Team")

        meta_layout.addWidget(QLabel("Feature"), 0, 0)
        meta_layout.addWidget(self.feature_input, 0, 1)
        meta_layout.addWidget(QLabel("Scenario Outline"), 1, 0)
        meta_layout.addWidget(self.scenario_title_input, 1, 1)
        meta_layout.addWidget(QLabel("Requirement ID"), 0, 2)
        meta_layout.addWidget(self.requirement_id_input, 0, 3)
        meta_layout.addWidget(QLabel("Author"), 1, 2)
        meta_layout.addWidget(self.author_input, 1, 3)

        layout.addWidget(meta_group)

        steps_group = QGroupBox("BDD Steps")
        steps_layout = QGridLayout(steps_group)

        self.given_input = QLineEdit('thermostat is set to "HEAT" mode')
        self.and1_input = QLineEdit('heating setpoint is <setpoint> °F')
        self.and2_input = QLineEdit('current room temperature is <room_temp> °F')
        self.when_input = QLineEdit('system evaluates temperature conditions')
        self.then_input = QLineEdit('heat pump should be "<expected_status>"')

        steps_layout.addWidget(QLabel("Given"), 0, 0)
        steps_layout.addWidget(self.given_input, 0, 1)
        steps_layout.addWidget(QLabel("And"), 1, 0)
        steps_layout.addWidget(self.and1_input, 1, 1)
        steps_layout.addWidget(QLabel("And"), 2, 0)
        steps_layout.addWidget(self.and2_input, 2, 1)
        steps_layout.addWidget(QLabel("When"), 3, 0)
        steps_layout.addWidget(self.when_input, 3, 1)
        steps_layout.addWidget(QLabel("Then"), 4, 0)
        steps_layout.addWidget(self.then_input, 4, 1)

        layout.addWidget(steps_group)

        examples_group = QGroupBox("Examples / Parameter Matrix")
        examples_layout = QVBoxLayout(examples_group)

        self.examples_table = QTableWidget(0, 4)
        self.examples_table.setHorizontalHeaderLabels(["TC_ID", "setpoint", "room_temp", "expected_status"])
        self.examples_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.examples_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.examples_table.setAlternatingRowColors(True)
        examples_layout.addWidget(self.examples_table)

        btn_row = QHBoxLayout()
        self.add_example_btn = QPushButton("Add Example Row")
        self.delete_example_btn = QPushButton("Delete Selected Example")
        self.load_sample_btn = QPushButton("Load HVAC Sample")
        btn_row.addWidget(self.add_example_btn)
        btn_row.addWidget(self.delete_example_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.load_sample_btn)
        examples_layout.addLayout(btn_row)

        layout.addWidget(examples_group)

        self.add_example_btn.clicked.connect(self.add_example_row)
        self.delete_example_btn.clicked.connect(self.delete_selected_example_row)
        self.load_sample_btn.clicked.connect(self.load_sample_data)

    def _build_execution_tab(self):
        layout = QVBoxLayout(self.execution_tab)
        layout.setSpacing(10)

        exec_group = QGroupBox("Executed Test Cases")
        exec_layout = QVBoxLayout(exec_group)

        self.execution_table = QTableWidget(0, 8)
        self.execution_table.setHorizontalHeaderLabels([
            "TC_ID",
            "Setpoint",
            "Room Temp",
            "Expected",
            "Actual",
            "Status",
            "Logs",
            "Comments",
        ])
        self.execution_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.execution_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.execution_table.setAlternatingRowColors(True)
        exec_layout.addWidget(self.execution_table)

        btn_row = QHBoxLayout()
        self.add_testcase_btn = QPushButton("Add Test Case Row")
        self.delete_testcase_btn = QPushButton("Delete Selected Test Case")
        self.sync_examples_btn = QPushButton("Sync from Examples")
        btn_row.addWidget(self.add_testcase_btn)
        btn_row.addWidget(self.delete_testcase_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.sync_examples_btn)
        exec_layout.addLayout(btn_row)

        layout.addWidget(exec_group)

        summary_group = QGroupBox("Execution Summary")
        summary_layout = QGridLayout(summary_group)

        self.env_input = QLineEdit("HVAC Bench / Simulator")
        self.build_input = QLineEdit("Build-1.0.0")
        self.exec_date_input = QLineEdit(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.tester_input = QLineEdit("Automation Engineer")

        summary_layout.addWidget(QLabel("Environment"), 0, 0)
        summary_layout.addWidget(self.env_input, 0, 1)
        summary_layout.addWidget(QLabel("Build"), 0, 2)
        summary_layout.addWidget(self.build_input, 0, 3)
        summary_layout.addWidget(QLabel("Execution Date"), 1, 0)
        summary_layout.addWidget(self.exec_date_input, 1, 1)
        summary_layout.addWidget(QLabel("Executed By"), 1, 2)
        summary_layout.addWidget(self.tester_input, 1, 3)

        layout.addWidget(summary_group)

        self.add_testcase_btn.clicked.connect(self.add_execution_row)
        self.delete_testcase_btn.clicked.connect(self.delete_selected_execution_row)
        self.sync_examples_btn.clicked.connect(self.sync_execution_from_examples)

    def _build_preview_tab(self):
        layout = QVBoxLayout(self.preview_tab)
        layout.setSpacing(12)

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setHtml(
            """
            <h3>How to use</h3>
            <ol>
              <li>Define the <b>Scenario Outline</b> in the <b>BDD Design</b> tab.</li>
              <li>Add example rows for your behavior/data matrix.</li>
              <li>Use <b>Sync from Examples</b> to generate execution rows.</li>
              <li>Update Actual, Status, Logs, and Comments in <b>Test Cases</b>.</li>
              <li>Generate the HTML report to show both layers plus traceability.</li>
            </ol>
            <p>The generated report includes:</p>
            <ul>
              <li>Scenario metadata</li>
              <li>BDD Scenario Outline and Examples table</li>
              <li>Executed test cases table</li>
              <li>Traceability mapping</li>
              <li>Pass/fail summary cards</li>
            </ul>
            """
        )
        layout.addWidget(instructions)

        action_row = QHBoxLayout()
        self.generate_report_btn = QPushButton("Generate HTML Report")
        self.open_report_btn = QPushButton("Open Last Report")
        self.clear_all_btn = QPushButton("Clear All")
        action_row.addWidget(self.generate_report_btn)
        action_row.addWidget(self.open_report_btn)
        action_row.addWidget(self.clear_all_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        self.generate_report_btn.clicked.connect(self.generate_html_report)
        self.open_report_btn.clicked.connect(self.open_last_report)
        self.clear_all_btn.clicked.connect(self.clear_all)

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #0f172a;
            }
            QWidget {
                color: #e5e7eb;
                font-size: 13px;
            }
            #titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f8fafc;
            }
            #subtitleLabel {
                color: #cbd5e1;
                padding-bottom: 4px;
            }
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 14px;
                font-weight: bold;
                background: #111827;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px 0 4px;
                color: #93c5fd;
            }
            QLineEdit, QTextEdit, QTableWidget, QTabWidget::pane {
                background: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
            }
            QTableWidget {
                gridline-color: #334155;
                alternate-background-color: #0b1220;
            }
            QHeaderView::section {
                background: #1e293b;
                color: #e5e7eb;
                padding: 6px;
                border: 1px solid #334155;
            }
            QPushButton {
                background: #2563eb;
                border: none;
                border-radius: 8px;
                padding: 9px 14px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton:pressed {
                background: #1e40af;
            }
            QTabBar::tab {
                background: #1e293b;
                color: #cbd5e1;
                padding: 10px 16px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #2563eb;
                color: white;
            }
            QStatusBar {
                background: #111827;
                color: #cbd5e1;
            }
            """
        )

    def add_example_row(self, values=None):
        row = self.examples_table.rowCount()
        self.examples_table.insertRow(row)
        defaults = values or [f"TC_{row + 1:02d}", "72", "70", "ON"]
        for col, value in enumerate(defaults):
            self.examples_table.setItem(row, col, QTableWidgetItem(str(value)))

    def delete_selected_example_row(self):
        row = self.examples_table.currentRow()
        if row >= 0:
            self.examples_table.removeRow(row)

    def add_execution_row(self, values=None):
        row = self.execution_table.rowCount()
        self.execution_table.insertRow(row)
        defaults = values or [f"TC_{row + 1:02d}", "72", "70", "ON", "ON", "Pass", "", ""]
        for col, value in enumerate(defaults):
            self.execution_table.setItem(row, col, QTableWidgetItem(str(value)))

    def delete_selected_execution_row(self):
        row = self.execution_table.currentRow()
        if row >= 0:
            self.execution_table.removeRow(row)

    def sync_execution_from_examples(self):
        self.execution_table.setRowCount(0)
        for row in range(self.examples_table.rowCount()):
            tc_id = self._table_text(self.examples_table, row, 0)
            setpoint = self._table_text(self.examples_table, row, 1)
            room_temp = self._table_text(self.examples_table, row, 2)
            expected = self._table_text(self.examples_table, row, 3)
            self.add_execution_row([tc_id, setpoint, room_temp, expected, "", "Not Run", "", ""])
        self.statusBar().showMessage("Execution table synced from examples")

    def load_sample_data(self):
        self.examples_table.setRowCount(0)
        samples = [
            ["TC_01", "72", "70", "ON"],
            ["TC_02", "72", "71", "ON"],
            ["TC_03", "72", "72", "OFF"],
            ["TC_04", "72", "73", "OFF"],
            ["TC_05", "68", "65", "ON"],
        ]
        for row in samples:
            self.add_example_row(row)
        self.sync_execution_from_examples()
        self.statusBar().showMessage("HVAC sample data loaded")

    def clear_all(self):
        self.examples_table.setRowCount(0)
        self.execution_table.setRowCount(0)
        self.current_file_path = ""
        self.statusBar().showMessage("Cleared")

    def generate_html_report(self):
        if self.examples_table.rowCount() == 0:
            QMessageBox.warning(self, "Missing data", "Please add at least one example row before generating the report.")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML Report",
            f"bdd_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html)",
        )

        if not output_path:
            return

        try:
            report_html = self._build_html_report()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_html)

            self.current_file_path = output_path
            self.statusBar().showMessage(f"Report generated: {output_path}")
            QMessageBox.information(self, "Success", f"HTML report generated successfully.\n\n{output_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{exc}")

    def open_last_report(self):
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            QMessageBox.information(self, "No report", "No generated report found yet.")
            return
        webbrowser.open(f"file:///{os.path.abspath(self.current_file_path).replace(os.sep, '/')}")

    def _build_html_report(self):
        feature = self._escape(self.feature_input.text())
        scenario_title = self._escape(self.scenario_title_input.text())
        requirement_id = self._escape(self.requirement_id_input.text())
        author = self._escape(self.author_input.text())
        environment = self._escape(self.env_input.text())
        build = self._escape(self.build_input.text())
        exec_date = self._escape(self.exec_date_input.text())
        tester = self._escape(self.tester_input.text())

        given = self._escape(self.given_input.text())
        and1 = self._escape(self.and1_input.text())
        and2 = self._escape(self.and2_input.text())
        when = self._escape(self.when_input.text())
        then = self._escape(self.then_input.text())

        example_rows = []
        for row in range(self.examples_table.rowCount()):
            example_rows.append(
                {
                    "tc_id": self._escape(self._table_text(self.examples_table, row, 0)),
                    "setpoint": self._escape(self._table_text(self.examples_table, row, 1)),
                    "room_temp": self._escape(self._table_text(self.examples_table, row, 2)),
                    "expected": self._escape(self._table_text(self.examples_table, row, 3)),
                }
            )

        execution_rows = []
        pass_count = 0
        fail_count = 0
        not_run_count = 0

        for row in range(self.execution_table.rowCount()):
            status_value = self._table_text(self.execution_table, row, 5).strip()
            status_lower = status_value.lower()
            if status_lower == "pass":
                pass_count += 1
            elif status_lower == "fail":
                fail_count += 1
            else:
                not_run_count += 1

            execution_rows.append(
                {
                    "tc_id": self._escape(self._table_text(self.execution_table, row, 0)),
                    "setpoint": self._escape(self._table_text(self.execution_table, row, 1)),
                    "room_temp": self._escape(self._table_text(self.execution_table, row, 2)),
                    "expected": self._escape(self._table_text(self.execution_table, row, 3)),
                    "actual": self._escape(self._table_text(self.execution_table, row, 4)),
                    "status": self._escape(status_value),
                    "logs": self._escape(self._table_text(self.execution_table, row, 6)),
                    "comments": self._escape(self._table_text(self.execution_table, row, 7)),
                }
            )

        total_count = len(execution_rows)

        examples_html = "".join(
            f"<tr><td>{r['tc_id']}</td><td>{r['setpoint']}</td><td>{r['room_temp']}</td><td>{r['expected']}</td></tr>"
            for r in example_rows
        )

        execution_html = "".join(
            f"<tr>"
            f"<td>{r['tc_id']}</td>"
            f"<td>{r['setpoint']}</td>"
            f"<td>{r['room_temp']}</td>"
            f"<td>{r['expected']}</td>"
            f"<td>{r['actual']}</td>"
            f"<td><span class='status {self._status_class(r['status'])}'>{r['status']}</span></td>"
            f"<td>{r['logs']}</td>"
            f"<td>{r['comments']}</td>"
            f"</tr>"
            for r in execution_rows
        )

        mapping_html = "".join(
            f"<tr><td>{scenario_title}</td><td>{r['tc_id']}</td><td>{requirement_id}</td></tr>"
            for r in example_rows
        )

        generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BDD Test Report</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f6fb;
      color: #1f2937;
    }}
    .container {{
      width: 94%;
      max-width: 1400px;
      margin: 24px auto;
    }}
    .hero {{
      background: linear-gradient(135deg, #0f172a, #2563eb);
      color: white;
      padding: 28px;
      border-radius: 18px;
      box-shadow: 0 12px 30px rgba(15, 23, 42, 0.20);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 30px;
    }}
    .hero p {{
      margin: 6px 0;
      color: #dbeafe;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-top: 20px;
    }}
    .card {{
      background: white;
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
    }}
    .metric {{
      font-size: 28px;
      font-weight: bold;
      margin-top: 8px;
    }}
    .section {{
      margin-top: 22px;
      background: white;
      border-radius: 16px;
      padding: 22px;
      box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
    }}
    .section h2 {{
      margin-top: 0;
      color: #0f172a;
    }}
    .label {{
      display: inline-block;
      font-size: 12px;
      font-weight: bold;
      letter-spacing: .4px;
      text-transform: uppercase;
      color: #2563eb;
      margin-bottom: 10px;
    }}
    .bdd-box {{
      background: #0f172a;
      color: #e5e7eb;
      padding: 18px;
      border-radius: 14px;
      line-height: 1.8;
      overflow-x: auto;
    }}
    .bdd-keyword {{
      color: #93c5fd;
      font-weight: bold;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
    }}
    th, td {{
      border: 1px solid #dbe3f0;
      padding: 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eff6ff;
      color: #1e3a8a;
    }}
    tr:nth-child(even) {{
      background: #fafcff;
    }}
    .status {{
      display: inline-block;
      min-width: 76px;
      text-align: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-weight: bold;
      font-size: 12px;
    }}
    .pass {{ background: #dcfce7; color: #166534; }}
    .fail {{ background: #fee2e2; color: #991b1b; }}
    .notrun {{ background: #e5e7eb; color: #374151; }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px 18px;
      margin-top: 12px;
    }}
    .meta-item {{
      background: #f8fbff;
      border: 1px solid #dbeafe;
      border-radius: 12px;
      padding: 12px;
    }}
    .meta-item strong {{
      display: block;
      color: #1d4ed8;
      margin-bottom: 4px;
    }}
    .footer {{
      text-align: center;
      margin: 26px 0 12px;
      color: #64748b;
      font-size: 13px;
    }}
    @media (max-width: 980px) {{
      .grid {{ grid-template-columns: repeat(2, 1fr); }}
      .meta-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 600px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <h1>BDD + Test Case Execution Report</h1>
      <p><strong>Feature:</strong> {feature}</p>
      <p><strong>Scenario Outline:</strong> {scenario_title}</p>
      <p><strong>Requirement ID:</strong> {requirement_id}</p>
    </div>

    <div class="grid">
      <div class="card"><div>Total Tests</div><div class="metric">{total_count}</div></div>
      <div class="card"><div>Passed</div><div class="metric">{pass_count}</div></div>
      <div class="card"><div>Failed</div><div class="metric">{fail_count}</div></div>
      <div class="card"><div>Not Run</div><div class="metric">{not_run_count}</div></div>
    </div>

    <div class="section">
      <div class="label">Scenario metadata</div>
      <h2>Overview</h2>
      <div class="meta-grid">
        <div class="meta-item"><strong>Author</strong>{author}</div>
        <div class="meta-item"><strong>Generated On</strong>{generated_on}</div>
        <div class="meta-item"><strong>Environment</strong>{environment}</div>
        <div class="meta-item"><strong>Build</strong>{build}</div>
        <div class="meta-item"><strong>Execution Date</strong>{exec_date}</div>
        <div class="meta-item"><strong>Executed By</strong>{tester}</div>
      </div>
    </div>

    <div class="section">
      <div class="label">Behavior layer</div>
      <h2>BDD Scenario Outline</h2>
      <div class="bdd-box">
        <div><span class="bdd-keyword">Feature:</span> {feature}</div>
        <div><span class="bdd-keyword">Scenario Outline:</span> {scenario_title}</div>
        <div><span class="bdd-keyword">Given</span> {given}</div>
        <div><span class="bdd-keyword">And</span> {and1}</div>
        <div><span class="bdd-keyword">And</span> {and2}</div>
        <div><span class="bdd-keyword">When</span> {when}</div>
        <div><span class="bdd-keyword">Then</span> {then}</div>
      </div>

      <h3>Examples</h3>
      <table>
        <thead>
          <tr>
            <th>TC_ID</th>
            <th>Setpoint</th>
            <th>Room Temperature</th>
            <th>Expected Status</th>
          </tr>
        </thead>
        <tbody>
          {examples_html}
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="label">Execution layer</div>
      <h2>Executed Test Cases</h2>
      <table>
        <thead>
          <tr>
            <th>TC_ID</th>
            <th>Setpoint</th>
            <th>Room Temp</th>
            <th>Expected</th>
            <th>Actual</th>
            <th>Status</th>
            <th>Logs</th>
            <th>Comments</th>
          </tr>
        </thead>
        <tbody>
          {execution_html}
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="label">Traceability</div>
      <h2>Scenario to Test Case Mapping</h2>
      <table>
        <thead>
          <tr>
            <th>Scenario Outline</th>
            <th>Test Case ID</th>
            <th>Requirement ID</th>
          </tr>
        </thead>
        <tbody>
          {mapping_html}
        </tbody>
      </table>
    </div>

    <div class="footer">
      Generated by PyQt5 BDD + HTML Report Generator
    </div>
  </div>
</body>
</html>
        """

    def _status_class(self, status):
        s = status.strip().lower()
        if s == "pass":
            return "pass"
        if s == "fail":
            return "fail"
        return "notrun"

    def _table_text(self, table, row, col):
        item = table.item(row, col)
        return item.text() if item else ""

    def _escape(self, value):
        return html.escape(value or "")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = BDDReportGenerator()
    window.show()
    sys.exit(app.exec_())
