
  // scroll reveal content
  function revealOnScroll() {
    const elements = document.querySelectorAll('[data-animate]');
    const windowHeight = window.innerHeight;

    elements.forEach(el => {
      const elementTop = el.getBoundingClientRect().top;

      if (elementTop < windowHeight - 100) {
        el.classList.add('visible');
      } else {
        el.classList.remove('visible'); 
      }
    });
  }

  window.addEventListener('scroll', revealOnScroll);
  window.addEventListener('load', revealOnScroll);


// prediction box
function closeModal() {
  document.getElementById("predictionModal").style.display = "none";
}

window.onload = function () {
  var modal = document.getElementById("predictionModal");
  if (modal && modal.style.display === "block") {
    setTimeout(() => {
      modal.style.display = "none";
    }, 5000); 
  }
};

window.onclick = function(event) {
  var modal = document.getElementById("predictionModal");
  if (event.target == modal) {
    modal.style.display = "none";
  }
}


//clear form
function clearForm() {
  const form = document.getElementById("predictionForm");
  form.reset();


  const selects = form.querySelectorAll("select");
  selects.forEach(select => select.selectedIndex = 0);

  const inputs = form.querySelectorAll("input");
  inputs.forEach(input => {
    if (input.type === "number") input.value = "";
  });

  document.getElementById("predict").scrollIntoView({ behavior: "smooth" });
}










