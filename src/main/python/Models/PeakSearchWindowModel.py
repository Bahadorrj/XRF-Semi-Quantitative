from src.main.python.Logic.Sqlite import DATABASES

def writeElementToTable(elements, condition):
    connection = DATABASES.get("fundamentals").getConnection()
    cur = connection.cursor()
    for element in elements:
        if element.isActivated():
            query = f"""
                UPDATE elements
                SET low_Kev = {element.getLowKev()},
                    high_Kev = {element.getHighKev()},
                    intensity = {element.getIntensity()},
                    active = 1,
                    condition_id =
                        (SELECT condition_id
                        FROM conditions
                        WHERE conditions.name = '{condition.getName()}')
                WHERE element_id = {element.getAttribute("element_id")};
            """
            cur.execute(query)
        else:
            query = f"""
                UPDATE elements
                SET intensity = null,
                    active = 0,
                    condition_id = null
                WHERE element_id = {element.getAttribute("element_id")};
            """
            cur.execute(query)
    connection.commit()
