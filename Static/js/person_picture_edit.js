var remove_pic_index = -1;

$(document).ready(function() {
  // add the proper thumbnail setter function for every pic
  $(".pic-btn.make-thumb").click(function() {
    image = $(this)
      .parents(".inner-face")
      .children(".img-name-value")
      .first()
      .val();
    name = $("#person-name").text();
    pic_to_thumbnail(name, image, function() {
      $("#thumbnail-pic").attr("src", "/Images/" + image);
    });
  });

  // add remove functionality for every pic
  $(".pic-btn.remove-pic").click(function() {
    if (confirm("Are you sure? This action cannot be undone!")) {
      image = $(this)
        .parents(".inner-face")
        .children(".img-name-value")
        .first()
        .val();
      name = $("#person-name").text();
      delete_image(name, image, function() {
        remove_pic_from_dom(this);
      }.bind(this));
    }
  });

  $(".pic-btn.change-pers").click(function() {
    image = $(this)
      .parents(".inner-face")
      .children(".img-name-value")
      .first()
      .val();
    name = $("#person-name").text();
    $("#current-owner").text(name);
    $("#moving-pic-name").text(image);

    $("#choose-new-owner").show();
    $("#choose-new-owner").css("display", "flex");
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
    index = Array.prototype.findIndex
              .call(
                $(".img-name-value"),
                img_name => img_name.value == image
              );
    change_pic_owner(
      old_name,
      new_name,
      image,
      function() {
        remove_pic_from_dom(
          $(".inner-face")[index]
        );
      }
    );
    $("#choose-new-owner").hide();
  });

  $(".outer-face").click(function(e) {
    gif = $(this)
      .children(".inner-face")
      .children(".grow-inner-face")[0];
    if (getComputedStyle(gif, null).getPropertyValue("display") != "none")
      $(gif).toggleClass("grow");
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

function remove_pic_from_dom(t) {
  let outer = $(t).parents(".outer-face");

  let image = outer.children("img").first();
  image.css("height", image.height() + "px");

  outer.addClass("collapse-me");
  setTimeout(() => {
    outer.remove();
  }, 420);
}

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
      alert(error.responseJSON.message);
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
      alert(error.responseJSON.message);
    }
  });
}

function delete_image(name, image, success_func) {
  $.ajax({
    url: $SCRIPT_ROOT + "/delete_image_of_person",
    data: { name: name, image: image },
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(error.responseJSON.message);
    }
  });
}
