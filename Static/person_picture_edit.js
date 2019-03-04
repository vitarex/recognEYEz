
var remove_pic_index = -1;

$(function () { // add the proper thumbnail setter function for every pic
    $('.inner-face .make-thumb').each(function (index) {
        $(this).bind('click', function () {
            pic = $('#img-name-' + (index )).text();
            name = $('#person-name').text();
            pic_to_thumbnail(name, pic);
            return true;
        });
    });
});


/* #region delete pic*/
$(function () { // add remove functionality for every pic
    $('.remove-pic').each(function (index) {
        $(this).bind('click', function () {
            $("#confirmation").show();
            remove_pic_index = index;
            pic = $('#img-name-' + (index )).text();
            name = $('#person-name').text();
            $("#removing-pic-name").text(pic);
            return true;
        });
    });
});

    $(function () { // cancel delete
        $('.cancel-pic-delete').each(function (index) {
            $(this).bind('click', function () {
                $("#confirmation").hide();
                return true;
            });
        });
    });

    $(function () { // submit delete
        $('#remove-pic-btn').each(function (index) {
            $(this).bind('click', function () {

                name = $("#owner-name").val();
                pic = $("#removing-pic-name").text();
                if (delete_pic(name, pic)) {

                $("#outer-face-"+(remove_pic_index)).hide();
                $("#outer-face-"+(remove_pic_index)).attr("display", "none");
//                $(this).hide();
//                $(this).attr("display", "none");
                $("#confirmation").hide();
                return true;
                }
                else {
                alert("Error during communication with the server")
                }
            });
        });
    });
/* #endregion */ 


/* #region Change owner*/
$(function () { // show confirmation dialog
    $('.inner-face .change-pers').each(function (index) {
        $(this).bind('click', function () {
            pic = $('#img-name-' + (index )).text();
            name = $('#person-name').text();
            $("#current-owner").text(name);
            $("#moving-pic-name").text(pic);
            $("#choose-new-owner").show();
            return false;
        });
    });
});

    $(function () { // cancel change
        $('.cancel-person-change').each(function (index) {
            $(this).bind('click', function () {
                $("#choose-new-owner").hide();
                return false;
            });
        });
    });

    $(function () { // submit change
        $('#change-person-btn').each(function (index) {
            $(this).bind('click', function () {
                old_name = $("#current-owner").text();
                pic = $("#moving-pic-name").text();
                new_name = $('#possible-persons').find(":selected").text();
                change_pic_owner(old_name, new_name, pic);
                $("#choose-new-owner").hide();
                return false;
            });
        });
    });

/* #endregion */




function change_pic_owner(old_name, new_name, pic) {
    $.getJSON($SCRIPT_ROOT + "/change_pic_owner", {
        oname: old_name,
        pic: pic,
        nname: new_name
    });
    return true
}


function pic_to_thumbnail(name, pic) {
    $.ajax({
        url: $SCRIPT_ROOT + "/change_thumbnail_for_person",
        data : { n: name, p : pic},
        type: 'POST',
        success: function(response) {
            new_src="/dnn_data/"+name+"/"+pic;
            $("#thumbnail-pic").attr("src",new_src);
        },
        error: function(error) {
            alert("Error during thumbnail change.");
        }
    });
}



function delete_pic(name, pic) {
        $.ajax({
        url: $SCRIPT_ROOT + "/delete_pic_of_person",
        data : { n: name, p : pic},
        type: 'POST',
        success: function(response) {
            return true;
        },
        error: function(error) {
            return false;
        }
    });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}