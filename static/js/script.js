

$(document).ready(function(){
    $("#delete-user-modal").on("show.bs.modal", function(event){
        // Get the button that triggered the modal
        var button = $(event.relatedTarget);

        // Extract value from the custom data-* attribute
        var url = button.data("url");
        $(this).find('#confirm-delete').attr('href', url)
    });
});


document.addEventListener("DOMContentLoaded", function() {
  var elems = document.querySelectorAll(".sidenav");
  var options = {};
  var instances = M.Sidenav.init(elems, options);

  document
    .querySelector(".sidenav-close")
   
    .addEventListener("click", function() {
      var elem = document.querySelector(".sidenav");
      var instance = M.Sidenav.getInstance(elem);

        instance.close();
  
    });
});


$(document).ready(function(){
    $('select').formSelect();
  });

$(document).ready(function(){
    $('.tooltipped').tooltip();
  });
$(document).ready(function(){

$("#browse-toggle").click(function(){
  $("#letters").toggleClass('hidden');
  $("#search-input").toggleClass('hidden');
  $("#search-btn-desktop").toggleClass('hidden');
});
});

  $(document).ready(function(){
    $('.modal').modal({
        // Rohan Kumar of Stack Overflow gave the code necessary to prevent the modal from appearing underneath other page elements
        startingTop: '30%',
        endingTop: '40%'
    });
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

function alert(){
    let toastAlert = document.getElementById('alert').getAttribute('value')
    M.toast({html: toastAlert})
}

let toastInfo = document.getElementById('message').getAttribute('value')
M.toast({html: toastInfo})