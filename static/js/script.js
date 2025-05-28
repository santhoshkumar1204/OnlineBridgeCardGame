const suits = ['♠', '♥', '♦', '♣'];
const suitColors = { '♠': 'black', '♣': 'black', '♥': 'red', '♦': 'red' };
const ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

// Map between numeric IDs and positions
const playerPositions = {
  '1': 'south',  // Player 1 at bottom
  '2': 'east',   // Player 2 on right
  '3': 'north',  // Player 3 at top
  '4': 'west'    // Player 4 on left
};

const positionToId = {
  'south': '1',  // Bottom is Player 1
  'east': '2',   // Right is Player 2
  'north': '3',  // Top is Player 3
  'west': '4'    // Left is Player 4
};

let currentTurn = '1'; // Default to Player 1 (bottom)
let hands = {};
let totalTricks = 0;
let contractDetails = {
  declarer: null,
  bid: null,
  requiredTricks: null
};

// Initialize global game state
window.gameState = window.gameState || {};
window.gameState.trickWins = window.gameState.trickWins || {};

function getPlayerPosition(playerId) {
  return playerPositions[playerId] || 'south';  // Default to bottom position (Player 1)
}

function getPlayerId(position) {
  return positionToId[position] || '1';  // Default to Player 1
}

function getPlayerLabel(playerId) {
  return `Player ${playerId}`;
}

function initializeGame() {
  console.log("Initializing game...");
  console.log("Window gameState:", window.gameState);

  try {
    // Use the initial game state from the template
    if (window.gameState && window.gameState.initialHands) {
      currentTurn = window.gameState.currentPlayer || '1';
      hands = window.gameState.initialHands;
      
      // Initialize contract details
      contractDetails.declarer = window.gameState.highestBidder;
      const bidNumber = parseInt(window.gameState.highestBid);
      contractDetails.bid = bidNumber;
      contractDetails.requiredTricks = bidNumber + 6; // Contract level + 6 for required tricks
      
      // Initialize trickWins
      window.gameState.trickWins = window.gameState.trickWins || {};
      
      console.log("Using template game state:", { currentTurn, hands, contractDetails });
      showCards(currentTurn);
      updateGameInfo();
      return;
    } else {
      console.error("No initial hands in game state!");
    }
  } catch (error) {
    console.error("Error using game state:", error);
  }

  // Fallback to fetching from server if gameState not available
  fetch("/api/get_game_state")
    .then(res => res.json())
    .then(data => {
      console.log("Server game state:", data);
      if (data.error) {
        console.error(data.error);
        return;
      }
      
      currentTurn = data.current_player || '1';  // Default to player 1 if not specified
      hands = data.hands;
      
      // Initialize contract details from server
      if (data.contract_details) {
        contractDetails.declarer = data.contract_details.declarer;
        contractDetails.bid = data.contract_details.bid;
        contractDetails.requiredTricks = data.contract_details.required_tricks;
      }
      
      // Initialize trickWins
      window.gameState.trickWins = data.trick_wins || {};
      
      console.log("Using server game state:", { currentTurn, hands, contractDetails });
      showCards(currentTurn);
      updateGameInfo();
    })
    .catch(err => console.error("Error initializing game:", err));
}

function createCard(card, isPlayable, isFaceUp = true) {
  console.log("Creating card:", isFaceUp ? card : "face-down");
  const cardDiv = document.createElement('div');
  cardDiv.className = `card ${isPlayable ? 'playable' : ''} ${!isFaceUp ? 'face-down' : ''}`;
  
  if (isFaceUp) {
    const color = suitColors[card.suit];
    cardDiv.style.color = color;

    // Create rank element
    const rankDiv = document.createElement('div');
    rankDiv.className = 'rank';
    rankDiv.textContent = card.rank;
    cardDiv.appendChild(rankDiv);

    // Create suit element
    const suitDiv = document.createElement('div');
    suitDiv.className = 'suit';
    suitDiv.textContent = card.suit;
    cardDiv.appendChild(suitDiv);
    
    if (isPlayable) {
      cardDiv.addEventListener('click', () => playCard(card, currentTurn));
    }
  }
  
  return cardDiv;
}

function createFaceDownCard() {
  return createCard(null, false, false);
}

function moveCardToTable(card, player) {
  const playZone = document.getElementById("play-zone");
  // Cards played to the table are always face up
  const tableCard = createCard(card, false, true);
  tableCard.style.position = "relative";
  tableCard.style.margin = "5px";
  playZone.appendChild(tableCard);
}

