import random
import heapq

class Node:
    def __init__(self, player, bid):
        self.player = player
        self.bid = bid
        self.left = None
        self.right = None
        self.color = 1  # Red = 1, Black = 0

class RedBlackTree:
    def __init__(self):
        self.NULL = Node(None, 0)
        self.NULL.color = 0
        self.NULL.left = None
        self.NULL.right = None
        self.root = self.NULL

    def insert(self, player, bid):
        node = Node(player, bid)
        node.parent = None
        node.left = self.NULL
        node.right = self.NULL
        node.color = 1

        parent = None
        current = self.root

        while current != self.NULL:
            parent = current
            if node.bid < current.bid:
                current = current.left
            else:
                current = current.right

        node.parent = parent
        if parent is None:
            self.root = node
        elif node.bid < parent.bid:
            parent.left = node
        else:
            parent.right = node

        if node.parent is None:
            node.color = 0
            return

        if node.parent.parent is None:
            return

        self.fix_insert(node)

    def fix_insert(self, node):
        while node.parent and node.parent.color == 1:
            if node.parent == node.parent.parent.right:
                uncle = node.parent.parent.left
                if uncle and uncle.color == 1:
                    uncle.color = 0
                    node.parent.color = 0
                    node.parent.parent.color = 1
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self.right_rotate(node)
                    node.parent.color = 0
                    node.parent.parent.color = 1
                    self.left_rotate(node.parent.parent)
            else:
                uncle = node.parent.parent.right
                if uncle and uncle.color == 1:
                    uncle.color = 0
                    node.parent.color = 0
                    node.parent.parent.color = 1
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self.left_rotate(node)
                    node.parent.color = 0
                    node.parent.parent.color = 1
                    self.right_rotate(node.parent.parent)
            if node == self.root:
                break
        self.root.color = 0

    def left_rotate(self, node):
        right = node.right
        node.right = right.left
        if right.left != self.NULL:
            right.left.parent = node
        right.parent = node.parent
        if node.parent is None:
            self.root = right
        elif node == node.parent.left:
            node.parent.left = right
        else:
            node.parent.right = right
        right.left = node
        node.parent = right

    def right_rotate(self, node):
        left = node.left
        node.left = left.right
        if left.right != self.NULL:
            left.right.parent = node
        left.parent = node.parent
        if node.parent is None:
            self.root = left
        elif node == node.parent.right:
            node.parent.right = left
        else:
            node.parent.left = left
        left.right = node
        node.parent = left

    def get_highest_bid(self):
        current = self.root
        while current.right != self.NULL:
            current = current.right
        return current.player, current.bid

