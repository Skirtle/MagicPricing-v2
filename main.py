import card_api, logger, magic_excel as me
import pyodbc, argparse
from os import getcwd
from datetime import datetime
from openpyxl.styles import Alignment
from openpyxl.styles import PatternFill, Border, Side, Font
from colorama import just_fix_windows_console

# Pre fixing
just_fix_windows_console()
pyodbc.pooling = False

parser = argparse.ArgumentParser(prog = "Magic Card Pricing", description = "Logs the prices of Magic cards into an Excel spreadsheet")
parser.add_argument("--dont_read_cache", action = "store_false", default = True, help = "Do not read from prices.cache")
parser.add_argument("--dont_write_cache", action = "store_false", default = True, help = "Do not write to prices.cache")
parser.add_argument("-l", "--log", action = "store_true", default = False, help = "Log events to the log file. NOT IMPLEMENTED YET") # TODO - Implement
parser.add_argument("-v", "--verbose", action = "store_true", default = False, help = "Print debug information to the screen")
parser.add_argument("-p", "--print_cards", action = "store_true", default = False, help = "Print the cards to screen as the price is found. Currently only works when using --individual") # TODO - Add this for using without -i
parser.add_argument("--sql", default = "SELECT * FROM Cards", help = "Use a custom SQL query. Default is 'SELECT * FROM Cards'")
parser.add_argument("--log_file", default = "magic.log", help = "The log file's name. NOT YET IMPLEMENTED") # TODO - Implement
parser.add_argument("--database", default = "Magic.accdb", help = "The database file to read from. Currently only allows for .accdb files") # TODO - Implement
parser.add_argument("--clear_cache", action = "store_true", default = False, help = "Clear the cache before fetching prices regardless of the date")
parser.add_argument("--excel_filename", default = "magic.xlsx", help = "The filename for the exported Excel spreadsheet. Default is 'magic.xlsx'")
parser.add_argument("-E", "--dont_export", action = "store_true", default = False, help = "Don't export to Excel")
parser.add_argument("--keep_open", action = "store_true", default = False, help = "Keep program open at the end")
parser.add_argument("--cache_filename", default = "prices.cache", help = "The filename for the price cache file. Default is 'prices.cache'")
args = parser.parse_args()

def get_cards_from_access_database(database_filename: str, sql: str = "SELECT * FROM Cards") -> list[card_api.Card]:
    """Read an Access datebase and retrieve cards from a specified query

    Args:
        filename (str): The name of the Access database
        sql (str, optional): The SQL query to specify which cards to find. Defaults to "SELECT * FROM Cards".

    Returns:
        list[card_api.Card]: A list of all the cards found from the query
    """
    if (".accdb" not in database_filename): database_filename += ".accdb"
    
    # Connect to database
    try:
        encoding = "latin-1"
        directory = getcwd() + "\\"
        driverStr = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='
        cnxn = pyodbc.connect(driverStr + directory + database_filename + ";", timeout = 10)
        logger.log(f"Connection to {database_filename} opened", "INFO", args.log_file, args.log, args.verbose)
        cursor = cnxn.cursor()
        cnxn.setdecoding(pyodbc.SQL_CHAR, encoding = encoding)
        cnxn.setdecoding(pyodbc.SQL_WCHAR, encoding = encoding)
        cnxn.setencoding(encoding = encoding)
    except Exception as err:
        print(err)
        return []
    
    # Read the database
    try: cursor.execute(sql)
    except Exception as err: 
        logger.log(f"Error when executing SQL query '{logger.Color.YELLOW}{sql}{logger.Color.RESET}', using default instead", "ERROR", args.log_file, args.log, args.verbose)
        sql = "SELECT * FROM Cards"
        cursor.execute(sql)
    
    logger.log(f"Fetching cards using '{sql}'", "INFO", args.log_file, args.log, args.verbose)
    rows = cursor.fetchall()
    logger.log(f"Found {len(rows)} cards", "INFO", args.log_file, args.log, args.verbose)
    card_list = []
    
    # Create the card objects
    for temp_card in rows:
        card_name = temp_card[0]
        card_cn = temp_card[1]
        card_set = temp_card[2]
        card_foil = temp_card[3].lower()
        card_quantity = int(temp_card[4])
        if (card_set == "PLIST"): card_set = "PLST" 
        
        card = card_api.Card(card_name, card_cn, card_set, card_foil, quantity = card_quantity)
        card_list.append(card)
        
    
    # Clean up
    cursor.close()
    cnxn.close()
    logger.log(f"Connection to {database_filename} closed", "INFO", args.log_file, args.log, args.verbose)
    return card_list

