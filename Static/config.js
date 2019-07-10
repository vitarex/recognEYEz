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
});