class BridgeGame:
    def __init__(self, players):
        self.suits = ["spades", "hearts", "diamonds", "clubs"]
        self.ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.deck = []
        self.players = {name: [] for name in players}
        self.rbt = RedBlackTree()
        self.current_trick = {}
        self.trick_history = []
        self.trick_wins = {p: 0 for p in self.players}
        self.trump_suit = None
        self.declarer = None
        self.highest_bid = None
        self.round_wins = {name: 0 for name in players}
        self.passes_in_a_row = 0
        self.last_bid = None
        self.bidding_history = []

    def shuffle_with_heap(self):
        heap = []
        for suit in self.suits:
            for rank in self.ranks:
                card = (suit, rank)
                priority = random.randint(1, 10000)
                heapq.heappush(heap, (priority, card))

        while heap:
            _, card = heapq.heappop(heap)
            self.deck.append(card)

    def distribute_cards(self):
        for _ in range(13):
            for player in self.players:
                self.players[player].append(self.deck.pop())

    def validate_bid(self, bid_input):
        try:
            bid_number, bid_suit = bid_input.split()
            bid_number = int(bid_number)
            # Allow "nt" as a suit for No Trump
            if bid_suit == "nt":
                return 1 <= bid_number <= 7
            return 1 <= bid_number <= 7 and (bid_suit in self.suits)
        except ValueError:
            return False

    def bidding_phase(self, player, bid_type, bid_number=None, bid_suit=None):
        if bid_type == 'pass':
            self.passes_in_a_row += 1
            self.bidding_history.append({'player': player, 'bid': 'PASS'})
            if self.passes_in_a_row >= 3 and self.last_bid:
                self.declarer, bid_val = self.rbt.get_highest_bid()
                self.trump_suit = self.last_bid[1] if self.last_bid[1] != 'nt' else None
                self.highest_bid = self.last_bid
                return {
                    'status': 'complete',
                    'next_player': None,
                    'history': self.bidding_history,
                    'error': None
                }
        elif bid_type == 'double':
            if not self.last_bid:
                return {'status': 'continue', 'next_player': player, 'history': self.bidding_history, 'error': 'Cannot double without a previous bid'}
            self.bidding_history.append({'player': player, 'bid': 'DOUBLE'})
            self.passes_in_a_row = 0
        elif bid_type == 'normal':
            if not bid_number or not bid_suit:
                return {'status': 'continue', 'next_player': player, 'history': self.bidding_history, 'error': 'Missing bid number or suit'}
            bid_value = (bid_number, bid_suit)
            if bid_suit == "nt":
                bid_value = (bid_number, "nt")
            if self.last_bid and bid_value <= self.last_bid:
                return {'status': 'continue', 'next_player': player, 'history': self.bidding_history, 'error': 'Bid must be higher than last bid'}
            self.last_bid = bid_value
            self.rbt.insert(player, bid_number)
            self.bidding_history.append({'player': player, 'bid': f"{bid_number} {bid_suit.upper()}"})
            self.passes_in_a_row = 0

        player_list = list(self.players.keys())
        idx = player_list.index(player)
        next_idx = (idx + 1) % len(player_list)
        next_player = player_list[next_idx]

        return {
            'status': 'continue',
            'next_player': next_player,
            'history': self.bidding_history,
            'error': None
        }

    def play_card(self, player_name, card):
        if player_name not in self.players:
            raise ValueError("Invalid player")
            
        # Validate turn order
        if len(self.current_trick) > 0:
            last_player = list(self.current_trick.keys())[-1]
            player_list = list(self.players.keys())
            expected_player = player_list[(player_list.index(last_player) + 1) % len(player_list)]
            if player_name != expected_player:
                raise ValueError("Not your turn")
        
        if card not in self.players[player_name]:
            raise ValueError("Card not in player's hand")
        
        # Validate following suit only if not the first card of the trick
        if len(self.current_trick) > 0:
            lead_suit = self.current_trick[list(self.current_trick.keys())[0]][0]
            player_cards = self.players[player_name]
            has_suit = any(c[0] == lead_suit for c in player_cards)
            if has_suit and card[0] != lead_suit:
                raise ValueError("Must follow suit when possible")
        
        # Add card to trick
        self.current_trick[player_name] = card
        self.players[player_name].remove(card)

        # Calculate next player
        player_list = list(self.players.keys())
        current_idx = player_list.index(player_name)
        next_player = player_list[(current_idx + 1) % len(player_list)]

        # If trick is complete, evaluate winner
        if len(self.current_trick) == 4:
            winner = self.evaluate_trick()
            self.trick_wins[winner] += 1
            self.trick_history.append(self.current_trick.copy())
            self.current_trick.clear()
            return {
                "trick_winner": winner,
                "trick_complete": True,
                "next_player": winner  # Next trick starts with the winner
            }
        
        # Return current trick state
        return {
            "trick_progress": self.current_trick,
            "trick_complete": False,
            "next_player": next_player
        }
    
    def evaluate_trick(self):
        lead_card = self.current_trick[list(self.current_trick.keys())[0]]
        lead_suit = lead_card[0]
        
        def card_value(card):
            suit, rank = card
            rank_values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                          "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
            return rank_values[rank]
        
        winning_card = lead_card
        winning_player = list(self.current_trick.keys())[0]
        
        for player, card in self.current_trick.items():
            if card[0] == self.trump_suit and winning_card[0] != self.trump_suit:
                winning_card = card
                winning_player = player
            elif card[0] == winning_card[0] and card_value(card) > card_value(winning_card):
                winning_card = card
                winning_player = player
        
        return winning_player

    def play_rounds(self):
        print("\nGame Start!")
        for round_num in range(13):
            print(f"\nRound {round_num + 1}")
            played_cards = {}
            for player in self.players:
                print(f"\n{player}'s cards: {self.players[player]}")
                while True:
                    try:
                        choice = int(input(f"{player}, choose card to play (1-{len(self.players[player])}): ")) - 1
                        if 0 <= choice < len(self.players[player]):
                            card = self.players[player].pop(choice)
                            played_cards[player] = card
                            print(f"{player} played {card}")
                            break
                        else:
                            print("Invalid card number.")  
                    except ValueError:
                        print("Enter a valid number.")
            winner = max(played_cards, key=lambda p: played_cards[p])
            self.round_wins[winner] += 1
            print(f"\nRound {round_num + 1} Winner: {winner}")

        self.get_final_result()

    def get_final_result(self):
        required_tricks = self.highest_bid[0] + 6  # bid number + 6
        tricks_won = self.trick_wins[self.declarer]

        if tricks_won >= required_tricks:
            return f"{self.declarer}'s team made the contract! ({tricks_won} tricks won)"
        else:
            return f"{self.declarer}'s team failed the contract. ({tricks_won} tricks won)"
