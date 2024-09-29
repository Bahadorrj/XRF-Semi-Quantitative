from functools import partial

import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore


class GeneralDataWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        editable: bool = False,
    ) -> None:
        super().__init__(parent)
        self._editable = editable
        self._generalDataWidgetsMap = {}
        self._initializeUi()

    def _initializeUi(self) -> None:
        self._createPlotWidget()
        self._createCoordinateLabel()
        self._createGeneralDataGroupBox()
        self._setUpView()

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget(self)
        self._plotWidget.setObjectName("plot-widget")
        # self._plotWidget.getPlotItem().setMouseEnabled(x=False, y=False)
        self._plotWidget.setBackground("#FFFFFF")
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)
        self._legend = plotItem.addLegend(
            offset=(-25, 25),
            pen=pg.mkPen(color="#E0E0E0", width=1),
            brush=pg.mkBrush(color="#F2F2F2"),
            labelTextColor="#000000",
        )
        self._plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)

    def _mouseMoved(self, pos: QtCore.QPointF) -> None:
        if self._plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self._plotWidget.getPlotItem().vb.mapSceneToView(pos)
            self._setCoordinate(mousePoint.x(), mousePoint.y())

    def _setCoordinate(self, x: float, y: float) -> None:
        self._coordinateLabel.setText(f"x= {round(x, 2)} y= {round(y, 2)}")

    def _createCoordinateLabel(self) -> None:
        self._coordinateLabel = QtWidgets.QLabel(self)
        self._coordinateLabel.setObjectName("coordinate-label")
        self._coordinateLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._setCoordinate(0, 0)

    def _createGeneralDataGroupBox(self) -> None:
        self._generalDataGroupBox = QtWidgets.QGroupBox(self)
        self._generalDataGroupBox.setTitle("General Data")

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainLayout.setSpacing(10)
        self.mainLayout.addWidget(self._plotWidget, 0, 0)
        self.mainLayout.addWidget(self._generalDataGroupBox, 0, 1, 1, 2)
        self.mainLayout.addWidget(self._coordinateLabel, 1, 0)
        self.setLayout(self.mainLayout)

    def _fillGeneralDataGroupBox(self) -> None:
        self._generalDataLayout = QtWidgets.QVBoxLayout()
        self._generalDataLayout.setSpacing(25)
        for label, widget in self._generalDataWidgetsMap.items():
            self._addWidgetToLayout(label, widget)
        self._generalDataGroupBox.setLayout(self._generalDataLayout)

    def _addWidgetToLayout(self, key: str, widget: QtWidgets.QWidget) -> None:
        widget.setFixedSize(100, 25)
        widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addWidget(QtWidgets.QLabel(f"{key}:"))
        hLayout.addWidget(widget)
        self._generalDataLayout.addLayout(hLayout)
        if isinstance(widget, QtWidgets.QLineEdit):
            widget.editingFinished.connect(
                partial(self._generalDataChanged, key, widget)
            )
        elif isinstance(widget, QtWidgets.QComboBox):
            widget.currentTextChanged.connect(
                partial(self._generalDataChanged, key, widget)
            )

    def _generalDataChanged(self, key, widget) -> None:
        pass

    def _drawCanvas(self) -> None:
        pass

    def _setPlotLimits(self, maxIntensity: int) -> None:
        xMin = -100
        xMax = 2048 + 100
        yMin = -maxIntensity * 0.1
        yMax = maxIntensity * 1.1
        self._plotWidget.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)
