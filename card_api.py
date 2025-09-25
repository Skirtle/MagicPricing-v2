from dataclasses import dataclass, field
from hashlib import sha256
from time import sleep
from logger import Color
import requests

API_CALL_TIMEOUT_MS = 100 # Must be between 50-100 ms 
API_URL = "https://api.scryfall.com"

CURRENCY = "usd"

foiling_to_price = {
    "nonfoil": f"{CURRENCY}",
    "foil": f"{CURRENCY}_foil",
    "etched": f"{CURRENCY}_etched"
}
foil_options = ["nonfoil", "foil", "etched"]
currency_symbols = {
    "usd": "$",
    "eur": "€",
    "tix": "tix "
}

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

    def __post_init__(self):
        object.__setattr__(self, "sort_index", self.name)
        if (self.foiling not in foil_options): self.foiling = "nonfoil"
        if (self.call_api):
            self.response_json = get_api_response(self)
            self.set_price_from_api()
        else: self.response_json = {}
    
    def __str__(self) -> str:  return f"x{self.quantity} {Color.BLUE}{self.name}{Color.RESET} [#{self.collector_number} {self.set}, {self.foiling}] = {Color.GREEN}{currency_symbols[CURRENCY]}{self.price:.2f}{Color.RESET}"
    
    def generate_hash(self) -> str: return sha256(f"{self.name}{self.collector_number}{self.set}{self.foiling}".encode()).hexdigest()
    
    def set_price_from_api(self) -> None:
        # {'usd': '0.45', 'usd_foil': '1.47', 'usd_etched': None, 'eur': '0.75', 'eur_foil': '1.67', 'tix': '2.50'}
        if (self.response_json == {}): self.response_json = get_api_response(self)
        
        prices = self.response_json["prices"]
        price = prices[foiling_to_price[self.foiling]]
        
        # Bad price handling
        if (price == None and self.foiling != "nonfoiil"): price = prices["usd"] # Use nonfoil price, if it exists
        if (price == None): self.price = 0.0 # No price, set to 0
        else: self.price = float(price)
       
class BadCardCallError(Exception):
    def __init__(self, code: int, card: Card) -> None:
        self.code = code
        self.card = card
        super().__init__(code)
        
    def __str__(self) -> str:
        return f"Got status code {self.code} for {self.card.name} [{self.card.collector_number}, {self.card.set}, {self.card.foiling}]\nURL = {API_URL}/cards/{self.card.set}/{self.card.collector_number}"

def get_api_response(card) -> dict:
    card_url = f"{API_URL}/cards/{card.set}/{card.collector_number}"
    response = requests.get(card_url)
    sleep(API_CALL_TIMEOUT_MS / 1000)
    
    if (response.status_code != 200):
        print(card_url)
        raise BadCardCallError(response.status_code, card)
    
    return response.json()


if __name__ == "__main__":
    print("Welcome to card_api.py")
    rep = get_api_response(Card("Faithless Looting", "642", "CMM", "nonfoil"))
    for key in rep:
        print(f"{key}: {rep[key]}\n")