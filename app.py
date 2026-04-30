from flask import Flask, render_template, request, redirect, session
from GameState import GameState, RANK_TEXT
from Deck import Card
from HandEvaluator import evaluate_hand

app = Flask(__name__)
app.secret_key = "your-secret-key"

def get_game():
    if "game" not in session:
        session["game"] = GameState().to_dict()
    return GameState.from_dict(session["game"])


def save_game(game):
    session["game"] = game.to_dict()

@app.route("/", methods=["GET"])
def index():
    game = get_game()
    return render_template("index.html", state=game)

@app.route("/start", methods=["POST"])
def start():
    game = GameState()
    game.start_round()
    save_game(game)
    return redirect("/play")

@app.route("/play", methods=["GET", "POST"])
def play():
    game = get_game()

    if request.method == "POST":
        action = request.form.get("action")

        # BETTING PHASE
        if game.phase == "betting":
            if action == "raise":
                game.player_raise()
            elif action == "check":
                game.player_check()
            elif action == "fold":
                game.player_fold()

            # Dealer auto-responds if needed
            game.update_after_betting()

        # DISCARD PHASE
        elif game.phase == "discard":
            if action == "discard":
                indexes = request.form.getlist("discard[]")
                indexes = [int(i) for i in indexes]
                game.player_discard(indexes)
            elif action == "skip":
                game.player_skip_discard()

            game.finish_discard_phase()

        save_game(game)

    return render_template("play.html", state=game)

@app.route("/restart", methods=["POST"])
def restart():
    game = get_game()
    game.start_round()
    save_game(game)
    return redirect("/play")
#----------------------------------------------------
#DEBUGGING#

@app.route("/debug", methods=["GET", "POST"])
def debug():
    game = get_game()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "set_hands":
            # Set custom hands
            player_cards = []
            dealer_cards = []

            # Parse player hand
            for i in range(5):
                rank = request.form.get(f"player_rank_{i}")
                suit = request.form.get(f"player_suit_{i}")
                if rank and suit:
                    player_cards.append(Card(rank, suit))

            # Parse dealer hand
            for i in range(5):
                rank = request.form.get(f"dealer_rank_{i}")
                suit = request.form.get(f"dealer_suit_{i}")
                if rank and suit:
                    dealer_cards.append(Card(rank, suit))

            if len(player_cards) == 5:
                game.player_hand = player_cards
                game.player_rank, game.player_tb = evaluate_hand(game.player_hand)
                game.player_rank_text = RANK_TEXT[game.player_rank]
                game.update_sorted_groups()

            if len(dealer_cards) == 5:
                game.dealer_hand = dealer_cards
                game.dealer_rank, game.dealer_tb = evaluate_hand(game.dealer_hand)
                game.dealer_rank_text = RANK_TEXT[game.dealer_rank]
                game.update_dealer_sorted_groups()

            save_game(game)

        elif action == "load_example":
            example = request.form.get("example")
            examples = get_hand_examples()
            if example in examples:
                player_cards, dealer_cards = examples[example]
                game.player_hand = player_cards
                game.dealer_hand = dealer_cards

                game.player_rank, game.player_tb = evaluate_hand(game.player_hand)
                game.player_rank_text = RANK_TEXT[game.player_rank]
                game.update_sorted_groups()

                game.dealer_rank, game.dealer_tb = evaluate_hand(game.dealer_hand)
                game.dealer_rank_text = RANK_TEXT[game.dealer_rank]
                game.update_dealer_sorted_groups()

                save_game(game)

    return render_template("debug.html", state=game)


def get_hand_examples():
    """Return example hands for testing different poker ranks."""
    return {
        "royal_flush": (
            [Card("10", "Hearts"), Card("Jack", "Hearts"), Card("Queen", "Hearts"), Card("King", "Hearts"), Card("Ace", "Hearts")],
            [Card("2", "Clubs"), Card("3", "Clubs"), Card("4", "Clubs"), Card("5", "Clubs"), Card("6", "Clubs")]
        ),
        "straight_flush": (
            [Card("9", "Spades"), Card("10", "Spades"), Card("Jack", "Spades"), Card("Queen", "Spades"), Card("King", "Spades")],
            [Card("2", "Diamonds"), Card("3", "Diamonds"), Card("4", "Diamonds"), Card("5", "Diamonds"), Card("6", "Diamonds")]
        ),
        "four_of_a_kind": (
            [Card("Ace", "Hearts"), Card("Ace", "Clubs"), Card("Ace", "Diamonds"), Card("Ace", "Spades"), Card("King", "Hearts")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("7", "Hearts")]
        ),
        "full_house": (
            [Card("Queen", "Hearts"), Card("Queen", "Clubs"), Card("Queen", "Diamonds"), Card("Jack", "Hearts"), Card("Jack", "Spades")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("6", "Hearts")]
        ),
        "flush": (
            [Card("2", "Hearts"), Card("5", "Hearts"), Card("7", "Hearts"), Card("9", "Hearts"), Card("King", "Hearts")],
            [Card("Ace", "Clubs"), Card("King", "Clubs"), Card("Queen", "Clubs"), Card("Jack", "Clubs"), Card("10", "Clubs")]
        ),
        "straight": (
            [Card("7", "Hearts"), Card("8", "Clubs"), Card("9", "Diamonds"), Card("10", "Spades"), Card("Jack", "Hearts")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("6", "Hearts")]
        ),
        "three_of_a_kind": (
            [Card("8", "Hearts"), Card("8", "Clubs"), Card("8", "Diamonds"), Card("Ace", "Spades"), Card("King", "Hearts")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("6", "Hearts")]
        ),
        "two_pair": (
            [Card("King", "Hearts"), Card("King", "Clubs"), Card("Queen", "Diamonds"), Card("Queen", "Spades"), Card("Jack", "Hearts")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("6", "Hearts")]
        ),
        "one_pair": (
            [Card("Ace", "Hearts"), Card("Ace", "Clubs"), Card("King", "Diamonds"), Card("Queen", "Spades"), Card("Jack", "Hearts")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("6", "Hearts")]
        ),
        "high_card": (
            [Card("Ace", "Hearts"), Card("King", "Clubs"), Card("Queen", "Diamonds"), Card("Jack", "Spades"), Card("9", "Hearts")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("6", "Hearts")]
        )
    }
#----------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
