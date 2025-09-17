import cards_api

card1 = cards_api.Card("Chromanticore", "144", "BNG", "nonfoil", call_api = True)
card2 = cards_api.Card("Breeding Pool", "399", "RVR", "foil", call_api = True)
card3 = cards_api.Card("Hunting Cheetah", "134", "MB2", "nonfoil", call_api = True)

print(card1)
print(card2)
print(card3)