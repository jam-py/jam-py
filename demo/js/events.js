(function(window, undefined) {
"use strict";
var $ = window.$;

function TaskEvents() {}

window.task_events = new TaskEvents();

function Events1() { // demo 

	function on_page_loaded(task) {
		var content = $("#content"),
			groups = [task.journals, task.reports, task.catalogs];
	
		$("#title").html('Jam.py demo application');
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
		for (var i = 0; i < groups.length; i++) {
			$("#menu").append($('<li></li>').append(
					$('<a href="#"></a>').text(groups[i].item_caption).data('group', groups[i])
				)
			);
		}
		$('#menu').on('click', 'a', (function(e) {
				var submenu = $("#submenu"),
					group = $(this).data('group'),
					item;
				e.preventDefault();
				if (group) {
					submenu.empty();
					$("#menu > li" ).removeClass('active');
					$(this).parent().addClass('active');
					for (var i = 0; i < group.items.length; i++) {
						item = group.items[i];
						if (item.visible && item.can_view()) {
							submenu.append($('<li></li>').append(
									$('<a href="#"></a>').text(item.item_caption).data('item', item)
								)
							);
						}
					}
				}
			}
		));
		$('#submenu').on('click', 'a', (function(e) {
			var item = $(this).data('item');
			e.preventDefault();
			$("#submenu > li" ).removeClass('active');
			$(this).parent().addClass('active');
			if (item.task.cur_item) {	
				item.task.cur_item.close_view_form();  
			}
			if (item.item_type === "report") { 
				item.print_report(false);
			} 
			else { 
				content.empty();
				item.task.cur_item = item;
				item.view(content);
			}
		}));
		$("#menu").append($('<li></li>').append($('<a href="#">About</a>').click(function(e) {
			e.preventDefault();
			task.information($(
				'<a href="http://jam-py.com/" target="_blank"><h3>Jam.py</h3></a>' +
				'<h3>Demo application</h3>' +
				' with <a href="http://chinookdatabase.codeplex.com/" target="_blank">Chinook Database</a>' +
				'<p>by Andrew Yushev</p>' +
				'<p>2014</p>'),
				{title: 'Jam.py framework', margin: 0, text_center: true, buttons: {"OK": undefined}, center_buttons: true}
			);
		})));
	
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
					$li.on('click', 'a', function(e) {
						e.preventDefault();
						$(this).data('report').print_report(false);
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
		var expand_selected_row,
			table_options = {
				height: 480,
				word_wrap: false,
				sortable: true
			};
		if (!item.master) {
			item.paginate = true;
		}
		if (item.view_form.hasClass('modal')) {
			item.view_options.width = 960;
		}
		else {
			item.view_form.find(".modal-body").css('padding', 0);
			item.view_form.find(".view-title #title-left").append($('<h4>' + item.item_caption + '<h4>'));
			table_options.height = $(window).height() - $('body').height() - 10;
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
		
		create_print_btns(item);
	
		if (item.init_table) {
			item.init_table(item, table_options);
		}
		item.view_table = item.create_table(item.view_form.find(".view-table"), table_options);
	}
	
	function on_after_show_view_form(item) {
		expand_buttons(item.view_form);
		item.open();
	}
	
	function on_before_show_edit_form(item) {
		var input_options = {
				col_count: 1
			};
		item.edit_options.width = 560;
		if (item.init_inputs) {
			item.init_inputs(item, input_options);
		}
		item.create_inputs(item.edit_form.find(".edit-body"), input_options);
		item.edit_form.find("#cancel-btn").attr("tabindex", 101)
			.on('click.task', function(e) {item.cancel_edit(e); return false;});
		item.edit_form.find("#ok-btn").attr("tabindex", 100)
			.on('click.task', function() {item.apply_record()});
	}
	
	function expand_buttons(form) {
		form.find(".modal-footer button.btn").each(function() {
			if ($(this).outerWidth() < 100) {
				$(this).outerWidth(100);
			}
		});
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
		expand_buttons(item.edit_form);
		resize_edit_table(item);	
	}
	
	function on_edit_form_close_query(item) {
		var result = true;
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
				result = false;
			}
			else {
				item.cancel();
			}
		}
		return result;
	}
	
	function on_before_show_filter_form(item) {
		item.filter_form.title = item.item_caption + ' - filter';
		item.create_filter_inputs(item.filter_form.find(".edit-body"));
		item.filter_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function() {item.close_filter()});
		item.filter_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.apply_filter()});
	}
	
	function on_after_show_filter_form(item) {
		expand_buttons(item.filter_form);
	}
	
	function on_before_show_params_form(item) {
		item.create_param_inputs(item.params_form.find(".edit-body"));
		item.params_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function() {item.close_params_form()});
		item.params_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.process_report()});
	}
	
	function on_after_show_params_form(item) {
		expand_buttons(item.params_form);
	}
	
	function on_view_keyup(item, event) {
		if (event.keyCode === 45 && event.ctrlKey === true){
			event.preventDefault();
			item.insert_record();
		}
		else if (event.keyCode === 46 && event.ctrlKey === true){
			event.preventDefault();
			item.delete_record();
		}
	}
	
	function on_edit_keyup(item, event) {
		if (event.keyCode === 13 && event.ctrlKey === true){
			event.preventDefault();
			item.edit_form.find("#ok-btn").focus();
			item.apply_record();
		}
	}
	
	function resize_view_table(item) {
		var height;
		if (item.view_table) {
			height = item.view_table.height() + $(window).height() - $('body').height() - 10;
			if (height < 200) {
				height = 200;
			}
			item.view_table.height(height);
			item.view_table.resize();
		}
	}
	
	function resize_edit_table(item, window_resized) {
		var edit_form_height,
			window_height,
			height;
		if (item.edit_form && item.edit_table) {
			edit_form_height = item.edit_form.height();
			window_height = $(window).height();
			if (window_resized || edit_form_height > window_height - 20) {
				height = item.edit_table.height() - (edit_form_height - window_height) - 20;
				if (height > 450) {
					height = 450;
				}
				if (height < 200) {
					height = 200;
				}
				item.edit_table.height(height);
				item.edit_table.resize();
			}
		}
	}
	
	var timeOut;
	
	
	function resize(task) {
		var item = task.cur_item;
		clearTimeout(timeOut);
		timeOut = setTimeout(function() {
			if (item) {
				resize_view_table(item);
				resize_edit_table(item, true);
			}
		},
		100);
	}
	this.on_page_loaded = on_page_loaded;
	this.create_print_btns = create_print_btns;
	this.on_before_show_view_form = on_before_show_view_form;
	this.on_after_show_view_form = on_after_show_view_form;
	this.on_before_show_edit_form = on_before_show_edit_form;
	this.expand_buttons = expand_buttons;
	this.on_after_show_edit_form = on_after_show_edit_form;
	this.on_edit_form_close_query = on_edit_form_close_query;
	this.on_before_show_filter_form = on_before_show_filter_form;
	this.on_after_show_filter_form = on_after_show_filter_form;
	this.on_before_show_params_form = on_before_show_params_form;
	this.on_after_show_params_form = on_after_show_params_form;
	this.on_view_keyup = on_view_keyup;
	this.on_edit_keyup = on_edit_keyup;
	this.resize_view_table = resize_view_table;
	this.resize_edit_table = resize_edit_table;
	this.resize = resize;
}

