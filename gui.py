import dearpygui.dearpygui as dpg, numpy as np, pandas as pd
import card_api, logger, magic_excel as me


def get_price_history_excel(filename: str) -> list[card_api.Card]:
    cards = []
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

def convert_to_df(cards: list[card_api.Card], drop_nan: bool = True) -> pd.DataFrame:
    df = pd.DataFrame({
        f"{card.name} [{card.collector_number} {card.set} {card.foiling}]": card.price_history for card in cards
    })
    
    df.index = pd.to_datetime(df.index, format = "mixed")
    df.index.name = "Date"
    
    if (drop_nan):
        for card in df:
            df[card].dropna()
    
    return df
  
def main():
    def callback_card_chosen(sender, data):
        logger.log_to_screen(f"Card chosen: {data}", "LOG")
        update_graph_table(data)

    def update_graph_table(card_name):
        # Get and set axis information
        card_series = cards_df[card_name].dropna()
        x = (card_series.index.astype("int64") // 1e9).tolist()
        y = card_series.values.tolist()
        dpg.set_value("price_series", [x, y])
        
        # Fit the axis
        dpg.fit_axis_data("x_axis")
        y_max = max(y) if y else 1
        dpg.set_axis_limits("y_axis", 0, y_max * 1.1)
        

        # Update text
        if (all_cards_added): 
            logger.log_to_screen(f"{card_name} already added to table", "WARNING")
            return
        with dpg.table_row(parent = "recent_cards"):
            dpg.add_text(f"{card_name}") # Card name
            dpg.add_text(f"${y[-1]:,.2f}") # Current price
            dpg.add_text(f"${max(y):,.2f}") # Highest price
            dpg.add_text(f"${min(y):,.2f}") # Lowest price
            dpg.add_text(f"${np.average(y):,.2f}") # Total average
            dpg.add_text(f"${np.average(y[-7]):,.2f}") # Last week average
            
        added_cards.append(card_name)

    def callback_set_all_cards(sender, data):
        # Check if already added all cards. If have, stop
        nonlocal all_cards_added
        if (all_cards_added):
            logger.log_to_screen("Already added all cards to the table", "WARNING")
            return
        logger.log_to_screen("Adding all cards to the table", "LOG")
        
        # Loop through already added cards, do not add ones already there
        for card in cards_df:
            if card in added_cards:
                logger.log_to_screen(f"Already added {card}, skipping", "WARNING")
            else:
                with dpg.table_row(parent = "recent_cards"):
                    dpg.add_text(f"{card}") # Card name
                    dpg.add_text(f"${cards_df[card].dropna().iloc[-1]:,.2f}") # Current price
                    dpg.add_text(f"${max(cards_df[card].dropna()):,.2f}") # Highest price
                    dpg.add_text(f"${min(cards_df[card].dropna()):,.2f}") # Lowest price
                    dpg.add_text(f"${np.average(cards_df[card].dropna()):,.2f}") # Total average
                    try:
                        # Try to get the 7 day average
                        dpg.add_text(f"${np.average(cards_df[card].dropna().iloc[-7]):,.2f}") # Last week average
                    except:
                        # Fails (usually due to less than 7 days of data). Use normal average instead
                        dpg.add_text(f"${np.average(cards_df[card].dropna()):,.2f}") # Last week average
        
        # Set all_cards_added to True
        all_cards_added = True
    
    # global all_cards_added # idk why i need to set this to global but no other variable
    all_cards_added = False
    filename = "magic.xlsx"
    logger.log_to_screen(f"File {filename} chosen", "LOG")
    cards = get_price_history_excel(filename)
    logger.log_to_screen(f"Retrieving prices from {filename}", "LOG")
    cards_df = convert_to_df(cards)
    cards_df = cards_df[sorted(cards_df.columns)]
    logger.log_to_screen(f"Converting cards to dataframe", "LOG")
    added_cards = []
    
    
    # Create main window
    dpg.create_context()
    with dpg.window(tag = "main_window"):
        # Drop down menu for selecting a card
        dpg.add_combo(label = "Cards", items = list(cards_df.keys()), callback = callback_card_chosen)
        
        # Line graph for price history
        with dpg.plot(label = "History", height = 800, width = -1):
            dpg.add_plot_axis(dpg.mvXAxis, label = "Date", tag = "x_axis", tick_format = "%Y-%m-%d", scale = dpg.mvPlotScale_Time)
            dpg.add_plot_axis(dpg.mvYAxis, label = "Price", tag = "y_axis", tick_format = "$%.2f")
            dpg.add_line_series([], [], label = "Price", parent = "y_axis", tag = "price_series")
        
        
        # Table with all/recent cards
        dpg.add_button(label = "Add all cards to table", callback = callback_set_all_cards)
        with dpg.table(header_row = True, tag = "recent_cards", resizable = True, borders_innerH = True, borders_innerV = True, borders_outerH = True, borders_outerV = True, policy = dpg.mvTable_SizingFixedFit):
            dpg.add_table_column(label = "Card name", width_stretch = True) # Card name
            dpg.add_table_column(label = "Current price", width_stretch = True) # Current price
            dpg.add_table_column(label = "Highest price", width_stretch = True) # Highest price
            dpg.add_table_column(label = "Lowest price", width_stretch = True) # Lowest price
            dpg.add_table_column(label = "Average price (all time)", width_stretch = True) # Total average
            dpg.add_table_column(label = "Average price (1 week)", width_stretch = True) # Last week average

    # Run that shit
    dpg.create_viewport(title = "Card Pricing History and Statistics", width = 1280, height = 1024) 
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main_window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()