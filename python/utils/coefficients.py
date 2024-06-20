from pathlib import Path

from database import getDatabase


def calculateCoefficients(filename: str) -> list:
    out = list()
    with open(filename, "r") as f:
        line = f.readline()
        while line:
            splited = line.strip().split(":")
            symbol = splited[0].split("-")[0]
            radiation = splited[0].split("-")[1]
            intensity = int(splited[1])
            if intensity != 0:
                coefficient = 100 / intensity
                out.append((symbol, radiation, coefficient))
            line = f.readline()
    return out


def writeToDatabase(filename: str):
    db = getDatabase("fundamentals.db")
    mainSymbol = Path(filename).stem
    mainRadiation = "Ka"
    line1_id = db.executeQuery(
        f"SELECT line_id FROM lines WHERE symbol = '{mainSymbol}' AND radiation_type = '{mainRadiation}'"
    ).fetchone()[0]
    coefficients = calculateCoefficients(filename)
    for symbol, radiation, coefficient in coefficients:
        line2_id = db.executeQuery(
            f"SELECT line_id FROM lines WHERE symbol = '{symbol}' AND radiation_type = '{radiation}'"
        ).fetchone()[0]
        query = f"""
            UPDATE Interferences
            SET coefficient = {coefficient}
            WHERE (line1_id = {line1_id} AND line2_id = {line2_id}) OR (line1_id = {line2_id} AND line2_id = {line1_id});
        """
        cursor = db.executeQuery(query)
        if cursor.fetchone() is None:
            query = f"""
            INSERT INTO Interferences (
                line1_id,
                line1_symbol,
                line1_radiation_type,
                line2_id,
                line2_symbol,
                line2_radiation_type,
                coefficient,
                percentage)
            VALUES (
                {line1_id}, '{mainSymbol}', '{mainRadiation}', {line2_id}, '{symbol}', '{radiation}', {coefficient}, 0
            )
            """
            db.executeQuery(query)
            query = f"""
            INSERT INTO Interferences (
                line1_id,
                line1_symbol,
                line1_radiation_type,
                line2_id,
                line2_symbol,
                line2_radiation_type,
                coefficient,
                percentage)
            VALUES (
                {line2_id}, '{symbol}', '{radiation}', {line1_id}, '{mainSymbol}', '{mainRadiation}', {coefficient}, 0
            )
            """
            db.executeQuery(query)
    db.closeConnection()


if __name__ == "__main__":
    path = r"F:\CSAN\XRF-Semi-Quantitative\Additional\cal\Au.txt"
    writeToDatabase(path)