def read_prices_from_cache() -> dict[str, float]:
    """Read the latest prices from the cache of prices

    Returns:
        dict[str, float]: A dictionary where the key is the hash of the card and the value is the cached price of the card. Returns empty if no cards found or the date is not the current date. 
    """
    cache_filename: str = args.cache_filename
    cache = {}
    today = datetime.today().strftime("%Y%m%d")
    
    with open(cache_filename, "r") as file:
        logger.log(f"Cache file {cache_filename} opened for reading", "INFO", args.log_file, args.log, args.verbose)
        # If date is today, we can continue
        cache_date = file.readline().strip()
        if (today != cache_date): logger.log(f"Cache is old, ignoring the cache", "WARNING", args.log_file, args.log, args.verbose)
        
        else: # We are good to continue
            cached_price_list = [l.strip().split(",") for l in file.readlines()] # Get all the hashes and prices
            for price in cached_price_list:
                hash = price[0]
                card_price = price[1]
                cache[hash] = card_price
            logger.log(f"Found {len(cache)} cached card prices", "INFO", args.log_file, args.log, args.verbose)
    
    return cache

def write_prices_to_cache(new_cache: dict, current_cache: dict) -> None:
    cache_filename: str = args.cache_filename
    today: str = datetime.today().strftime("%Y%m%d")
    
    cache_date: str = "not today!"
    cards_added: int = 0
    with open(cache_filename, "r") as file: cache_date = file.readline().strip()
    
    if (cache_date != today): 
        with open(cache_filename, "w") as file:
            logger.log(f"Cache file {cache_filename} opened for writing", "INFO", args.log_file, args.log, args.verbose)
            
            file.write(f"{today}\n")
            for hash_key in new_cache: 
                cards_added += 1
                file.write(f"{hash_key},{new_cache[hash_key]}\n")
                
            logger.log(f"Finished writing {cards_added} to the cache", "INFO", args.log_file, args.log, args.verbose)
        
    else:
        # TODO: Check if card is in old_cache. If it is not, append card to file
        with open(cache_filename, "a") as file:
            logger.log(f"Cache file {cache_filename} opened for writing", "INFO", args.log_file, args.log, args.verbose)
            
            for hash_key in new_cache:
                if (hash_key not in current_cache):
                    cards_added += 1
                    file.write(f"{hash_key},{new_cache[hash_key]}\n")
            logger.log(f"Finished writing {cards_added} to the cache", "INFO", args.log_file, args.log, args.verbose)
    
def get_card_prices_from_api(cards: list[card_api.Card], check_cache: bool = True, write_to_cache: bool = True) -> None:
    current_cache: dict = {}
    new_cache: dict = {}
    today: str = datetime.today().strftime("%Y%m%d")
    
    logger.log(f"Today's date: {today}", "INFO", args.log_file, args.log, args.verbose)
    
    # Make sure the file exists
    file = open(args.cache_filename, "a")
    file.close()
    
    # Read the cache
    if (check_cache): current_cache = read_prices_from_cache()
        
    # Go through old_cache and get prices
    if (args.print_cards): print("Starting card price fetching")
    
    # Create collections of 75 cards each, set the cards and their prices, then create the next batch of cards
    card_collections: list[list[card_api.Card]] = []
    
    # Create the list of collections of cards
    temp_collection: list[card_api.Card] = []
    for card in cards:
        if (len(temp_collection) >= card_api.MAX_COLLECTION_SIZE):
            card_collections.append(temp_collection)
            temp_collection = []
        
        # Check if card is already cached. If not, add the card to the collection.
        card_hash = card.generate_hash()
        if (card_hash in current_cache):
            card.price = float(current_cache[card_hash])
        
        else: # Cached price for card was not found, add to collection to find later
            temp_collection.append(card)
    if (temp_collection): card_collections.append(temp_collection)
    
    
    # Get data from API for current collection
    for collection in card_collections:
        post_data = card_api.create_collection_from_list(collection)
        resp = card_api.get_api_collection_response(post_data)
        data = resp["data"]
        
        # Match data
        for card in collection:
            for resp_data in data:
                card_set = card.set.lower()
                card_cn = card.collector_number.lower()
                response_set = resp_data["set"].lower()
                response_cn = resp_data["collector_number"].lower()
                
                if (card_set == response_set and card_cn == response_cn):
                    card.response_json = resp_data
                    break
            else:
                print(f"Did not find matching data for {card}")
    
    for card in cards:
        card.set_price_from_api()
        card_hash = card.generate_hash()
        new_cache[card_hash] = card.price
    
    # Write to cache
    if (write_to_cache): write_prices_to_cache(new_cache, current_cache)
    
    logger.log(f"Finished fetching", "INFO", args.log_file, args.log, args.verbose)

