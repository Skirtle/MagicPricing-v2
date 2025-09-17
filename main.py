import card_api, pyodbc
from os import getcwd
from datetime import datetime

def get_cards_from_database(filename: str, sql: str = "", autocall_api: bool = False) -> list[card_api.Card]:
    if (sql == ""): sql = "SELECT * FROM Cards"
    
    # Connect to database
    try:
        encoding = "latin-1"
        directory = getcwd() + "\\"
        driverStr = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='
        cnxn = pyodbc.connect(driverStr + directory + filename + ";")
        cursor = cnxn.cursor()
        cnxn.setdecoding(pyodbc.SQL_CHAR, encoding=encoding)
        cnxn.setdecoding(pyodbc.SQL_WCHAR, encoding=encoding)
        cnxn.setencoding(encoding=encoding)
        print(f"Opened {filename}")
    except Exception as err:
        print(err)
        return []
    
    # Read the database
    
    try: cursor.execute(sql)
    except Exception as err: cursor.execute("SELECT * FROM Cards")
    
    rows = cursor.fetchall()
    card_list = []
    
    # Create the card objects
    for temp_card in rows:
        card_name = temp_card[0]
        card_cn = temp_card[1]
        card_set = temp_card[2]
        card_foil = temp_card[3].lower()
        card_quantity = int(temp_card[4])
        card = card_api.Card(card_name, card_cn, card_set, card_foil, quantity = card_quantity, call_api = autocall_api)
        card_list.append(card)
        
    
    # Clean up
    cursor.close()
    cnxn.close()
    
    return card_list

def get_card_prices(cards: list[card_api.Card], check_cache: bool = True, write_to_cache: bool = True) -> None:
    cache_filename = "prices.cache"
    old_cache = {}
    new_cache = {}
    today = datetime.today().strftime("%Y%m%d")
    
    if (check_cache):
        with open(cache_filename, "r") as file:
            # If date is today, we can continue
            cache_date = file.readline().strip()
            print(f"{cache_date = } {today = }")
            if (today == cache_date): # We are good to continue
                print("We are checking the old cache now")
                prices = [l.strip().split(",") for l in file.readlines()]
                for price in prices:
                    old_cache[price[0]] = price[1]
                    
    # Go through old_cache and get prices
    # If check_cache = False, then old_cache is empty no matter what
    for card in cards:
        card_hash = card.generate_hash()
        if (card_hash in old_cache):
            card.price = float(old_cache[card_hash])
            new_cache[card_hash] = float(old_cache[card_hash])
        
        else:
            card.set_price_from_api()
            new_price = card.price
            new_cache[card_hash] = new_price
            # This is where we call the API
            # We will also write the new price to the new_cache, only writing to file if allowed
    
    # Write all the new prices to the cache
    if (write_to_cache):
        print("We are now writing the new cache")
        with open(cache_filename, "w") as file:
            file.write(f"{today}\n")
            for hash_key in new_cache:
                file.write(f"{hash_key},{new_cache[hash_key]}\n")
            

x = get_cards_from_database("Magic.accdb", sql = "SELECT * FROM Cards WHERE Amount >= 2")
get_card_prices(x, True, True)