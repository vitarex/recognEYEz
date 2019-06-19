
$(function () {
    $('#unknown_persons .my-add-button').each(function (index) {
        // alert("for one" + index);
        $(this).bind('click', function () {
            name = $(".add-arg", this).text();
            folder = $(".add-folder-arg", this).text();
            add_or_merge_dialog(name, folder);
            return false;
        });
    });
});



    $(function () { // cancel change
        $('#add-or-merge-dialog .cancel-add-or-merge').each(function (index) {
            $(this).bind('click', function () {
                $("#add-or-merge-dialog").hide();
                return false;
            });
        });
    });

    $(function () { // merge
        $('#add-or-merge-dialog #merge-btn').each(function (index) {
            $(this).bind('click', function () {
                name = $("#selected-add-or-merge-name").text();
                folder = $("#selected-add-or-merge-folder").text();
                merge_to = $("#merge-options").val();
                send_to_merge(name, folder, merge_to);
                $("#add-or-merge-dialog").hide();
                return false;
            });
        });
    });

    $(function () { // add as new
        $('#add-or-merge-dialog #add-btn').each(function (index) {
            $(this).bind('click', function () {
                name = $("#selected-add-or-merge-name").text();
                folder = $("#selected-add-or-merge-folder").text();
                new_from_unk(name, folder);
                $("#add-or-merge-dialog").hide();
                return false;
            });
        });
    });




function add_or_merge_dialog(name, folder) {
    $("#selected-add-or-merge-name").text(name);
    $("#selected-add-or-merge-folder").text(folder);
    $("#add-or-merge-dialog").show();
    $("#add-or-merge-dialog").css("display", "inline-block");
}


function send_to_merge(name, folder, merge_to) {
    $.getJSON($SCRIPT_ROOT + "/_merge_with", {
        n: name,
        f: folder,
        m2: merge_to
    });
    return true
}


function new_from_unk(name, folder) {
    $.getJSON($SCRIPT_ROOT + "/_new_person_from_unk", {
        n: name,
        f: folder
    });
    return true
}