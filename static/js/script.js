document.addEventListener("DOMContentLoaded", function() {
  var elems = document.querySelectorAll(".sidenav");
  var options = {};
  var instances = M.Sidenav.init(elems, options);

  document
    .querySelector(".sidenav")
    .addEventListener("click", function() {
      var elem = document.querySelector(".sidenav");
      var instance = M.Sidenav.getInstance(elem);

      if (instance.isOpen) {
        instance.close();
      } else {
        instance.open();
      }
    });
});

document.addEventListener("DOMContentLoaded", function() {
  var elems = document.querySelectorAll(".sidenav");
  var options = {};
  var instances = M.Sidenav.init(elems, options);

  document
    .querySelector("main")
    .querySelector("#nav-closed")
    .addEventListener("click", function() {
      var elem = document.querySelector(".sidenav");
      var instance = M.Sidenav.getInstance(elem);

        instance.close();
  
    });
});

// $(document).ready(function(){
//     $('.sidenav')
//         .sidenav()
//         .on('click tap', 'li a', () => {
//             $('.sidenav').sidenav('close');
//         });
//     $('.sidenav')
//         .sidenav()
//         .on('click tap', '#notifications', () => {
//             $('.sidenav').sidenav('close');
//         });
// });

$(document).ready(function(){
    $('select').formSelect();
  });

$(document).ready(function(){

$("#browse-toggle").click(function(){
  $("#letters").toggleClass('hidden');
  $("#search-input").toggleClass('hidden');
});
});

  $(document).ready(function(){
    $('.modal').modal();
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


