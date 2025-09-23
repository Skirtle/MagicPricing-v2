import card_api, pyodbc, argparse, logger
from os import getcwd
from datetime import datetime

parser = argparse.ArgumentParser(prog = "Magic Card Pricing", description = "Logs the prices of Magic cards")
parser.add_argument("--dont_read_cache", action = "store_false", default = True, help = "Do not read from prices.cache")
parser.add_argument("--dont_write_cache", action = "store_false", default = True, help = "Do not write to prices.cache")
parser.add_argument("-l", "--log", action = "store_true", default = False, help = "Log events to the magic.log")
parser.add_argument("-v", "--verbose", action = "store_true", default = False, help = "Print information to the screen")
parser.add_argument("-p", "--print_cards", action = "store_true", default = False, help = "Print the cards to screen as the price is found")
parser.add_argument("-V", "--validate", action = "store_true", default = False, help = "Validate the card names. If a card does not match, stop the whole program")
parser.add_argument("-Vo", "--validate_only", action = "store_true", default = False, help = "Validate card names and write all mismatches to validate.txt")
parser.add_argument("--sql", default = "SELECT * FROM Cards", help = "Use a custom SQL query. Default is 'SELECT * FROM Cards'")

args = parser.parse_args()

def get_cards_from_database(filename: str, sql: str = "", autocall_api: bool = False) -> list[card_api.Card]:
    if (sql == ""): sql = "SELECT * FROM Cards"
    
    # Connect to database
    try:
        encoding = "latin-1"
        directory = getcwd() + "\\"
        driverStr = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='
        cnxn = pyodbc.connect(driverStr + directory + filename + ";")
        logger.log(f"Connection to {filename} opened", "LOG", "magic.log", args.log, args.verbose)
        cursor = cnxn.cursor()
        cnxn.setdecoding(pyodbc.SQL_CHAR, encoding=encoding)
        cnxn.setdecoding(pyodbc.SQL_WCHAR, encoding=encoding)
        cnxn.setencoding(encoding=encoding)
    except Exception as err:
        print(err)
        return []
    
    # Read the database
    
    try: cursor.execute(sql)
    except Exception as err: cursor.execute("SELECT * FROM Cards")
    
    logger.log(f"Fetching cards using {sql}", "LOG", "magic.log", args.log, args.verbose)
    rows = cursor.fetchall()
    logger.log(f"Found {len(rows)} cards", "LOG", "magic.log", args.log, args.verbose)
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
    
    logger.log(f"Connection to Access closed", "LOG", "magic.log", args.log, args.verbose)
    
    return card_list

def read_cards_from_cache() -> dict:
    cache_filename = "prices.cache"
    cache = {}
    today = datetime.today().strftime("%Y%m%d")
    
    with open(cache_filename, "r") as file:
        logger.log(f"Cache file {cache_filename} opened for reading", "LOG", "magic.log", args.log, args.verbose)
        # If date is today, we can continue
        cache_date = file.readline().strip()
        
        if (today == cache_date): # We are good to continue
            prices = [l.strip().split(",") for l in file.readlines()]
            for price in prices: cache[price[0]] = price[1]
            logger.log(f"Found {len(cache)} cached card prices", "LOG", "magic.log", args.log, args.verbose)
        
        else: logger.log(f"Cache is old, ignoring the cache", "WARNING", "magic.log", args.log, args.verbose)
    
    return cache

def write_cards_to_cache(cards: dict) -> None:
    
    
    
    return

def get_card_prices_from_api(cards: list[card_api.Card], check_cache: bool = True, write_to_cache: bool = True) -> None:
    cache_filename = "prices.cache"
    old_cache = {}
    new_cache = {}
    today = datetime.today().strftime("%Y%m%d")
    
    logger.log(f"Today's date: {today}", "LOG", "magic.log", args.log, args.verbose)
    
    # Make sure the file exists
    file = open(cache_filename, "a")
    file.close()
    
    if (check_cache):
        with open(cache_filename, "r") as file:
            logger.log(f"Cache file {cache_filename} opened for reading", "LOG", "magic.log", args.log, args.verbose)
            # If date is today, we can continue
            cache_date = file.readline().strip()
            if (today == cache_date): # We are good to continue
                prices = [l.strip().split(",") for l in file.readlines()]
                for price in prices: old_cache[price[0]] = price[1]
                logger.log(f"Found {len(old_cache)} cached card prices", "LOG", "magic.log", args.log, args.verbose)
            else:
                logger.log(f"Cache is old, ignoring the cache", "WARNING", "magic.log", args.log, args.verbose)
                    
    # Go through old_cache and get prices
    # If check_cache = False, then old_cache is empty no matter what
    for card in cards:
        if (args.validate): ... # If validate, we will call the API for each card regardless, so we can skip everything following
        
        
        card_hash = card.generate_hash()
        if (card_hash in old_cache):
            card.price = float(old_cache[card_hash])
            new_cache[card_hash] = float(old_cache[card_hash])
        
        else:
            # This is where we call the API
            # We will also write the new price to the new_cache, only writing to file if allowed
            card.set_price_from_api()
            new_price = card.price
            new_cache[card_hash] = new_price
        
        
        if (args.print_cards): print(f"\tFound {card}")
    
    # Write all the new prices to the cache
    if (write_to_cache):
        with open(cache_filename, "w") as file:
            logger.log(f"Cache file {cache_filename} opened for writing", "LOG", "magic.log", args.log, args.verbose)
            file.write(f"{today}\n")
            for hash_key in new_cache:
                file.write(f"{hash_key},{new_cache[hash_key]}\n")
            logger.log(f"Finished writing {len(new_cache)} to the cache", "LOG", "magic.log", args.log, args.verbose)
            
    logger.log(f"Finished fetching all card prices", "LOG", "magic.log", args.log, args.verbose)

def validate_card_names(cards: list[card_api.Card]) -> bool:
    
    
    
    return True

if __name__ == "__main__":
    x = get_cards_from_database("Magic.accdb")
    get_card_prices_from_api(x, True, True)