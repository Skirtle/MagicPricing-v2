import card_api, logger, excel
import pyodbc, argparse
from os import getcwd
from datetime import datetime

parser = argparse.ArgumentParser(prog = "Magic Card Pricing", description = "Logs the prices of Magic cards")
parser.add_argument("--dont_read_cache", action = "store_false", default = True, help = "Do not read from prices.cache")
parser.add_argument("--dont_write_cache", action = "store_false", default = True, help = "Do not write to prices.cache")
parser.add_argument("-l", "--log", action = "store_true", default = False, help = "Log events to the log file")
parser.add_argument("-v", "--verbose", action = "store_true", default = False, help = "Print information to the screen")
parser.add_argument("-p", "--print_cards", action = "store_true", default = False, help = "Print the cards to screen as the price is found")
parser.add_argument("-V", "--validate", action = "store_true", default = False, help = "Validate the card names. If a card does not match, stop the whole program")
parser.add_argument("-Vo", "--validate_only", action = "store_true", default = False, help = "Validate card names and write all mismatches to validate.txt")
parser.add_argument("--sql", default = "SELECT * FROM Cards", help = "Use a custom SQL query. Default is 'SELECT * FROM Cards'")
parser.add_argument("--log_file", default = "magic.log", help = "Filename where logs are stored")
parser.add_argument("--database", default = "Magic.accdb", help = "The database to read from")
parser.add_argument("--strict_mode", action = "store_true", default = False, help = "Only continue if there are no invalid cards after validation")
parser.add_argument("--clear_cache", action = "store_true", default = False, help = "Clear the cache before starting")

args = parser.parse_args()

def get_cards_from_database(filename: str, sql: str = "", autocall_api: bool = False) -> list[card_api.Card]:
    if (sql == ""): sql = "SELECT * FROM Cards"
    
    # Connect to database
    try:
        encoding = "latin-1"
        directory = getcwd() + "\\"
        driverStr = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='
        cnxn = pyodbc.connect(driverStr + directory + filename + ";")
        logger.log(f"Connection to {filename} opened", "LOG", args.log_file, args.log, args.verbose)
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
    
    logger.log(f"Fetching cards using {sql}", "LOG", args.log_file, args.log, args.verbose)
    rows = cursor.fetchall()
    logger.log(f"Found {len(rows)} cards", "LOG", args.log_file, args.log, args.verbose)
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
    
    logger.log(f"Connection to {filename} closed", "LOG", args.log_file, args.log, args.verbose)
    
    return card_list

def read_cards_from_cache() -> dict:
    cache_filename = "prices.cache"
    cache = {}
    today = datetime.today().strftime("%Y%m%d")
    
    with open(cache_filename, "r") as file:
        logger.log(f"Cache file {cache_filename} opened for reading", "LOG", args.log_file, args.log, args.verbose)
        # If date is today, we can continue
        cache_date = file.readline().strip()
        
        if (today == cache_date): # We are good to continue
            prices = [l.strip().split(",") for l in file.readlines()]
            for price in prices: cache[price[0]] = price[1]
            logger.log(f"Found {len(cache)} cached card prices", "LOG", args.log_file, args.log, args.verbose)
        
        else: logger.log(f"Cache is old, ignoring the cache", "WARNING", args.log_file, args.log, args.verbose)
    
    return cache

def write_cards_to_cache(new_cache: dict, old_cache: dict) -> None:
    cache_filename: str = "prices.cache"
    today: str = datetime.today().strftime("%Y%m%d")
    
    cache_date: str = "not today!"
    cards_added: int = 0
    with open(cache_filename, "r") as file: cache_date = file.readline().strip()
    
    if (cache_date != today): 
        # TODO: Rewrite entire cache regardless
        with open(cache_filename, "w") as file:
            logger.log(f"Cache file {cache_filename} opened for writing", "LOG", args.log_file, args.log, args.verbose)
            file.write(f"{today}\n")
            for hash_key in new_cache: 
                cards_added += 1
                file.write(f"{hash_key},{new_cache[hash_key]}\n")
            logger.log(f"Finished writing {cards_added} to the cache", "LOG", args.log_file, args.log, args.verbose)
        
    else:
        # TODO: Check if card is in old_cache. If it is not, append card to file
        with open(cache_filename, "a") as file:
            logger.log(f"Cache file {cache_filename} opened for writing", "LOG", args.log_file, args.log, args.verbose)
            
            for hash_key in new_cache:
                if (hash_key not in old_cache):
                    cards_added += 1
                    file.write(f"{hash_key},{new_cache[hash_key]}\n")
            logger.log(f"Finished writing {cards_added} to the cache", "LOG", args.log_file, args.log, args.verbose)
    
    
    return

def get_card_prices_from_api(cards: list[card_api.Card], check_cache: bool = True, write_to_cache: bool = True) -> bool:
    cache_filename: str = "prices.cache"
    old_cache: dict = {}
    new_cache: dict = {}
    invalid_cards: list[card_api.Card] = []
    today: str = datetime.today().strftime("%Y%m%d")
    
    logger.log(f"Today's date: {today}", "LOG", args.log_file, args.log, args.verbose)
    
    # Make sure the file exists
    file = open(cache_filename, "a")
    file.close()
    
    # Read the cache
    if (check_cache): old_cache = read_cards_from_cache()
    
    # If we are validating, call API for all cards, no matter what
    if (args.validate or args.validate_only): 
        # Call API for all cards, no matter what
        for card in cards:
            card_str = f"{card.name} [{card.set} {card.collector_number} {card.foiling}]"
            print(f"Validation of {logger.Color.BLUE}{card_str}{logger.Color.RESET}", end = "")
            card_valid = validate_card_name(card)
            
            if (not card_valid): 
                # We found an invalid card
                invalid_cards.append(card)
                print(f"{logger.Color.RED} failed {logger.Color.RESET}")
            else:
                print(f"{logger.Color.GREEN} succeeded {logger.Color.RESET}")
        
        
        # Write to file
        with open("validate.txt", "w") as file:
            for card in invalid_cards:
                db_card = f"{card.name} [{card.set} {card.collector_number} {card.foiling}]"
                api_card = f"{card.response_json['name']} [{card.response_json['set'].upper()} {card.response_json['collector_number']}]"
                file.write(f"Got {db_card} but found {api_card}\n")
                
        if ((len(invalid_cards) > 0 and args.strict_mode) or args.validate_only): 
            if (len(invalid_cards) > 0): logger.log("Not all cards succeeded validation, quitting", "ERROR", args.log_file, args.log, args.verbose)
            else: logger.log("All cards validated successfully", "LOG", args.log_file, args.log, args.verbose)
            return len(invalid_cards) == 0
        
    # Go through old_cache and get prices
    if (args.print_cards): print("Starting card price fetching")
    for card in cards:
        if (card in invalid_cards): 
            if (args.print_cards): print(f"\tSkipping invalid card {card}")
            continue
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
    
    # Write to cache
    if (write_to_cache): write_cards_to_cache(new_cache, old_cache)
    
    logger.log(f"Finished fetching", "LOG", args.log_file, args.log, args.verbose)
    return len(invalid_cards) == 0

def validate_card_name(card: card_api.Card) -> bool:
    card.response_json = card_api.get_api_response(card) # May as well set the price as well
    return card.name == card.response_json["name"]

if __name__ == "__main__":

    
    
    exit()
    if (args.clear_cache): 
        file = open("prices.cache", "w")
        file.close()
    
    card_list = get_cards_from_database("Magic.accdb")
    cards_valid = get_card_prices_from_api(card_list, args.dont_read_cache, args.dont_write_cache)