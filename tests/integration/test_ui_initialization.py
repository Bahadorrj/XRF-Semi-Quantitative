import inspect
import pytest
import importlib
import pkgutil


def check_initialize_ui_blueprint(cls, blueprint_methods):
    def find_method_calls(source_code, blueprint_methods):
        last_method_index = -1
        for method in blueprint_methods:
            method_index = source_code.find(f"self.{method}(")
            if method_index != -1:
                assert (
                    method_index > last_method_index
                ), f"{method} is called out of order."
                last_method_index = method_index
            else:
                return method, last_method_index
        return None, last_method_index

    current_cls = cls
    blueprint_methods_remaining = blueprint_methods.copy()

    while current_cls is not object:
        # Ensure _initializeUi method exists
        if hasattr(current_cls, "_initializeUi"):
            initialize_ui_method = getattr(current_cls, "_initializeUi")
            source_code = inspect.getsource(initialize_ui_method)

            # Check if super() is called in the current class's _initializeUi method
            if "super()._initializeUi()" in source_code:
                # Process the method calls that are in this class
                method, last_index = find_method_calls(
                    source_code, blueprint_methods_remaining
                )
                if method is None:
                    return  # All blueprint methods were found
                else:
                    # Remove the found methods from the blueprint to check the rest in the super classes
                    blueprint_methods_remaining = blueprint_methods_remaining[
                        blueprint_methods_remaining.index(method) :
                    ]

                # Move to the superclass if super()._initializeUi() is called
                current_cls = current_cls.__bases__[0]
            else:
                # Process the method calls normally if super() is not called
                find_method_calls(source_code, blueprint_methods_remaining)
                return  # No need to check further up the inheritance chain
        else:
            current_cls = current_cls.__bases__[0]

    # If we exit the loop without finding all blueprint methods, raise an error
    assert (
        not blueprint_methods_remaining
    ), f"{cls.__name__}._initializeUi or its superclasses are missing calls to: {', '.join(blueprint_methods_remaining)}."


def get_all_classes_from_package(package_name):
    classes = []
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, f"{package.__name__}."
    ):
        module = importlib.import_module(module_name)
        classes.extend(
            obj
            for name, obj in inspect.getmembers(module, inspect.isclass)
            if obj.__module__.startswith(package.__name__)
        )
    return classes


tray_classes = get_all_classes_from_package("src.views.trays")
tray_classes_blueprint = [
    "_createActions",
    "_createMenus",
    "_fillMenusWithActions",
    "_createToolBar",
    "_fillToolBarWithActions",
    "_createTableWidget",
    "_createTabWidget",
    "_setUpView",
]


# Parametrize the test function to run it for each class
@pytest.mark.parametrize(
    "cls", tray_classes, ids=[cls.__name__ for cls in tray_classes]
)
def test_ui_initialization(cls):
    check_initialize_ui_blueprint(cls, tray_classes_blueprint)
