from Deck import Deck
from HandEvaluator import evaluate_hand, format_hand, sort_and_group_cards

deck = Deck()
deck.shuffle()
hand = deck.deal_hand()

class Person:
    def __init__(self, hand, rank):
        self.hand = hand
        self.rank = rank
        self.draw = deck.deal_hand

    def evaluate(self):
        return evaluate_hand(self.hand)

class Player(Person):
    def __init__(self, hand, rank):
        super().__init__(hand, rank)

class Dealer(Person):
    def __init__(self, hand, rank):
        super().__init__(hand, rank)

# Test: Player and Dealer drawing cards
player_hand = deck.deal_hand()
dealer_hand = deck.deal_hand()

# Grouped output
print("\nGrouped Player Hand:")
groups = sort_and_group_cards(player_hand)
for group in groups:
    print([str(card) for card in group])

player = Player(player_hand, "Player")
dealer = Dealer(dealer_hand, "Dealer")

print("\nPlayer's hand (grouped):")
for group in sort_and_group_cards(player.hand):
    print([str(card) for card in group])

rank, tiebreakers = player.evaluate()
print("Player:", format_hand(rank, tiebreakers))

print("\nDealer's hand (grouped):")
for group in sort_and_group_cards(dealer.hand):
    print([str(card) for card in group])

rank, tiebreakers = dealer.evaluate()
print("Dealer:", format_hand(rank, tiebreakers))
