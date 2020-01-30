(function($, task) {
"use strict";

function Events1() { // demo 

	function on_page_loaded(task) {
		
		$("title").text(task.item_caption);
		$("#app-title").text(task.item_caption);
		  
		if (task.safe_mode) {
			$("#user-info").text(task.user_info.role_name + ' ' + task.user_info.user_name);
			$('#log-out')
			.show() 
			.click(function(e) {
				e.preventDefault();
				task.logout();
			}); 
		}
	
		if (task.full_width) {
			$('#container').removeClass('container').addClass('container-fluid');
		}
		$('#container').show();
		
		task.create_menu($("#menu"), $("#content"), {
			splash_screen: '<h1 class="text-center">Jam.py Demo Application</h1>',
			view_first: true
		});
	
		$("#menu-right #admin a").click(function(e) {
			var admin = [location.protocol, '//', location.host, location.pathname, 'builder.html'].join('');
			e.preventDefault();
			window.open(admin, '_blank');
		});
		$("#menu-right #about a").click(function(e) {
			e.preventDefault();
			task.message(
				task.templates.find('.about'),
				{title: 'Jam.py framework', margin: 0, text_center: true, 
					buttons: {"OK": undefined}, center_buttons: true}
			);
		});
	
		$("#menu-right #pass a").click(function(e) {
			e.preventDefault();
			task.change_password.open({open_empty: true});
			task.change_password.append_record();
		});
	
		// $(document).ajaxStart(function() { $("html").addClass("wait"); });
		// $(document).ajaxStop(function() { $("html").removeClass("wait"); });
	} 
	
	function on_view_form_created(item) {
		var table_options_height = item.table_options.height,
			table_container;
	
		// item.paginate = false; 
		// item.table_options.show_paginator = false;
		// item.table_options.show_scrollbar = true;
		
		item.clear_filters();
		
		item.view_options.table_container_class = 'view-table';
		item.view_options.detail_container_class = 'view-detail';
		item.view_options.open_item = !item.virtual_table;
		
		if (item.view_form.hasClass('modal')) {
			item.view_options.width = 1060;
			item.table_options.height = $(window).height() - 300;
		}
		else {
			if (!item.table_options.height) {
				item.table_options.height = $(window).height() - $('body').height() - 20;
			}
		}
		
		if (item.can_create()) {
			item.view_form.find("#new-btn").on('click.task', function(e) {
				e.preventDefault();
				if (item.master) {
					item.append_record();
				}
				else {
					item.insert_record();
				}
			});
		}
		else {
			item.view_form.find("#new-btn").prop("disabled", true);
		}
	
		item.view_form.find("#edit-btn").on('click.task', function(e) {
			e.preventDefault();
			item.edit_record();
		});
	
		if (item.can_delete()) {
			item.view_form.find("#delete-btn").on('click.task', function(e) {
				e.preventDefault();
				item.delete_record();
			});
		}
		else {
			item.view_form.find("#delete-btn").prop("disabled", true);
		}
		
		create_print_btns(item);
	
		task.view_form_created(item);
		
		if (!item.master && item.owner.on_view_form_created) {
			item.owner.on_view_form_created(item);
		}
	
		if (item.on_view_form_created) {
			item.on_view_form_created(item);
		}
		
		item.create_view_tables();
		
		if (!item.master && item.view_options.open_item) {
			item.open(true);
		}
	
		if (!table_options_height) {
			item.table_options.height = undefined;
		}
		return true;
	}
	
	function on_view_form_shown(item) {
		item.view_form.find('.dbtable.' + item.item_name + ' .inner-table').focus();
	}
	
	function on_view_form_closed(item) {
		if (!item.master && item.view_options.open_item) {	
			item.close();
		}
	}
	
	function on_edit_form_created(item) {
		item.edit_options.inputs_container_class = 'edit-body';
		item.edit_options.detail_container_class = 'edit-detail';
		
		item.edit_form.find("#cancel-btn").on('click.task', function(e) { item.cancel_edit(e) });
		item.edit_form.find("#ok-btn").on('click.task', function() { item.apply_record() });
		if (!item.is_new() && !item.can_modify) {
			item.edit_form.find("#ok-btn").prop("disabled", true);
		}
		
		task.edit_form_created(item);
		
		if (!item.master && item.owner.on_edit_form_created) {
			item.owner.on_edit_form_created(item);
		}
	
		if (item.on_edit_form_created) {
			item.on_edit_form_created(item);
		}
			
		item.create_inputs(item.edit_form.find('.' + item.edit_options.inputs_container_class));
		item.create_detail_views(item.edit_form.find('.' + item.edit_options.detail_container_class));
	
		return true;
	}
	
	function on_edit_form_shown(item) {
		if (item.check_field_value) {
			item.each_field( function(field) {
				var input = item.edit_form.find('input.' + field.field_name);
				input.blur( function(e) {
					var err;
					if ($(e.relatedTarget).attr('id') !== "cancel-btn") {
						err = item.check_field_value(field);
						if (err) {
							item.alert_error(err);
							input.focus();			 
						}
					}
				});
			});
		}
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
				item.cancel_edit();
			}
		}
		return result;
	}
	
	function on_filter_form_created(item) {
		item.filter_options.title = item.item_caption + ' - filters';
		item.create_filter_inputs(item.filter_form.find(".edit-body"));
		item.filter_form.find("#cancel-btn").on('click.task', function() {
			item.close_filter_form(); 
		});
		item.filter_form.find("#ok-btn").on('click.task', function() { 
			item.set_order_by(item.view_options.default_order);
			item.apply_filters(item._search_params); 
		});
	}
	
	function on_param_form_created(item) {
		item.create_param_inputs(item.param_form.find(".edit-body"));
		item.param_form.find("#cancel-btn").on('click.task', function() { 
			item.close_param_form();
		});
		item.param_form.find("#ok-btn").on('click.task', function() { 
			item.process_report();
		});
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
			if (item.master) {
				item.append_record();
			}
			else {
				item.insert_record();				
			}
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
	this.on_page_loaded = on_page_loaded;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.on_view_form_closed = on_view_form_closed;
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_shown = on_edit_form_shown;
	this.on_edit_form_close_query = on_edit_form_close_query;
	this.on_filter_form_created = on_filter_form_created;
	this.on_param_form_created = on_param_form_created;
	this.on_before_print_report = on_before_print_report;
	this.on_view_form_keyup = on_view_form_keyup;
	this.on_edit_form_keyup = on_edit_form_keyup;
	this.create_print_btns = create_print_btns;
}

task.events.events1 = new Events1();

function Events10() { // demo.catalogs.customers 

	function on_view_form_created(item) {
		item.table_options.multiselect = false;
		if (!item.lookup_field) {	
			var print_btn = item.add_view_button('Print', {image: 'icon-print'}),
				email_btn = item.add_view_button('Send email', {image: 'icon-pencil'});
			email_btn.click(function() { send_email() });
			print_btn.click(function() { print(item) });
			item.table_options.multiselect = true;
		}
	}  
	
	function send_email() {
		if (task.mail.can_create()) {
			task.mail.open({open_empty: true}); 
			task.mail.append_record(); 
		}
		else { 
			item.warning('You are not allowed to send emails.');
		}
	}
	
	function print(item) {
		task.customers_report.customers.value = item.selections;
		task.customers_report.print(false);
	}
	this.on_view_form_created = on_view_form_created;
	this.send_email = send_email;
	this.print = print;
}

task.events.events10 = new Events10();

function Events15() { // demo.catalogs.tracks 

	function on_view_form_created(item) {
		if (!item.lookup_field) {
			item.table_options.height -= 200;
			item.invoice_table = task.invoice_table.copy();
			item.invoice_table.paginate = false;
			item.invoice_table.create_table(item.view_form.find('.view-detail'), {
				height: 200,
				summary_fields: ['date', 'total'],
				on_dblclick: function() {
					show_invoice(item.invoice_table);
				}
			});
			item.alert('Double-click the record in the bottom table to see the invoice in which the track was sold.');
			
			item.table_options.multiselect = true;
			item.add_view_button('Set media type').click(function() {
				set_media_type(item);
			});   
		}
	}
	
	var scroll_timeout;
	
	function on_after_scroll(item) {
		if (!item.lookup_field && item.view_form.length) {
			clearTimeout(scroll_timeout);
			scroll_timeout = setTimeout(
				function() {
					if (item.rec_count) {
						item.invoice_table.set_where({track: item.id.value});
						item.invoice_table.set_order_by(['-invoice_date']);
						item.invoice_table.open(true);
					}
					else {
						item.invoice_table.close();
					}
				},
				100
			);
		}
	}
	
	function show_invoice(invoice_table) {
		var invoices = task.invoices.copy();
		invoices.set_where({id: invoice_table.master_rec_id.value});
		invoices.open(function(i) {
			i.edit_options.modeless = false;
			i.can_modify = false;
			i.invoice_table.on_after_open = function(t) {
				t.locate('id', invoice_table.id.value);
			};
			i.edit_record();
		});
	}
	
	function set_media_type(item) {
		var copy = item.copy({handlers: false}),
			selections = item.selections;
		if (selections.length > 1000) {
			item.alert('Too many records selected.');
		}
		else if (selections.length || item.rec_count) {		
			if (selections.length === 0) {
				selections = [item.id.value];
			}
			
			copy.set_fields(['media_type']);
			copy.open({open_empty: true});
			
			copy.edit_options.title = 'Set media type to ' + selections.length + ' record(s)';
			copy.edit_options.history_button = false;
			copy.media_type.required = true;
			
			copy.on_edit_form_created = function(c) {
				c.edit_form.find('#ok-btn').off('click.task').on('click', function() {
					try {
						c.post();
						item.server('set_media_type', [c.media_type.value, selections], function(res, error) {
							if (error) {
								item.alert_error(error);
							}
							if (res) {
								item.selections = [];
								item.refresh_page(true);
								c.cancel_edit();
								item.alert(selections.length + ' record(s) have been modified.');
							}
						});
					}
					finally {
						c.edit();
					}
				});
			};
			copy.append_record();
		}
	}
	
	function check_field_value(field) {
		if (field.field_name === 'album' && !field.value) {
			return 'Album must be specified';
		}
		if (field.field_name === 'unitprice' && field.value <= 0) {
			return 'Unit price must be greater that 0';
		}
	}
	
	function on_before_post(item) {
		item.each_field( function(field) {
			var err = check_field_value(field);
			if (err) {
				item.edit_form.find('input.' + field.field_name).focus();
				throw err;
			}
		});
	}
	
	function on_field_validate(field) {
		 if (field.field_name === 'unitprice' && field.value <= 0) {
			return 'Unit price must be greater that 0';
		}
	}
	this.on_view_form_created = on_view_form_created;
	this.on_after_scroll = on_after_scroll;
	this.show_invoice = show_invoice;
	this.set_media_type = set_media_type;
	this.check_field_value = check_field_value;
	this.on_before_post = on_before_post;
	this.on_field_validate = on_field_validate;
}

task.events.events15 = new Events15();

function Events16() { // demo.journals.invoices 

	function on_field_get_text(field) {
		if (field.field_name === 'customer' && field.value) {
			return field.owner.firstname.lookup_text + ' ' + field.lookup_text;
		}
	}
	
	function on_field_get_html(field) {
		if (field.field_name === 'total') {
			if (field.value > 10) {
				return '<strong>' + field.display_text + '</strong>';
			}
		}
	}
	
	function on_field_changed(field, lookup_item) {
		var item = field.owner,
			rec;
		if (field.field_name === 'taxrate') {
			rec = item.invoice_table.rec_no;
			item.invoice_table.disable_controls();
			try {
				item.invoice_table.each(function(t) {
					t.edit();
					t.calc(t);
					t.post();
				});
			}
			finally {
				item.invoice_table.rec_no = rec;
				item.invoice_table.enable_controls();
			}
		}
	}
	
	function on_detail_changed(item, detail) {
		var fields = [
			{"total": "total"}, 
			{"tax": "tax"}, 
			{"subtotal": "amount"}
		];  
		item.calc_summary(detail, fields);
	}
	
	function on_before_post(item) {
		var rec = item.invoice_table.rec_no;
		item.invoice_table.disable_controls();
		try {
			item.invoice_table.each(function(t) {
				t.edit();
				t.customer.value = item.customer.value;
				t.post();
			});	
		}
		finally {
			item.invoice_table.rec_no = rec;
			item.invoice_table.enable_controls();
		}
	}
	this.on_field_get_text = on_field_get_text;
	this.on_field_get_html = on_field_get_html;
	this.on_field_changed = on_field_changed;
	this.on_detail_changed = on_detail_changed;
	this.on_before_post = on_before_post;
}

task.events.events16 = new Events16();

function Events18() { // demo.journals.invoices.invoice_table 

	function calc(item) {
		item.amount.value = item.round(item.quantity.value * item.unitprice.value, 2);
		item.tax.value = item.round(item.amount.value * item.owner.taxrate.value / 100, 2);
		item.total.value = item.amount.value + item.tax.value;
	}
	
	function on_field_changed(field, lookup_item) {
		var item = field.owner;
		if (field.field_name === 'track' && lookup_item) {
			item.unitprice.value = lookup_item.unitprice.value;
		}
		else if (field.field_name === 'quantity' || field.field_name === 'unitprice') {
			calc(item);
		}
	}
	
	function on_view_form_created(item) {
		var btn = item.add_view_button('Select', {type: 'primary', btn_id: 'select-btn'});
		btn.click(function() {
			item.alert('Select the records to add to the invoice and close the from');
			item.select_records('track');
		});
	}
	
	function on_after_append(item) {
		item.invoice_date.value = new Date();
	}
	this.calc = calc;
	this.on_field_changed = on_field_changed;
	this.on_view_form_created = on_view_form_created;
	this.on_after_append = on_after_append;
}

task.events.events18 = new Events18();

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

function Events24() { // demo.analytics.dashboard 

	function on_view_form_created(item) {
		show_cusomers(item, item.view_form.find('#cutomers-canvas').get(0).getContext('2d'));
		show_tracks(item, item.view_form.find('#tracks-canvas').get(0).getContext('2d'));
	}
	
	function show_cusomers(item, ctx) {
		var inv = item.task.invoices.copy({handlers: false});
		inv.open(
			{
				fields: ['customer', 'total'], 
				funcs: {total: 'sum'},
				group_by: ['customer'],
				order_by: ['-total'],
				limit: 10
			}, 
			function() {
				var labels = [],
					data = [],
					colors = [];
				inv.each(function(i) {
					labels.push(i.customer.display_text);
					data.push(i.total.value.toFixed(2));
					colors.push(lighten('#006bb3', (i.rec_no - 1) / 10));
				});
				inv.first();
				draw_chart(item, ctx, labels, data, colors, 'Ten most active customers');
				inv.create_table(item.view_form.find('#customer-table'), 
					{row_count: 10, dblclick_edit: false});						
			}
		);
		return inv;
	}
	
	function show_tracks(item, ctx) {
		var tracks = item.task.tracks.copy({handlers: false});
		tracks.open(
			{
				fields: ['name', 'tracks_sold'], 
				order_by: ['-tracks_sold'],
				limit: 10
			}, 
			
			function() {
				var labels = [],
					data = [],
					colors = [];
				tracks.each(function(t) {
					labels.push(t.name.display_text);
					data.push(t.tracks_sold.value);
					colors.push(lighten('#196619', (t.rec_no - 1) / 10));
				});
				tracks.first();
				tracks.name.field_caption = 'Track';
				draw_chart(item, ctx, labels, data, colors, 'Ten most popular tracks');
				tracks.create_table(item.view_form.find('#tracks-table'), 
					{row_count: 10, dblclick_edit: false});
			}
		);
		return tracks;
	}
	
	function draw_chart(item, ctx, labels, data, colors, title) {
		new Chart(ctx,{
			type: 'pie',
			data: {
				labels: labels,
				datasets: [
					{
						data: data,
						backgroundColor: colors
					}
				]					
			},
			options: {
				 title: {
					display: true,
					fontsize: 14,
					text: title
				},
				legend: {
					position: 'bottom',
				},
			}
		});
	}
	
	function lighten(color, luminosity) {
		color = color.replace(/[^0-9a-f]/gi, '');
		if (color.length < 6) {
			color = color[0]+ color[0]+ color[1]+ color[1]+ color[2]+ color[2];
		}
		luminosity = luminosity || 0;
		var newColor = "#", c, i, black = 0, white = 255;
		for (i = 0; i < 3; i++) {
			c = parseInt(color.substr(i*2,2), 16);
			c = Math.round(Math.min(Math.max(black, c + (luminosity * white)), white)).toString(16);
			newColor += ("00"+c).substr(c.length);
		}
		return newColor; 
	}
	this.on_view_form_created = on_view_form_created;
	this.show_cusomers = show_cusomers;
	this.show_tracks = show_tracks;
	this.draw_chart = draw_chart;
	this.lighten = lighten;
}

task.events.events24 = new Events24();

function Events25() { // demo.catalogs.mail 

	function on_edit_form_created(item) {
		var title = 'Email to ';
		if (task.customers.selections && task.customers.selections.length)
			title += task.customers.selections.length + ' selected customers';
		else {
			title += task.customers.firstname.value + ' ' +
				task.customers.lastname.value;
		}
		item.edit_options.title = title;
		item.edit_form.find('#ok-btn')
			.text('Send email')
			.off('click.task')
			.on('click', function() {
				send_email(item);
			});
		item.edit_form.find('textarea.mess').height(120);
	}
	
	function send_email(item) {
		var selected = task.customers.selections;
		item.post();
		if (!selected.length) {
			selected.add(task.customers.id.value);
		}
		
		item.server('send_email', [selected, item.subject.value, item.mess.value], 
			function(result, err) {
				if (err) {
					item.alert_error('Failed to send the mail: ' + err);
					item.edit();
				}
				else {
					item.alert('Successfully sent the mail');
					item.close_edit_form();
					item.delete();			
				}
			}
		);
	}
	this.on_edit_form_created = on_edit_form_created;
	this.send_email = send_email;
}

task.events.events25 = new Events25();

})(jQuery, task)