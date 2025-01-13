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
            });
        }
    });
});