function showCards(playerTurn) {
  console.log("Showing cards for turn:", playerTurn);
  console.log("Current hands:", hands);
  
  // Update current turn
  currentTurn = String(playerTurn);
  console.log("Updated currentTurn to:", currentTurn);
  
  Object.entries(playerPositions).forEach(([id, position]) => {
    const handDiv = document.getElementById(`${position}-hand`);
    if (!handDiv) {
      console.error(`Hand div not found for position: ${position}`);
      return;
    }
    
    handDiv.innerHTML = '';
    if (hands[id] && Array.isArray(hands[id])) {
      console.log(`Displaying ${hands[id].length} cards for Player ${id}`);
      const isCurrentPlayer = String(id) === currentTurn;
      console.log(`Is current player (${id} === ${currentTurn}):`, isCurrentPlayer);
      
      if (isCurrentPlayer) {
        // Show face-up cards for current player
        hands[id].forEach(card => {
          const cardElement = createCard(card, true, true);
          handDiv.appendChild(cardElement);
        });
      } else {
        // Show face-down cards for other players
        for (let i = 0; i < hands[id].length; i++) {
          const cardElement = createFaceDownCard();
          handDiv.appendChild(cardElement);
        }
      }
    } else {
      console.log(`No cards or invalid cards for Player ${id}:`, hands[id]);
    }
  });
  
  const turnIndicator = document.getElementById('turn-indicator');
  if (turnIndicator) {
    turnIndicator.textContent = `Player ${currentTurn}`;
    console.log("Updated turn indicator to:", `Player ${currentTurn}`);
  }
}

function playCard(card, playerId) {
  console.log("Playing card:", card, "for player:", playerId);
  
  // Ensure trickWins is initialized
  window.gameState.trickWins = window.gameState.trickWins || {};
  
  // Validate it's the player's turn
  if (String(playerId) !== currentTurn) {
    console.error("Not your turn! Current turn:", currentTurn, "Your ID:", playerId);
    alert("Not your turn! It's currently Player " + currentTurn + "'s turn.");
    return;
  }
  
  // Convert suit symbol back to suit name for the server
  const suitNames = {
    '♠': 'spades',
    '♥': 'hearts',
    '♦': 'diamonds',
    '♣': 'clubs'
  };

  const serverCard = {
    rank: card.rank,
    suit: suitNames[card.suit] || card.suit
  };

  // Convert playerId to number for server
  const numericPlayerId = parseInt(playerId, 10);

  console.log("Sending to server:", {
    player: numericPlayerId,
    card: serverCard
  });

  // Send play to server
  fetch("/api/play_round", {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ 
      player: numericPlayerId, 
      card: serverCard
    })
  })
  .then(res => {
    if (!res.ok) {
      return res.text().then(text => {
        console.error("Server error response:", text);
        throw new Error(`Server returned ${res.status}: ${text}`);
      });
    }
    return res.json();
  })
  .then(data => {
    console.log("Server response:", data);
    if (data.error) {
      alert(data.error);
      return;
    }

    // Remove card from hand visually
    const position = getPlayerPosition(playerId);
    const handDiv = document.getElementById(`${position}-hand`);
    const cardElements = handDiv.getElementsByClassName('card');
    for (let element of cardElements) {
      const rankElement = element.querySelector('.rank');
      const suitElement = element.querySelector('.suit');
      if (rankElement.textContent === card.rank && suitElement.textContent === card.suit) {
        element.remove();
        break;
      }
    }

    // Move card to table
    moveCardToTable(card, playerId);

    // Handle trick completion
    if (data.trick_complete) {
      if (data.trick_winner) {
        totalTricks++;
        window.gameState.trickWins = window.gameState.trickWins || {};
        window.gameState.trickWins[data.trick_winner] = (window.gameState.trickWins[data.trick_winner] || 0) + 1;
        
        // Update team tricks
        const team1Tricks = (window.gameState.trickWins[1] || 0) + (window.gameState.trickWins[3] || 0);
        const team2Tricks = (window.gameState.trickWins[2] || 0) + (window.gameState.trickWins[4] || 0);
        
        // Update declarer's team tricks
        const declarerNumber = parseInt(contractDetails.declarer);
        const partnerNumber = declarerNumber <= 2 ? declarerNumber + 2 : declarerNumber - 2;
        const declarerTeamTricks = (window.gameState.trickWins[declarerNumber] || 0) + 
                                 (window.gameState.trickWins[partnerNumber] || 0);
        
        // Update the UI
        document.querySelector('.game-info').innerHTML = `
          <div>Declarer: Player ${contractDetails.declarer}</div>
          <div>Contract: ${contractDetails.bid}</div>
          <div>Required tricks: ${contractDetails.requiredTricks}</div>
          <div>Tricks won by declarer's team: ${declarerTeamTricks}/${contractDetails.requiredTricks}</div>
          <div id="team-tricks">
            <div>Team 1 (Players 1-3): ${team1Tricks}</div>
            <div>Team 2 (Players 2-4): ${team2Tricks}</div>
          </div>
          <div id="player-tricks">
            <div>Player 1: ${window.gameState.trickWins[1] || 0}</div>
            <div>Player 2: ${window.gameState.trickWins[2] || 0}</div>
            <div>Player 3: ${window.gameState.trickWins[3] || 0}</div>
            <div>Player 4: ${window.gameState.trickWins[4] || 0}</div>
          </div>
          <div>Total tricks played: ${totalTricks}/13</div>
        `;
        
        alert(`Trick won by Player ${data.trick_winner}`);
        
        setTimeout(() => {
          document.getElementById("play-zone").innerHTML = "";
          checkGameEnd();
        }, 1000);
      }
    }

    // Update turn
    if (data.next_player) {
      console.log("Updating turn to:", data.next_player);
      // Update current turn immediately
      currentTurn = String(data.next_player);
      console.log("Updated currentTurn to:", currentTurn);
      
      // Refresh game state to ensure all players see the current state
      fetch("/api/get_game_state")
        .then(res => res.json())
        .then(gameState => {
          if (gameState.error) {
            console.error(gameState.error);
            return;
          }
          console.log("Received updated game state:", gameState);
          hands = gameState.hands;
          showCards(currentTurn);
        })
        .catch(err => console.error("Error refreshing game state:", err));
    } else {
      console.warn("No next_player in response:", data);
    }
  })
  .catch(err => {
    console.error("Error playing card:", err);
    alert("Error playing card: " + err.message);
  });
}

