  $(document).ready(function(){
    $('.sidenav').sidenav();
  });

$(document).ready(function(){
    $('select').formSelect();
  });

  $(document).ready(function(){
  // Add smooth scrolling to all links
  $("#notification").on('click', function(event) {
    
    // Make sure this.hash has a value before overriding default behavior
    if (this.hash !== "") {
      // Prevent default anchor click behavior
      event.preventDefault();

      // Store hash
      var hash = this.hash;

      // Using jQuery's animate() method to add smooth page scroll
      // The optional number (800) specifies the number of milliseconds it takes to scroll to the specified area
      $('html, body').animate({
        scrollTop: $(hash).offset().top
      }, 800, function(){

        // Add hash (#) to URL when done scrolling (default click behavior)
        window.location.hash = hash;
      });
    } // End if
  });
});

 

  function add_field(what, parent_id, add_class) {
    field_name = what
    to_add = document.createElement('div')
    to_add.innerHTML = `<input name="${what}" class="${add_class}">`
    add_to = document.getElementById(parent_id)
    add_to.appendChild(to_add)
  }