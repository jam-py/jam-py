
function on_page_loaded(task) {
    11
    $("title").text(task.item_caption);
    $("#title").text(task.item_caption);
    
    if (task.safe_mode) {
        $("#user-info").text(task.user_info.role_name + ' ' + task.user_info.user_name);
        $('#log-out')
        .show() 
        .click(function(e) {
            e.preventDefault();
            task.logout();
        }); 
    }

    $("#taskmenu").show();
    task.each_item(function(group) {
        var li,
            li_html = group.item_caption,
            ul;
        if (group.visible) {
            if (group.items.length) {
                li_html += ' <b class="caret"></b>';
            }
            li = $('<li class="dropdown"><a class="dropdown-toggle" data-toggle="dropdown" href="#">' + 
                li_html + '</a></li>');                        
            $("#menu").append(li);
            if (group.items.length) {
                ul = $('<ul class="dropdown-menu">'); 
                li.append(ul);
                group.each_item(function(item) {
                    if (item.visible) {
                        ul.append($('<li>')
                            .append($('<a class="item-menu" href="#">' + item.item_caption + '</a>').data('item', item)));                    
                    }
                });
            }
        }
    });

    $('#menu .item-menu').on('click', (function(e) {
        var item = $(this).data('item'); 
        e.preventDefault();
        if (item.item_type === "report") { 
            item.print(false);
        } 
        else { 
            item.view($("#content"));
        }
    }));

    $("#menu").append($('<li></li>').append($('<a href="#">Dashboard</a>').click(function(e) {
        e.preventDefault();
        task.dashboard.view($("#content"));
    })));
    
    $("#menu").append(
        '<li id="themes" class="dropdown">' +
            '<a class="dropdown-toggle" data-toggle="dropdown" href="#">Themes <b class="caret"></b></a>' +
            '<ul class="dropdown-menu">' +
                '<li><a href="#">Bootrap</a></li>' +
                '<li><a href="#">Cerulean</a></li>' +                
                '<li><a href="#">Amelia</a></li>' +                
                '<li><a href="#">Flatly</a></li>' +
                '<li><a href="#">Journal</a></li>' +                
                '<li><a href="#">Slate</a></li>' +
                '<li><a href="#">United</a></li>' +                
                '<li><a href="#">Cosmo</a></li>' +
                '<li><a href="#">Readable</a></li>' +
                '<li><a href="#">Spacelab</a></li>' +                
                '<li class="divider"></li>' +
                '<li><a href="#">Container</a></li>' +
            '</ul>' +
        '</li>'
    );  
    set_theme(task, 'Cerulean');
    $('#menu #themes ul a').on('click', (function(e) {
        e.preventDefault();        
        set_theme(task, $(this).text().substr(2));
    }));
    $("#menu").append($('<li></li>').append($('<a href="#">About</a>').click(function(e) {
        e.preventDefault();
        task.message(
            task.templates.find('.about'),
            {title: 'Jam.py framework', margin: 0, text_center: true, 
                buttons: {"OK": undefined}, center_buttons: true}
        );
    })));
    
    $("#menu").append($('<li><a href="http://jam-py.com/" target="_blank">Jam.py</a></li>'));     
  
//    task.customers.view($("#content"));
    $('#menu .item-menu:first').click(); 

    // $(document).ajaxStart(function() { $("html").addClass("wait"); });
    // $(document).ajaxStop(function() { $("html").removeClass("wait"); });
} 

function set_theme(task, theme) {
    var new_css,
        old_css;
    if (!task.theme) {
        task.theme = theme;
        task.small_font = true;
        task.in_container = true;
        $('#menu #themes ul a').each(function() {
            var theme = $(this).text();
            $(this).html('&nbsp;&nbsp;' + theme);
        });
    }
    if (theme === 'Container') {
        task.in_container = !task.in_container;
        if (task.in_container) {
            $('body #container').addClass('container');
        }
        else {
            $('body #container').removeClass('container');
        }
        $('#menu .item-menu:first').click();         
        $('window').resize();        
    }
    else {
        new_css = get_theme(task, theme),
        old_css = get_theme(task, task.theme);
        if (theme !== task.theme) {
            $("head").find("link").attr("href", function () {
                if (this.href.split('/').pop() === old_css) {
                    this.href = this.href.replace(old_css, new_css);
                }
            });
            task.theme = theme;
//            $('#menu .item-menu:first').click();
            $('window').resize();            
        }
    }
    $('#menu #themes ul a').each(function() {
        var theme = $(this).text().substr(2);
        if (theme === 'Container' && task.in_container) {
            $(this).html('&#x2714;&nbsp;' + theme);
        }        
        else if (theme === task.theme) {
            $(this).html('&#x2714;&nbsp;' +theme);
        }
        else {
            $(this).html('&nbsp;&nbsp;' + theme);            
        }
    });        
}

