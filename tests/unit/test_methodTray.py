import pytest
from PyQt6 import QtWidgets
from src.utils.datatypes import Method
from src.views.trays.methodtray import MethodTrayWidget


@pytest.fixture(autouse=True)
def widget(request, qtbot, mocker, mock_methods):
    fixture_name = request.param
    if fixture_name == "widget_without_dataframe":
        widget = MethodTrayWidget()
    else:
        mocker.patch(
            "src.utils.datatypes.Method.fromATXMFile",
            return_value=Method("method_1", "none", 0),
        )
        mocker.patch("src.utils.datatypes.Method.save", new_callable=mocker.MagicMock)
        if fixture_name == "widget_with_empty_dataframe":
            widget = MethodTrayWidget(dataframe=mock_methods.drop(mock_methods.index))
        elif fixture_name == "widget_with_dataframe":
            widget = MethodTrayWidget(dataframe=mock_methods)
    qtbot.addWidget(widget)
    return widget


@pytest.mark.parametrize(
    "widget",
    [
        "widget_without_dataframe",
        "widget_with_empty_dataframe",
        "widget_with_dataframe",
    ],
    indirect=True,
)
def test_init(widget):
    assert widget is not None


@pytest.mark.parametrize(
    "widget",
    [
        "widget_with_empty_dataframe",
        "widget_with_dataframe",
    ],
    indirect=True,
)
def test_widgets(widget):
    assert widget.widgets is not None


# First set of parameters: different widget configurations
@pytest.mark.parametrize(
    "widget",
    [
        "widget_with_empty_dataframe",
        "widget_with_dataframe",
    ],
    indirect=True,
)
# Second set of parameters: different input values for the method addition
@pytest.mark.parametrize(
    "dialog_fields, expected_status",
    [
        ({"filename": "test_file1", "description": "desc1"}, "Initial state"),
        ({"filename": "test_file2", "description": "desc2"}, "Initial state"),
        ({"filename": "test_file3", "description": "desc3"}, "Initial state"),
    ],
)
def test_addMethod(mocker, widget, dialog_fields, expected_status):
    # Mocking the dialog that asks for user input
    mock_dialog = mocker.patch("src.views.trays.methodtray.MethodFormDialog")
    mock_dialog_instance = mock_dialog.return_value
    mock_dialog_instance.exec.return_value = True  # Simulate user clicking 'OK'
    mock_dialog_instance.fields = dialog_fields

    # Mocking database operations
    mock_db = mocker.patch("src.utils.database._db")
    mock_db.executeQuery = mocker.MagicMock()

    # Test the method
    before_row_count = widget.tableWidget.rowCount()
    widget.addMethod()
    after_row_count = widget.tableWidget.rowCount()

    # Check that the database query was executed correctly
    mock_db.executeQuery.assert_called_once_with(
        "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
        (dialog_fields["filename"], dialog_fields["description"], 0),
    )

    assert after_row_count == before_row_count + 1
    assert (
        widget.tableWidget.getRow(after_row_count - 1)["filename"].text()
        == dialog_fields["filename"]
    )
    assert (
        widget.tableWidget.getRow(after_row_count - 1)["description"].text()
        == dialog_fields["description"]
    )
    assert (
        widget.tableWidget.getRow(after_row_count - 1)["status"].text()
        == expected_status
    )


@pytest.mark.parametrize(
    "widget",
    [
        "widget_with_dataframe",
    ],
    indirect=True,
)
def test_removeCurrentMethod(mocker, widget):
    mock_message_box = mocker.patch("PyQt6.QtWidgets.QMessageBox")
    mock_message_box_instance = mock_message_box.return_value
    mock_message_box_instance.exec = mocker.MagicMock()
    mock_message_box_instance.exec.return_value = (
        QtWidgets.QMessageBox.StandardButton.Yes
    )
    mock_os_remove = mocker.patch("os.remove")
    mock_db = mocker.patch("src.utils.database._db")
    mock_db.executeQuery = mocker.MagicMock()
    method = widget.method

    before_row_count = widget.tableWidget.rowCount()
    widget.removeCurrentMethod()
    mock_os_remove.assert_called_once_with(f"methods/{method.filename}.atxm")
    mock_db.executeQuery.assert_called_once_with(
        "DELETE FROM Methods WHERE filename = ?", (method.filename,)
    )
    assert before_row_count == widget.tableWidget.rowCount() + 1
