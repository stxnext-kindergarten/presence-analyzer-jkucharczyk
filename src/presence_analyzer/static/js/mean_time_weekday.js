(function($) {
    $(document).ready(function() {
        var loading = $('#loading');
        $.getJSON("/api/v1/users", function(result) {
            var dropdown = $("#user_id");
            data_img = {};
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this[0]).text(this[1]["name"]));
                data_img[this[0]] = this[1]["avatar_url"];
            });
            dropdown.show();
            loading.hide();
        });
        $('#user_id').change(function() {
            var selected_user = $("#user_id").val(),
                chart_div = $('#chart_div');
                user_img = $('#user_img');
            $('#user_no_data').hide()
            if(selected_user) {
                loading.show();
                chart_div.hide();
                user_img.hide();
                user_img.attr('src', data_img[selected_user]);;
                $.ajax({
                    type: 'HEAD',
                    url: "/api/v1/mean_time_weekday/" + selected_user,
                    success: $.getJSON("/api/v1/mean_time_weekday/" + selected_user, function(result) {
                        $.each(result, function(index, value) {
                            value[1] = parseInterval(value[1]);
                        });
                        var data = new google.visualization.DataTable();
                        data.addColumn('string', 'Weekday');
                        data.addColumn('datetime', 'Mean time (h:m:s)');
                        data.addRows(result);
                        var options = {
                            hAxis: {title: 'Weekday'}
                        },
                            formatter = new google.visualization.DateFormat({pattern: 'HH:mm:ss'});
                        formatter.format(data, 1);                 
                        chart_div.show();
                        if (selected_user != 0) {
                            user_img.show();
                        }
                        loading.hide();
                        var chart = new google.visualization.ColumnChart(chart_div[0]);
                        chart.draw(data, options);
                    }),
                    error: function() {
                        loading.hide();
                        if (selected_user != 0) {
                            $('#user_no_data').show();
                            user_img.show();
                        }
                    }
                });
            }
        });
    });
})(jQuery);
