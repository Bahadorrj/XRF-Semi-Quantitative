from python.Logic.Sqlite import DatabaseConnection
import qrcResources

def writeElementToTable(elements, conditionID):
    database = DatabaseConnection.getInstance(":fundamentals.db")
    for element in elements:
        if element.activated:
            query = f"""
                UPDATE elements
                SET low_Kev = {element.lowKev},
                    high_Kev = {element.highKev},
                    intensity = {element.intensity},
                    active = 1,
                    condition_id = {conditionID}
                WHERE element_id = {element.getAttribute("element_id")};
            """
            database.executeQuery(query)
        else:
            query = f"""
                UPDATE elements
                SET intensity = null,
                    active = 0,
                    condition_id = null
                WHERE element_id = {element.getAttribute("element_id")};
            """
            database.executeQuery(query)
