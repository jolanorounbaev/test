// profile.js
let currentSlide = 0;
const carousel = document.getElementById('carousel');
const items = carousel ? document.querySelectorAll('.carousel-item') : [];
const totalSlides = items.length;

function updateCarousel() {
  if (carousel && totalSlides > 0) {
    const offset = -currentSlide * 100;
    carousel.style.transform = `translateX(${offset}%)`;
  }
}

function changeSlide(direction) {
  if (totalSlides > 0) {
    currentSlide = (currentSlide + direction + totalSlides) % totalSlides;
    updateCarousel();
  }
}

// Only run carousel code if carousel exists
if (carousel && totalSlides > 0) {
  updateCarousel();
}
