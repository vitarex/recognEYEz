$(document).ready(function()
{
    $(".camera-select").click(function(e)
    {
         $(".camera-fieldset").hide().prop("disabled",true)
        $("#"+e.target.id+"-fieldset").show().prop("disabled",false)
    })

    $(".has-surrogate").click(function(e)
    {
        $("#"+e.target.id+"-surrogate").checked = !e.target.checked
    })
})