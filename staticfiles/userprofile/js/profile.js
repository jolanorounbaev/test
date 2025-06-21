    // profile.js
let currentSlide = 0;
const carousel = document.getElementById('carousel');
const items = document.querySelectorAll('.carousel-item');
const totalSlides = items.length;

function updateCarousel() {
  const offset = -currentSlide * 100;
  carousel.style.transform = `translateX(${offset}%)`;
}

function changeSlide(direction) {
  currentSlide = (currentSlide + direction + totalSlides) % totalSlides;
  updateCarousel();
}

updateCarousel();

window.addEventListener('DOMContentLoaded', function () {
  fetch('/static/maps/europe.svg')
    .then(response => response.text())
    .then(svgText => {
      const container = document.getElementById('svgMapContainer');
      container.innerHTML = svgText;

      const svg = container.querySelector('svg');
      if (svg) {
        console.log("SVG loaded!");
        const belgium = svg.querySelector('#belgium');
        if (belgium) {
          belgium.style.fill = 'red';
        }
      }
    })
    .catch(err => console.error('Failed to load SVG:', err));
});
