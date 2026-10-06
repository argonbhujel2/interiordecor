document.addEventListener('DOMContentLoaded', function() {
  // Sticky navbar
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 50);
    });
  }

  // Mobile menu
  const hamburger = document.querySelector('.hamburger');
  const navLinks = document.querySelector('.nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      hamburger.classList.toggle('active');
    });
  }

  // Flash auto-dismiss
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.style.opacity = '0', 4000);
    setTimeout(() => el.remove(), 4500);
  });

  // Calculator
  const calcForm = document.getElementById('calculator-form');
  if (calcForm) {
    calcForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const length = parseFloat(document.getElementById('room_length').value) || 0;
      const width = parseFloat(document.getElementById('room_width').value) || 0;
      const unit = document.getElementById('unit').value;
      const material = document.getElementById('material').value;
      const installation = document.getElementById('installation').value;

      const resultBox = document.getElementById('calc-result');
      resultBox.innerHTML = '<p>Calculating...</p>';

      try {
        const res = await fetch('/api/calculate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ length, width, unit, material, installation })
        });
        const data = await res.json();
        if (data.success) {
          resultBox.innerHTML = `
            <div class="calc-result">
              <p><strong>Estimated Area:</strong> ${data.area_display}</p>
              <p><strong>Material Cost:</strong> Rs. ${data.material_cost.toLocaleString()}</p>
              <p><strong>Installation Cost:</strong> Rs. ${data.installation_cost.toLocaleString()}</p>
              <p class="total">Estimated Total: Rs. ${data.total.toLocaleString()}</p>
              <p class="calc-note">${data.note}</p>
            </div>`;
        } else {
          resultBox.innerHTML = `<p style="color:red">${data.error || 'Error calculating'}</p>`;
        }
      } catch (err) {
        resultBox.innerHTML = '<p style="color:red">Network error. Please try again.</p>';
      }
    });
  }

  // Quote form area auto-calc
  const lenInput = document.getElementById('room_length');
  const widInput = document.getElementById('room_width');
  const areaInput = document.getElementById('estimated_area');
  if (lenInput && widInput && areaInput) {
    const updateArea = () => {
      const l = parseFloat(lenInput.value) || 0;
      const w = parseFloat(widInput.value) || 0;
      areaInput.value = (l * w).toFixed(2);
    };
    lenInput.addEventListener('input', updateArea);
    widInput.addEventListener('input', updateArea);
  }

  // Lazy load images
  if ('IntersectionObserver' in window) {
    const imgs = document.querySelectorAll('img[data-src]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.src = entry.target.dataset.src;
          entry.target.removeAttribute('data-src');
          observer.unobserve(entry.target);
        }
      });
    });
    imgs.forEach(img => observer.observe(img));
  }
});
