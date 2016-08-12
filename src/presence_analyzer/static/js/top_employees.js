(function($) {
    $(document).ready(function() {
        var loading = $('#loading');
        $.getJSON("/api/v1/years", function(result) {
            var dropdown_year = $("#year_id");
            $.each(result, function(item) {
                dropdown_year.append($("<option />").val(this).text(this));
            });
            dropdown_year.show();
            loading.hide();
        });
        $('#year_id').change(function() {            
            selected_year = $("#year_id").val();
            $("#month_id").hide()
            $("#chart_div").hide()
            $("#employees_title").hide()
            loading.show()
            if (selected_year != 0) {
                $("#month_id").empty();
                $("#chart_div").empty(); 
                $("#employees_title").empty();
                $("#month_id").append($("<option />").val(0).text('--  '));
                $.getJSON("/api/v1/top_employees/" + selected_year, function(result) {
                    var dropdown_month = $("#month_id");
                    $.each(result, function(item) {
                        var month_val = this[0],
                            month_text = this[1]
                        dropdown_month.append($("<option />").val(month_val).text(month_text));
                        dropdown_month.show();
                    });
                });
            }
            loading.hide();
        });
        $("#month_id").change(function() {
            $("#chart_div").empty();
            $("#chart_div").hide()
            $("#employees_title").empty();
            loading.show();
            var places = ["1st", "2nd", "3rd", "4th", "5th"];
            var selected_month = $("#month_id").val();
                selected_month_text = $("#month_id option:selected").text()
            if (selected_month != 0) {
                $.getJSON("/api/v1/top_employees/" + selected_year + "/" + selected_month, function(result) {
                    for (i = 0; i < Math.min(result.length, 5); i++) {
                        var place = '<p><b>' + places[i] + ' place:</b></p>' ,
                            img_url = "<p><img class='user_img' src=" + result[i][1].avatar_url + '></p>',
                            worker_name = "<p>" + result[i][0] + "</p>",
                            worked_hours = Math.floor(result[i][1].worked_hours),
                            worked_minutes = parseInt((result[i][1].worked_hours % 1) * 60);
                        if (worked_minutes < 10) {
                            worked_minutes = '0' + worked_minutes;
                        }
                        var worked_time = "title='Worked " + worked_hours + ':' + worked_minutes + " hours'";
                        $('#chart_div').append("<div class='worker_div'" + worked_time + " >" + place + img_url + worker_name + '</div>');
                    }
                });
                $('#employees_title').text("TOP 5 employees in " + selected_month_text)
                $('#employees_title').show()
                $('#chart_div').show()
            }
            loading.hide();
        });
    });                    
})(jQuery);
