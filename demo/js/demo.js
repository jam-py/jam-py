(function($, task) {
"use strict";

function Events1() { // demo 

	function on_page_loaded(task) { 
		
		$("title").text(task.item_caption);
		$("#app-title").text(task.item_caption); 
	
		if (task.small_font) {
			$('html').css('font-size', '14px');
		}
		if (task.full_width) {
			$('#container').removeClass('container').addClass('container-fluid');
		}
		  
		if (task.safe_mode) {
			$("#user-info").text(task.user_info.role_name + ' ' + task.user_info.user_name);
			$('#log-out')
			.show() 
			.click(function(e) {
				e.preventDefault();
				task.logout();
			}); 
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
		
		if (item.view_form.hasClass('modal-form')) {
			item.view_options.width = 1060;
			item.table_options.height = $(window).height() - 300;
		}
		else {
			if (!item.table_options.height) {
				item.table_options.height = $(window).height() - $('body').height();
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
		
		translate_btns(item.view_form.find('.form-footer'));
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
	
		translate_btns(item.edit_form.find('.form-footer'));
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
			result = false;
			if (item.is_modified()) {
				item.yes_no_cancel(task.language.save_changes,
					function() {
						item.apply_record();
					},
					function() {
						item.cancel_edit();
					}
				);
			}
			else {
				item.cancel_edit();
			}
		}
		return result;
	}
	
	function on_filter_form_created(item) {
		item.filter_options.title = item.item_caption + ' - filters';
		item.filter_form.find("#cancel-btn").on('click.task', function() {
			item.close_filter_form();
		});
		item.filter_form.find("#ok-btn").on('click.task', function() {
			item.set_order_by(item.view_options.default_order);
			item.apply_filters(item._search_params);
		});
		if (!item.master && item.owner.on_filter_form_created) {
			item.owner.on_filter_form_created(item);
		}
		if (item.on_filter_form_created) {
			item.on_filter_form_created(item);
		}
		item.create_filter_inputs(item.filter_form.find(".edit-body"));	
		translate_btns(item.filter_form.find('.form-footer'));	
		return true;
	}
	
	function on_param_form_created(item) {
		item.param_form.find("#cancel-btn").on('click.task', function() { 
			item.close_param_form();
		});
		item.param_form.find("#ok-btn").on('click.task', function() { 
			item.process_report();
		});
		if (item.owner.on_param_form_created) {
			item.owner.on_param_form_created(item);
		}
		if (item.on_param_form_created) {
			item.on_param_form_created(item);
		}
		item.create_param_inputs(item.param_form.find(".edit-body"));	
		translate_btns(item.filter_form.find('.form-footer'));
		return true;
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
					$li = $('<li><a class="dropdown-item" href="#">' + reports[i].item_caption + '</a></li>');
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
	
	function translate_btns(container) {
		container.find('.btn').each(function() {
			let btn = $(this).clone();
			btn.find('i', 'small').remove()
			let text = btn.text().trim();
			text = text.split()[0].split('[')[0];
			text = text.trim();
			let translation = task.language[text.toLowerCase()];
			if (translation) {
				$(this).html($(this).html().replace(text, translation)) 
			}
		});
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
	this.translate_btns = translate_btns;
}

task.events.events1 = new Events1();

function Events10() { // demo.catalogs.customers 

	function on_view_form_created(item) {
		item.table_options.multiselect = false;
		if (!item.lookup_field) {	
			var print_btn = item.add_view_button('Print', {image: 'bi bi-printer'}),
				email_btn = item.add_view_button('Send email', {image: 'bi bi-envelope-paper'});
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
			item.table_options.multiselect = true;
			item.add_view_button('Set media type').click(function() {
				set_media_type(item);
			});   
		}
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
	this.on_view_form_created = on_view_form_created;
	this.set_media_type = set_media_type;
}

task.events.events15 = new Events15();

function Events16() { // demo.journals.invoices 

	function on_view_form_created(item) {
		item.invoice_table.master_applies = false;
		set_paid_btn(item);
	}
	
	function set_paid_btn(item) {
		let btn = item.add_view_button('Set paid', {type: 'primary', btn_id: 'paid-btn'});
		btn.click(function() {
			item.question('Was the invoice paid?', function () {
				item.paid.value = true;
				item.apply(true);
			});
		});
	}
	
	function on_edit_form_created(item) {
		item.read_only = item.paid.value;
		item.edit_form.find('.form-footer').remove();
	}
	
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
		let item = field.owner;
		if (field.field_name === 'taxrate') {
			item.apply(function(res) {
				item.refresh_record();
			});
		}
	}
	
	var scroll_timeout;
	
	function on_after_scroll(item) {
		clearTimeout(scroll_timeout);
		scroll_timeout = setTimeout(
			function() {
				if (item.view_form && item.rec_count) {
					item.view_form.find("#delete-btn, #paid-btn").prop("disabled", item.paid.value);
				}
			}, 50
		);
	}
	this.on_view_form_created = on_view_form_created;
	this.set_paid_btn = set_paid_btn;
	this.on_edit_form_created = on_edit_form_created;
	this.on_field_get_text = on_field_get_text;
	this.on_field_get_html = on_field_get_html;
	this.on_field_changed = on_field_changed;
	this.on_after_scroll = on_after_scroll;
}

task.events.events16 = new Events16();

function Events17() { // demo.details.invoice_table 

	function on_view_form_created(item) {
		if (item.master) {
			item.view_form.find('#new-btn').off('click.task').on('click', function() {
				item.select_records('track');
			});
			item.view_form.find("#delete-btn, #new-btn").prop("disabled", item.owner.paid.value);		
		}
	}		
	
	function calc_track(item) {
		item.amount.value = item.quantity.value * item.unitprice.value;
		item.tax.value = item.amount.value * item.master.taxrate.value / 100;
		item.total.value = item.amount.value + item.tax.value;
		item.paid.value = item.master.paid.value;
	}
	
	function on_field_changed(field, lookup_item) {
		let item = field.owner;
		if (lookup_item) {
			item.unitprice.value = lookup_item.unitprice.value;
		}
		if (item.master.item_name == 'invoices_client') {
			calc_track(item);
		}
	}
	this.on_view_form_created = on_view_form_created;
	this.calc_track = calc_track;
	this.on_field_changed = on_field_changed;
}

task.events.events17 = new Events17();

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

function Events57() { // demo.journals.invoices_client 

	function on_field_get_text(field) {
		task.invoices.on_field_get_text(field);
	}
	
	function on_field_get_html(field) {
		task.invoices.on_field_get_html(field);
	}
	
	function on_after_scroll(item) {
		task.invoices.on_after_scroll(item);
	}
	
	function on_view_form_created(item) {
		item.invoice_table.master_applies = true;
		task.invoices.set_paid_btn(item);	
	}
	
	function on_edit_form_created(item) {
		item.read_only = item.paid.value;
	}
	
	function on_field_changed(field, lookup_item) {
		let item = field.owner;
		if (field.field_name === 'taxrate') {
			let rec = item.invoice_table.rec_no;
			item.invoice_table.disable_controls();
			try {
				item.invoice_table.each(function(t) {
					t.calc_track(t);
				});
			}
			finally {
				item.invoice_table.rec_no = rec;
				item.invoice_table.enable_controls();
			}
		}		
		calc_invoice(item);
	}
	
	function calc_invoice(item) {
		let clone = item.invoice_table.clone(),
			subtotal = 0,
			tax = 0,
			total = 0;
		clone.each(function(c) {
			subtotal += c.amount.value;
			tax += c.tax.value;
			total += c.total.value;
		});
		item.subtotal.value = subtotal;
		item.tax.value = tax;
		item.total.value = total;
	}
	
	function on_detail_changed(item, detail) {
		calc_invoice(item);
	}
	this.on_field_get_text = on_field_get_text;
	this.on_field_get_html = on_field_get_html;
	this.on_after_scroll = on_after_scroll;
	this.on_view_form_created = on_view_form_created;
	this.on_edit_form_created = on_edit_form_created;
	this.on_field_changed = on_field_changed;
	this.calc_invoice = calc_invoice;
	this.on_detail_changed = on_detail_changed;
}

task.events.events57 = new Events57();

})(jQuery, task)