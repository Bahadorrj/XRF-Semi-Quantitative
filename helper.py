import pandas as pd

if __name__ == "__main__":
    df = pd.read_excel('Additional/elements.xlsx', "Sheet1")
    symbols = df['Symbol'].tolist()
    with open('symbols.txt', 'w') as f:
        f.write("[")
        for symbol in symbols[:-1]:
            f.write(f"'{symbol}', ")
        f.write(f"'{symbols[-1]}']")
