var preview_interval = null;
$(document).ready(function () {
    $('.start-camera-action').click(function (e) { 
        e.preventDefault();
        $.ajax({
            type: "GET",
            url: "/start_camera",
            success: function (response) {
                let parent = $('.camera-status').parent('p');
                $('.camera-status').remove();
                parent.append("<b class='camera-status' style='color:lightgreen;'>RUNNING</b>");
                preview_interval = setInterval(function(){
                    d = new Date();
                    $(".card-img-top").attr("src", "/preview?"+d.getTime());
                }, 1000);
                $('.preview').append("<img class='card-img-top' src='/preview'>");
            }
        });
    });
    $('.stop-camera-action').click(function (e) { 
        e.preventDefault();
        $.ajax({
            type: "GET",
            url: "/stop_camera",
            success: function (response) {
                let parent = $('.camera-status').parent('p');
                $('.camera-status').remove();
                parent.append("<b class='camera-status' style='color:red;'>NOT RUNNING</b>");
                clearInterval(preview_interval);
                $('.card-img-top').remove();
            }
        });
    });
    $('.force-rescan-action').click(function (e) { 
        e.preventDefault();
        $.ajax({
            type: "GET",
            url: "/force_rescan"
        });
    });
});