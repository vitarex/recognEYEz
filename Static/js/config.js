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

  $(".preferred-id-select").change(function(e) {
    if (e.target.value == -1)
      $("#url-" + e.target.options[e.target.options.length - 1].id).prop(
        "disabled",
        false
      );
    else
      $("#url-" + e.target.options[e.target.options.length - 1].id).prop(
        "disabled",
        true
      );
  });

  $(".delete-setting").click(function(e) {
    delete_setting(
      e.target.id.replace("delete-setting-", ""),
      function() {
        var fieldset = $(this).parent();
        var radio_input = $(fieldset).siblings(
          "#" + fieldset.id.replace("-fieldset", "")
        );
        fieldset.remove();
        radio_input.remove();
      }.bind(e.target)
    );
  });

  $("#submit-password-change").click(function(e) {
    var array = $(this)
      .parent()
      .serializeArray();
    var username = array[0].value;
    var old_password = array[1].value;
    var new_password1 = array[2].value;
    var new_password2 = array[3].value;

    if (new_password1 == new_password2) {
      if (new_password1.length > 5 && new_password1.length < 19) {
        change_psw(old_password, new_password1, username, function() {
          alert("Your password has been changed successfully!");
        });
      } else {
        alert("Your password must be between 6 and 18 characters.");
      }
    } else {
      alert("Passwords must match!");
    }
  });
});

function delete_setting(setting_name, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/delete_camera_config",
    data: { setting_name: setting_name },
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(JSON.parse(error).message);
    }
  });
}

function change_psw(old_password, new_password, username, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/change_password",
    data: {
      old_password: old_password,
      new_password: new_password,
      username: username
    },
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(error.responseText);
    }
  });
}
