(function(window, undefined) {
"use strict";
var $ = window.$;

function TaskEvents() {};

window.task_events = new TaskEvents();

function Events1() { // demo 

	function viewItem(item) {
		var content;
		if (item.item_type === "report") {
			item.print_report();
		}
		else {
			content = $("#content");
			content.empty();
			item.task.cur_item = item;
			item.view(content);
		}
	}
	
	
	function on_before_show_main_form(task)  {
		var groups;
	
		$("#title").html( task.item_caption);
		if (task.safe_mode) {
			$("#user-info").text(task.user_info.role_name + ' ' + task.user_info.user_name);
			$('#log-out')
			.show()
			.click(function(e) {
				e.preventDefault();
				task.logout();
			})
		}
	
		groups = [task.journals, task.reports, task.catalogs];
		$("#taskmenu").show();
		for (var i = 0; i < groups.length; i++) {
			$("#menu").append($('<li></li>').append(
				$('<a href="#"></a>')
				.text(groups[i].item_caption)
				.data('group', groups[i])
				.click(function(e) {
					var item,
						submenu = $("#submenu").empty(),
						group = $(this).data('group');
					$("#menu li" ).removeClass('active');
					$(this).parent().addClass('active');
					e.preventDefault();
					for (var i = 0; i < group.items.length; i++) {
						item = group.items[i];
						if (item.visible && item.can_view()) {
							submenu.append($('<li></li>').append(
							$('<a href="#"></a>')
							.text(item.item_caption)
							.data('item', item)
							.click(function(e) {
								var item = $(this).data('item');
								$("#submenu li" ).removeClass('active');
								$(this).parent().addClass('active');
								e.preventDefault();
								viewItem(item);
							})));
						}
					}
			})));
		}
	
		$(window).on('resize', function() {
			resize(task);
		});
	}
	
	function create_print_btns(item) {
		var $ul,
			$li,
			reports = [];
		if (item.reports) {
			for (var i = 0; i < item.reports.length; i++) {
				if (item.reports[i].can_view()) {
					reports.push(item.reports[i]);
				}
			}
			if (reports.length) {
				$ul = item.view_form.find("#report-btn ul");
				for (var i = 0; i < reports.length; i++) {
					$li = $('<li><a href="#">' + reports[i].item_caption + '</a></li>');
					$li.find('a').data('report', reports[i]);
					$li.on('click', 'a', function() {
						$(this).data('report').print_report();
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
	
	function on_before_show_view_form(item) {
		var grid_height;
		if (!item.master) {
			item.auto_loading = true;
		}
		if (item.is_lookup_item) {
			item.view_form.find("#select-btn").on('click.task', function() {item.set_lookup_field_value();});
			item.view_form.modal_width = 960;
			grid_height = 480;
		}
		else {
			item.view_form.find(".modal-body").css('padding', 0);
			item.view_form.find(".view-title #title-left").append($('<h4>' + item.item_caption + '<h4>'));
			item.view_form.find("#select-btn").hide()
			grid_height = $(window).height() - $('body').height() - 40;
		}
	
		if (item.can_create()) {
			item.view_form.find("#new-btn").on('click.task', function() {item.insert_record();});
		}
		else {
			item.view_form.find("#new-btn").attr('disabled','disabled');
		}
		if (item.can_edit()) {
			item.view_form.find("#edit-btn").on('click.task', function() {item.edit_record();});
		}
		else {
			item.view_form.find("#edit-btn").attr('disabled','disabled');
		}
		if (item.can_delete()) {
			item.view_form.find("#delete-btn").on('click.task', function() {item.delete_record();});
		}
		else {
			item.view_form.find("#delete-btn").attr('disabled','disabled');
		}
	
		item.view_grid = item.create_grid(item.view_form.find(".view-table"),
			{
				height: grid_height,
				word_wrap: false,
				sortable: true,
			}
		);
	
		create_print_btns(item);
	}
	
	function on_after_show_view_form(item) {
		item.open();
	}
	
	function on_before_show_edit_form(item) {
		var col_count = 1,
			width = 560;
		item.edit_form.modal_width = width;
		item.create_entries(item.edit_form.find(".edit-body"), {col_count: col_count});
		item.edit_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function(e) {item.cancel_edit(e); return false;});
		item.edit_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.apply_record()});
	}
	
	function on_after_show_edit_form(item) {
		if (item.details_active) {
			item.eachDetail(function(d) {
				d.update_controls();
			});
		}
		else {
			item.open_details();
		}
		resize_edit_grid(item);
	}
	
	function on_edit_form_close_query(item) {
		if (item.is_changing()) {
			if (item.modified) {
				item.yesNoCancel(task.language.save_changes,
					function() {
						item.apply_record();
					},
					function() {
						item.cancel_edit();
					}
				);
				return false;
			}
			else {
				item.cancel();
				return true;
			}
		}
	}
	
	function on_before_show_filter_form(item) {
		item.filter_form.title = item.item_caption + ' - filter';
		item.create_filter_entries(item.filter_form.find(".edit-body"));
		item.filter_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function() {item.close_filter()});
		item.filter_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.apply_filter()});
	}
	
	function on_before_show_params_form(item) {
		item.create_params(item.params_form.find(".edit-body"));
		item.params_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function() {item.close_params_form()});
		item.params_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.process_report()});
	}
	
	function on_view_keypressed(item, event) {
		if (event.keyCode === 45 && event.ctrlKey === true){
			event.preventDefault();
			item.insert_record();
		}
		else if (event.keyCode === 46 && event.ctrlKey === true){
			event.preventDefault();
			item.delete_record();
		}
	}
	
	function on_edit_keypressed(item, event) {
		if (event.keyCode === 13 && event.ctrlKey === true){
			event.preventDefault();
			item.edit_form.find("#ok-btn").focus();
			item.apply_record();
		}
	}
	
	function resize_view_grid(item) {
		var newHeight;
		if (item.view_grid) {
			newHeight = item.view_grid.height() + $(window).height() - $('body').height() - 40;
			if (newHeight < 200) {
				newHeight = 200;
			}
			item.view_grid.height(newHeight);
			item.view_grid.resize();
		}
	}
	
	function resize_edit_grid(item, window_resized) {
		var edit_form_height,
			window_height,
			newHeight;
		if (item.edit_form && item.edit_grid) {
			edit_form_height = item.edit_form.height();
			window_height = $(window).height();
			if (window_resized || edit_form_height > window_height - 20) {
				newHeight = item.edit_grid.height() - (edit_form_height - window_height) - 20;
				if (newHeight > 450) {
					newHeight = 450;
				}
				if (newHeight < 200) {
					newHeight = 200;
				}
				item.edit_grid.height(newHeight);
				item.edit_grid.resize();
			}
		}
	}
	
	var timeOut;
	
	function resize(task) {
		var item = task.cur_item;
		clearTimeout(timeOut);
		timeOut = setTimeout(function() {
			if (item) {
				resize_view_grid(item);
				resize_edit_grid(item, true);
			}
		},
		100);
	}
	this.viewItem = viewItem;
	this.on_before_show_main_form = on_before_show_main_form;
	this.create_print_btns = create_print_btns;
	this.on_before_show_view_form = on_before_show_view_form;
	this.on_after_show_view_form = on_after_show_view_form;
	this.on_before_show_edit_form = on_before_show_edit_form;
	this.on_after_show_edit_form = on_after_show_edit_form;
	this.on_edit_form_close_query = on_edit_form_close_query;
	this.on_before_show_filter_form = on_before_show_filter_form;
	this.on_before_show_params_form = on_before_show_params_form;
	this.on_view_keypressed = on_view_keypressed;
	this.on_edit_keypressed = on_edit_keypressed;
	this.resize_view_grid = resize_view_grid;
	this.resize_edit_grid = resize_edit_grid;
	this.resize = resize;
}

