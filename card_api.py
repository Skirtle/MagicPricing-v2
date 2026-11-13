from dataclasses import dataclass, field
from hashlib import sha256
from time import sleep
from logger import Color
from currency_converter import CurrencyConverter
import requests

API_INDIVIDUAL_CALL_TIMEOUT_MS = 100 # 10 per second at most
API_COLLECTION_CALL_TIMEOUT_MS = 500 # 2 per second at most
MAX_COLLECTION_SIZE = 75
API_URL = "https://api.scryfall.com"

DEFAULT_CURRENCY = "usd"
BASE_HEADER = {"User-Agent": "MagicPricing-v2.1"}
COLLECTION_HEADER = {"User-Agent": "MagicPricing-v2.1", "Content-Type": "application/json", "Accept": "application/json"}


foil_options = ["nonfoil", "foil", "etched"]
foiling_to_price = {
    "nonfoil": f"{DEFAULT_CURRENCY}",
    "foil": f"{DEFAULT_CURRENCY}_foil",
    "etched": f"{DEFAULT_CURRENCY}_etched"
}
currency_symbols = {
    "usd": "$",
    "eur": "€",
    "tix": "tix "
}
opposite_currency = {"usd": "eur", "eur": "usd"}
curr_conv = CurrencyConverter()

@dataclass(order=True)
class Card:
    sort_index: str = field(init=False, repr=False)
    name: str
    collector_number: str 
    set: str
    foiling: str
    quantity: int = 1
    price: float = 0.0
    call_api: bool = False
    response_json: dict = field(default_factory = dict)
    price_history: dict[str, float | None] = field(default_factory = dict)
    quantity_price: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "sort_index", self.name)
        if (self.foiling not in foil_options): self.foiling = "nonfoil"
        if (self.call_api): self.set_price_from_api()
    
    def __str__(self) -> str: return f"x{self.quantity} {Color.BLUE}{self.name}{Color.RESET} [#{self.collector_number} {self.set}, {self.foiling}] = {Color.GREEN}{currency_symbols[DEFAULT_CURRENCY]}{self.price:.2f}{Color.RESET}"
    
    def generate_hash(self) -> str: return sha256(f"{self.name}{self.collector_number}{self.set}{self.foiling}".encode()).hexdigest()
    
    def set_price_from_api(self) -> None:
        """Sets the price of the card. If there the card has not gotten an API response yet, call the API and set the price."""
        if (self.response_json == {}): self.response_json = get_card_api_response(self) # If there is no response, call API for information
        self.price = get_price_from_response(self)       
       
class BadCardError(Exception):
    def __init__(self, code: int, card: Card) -> None:
        self.code = code
        self.card = card
        super().__init__(code)
        
    def __str__(self) -> str:
        return f"Got status code {self.code} for {self.card.name} [{self.card.collector_number}, {self.card.set}, {self.card.foiling}]\nURL = {API_URL}/cards/{self.card.set}/{self.card.collector_number}"
    
class BadCollectionError(Exception):
    def __init__(self, code: int, reason: str) -> None:
        self.code = code
        self.reason = reason
        super().__init__(code)
        
    def __str__(self) -> str:
        return f"Got status code {self.code} for collection\nReason: {self.reason}"

def get_price_from_response(card: Card) -> float:
    """Use the response JSON to find the price of a card and return it

    Args:
        card (Card): The card to find the price of

    Returns:
        float: The resulting price of the card, if found. If the price was not found, 0.0 is returned. 
    """
    if (card.price != 0.0): return card.price
    prices: dict[str, float | None] = card.response_json["prices"]
    price: float | None = 0.0
    """Example response_json["prices"]
    "prices": {
        'usd': '0.45', 
        'usd_foil': '1.47',
        'usd_etched': None,
        'eur': '0.75',
        'eur_foil': '1.67',
        'tix': '2.50'
    }
    """
    if (card.foiling == "foil"):
        # Checking foil options
        price = prices[f"{DEFAULT_CURRENCY}_foil"]
        if (price == None): 
            price = prices[f"{opposite_currency[DEFAULT_CURRENCY]}_foil"]
            # Convert price, if it exists
            if (price != None): price = float(curr_conv.convert(price, opposite_currency[DEFAULT_CURRENCY].upper(), DEFAULT_CURRENCY.upper()))
    
    # If the card is nonfoil, or the foil price failed to find a price, use nonfoil
    elif (card.foiling == "nonfoil" or price == None):
        # Check nonfoil options
        price = prices[f"{DEFAULT_CURRENCY}"]
        if (price == None): 
            price = prices[f"{opposite_currency[DEFAULT_CURRENCY]}"]
            # Convert price, if it exists
            if (price != None): price = price = float(curr_conv.convert(price, opposite_currency[DEFAULT_CURRENCY].upper(), DEFAULT_CURRENCY.upper()))
        
    if (price == None): price = 0.0 # Nothing exists, I guess!
     
    return float(price)

def get_card_api_response(card: Card) -> dict:
    """Get a response from Scryfall API foor an individual card, formatted in JSON

    Args:
        card (Card): The card to check

    Raises:
        BadCardError: The card resulted in a response error

    Returns:
        dict: The response JSON from the Scryfall API
    """
    card_url = f"{API_URL}/cards/{card.set}/{card.collector_number}"
    response = requests.get(card_url, headers = BASE_HEADER)
    if (response.status_code != 200): raise BadCardError(response.status_code, card)
    sleep(API_INDIVIDUAL_CALL_TIMEOUT_MS / 1000)
    return response.json()

def create_collection_from_list(card_list: list[Card]) -> dict:
    """Create a properly formatted collection for the Scryfall API to use

    Args:
        card_list (list[Card]): The list of cards to turn into a collection

    Returns:
        dict: The JSON to send to the Scryfall API as a collection
    """
    collection = {"identifiers": []}
    for card in card_list[:75]: collection["identifiers"].append({"set": card.set, "collector_number": card.collector_number})
    return collection
    
def get_api_collection_response(collection: dict) -> dict:
    """Send a collection (75 cards max) to the Scryfall API to get card information

    Args:
        collection (dict): The properly formatted JSON to send as a collection (use create_collection_from_list() to create)

    Raises:
        BadCollectionError: The collection resulted in an error when getting a response from Scryfall

    Returns:
        dict: The collection's information for each card sent
    """
    api_collection_url = f"{API_URL}/cards/collection"
    resp = requests.post(api_collection_url, json = collection, headers = COLLECTION_HEADER)
    if (resp.status_code != 200): raise BadCollectionError(resp.status_code, resp.json()["details"])
    sleep(API_COLLECTION_CALL_TIMEOUT_MS / 1000)
    return resp.json()


if __name__ == "__main__":
    print("Welcome to card_api.py")