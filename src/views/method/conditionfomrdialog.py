from typing import Sequence
from PyQt6 import QtWidgets

from src.views.base.formdialog import FormDialog


class ConditionFormDialog(FormDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: Sequence | None = None,
        values: Sequence | None = None,
        previousConditionName: str | None = None,
    ) -> None:
        super().__init__(parent, inputs, values)
        self._previousConditionName = previousConditionName

    def _check(self) -> None:
        self._fill()
        self._errorLabel.clear()
        mapper = {
            0: self.parent().isConditionNameValid,
            1: self.parent().isKiloVoltValid,
            2: self.parent().isMilliAmpereValid,
            3: self.parent().isTimeValid,
            5: self.parent().isEnvironmentValid,
            6: self.parent().isFilterValid,
            7: self.parent().isMaskValid,
        }
        results = [mapper[i](self._values[i]) for i in mapper]
        if results[0] is False:
            results[0] = self._values[0] == self._previousConditionName
        if not all(results):
            QtWidgets.QApplication.beep()
            errors = {
                0: "Condition name already exists!",
                1: "Kilovolt must be a number between 0 and 40 kV!",
                2: "Milliampere must be a number between 0 and 1000 mA!",
                3: "Time must be a number between 0 and 1000 ms!",
                5: "Environment is invalid!",
                6: "Filter must be one of the following integers: 1, 2, 3!",
                7: "Mask must be a one of the following integers: 1, 2, 3!",
            }
            for index, result in enumerate(results):
                if not result:
                    list(self._fields.values())[index][1].setStyleSheet("color: red;")
                    self._addError(errors[index] + "\n")
                else:
                    list(self._fields.values())[index][1].setStyleSheet("color: black;")
            return
        return super()._check()
