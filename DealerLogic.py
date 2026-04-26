import random
from HandEvaluator import convert_ranks_to_values, is_straight, is_flush

# ---------------------------------------------------------
# Personality Profile
# ---------------------------------------------------------

class DealerPersonality:
    def __init__(self, aggression=0.15, caution=0.15, randomness=0.10):
        self.aggression = aggression      # bluffing frequency
        self.caution = caution            # folding / nervous play
        self.randomness = randomness      # human-like mistakes


# ---------------------------------------------------------
# Dealer Thought Messages
# ---------------------------------------------------------

class DealerThoughts:

    @staticmethod
    def bluff():
        return random.choice([
            "The dealer looks confident.",
            "The dealer straightens up.",
            "The dealer acts unfazed."
        ])

    @staticmethod
    def cautious():
        return random.choice([
            "The dealer hesitates.",
            "The dealer seems unsure.",
            "The dealer pauses."
        ])

    @staticmethod
    def mistake():
        return random.choice([
            "The dealer frowns.",
            "The dealer mutters quietly.",
            "The dealer looks uncertain.",
            "The dealer sighs — maybe that wasn’t the right move."
        ])

    @staticmethod
    def strong():
        return random.choice([
            "The dealer stays calm.",
            "The dealer barely reacts.",
            "The dealer looks steady."
        ])

    @staticmethod
    def fold():
        return random.choice([
            "The dealer shakes his head.",
            "The dealer gives up the hand.",
            "The dealer folds quietly."
        ])


# ---------------------------------------------------------
# Dealer Logic
# ---------------------------------------------------------

class DealerAI:
    def __init__(self, personality=None):
        self.personality = personality or DealerPersonality()

    # Main entry point
    def choose_discards(self, hand, player_discard_count):
        values = [convert_ranks_to_values([card.rank])[0] for card in hand]
        suits = [card.suit for card in hand]
        counts = {v: values.count(v) for v in set(values)}

    # -------------------------------------------------
    # 1. Made hands (pair or better) → keep everything
    # -------------------------------------------------
        if any(c >= 2 for c in counts.values()):
            message = DealerThoughts.strong()
            return [], message, False

    # -------------------------------------------------
    # 2. Detect draws
    # -------------------------------------------------

    # 4 to a flush
        flush_suit = None
        for s in set(suits):
            if suits.count(s) == 4:
                flush_suit = s
                break

    # 4 to a straight
        straight, straight_tb = is_straight(values)
        has_straight_draw = False
        if not straight:
            sorted_vals = sorted(values)
            for i in range(2, 15):
                run = list(range(i, i + 4))
                if sum(v in run for v in sorted_vals) == 4:
                    has_straight_draw = True
                    break

    # -------------------------------------------------
    # 3. Rare folding logic (pre-draw, based on player discards)
    # -------------------------------------------------
        weak_hand = (
            not flush_suit and
            not has_straight_draw and
            max(values) <= 10
        )

        if weak_hand and player_discard_count <= 2:
            if random.random() < self.personality.caution:
                message = DealerThoughts.fold()
                return [], message, True

    # -------------------------------------------------
    # 4. Bluffing (aggression)
    # -------------------------------------------------
        if random.random() < self.personality.aggression:
            high_cards = {11, 12, 13, 14}
            keep = [i for i, v in enumerate(values) if v in high_cards]

            if keep:
                discards = [i for i in range(5) if i not in keep]
                message = DealerThoughts.bluff()
                return discards[:random.randint(0, 2)], message, False

    # -------------------------------------------------
    # 5. Mistakes (randomness)
    # -------------------------------------------------
        if random.random() < self.personality.randomness:
            k = random.randint(1, 3)
            discards = random.sample(range(5), k)
            message = DealerThoughts.mistake()
            return discards, message, False

    # -------------------------------------------------
    # 6. Strong draws
    # -------------------------------------------------

    # Flush draw
        if flush_suit:
            discards = [i for i, card in enumerate(hand) if card.suit != flush_suit]
            message = (
                DealerThoughts.cautious()
                if random.random() < self.personality.caution
                else DealerThoughts.strong()
            )
            return discards[:1], message, False

    # Straight draw
        if has_straight_draw:
            sorted_vals = sorted(values)
            for i in range(2, 15):
                run = list(range(i, i + 4))
                if sum(v in run for v in sorted_vals) == 4:
                    discards = [idx for idx, v in enumerate(values) if v not in run]
                    message = DealerThoughts.strong()
                    return discards[:1], message, False

    # -------------------------------------------------
    # 7. High card strategy
    # -------------------------------------------------
        high_cards = {11, 12, 13, 14}
        keep = [i for i, v in enumerate(values) if v in high_cards]

        if len(keep) >= 2:
            discards = [i for i in range(5) if i not in keep]
            message = DealerThoughts.cautious()
            return discards[:3], message, False

    # -------------------------------------------------
    # 8. Default: discard 3 lowest cards
    # -------------------------------------------------
        sorted_indices = sorted(range(5), key=lambda i: values[i])
        discards = sorted_indices[:3]
        message = DealerThoughts.cautious()
        return discards, message, False

    def second_round_action(self, hand, player_bet=False):
        values = [convert_ranks_to_values([card.rank])[0] for card in hand]
        counts = {v: values.count(v) for v in set(values)}

    # Made hand (pair or better)
        has_pair = any(c >= 2 for c in counts.values())

    # High cards
        high_cards = sum(1 for v in values if v >= 11)

    # -------------------------------------------------
    # Folding logic (rare)
    # -------------------------------------------------
        weak_hand = (not has_pair and high_cards <= 1 and max(values) <= 10)

        if weak_hand:
            fold_chance = self.personality.caution + (0.15 if player_bet else 0)

            if random.random() < fold_chance:
                return "fold", DealerThoughts.fold()

    # -------------------------------------------------
    # If player checks
    # -------------------------------------------------
        if not player_bet:
            if random.random() < self.personality.aggression:
                return "check", DealerThoughts.bluff()
            return "check", DealerThoughts.cautious()

    # -------------------------------------------------
    # If player bets
    # -------------------------------------------------

    # Strong enough to call
        if has_pair or high_cards >= 2:
            return "call", DealerThoughts.strong()

    # Bluff call
        if random.random() < self.personality.aggression:
            return "call", DealerThoughts.bluff()

    # Otherwise fold
        return "fold", DealerThoughts.fold()

