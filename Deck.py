from dataclasses import dataclass, field
from random import shuffle
from typing import List

SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

@dataclass
class Card:
    rank: str
    suit: str
    original_index: int | None = field(default=None)

    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"

    def __repr__(self) -> str:
        return f"{self.rank!r} of {self.suit!r}"
    
    def to_dict(self):
        return {
            "rank": self.rank,
            "suit": self.suit,
            "original_index": self.original_index,
        }
    
    @staticmethod
    def from_dict(data):
        return Card(
            data["rank"],
            data["suit"],
            data.get("original_index"),
        )



class Deck:
    # A standard 52-card deck for poker.

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        #Reset the deck to a new, ordered 52-card deck.
        self._cards: List[Card] = [Card(rank, suit) for suit in SUITS for rank in RANKS]

    def shuffle(self) -> None:
        #Shuffle the deck in place.
        shuffle(self._cards)

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self):
        return iter(self._cards)

    def deal(self, count: int = 1) -> List[Card]:
        #Deal the requested number of cards from the top of the deck.
        if count < 1:
            raise ValueError("deal count must be at least 1")
        if count > len(self._cards):
            raise ValueError(f"cannot deal {count} cards from a deck of {len(self._cards)}")
        dealt_cards = self._cards[:count]
        self._cards = self._cards[count:]
        return dealt_cards

    def deal_hand(self) -> List[Card]:
        #Deal a standard 5-card poker hand.
        return self.deal(5)

    def top_card(self) -> Card:
        #Return the top card from the deck.
        return self.deal(1)[0]

    def remaining(self) -> int:
        #Return the number of cards left in the deck.
        return len(self._cards)
    
    @property
    def cards(self) -> List[Card]:
        #Return the list of remaining cards in the deck.
        return self._cards
    
    def to_dict(self):
        return {
            "cards": [card.to_dict() for card in self._cards]
        }
    
    @staticmethod
    def from_dict(data):
        d = Deck()
        d._cards = [Card.from_dict(c) for c in data["cards"]]
        return d


    