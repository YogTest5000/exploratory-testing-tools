import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QTableView, \
    QMessageBox, QComboBox, QHBoxLayout
from PyQt5.QtCore import QAbstractTableModel, Qt
from bokeh.plotting import figure, show
from bokeh.io import output_file
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.models import DatetimeTickFormatter


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            if orientation == Qt.Vertical:
                return str(self._data.index[section])
        return None


class CSVViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None  # Ensure df is initialized early
        self.initUI()

    def initUI(self):
        self.setWindowTitle("CSV Data Viewer and Bokeh Plotter")
        self.setGeometry(100, 100, 800, 600)

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.layout = QVBoxLayout()
        self.centralWidget.setLayout(self.layout)

        self.loadButton = QPushButton("Load CSV File")
        self.loadButton.clicked.connect(self.loadCSV)
        self.layout.addWidget(self.loadButton)

        self.tableView = QTableView()
        self.layout.addWidget(self.tableView)

        self.columnSelectorX = QComboBox()
        self.ySelectors = []

        self.selectorLayout = QHBoxLayout()
        self.selectorLayout.addWidget(self.columnSelectorX)

        self.addYSelector()
        self.addYSelectorButton = QPushButton("Add Y Axis Column")
        self.addYSelectorButton.clicked.connect(self.addYSelector)
        self.layout.addLayout(self.selectorLayout)
        self.layout.addWidget(self.addYSelectorButton)

        self.plotButton = QPushButton("Plot Selected Columns")
        self.plotButton.clicked.connect(self.plotData)
        self.layout.addWidget(self.plotButton)

    def addYSelector(self):
        ySelector = QComboBox()
        self.ySelectors.append(ySelector)
        self.selectorLayout.addWidget(ySelector)
        if self.df is not None:
            ySelector.addItems(self.df.columns)

    def loadCSV(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)",
                                                  options=options)

        if filePath:
            try:
                self.df = pd.read_csv(filePath, parse_dates=True)
                self.model = PandasModel(self.df)
                self.tableView.setModel(self.model)

                self.columnSelectorX.clear()
                self.columnSelectorX.addItems(self.df.columns)

                for selector in self.ySelectors:
                    selector.clear()
                    selector.addItems(self.df.columns)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def plotData(self):
        if self.df is None:
            QMessageBox.warning(self, "Warning", "No data loaded!")
            return

        x_col = self.columnSelectorX.currentText()
        y_cols = [selector.currentText() for selector in self.ySelectors if selector.currentText()]

        if not x_col or not y_cols:
            QMessageBox.warning(self, "Warning", "Please select X and at least one Y column.")
            return

        try:
            self.df[x_col] = pd.to_datetime(self.df[x_col], errors='coerce')
            if self.df[x_col].isnull().all():
                QMessageBox.critical(self, "Error", "Selected X column is not a valid datetime.")
                return

            output_file("bokeh_plot.html")
            p = figure(title=f"Plot of {', '.join(y_cols)} vs {x_col}", x_axis_label=x_col, width=800, height=600,
                       x_axis_type='datetime')
            p.xaxis.formatter = DatetimeTickFormatter()

            for y_col in y_cols:
                p.line(self.df[x_col], self.df[y_col], legend_label=y_col, line_width=2)

            html = file_html(p, CDN, "Bokeh Plot")
            show(p)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CSVViewer()
    viewer.show()
    sys.exit(app.exec_())
