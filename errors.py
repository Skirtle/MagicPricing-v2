from cards import Card

class BadCardCallError(Exception):
    def __init__(self, code: int, card: Card) -> None:
        self.code = code
        self.card = card
        super().__init__(code)
        
    def __str__(self) -> str:
        return f"Got status code {self.code} for {self.card.name} [{self.card.collector_number}, {self.card.set}, {self.card.foiling}]"
    
    