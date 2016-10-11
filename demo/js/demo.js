(function($, task) {
"use strict";

function Events1() { // demo 

	function on_page_loaded(task) { 
		
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
		for (var i = 0; i < task.items.length; i++) {
			if (task.items[i].visible) {
				$("#menu").append(
					$('<li></li>').append(
						$('<a href=""></a>').text(task.items[i].item_caption).data('group', task.items[i])
					)
				);
			}
		}
		$('#menu').on('click', 'a', (function(e) {
				var submenu = $("#submenu"),
					group = $(this).data('group'),
					item;
				if (group) {
					e.preventDefault();
					submenu.empty();
					$("#menu > li" ).removeClass('active');
					$(this).parent().addClass('active');
					for (var i = 0; i < group.items.length; i++) {
						item = group.items[i];
						if (item.visible && item.can_view()) {
							submenu.append($('<li></li>').append(
									$('<a href=""></a>').text(item.item_caption).data('item', item)
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
			if (item.item_type === "report") { 
				item.print(false);
			} 
			else { 
				item.view($("#content"));
			}
		}));
		
		$("#menu").append($('<li></li>').append($('<a href="#">About</a>').click(function(e) {
			e.preventDefault();
			task.message(
				'<a href="http://jam-py.com/" target="_blank"><h3>Jam.py</h3></a>' +
				'<h3>Demo application</h3>' +
				' with <a href="http://chinookdatabase.codeplex.com/" target="_blank">Chinook Database</a>' +
				'<p>by Andrew Yushev</p>' +
				'<p>2016</p>',
				{title: 'Jam.py framework', margin: 0, text_center: true, buttons: {"OK": undefined}, center_buttons: true}
			);
		})));
		$("#menu").append($('<li><a href="http://jam-py.com/" target="_blank">Jam.py</a></li>'));	
		
		$('#menu').children(":first").find('a').click();
		$('#submenu').children(":first").find('a').click();	
		
		// $(document).ajaxStart(function() { $("html").addClass("wait"); });
		// $(document).ajaxStop(function() { $("html").removeClass("wait"); });
	
		$(window).on('resize', function() {
			resize(task);
		});
	} 
	
	function on_view_form_created(item) {
		var table_options = {
				height: 480,
				sortable: true
			};
			
		if (!item.master) {
			item.paginate = true;
		}
		item.clear_filters();
	
		if (item.view_form.hasClass('modal')) {
			item.view_options.width = 960;
		}
		else {
			item.view_form.find(".modal-body").css('padding', 0);
			item.view_form.find(".view-title #title-left")
				.append($('<h4>' + item.item_caption + '<h4>'));
			table_options.height = $(window).height() - $('body').height() - 10;
		}
		if (item.can_create()) {
			item.view_form.find("#new-btn")
				.on('click.task', function() { item.insert_record(); });
		}
		else {
			item.view_form.find("#new-btn").prop("disabled", true);
		}
		if (item.can_edit()) {
			item.view_form.find("#edit-btn")
				.on('click.task', function() { item.edit_record(); });
		}
		else {
			item.view_form.find("#edit-btn").prop("disabled", true);
		}
		if (item.can_delete()) {
			item.view_form.find("#delete-btn")
				.on('click.task', function() { item.delete_record();} );
		}
		else {
			item.view_form.find("#delete-btn").prop("disabled", true);
		}
		
		create_print_btns(item);
	
		if (item.init_table) {
			item.init_table(item, table_options);
		}
		item.create_table(item.view_form.find(".view-table"), table_options);
		
		item.open(function() {});	
	}
	
	
	function on_view_form_close_query(item) {
		item.close();
	}
	
	function on_edit_form_created(item) {
		var input_options = {
				col_count: 1
			};
		item.edit_options.width = 560;
		if (item.init_inputs) {
			item.init_inputs(item, input_options);
		}
		item.create_inputs(item.edit_form.find(".edit-body"), input_options);
		item.edit_form.find("#cancel-btn").on('click.task', function(e) { item.cancel_edit(e) });
		item.edit_form.find("#ok-btn").on('click.task', function() { item.apply_record() });
	}
	
	function on_edit_form_shown(item) {
		resize_edit_table(item);	
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
		item.create_filter_inputs(item.filter_form.find(".edit-body"));
		item.filter_form.find("#cancel-btn")
			.on('click.task', function() { item.close_filter_form() });
		item.filter_form.find("#ok-btn")
			.on('click.task', function() { item.apply_filters() });
	}
	
	function on_param_form_created(item) {
		item.create_param_inputs(item.param_form.find(".edit-body"));
		item.param_form.find("#cancel-btn")
			.on('click.task', function() { item.close_param_form() });
		item.param_form.find("#ok-btn")
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
			item.edit_form.find("#ok-btn").focus();
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
	
	function resize_view_table(item) {
		item.view_form.find(".dbtable").each(function() {
			var height,
				table = $(this).data('dbtable');
			if (table && table.item === item) {
				height = table.height() + $(window).height() - $('body').height() - 10;
				if (height < 200) {
					height = 200;
				}
				table.height(height);
				item.update_controls();
				item.each_detail(function(d) {
					d.update_controls();
				});
			}
		});
	}
	
	function resize_edit_table(item, window_resized) {
		item.edit_form.find(".dbtable").each(function() {
			var height,
				form_height = item.edit_form.height(),
				window_height = $(window).height(),
				table = $(this).data('dbtable');
			if (table) {
				if (window_resized || form_height > window_height - 20) {
					height = table.height() - (form_height - window_height) - 20;
					if (height > 450) {
						height = 450;
					}
					if (height < 200) {
						height = 200;
					}
					table.height(height);
					item.update_controls();
				}			
			}
		});
	}
	
	var timeOut;
	
	function resize(task) {
		clearTimeout(timeOut);
		timeOut = setTimeout(function() {
			task.all(function(item) {
				  if (item.view_form) {
					  resize_view_table(item);
				  }
				  if (item.edit_form) {
					  resize_edit_table(item, true);
				  }
			});
		},
		200);
	}
	this.on_page_loaded = on_page_loaded;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_close_query = on_view_form_close_query;
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_shown = on_edit_form_shown;
	this.on_edit_form_close_query = on_edit_form_close_query;
	this.on_filter_form_created = on_filter_form_created;
	this.on_param_form_created = on_param_form_created;
	this.on_before_print_report = on_before_print_report;
	this.on_view_form_keyup = on_view_form_keyup;
	this.on_edit_form_keyup = on_edit_form_keyup;
	this.create_print_btns = create_print_btns;
	this.resize_view_table = resize_view_table;
	this.resize_edit_table = resize_edit_table;
	this.resize = resize;
}

task.events.events1 = new Events1();

function Events2() { // demo.catalogs 

	function on_view_form_created(item) {
		var timeOut,
			search;
		if (item.default_field) {
			if (item.lookup_field && item.lookup_field.value) {
				item.view_form.find(".view-title #title-left")
					.append($('<p><a href="#" id="cur_value" tabindex="-1">' + item.lookup_field.lookup_text + '</a></p>'))
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
				var code = e.which;
				if (code === 13) {
					e.preventDefault();
				}
				else if (code === 40) {
					item.view_form.find(".inner-table").focus();
					e.preventDefault();
				}
			});
			item.view_form.on('keydown', function(e) {
				var code = e.which;
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
	
	function on_view_form_shown(item) {
		setTimeout(function() {
				item.view_form.find(".view-title input").focus();
			},
			100
		);	
	}
	this.on_view_form_created = on_view_form_created;
	this.isCharCode = isCharCode;
	this.on_view_form_shown = on_view_form_shown;
}

task.events.events2 = new Events2();

function Events16() { // demo.journals.invoices 

	function on_after_append(item) {
		item.date.value = new Date();
		item.taxrate.value = 5;
	}
	
	function init_table(item, table_options) {
		item.filters.invoicedate1.value = new Date(new Date().setYear(new Date().getFullYear() - 1));
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
	
	function on_view_form_created(item) {
		item.view_form.find("#filter-btn").click(function() {item.create_filter_form()});	
	
		item.invoice_table.create_table(item.view_form.find(".view-detail"),
			{height: 200 - 4, dblclick_edit: false, column_width: {"track": "60%"}});
	}
	
	function on_view_form_shown(item) {
		item.view_form.find(".dbtable.invoices .inner-table").focus();
	}
	
	function on_filters_applied(item) {
		if (item.view_form) {
			item.view_form.find(".view-title #title-right")
				.html('<h5 class="pull-right">' + item.get_filter_text() + '<h5>');
			calc_footer(item);
		}
	}
	
	function calc_footer(item) {
		var copy = item.copy({handlers: false, details: false});
		copy.assign_filters(item);
		copy.open(
			{fields: ['subtotal', 'tax', 'total'], 
			funcs: {subtotal: 'sum', tax: 'sum', total: 'sum'}}, 
			function() {
				var footer = item.view_form.find('.dbtable.' + item.item_name + ' tfoot');
				copy.each_field(function(f) {
					footer.find('div.' + f.field_name)
						.css('text-align', 'right')
						.css('color', 'black')
						.text(f.display_text);
				});
			}
		);
	}
	
	function init_inputs(item, input_options) {
		input_options.col_count = 2;
	}
	
	function on_edit_form_created(item) {
		item.edit_options.width = 1050;
		item.invoice_table.create_table(item.edit_form.find(".edit-detail"),
			{
				height: 450,
				tabindex: 90,
				editable: true,
				editable_fields: ['track', 'quantity'],
				sortable: true,
				column_width: {"track": "60%"}
			});
		item.edit_form.find("#new-btn")
			.on('click.task', function() { item.invoice_table.append_record() });
		item.edit_form.find("#edit-btn")
			.on('click.task', function() { item.invoice_table.edit_record() });
		item.edit_form.find("#delete-btn")
			.on('click.task', function() { item.invoice_table.delete_record() });
	}
	
	function on_get_field_text(field) {
		if (field.field_name === 'customer' && field.value) {
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
	
	function on_edit_form_keyup(item, event) {
		if (event.keyCode === 45 && event.ctrlKey === true){
			item.invoice_table.append_record();
		}
		else if (event.keyCode === 46 && event.ctrlKey === true){
			item.invoice_table.delete_record();
		}
	}
	
	function on_after_apply(item) {
		calc_footer(item);
	}
	
	var ScrollTimeOut;
	
	function on_after_scroll(item) {
		clearTimeout(ScrollTimeOut);
		ScrollTimeOut = setTimeout(
			function() {
				item.invoice_table.open(function() {});
			},
			100
		);
	}
	this.on_after_append = on_after_append;
	this.init_table = init_table;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.on_filters_applied = on_filters_applied;
	this.calc_footer = calc_footer;
	this.init_inputs = init_inputs;
	this.on_edit_form_created = on_edit_form_created;
	this.on_get_field_text = on_get_field_text;
	this.on_field_changed = on_field_changed;
	this.calc_total = calc_total;
	this.calculate = calculate;
	this.on_edit_form_keyup = on_edit_form_keyup;
	this.on_after_apply = on_after_apply;
	this.on_after_scroll = on_after_scroll;
}

task.events.events16 = new Events16();

function Events15() { // demo.catalogs.tracks 

	function init_table(item, options) {
	//	options.sortable = false;
		options.row_line_count = 2;
		options.expand_selected_row = 3;
	}
	
	function on_before_post(item) {
	   item.track.value = item.name.value;
	   if (item.album.value) {
		   item.track.value += '; album: ' + item.album.display_text;
	   }
	   if (item.composer.value) {
		   item.track.value += '; composer: ' + item.composer.display_text;
	   }
	}
	this.init_table = init_table;
	this.on_before_post = on_before_post;
}

task.events.events15 = new Events15();

function Events19() { // demo.reports.invoice 

	function on_before_print_report(report) {
		report.id.value = report.task.invoices.id.value;
	}
	this.on_before_print_report = on_before_print_report;
}

task.events.events19 = new Events19();

function Events20() { // demo.reports.purchases_report 

	function on_param_form_created( report ) {
		var now = new Date();
		if (!report.invoicedate1.value) {
			report.invoicedate1.value = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
			report.invoicedate2.value = now;
		}
	}
	this.on_param_form_created = on_param_form_created;
}

task.events.events20 = new Events20();

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
	this.on_after_post = on_after_post;
	this.on_field_changed = on_field_changed;
	this.on_after_delete = on_after_delete;
}

task.events.events18 = new Events18();

})(jQuery, task)