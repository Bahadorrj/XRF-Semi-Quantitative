import time

icon = {'CSAN': r"myIcons\CSAN.ico",
        'peak_search': r"myIcons\peak-search.png",
        'cross': r"myIcons\cross-button.png",
        'hide': r"myIcons\hide.png",
        'unhide': r"myIcons\unhide.png",
        'exclamation': r"myIcons\exclamation.png",
        'open': r"myIcons\folder-horizontal.png",
        'conditions': r"myIcons\database.png",
        'elements': r"myIcons\map.png"
        }

addr = {'dbFundamentals': r"myFiles\fundamentals.db",
        'dbTables': r"myFiles\tables.db"}

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

