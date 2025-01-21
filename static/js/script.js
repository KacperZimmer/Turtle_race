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

document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, adding drag and drop handlers');
    addDragAndDropHandlers();
});
