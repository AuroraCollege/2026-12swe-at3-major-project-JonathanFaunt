from Deck import Deck, Card
from DealerLogic import DealerAI
from HandEvaluator import (
    evaluate_hand,
    format_hand,
    get_payout_multiplier,
    sort_and_group_cards
)

# Rank text for UI
RANK_TEXT = {
    0: "",
    1: "Pair!",
    2: "Two Pair!",
    3: "Three of a Kind!",
    4: "Straight!",
    5: "Flush!",
    6: "Full House!",
    7: "Four of a Kind!",
    8: "Straight Flush!",
    9: "Royal Flush!",
    10: "Five of a Kind!"
}


class GameState:
    def __init__(self):
        self.player_hand = []
        self.dealer_hand = []

        # Always initialize rank so serialization never crashes
        self.player_rank = 0
        self.player_tb = []
        self.player_rank_text = ""

        self.dealer_rank = 0
        self.dealer_tb = []
        self.dealer_rank_text = ""

        self.deck = Deck()

        # PHASES: betting → discard → showdown
        self.phase = "betting"

        self.player_chips = 500
        self.pot = 0
        self.current_bet = 0

        self.dealer_message = ""
        self.dealer_folded = False

        self.dealer_ai = DealerAI()

        self.sorted_groups = []
        self.dealer_sorted_groups = []
        self.outcome_message = ""

        self.stats_recorded = False
        self.previous_chips = 500

    # ---------------------------------------------------------
    # Start a new round
    # ---------------------------------------------------------
    def start_round(self):
        self.deck = Deck()
        self.deck.shuffle()

        self.player_hand = self.deck.deal(5)
        self.dealer_hand = self.deck.deal(5)

        # Evaluate immediately
        self.player_rank, self.player_tb = evaluate_hand(self.player_hand)
        self.player_rank_text = RANK_TEXT[self.player_rank]

        # Assign original indexes for discard mapping
        for i, card in enumerate(self.player_hand):
            card.original_index = i

        self.phase = "betting"
        self.pot = 10
        self.current_bet = 10
        self.player_chips -= 10
        self.stats_recorded = False
        self.dealer_folded = False
        self.outcome_message = ""

        self.dealer_message = "Place your bet."
        self.update_sorted_groups()

    # ---------------------------------------------------------
    # BETTING PHASE
    # ---------------------------------------------------------
    def player_raise(self):
        if self.current_bet >= 100:
            return  # Cannot raise beyond 100
        self.current_bet += 10
        self.pot += 10
        self.player_chips -= 10
        if self.current_bet >= 100:
            self.dealer_message = "You raised 10. Bet is now at maximum."
        else:
            self.dealer_message = "You raised 10. Raise again or check."

    def player_check(self):
        self.dealer_message = "You checked."

    def player_fold(self):
        self.dealer_folded = True
        self.phase = "showdown"
        self.outcome_message = "You folded. Dealer wins."
        self.dealer_message = "The dealer takes the pot."

    def update_after_betting(self):
        if self.dealer_folded:
            return

        # Dealer chooses discards BEFORE player discards
        dealer_discards, msg, folded = self.dealer_ai.choose_discards(
            self.dealer_hand,
            player_discard_count=0
        )

        self.dealer_message = msg

        if folded:
            self.dealer_folded = True
            self.phase = "showdown"
            self.outcome_message = "Dealer folded. You win the pot!"
            self.player_chips += self.pot
            return

        # Store dealer discards for later
        self._dealer_discards = dealer_discards

        self.phase = "discard"

    # ---------------------------------------------------------
    # DISCARD PHASE
    # ---------------------------------------------------------
    def player_discard(self, indexes):
        # Build new hand
        new_hand = [card for i, card in enumerate(self.player_hand) if i not in indexes]
        needed = 5 - len(new_hand)
        new_hand.extend(self.deck.deal(needed))

        # Reassign original indexes
        for i, card in enumerate(new_hand):
            card.original_index = i

        self.player_hand = new_hand
        self.dealer_message = "You drew new cards."

        # Re-evaluate rank
        self.player_rank, self.player_tb = evaluate_hand(self.player_hand)
        self.player_rank_text = RANK_TEXT[self.player_rank]

        self.update_sorted_groups()

        # Dealer draws now
        if hasattr(self, "_dealer_discards"):
            d_new = []
            for i, card in enumerate(self.dealer_hand):
                if i not in self._dealer_discards:
                    d_new.append(card)
            needed = 5 - len(d_new)
            d_new.extend(self.deck.deal(needed))
            self.dealer_hand = d_new

    def player_skip_discard(self):
        self.dealer_message = "You kept your hand."

    def finish_discard_phase(self):
        self.phase = "showdown"
        self.evaluate_showdown()

    # ---------------------------------------------------------
    # SHOWDOWN
    # ---------------------------------------------------------
    def evaluate_showdown(self):
        if self.dealer_folded:
            return

        p_rank, p_tb = evaluate_hand(self.player_hand)
        d_rank, d_tb = evaluate_hand(self.dealer_hand)

        p_name = format_hand(p_rank, p_tb)
        d_name = format_hand(d_rank, d_tb)

        # Update UI rank
        self.player_rank, self.player_tb = p_rank, p_tb
        self.player_rank_text = RANK_TEXT[self.player_rank]

        self.dealer_rank, self.dealer_tb = d_rank, d_tb
        self.dealer_rank_text = RANK_TEXT[self.dealer_rank]

        self.update_sorted_groups()
        self.update_dealer_sorted_groups()

        if p_rank > d_rank:
            mult = get_payout_multiplier(p_rank)
            winnings = self.current_bet * mult
            self.player_chips += winnings
            self.outcome_message = (
                f"You win! {p_name}. Dealer had {d_name}. "
                f"You win {winnings} chips."
            )

        elif d_rank > p_rank:
            self.outcome_message = f"Dealer wins with {d_name}. You had {p_name}."

        else:
            # Compare tiebreakers
            if p_tb > d_tb:
                mult = get_payout_multiplier(p_rank)
                winnings = self.current_bet * mult
                self.player_chips += winnings
                self.outcome_message = (
                    f"You win! {p_name}. Dealer had {d_name}. "
                    f"You win {winnings} chips."
                )
            elif d_tb > p_tb:
                self.outcome_message = f"Dealer wins with {d_name}. You had {p_name}."
            else:
                # Tie
                self.player_chips += self.current_bet
                self.outcome_message = (
                    f"It's a tie! Both had {p_name}. Your bet is returned."
                )

    # ---------------------------------------------------------
    # UI grouping
    # ---------------------------------------------------------
    def update_sorted_groups(self):
        self.sorted_groups = sort_and_group_cards(self.player_hand)

    def update_dealer_sorted_groups(self):
        self.dealer_sorted_groups = sort_and_group_cards(self.dealer_hand)

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------
    def to_dict(self):
        return {
            "player_hand": [card.to_dict() for card in self.player_hand],
            "dealer_hand": [card.to_dict() for card in self.dealer_hand],
            "deck": self.deck.to_dict(),
            "phase": self.phase,
            "player_chips": self.player_chips,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "dealer_message": self.dealer_message,
            "dealer_folded": self.dealer_folded,
            "outcome_message": self.outcome_message,
            "player_rank": self.player_rank,
            "player_rank_text": self.player_rank_text,
            "dealer_rank": self.dealer_rank,
            "dealer_rank_text": self.dealer_rank_text,
            "stats_recorded": self.stats_recorded,
            "previous_chips": self.previous_chips,
        }

    @staticmethod
    def from_dict(data):
        gs = GameState()

        gs.player_hand = [Card.from_dict(c) for c in data["player_hand"]]
        gs.dealer_hand = [Card.from_dict(c) for c in data["dealer_hand"]]
        gs.deck = Deck.from_dict(data["deck"])

        gs.phase = data["phase"]
        gs.player_chips = data["player_chips"]
        gs.pot = data["pot"]
        gs.current_bet = data["current_bet"]
        gs.dealer_message = data["dealer_message"]
        gs.dealer_folded = data["dealer_folded"]
        gs.outcome_message = data.get("outcome_message", "")

        gs.player_rank = data.get("player_rank", 0)
        gs.player_rank_text = data.get("player_rank_text", RANK_TEXT.get(gs.player_rank, ""))

        gs.dealer_rank = data.get("dealer_rank", 0)
        gs.dealer_rank_text = data.get("dealer_rank_text", RANK_TEXT.get(gs.dealer_rank, ""))

        gs.stats_recorded = data.get("stats_recorded", False)
        gs.previous_chips = data.get("previous_chips", gs.player_chips)

        gs.update_sorted_groups()
        gs.update_dealer_sorted_groups()

        return gs

        # Reassign original indexes
        for i, card in enumerate(gs.player_hand):
            card.original_index = i

        gs.update_sorted_groups()
        return gs
