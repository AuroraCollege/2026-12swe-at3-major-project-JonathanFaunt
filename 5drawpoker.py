from Deck import Deck
from HandEvaluator import *
from DealerLogic import DealerAI

# This isn't actually used in the Flask app, mainly because this is a version made specifically for the terminal.
# May be deleted soon

dealer_ai = DealerAI()
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

    def discard_and_draw(self, indexes, deck):
        for i in indexes:
            self.hand[i] = deck.top_card()

class Player(Person):
    def __init__(self, hand, rank, chips=100):
        super().__init__(hand, rank)
        self.chips = chips

class Dealer(Person):
    def __init__(self, hand, rank):
        super().__init__(hand, rank)

    def choose_discards(self):
        # Keep pairs or better, discard everything else
        values = [convert_ranks_to_values([card.rank])[0] for card in self.hand]
        counts = {v: values.count(v) for v in set(values)}

        # Keep any card that is part of a pair or better
        keep_values = {v for v, c in counts.items() if c >= 2}

        # Discard everything else
        discards = [i for i, card in enumerate(self.hand)
                if convert_ranks_to_values([card.rank])[0] not in keep_values]

        return discards[:3]  # dealer never discards more than 3

def play_round():
    deck = Deck()
    deck.shuffle()

    player.hand = deck.deal_hand()
    dealer = Dealer(deck.deal_hand(), "Dealer")

    print(f"\nYou have {player.chips} chips.")
    bet = int(input("Enter your bet: "))

    if bet > player.chips:
        print("You cannot bet more than you have.")
        return

    player.chips -= bet

    print("\nYour hand:")
    for i, card in enumerate(player.hand):
        print(f"{i}: {card}")

    # Player chooses discards
    while True:
        raw = input("\nEnter card indexes to discard (0-4), separated by spaces: ")
        if not raw.strip():
            player_discards = []
            break
        try:
            indices = [int(x) for x in raw.split()]
            if all(0 <= i <= 4 for i in indices) and len(set(indices)) == len(indices):
                player_discards = sorted(indices)
                break
            else:
                print("Invalid input. Please enter unique numbers between 0 and 4.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by spaces.")
    
    player.discard_and_draw(player_discards, deck)
    
    player_discard_count = len(player_discards)

    # Dealer AI decision
    dealer_discards, dealer_message, dealer_folded = dealer_ai.choose_discards(
        dealer.hand,
        player_discard_count
    )

    print(dealer_message)

    # Handle folding
    if dealer_folded:
        winnings = int(bet * 1.5)
        player.chips += winnings
        print(f"The dealer folds. You win {winnings} chips!")
        return

# Dealer performs discards
    dealer.discard_and_draw(dealer_discards, deck)

# -------------------------
# SECOND ROUND
# -------------------------

    print("\nSecond round:")

    for group in sort_and_group_cards(player.hand):
        print([str(card) for card in group])

    print("1. Check")
    print("2. Bet")
    print("3. Fold")

    choice = input("Choose an option: ").strip()

# Player folds
    if choice == "3":
        print("You fold. The dealer wins the pot.")
        return

# Player checks
    if choice == "1":
        dealer_action, dealer_message = dealer_ai.second_round_action(dealer.hand, player_bet=False)
        print(dealer_message)

        if dealer_action == "fold":
            winnings = int(bet * 1.5)
            player.chips += winnings
            print(f"The dealer folds. You win {winnings} chips!")
            return

    # Both checked → continue to showdown

# Player bets
    if choice == "2":
        dealer_action, dealer_message = dealer_ai.second_round_action(dealer.hand, player_bet=True)
        print(dealer_message)

        if dealer_action == "fold":
            winnings = int(bet * 1.5)
            player.chips += winnings
            print(f"The dealer folds. You win {winnings} chips!")
            return

    # Dealer calls → continue to showdown

    # Showdown
    print("\nFinal Player Hand:")
    for group in sort_and_group_cards(player.hand):
        print([str(card) for card in group])

    print("\nFinal Dealer Hand:")
    for group in sort_and_group_cards(dealer.hand):
        print([str(card) for card in group])

    # Evaluate
    p_rank, p_tb = player.evaluate()
    d_rank, d_tb = dealer.evaluate()

    print("\nPlayer:", format_hand(p_rank, p_tb))
    print("Dealer:", format_hand(d_rank, d_tb))

    # Determine winner
    if p_rank > d_rank:
        multiplier = get_payout_multiplier(p_rank)
        winnings = bet * multiplier
        player.chips += winnings
        print(f"\nYou win {winnings} chips! New balance: {player.chips}")

    elif d_rank > p_rank:
        print(f"\nDealer wins. You lost {bet} chips. New balance: {player.chips}")

    else:
    # Same rank → compare tiebreakers
        if p_tb > d_tb:
            multiplier = get_payout_multiplier(p_rank)
            winnings = bet * multiplier
            player.chips += winnings
            print(f"\nYou win {winnings} chips! New balance: {player.chips}")

        elif d_tb > p_tb:
            print(f"\nDealer wins. You lost {bet} chips. New balance: {player.chips}")

        else:
            # Tie → return bet
            player.chips += bet
            print(f"\nIt's a tie! Your bet is returned. New balance: {player.chips}")

player = Player([], "Player", chips=100)

while True:
    play_round()

    if player.chips <= 0:
        print("\nYou are out of chips. Game Over.")
        buy = input("Buy more chips? (y/n): ").lower()
        if buy == "y":
            player.chips = 100
            continue
        else:
            break

    again = input("\nPlay again? (y/n): ").lower()
    if again != "y":
        break

