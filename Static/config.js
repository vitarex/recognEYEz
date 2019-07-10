$(document).ready(function()
{
    $(".camera-select").click(function(e)
    {
         $(".camera-fieldset").hide().prop("disabled",true)
        $("#"+e.target.id+"-fieldset").show().prop("disabled",false)
    })

    $(".has-surrogate").click(function(e)
    {
        $("#"+e.target.id+"-surrogate").prop("checked", !e.target.checked)
    })
})

/*
function update_face_rec_configuration_settings(camera, ) {
    $.ajax({
    url: $SCRIPT_ROOT + "/face_recognition_settings",
    data: {},
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(JSON.parse(error).message);
    });
}
*/

function update_notification_settings(email, broker_url,port, topic, m_notif_spec, m_notif_kno, m_notif_unk, e_notif_spec, e_notif_kno, e_notif_unk) {
    $.ajax({
    url: $SCRIPT_ROOT + "/notification_settings",
    data: {email,
        broker_url: broker_url,
        port: port,
        topic: topic,
        m_notif_spec: m_notif_spec,
        m_notif_kno: m_notif_kno,
        m_notif_unk: m_notif_unk,
        e_notif_spec: e_notif_spec,
        e_notif_kno: e_notif_kno,
        e_notif_unk: e_notif_unk},
    type: "POST",
    success: success_func,
    error: function(error) {
      alert(JSON.parse(error).message);
    });
}