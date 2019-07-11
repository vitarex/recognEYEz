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
});
