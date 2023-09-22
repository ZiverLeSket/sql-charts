import qasync
import asyncio
import functools
import sys, os
from PySide6.QtWidgets import(
    QWidget,
    QApplication,
    QMenu,
    QHBoxLayout,
    QVBoxLayout,
    QMainWindow,
    QFileDialog,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QPushButton,
)
from PySide6.QtGui import QIcon, QAction
import db_reader
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QCategoryAxis, QValueAxis
from PySide6.QtCore import Qt
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
         base_path = os.path.dirname(__file__)
    return  os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Charts')
        
        self.fname :tuple

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.filemenu = QMenu()
        self.openAct = QAction('Open File')
        self.exitAct = QAction('Exit')

        self.openAct.triggered.connect(self.openFile)
        self.exitAct.triggered.connect(self.exit)
        # D:\Code\pyton\Charts\main.py
        self.filterLayout = QVBoxLayout()
        self.vLayout = QVBoxLayout()
        self.hLayout = QHBoxLayout()

        self.chart = QChart()
        self.chartview = QChartView()
        self.chartview.setChart(self.chart)
        self.vLayout.addWidget(self.chartview)

        self.data = {'':''}

        self.xparam = QComboBox()
        self.yparam = QComboBox()
        self.plotbtn = QPushButton('Plot')
        self.plotbtn.clicked.connect(self.calculateChart)

        self.series = QLineSeries()        
        
        self.createMenu()
        
    def createMenu(self):
        self.fileMenu = self.menuBar().addMenu("File")
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
    
    def openFile(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Open file')
        if self.fname[0] == '':
            return
        db = db_reader.DataBaseHandler(self.fname[0])
        self.data = db.get_start_data()
        self.charFilter()
        self.chartParams()
        self.hLayout.addLayout(self.vLayout)
        self.widget.setLayout(self.hLayout)

    def exit(self):
        self.exit()

    def charFilter(self):
        itemgroup = QGroupBox()
        checkbox = QCheckBox()
        self.filterLayout = QVBoxLayout()
        for itemclass, itemlist in self.data.items():
            hbox = QHBoxLayout()
            itemgroup = QGroupBox(itemclass)
            for item in itemlist:
                checkbox = QCheckBox(str(item))
                checkbox.setChecked(True)
                hbox.addWidget(checkbox)
            itemgroup.setLayout(hbox)
            self.filterLayout.addWidget(itemgroup)
        self.hLayout.addLayout(self.filterLayout)

    def filterUpdate(self):
        checklist = {}
        for group_id in range(self.filterLayout.count()):
            group_box: QGroupBox = self.filterLayout.itemAt(group_id).widget()
            group_box_layout = group_box.layout()
            check_box_text = []
            for check_box_id in range(group_box_layout.count()):
                check_box: QCheckBox = group_box_layout.itemAt(check_box_id).widget()
                if check_box.checkState() == Qt.CheckState.Checked:
                    check_box_text.append(check_box.text())
            checklist2 = {group_box.title():check_box_text}
            checklist.update(checklist2)
        db = db_reader.DataBaseHandler(self.fname[0])
        data = db.get_data(None, checklist)
        return data
    
    def chartParams(self):
        for itemclass, itemlist in self.data.items():
            self.xparam.addItem(str(itemclass), itemclass)
            self.yparam.addItem(str(itemclass), itemclass)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.xparam)
        hLayout.addWidget(self.yparam)
        hLayout.addWidget(self.plotbtn)
        self.vLayout.addLayout(hLayout)


    def calculateChart(self):
        data = self.filterUpdate()
        self.chart = QChart()
        self.chartview.setChart(self.chart)
        self.series = QLineSeries()
        if isinstance(data[self.xparam.currentData()][0], float) and isinstance(data[self.yparam.currentData()][0], float):
            for x in data[self.xparam.currentData()]:
                for y in data[self.yparam.currentData()]:
                    self.series.append(x, y)
            self.chart.addSeries(self.series)
            self.chart.createDefaultAxes()
        elif isinstance(data[self.xparam.currentData()][0], str) and isinstance(data[self.yparam.currentData()][0], float):
            axisX = QCategoryAxis()
            axisY = QValueAxis() 
            axisX.setMin(0)
            x_dict = {}
            axisX.setMax(data[self.xparam.currentData()].count())
            for i in range(data[self.xparam.currentData()].count()):
                axisX.append(data[self.xparam.currentData()][i], i)
                x_dict_temp = {data[self.xparam.currentData()][i]: i}
                x_dict.update(x_dict_temp)
                self.series.append(data[self.yparam.currentData()][i], x_dict[data[self.xparam.currentData()][i]])
            axisY.setRange(0.0, max(data[self.yparam.currentData()]))
            self.chart.addAxis(axisX, Qt.AlignmentFlag.AlignTop)
            self.chart.addAxis(axisY, Qt.AlignmentFlag.AlignLeft)
            self.chart.addSeries(self.series)
            

async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    app = QApplication.instance()
    app.setWindowIcon(QIcon(resource_path("ico.ico")))
    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(
            functools.partial(close_future, future, loop)
        )

    mainWindow = MainWindow()
    mainWindow.show()

    await future
    return True

if __name__ == "__main__":
    try:
        if sys.version_info.major == 3 and sys.version_info.minor == 11:
            with qasync._set_event_loop_policy(qasync.DefaultQEventLoopPolicy()):
                runner = asyncio.runners.Runner()
                try:
                    runner.run(main())
                finally:
                    runner.close()
        else:
            qasync.run(main())

    except asyncio.exceptions.CancelledError:
        sys.exit(0)