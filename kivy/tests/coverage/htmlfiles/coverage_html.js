// Coverage.py HTML report browser code.

// Loaded on index.html
function index_ready($) {
    // Look for a cookie containing previous sort settings:
    sort_list = [];
    cookie_name = "COVERAGE_INDEX_SORT";

    // This almost makes it worth installing the jQuery cookie plugin:
    if (document.cookie.indexOf(cookie_name) > -1) {
        cookies = document.cookie.split(";");
        for (var i=0; i < cookies.length; i++) {
            parts = cookies[i].split("=")

            if ($.trim(parts[0]) == cookie_name && parts[1]) {
                sort_list = eval("[[" + parts[1] + "]]");
                break;
            }
        }
    }

    // Create a new widget which exists only to save and restore
    // the sort order:
    $.tablesorter.addWidget({
        id: "persistentSort",

        // Format is called by the widget before displaying:
        format: function(table) {
            if (table.config.sortList.length == 0 && sort_list.length > 0) {
                // This table hasn't been sorted before - we'll use
                // our stored settings:
                $(table).trigger('sorton', [sort_list]);
            }
            else {
                // This is not the first load - something has
                // already defined sorting so we'll just update
                // our stored value to match:
                sort_list = table.config.sortList;
            }
        }
    });

    // Configure our tablesorter to handle the variable number of
    // columns produced depending on report options:
    var headers = {};
    var col_count = $("table.index > thead > tr > th").length;

    headers[0] = { sorter: 'text' };
    for (var i = 1; i < col_count-1; i++) {
        headers[i] = { sorter: 'digit' };
    }
    headers[col_count-1] = { sorter: 'percent' };

    // Enable the table sorter:
    $("table.index").tablesorter({
        widgets: ['persistentSort'],
        headers: headers
    });

    // Watch for page unload events so we can save the final sort settings:
    $(window).unload(function() {
        document.cookie = cookie_name + "=" + sort_list.toString() + "; path=/"
    });
}

// -- pyfile stuff --

function pyfile_ready($) {
    // If we're directed to a particular line number, highlight the line.
    var frag = location.hash;
    if (frag.length > 2 && frag[1] == 'n') {
        $(frag).addClass('highlight');
    }
}

function toggle_lines(btn, cls) {
    btn = $(btn);
    var hide = "hide_"+cls;
    if (btn.hasClass(hide)) {
        $("#source ."+cls).removeClass(hide);
        btn.removeClass(hide);
    }
    else {
        $("#source ."+cls).addClass(hide);
        btn.addClass(hide);
    }
}
