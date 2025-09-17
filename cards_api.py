from dataclasses import dataclass, field
from hashlib import sha256
from time import sleep
import requests

API_CALL_TIMEOUT_MS = 100 # Must be between 50-100 ms 
API_URL = "https://api.scryfall.com"
HEADER = { "Content-Type": "application/json" }

foiling_to_price = {
    "nonfoil": "usd",
    "foil": "usd_foil",
    "etched": "usd_etched"
}

foil_options = ["nonfoil", "foil", "etched"]


@dataclass(init=False, order=True)
class Card:
    # Each card has a name, collector number, set, foiling. These affect the hash of the card itself
    # They also have a quanitity, but that is for the user
    sort_index: int = field(init=False, repr=False)
    name: str
    collector_number: str 
    set: str
    foiling: str # No, Yes, and Etched
    quantity: int = 1
    price: float = 0.0
    
    def __init__(self, name: str, collector_number: str, set: str, foiling: str, quantity: int = 0, call_api: bool = False):
        self.name = name
        self.collector_number = collector_number
        self.set = set
        self.foiling = foiling if foiling in foil_options else "nonfoil" # Assume nonfoil is bad foiling option
        
        if (call_api): 
            self.response_json = get_api_response(self)
            self.set_price_from_api()
        else: self.response_json = {}
        
    def __post_init__(self): object.__setattr__(self, "sort_index", self.name)
    
    def __str__(self) -> str: 
        return f"x{self.quantity} {self.name} [#{self.collector_number} {self.set}, {self.foiling}] = ${self.price}"
    
    def generate_hash(self) -> str:
        return sha256(f"{self.name}{self.collector_number}{self.set}{self.foiling}".encode()).hexdigest()
    
    def set_price_from_api(self) -> None:
        if (self.response_json == {}): 
            print("Empty API response, calling the API")
            self.response_json = get_api_response(self)
        
        prices = self.response_json["prices"]
        price = prices[foiling_to_price[self.foiling]]
        
        # Bad price handling
        if (price == None and self.foiling != "nonfoiil"): price = prices["usd"] # Use nonfoil price, if it exists
        if (price == None): self.price = 0.0 # No price, set to 0
        else: self.price = price
       
class BadCardCallError(Exception):
    def __init__(self, code: int, card: Card) -> None:
        self.code = code
        self.card = card
        super().__init__(code)
        
    def __str__(self) -> str:
        return f"Got status code {self.code} for {self.card.name} [{self.card.collector_number}, {self.card.set}, {self.card.foiling}]"


def get_api_response(card) -> dict:
    card_url = f"{API_URL}/cards/{card.set}/{card.collector_number}"
    response = requests.get(card_url)
    sleep(API_CALL_TIMEOUT_MS / 1000)
    return response.json()

if __name__ == "__main__":
    print("Welcome to cards.py")
    card1 = Card("Alms Collector", "10", "CMM", "nonfoil", call_api = True)
    card2 = Card("Alms Collector", "10", "CMM", "foil", call_api = True)
    card3 = Card("Alms Collector", "455", "CMM", "etched", call_api = True)
    print(card1)
    print(card2)
    print(card3)