$(function() {
  $(".unknown-person-wrapper .add-merge-btn").click(function() {
    name = $(this)
      .children("span")
      .text();
    add_or_merge_dialog(name);
    return false;
  });
  $(".dialog-overlay").click(function(e) {
    if ($(e.target).hasClass("dialog-overlay")) {
      $("#merge-options").remove();
      $(this).hide();
    }
  });
  $("#cancel-add-small").click(function(e) {
    $("#merge-options").remove();
    $(".dialog-overlay").hide();
  });
});

$(function close_overlay(e) {});

$(function() {
  // cancel change
  $("#add-or-merge-dialog .cancel-add-or-merge").each(function(index) {
    $(this).bind("click", function() {
      $("#add-or-merge-dialog").hide();
      return false;
    });
  });
});

$(function() {
  // merge
  $("#add-or-merge-dialog #merge-btn").each(function(index) {
    $(this).bind("click", function() {
      name = $("#selected-add-or-merge-name").text();
      merge_to = $("#merge-options").val();
      send_to_merge(name, merge_to);
      setTimeout(() => {
        document.location.reload()
      }, 1000);
      return false;
    });
  });
});

$(function() {
  // add as new
  $("#add-or-merge-dialog #add-btn").each(function(index) {
    $(this).bind("click", function() {
      name = $("#selected-add-or-merge-name").text();
      new_from_unk(name);
      setTimeout(() => {
        document.location.reload()
      }, 1000);
      return false;
    });
  });
});

function add_or_merge_dialog(name) {
  $("#selected-add-or-merge-name").text(name);

  if ($("#merge-options-copy").length > 0) {
    let new_select = $("#merge-options-copy")
      .clone()
      .attr("id", "merge-options")
      .removeClass("d-none")[0];
  
    let ind = Array.prototype.findIndex.call(
      new_select.options,
      option => option.value == name
    );
  
    if (ind > -1) new_select.options[ind].remove();
    $(new_select).insertAfter("#merge-options-copy");
  }


  $("#add-or-merge-dialog").show();
  $("#add-or-merge-dialog").css("display", "flex");
}

function send_to_merge(name, merge_to) {
  $.getJSON($SCRIPT_ROOT + "/_merge_with", {
    n: name,
    m2: merge_to
  });
  return true;
}

function new_from_unk(name) {
  $.getJSON($SCRIPT_ROOT + "/_new_person_from_unk", {
    n: name
  });
  return true;
}
