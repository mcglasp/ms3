  $(document).ready(function(){
    $('.sidenav').sidenav();
  });

$(document).ready(function(){
    $('select').formSelect();
  });

 

  function add_field(what, parent_id) {
    field_name = what
    to_add = document.createElement('div')
    to_add.innerHTML = `<input name="${what}">`
    add_to = document.getElementById(parent_id)
    add_to.appendChild(to_add)
  }