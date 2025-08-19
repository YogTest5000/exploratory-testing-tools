import sys
import csv
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateTimeEdit, QPushButton, QMessageBox, QFileDialog, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtGui import QBrush, QColor, QFont


APP_QSS = """
/* ---------- Base ---------- */
QMainWindow {
    background: #0f172a; /* slate-900 */
}
QWidget {
    color: #e2e8f0;      /* slate-200 */
    font-size: 13px;
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
}
QLabel {
    color: #cbd5e1;      /* slate-300 */
}

/* ---------- Inputs ---------- */
QLineEdit, QDateTimeEdit, QComboBox {
    background: #111827; /* gray-900 */
    color: #e5e7eb;      /* gray-200 */
    border: 1px solid #334155; /* slate-700 */
    border-radius: 8px;
    padding: 6px 8px;
}
QLineEdit:focus, QDateTimeEdit:focus, QComboBox:focus {
    border: 1px solid #22d3ee; /* cyan-400 */
}

/* ---------- Buttons ---------- */
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0ea5e9, stop:1 #0284c7); /* sky-500 -> sky-600 */
    border: none;
    color: white;
    padding: 8px 12px;
    border-radius: 10px;
    font-weight: 600;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #38bdf8, stop:1 #0ea5e9);
}
QPushButton:disabled {
    background: #1f2937;
    color: #6b7280;
}

/* ---------- Tabs ---------- */
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 10px;
    background: #0b1220;
}
QTabBar::tab {
    background: #0b1220;
    color: #cbd5e1;
    padding: 8px 14px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #0f172a;
    color: #22d3ee;
    font-weight: 600;
}

/* ---------- Table ---------- */
QTableWidget {
    background: #0b1220;
    alternate-background-color: #0f172a;
    gridline-color: #1f2937;
    border: 1px solid #334155;
    border-radius: 10px;
}
QHeaderView::section {
    background: #0f172a;
    color: #e2e8f0;
    padding: 6px;
    border: 0px;
    border-right: 1px solid #334155;
}
QTableWidget::item:selected {
    background: #1e293b; /* slate-800 */
}

/* ---------- Info badge ---------- */
#infoBadge {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 10px;
    color: #a5b4fc; /* indigo-300 */
}
"""


class DateRangeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # -- Date-Time Widgets (range) --
        self.from_label = QLabel("From:")
        self.from_dt = QDateTimeEdit(QDateTime.currentDateTime())
        self.from_dt.setCalendarPopup(True)

        self.to_label = QLabel("To:")
        self.to_dt = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.to_dt.setCalendarPopup(True)

        # Constrain "to" to be >= "from"
        self.to_dt.setMinimumDateTime(self.from_dt.dateTime())
        self.from_dt.dateTimeChanged.connect(self._sync_min_to)
        self.to_dt.dateTimeChanged.connect(self._ensure_order)

        # -- CSV Picker Widgets --
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setPlaceholderText("No file selected")
        self.csv_path_edit.setReadOnly(True)

        self.browse_btn = QPushButton("Browse CSV…")
        self.browse_btn.clicked.connect(self._browse_csv)

        # -- Text Search Widgets (row highlight: yellow) --
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to highlight matching rows...")
        self.search_edit.textChanged.connect(self._highlight_matches)

        self.clear_search_btn = QPushButton("Clear")
        self.clear_search_btn.clicked.connect(lambda: self.search_edit.clear())

        # -- DateTime Nearest Search Widgets (row mark: cyan) --
        self.dt_search_label = QLabel("Find nearest time:")
        self.dt_search = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_search.setCalendarPopup(True)

        self.dt_col_combo = QComboBox()
        self.dt_col_combo.setEditable(False)
        self.dt_col_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.dt_col_combo.setEnabled(False)  # enabled after CSV load

        self.find_nearest_btn = QPushButton("Find Nearest")
        self.find_nearest_btn.setEnabled(False)
        self.find_nearest_btn.clicked.connect(self._find_nearest_datetime)

        # -- Table to display CSV --
        self.table = QTableWidget()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)

        # Info/status labels
        self.info_label = QLabel("Rows: 0 | Columns: 0")
        self.info_label.setObjectName("infoBadge")

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("infoBadge")

        # Action button (demo)
        self.read_btn = QPushButton("Read Selected Range")
        self.read_btn.clicked.connect(self._show_range)

        # Track last nearest mark to clear later
        self._last_nearest_row = None

        # -- Layouts --
        # Row for date-time range
        dt_row = QHBoxLayout()
        dt_row.addWidget(self.from_label)
        dt_row.addWidget(self.from_dt, 1)
        dt_row.addSpacing(12)
        dt_row.addWidget(self.to_label)
        dt_row.addWidget(self.to_dt, 1)

        # Row for CSV picker
        csv_row = QHBoxLayout()
        csv_row.addWidget(QLabel("CSV:"))
        csv_row.addWidget(self.csv_path_edit, 1)
        csv_row.addWidget(self.browse_btn)

        # Row for text search
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.clear_search_btn)

        # Row for datetime nearest search
        dt_search_row = QHBoxLayout()
        dt_search_row.addWidget(self.dt_search_label)
        dt_search_row.addWidget(self.dt_search)
        dt_search_row.addSpacing(12)
        dt_search_row.addWidget(QLabel("In column:"))
        dt_search_row.addWidget(self.dt_col_combo, 1)
        dt_search_row.addWidget(self.find_nearest_btn)

        # Controls row (badges + demo button)
        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(self.info_label)
        ctrl_row.addSpacing(8)
        ctrl_row.addWidget(self.status_label, 1)
        ctrl_row.addWidget(self.read_btn)

        root = QVBoxLayout(self)
        root.addLayout(dt_row)
        root.addSpacing(8)
        root.addLayout(csv_row)
        root.addSpacing(8)
        root.addLayout(search_row)
        root.addSpacing(8)
        root.addLayout(dt_search_row)
        root.addSpacing(8)
        root.addWidget(self.table, 1)
        root.addSpacing(8)
        root.addLayout(ctrl_row)

    # ----- Date constraints -----
    def _sync_min_to(self, dt: QDateTime):
        self.to_dt.setMinimumDateTime(dt)
        if self.to_dt.dateTime() < dt:
            self.to_dt.setDateTime(dt)

    def _ensure_order(self, dt: QDateTime):
        if dt < self.from_dt.dateTime():
            self.to_dt.setDateTime(self.from_dt.dateTime())

    # ----- CSV loading -----
    def _browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV file",
            str(Path.home()),
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if path:
            self.csv_path_edit.setText(path)
            self._load_csv_to_table(path)
            # Re-run highlight in case there is already text in the box
            self._highlight_matches(self.search_edit.text())

    def _load_csv_to_table(self, filepath: str):
        try:
            try_encodings = ("utf-8-sig", "utf-8")
            reader = None
            f = None
            for enc in try_encodings:
                try:
                    f = open(filepath, "r", encoding=enc, newline="")
                    reader = csv.reader(f)
                    first_row = next(reader, None)
                    if first_row is None:
                        f.close()
                        raise ValueError("CSV is empty.")
                    break
                except UnicodeDecodeError:
                    if f and not f.closed:
                        f.close()
                    continue

            if reader is None:
                raise UnicodeDecodeError("csv", b"", 0, 1, "Unable to decode")

            headers = [h if h is not None else "" for h in first_row]
            self.table.clear()
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)

            rows = [row for row in reader]
            f.close()

            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                row = (row + [""] * len(headers))[:len(headers)]
                for c, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.table.setItem(r, c, item)

            # Resize columns
            if len(headers) <= 6:
                self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            else:
                self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

            self.info_label.setText(f"Rows: {len(rows)} | Columns: {len(headers)}")

            # Clear any previous highlights / selections / nearest mark
            self._clear_all_highlights()
            self._clear_nearest_mark()
            self.table.clearSelection()

            # Populate datetime column selector
            self.dt_col_combo.clear()
            self.dt_col_combo.addItems(headers)
            self.dt_col_combo.setEnabled(True)
            self.find_nearest_btn.setEnabled(True)

            self.status_label.setText("CSV loaded ✔")

        except Exception as e:
            QMessageBox.critical(self, "Failed to Load CSV", f"Error: {e}")
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.dt_col_combo.clear()
            self.dt_col_combo.setEnabled(False)
            self.find_nearest_btn.setEnabled(False)
            self.info_label.setText("Rows: 0 | Columns: 0")
            self.status_label.setText("Load failed")

    # ----- Text Search & highlight (yellow) -----
    def _highlight_matches(self, text: str):
        """Highlight rows containing 'text' (case-insensitive) across any column."""
        query = (text or "").strip().lower()
        self._clear_all_highlights()
        if not query:
            return

        yellow = QBrush(QColor(255, 255, 0))
        rows = self.table.rowCount()
        cols = self.table.columnCount()

        for r in range(rows):
            row_matches = False
            for c in range(cols):
                item = self.table.item(r, c)
                if item and query in item.text().lower():
                    row_matches = True
                    break
            if row_matches:
                for c in range(cols):
                    item = self.table.item(r, c)
                    if item:
                        item.setBackground(yellow)

    def _clear_all_highlights(self):
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        clear_brush = QBrush()
        for r in range(rows):
            for c in range(cols):
                item = self.table.item(r, c)
                if item:
                    item.setBackground(clear_brush)
                    f = item.font()
                    f.setBold(False)
                    item.setFont(f)

    # ----- DateTime Nearest Search (cyan) -----
    def _find_nearest_datetime(self):
        if self.table.rowCount() == 0 or self.table.columnCount() == 0:
            QMessageBox.warning(self, "No Data", "Please load a CSV first.")
            return

        col_index = self.dt_col_combo.currentIndex()
        if col_index < 0:
            QMessageBox.warning(self, "No Column", "Please choose a datetime column.")
            return

        target = self.dt_search.dateTime()
        best_row, best_abs_secs, parsed_dt = self._nearest_row_for_datetime(col_index, target)

        if best_row is None:
            self.status_label.setText("No parseable datetimes found in selected column.")
            QMessageBox.information(self, "No Parseable Dates",
                                    "Could not parse any datetimes in the selected column.")
            return

        # Mark nearest row (cyan), bold text; clear previous mark
        self._clear_nearest_mark()
        cyan = QBrush(QColor(173, 216, 230))  # light cyan
        cols = self.table.columnCount()
        for c in range(cols):
            it = self.table.item(best_row, c)
            if it:
                it.setBackground(cyan)
                f = it.font(); f.setBold(True); it.setFont(f)

        # Select and scroll to the best row
        self.table.clearSelection()
        self.table.setCurrentCell(best_row, max(0, col_index))
        self.table.selectRow(best_row)
        self.table.scrollToItem(self.table.item(best_row, max(0, col_index)),
                                hint=QTableWidget.PositionAtCenter)

        # Save last marked row
        self._last_nearest_row = best_row

        # Status
        delta_text = self._format_delta(best_abs_secs)
        self.status_label.setText(
            f"Nearest match → row {best_row + 1}, time={parsed_dt.toString('yyyy-MM-dd HH:mm:ss')}, Δ={delta_text}"
        )

    def _clear_nearest_mark(self):
        if self._last_nearest_row is None:
            return
        row = self._last_nearest_row
        cols = self.table.columnCount()
        for c in range(cols):
            item = self.table.item(row, c)
            if item:
                item.setBackground(QBrush())
                f = item.font(); f.setBold(False); item.setFont(f)
        self._last_nearest_row = None

    def _nearest_row_for_datetime(self, col_index: int, target: QDateTime):
        """Return (row_index, |delta_secs|, parsed_dt) for row with nearest datetime in given column."""
        rows = self.table.rowCount()
        best_row = None
        best_abs_secs = None
        best_dt = None

        for r in range(rows):
            item = self.table.item(r, col_index)
            if not item:
                continue
            dt = self._parse_dt_flex(item.text())
            if not dt.isValid():
                continue
            diff_secs = abs(dt.secsTo(target))
            if (best_abs_secs is None) or (diff_secs < best_abs_secs):
                best_abs_secs = diff_secs
                best_row = r
                best_dt = dt

        return best_row, best_abs_secs, best_dt

    def _parse_dt_flex(self, text: str) -> QDateTime:
        """
        Try several common datetime formats and return a QDateTime.
        Add/adjust formats as needed to match your CSV.
        """
        s = (text or "").strip()
        if not s:
            return QDateTime()

        fmts = [
            "yyyy-MM-dd HH:mm:ss",
            "yyyy-MM-dd HH:mm",
            "yyyy-MM-dd'T'HH:mm:ss",
            "yyyy-MM-dd'T'HH:mm",
            "MM/dd/yyyy HH:mm:ss",
            "MM/dd/yyyy HH:mm",
            "MM/dd/yyyy",
            "dd/MM/yyyy HH:mm:ss",
            "dd/MM/yyyy HH:mm",
            "dd/MM/yyyy",
            "yyyy/MM/dd HH:mm:ss",
            "yyyy/MM/dd HH:mm",
            "yyyy/MM/dd",
            "yyyy-MM-dd",
            "HH:mm:ss",
            "HH:mm",
        ]

        for fmt in fmts:
            dt = QDateTime.fromString(s, fmt)
            if dt.isValid():
                # If time-only, assume today's date
                if "H" in fmt and all(token not in fmt for token in ["y", "M", "d"]):
                    today = QDateTime.currentDateTime()
                    dt.setDate(today.date())
                dt.setTimeSpec(Qt.LocalTime)
                return dt

        dt = QDateTime.fromString(s, Qt.ISODate)
        if dt.isValid():
            dt.setTimeSpec(Qt.LocalTime)
            return dt

        return QDateTime()  # invalid

    def _format_delta(self, seconds: int) -> str:
        if seconds is None:
            return "n/a"
        s = int(seconds)
        sign = ""  # absolute already
        mins, sec = divmod(s, 60)
        hrs, mins = divmod(mins, 60)
        days, hrs = divmod(hrs, 24)
        parts = []
        if days: parts.append(f"{days}d")
        if hrs:  parts.append(f"{hrs}h")
        if mins: parts.append(f"{mins}m")
        parts.append(f"{sec}s")
        return sign + " ".join(parts)

    # ----- Demo: read current range -----
    def get_range(self):
        return self.from_dt.dateTime(), self.to_dt.dateTime()

    def _show_range(self):
        f, t = self.get_range()
        csv_path = self.csv_path_edit.text().strip() or "(none)"
        msg = (
            f"From: {f.toString('yyyy-MM-dd HH:mm:ss')}\n"
            f"To:   {t.toString('yyyy-MM-dd HH:mm:ss')}\n"
            f"CSV:  {csv_path}"
        )
        QMessageBox.information(self, "Selected Inputs", msg)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Viewer • Search & Nearest Time")
        tabs = QTabWidget()
        tabs.addTab(DateRangeTab(), "Date Range & CSV")
        self.setCentralWidget(tabs)
        self.resize(1180, 640)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
