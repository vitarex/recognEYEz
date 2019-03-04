
$(function () {

    $(".remove-person-btn").each(function (index) {
        // alert("for one" + index);
        $(this).bind('click', function () {
            name = $(".remove-arg", this).text();
            folder = $(".remove-folder-arg", this).text();
            $("#remove-dialog-text").html(name);
            confirm_delete(name, folder);
            return false;
        });
    });
});




function confirm_delete(name, folder) {
    $("#remove-confirmation").dialog({
        resizable: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
            Remove: function() {
                if (folder) {
                    send_unknown_to_remove(name, folder, '/_remove_unknown_person');
                }
                else {
                    send_known_to_remove(name, '/_remove_person');
                }
                $(this).dialog("close");
                location.reload();
            },
            Cancel: function () {
                $(this).dialog("close");
                return false
            }
        }
    });
};


function send_known_to_remove(name, target_url) {
    $.getJSON($SCRIPT_ROOT + target_url, {
        p: name
    });
    return true
}


function send_unknown_to_remove(name, folder, target_url) {
    $.getJSON($SCRIPT_ROOT + target_url, {
        p: name,
        f: folder
    });
    return true
}