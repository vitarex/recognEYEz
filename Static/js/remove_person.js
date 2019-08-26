$("body").ready(function() {
    $(".remove-person-button").click(function() {
        name = $(".remove-arg", this).text();
        if (confirm(`Are you sure you want to delete the person: ${name}?`))
        {
            remove_person(name, function() {
                if($(this).hasClass('person-btn-unk')){
                    $(this).parents(".unknown-person-wrapper").first().fadeTo(200, 0.01, function(){ 
                        $(this).slideUp(150, function() {
                            $(this).remove(); 
                        }); 
                    });
                }
                else {
                    $(this).parents(".known-person-wrapper").first().fadeTo(200, 0.01, function(){ 
                        $(this).slideUp(150, function() {
                            $(this).remove(); 
                        }); 
                    });
                }
            }.bind(this));
        }
        return false;
    });
});

function remove_person(name, success_func){
    $.ajax({
        url: $SCRIPT_ROOT + "/remove_person",
        data: { name: name},
        type: "POST",
        success: success_func,
        error: function(error) {
            alert(error.responseJSON.message);
        }
    });
}