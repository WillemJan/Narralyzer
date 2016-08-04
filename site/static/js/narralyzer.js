$("[id^=chapter]").click(function () {
    var $c=$(this).css("background-color");
    $name=$(this).attr('id').replace('_','');

    if ($("#" + $name).is(':checked')) {
        $(this).css({'background-color' : 'lightgray'});
        $("#" + $name).attr('checked', false)
    } else {
        $(this).css({'background-color' : 'lightgreen'});
        $name=$(this).attr('id').replace('_','');
        $("#" + $name).attr('checked', true)
    }
});


