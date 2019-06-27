$(document).ready(function()
{
    $(".camera-select").click(function(e)
    {
        $(".camera-fieldset").hide()
        $("#"+e.target.id+"-fieldset").show()
    })

    $(".has-surrogate").click(function(e)
    {
        $("#"+e.target.id+"-surrogate").prop("checked", !e.target.checked)
    })
})