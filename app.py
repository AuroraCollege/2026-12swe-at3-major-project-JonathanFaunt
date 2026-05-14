import sqlite3

from flask import Flask, render_template, request, redirect, session, g
from GameState import GameState, RANK_TEXT
from Deck import Card
from HandEvaluator import evaluate_hand
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your-secret-key"
DATABASE = "database.db"



def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        init_db()
    return g.db


def init_db():
    db = g.db
    db.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, passhash TEXT NOT NULL, chips INTEGER NOT NULL DEFAULT 500, wins INTEGER NOT NULL DEFAULT 0, losses INTEGER NOT NULL DEFAULT 0)"
    )
    columns = [row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()]
    if "chips" not in columns:
        db.execute("ALTER TABLE users ADD COLUMN chips INTEGER NOT NULL DEFAULT 500")
    if "wins" not in columns:
        db.execute("ALTER TABLE users ADD COLUMN wins INTEGER NOT NULL DEFAULT 0")
    if "losses" not in columns:
        db.execute("ALTER TABLE users ADD COLUMN losses INTEGER NOT NULL DEFAULT 0")
    db.commit()


def get_user(user_id):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def record_user_stats(game, user_id):
    user = get_user(user_id)
    if user is None:
        return

    previous_chips = getattr(game, "previous_chips", user["chips"])
    net = game.player_chips - previous_chips
    wins = user["wins"] or 0
    losses = user["losses"] or 0

    if net > 0:
        wins += 1
    elif net < 0:
        losses += 1

    db = get_db()
    db.execute(
        "UPDATE users SET chips = ?, wins = ?, losses = ? WHERE id = ?",
        (game.player_chips, wins, losses, user_id)
    )
    db.commit()

    game.previous_chips = game.player_chips
    game.stats_recorded = True


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_game():
    if "game" not in session:
        game = GameState()
        if session.get("user_id"):
            user = get_user(session["user_id"])
            if user:
                game.player_chips = user["chips"]
                game.previous_chips = user["chips"]
        session["game"] = game.to_dict()
    return GameState.from_dict(session["game"])


def save_game(game):
    session["game"] = game.to_dict()

@app.route("/", methods=["GET"])
def index():
    session.pop("game", None)  # Reset the game
    game = get_game()
    return render_template("index.html", state=game)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        # Check if username exists
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing:
            return render_template("register.html", error="Username already taken")

        # Create user
        passhash = generate_password_hash(password)

        db.execute(
            "INSERT INTO users (username, passhash, chips, wins, losses) VALUES (?, ?, ?, ?, ?)",
            (username, passhash, 500, 0, 0)
        )
        db.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["passhash"], password):
            return render_template("login.html", error="Invalid username or password")

        # Store user in session and reset game state from persistent stats
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session.pop("game", None)

        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/start", methods=["POST"])
def start():
    game = get_game()
    if session.get("user_id"):
        user = get_user(session["user_id"])
        if user:
            game.player_chips = user["chips"]
            game.previous_chips = user["chips"]
    game.start_round()
    save_game(game)
    return redirect("/play")

@app.route("/play", methods=["GET", "POST"])
def play():
    game = get_game()

    if request.method == "POST":
        action = request.form.get("player_action")

        # BETTING PHASE
        if game.phase == "betting":
            if action == "raise":
                game.player_raise()
            elif action == "check":
                game.player_check()
                # Dealer responds once the player decides to stop raising
                game.update_after_betting()
            elif action == "fold":
                game.player_fold()
            print("DEBUG original indexes:", [c.original_index for c in game.player_hand])

        # DISCARD PHASE
        elif game.phase == "discard":
            if action == "discard":
                indexes = request.form.getlist("discard[]")
                indexes = [int(i) for i in indexes if i and i.isdigit()]
                game.player_discard(indexes)
            elif action == "skip":
                game.player_skip_discard()

            game.finish_discard_phase()

        if session.get("user_id") and game.phase == "showdown" and not getattr(game, "stats_recorded", False):
            record_user_stats(game, session["user_id"])

        save_game(game)

    return render_template("play.html", state=game)

@app.route("/restart", methods=["POST"])
def restart():
    game = get_game()
    game.start_round()
    save_game(game)
    return redirect("/play")

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    db = get_db()
    sort = request.args.get("sort", "chips")

    if sort == "chips":
        order = "chips DESC, wins DESC, losses ASC"
    elif sort == "wins":
        order = "wins DESC, chips DESC, losses ASC"
    elif sort == "losses":
        order = "losses ASC, chips DESC, wins DESC"
    elif sort == "winrate":
        order = "(CASE WHEN (wins + losses) = 0 THEN 0.0 ELSE CAST(wins AS FLOAT) / (wins + losses) END) DESC, wins DESC, chips DESC"
    else:
        order = "chips DESC, wins DESC, losses ASC"

    query = f"SELECT username, chips, wins, losses FROM users ORDER BY {order}"
    rows = db.execute(query).fetchall()

    return render_template("leaderboard.html", rows=rows, sort=sort, state=get_game())

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
                
                for i, card in enumerate(game.player_hand):
                    card.original_index = i

                for i, card in enumerate(game.dealer_hand):
                    card.original_index = i

                save_game(game)

    return render_template("debug.html", state=game)


def get_hand_examples():
    # Return example hands for testing different poker ranks.
    return {
        "five_of_a_kind": (
            [Card("Ace", "Hearts"), Card("Ace", "Clubs"), Card("Ace", "Diamonds"), Card("Ace", "Spades"), Card("Ace", "Hearts")],
            [Card("2", "Hearts"), Card("3", "Hearts"), Card("4", "Hearts"), Card("5", "Hearts"), Card("6", "Hearts")]
        ),
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
