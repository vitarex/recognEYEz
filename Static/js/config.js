var toOpen = null;

$(document).ready(function() {
  make_only_card();

  $('#email-switch-on').click(function() {
    $('#email-fieldset').prop('disabled', false);
    $('#email-fieldset').removeClass('disabled');
  });
  $('#email-switch-off').click(function() {
    $('#email-fieldset').prop('disabled', true);
    $('#email-fieldset').addClass('disabled');
  });
  
  $('#mqtt-switch-on').click(function() {
    $('#mqtt-fieldset').prop('disabled', false);
    $('#mqtt-fieldset').removeClass('disabled');
  });
  $('#mqtt-switch-off').click(function() {
    $('#mqtt-fieldset').prop('disabled', true);
    $('#mqtt-fieldset').addClass('disabled');
  });

  $('.setting-collapse').on('hidden.bs.collapse', function () {
    toOpen.collapse('show');
  });
  $('.setting-collapse').on('hide.bs.collapse', function () {
    $(this).children(".card-body").children("fieldset").prop("disabled", true);
  });
  $('.setting-collapse').on('show.bs.collapse', function () {
    $(this).siblings('.card-header')[0].scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
    $(this).children(".card-body").children("fieldset").prop("disabled", false);
  });

  $(".accordion-heading").click(function() {
    let og = $(this).siblings(".setting-collapse")[0];
    toOpen = $(og);
    $(".setting-collapse").each(function() {
      if (og != this) $(this).collapse('hide');
    });
  });

  $(".preferred-id-select").change(function(e) {
    let target = $("#url-" + e.target.options[e.target.options.length - 1].id)
    if (e.target.value == -1) {
      target.prop("disabled", false);
      target.parent().parent().removeClass("disabled");
    }
    else {
      target.prop("disabled", true);
      target.parent().parent().addClass("disabled");
    }
  });

  $(".delete-setting").click(function(e) {
    delete_setting(
      e.target.id.replace("delete-setting-", ""),
      function() {
        let parent_card = $(this)
                        .parent()
                        .parent()
                        .parent(".card-body")
                        .parent(".setting-collapse")
                        .parent(".card");
        parent_card.fadeTo(200, 0.01, function(){ 
          $(this).slideUp(150, function() {
              $(this).remove(); 
              $(".setting-collapse").first().collapse('show');
              make_only_card();
          });
        });
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

function make_only_card() {
  if ($(".setting-collapse").length == 1)
    $(".setting-collapse").first().addClass('only-card');
}

function delete_setting(setting_name, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/delete_camera_config",
    data: { setting_name: setting_name },
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(error.responseJSON.message);
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
