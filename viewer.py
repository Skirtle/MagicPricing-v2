import argparse, pandas as pd, numpy as np
import card_api, logger, magic_excel as me

cards: list [card_api.Card] = []
filename = "magic.xlsx"

def get_price_history_excel(filename: str) -> list[card_api.Card]:
    with me.ExcelManager(filename, "r") as file:
        sheet = file.active
        if (sheet == None): exit()
        
        end_column: int = 1
        end_row: int = 1
        while (sheet[f"{me.number_to_column(end_column + 1)}1"].value != None):
            end_column += 1
            
        while (sheet[f"A{end_row + 1}"].value != None):
            end_row += 1
            
        for row in range(2, end_row + 1):
            card_name = sheet[f"A{row}"].value
            card_num = sheet[f"B{row}"].value
            card_set = sheet[f"C{row}"].value
            card_foil = sheet[f"D{row}"].value
            card_count = sheet[f"E{row}"].value
            prices = {}
            for col in range(6, end_column + 1):
                col_letter = me.number_to_column(col)
                date = str(sheet[f"{col_letter}1"].value)
                price = sheet[f"{col_letter}{row}"].value
                if (price != None): price = float(price)
                prices[date] = price
            
            new_card = card_api.Card(card_name, card_num, card_set, card_foil, card_count, price_history = prices)
            cards.append(new_card)
            
            
    return cards

def convert_to_df(cards: list[card_api.Card]) -> pd.DataFrame:
    df = pd.DataFrame({
        f"{card.name} [{card.collector_number} {card.set} {card.foiling}]": card.price_history for card in cards
    })
    
    df.index = pd.to_datetime(df.index, format = "mixed")
    df.index.name = "Date"
    
    return df


cards = get_price_history_excel("magic.xlsx")
cards_df = convert_to_df(cards)
