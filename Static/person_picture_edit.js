var remove_pic_index = -1;

$(document).ready(function() {
  // add the proper thumbnail setter function for every pic
  $(".pic-btn.make-thumb").click(function() {
    image = $(this).siblings(".img-name-value").val();
    name = $("#person-name").text();
    pic_to_thumbnail(name, image, function() { $("#thumbnail-pic").attr("src", "/Images/" + image); });
  });

  // add remove functionality for every pic
  $(".pic-btn.remove-pic").click(function() {
    if (confirm("Are you sure? This action cannot be undone!")) {
      image = $(this).siblings(".img-name-value").val();
      name = $("#person-name").text();
      delete_image(name, image, function() { $(this).parent().parent().remove(); }.bind(this));
    }
  });

  $(".pic-btn.change-pers").click(function() {
    image = $(this).siblings(".img-name-value").val();
    name = $("#person-name").text();
    $("#current-owner").text(name);
    $("#moving-pic-name").text(image);
    $("#choose-new-owner").show();
  });

  // cancel change
  $(".cancel-person-change").click(function() {
    $("#choose-new-owner").hide();
    return false;
  });

  // submit change
  $("#change-person-btn").click(function() {
    old_name = $("#current-owner").text();
    image = $("#moving-pic-name").text();
    new_name = $("#possible-persons")
      .find(":selected")
      .text();
    change_pic_owner(old_name, new_name, image, function() { $(this).parent().parent().remove(); }.bind(this));
    $("#choose-new-owner").hide();
  });
});

function change_pic_owner(old_name, new_name, image, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/change_pic_owner",
    data: {
      oname: old_name,
      image: image,
      nname: new_name
    },
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(JSON.parse(error).message);
    }
  });
}

function pic_to_thumbnail(name, image, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/change_thumbnail_for_person",
    data: { name: name, image: image },
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(JSON.parse(error).message);
    }
  });
}

function delete_image(name, image, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/delete_image_of_person",
    data: {name: name, image: image },
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(JSON.parse(error).message);
    }
  });
}
