from dataclasses import dataclass, field
from hashlib import sha256
from time import sleep
import api


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
            self.response_json = api.get_api_response(self)
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
            self.response_json = api.get_api_response(self)
        
        prices = self.response_json["prices"]
        price = prices[foiling_to_price[self.foiling]]
        
        # Bad price handling
        if (price == None and self.foiling != "nonfoiil"): price = prices["usd"] # Use nonfoil price, if it exists
        if (price == None): self.price = 0.0 # No price, set to 0
        else: self.price = price
       
     

if __name__ == "__main__":
    print("Welcome to cards.py")
    card1 = Card("Alms Collector", "10", "CMM", "nonfoil", call_api = True)
    card2 = Card("Alms Collector", "10", "CMM", "foil", call_api = True)
    card3 = Card("Alms Collector", "455", "CMM", "etched", call_api = True)
    print(card1)
    print(card2)
    print(card3)