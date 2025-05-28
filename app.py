from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from game_logic import BridgeGame
import csv
import os
import webbrowser
import threading

app = Flask(__name__)
app.secret_key = 'f3a9d1c44a8c4dfcbe7b2a983b6dfd23'

# Global Bridge game instance
game=None

# Open browser automatically
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# Homepage (index.html)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with open('users.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row and row[0] == username and row[1] == password:
                    session['user'] = username
                    return redirect(url_for('game_rules'))

        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/game_rules')
def game_rules():
    return render_template('game_rules.html')

@app.route('/play_with_friends')
def play_with_friends():
    return render_template('play_with_friends.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']

        with open('users.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([username, password, email, phone])

        return render_template('index.html')
    return render_template('signup.html')

@app.route('/create_match', methods=['GET', 'POST'])
def create_match():
    global game
    if 'user' not in session:
        return redirect(url_for('login'))

    players = [1,2,3,4]

    game = BridgeGame(players)
    game.shuffle_with_heap()
    game.distribute_cards()

        # Initialize bidding state
    session['bidding_status'] = []
    session['current_player'] = players[0]
    session['bidding_history'] = []
    session['passes_in_a_row'] = 0
    session['last_bid'] = None
    session['is_doubled'] = False

        # Store game state in session
    session['game_initialized'] = True
    session['players'] = players

    

    return redirect(url_for(('start_bidding'))) 

@app.route('/start_bidding')
def start_bidding():
    global game
    if not game:
        return redirect(url_for('home'))
    return render_template('bidding_interface.html', 
                         current_player=session.get('current_player'),
                         bidding_history=session.get('bidding_history', []))

@app.route('/api/make_bid', methods=['POST'])
def make_bid():
    global game
    if not game:
        return jsonify({'error': 'Game not initialized'}), 400

    data = request.get_json()
    try:
        # Get current player and validate turn
        current_player = session.get('current_player')
        if current_player != data['player']:
            return jsonify({'error': 'Not your turn'}), 400

        # Process the bid
        result = game.bidding_phase(
            player=data['player'],
            bid_type=data['type'],
            bid_number=data.get('number'),
            bid_suit=data.get('suit')
        )

        # Update session state
        session['current_player'] = result['next_player']
        session['bidding_history'] = result['history']
        session['passes_in_a_row'] = result.get('passes_in_a_row', 0)
        session['last_bid'] = result.get('last_bid')
        session['is_doubled'] = result.get('is_doubled', False)

        # Check if bidding is complete
        if session['passes_in_a_row'] >= 3:
                highest_bidder, highest_bid = game.rbt.get_highest_bid()
                return jsonify({
              'status': 'complete',
              'highest_bidder': highest_bidder,
              'highest_bid': highest_bid
       })


        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/get_bidding_state', methods=['GET'])
def get_bidding_state():
    global game
    if not game:
        return jsonify({'error': 'Game not initialized'}), 400

    try:
        return jsonify({
            'current_player': session.get('current_player'),
            'bidding_history': session.get('bidding_history', []),
            'passes_in_a_row': session.get('passes_in_a_row', 0),
            'last_bid': session.get('last_bid'), 
            'is_doubled': session.get('is_doubled', False)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/end_bidding')
def end_bidding():
    global game
    if not game:
        return redirect(url_for('home'))

    highest_bidder, highest_bid = game.rbt.get_highest_bid()
    game.trump_suit = highest_bid
    game.declarer = highest_bidder

    session['highest_bid'] = highest_bid
    session['declarer'] = highest_bidder

    return redirect(url_for('start_game'))

# Game Interface - renders game.html
@app.route('/start_game')
def start_game():
    global game
    if game is None:
        print("Game is None!")
        return redirect(url_for('home'))

    # Debug print game state
    print("Game state:")
    print("Players:", game.players)
    print("Declarer:", game.declarer)
    print("Trump suit:", game.trump_suit)
    
    # Initialize current player to the player to the left of declarer
    players = list(game.players.keys())
    declarer_idx = players.index(game.declarer)
    session['current_player'] = players[(declarer_idx + 1) % len(players)]

    # Format the hands for the frontend
    formatted_hands = {}
    suit_symbols = {'spades': '♠', 'hearts': '♥', 'diamonds': '♦', 'clubs': '♣'}
    
    for player in players:
        print(f"Player {player}'s cards:", game.players[player])
        formatted_hands[player] = [
            {
                'rank': card[1],  # rank is the second element
                'suit': suit_symbols[card[0]]  # convert suit name to symbol
            }
            for card in game.players[player]
        ]
        print(f"Formatted cards for {player}:", formatted_hands[player])

    print("Final formatted hands:", formatted_hands)
    print("Current player:", session.get('current_player'))

    return render_template('game.html',
                           highest_bidder=game.declarer,
                           highest_bid=game.trump_suit,
                           players=game.players,
                           initial_hands=formatted_hands)

@app.route('/api/get_game_state', methods=['GET'])
def get_game_state():
    global game
    if not game:
        return jsonify({'error': 'Game not initialized'}), 400
    
    try:
        # Format the hands for the frontend
        formatted_hands = {}
        suit_symbols = {'spades': '♠', 'hearts': '♥', 'diamonds': '♦', 'clubs': '♣'}
        
        for player in game.players:
            formatted_hands[player] = [
                {
                    'rank': card[1],  # rank is the second element
                    'suit': suit_symbols[card[0]]  # convert suit name to symbol
                }
                for card in game.players[player]
            ]

        # Format contract details
        bid_number = game.highest_bid[0] if isinstance(game.highest_bid, tuple) else game.highest_bid
        required_tricks = bid_number + 6

        return jsonify({
            'current_player': session.get('current_player'),
            'hands': formatted_hands,
            'trick_wins': game.trick_wins,
            'current_trick': game.current_trick,
            'contract_details': {
                'declarer': game.declarer,
                'bid': game.highest_bid,
                'required_tricks': required_tricks
            }
        })
    except Exception as e:
        print("Error in get_game_state:", str(e))  # Debug print
        return jsonify({'error': str(e)}), 400

@app.route("/api/game_play", methods=["POST"])
def game_play():
    data = request.get_json()
    if not game:
        return jsonify({"error": "Game not initialized"}), 400
    try:
        result = game.play_card(data["player"], data["card"])
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/play_round", methods=["POST"])
def play_round():
    global game
    if not game:
        return jsonify({"error": "Game not initialized"}), 400

    data = request.get_json()
    print("Received play request:", data)  # Debug print
    
    try:
        # Get current player and validate turn
        current_player = session.get('current_player')
        # Convert string player ID from frontend to integer
        player_id = int(data['player'])
        
        print(f"Current player from session: {current_player}, Received player: {player_id}")  # Debug print
        
        if current_player != player_id:
            print(f"Turn mismatch: expected {current_player}, got {player_id}")  # Debug print
            return jsonify({'error': 'Not your turn'}), 400

        # Format card data for game logic
        card_data = data['card']
        card = (card_data['suit'], card_data['rank'])
        print("Playing card:", card)  # Debug print

        # Play the card
        result = game.play_card(player_id, card)
        print("Play result from game:", result)  # Debug print
        
        # Update current player for next turn
        players = list(game.players.keys())
        current_idx = players.index(current_player)
        next_player = players[(current_idx + 1) % len(players)]
        session['current_player'] = next_player
        print(f"Updated next player in session to: {next_player}")  # Debug print

        # Merge the next_player into the result
        if isinstance(result, dict):
            result['next_player'] = next_player
        else:
            result = {'next_player': next_player}
        
        print("Final response with next player:", result)  # Debug print
        return jsonify(result)
    except ValueError as e:
        if "invalid literal for int()" in str(e):
            return jsonify({"error": "Invalid player ID format"}), 400
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print("Error in play_round:", str(e))  # Debug print
        return jsonify({"error": str(e)}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/leaderboard')
def leaderboard():
    global game
    if not game:
        return redirect(url_for('home'))

    # Calculate team tricks
    team1_tricks = (game.trick_wins.get(1, 0) + game.trick_wins.get(3, 0))
    team2_tricks = (game.trick_wins.get(2, 0) + game.trick_wins.get(4, 0))

    # Extract bid number from the highest bid tuple (number, suit)
    bid_number = game.highest_bid[0] if isinstance(game.highest_bid, tuple) else game.highest_bid
    required_tricks = bid_number + 6

    # Determine if contract was made
    declarer_team_tricks = team1_tricks if game.declarer in [1, 3] else team2_tricks
    contract_made = declarer_team_tricks >= required_tricks

    # Format the contract display
    def get_suit_name(suit):
        if isinstance(suit, str):
            return suit.upper()
        # If it's not a string, assume it's using the numeric system
        suit_names = {1: 'CLUBS', 2: 'DIAMONDS', 3: 'HEARTS', 4: 'SPADES', 5: 'NT'}
        return suit_names.get(suit, 'NT')

    contract_display = f"{bid_number} {get_suit_name(game.trump_suit)}"

    # Determine winning team
    team1_won = (game.declarer in [1, 3] and contract_made) or (game.declarer in [2, 4] and not contract_made)
    team2_won = not team1_won

    return render_template('leaderboard.html',
        declarer=game.declarer,
        contract=contract_display,
        required_tricks=required_tricks,
        contract_made=contract_made,
        team1_tricks=team1_tricks,
        team2_tricks=team2_tricks,
        team1_won=team1_won,
        team2_won=team2_won,
        player_tricks=game.trick_wins
    )

if __name__ == '__main__':
    threading.Timer(1.25, open_browser).start()
    app.run(debug=True)
