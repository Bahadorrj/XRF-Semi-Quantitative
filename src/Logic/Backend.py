import time

icons = {'CSAN': r"Icons\CSAN.ico",
         'peak_search': r"Icons\peak-search.png",
         'cross': r"Icons\cross-button.png",
         'show': r"Icons\show.png",
         'hide': r"Icons\hide.png",
         'exclamation': r"Icons\exclamation.png",
         'open': r"Icons\folder-horizontal.png",
         'conditions': r"Icons\database.png",
         'elements': r"Icons\map.png"
         }

addresses = {"fundamentals": r"..\DB\fundamentals.db",
             "tables": r"..\DB\tables.db"}


def runtime_monitor(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(
            f"Function '{func.__name__}' took {execution_time:.6f} seconds to run.")
        return result

    return wrapper
