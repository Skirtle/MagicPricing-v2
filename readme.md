# MagicPricing

## Setup

1. Clone the repo
2. Create and activate a virtual environment (choose one):
   - `python -m venv venv`
   - `venv\Scripts\activate`
3. Install dependencies: 
   - `pip install -r requirements.txt`
4. Run the project 
   - `python main.py`


## Things to know
### Templating
* Cards from the List are formatted in a way that the collector number is SET-NUM. Check Scryfall if not sure
* Foiling options currently only support nonfoil, foil, and etched, all case-sensetive (I think)
* Be sure to check the Scryfall for promos, they may be different than what is shown on the card (i.e. Secluded Starforge pre-release promo is actually 257s PEOE instead of just 257 EOE)