function get_theme(task, theme) {
    var css;
    if (theme === 'Bootrap') {
        css = "bootstrap.css";
    }
    else if (theme === 'Cosmo') {
        css = "bootstrap-cosmo.css";
    }
    else if (theme === 'Cerulean') {
        css = "bootstrap-cerulean.css";
    }
    else if (theme === 'Journal') {
        css = "bootstrap-journal.css";
    }
    else if (theme === 'Flatly') {
        css = "bootstrap-flatly.css";
    }
    else if (theme === 'Slate') {
        css = "bootstrap-slate.css";
    }
    else if (theme === 'Amelia') {
        css = "bootstrap-amelia.css";
    }
    else if (theme === 'United') {
        css = "bootstrap-united.css";
    }
    else if (theme === 'Spacelab') {
        css = "bootstrap-spacelab.css";
    }
    else if (theme === 'Readable') {
        css = "bootstrap-readable.css";
    }
    return css;
}

function on_view_form_created(item) {
    var table_options = {
            height: 580,
            sortable: true
        };
  
    if (!item.master) {
        item.paginate = true;
    }

    item.clear_filters();

    if (item.view_form.hasClass('modal')) {
        item.view_options.width = 1060;
    }
    else {
        item.view$(".modal-body").css('padding', 0);
        item.view$("#title-text")
            .text(item.item_caption)
            .click(function() {
                item.view(item.view_form.parent());
            });
        table_options.height = $(window).height() - $('body').height() - 10;
    }
    if (item.can_create()) {
        item.view$("#new-btn").on('click.task', function() { item.insert_record(); });
    }
    else {
        item.view$("#new-btn").prop("disabled", true);
    }
    if (item.can_edit()) {
        item.view$("#edit-btn").on('click.task', function() { item.edit_record() });
    }
    else {
        item.view$("#edit-btn").prop("disabled", true);
    }
    if (item.can_delete()) {
        item.view$("#delete-btn").on('click.task', function() { item.delete_record() } );
    }
    else {
        item.view$("#delete-btn").prop("disabled", true);
    }
    
    create_print_btns(item);

    if (item.view$(".view-table").length) {
        if (item.init_table) {
            item.init_table(item, table_options);
        }
        item.create_table(item.view$(".view-table"), table_options);
        item.open(true);        
    }
}

function on_view_form_closed(item) {
    item.close();
}

function on_edit_form_created(item) {
    var options = {
            col_count: 1,
            create_inputs: true
        };
    if (item.init_inputs) {
        item.init_inputs(item, options);
    }
    if (options.create_inputs) {
        item.create_inputs(item.edit_form.find(".edit-body"), options);
    }
    item.edit$("#cancel-btn").on('click.task', function(e) { item.cancel_edit(e) });
    item.edit$("#ok-btn").on('click.task', function() { item.apply_record() });
}

function on_edit_form_close_query(item) {
    var result = true;
    if (item.is_changing()) {
        if (item.is_modified()) {
            item.yes_no_cancel(task.language.save_changes,
                function() {
                    item.apply_record();
                },
                function() {
                    item.cancel_edit();
                }
            );
            result = false;
        }
        else {
            item.cancel();
        }
    }
    return result;
}

function on_filter_form_created(item) {
    item.filter_options.title = item.item_caption + ' - filter';
    item.create_filter_inputs(item.filter$(".edit-body"));
    item.filter$("#cancel-btn")
        .on('click.task', function() { item.close_filter_form() });
    item.filter$("#ok-btn")
        .on('click.task', function() { item.apply_filters() });
}

function on_param_form_created(item) {
    item.create_param_inputs(item.param$(".edit-body"));
    item.param$("#cancel-btn")
        .on('click.task', function() { item.close_param_form() });
    item.param$("#ok-btn")
        .on('click.task', function() { item.process_report() });
}

function on_before_print_report(report) {
    var select;
    report.extension = 'pdf';
    if (report.param_form) {
        select = report.param_form.find('select');
        if (select && select.val()) {
            report.extension = select.val();
        }
    }
}

function on_view_form_keyup(item, event) {
    if (event.keyCode === 45 && event.ctrlKey === true){
        item.insert_record();
    }
    else if (event.keyCode === 46 && event.ctrlKey === true){
        item.delete_record();
    }
}

function on_edit_form_keyup(item, event) {
    if (event.keyCode === 13 && event.ctrlKey === true){
        item.edit$("#ok-btn").focus();
        item.apply_record();
    }
}

function create_print_btns(item) {
    var i,
        $ul,
        $li,
        reports = [];
    if (item.reports) {
        for (i = 0; i < item.reports.length; i++) {
            if (item.reports[i].can_view()) {
                reports.push(item.reports[i]);
            }
        }
        if (reports.length) {
            $ul = item.view_form.find("#report-btn ul");
            for (i = 0; i < reports.length; i++) {
                $li = $('<li><a href="#">' + reports[i].item_caption + '</a></li>');
                $li.find('a').data('report', reports[i]);
                $li.on('click', 'a', function(e) {
                    e.preventDefault();
                    $(this).data('report').print(false);
                });
                $ul.append($li);
            }
        }
        else {
            item.view_form.find("#report-btn").hide();
        }
    }
    else {
        item.view_form.find("#report-btn").hide();
    }
}
