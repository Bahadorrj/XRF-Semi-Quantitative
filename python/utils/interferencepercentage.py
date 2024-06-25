import pandas as pd

from python.utils.database import getDatabase
from python.utils.paths import resourcePath


def fill_interferences(database, lines: pd.DataFrame):
    for lineIndex, line in lines.iterrows():
        interference = ((lines['kiloelectron_volt'] - line['kiloelectron_volt']).abs()).sort_values()
        importantInterferences = interference[interference < 0.5]
        for index in importantInterferences.index:
            if index != lineIndex:
                percentage = round(100 - importantInterferences[index] / 0.5 * 100, 2)
                if percentage == 0:
                    break
                query = (f"""
                    INSERT INTO Interferences(
                            line1_id,
                            line1_symbol, 
                            line1_radiation_type, 
                            line2_id, 
                            line2_symbol, 
                            line2_radiation_type, 
                            percentage
                        )
                    VALUES (
                            {line['line_id']}, 
                            '{line['symbol']}',
                            '{line['radiation_type']}',
                            {lines.at[index, 'line_id']},
                            '{lines.at[index, 'symbol']}',
                            '{lines.at[index, 'radiation_type']}', 
                            {percentage}
                        );
                """)
                database.executeQuery(query)


if __name__ == '__main__':
    db = getDatabase(resourcePath('../../fundamentals.db'))
    df = db.dataframe('SELECT * FROM Lines')
    for row in df.itertuples():
        query = f"""
        UPDATE Lines 
        SET element_id = (SELECT element_id FROM Elements WHERE atomic_number = {row.atomic_number})
        WHERE line_id = {row.line_id};
        """
        db.executeQuery(query)
    db.closeConnection()
