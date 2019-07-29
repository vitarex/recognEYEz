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
    if (e.target.value == -1) $("#url-" + e.target.options[e.target.options.length-1].id).prop("disabled", false);
    else $("#url-" + e.target.options[e.target.options.length-1].id).prop("disabled", true);
  });

  $(".delete-setting").click(function(e) {
    delete_setting(
      e.target.id.replace("delete-setting-", ""),
      function() {
        var fieldset = $(this).parent()
        var radio_input = $(fieldset).siblings("#" + fieldset.id.replace("-fieldset", ""))
        fieldset.remove()
        radio_input.remove()
      }.bind(e.target));
  });
});

function delete_setting(setting_name, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/delete_camera_config",
    data: { setting_name: setting_name},
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(JSON.parse(error).message);
    }
  });
}