window.task_events.events1 = new Events1();

function Events2() { // demo.catalogs 

	function on_before_show_view_form(item) {
		var timeOut,
			search;
		if (item.default_field) {
			if (item.is_lookup_item && item.lookup_field && item.lookup_field.value) {
				item.view_form.find(".view-title #title-left")
					.append($('<p><a href="#" id="cur_value">' + item.lookup_field.lookup_text + '</a></p>'))
					.css('padding-top', '12px');
				item.view_form.find("#cur_value").click(function() {
					var text = item.view_form.find("#cur_value").text();
					item.view_form.find('#input-find').val(text);
					item.search(item.default_field.field_name, text);
				});
			}
			search = item.view_form.find(".view-title input");
			search.on('input', function() {
				var where = {},
					input = $(this);
				clearTimeout(timeOut);
				timeOut = setTimeout(function() {
	//					where[item.default_field.field_name + '__contains'] = input.val();
	//					item.open({where: where});
						item.search(item.default_field.field_name, input.val());
					},
					500
				);
			});
			search.keydown(function(e) {
				var code = (e.keyCode ? e.keyCode : e.which);
				if (code === 13) {
					e.preventDefault();
				}
				else if (code === 40) {
					item.view_form.find(".inner-table").focus();
					e.preventDefault();
				}
			});
			item.view_form.keypress(function(e) {
				var ch = String.fromCharCode(e.which),
					input,
					digits = '0123456789';
				if (digits.indexOf(ch) === -1 && e.which !== 13) {
					input = item.view_form.find('#input-find');
					if (!input.is(":focus")) {
						input.focus();
					}
				}
			});
		}
		else {
			item.view_form.find("#title-right .form-inline").hide()
		}
	}
	
	function on_after_show_view_form(item) {
		item.view_form.find(".view-title input").focus();
	}
	this.on_before_show_view_form = on_before_show_view_form;
	this.on_after_show_view_form = on_after_show_view_form;
}

window.task_events.events2 = new Events2();

function Events3() { // demo.journals 

	function on_before_show_view_form(item) {
		var gridHeight;
		item.view_form.find("#filter-btn").click(function() {item.create_filter_form()});
		item.on_filter_applied = function(item) {
			if (item.view_form) {
				item.view_form.find(".view-title #title-right")
					.html('<h5 class="pull-right">' + item.get_status_text() + '<h5>');
			}
		}
	}
	this.on_before_show_view_form = on_before_show_view_form;
}

window.task_events.events3 = new Events3();

function Events4() { // demo.tables 

	function on_before_show_view_form(item) {
		var gridHeight;
		item.view_form.find("#filter-btn").click(function() {item.create_filter_form()});
		item.on_filter_applied = function(item) {
			if (item.view_form) {
				item.view_form.find(".view-title #title-right")
					.html('<h5 class="pull-right">' + item.get_status_text() + '<h5>');
			}
		}
	}
	this.on_before_show_view_form = on_before_show_view_form;
}

window.task_events.events4 = new Events4();

function Events5() { // demo.reports 

	function on_before_print_report(report) {
		report.extension = 'pdf';
	}
	this.on_before_print_report = on_before_print_report;
}

window.task_events.events5 = new Events5();

})( window )