# TODO - Refactor
def validate_card_name(card: card_api.Card) -> bool:
    card.response_json = card_api.get_card_api_response(card) # May as well set the price as well
    return card.name == card.response_json["name"]

# TODO - Refactor
def export_excel(filename: str, cards: list[card_api.Card], sheet_name = "Sheet") -> None:
    with me.ExcelManager(filename, "w") as file:
        sheet = file.active
        center_align = Alignment(horizontal = "center", vertical = "center")
        if (sheet == None): raise ValueError("how")
        sheet.title = sheet_name
        logger.log(f"Opened {filename}, sheet {sheet.title}", "INFO", args.log_file, args.log, args.verbose)
        
        # Initial settings
        sheet["A1"] = "Name"
        sheet["B1"] = "Number"
        sheet["C1"] = "Set"
        sheet["D1"] = "Foiling"
        sheet["E1"] = "Quantity"
        
        # Start writing data in first available space
        # Get the first empty column and set it
        new_column = me.get_first_empty_column(sheet)
        date_formatted = datetime.now().strftime("%Y-%m-%d")
        sheet[f"{new_column}1"] = date_formatted
        sheet[f"{new_column}1"].number_format = "YYYY-MM-DD"
        
        logger.log(f"Next empty column found: {new_column}, setting date to {date_formatted}", "INFO", args.log_file, args.log, args.verbose)
        
        # Start inputting  card information
        for card in cards:
            card_row = me.find_card_in_sheet(card, sheet)
            sheet[f"A{card_row}"] = card.name
            sheet[f"B{card_row}"] = card.collector_number
            sheet[f"C{card_row}"] = card.set
            sheet[f"D{card_row}"] = card.foiling
            sheet[f"E{card_row}"] = card.quantity
            sheet[f"{new_column}{card_row}"] = card.price
            sheet[f"{new_column}{card_row}"].number_format = '"$"#,##0.00'
            
        logger.log(f"Adding style and alignment to cells", "INFO", args.log_file, args.log, args.verbose)
        # Center align all of the cells
        center_align = Alignment(horizontal="center", vertical="center")
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = center_align
                
                
        fill = PatternFill(start_color="A5A5A5", end_color="A5A5A5", fill_type="solid")
        font = Font(name="Calibri", size=11, bold=True, color="FFFFFFFF")
        double_side = Side(border_style="double", color="000000")
        thin_side = Side(border_style="thin", color="000000")
        border = Border(left=thin_side, right=thin_side, top=double_side, bottom=double_side)
        
        # Fix the width/style of the columns that can/did change
        for i in [1, 2, 3, 4, 5, me.column_to_number(new_column)]:
            me.set_column_width(sheet, me.number_to_column(i))
            sheet[f"{me.number_to_column(i)}1"].fill = fill
            sheet[f"{me.number_to_column(i)}1"].border = border
            sheet[f"{me.number_to_column(i)}1"].font = font
            
    logger.log(f"Saved and closed {filename}", "INFO", args.log_file, args.log, args.verbose)

# TODO - Refactor
def main():
    if (args.clear_cache): 
        file = open("prices.cache", "w")
        file.close()
    
    card_list = get_cards_from_access_database(args.database, args.sql)
    get_card_prices_from_api(card_list, args.dont_read_cache, args.dont_write_cache)
    
    if (".xlsx" not in args.excel_filename): excel_filename = args.excel_filename + ".xlsx"
    else: excel_filename = args.excel_filename
    
    if (not args.dont_export): export_excel(excel_filename, card_list, args.database.split(".")[0])
            
    logger.log(f"Done", "INFO", args.log_file, args.log, args.verbose)
    if (args.keep_open): input("Press enter to exit ")
    
    main()
            

if __name__ == "__main__":
    main()