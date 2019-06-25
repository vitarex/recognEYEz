$(document).ready(function()
{
    $(".camera-select").click(function(e)
    {
        $(".camera-fieldset").hide()
        $("#"+e.target.id+"-fieldset").show()
    })
})