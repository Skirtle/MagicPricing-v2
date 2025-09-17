import requests
import errors
from cards import *
from time import sleep

API_CALL_TIMEOUT_MS = 100 # Must be between 50-100 ms 
API_URL = "https://api.scryfall.com"
HEADER = { "Content-Type": "application/json" }

def get_api_response(card) -> dict:
    card_url = f"{API_URL}/cards/{card.set}/{card.collector_number}"
    response = requests.get(card_url)
    sleep(API_CALL_TIMEOUT_MS / 1000)
    
    if (response.status_code != 200): raise errors.BadCardCallError(response.status_code, card)
    return response.json()

def validate_card_name(card: Card, response: dict) -> bool:
    return card.name == response["name"]

if __name__ == "__main__":
    card = Card("Faithless Looting", "220", "CMM", "nonfoil")
    print(card, card.generate_hash())
    
    response = None
    
    try: response = get_api_response(card)
    except: ... # We want to log the error here
    
    
    if (response == None): exit(2)
    
    print(response["prices"])
        
        