window.task_events.events1 = new Events1();

function Events2() { // demo.catalogs 

	function on_before_show_view_form(item) {
		var timeOut,
			search;
		if (item.default_field) {
			if (item.lookup_field && item.lookup_field.value) {
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
				search.css('font-weight', 'normal');
				var where = {},
					input = $(this);
				clearTimeout(timeOut);
				timeOut = setTimeout(function() {
						item.search(item.default_field.field_name, input.val());
						search.css('font-weight', 'bold');
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
			item.view_form.on('keydown', function(e) {
				var code = (e.keyCode ? e.keyCode : e.which);
				if (isCharCode(code) || code === 32 || code === 8) {
					if (!search.is(":focus")) {
						if (code !== 8) {
							search.val('');
						}
						search.focus();
					}
				}
			});
		}
		else {
			item.view_form.find("#title-right .form-inline").hide();
		}
	}
	
	function isCharCode(code) {
		if (code >= 65 && code <= 90 || code >= 186 && code <= 192 || code >= 219 && code <= 222) {
			return true;
		}
	}
	
	function on_after_show_view_form(item) {
		setTimeout(function() {
				item.view_form.find(".view-title input").focus();
			},
			50
		);	
	}
	this.on_before_show_view_form = on_before_show_view_form;
	this.isCharCode = isCharCode;
	this.on_after_show_view_form = on_after_show_view_form;
}

window.task_events.events2 = new Events2();

function Events5() { // demo.reports 

	function on_before_print_report(report) {
		var select;
		report.extension = 'pdf';
		if (report.params_form) {
			select = report.params_form.find('select');
			if (select && select.val()) {
				report.extension = select.val();
			}
		}
	}
	this.on_before_print_report = on_before_print_report;
}

window.task_events.events5 = new Events5();

function Events15() { // demo.catalogs.tracks 

	function init_table(item, table_options) {
		table_options.sortable = false;
	}
	this.init_table = init_table;
}

window.task_events.events15 = new Events15();

function Events16() { // demo.journals.invoices 

	function on_after_append(item) {
		item.invoicedate.value = new Date();
		item.taxrate.value = 5;
	}
	
	function init_table(item, table_options) {
		table_options.height = $(window).height() - $('body').height() - 200 - 10;
		if (table_options.height < 200) {
			table_options.height = 200;
		}
		table_options.show_footer = true;	
		table_options.row_callback = function(row, it) {
			var font_weight = 'normal';
			if (it.total.value > 10) {
				font_weight = 'bold';
			}
			row.find('td.total').css('font-weight', font_weight);
		};
	}
	
	function on_before_show_view_form(item) {
		var now = new Date();
		now.setDate(now.getDate() - 365);
		item.filters.invoicedate1.value = now;
		item.calculating = false;
		
		item.details_active = true;
		item.detail_table = item.invoice_table.create_table(item.view_form.find(".view-detail"),
			{height: 200 - 4, dblclick_edit: false, column_width: {"track": "60%"}});
			
		item.view_form.find("#filter-btn").click(function() {item.create_filter_form()});
	}
	
	function on_filter_applied(item) {
		if (item.view_form) {
			item.view_form.find(".view-title #title-right")
				.html('<h5 class="pull-right">' + item.get_status_text() + '<h5>');
			calc_footer(item);
		}
	}
	
	function calc_footer(item) {
		var copy = item.copy();
		copy.assign_filters(item);
		copy.open({fields: ['subtotal', 'tax', 'total'], funcs: {subtotal: 'sum', tax: 'sum', total: 'sum'}}, function() {
			var footer = item.view_form.find('.dbtable.' + item.item_name + ' tfoot');
			copy.eachField(function(f) {
				footer.find('div.' + f.field_name)
					.css('text-align', 'right')
					.css('color', 'black')
					.text(f.display_text);
			});
		});
	}
	
	function init_inputs(item, input_options) {
		input_options.col_count = 2;
	}
	
	function on_before_show_edit_form(item) {
		item.edit_options.width = 1050;
		item.edit_table = item.invoice_table.create_table(item.edit_form.find(".edit-detail"),
			{
				height: 400,
				tabindex: 90,
				editable: true,
				editable_fields: ['quantity'],
				sortable: true,
				column_width: {"track": "60%"}
			});
		item.edit_form.find("#new-btn").attr("tabindex", 92).on('click.task', function() {item.invoice_table.append_record()});
		item.edit_form.find("#edit-btn").attr("tabindex", 91).on('click.task', function() {item.invoice_table.edit_record()});
		item.edit_form.find("#delete-btn").attr("tabindex", 90).on('click.task', function() {item.invoice_table.delete_record()});
	}
	
	function on_get_field_text(field) {
		if (field.field_name === 'customer') {
			return field.owner.firstname.lookup_text + ' ' + field.lookup_text;
		}
	}
	
	function on_field_changed(field, lookup_item) {
		if (field.field_name === 'taxrate') {
			calculate(field.owner, true);
		}
	}
	
	function calc_total(item) {
		item.amount.value = item.round(item.quantity.value * item.unitprice.value, 2);
		item.tax.value = item.round(item.amount.value * item.owner.taxrate.value / 100, 2);
		item.total.value = item.amount.value + item.tax.value;
	}
	
	function calculate(item, recalc) {
		var subtotal,
			tax,
			total,
			rec;
		if (!item.calculating) {
			item.calculating = true;
			try {
				subtotal = 0;
				tax = 0;
				total = 0;
				item.invoice_table.disable_controls();
				rec = item.invoice_table.rec_no;
				try {
					item.invoice_table.each(function(d) {
						if (recalc) {
							d.edit();
							calc_total(d);
							d.post();
						}
						subtotal += d.amount.value;
						tax += d.tax.value;
						total += d.total.value;
					});
				}
				finally {
					item.invoice_table.rec_no = rec;
					item.invoice_table.enable_controls();
				}
				item.subtotal.value = subtotal;
				item.tax.value = tax;
				item.total.value = total;
				if (recalc) {
					item.invoice_table.update_controls();
				}
			}
			finally {
				item.calculating = false;
			}
		}
	}
	
	function on_edit_keyup(item, event) {
		if (event.keyCode === 45 && event.ctrlKey === true){
			event.preventDefault();
			item.invoice_table.append_record();
		}
		else if (event.keyCode === 46 && event.ctrlKey === true){
			event.preventDefault();
			item.invoice_table.delete_record();
		}
	}
	this.on_after_append = on_after_append;
	this.init_table = init_table;
	this.on_before_show_view_form = on_before_show_view_form;
	this.on_filter_applied = on_filter_applied;
	this.calc_footer = calc_footer;
	this.init_inputs = init_inputs;
	this.on_before_show_edit_form = on_before_show_edit_form;
	this.on_get_field_text = on_get_field_text;
	this.on_field_changed = on_field_changed;
	this.calc_total = calc_total;
	this.calculate = calculate;
	this.on_edit_keyup = on_edit_keyup;
}

window.task_events.events16 = new Events16();

function Events19() { // demo.reports.invoice 

	function on_before_print_report(report) {
		report.id.value = report.task.invoices.id.value;
	}
	this.on_before_print_report = on_before_print_report;
}

window.task_events.events19 = new Events19();

function Events20() { // demo.reports.purchases_report 

	function on_before_show_params_form( report ) {
		var now = new Date();
		if (!report.invoicedate1.value) {
			report.invoicedate1.value = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
			report.invoicedate2.value = now;
		}
	}
	this.on_before_show_params_form = on_before_show_params_form;
}

window.task_events.events20 = new Events20();

function Events18() { // demo.journals.invoices.invoice_table 

	function on_after_post(item) {
		item.owner.calculate(item.owner);
	}
	
	function on_field_changed(field, lookup_item) {
		var item = field.owner;
		if (field.field_name === 'quantity' || field.field_name === 'unitprice') {
			item.owner.calc_total(item);
		}
		else if (field.field_name === 'track' && lookup_item) {
			item.quantity.value = 1;
			item.unitprice.value = lookup_item.unitprice.value;
		}
	}
	
	function on_after_delete(item) {
		item.owner.calculate(item.owner);
	}
	
	function on_after_show_edit_form(item) {
		if (item.is_new()) {
			item.track.select_from_view_form();
		}
	}
	this.on_after_post = on_after_post;
	this.on_field_changed = on_field_changed;
	this.on_after_delete = on_after_delete;
	this.on_after_show_edit_form = on_after_show_edit_form;
}

window.task_events.events18 = new Events18();

})( window )