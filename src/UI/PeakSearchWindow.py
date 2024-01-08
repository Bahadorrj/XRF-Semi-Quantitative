import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import mkPen, GraphicsLayoutWidget, LinearRegionItem, InfiniteLine

from src.Logic import Calculation
from src.Logic import Sqlite
from src.Logic.Backend import icons
from src.Types.ElementClass import Element
from src.UI import MessegeBox
from src.UI.TableWidget import Form


class Window(QtWidgets.QMainWindow):
    def __init__(self, size):
        super().__init__()
        # size
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.75), int(size.height() * 0.75)
        )
        # components
        self.mainLayout = QtWidgets.QVBoxLayout()
        headers = [
            "Remove Widget",
            "Hide Widget",
            "Element",
            "Type",
            "Kev",
            "Low Kev",
            "High Kev",
            "Intensity",
            "Status",
            "Activate Widget"
        ]
        self.form = Form(headers)
        self.graph = GraphicsLayoutWidget()
        self.peakPlot = self.graph.addPlot(row=0, col=0)
        self.spectrumPlot = self.graph.addPlot(row=1, col=0)
        self.peakPlotVB = self.peakPlot.vb
        self.spectrumPlotVB = self.spectrumPlot.vb
        self.spectrumRegion = LinearRegionItem()
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.coordinateLabel = QtWidgets.QLabel()
        self.mainWidget = QtWidgets.QWidget()
        # variables
        self.__dfElements = Sqlite.dataframe_of_database("fundamentals", "elements")
        self.set_elements_dataframe(Sqlite.dataframe_of_database("fundamentals", "elements"))
        self.__condition = None
        self.__elements = list()
        self.__added_elements = list()
        self.__counts = np.zeros(2048, dtype=np.int32)
        self.__px = np.zeros(2048, dtype=np.int16)
        self.__kilo_electron_volts = list()
        self.__Kev = float()

    def get_condition(self):
        return self.__condition

    def set_condition(self, condition):
        self.__condition = condition

    def get_elements(self):
        return self.__elements

    def set_elements(self, elements):
        self.__elements = elements

    def get_element(self, index):
        return self.get_elements()[index]

    def get_element_by_id(self, id):
        for element in self.get_elements():
            if element.get_attribute("element_id") == id:
                return element

    def get_added_elements(self):
        return self.__added_elements

    def set_added_elements(self, elements):
        self.__added_elements = elements

    def init_elements(self):
        elements = list()
        values = Sqlite.get_values(
            "fundamentals",
            "elements",
        )
        for value in values:
            e = Element(value[0])
            elements.append(e)
        self.set_elements(elements)

    def get_kilo_electron_volts(self):
        return self.__kilo_electron_volts

    def set_kilo_electron_volts(self, kilo_electron_volts):
        self.__kilo_electron_volts = kilo_electron_volts

    def get_kilo_electron_volt_value(self, px):
        return self.get_kilo_electron_volts()[px]

    def get_px(self):
        return self.__px

    def set_px(self, px):
        self.__px = px

    def get_counts(self):
        return self.__counts

    def set_counts(self, intensity_range):
        self.__counts = intensity_range

    def get_kev(self):
        return self.__Kev

    def set_kev(self, kev):
        self.__Kev = kev

    def get_elements_dataframe(self):
        return self.__dfElements

    def set_elements_dataframe(self, elements):
        self.__dfElements = elements

    def init_plot_items(self):
        self.spectrumPlot.setLimits(
            xMin=0, xMax=max(self.get_px()), yMin=0, yMax=1.1 * max(self.get_counts())
        )
        self.spectrumPlot.plot(
            x=self.get_px(), y=self.get_counts(), pen=mkPen("w", width=2))
        self.peakPlot.setLimits(
            xMin=0, xMax=max(self.get_px()), yMin=0, yMax=1.1 * max(self.get_counts())
        )
        self.peakPlot.plot(
            x=self.get_px(), y=self.get_counts(), pen=mkPen("w", width=2))
        self.spectrumRegion.setBounds((0, max(self.get_px())))

    def setup_ui(self, counts, condition):
        self.set_counts(counts)
        self.set_px(np.arange(0, len(self.get_counts()), 1))
        self.set_kilo_electron_volts([Calculation.px_to_ev(i) for i in self.get_px()])
        self.set_condition(condition)
        self.init_plot_items()
        self.init_elements()
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle(self.get_condition().get_attribute("name"))
        # self.showMaximized()

        # form config
        self.form.setup_ui()
        self.form.setMaximumHeight(int(self.size().height() * 0.3))
        self.form.itemClicked.connect(self.item_clicked)
        self.form.horizontalHeader().sectionClicked.connect(self.header_clicked)

        # graphics config
        self.spectrumRegion.setZValue(10)
        self.spectrumRegion.sigRegionChanged.connect(self.scale_peak_plot)
        self.spectrumPlot.showGrid(x=True, y=True)
        self.spectrumPlot.addItem(self.spectrumRegion, ignoreBounds=True)

        self.spectrumPlot.setMouseEnabled(x=False, y=False)
        self.spectrumPlot.scene().sigMouseMoved.connect(self.mouse_moved)
        self.peakPlot.setMinimumHeight(int(self.size().height() * 0.4))
        self.peakPlot.showGrid(x=True, y=True)
        self.peakPlot.scene().sigMouseClicked.connect(self.open_popup)
        self.spectrumRegion.setClipItem(self.spectrumPlot)
        self.spectrumRegion.setRegion([0, 100])
        self.peakPlot.addItem(self.vLine, ignoreBounds=True)
        self.peakPlot.addItem(self.hLine, ignoreBounds=True)
        self.peakPlotVB.scaleBy(center=(0, 0))
        self.peakPlotVB.menu.clear()
        self.mainLayout.addWidget(self.form)
        self.mainLayout.addWidget(self.graph)
        self.mainLayout.addWidget(self.coordinateLabel)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

    def mouse_moved(self, event):
        if self.peakPlot.sceneBoundingRect().contains(event):
            mouse_point = self.peakPlotVB.mapSceneToView(event)
            x = int(mouse_point.x())
            y = int(mouse_point.y())
            kev = self.get_kilo_electron_volt_value(x)
            self.set_kev(kev)
            self.coordinateLabel.setText(
                f"""<span style='font-size: 2rem'>
                        x={x}, y={y}, , kEV= {kev}
                    </span>"""
            )
            self.vLine.setPos(mouse_point.x())
            self.hLine.setPos(mouse_point.y())

    def scale_peak_plot(self):
        min_x, max_x = self.spectrumRegion.getRegion()
        self.peakPlot.setXRange(min_x, max_x, padding=0)

    def open_popup(self, event):
        pos = event.pos()
        mouse_point = self.peakPlotVB.mapSceneToView(pos)
        self.set_kev(self.get_kilo_electron_volt_value(int(mouse_point.x())))
        if event.button() == QtCore.Qt.RightButton:
            self.peakPlotVB.menu.clear()
            greater_than_low = self.get_elements_dataframe()["low_Kev"] < self.get_kev()
            smaller_than_high = self.get_kev() < self.get_elements_dataframe()["high_Kev"]
            mask = np.logical_and(greater_than_low, smaller_than_high)
            filtered_data = self.get_elements_dataframe()[mask]
            for radiation_type in ["Ka", "KB", "La", "LB", "Ly", "Ma", "Bg"]:
                type_elements = filtered_data[filtered_data["radiation_type"] == radiation_type]
                if type_elements.empty is False:
                    menu = self.peakPlotVB.menu.addMenu(radiation_type)
                    menu.triggered.connect(self.action_clicked)
                    for symbol in type_elements["symbol"].tolist():
                        menu.addAction(symbol)

    def action_clicked(self, action):
        element_symbol = action.text()
        radiation_type = action.parent().title()
        mask = np.logical_and(
            self.get_elements_dataframe()["symbol"] == element_symbol,
            self.get_elements_dataframe()["radiation_type"] == radiation_type)
        element_id = self.get_elements_dataframe()[mask]["element_id"].iloc[0]
        if element_id in self.form.get_row_ids():
            message_box = MessegeBox.Dialog(
                QtWidgets.QMessageBox.Information,
                "Duplicate  element!",
                f"{element_symbol} - {radiation_type} is already added to the table."
            )
            message_box.exec()
        else:
            element = self.get_element_by_id(element_id)
            self.init_element(element)
            self.add_element_to_form(element)

    def init_element(self, element):
        self.get_added_elements().append(element)
        element.get_region().sigRegionChanged.connect(lambda: self.set_range(element))
        all_ids = Sqlite.get_values(
            "fundamentals", "elements", column_name="element_id",
            where=f"WHERE symbol = '{element.get_attribute('symbol')}'"
        )
        for id in all_ids:
            if id[0] not in self.form.get_row_ids():
                e = self.get_element_by_id(id[0])
                self.plot_element_line(e)
        self.peakPlot.addItem(element.get_region())

    def plot_element_line(self, element):
        if element.is_activated():
            element.get_spectrum_line().setPen(mkPen("g", width=2))
            element.get_peak_line().setPen(mkPen("g", width=2))
        else:
            element.get_spectrum_line().setPen(mkPen("r", width=2))
            element.get_peak_line().setPen(mkPen("r", width=2))
        self.spectrumPlot.addItem(element.get_spectrum_line())
        self.peakPlot.addItem(element.get_peak_line())

    def plot_all_lines_of_element(self, element):
        if element.is_activated():
            self.plot_element_line(element)
        else:
            for e in self.get_elements():
                if e.get_name() == element.get_name():
                    if e.get_attribute("element_id") not in self.form.get_row_ids() or e.get_attribute(
                            "element_id") == element.get_attribute("element_id"):
                        self.plot_element_line(e)

    def remove_element_line(self, element):
        self.spectrumPlot.removeItem(element.get_spectrum_line())
        self.peakPlot.removeItem(element.get_peak_line())

    def remove_all_lines_of_element(self, element):
        if element.is_activated():
            self.remove_element_line(element)
        else:
            for e in self.get_elements():
                if e.get_name() == element.get_name():
                    if e.get_attribute("element_id") not in self.form.get_row_ids() or e.get_attribute(
                            "element_id") == element.get_attribute("element_id"):
                        self.remove_element_line(e)

    def add_element_to_form(self, element):
        remove_button = QtWidgets.QPushButton(icon=QtGui.QIcon(icons["cross"]))
        remove_button.clicked.connect(self.remove_row)
        hide_button = QtWidgets.QPushButton(icon=QtGui.QIcon(icons["unhide"]))
        hide_button.clicked.connect(self.visibility)
        element_item = QtWidgets.QTableWidgetItem(element.get_attribute("symbol"))
        element_item.setTextAlignment(QtCore.Qt.AlignCenter)
        element_item.setFlags(element_item.flags() ^ QtCore.Qt.ItemIsEditable)
        type_item = QtWidgets.QTableWidgetItem(element.get_attribute("radiation_type"))
        type_item.setTextAlignment(QtCore.Qt.AlignCenter)
        type_item.setFlags(type_item.flags() ^ QtCore.Qt.ItemIsEditable)
        kev_item = QtWidgets.QTableWidgetItem(str(element.get_attribute("Kev")))
        kev_item.setTextAlignment(QtCore.Qt.AlignCenter)
        kev_item.setFlags(kev_item.flags() ^ QtCore.Qt.ItemIsEditable)
        low_item = QtWidgets.QTableWidgetItem(str(element.get_low_kev()))
        low_item.setTextAlignment(QtCore.Qt.AlignCenter)
        low_item.setFlags(low_item.flags() ^ QtCore.Qt.ItemIsEditable)
        high_item = QtWidgets.QTableWidgetItem(str(element.get_high_kev()))
        high_item.setTextAlignment(QtCore.Qt.AlignCenter)
        high_item.setFlags(high_item.flags() ^ QtCore.Qt.ItemIsEditable)
        intensity_item = QtWidgets.QTableWidgetItem(str(element.get_intensity()))
        intensity_item.setTextAlignment(QtCore.Qt.AlignCenter)
        intensity_item.setFlags(intensity_item.flags() ^ QtCore.Qt.ItemIsEditable)
        status_item = QtWidgets.QTableWidgetItem()
        status_item.setTextAlignment(QtCore.Qt.AlignCenter)
        status_item.setFlags(status_item.flags() ^ QtCore.Qt.ItemIsEditable)
        status_button = QtWidgets.QPushButton()
        if element.is_activated():
            status_item.setText("Activated")
            status_button.setText("Deactivate")
        else:
            status_item.setText("Deactivated")
            status_button.setText("Activate")
        status_button.clicked.connect(self.status_changed)
        items = [remove_button, hide_button, element_item, type_item, kev_item,
                 low_item, high_item, intensity_item, status_item, status_button]
        self.form.add_row(items, element.get_attribute("element_id"))

    def set_range(self, element):
        low_px, high_px = element.get_region().getRegion()
        low_px = int(low_px)
        high_px = int(high_px)
        try:
            low_kev = self.get_kilo_electron_volt_value(low_px)
        except IndexError:
            low_kev = self.get_kilo_electron_volt_value(0)
        try:
            high_kev = self.get_kilo_electron_volt_value(high_px)
        except IndexError:
            high_kev = self.get_kilo_electron_volt_value(-1)
        row = self.form.get_row_by_id(element.get_attribute("element_id"))
        if low_kev > high_kev:
            low_kev = 0
        row["Low Kev"].setText(str(low_kev))
        row["High Kev"].setText(str(high_kev))

    def status_changed(self):
        row = self.form.get_current_row()
        element = self.get_element_by_id(self.form.get_current_row_id())
        if row.get("Status").text() == "Deactivated":
            self.activate_element(element, row)
        else:
            self.deactivate_element(element, row)

    def activate_element(self, element, row):
        rng = [Calculation.ev_to_px(row.get("Low Kev").text()),
               Calculation.ev_to_px(row.get("High Kev").text())]
        intensity = Calculation.calculate_intensity_in_range(rng, self.get_counts())

        row.get("Status").setText("Activated")
        row.get("Activate Widget").setText("Deactivate")
        row.get("Intensity").setText(str(intensity))

        self.remove_all_lines_of_element(element)
        self.peakPlot.removeItem(element.get_region())

        element.set_activated(True)
        element.set_low_kev(float(row.get("Low Kev").text()))
        element.set_high_kev(float(row.get("High Kev").text()))
        element.set_range(rng)
        element.set_intensity(intensity)

        self.plot_element_line(element)

    def deactivate_element(self, element, row):
        row.get("Status").setText("Deactivated")
        row.get("Activate Widget").setText("Activate")
        row.get("Intensity").setText("None")

        element.set_activated(False)

        self.plot_all_lines_of_element(element)
        self.peakPlot.addItem(element.get_region())

    def item_clicked(self):
        element = self.get_element_by_id(self.form.get_current_row_id())
        self.go_to_px(element.get_range())

    def go_to_px(self, rng):
        rng[0] -= 50
        rng[1] += 50
        self.spectrumRegion.setRegion(rng)

    def remove_row(self):
        row_index = self.form.currentRow()
        element = self.get_element(row_index)
        message_box = MessegeBox.Dialog(
            QtWidgets.QMessageBox.Warning,
            "Warning!",
            f"{element.get_attribute('symbol')} - {element.get_attribute('radiation_type')} will be removed."
        )
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        return_value = message_box.exec()
        if return_value == QtWidgets.QMessageBox.Ok:
            self.remove(element, row_index)

    def remove(self, element, index):
        element.set_activated(False)
        self.form.removeRow(index)
        self.remove_all_lines_of_element(element)
        self.peakPlot.removeItem(element.get_region())

    def visibility(self):
        id = self.form.get_current_row_id()
        element = self.get_element_by_id(id)
        if element.is_hidden():
            self.un_hide_element(element, id)
        else:
            self.hide_element(element, id)

    def hide_element(self, element, id):
        row = self.form.get_row_by_id(id)
        element.set_hidden(True)
        row.get("Hide Widget").setIcon(QtGui.QIcon(icons["hide"]))
        self.remove_all_lines_of_element(element)

    def un_hide_element(self, element, id):
        row = self.form.get_row_by_id(id)
        element.set_hidden(False)
        row.get("Hide Widget").setIcon(QtGui.QIcon(icons["unhide"]))
        self.plot_all_lines_of_element(element)

    def header_clicked(self, column):
        if column == 0:
            message_box = MessegeBox.Dialog(
                QtWidgets.QMessageBox.Warning,
                "Warning!",
                "All records will be removed.\nNote that all of the activated elements will also be deactivated.\n"
                "Press OK if you want to continue."
            )
            message_box.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            return_value = message_box.exec()
            if return_value == QtWidgets.QMessageBox.Ok:
                for element in self.get_added_elements():
                    self.remove(element, 0)
        elif column == 1:
            hidden = self.get_added_elements()[0].is_hidden()
            if hidden:
                for id in self.form.get_row_ids():
                    self.un_hide_element(self.get_element_by_id(id), id)
            else:
                for id in self.form.get_row_ids():
                    self.hide_element(self.get_element_by_id(id), id)
        elif column == 9:
            message_box = MessegeBox.Dialog(
                QtWidgets.QMessageBox.Warning,
                "Warning!",
                "All records will be activated.\nThere is no coming back after this!.\n"
                "Press OK if you want to continue."
            )
            message_box.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            return_value = message_box.exec()
            if return_value == QtWidgets.QMessageBox.Ok:
                for index, element in enumerate(self.get_added_elements()):
                    self.deactivate_element(element, self.form.get_row(index))

    def closeEvent(self, a0):
        Sqlite.write_elements_to_table(self.get_added_elements(), self.get_condition())
        self.get_added_elements().clear()
        self.form.clear()
        self.peakPlot.clear()
        self.spectrumPlot.clear()
        super().closeEvent(a0)

    def show(self):
        for element in self.get_elements():
            if element.is_activated():
                self.get_added_elements().append(element)
                self.plot_element_line(element)
                self.add_element_to_form(element)
        super().show()
