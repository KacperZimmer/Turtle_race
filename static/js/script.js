const socket = io();

socket.on('connect', () => {
    console.log('Connected to Socket.IO server');
});

socket.on('update_game_state', (new_game_state) => {
    console.log('Received new game state:', new_game_state);
    updateGameState(new_game_state);
});

function updateGameState(new_game_state) {
    const board = document.querySelector('.board');
    board.innerHTML = '';

    new_game_state.cells.forEach(cell => {
        const cellElement = document.createElement('div');
        cellElement.classList.add('cell');

        cell.forEach(turtle => {
            const turtleElement = document.createElement('p');
            turtleElement.classList.add('turtle');
            turtleElement.setAttribute('draggable', 'true');
            turtleElement.style.backgroundColor = turtle_colors[turtle];
            turtleElement.textContent = turtle;

            cellElement.appendChild(turtleElement);
        });

        board.appendChild(cellElement);
    });

    console.log('Game state updated in the DOM');
    addDragAndDropHandlers();
}

function makeMove(turtle, newPosition) {
    const data = {
        turtle_color: turtle,
        new_position: newPosition
    };

    fetch('/make_move', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(() => {
        console.log(`Move made for turtle: ${turtle} to position: ${newPosition}`);
    });
}

function addDragAndDropHandlers() {
    const turtles = document.querySelectorAll('.turtle');
    const cells = document.querySelectorAll('.cell');

    turtles.forEach((turtle, index) => {
        turtle.addEventListener('dragstart', (e) => {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', null); // Required for Firefox
            turtle.classList.add('dragged');
            turtle.dataset.index = index;
        });

        turtle.addEventListener('dragend', () => {
            turtle.classList.remove('dragged');
        });
    });

    cells.forEach((cell, cellIndex) => {
        cell.addEventListener('dragover', e => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });

        cell.addEventListener('drop', e => {
            e.preventDefault();
            const draggedTurtle = document.querySelector('.dragged');
            if (!draggedTurtle) return;

            const parentCell = draggedTurtle.closest('.cell');
            const turtlesInCell = Array.from(parentCell.children);
            const draggedIndex = turtlesInCell.indexOf(draggedTurtle);

            const parentCellIndex = Array.from(parentCell.parentNode.children).indexOf(parentCell);

            if (parentCellIndex === 0) {
                cell.appendChild(draggedTurtle);
                makeMove(draggedTurtle.textContent, Array.from(cell.parentNode.children).indexOf(cell));
            } else if (parentCellIndex > 0 && draggedIndex !== -1) {
                const turtlesBelow = turtlesInCell.slice(draggedIndex);
                turtlesBelow.forEach(turtle => {
                    cell.appendChild(turtle);
                    makeMove(turtle.textContent, Array.from(cell.parentNode.children).indexOf(cell));
                });
            }
        });
    });
}
function setupCardListeners() {
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', handleCardClick);
    });
}

function handleCardClick(event) {
    const cardElement = event.currentTarget;
    const cardText = cardElement.textContent.trim();
    const player_id = parseInt(document.getElementById('player-id').value);

    playCard(cardText, player_id, cardElement);
}

function playCard(card, player_id, cardElement) {
    fetch('/play_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            card: card,
            player_id: player_id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Replace old card with new card
            const newCard = createCardElement(data.new_card);
            cardElement.parentNode.replaceChild(newCard, cardElement);
        }
    });
}

function createCardElement(cardText) {
    const cardDiv = document.createElement('div');
    cardDiv.className = `card ${getCardClass(cardText)}`;
    cardDiv.textContent = cardText;
    cardDiv.addEventListener('click', handleCardClick);
    return cardDiv;
}

function getCardClass(cardText) {
    if (cardText.includes('Joker')) return 'joker';
    if (cardText.includes('Yellow')) return 'yellow';
    if (cardText.includes('Green')) return 'green';
    if (cardText.includes('Red')) return 'red';
    if (cardText.includes('Blue')) return 'blue';
    if (cardText.includes('Purple')) return 'purple';
    return '';
}
socket.on('card_played', (data) => {
    const logMessage = `Gracz ${data.player_id} zagrał kartę: ${data.card} i otrzymał nową kartę: ${data.new_card}`;
    console.log(logMessage)
    addLog(logMessage);
});

function addLog(message) {
    const logContainer = document.getElementById('log-container');
    if (!logContainer) {
        console.error('Log container not found!');
        return;
    }

    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.textContent = message;
    logContainer.appendChild(logEntry);

    // Przewiń do najnowszego loga
    logContainer.scrollTop = logContainer.scrollHeight;
}
document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, adding drag and drop handlers');
    addDragAndDropHandlers();
    setupCardListeners()
});