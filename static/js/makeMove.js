const socket = io();

socket.on('update_game_state', (new_game_state) => {
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
    });
}

function addDragAndDropHandlers() {
    const turtles = document.querySelectorAll('.turtle');
    const cells = document.querySelectorAll('.cell');

    turtles.forEach((turtle, index) => {
        turtle.addEventListener('dragstart', () => {
            turtle.classList.add('dragged');
            turtle.dataset.index = index;
        });

        turtle.addEventListener('dragend', () => {
            turtle.classList.remove('dragged');
        });
    });

    cells.forEach(cell => {
        cell.addEventListener('dragover', e => {
            e.preventDefault();
            const draggedTurtle = document.querySelector('.dragged');
            if (!draggedTurtle) return;

            const parentCell = draggedTurtle.closest('.cell');
            const turtlesInCell = Array.from(parentCell.children);
            const draggedIndex = turtlesInCell.indexOf(draggedTurtle);

            if (draggedIndex !== -1) {
                const turtlesBelow = turtlesInCell.slice(draggedIndex);
                turtlesBelow.forEach(turtle => {
                    cell.appendChild(turtle);
                    makeMove(turtle.textContent, Array.from(cell.parentNode.children).indexOf(cell));
                });
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', addDragAndDropHandlers);
