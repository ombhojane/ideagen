document.addEventListener('DOMContentLoaded', () => {
    const searchButtons = document.querySelectorAll('.search-btn');
    const projectCards = document.querySelectorAll('.project-card');

    searchButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const category = this.getAttribute('data-category');

            // Remove active class from all buttons and apply to the clicked button
            searchButtons.forEach(button => button.classList.remove('active'));
            this.classList.add('active');

            // Filter project cards based on the category
            if (category === 'All') {
                projectCards.forEach(card => card.style.display = 'block');
            } else {
                projectCards.forEach(card => {
                    if (card.getAttribute('data-category') === category) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
        });
    });
});