function updateGameInfo() {
  // Ensure trickWins is initialized
  window.gameState.trickWins = window.gameState.trickWins || {};
  
  // Calculate team tricks
  const team1Tricks = (window.gameState.trickWins[1] || 0) + (window.gameState.trickWins[3] || 0);
  const team2Tricks = (window.gameState.trickWins[2] || 0) + (window.gameState.trickWins[4] || 0);
  
  // Calculate declarer's team tricks
  const declarerNumber = parseInt(contractDetails.declarer);
  const partnerNumber = declarerNumber <= 2 ? declarerNumber + 2 : declarerNumber - 2;
  const declarerTeamTricks = (window.gameState.trickWins[declarerNumber] || 0) + 
                           (window.gameState.trickWins[partnerNumber] || 0);
  
  // Update the UI
  const gameInfo = document.querySelector('.game-info');
  if (gameInfo) {
    gameInfo.innerHTML = `
      <div>Declarer: Player ${contractDetails.declarer || 'Not set'}</div>
      <div>Contract: ${contractDetails.bid || 'Not set'}</div>
      <div>Required tricks: ${contractDetails.requiredTricks || 'Not set'}</div>
      <div>Tricks won by declarer's team: ${declarerTeamTricks}/${contractDetails.requiredTricks || 'Not set'}</div>
      <div id="team-tricks">
        <div>Team 1 (Players 1-3): ${team1Tricks}</div>
        <div>Team 2 (Players 2-4): ${team2Tricks}</div>
      </div>
      <div id="player-tricks">
        <div>Player 1: ${window.gameState.trickWins[1] || 0}</div>
        <div>Player 2: ${window.gameState.trickWins[2] || 0}</div>
        <div>Player 3: ${window.gameState.trickWins[3] || 0}</div>
        <div>Player 4: ${window.gameState.trickWins[4] || 0}</div>
      </div>
      <div>Total tricks played: ${totalTricks}/13</div>
    `;
  }
}

function getTricksWonByDeclarer() {
  const declarerNumber = parseInt(contractDetails.declarer);
  const partnerNumber = declarerNumber <= 2 ? declarerNumber + 2 : declarerNumber - 2;
  
  const declarerTeamTricks = (window.gameState.trickWins?.[declarerNumber] || 0) + 
                            (window.gameState.trickWins?.[partnerNumber] || 0);
  return declarerTeamTricks;
}

function checkGameEnd() {
  if (totalTricks === 13) {
    const tricksWon = getTricksWonByDeclarer();
    const required = contractDetails.requiredTricks;
    const team1Total = (window.gameState.trickWins?.[1] || 0) + (window.gameState.trickWins?.[3] || 0);
    const team2Total = (window.gameState.trickWins?.[2] || 0) + (window.gameState.trickWins?.[4] || 0);
    
    const result = tricksWon >= required ? 
      `Contract made! Declarer's team won ${tricksWon} tricks (needed ${required}).\n\n` :
      `Contract failed! Declarer's team won ${tricksWon} tricks (needed ${required}).\n\n`;
    
    const finalScore = `Final Score:\nTeam 1 (Players 1-3): ${team1Total} tricks\nTeam 2 (Players 2-4): ${team2Total} tricks`;
    
    setTimeout(() => {
      alert(result + finalScore);
      // Redirect to leaderboard
      window.location.href = '/leaderboard';
    }, 1000);
  }
}

// Initial setup
document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM loaded, initializing game...");
  initializeGame();
});


