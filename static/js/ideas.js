document.addEventListener('DOMContentLoaded', function() {
  const searchButtons = document.querySelectorAll('.search-btn');
  const ideaCards = document.querySelectorAll('.idea-card');

  searchButtons.forEach(button => {
    button.addEventListener('click', function() {
      const category = this.dataset.category;
      
      searchButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');

      ideaCards.forEach(card => {
        if (category === 'All' || card.dataset.category === category) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
});