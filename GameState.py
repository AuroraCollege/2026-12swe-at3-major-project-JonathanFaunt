# GameState.py

from Deck import Deck, Card
from DealerLogic import DealerAI

class GameState:
    def __init__(self):
        self.player_hand = []
        self.dealer_hand = []
        self.deck = Deck()
        self.stage = "betting"  # betting → draw → second_round → showdown
        self.player_chips = 500
        self.current_bet = 0
        self.dealer_message = ""
        self.dealer_folded = False

        self.dealer_ai = DealerAI()

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------
    def to_dict(self):
        return {
            "player_hand": [card.to_dict() for card in self.player_hand],
            "dealer_hand": [card.to_dict() for card in self.dealer_hand],
            "deck": self.deck.to_dict(),
            "stage": self.stage,
            "player_chips": self.player_chips,
            "current_bet": self.current_bet,
            "dealer_message": self.dealer_message,
            "dealer_folded": self.dealer_folded,
        }

    # ---------------------------------------------------------
    # Deserialization (rebuild from JSON)
    # ---------------------------------------------------------
    @staticmethod
    def from_dict(data):
        gs = GameState()

        gs.player_hand = [Card.from_dict(c) for c in data["player_hand"]]
        gs.dealer_hand = [Card.from_dict(c) for c in data["dealer_hand"]]
        gs.deck = Deck.from_dict(data["deck"])

        gs.stage = data["stage"]
        gs.player_chips = data["player_chips"]
        gs.current_bet = data["current_bet"]
        gs.dealer_message = data["dealer_message"]
        gs.dealer_folded = data["dealer_folded"]

        return gs
