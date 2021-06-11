// Materialize modal initialisation

$(document).ready(function(){

    $("#delete-user-modal").on("show.bs.modal", function(event){
        var button = $(event.relatedTarget);
        var url = button.data("url");
        $(this).find('#confirm-delete').attr('href', url);
    });

    $('.modal').modal({
        // Rohan Kumar of Stack Overflow gave the code necessary to prevent the modal from appearing underneath other page elements
        startingTop: '30%',
        endingTop: '40%'
    });
  });

  // Materialize sidenav initialisation

document.addEventListener("DOMContentLoaded", function() {
  var elems = document.querySelectorAll(".sidenav");
  var instances = M.Sidenav.init(elems);

  document.querySelector(".sidenav-close").addEventListener("click", function() {
      var elem = document.querySelector(".sidenav");
      var instance = M.Sidenav.getInstance(elem);

        instance.close();
  
    });
});

// Materialize components initialisation

$(document).ready(function(){
    $('select').formSelect();
    $('.tooltipped').tooltip();
    $("#browse-toggle").click(function(){
        $("#letters").toggleClass('hidden');
        $("#search-input").toggleClass('hidden');
        $("#search-btn-desktop").toggleClass('hidden');
    });
});

// Function to read flash message value and display it in Materialise toast

function alert(){
    let toastAlert = document.getElementById('alert').getAttribute('value');
    M.toast({html: toastAlert});
}

let toastInfo = document.getElementById('message').getAttribute('value');
M.toast({html: toastInfo});


// Function to add fields for incorrect and alternative term usage

  function add_field(what, parent_id, add_class) {
    let field_name = what;
    let to_add = document.createElement('div');
    to_add.innerHTML = `<input name="${what}" class="${add_class}">`;
    let add_to = document.getElementById(parent_id);
    add_to.appendChild(to_add);
  }

