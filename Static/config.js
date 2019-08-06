$(document).ready(function() {
  $(".setting-select").click(function(e) {
    $(".setting-fieldset")
      .hide()
      .prop("disabled", true);
    $("#" + e.target.id + "-fieldset")
      .show()
      .prop("disabled", false);
  });

  $(".has-surrogate").click(function(e) {
    $("#" + e.target.id + "-surrogate").prop("checked", !e.target.checked);
  });

  $("#submit-password-change").click(function(e) {
    var array = $(this).parent().serializeArray()
    var username = array[0].value
    var old_password = array[1].value
    var new_password1 = array[2].value
    var new_password2 = array[3].value

    if(new_password1 == new_password2)
    {
        if((new_password1.length>5) && (new_password1.length<19))
        {
            change_psw(old_password, new_password1, username, function() { alert("Your password has been changed successfully!");})
        }
        else{alert("Your password must be between 6 and 18 characters.");}
    }
    else{alert("Passwords must match!");}
  });
});

function change_psw(old_password, new_password, username, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/change_password",
    data: {old_password: old_password, new_password: new_password, username: username},
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(error.responseText);
    }
  });
}
