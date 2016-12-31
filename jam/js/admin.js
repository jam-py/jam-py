(function($, task) {
"use strict";

function Events0() { // admin 

	var item_types = {
		"ROOT_TYPE": 1,
		"USERS_TYPE": 2,
		"ROLES_TYPE": 3,
		"TASKS_TYPE": 4,
		"TASK_TYPE": 5,
		"ITEMS_TYPE": 6,
		"JOURNALS_TYPE": 7,
		"TABLES_TYPE": 8,
		"REPORTS_TYPE": 9,
		"ITEM_TYPE": 10,
		"JOURNAL_TYPE": 11,
		"TABLE_TYPE": 12,
		"REPORT_TYPE": 13,
		"DETAIL_TYPE": 14
		},
		db_types = {
			"SQLITE": 1,
			"FIREBIRD": 2,
			"POSTGRESQL": 3,
			"MYSQL": 4
		}
	
	function tree_changed(item) {
		var div;
		task.btns_panel.show();
		item.task.cur_item_title = item.f_name.value;
		if (item.type_id.value === item_types.ROOT_TYPE) {
			task.view_panel.empty();
			task.view_panel.append('<div class="admin-task-info"></div>')
			update_task_info(task);
			task.right_panel.show();
			task.btns_panel.empty();
			create_params_btn(item.task);
		}
		else if (item.type_id.value === item_types.USERS_TYPE) {
			task.right_panel.hide();
			item.task.sys_users.view_options.fields = ['f_name', 'f_login', 'f_password', 'f_role', 'f_admin'];
			item.task.sys_users.view(task.view_panel);
		}
		else if (item.type_id.value === item_types.ROLES_TYPE) {
			task.right_panel.hide();
			item.task.sys_roles.view(task.view_panel);
		}
		else {
			task.right_panel.show();
			item.task.sys_items.tree_changed(item.task.sys_items);
		}
	}
	
	function refresh_tree(task, item_id) {
		task.server('server_update_has_children', []);
		task.item_tree.set_where({has_children: true});
		task.item_tree.open({fields: ['id', 'parent', 'f_name', 'type_id', 'task_id']});
		task.item_tree.locate('type_id', item_types.TASK_TYPE);
		task.tree.expand(task.tree.selected_node);
		task.item_tree.on_after_scroll = tree_changed;
		if (item_id) {
			task.item_tree.locate('id', item_id);
		}
		else {
			task.item_tree.locate('type_id', item_types.ROOT_TYPE);
		}
		task.tree_panel.show();
		tree_changed(task.item_tree);
	}
	
	function open_sys_params(task) {
		var fields = task.sys_params.view_options.fields;
		fields.splice(fields.indexOf('f_field_id_gen'), 1);
		fields.push('id');
		task.sys_params.open({fields: fields});
	}
	
	function on_page_loaded(task)  {
		var items,
			fields;
	
		task._manual_update = false;
		task.init_project = true;
		task.item_types = item_types;
		task.db_types = db_types;
	
		open_sys_params(task)
		if (!task.sys_params.f_language.value) {
			task.sys_params.set_edit_fields(['f_language']);
			task.sys_params.edit_options.title = 'Project language';
			task.sys_params.edit_record();
			return
		}
	
		task.sys_tasks.open();
		if (!task.sys_tasks.f_db_type.value) {
			fields = ['f_name', 'f_item_name', 'f_db_type', 'f_alias', 'f_login',
				'f_password', 'f_host', 'f_port', 'f_encoding']
			task.sys_tasks.set_edit_fields(fields);
			task.sys_tasks.edit_options.title = task.language.project_params;
			task.sys_tasks.edit_record();
			return
		}
	
		if (task.sys_params.f_language.value && task.sys_tasks.f_db_type.value) {
			task.init_project = false;
			task.server('server_get_db_options', [task.sys_tasks.f_db_type.value], function(result) {
				task.db_options = result;
			});
	
			task.buttons_info = {
				divider: {},
				project_params:	{handler: set_project_params, short_cut: 'F2', key_code: 113, editor: true},
				project_locale:	{handler: set_locale_params, short_cut: 'F3', key_code: 114, editor: true},
				db:				{handler: edit_database, short_cut: 'F4', key_code: 115, editor: true},
				'export':		  {handler: export_task, short_cut: 'Ctrl-E', key_code: 69, key_ctrl: true},
				'import':		  {handler: import_task, short_cut: 'Ctrl-I', key_code: 73, key_ctrl: true},
				find:			  {handler: find_in_task, short_cut: 'Alt-F', key_code: 70, key_alt: true},
				print:			 {handler: print_code, short_cut: 'Shift-P', key_code: 80, key_shift: true},
				client_module:	 {handler: task.sys_items.edit_client, item: task.sys_items, short_cut: 'F8', key_code: 119, editor: true},
				server_module:	 {handler: task.sys_items.edit_server, item: task.sys_items, short_cut: 'F9', key_code: 120, editor: true},
				'index.html':	  {handler: task.sys_items.edit_index_html, item: task.sys_items, short_cut: 'F10', key_code: 121, editor: true},
				'project.css':	 {handler: task.sys_items.edit_project_css, item: task.sys_items, short_cut: 'F11', key_code: 122, editor: true},
				'Lookup lists':	{handler: show_lookup_lists, editor: true},
				viewing:		   {handler: task.sys_items.view_setup, item: task.sys_items, editor: true},
				editing:		   {handler: task.sys_items.edit_setup, item: task.sys_items, editor: true},
				filters:		   {handler: task.sys_items.filters_setup, item: task.sys_items, editor: true},
				details:		   {handler: task.sys_items.details_setup, item: task.sys_items, editor: true},
				order:			 {handler: task.sys_items.order_setup, item: task.sys_items, editor: true},
				indices:		   {handler: task.sys_items.indices_setup, item: task.sys_items, editor: true},
				foreign_keys:	  {handler: task.sys_items.foreign_keys_setup, item: task.sys_items, editor: true},
				reports:		   {handler: task.sys_items.reports_setup, item: task.sys_items, editor: true},
				report_params:	 {handler: task.sys_items.report_params_setup, item: task.sys_items, editor: true, short_cut: 'F7', key_code: 118, editor: true},
				privileges:		{handler: task.sys_items.privileges_setup, item: task.sys_items, editor: true}
			};
	
			$("#title").html(task.language.admin);
			if (task.safe_mode) {
				$("#user-info").text(task.user_info.role_name + ' ' + task.user_info.user_name);
				$('#log-out').show().click(function(e) {
					e.preventDefault();
					task.logout();
				})
			}
	
			task.left_panel = $("#left-panel");
			task.center_panel = $("#center-panel");
			task.right_panel = $("#right-panel");
			task.btns_panel = $("#btns-panel");
			task.view_panel = $("#view-panel");
			task.tree_panel = $("#tree-panel");
	
			task.item_tree = task.sys_items.copy({handlers: false, details: false});
			task.tree = task.item_tree.create_tree(task.tree_panel,
				{
					id_field: 'id',
					parent_field: 'parent',
					text_field: 'f_name',
					parent_of_root_value: 0
				}
			);
			task.tree.$element.height($("#left-panel").height());
			refresh_tree(task);
			update_db_manual_mode(task);
	
			$(window).on('focus.task', function(e) {
				update_task_info(task);
			});
			$(window).on('resize.task', function() {
				resize(task);
			});
			$(window).on('keydown.task', function(e) {
				if (e.which === 116) {
					task.editing_finished();
				}
	//			if (e.which === 118) {
	//				task.sys_lang.view()
	//			}
			});
	
			window.onbeforeunload = function(event) {
				task.editing_finished();
				window.onbeforeunload = undefined;
			};
	
			resize(task);
		}
	}
	
	function add_button(task, caption, handler, item, icon, short_cut, key_code, key_ctrl, key_shift, key_alt, editor) {
	
		function clicked(e) {
			var doc,
				cur_doc,
				it,
				item_id;
			e.preventDefault();
			e.stopImmediatePropagation();
			e.stopPropagation();
			if (item) {
				it = item,
				item_id = item.id.value;
			}
			else {
				it = task;
				item_id = 0;
			}
			if (editor) {
				doc = [it.ID, item_id, caption, task.user_info];
				cur_doc = task.server('check_doc_edited', doc)
				if (cur_doc) {
					task.question(task.doc_editing_message(cur_doc), function() {
						task.edited_doc = doc
						handler.call(it, it, task.language[caption]);
						task.server('set_edited', doc);
					});
				}
				else {
					task.edited_doc = doc
					handler.call(it, it, task.language[caption]);
					task.server('set_edited', doc);
				}
			}
			else {
				handler.call(it, it, task.language[caption]);
			}
		}
	
		var caption_html = '',
			icon_html = '',
			short_cut_html = '',
			btn;
		if (caption) {
			caption_html = task.language[caption];
			if (!caption_html) {
				caption_html = caption;
			}
		}
		if (icon) {
			icon_html = '<i class="' + icon + '"></i>';
		}
		if (short_cut) {
			short_cut_html = '<small class="muted">&nbsp;[' + short_cut + ']</small>'
		}
		btn = $('<button class="btn vert-btn text-center ' + caption + '" type="button">' + icon_html + ' ' + caption_html + short_cut_html + '</button>');
		task.btns_panel.append(btn);
		if (handler) {
			btn.click(function(e) {
				clicked(e);
			})
		}
		if (key_code) {
			$(window).off('keydown.' + caption);
			$(window).on('keydown.' + caption, (function(e) {
				var code = (e.keyCode ? e.keyCode : e.which);
				if (key_ctrl && e.ctrlKey && key_code === e.keyCode ||
					key_shift && e.shiftKey && key_code === e.keyCode ||
					key_alt && e.altKey && key_code === e.keyCode ||
					!key_ctrl && !key_shift && !key_alt && key_code === e.keyCode) {
					e.preventDefault();
					clicked(e);
				}
			}));
		}
	}
	
	function add_divider() {
		task.btns_panel.append('<div class="btns-divider">');
	}
	
	function add_buttons(task, buttons) {
		var i = 0,
			len = buttons.length,
			button_id,
			button;
		for (; i < len; i++) {
			button_id = buttons[i]
			if (button_id === 'divider') {
				add_divider();
			}
			else {
				button = task.buttons_info[button_id];
				add_button(task, button_id, button.handler, button.item, button.icon, button.short_cut,
					button.key_code, button.key_ctrl, button.key_shift, button.key_alt, button.editor);
			}
		}
	}
	
	function create_params_btn(task) {
		add_buttons(task,
			[
				'project_params',
				'project_locale',
				'divider',
				'db',
				'divider',
				'export',
				'import',
				'divider',
				'find',
				'print'
			]);
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
						$(this).data('report').print();
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
	
	function update_task_info(task) {
		if (task._importing) {
			return;
		}
		if (task.cur_task_info) {
			$('.admin-task-info').html(task.cur_task_info)
		}
		task.server('server_get_task_info', function(res) {
			var task_caption = res[1],
				task_version = res[2],
				task_db = res[3];
			task.task_name = res[0];
			if (task.server_started && task.server_started !== res[4]) {
				if (task.edited_doc) {
					if (task.server('check_doc_edited', task.edited_doc)) {
						location.reload();
					}
					else {
						task.server('set_edited', task.edited_doc);
					}
				}
			}
			task.server_started = res[4];
			task.cur_task_info = '<h4><span class="editor-title">' +
					task_caption + '</span> <span class="muted">' + task_db + '</span> v. ' + task_version + '</h4>';
			$('.admin-task-info').html(task.cur_task_info);
		});
	}
	
	function read_task_name(task) {
		var items = task.sys_items.copy();
		items.set_where({type_id: item_types.TASK_TYPE});
		items.open({fields: ['f_item_name', 'f_name']});
		task.task_name = items.f_item_name.value;
		task.task_caption = items.f_name.value;
	}
	
	function on_view_form_created(item) {
		var task = item.task,
			column_width,
			table_height,
			options;
	
		if (item.item_name === 'sys_fields_editor' || item.item_name === 'sys_code_editor' ||
			item.item_name === 'sys_lang') {
			return
		}
		item.paginate = false;
		if (item.view_form.hasClass('modal')) {
			item.view_form.find("#select-btn").on('click.task', function() {item.set_lookup_field_value();});
			item.view_options.width = 960;
			table_height = 480;
			if (item.item_name === 'sys_items' || item.item_name === 'sys_fields') {
				item.view_options.width = 560;
				item.view_form.find('.modal-footer').hide();
				column_width = {id: '10%'};
			}
			else if (item.item_name === 'sys_filters' || item.item_name === 'sys_indices') {
				item.view_options.width = 680;
				table_height = 460;
			}
			else if (item.item_name === 'sys_report_params') {
				item.view_options.width = 900;
				table_height = 560;
			}
		}
		else {
			task.cur_item = item;
			item.view_form.find(".modal-body").css('padding', 0);
			item.view_form.find("#title-left").html('<h4>' + '<span class="editor-title">' + task.cur_item_title + '</span>' + '</h4>');
			item.view_form.find("#select-btn").hide()
			table_height = task.center_panel.height() - task.view_panel.height();
			item.view_form.find("#title-right").addClass('admin-task-info');
			update_task_info(task);
		}
	
		if (item.item_name === 'sys_items') {
			column_width = {id: '5%', f_visible: '10%', f_soft_delete: '10%'};
		}
		if (item.item_name !== "sys_roles") {
			item.view_form.find("#new-btn")
				.text(item.task.language['new'])
				.on('click.task', function() {item.append_record();});
			item.view_form.find("#edit-btn")
				.text(item.task.language.edit)
				.on('click.task', function() {item.edit_record();});
			item.view_form.find("#delete-btn")
				.text(item.task.language['delete'])
				.on('click.task', function() {item.delete_record();});
			options =
				{
					height: table_height,
					word_wrap: false,
					column_width: column_width
				};
	
			if (item.init_view_table) {
				item.init_view_table(item, options);
			}
			item.view_table = item.create_table(item.view_form.find(".view-table"), options);
		}
		create_print_btns(item);
	}
	
	function expand_buttons(form) {
		form.find(".modal-footer button.btn").each(function() {
			if ($(this).outerWidth() < 100 && $(this).text()) {
				$(this).outerWidth(100);
			}
		});
	}
	
	function on_view_form_shown(item) {
		expand_buttons(item.view_form);
		if (item.item_name === 'sys_fields_editor' || item.item_name === 'sys_code_editor') {
			return
		}
		if (item ===item.task.sys_privileges) {
			item.open({params: {item_id: item.task.sys_items.id.value}});
		}
		else if (item.item_name === 'sys_items') {
			item.open({fields: [
				'id', 'deleted', 'parent', 'task_id', 'type_id', 'table_id', 'has_children', 'f_index',
				'f_name', 'f_item_name', 'f_table_name', 'f_view_template', 'f_visible', 'f_soft_delete',
				'f_virtual_table', 'f_js_external',
				'f_primary_key', 'f_deleted_flag', 'f_master_id', 'f_master_rec_id'
			]});
		}
		else {
			item.open();
		}
	}
	
	function on_edit_form_created(item) {
		var options = {};
		if (item.item_name !== 'sys_items' && item.item_name !== 'sys_fields' && item.item_name !== 'sys_code_editor') {
			item.edit_options.width = 560;
			if (item.init_edit_options) {
				item.init_edit_options(item, options);
			}
			item.create_inputs(item.edit_form.find(".edit-body"), options);
			item.edit_form.find("#cancel-btn")
				.text(item.task.language.cancel)
				.attr("tabindex", 101)
				.on('click.task', function(e) {item.cancel_edit(e); return false;});
			item.edit_form.find("#ok-btn")
				.attr("tabindex", 100)
				.text(item.task.language.ok)
				.on('click.task', function() {item.apply_record()});
		}
	}
	
	function on_edit_form_shown(item) {
		expand_buttons(item.edit_form);
		if (item.details_active) {
			item.each_detail(function(d) {
				d.update_controls();
			});
		}
		else {
			item.open_details();
		}
		resize_edit_table(item);
	}
	
	function on_edit_form_close_query(item) {
		var result;
		if (item.item_name !== 'sys_search') {
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
					result = true;
				}
			}
		}
		if (result !== false && item.edited_doc_info && item.edited_doc_info.edit_form) {
			item.task.editing_finished(item);
		}
		return result;
	}
	
	function on_filter_form_created(item) {
		item.filter_form.title = item.item_caption + ' - filter';
		item.create_filter_inputs(item.filter_form.find(".edit-body"));
		item.filter_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function() {item.close_filter()});
		item.filter_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.apply_filter()});
	}
	
	function on_param_form_created(item) {
		item.create_param_inputs(item.param_form.find(".edit-body"));
		item.param_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function() {item.close_param_form()});
		item.param_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.process_report()});
	}
	
	function set_project_params(task, caption) {
		open_sys_params(task);
		task.sys_params.params = true;
		task.sys_params.edit_options.fields = ['f_safe_mode', 'f_debugging', 'f_con_pool_size',
			'f_mp_pool', 'f_persist_con', 'f_compressed_js', 'f_single_file_js', 'f_dynamic_js', 'f_version'];
		task.sys_params.edit_options.title = caption;
		task.sys_params.edit_record();
	}
	
	function set_locale_params(task, caption) {
		open_sys_params(task);
		task.sys_params.params = false;
		task.sys_params.edit_options.fields = ['f_decimal_point', 'f_mon_decimal_point', 'f_mon_thousands_sep',
			'f_currency_symbol', 'f_frac_digits', 'f_p_cs_precedes', 'f_n_cs_precedes', 'f_p_sep_by_space',
			'f_n_sep_by_space', 'f_positive_sign', 'f_negative_sign',
			'f_p_sign_posn', 'f_n_sign_posn', 'f_d_fmt', 'f_d_t_fmt'];
		task.sys_params.edit_options.title = caption;
		task.sys_params.edit_options.width = 900;
		task.sys_params.edit_record();
	}
	
	function edit_database(task, caption) {
		var fields = ['f_manual_update', 'f_db_type', 'f_alias', 'f_login', 'f_password',
			'f_host', 'f_port', 'f_encoding']
		task.sys_tasks.open()
		task.sys_tasks.on_field_changed(task.sys_tasks.f_db_type);
		task.sys_tasks.edit_options.fields = fields;
		task.sys_tasks.f_name.required = false;
		task.sys_tasks.f_item_name.required = false;
		task.sys_tasks.edit_options.title = caption;
		task.sys_tasks.edit_record();
	}
	
	function show_lookup_lists(task) {
		task.sys_lookup_lists.view_options.fields = ['f_name'];
		task.sys_lookup_lists.edit_options.fields = ['f_name'];
		task.sys_lookup_lists.view();
	}
	
	function find_in_task(task) {
		task.sys_search.find_in_task(task);
	}
	
	function print_section(list, html) {
		var i,
			j,
			k,
			text,
			spaces = 0,
			lines,
			$p;
		for (i = 0; i < list.length; i++) {
			html.append($('<h4>' + list[i][0] + '</h4>'));
			lines = list[i][1].split('\n')
			for (j = 0; j < lines.length; j++) {
				text = lines[j];
				spaces = 0;
				for (k = 0; k < text.length; k++) {
					if (text[k] === ' ') {
						spaces += 1;
					}
					else if (text[k] === '\t ') {
						spaces += 4;
					}
					else {
						break;
					}
				}
				text = text.trim();
				if (text.length === 0) {
					$p = $('<p style="line-height: 16px; margin: 0px;">').html('&nbsp;')
				}
				else {
					$p = $('<p style="line-height: 16px; margin-top: 0px; margin-right: 0px; margin-bottom: 0px; margin-left: ' + spaces * 6 + 'px">').text(text)
				}
				$p.css("font-family", "'Courier New', Courier, monospace")
				html.append($p);
			}
		}
	}
	
	function print_code(task) {
		var width = $(window).width() - 50,
			height = $(window).height() - 200,
			html = $('<div>'),
			result = task.server('server_web_print_code', [task.sys_tasks.task_id.value]);
		if (result) {
			html.append($('<h2>' + result.task + '</h2>'));
			html.append($('<h3>Client</h3>'));
			print_section(result.client, html);
			html.append($('<h3>Server</h3>'));
			print_section(result.server, html);
			task.message(html,
				{title: 'Project code', margin: 10, width: width, height: height,
					text_center: false, buttons: {"Close": undefined}, center_buttons: false, print: true}
			)
		}
	}
	
	function do_import(task, file_name) {
		var mess;
	
		mess = task.show_message(
			$('<h5>Please wait while import is under way.</h5>'),
			{
				margin: "20px 20px",
				text_center: true,
			}
		);
		task._importing = true;
		task.server('server_import_task', [task.sys_tasks.task_id.value, 'static/internal/' + file_name, true], function(res) {
			var success = res[0],
				error = res[1],
				info = res[2],
				message,
				callback = function() {
						if (success) { location.reload()
					}},
				options = {text_center: false, width: 720, height: 400, title: 'Import result',
					close_button: false, print: true, margin: 0};
			task.hide_message(mess);
			if (success) {
				message = 'The metadata have been successfully imported';
				if (error) {
					message = 'The metadata have been imported with errors.';
				}
				message = '<h3 class="text-center">' + message + '</h3>'
			}
			else {
				message = '<h3 class="text-center text-error">The metadata have not been imported.</h3>'
			}
	//		if (error) {
	//			message += '<h4 class="text-error">Errors</h4><div>' + error + '</div>'
	//		}
			if (info) {
				message += '<h4 class="text-info">Import log</h4><div>' + info + '</div>'
			}
			task.warning(message, callback, options);
			task._importing = false;
		});
	}
	
	function import_task(task) {
		task.upload('static/internal', {multiple: false, callback: do_import});
	}
	
	function export_task(task) {
		var link,
			host = location.protocol + '/' +  '/' + location.hostname + (location.port ? ':' + location.port: ''),
			url = task.server('server_export_task', [task.sys_tasks.task_id.value, host]);
		window.open(url, "_self");
	}
	
	function move_vert(item, rec1, rec2) {
		var r1 = item._dataset[rec1],
			r2 = item._dataset[rec2],
			i,
			t;
		for (i = 0; i < r1.length - 1; i++) {
			t = r1[i];
			r1[i] = r2[i];
			r2[i] = t;
		}
		item.update_controls();
		item.rec_no = rec2;
	}
	
	function move_record_up(item) {
		if (item.rec_no > 0) {
			move_vert(item, item.rec_no, item.rec_no - 1);
		}
	}
	
	function move_record_down(item) {
		if (item.rec_no < item.record_count() - 1) {
			move_vert(item, item.rec_no, item.rec_no + 1);
		}
	}
	
	function resize_edit_table(item, window_resized) {
		var edit_form_height,
			window_height,
			newHeight;
		if (item.edit_form && item.edit_table) {
			edit_form_height = item.edit_form.height();
			window_height = $(window).height();
			if (window_resized || edit_form_height > window_height - 20) {
				newHeight = item.edit_table.height() - (edit_form_height - window_height) - 20;
				if (newHeight > 450) {
					newHeight = 450;
				}
				if (newHeight < 200) {
					newHeight = 200;
				}
				item.edit_table.height(newHeight);
				item.update_controls();
			}
		}
	}
	
	var timeOut;
	
	function resize(task) {
		clearTimeout(timeOut);
		timeOut = setTimeout(function() {
			var new_height = task.left_panel.height() + $(window).height() - $('body').height() - 40;
			task.left_panel.height(new_height);
			task.tree.height(new_height);
			task.btns_panel.height(new_height);
			if (task.cur_item) {
				task.cur_item.view_table.height(new_height - 74);
			}
			if (task.code_editor_item) {
				task.code_editor_item.resize(task.code_editor_item);
			}
		},
		100);
	}
	
	function update_db_manual_mode(task) {
		if (task._manual_update) {
			$("#project-mode").text('DB manual mode').css("color", "red");
		}
		else {
			$("#project-mode").text('')
		}
	}
	
	function on_view_form_keydown(item, event) {
		if (item.item_name === 'sys_users' ||
			item.item_name === 'sys_report_params' ||
			item.item_name === 'sys_filters') {
			if (event.keyCode === 45 && event.ctrlKey === true){
				event.preventDefault();
				item.append_record();
			}
			else if (event.keyCode === 46 && event.ctrlKey === true){
				event.preventDefault();
				item.delete_record();
			}
		}
	}
	
	function on_edit_form_keydown(item, event) {
		if (item.item_name === 'sys_users' ||
			item.item_name === 'sys_indices' ||
			item.item_name === 'sys_report_params' ||
			item.item_name === 'sys_filters') {
			if (event.keyCode === 13 && event.ctrlKey === true){
				event.preventDefault();
				item.edit_form.find("#ok-btn").focus();
				item.apply_record();
			}
		}
	}
	
	function editing_finished(item, callback) {
		if (this.edited_doc) {
			this.server('clear_edited', this.edited_doc, function() {
				this.edited_doc = undefined;
				$("title").html(task.language.admin);
				if (item && callback) {
					callback.call(item, item);
				}
			});
		}
	}
	
	function doc_editing_message(doc) {
		var task = this,
			doc_type = doc[2],
			user_name = '',
			doc_name = task.language[doc_type],
			mess;
		if (doc[3]) {
			user_name = doc[3].user_name;
		}
		if (!doc_name) {
			doc_name = doc_type;
		}
		if (user_name) {
			mess = task.language.is_edited_by;
			mess = mess.replace('%s', doc_name);
			mess = mess.replace('%s', user_name);
		}
		else {
			mess = task.language.is_edited;
			mess = mess.replace('%s', doc_name);
		}
		return mess;
	}
	this.tree_changed = tree_changed;
	this.refresh_tree = refresh_tree;
	this.open_sys_params = open_sys_params;
	this.on_page_loaded = on_page_loaded;
	this.add_button = add_button;
	this.add_divider = add_divider;
	this.add_buttons = add_buttons;
	this.create_params_btn = create_params_btn;
	this.create_print_btns = create_print_btns;
	this.update_task_info = update_task_info;
	this.read_task_name = read_task_name;
	this.on_view_form_created = on_view_form_created;
	this.expand_buttons = expand_buttons;
	this.on_view_form_shown = on_view_form_shown;
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_shown = on_edit_form_shown;
	this.on_edit_form_close_query = on_edit_form_close_query;
	this.on_filter_form_created = on_filter_form_created;
	this.on_param_form_created = on_param_form_created;
	this.set_project_params = set_project_params;
	this.set_locale_params = set_locale_params;
	this.edit_database = edit_database;
	this.show_lookup_lists = show_lookup_lists;
	this.find_in_task = find_in_task;
	this.print_section = print_section;
	this.print_code = print_code;
	this.do_import = do_import;
	this.import_task = import_task;
	this.export_task = export_task;
	this.move_vert = move_vert;
	this.move_record_up = move_record_up;
	this.move_record_down = move_record_down;
	this.resize_edit_table = resize_edit_table;
	this.resize = resize;
	this.update_db_manual_mode = update_db_manual_mode;
	this.on_view_form_keydown = on_view_form_keydown;
	this.on_edit_form_keydown = on_edit_form_keydown;
	this.editing_finished = editing_finished;
	this.doc_editing_message = doc_editing_message;
}

task.events.events0 = new Events0();

function Events3() { // admin.catalogs.sys_items 

	function init_fields(item) {
		var task = item.task;
		item.fields_editor = false;
		if (task.item_tree.type_id.value === task.item_types.TASKS_TYPE) {
			item.view_options.fields = ['id', 'f_name', 'f_item_name'];
			item.edit_options.fields = ['f_name', 'f_item_name'];
		}
		else if (task.item_tree.type_id.value === task.item_types.TASK_TYPE) {
			item.fields_editor = true;
			item.view_options.fields = ['id', 'f_name', 'f_item_name', 'f_visible'];
			item.edit_options.fields = ['f_name', 'f_item_name', 'f_visible'];
			item.sys_fields.view_options.fields = ['f_name', 'f_field_name',
				'f_data_type', 'f_size', 'f_required', 'f_read_only', 'f_object',
				'f_object_field', 'f_master_field', 'f_enable_typehead',
				'f_lookup_values', 'f_alignment', 'f_default'];
		}
		else if (task.item_tree.type_id.value === task.item_types.ITEMS_TYPE ||
			task.item_tree.type_id.value === task.item_types.TABLES_TYPE) {
			item.fields_editor = true;
			item.view_options.fields = ['id', 'f_name', 'f_item_name', 'f_table_name',
				'f_visible', 'f_soft_delete']
			item.edit_options.fields = ['f_name', 'f_item_name', 'f_table_name']
			item.sys_fields.view_options.fields = ['f_name', 'f_field_name',
				'f_data_type', 'f_size', 'f_required', 'f_read_only', 'f_object',
				'f_object_field', 'f_master_field', 'f_enable_typehead',
				'f_lookup_values', 'f_alignment', 'f_default'];
		}
		else if (task.item_tree.type_id.value === task.item_types.REPORTS_TYPE) {
			item.view_options.fields = ['id', 'f_name', 'f_item_name',
				'f_view_template', 'f_visible'];
			item.edit_options.fields = ['f_name', 'f_item_name',
				'f_view_template', 'f_visible', 'f_js_external'];
		}
		else if (task.item_tree.type_id.value === task.item_types.ITEM_TYPE ||
			task.item_tree.type_id.value === task.item_types.TABLE_TYPE) {
			item.view_options.fields = ['id', 'f_name', 'f_item_name', 'f_table_name'];
			item.edit_options.fields = ['f_name', 'f_item_name'];
		}
	}
	
	function init_buttons(item) {
		var task = item.task;
		task.btns_panel.empty();
		if (task.item_tree.type_id.value === task.item_types.TASKS_TYPE) {
			task.add_buttons(task, [
				'client_module',
				'server_module',
				'index.html',
				'project.css',
				'divider',
				'Lookup lists'
			]);
		}
		else if (task.item_tree.type_id.value === task.item_types.TASK_TYPE) {
			task.add_buttons(task, [
				'client_module',
				'server_module'
			]);
		}
		else if (task.item_tree.type_id.value === task.item_types.ITEMS_TYPE ||
			task.item_tree.type_id.value === task.item_types.TABLES_TYPE) {
			task.add_buttons(task, [
				'client_module',
				'server_module',
				'divider',
				'viewing',
				'editing',
				'filters',
				'divider',
				'details',
				'divider',
				'order',
				'indices',
				'foreign_keys',
				'divider',
				'reports',
				'divider',
				'privileges'
			]);
		}
		else if (task.item_tree.type_id.value === task.item_types.ITEM_TYPE ||
			task.item_tree.type_id.value === task.item_types.TABLE_TYPE) {
			task.add_buttons(task, [
				'client_module',
				'server_module',
				'divider',
				'viewing',
				'editing',
				'divider',
				'order'
			]);
		}
		else if (task.item_tree.type_id.value === task.item_types.REPORTS_TYPE) {
			task.add_buttons(task, [
				'client_module',
				'server_module',
				'divider',
				'report_params'
			]);
		}
	}
	
	function tree_changed(item) {
		var task = item.task,
			item_tree = item.task.item_tree,
			fields;
		item.filters.parent.value = item_tree.id.value;
		init_fields(item);
		item.view(task.view_panel);
		init_buttons(item);
	}
	
	function get_type_id(item) {
		var parent_type_id = item.task.item_tree.type_id.value,
			types = item.task.item_types,
			task = item.task;
		if (parent_type_id === types.TASKS_TYPE) {
			return types.TASK_TYPE;
		}
		else if (parent_type_id === types.TASK_TYPE) {
			return types.ITEMS_TYPE;
		}
		else if (parent_type_id === types.ITEMS_TYPE) {
			return types.ITEM_TYPE;
		}
		else if (parent_type_id === types.TABLES_TYPE) {
			return types.TABLE_TYPE;
		}
		else if (parent_type_id === types.REPORTS_TYPE) {
			return types.REPORT_TYPE;
		}
		else if (parent_type_id === types.ITEM_TYPE ||
			parent_type_id === types.TABLE_TYPE) {
			return types.DETAIL_TYPE;
		}
	}
	
	function save_order(item) {
		var i = 0,
			rec = item.rec_no;
		try {
			item.each(function(it) {
				it.edit();
				it.f_index.value = i;
				it.post();
				i++;
			})
			item.apply();
		}
		finally {
			item.rec_no = rec;
		}
	}
	
	function append_group(item) {
		var types = item.task.item_types;
		item.task.sys_new_group.on_edit_form_created = function(it) {
			it.edit_form.find("#ok-btn").off('click.task').on('click', function() {
				it.post_record();
			});
		}
		item.task.sys_new_group.on_after_post = function(it) {
			var group_type = it.group_type.value,
				group_type_ids = [types.ITEMS_TYPE, types.TABLES_TYPE, types.REPORTS_TYPE];
			if (group_type) {
				item.append()
				item.type_id.value = group_type_ids[group_type - 1];
			}
		setTimeout(
			function() {
					item.edit_record();
			},
			300
		);
		}
		item.task.sys_new_group.open({open_empty: true});
		item.task.sys_new_group.append_record();
	}
	
	function can_delete(item) {
		var error = '';
		if (item.id.value) {
			if (item.type_id.value === item.task.item_types.ITEMS_TYPE ||
				item.type_id.value === item.task.item_types.TABLES_TYPE ||
				item.type_id.value === item.task.item_types.REPORTS_TYPE) {
				if (!item.server('server_group_is_empty', [item.id.value])) {
					error = 'You can not delete the group. The group is not empty.';
				}
			}
			else {
				error = item.server('server_can_delete', [item.id.value]);
			}
		}
		return error;
	}
	
	function edit_item(item) {
		var doc = [item.ID, item.id.value, 'item_editor', item.task.user_info],
			cur_doc = task.server('check_doc_edited', doc);
		if (cur_doc) {
			item.task.question(item.task.doc_editing_message(cur_doc), function() {
				item.task.edited_doc = doc
				item.edit_record();
				item.task.server('set_edited', doc);
			});
		}
		else {
			item.task.edited_doc = doc
			item.edit_record();
			item.task.server('set_edited', doc);
		}
	
	}
	
	function init_view_table(item, options) {
		options.on_dblclick = edit_item;
	}
	
	function on_view_form_created(item) {
		var parent_type_id = item.task.item_tree.type_id.value,
			types = item.task.item_types;
	
		item.cur_record_count = undefined;
	
		if (parent_type_id === types.TASKS_TYPE || get_type_id(item) === types.DETAIL_TYPE) {
			item.view_form.find('#new-btn').hide();
			item.view_form.find('#delete-btn').hide();
			item.view_form.find('#up-btn').hide();
			item.view_form.find('#down-btn').hide();
		}
		item.view_form.find('#edit-btn').off('click.task').on('click', function() {
			edit_item(item);
		});
		item.view_form.find('#delete-btn').off('click.task').on('click', function() {
			if (item.record_count()) {
				item.question(item.task.language.delete_record, function() {
					var error = can_delete(item);
					if (error) {
						item.warning(error);
					}
					else {
						item.delete();
						item.apply();
					}
				})
			}
			else {
				item.warning('Record is not selected.');
			}
		});
		item.view_form.find("#new-btn").off('click.task').on('click', function() {
			if (parent_type_id === types.TASK_TYPE) {
				append_group(item);
			}
			else {
				item.append_record();
			}
		});
		item.view_form.find('#up-btn').click(function() {
			item.task.move_record_up(item);
			save_order(item);
		});
		item.view_form.find('#down-btn').click(function() {
			item.task.move_record_down(item);
			save_order(item);
		});
	}
	
	function on_edit_form_created(item) {
		var parent_type_id = item.task.item_tree.type_id.value,
			types = item.task.item_types,
			fields,
			row_count,
			height = 450,
			width = 560,
			item_tree = item.task.item_tree;
	
		if (item.type_id.value === types.ITEM_TYPE || item.type_id.value === types.TABLE_TYPE) {
			item.fields_editor = true;
			fields = ['f_name', 'f_item_name', 'f_table_name', 'f_primary_key', 'f_deleted_flag']
			row_count = 5;
			if (item.type_id.value === types.TABLE_TYPE) {
				fields = fields.concat(['f_master_id', 'f_master_rec_id'])
				row_count = 7;
			}
			fields = fields.concat(['f_visible', 'f_soft_delete', 'f_virtual_table', 'f_js_external'])
		}
		if (item.type_id.value === types.ITEMS_TYPE || item.type_id.value === types.TABLES_TYPE) {
			item.fields_editor = true;
			fields = ['f_name', 'f_item_name', 'f_visible', 'f_primary_key', 'f_deleted_flag']
			if (item.type_id.value === types.TABLES_TYPE) {
				fields = fields.concat(['f_master_id', 'f_master_rec_id'])
			}
		}
		else if (item.type_id.value === types.REPORTS_TYPE) {
			item.fields_editor = false;
		}
	
		if (item.fields_editor) {
			width = 1100;
			if ($(window).width() - 50 < width) {
				width = $(window).width() - 50;
			}
			item.create_inputs(item.edit_form.find(".edit-body"), {fields: fields, col_count: 2, row_count: row_count});
		}
		else {
			item.create_inputs(item.edit_form.find(".edit-body"));
		}
		item.edit_options.width = width;
		item.edit_form.find("#cancel-btn").attr("tabindex", 101).on('click.task', function(e) {item.cancel_edit(e); return false;});
		item.edit_form.find("#ok-btn").attr("tabindex", 100).on('click.task', function() {item.apply_record()});
		if (item.item_name === 'sys_items') {
			if (item.fields_editor) {
				if (parent_type_id === types.TASK_TYPE) {
					height = 520;
					if (item.id.value &&  !item.server('server_group_is_empty', [item.id.value])) {
						item.edit_form.find("#new-btn").prop("disabled", true);
						item.edit_form.find("#delete-btn").prop("disabled", true);
						update_sys_fields_read_only(item, true);
					}
					else {
						update_sys_fields_read_only(item, false);
					}
				}
				else {
					if (item.id.value) {
						update_sys_fields_read_only(item, true);
					}
					else {
						update_sys_fields_read_only(item, false);
					}
				}
				item.edit_table = item.sys_fields.create_table(item.edit_form.find(".edit-detail"),
					{
						height: height,
						tabindex: 90,
						sortable: true
					});
				item.edit_form.find("#new-btn").attr("tabindex", 92).on('click.task', function() {item.sys_fields.append_record()});
				item.edit_form.find("#edit-btn").attr("tabindex", 91).on('click.task', function() {item.sys_fields.edit_record()});
				item.edit_form.find("#delete-btn").attr("tabindex", 90).off('click.task')
					.on('click', function() {
						item.question(item.task.language.delete_record, function() {
							var error = item.sys_fields.can_delete(item.sys_fields);
							if (error) {
								item.warning(error);
							}
							else {
								item.sys_fields.delete();
								item.sys_fields.apply();
							}
					})
				});
			}
			else {
				item.edit_form.find('#edit-detail-footer').hide();
			}
		}
	}
	
	function on_edit_form_shown(item) {
		var caption = 'Item Editor';
	
		if (item.type_id.value === item.task.item_types.REPORT_TYPE) {
			caption = 'Report Editor';
		}
		else if (item.type_id.value === item.task.item_types.ITEMS_TYPE) {
			caption = 'Item Group Editor';
		}
		else if (item.type_id.value === item.task.item_types.TABLES_TYPE) {
			caption = 'Table Group Editor';
		}
		else if (item.type_id.value === item.task.item_types.REPORTS_TYPE) {
			caption = 'Report Group Editor';
		}
		if (item.is_new()) {
			item.edit_form.find('h4.modal-title').html(caption);
		}
		else {
			item.edit_form.find('h4.modal-title').html(caption + ' <span class="editor-title">' + item.f_item_name.value + '</span>');
		}
	}
	
	function on_edit_form_closed(item) {
		item.task.editing_finished();
	}
	
	function update_sys_fields_read_only(item, value) {
		item.f_primary_key.read_only = value;
		item.f_deleted_flag.read_only = value;
		if (item.f_master_id) {
			item.f_master_id.read_only = value;
		}
		if (item.f_master_rec_id) {
			item.f_master_rec_id.read_only = value;
		}
	}
	
	function on_after_append(item) {
		var parent = item.copy({handlers: false, details: false})
		item.f_visible.value = true;
		item.parent.value = item.task.item_tree.id.value;
		item.task_id.value = item.task.item_tree.task_id.value;
		item.table_id.value = 0;
		item.f_index.value = item.record_count();
		if (!item.type_id.value) {
			item.type_id.value = get_type_id(item);
		}
		parent.set_where({id: item.parent.value});
		parent.open();
		if (parent.record_count()) {
			item.f_primary_key.value = parent.f_primary_key.value;
			item.f_primary_key.lookup_value = parent.f_primary_key.lookup_value;
			item.f_deleted_flag.value = parent.f_deleted_flag.value;
			item.f_deleted_flag.lookup_value = parent.f_deleted_flag.lookup_value;
			item.f_master_id.value = parent.f_master_id.value;
			item.f_master_id.lookup_value = parent.f_master_id.lookup_value;
			item.f_master_rec_id.value = parent.f_master_rec_id.value;
			item.f_master_rec_id.lookup_value = parent.f_master_rec_id.lookup_value;
		}
		if (item.f_deleted_flag.value) {
			item.f_soft_delete.value = true;
		}
	}
	
	function on_field_validate(field) {
		var item = field.owner,
			copy,
			types = item.task.item_types,
			parent_types = [],
			parent_ids = [],
			check_detail,
			check_item,
			check_group,
			check_task,
			error;
		if (field.field_name === 'f_item_name') {
			if (!item.valid_identifier(field.value)) {
				return item.task.language.invalid_name
			}
			parent_ids.push(item.parent.value)
			if (item.type_id.value !== types.DETAIL_TYPE) {
				parent_types.push(types.TASK_TYPE);
			}
			if (item.type_id.value === types.ITEM_TYPE ||
				item.type_id.value === types.TABLE_TYPE ||
				item.type_id.value === types.REPORT_TYPE) {
				parent_types.push(types.ITEMS_TYPE);
				parent_types.push(types.TABLES_TYPE);
				parent_types.push(types.REPORTS_TYPE)
			}
			copy = item.copy({handlers: false, details: false})
			if (parent_types.length) {
				copy.set_where({type_id__in: parent_types})
				copy.open()
				copy.each(function(c) {
					parent_ids.push(c.id.value);
				});
			}
			copy.set_where({parent__in: parent_ids})
			copy.open()
			copy.each(function(c) {
				if (c.id.value !== item.id.value && c.f_item_name.value === field.value) {
					error = 'There is an item with this name';
					return false;
				}
			});
			if (error) {
				return error;
			}
			if (item.type_id.value === types.ITEM_TYPE ||
				item.type_id.value === types.TABLE_TYPE ||
				item.type_id.value === types.REPORT_TYPE) {
				check_item = new item.task.constructors.item()
				if (check_item[field.value] !== undefined) {
					return item.task.language.reserved_word;
				}
			}
			if (item.type_id.value === types.ITEMS_TYPE ||
				item.type_id.value === types.TABLES_TYPE ||
				item.type_id.value === types.REPORTS_TYPE) {
				check_group = new item.task.constructors.group()
				if (check_group[field.value] !== undefined) {
					return item.task.language.reserved_word;
				}
			}
			if (item.type_id.value === types.TASK_TYPE) {
				check_task = new item.task.constructors.task();
				if (check_task[field.value] !== undefined) {
					return item.task.language.reserved_word;
				}
			}
			if (item.type_id.value === types.DETAIL_TYPE) {
				check_detail = new item.task.constructors.detail();
				if (check_detail[field.value] !== undefined) {
					return item.task.language.reserved_word;
				}
			}
		}
		else if (field.field_name === 'f_primary_key') {
			if (!field.value && !item.f_virtual_table.value &&
				(item.type_id.value === types.ITEM_TYPE || item.type_id.value === types.TABLE_TYPE)) {
				return item.task.language.value_required;
			}
		}
		else if (field.field_name === 'f_master_rec_id' || field.field_name === 'f_master_id') {
			if (!field.value && !item.f_virtual_table.value && item.type_id.value === types.TABLE_TYPE) {
				return item.task.language.value_required;
			}
		}
	}
	
	function on_field_changed(field, lookup_item) {
		var copy,
			ident,
			item = field.owner
		if (item.is_new() && item.type_id.value != item.task.item_types.DETAIL_TYPE) {
			if (field.field_name == 'f_item_name') {
				copy = item.copy({handlers: false, details: false});
				copy.set_where({type_id: item.task.item_types.TASK_TYPE})
				copy.open();
				if (copy.record_count() === 1) {
					item.f_table_name.value = copy.f_item_name.value + '_' + field.value;
					if (task.db_options.UPPER_CASE) {
						item.f_table_name.value = item.f_table_name.value.toUpperCase();
					}
					else {
						item.f_table_name.value = item.f_table_name.value.toLowerCase();
					}
				}
			}
			if (field.field_name === 'f_name' && !item.f_item_name.value) {
				try {
					ident = field.text.replace(' ', '_').toLowerCase();
					if (valid_identifier(ident)) {
						item.f_item_name.value = ident;
					}
				}
				catch (e) {
				}
			}
		}
		if (field.field_name === 'f_deleted_flag') {
			if (field.value) {
				item.f_soft_delete.read_only = false;
				item.f_soft_delete.value = true;
			}
			else {
				item.f_soft_delete.value = false;
				item.f_soft_delete.read_only = true;
			}
		}
	}
	
	function valid_identifier(ident) {
	
		function is_char(ch) {
			return ch.charCodeAt(0) >= 65 && ch.charCodeAt(0) <= 90 ||
				ch.charCodeAt(0) >= 97 && ch.charCodeAt(0) <= 122;
		}
	
		function is_digit(ch) {
			return ch.charCodeAt(0) >= 48 && ch.charCodeAt(0) <= 57;
		}
	
		var i,
			len = ident.length;
		if (ident[0] === '_' || is_char(ident[0])) {
			for (i = 1; i < len; i++) {
				if (!(ident[i] === '_' || is_char(ident[i]) || is_digit(ident[i]))) {
					return false;
				}
			}
			return true;
		}
		return false;
	}
	
	function on_after_scroll(item) {
		var ScrollTimeOut
		clearTimeout(ScrollTimeOut);
		ScrollTimeOut = setTimeout(function() {
				task.btns_panel.find('button').prop("disabled", item.record_count() === 0);
				if (item.record_count() && item.f_table_name && item.f_virtual_table) {
					item.f_table_name.read_only = !item.is_new();
					item.f_virtual_table.read_only = !item.is_new();
					task.btns_panel.find('button.indices').prop("disabled", item.f_virtual_table.value);
					task.btns_panel.find('button.foreign_keys').prop("disabled", item.f_virtual_table.value);
				}
				if (item.f_soft_delete && item.f_deleted_flag) {
					item.f_soft_delete.read_only = !item.f_deleted_flag.value;
				}
			},
			100
		);
	}
	
	function get_fields_list(task) {
		var item = task.sys_items,
			table = item.copy(),
			fields = item.task.sys_fields.copy(),
			parent,
			list = [];
		if (item.table_id.value === 0) {
			fields.set_where({owner_rec_id__in: [item.id.value, item.parent.value]});
		}
		else {
			table.set_where({id: item.table_id.value});
			table.open({fields: ['id', 'parent']});
			parent = table.parent.value;
			fields.set_where({owner_rec_id__in: [item.table_id.value, parent]});
		}
		fields.set_order_by(['f_field_name']);
		fields.open({fields: ['id', 'f_field_name']});
		fields.each(function (f) {
			list.push([f.id.value, f.f_field_name.value]);
		});
		return list
	}
	
	function view_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			dest_list,
			title;
	
		function save_view(item, dest_list) {
			info.view_list = dest_list;
			item.server('server_store_interface', [item.id.value, info]);
		}
	
		info = item.server('server_load_interface', [item.id.value]);
		source_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		dest_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true, '60%'],
			['param1', 'Word wrap', false],
			['param2', 'Expand', false],
			['param3', 'Edit', false]
		];
		title = item.task.language.viewing + ' <span class="editor-title">' + item.f_item_name.value + '</span>';
		item.task.sys_fields_editor.fields_editor(item, title, source_def, get_fields_list(item.task), dest_def, info.view_list, save_view);
	}
	
	function edit_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			dest_list,
			title;
	
		function save_edit(item, dest_list) {
			info.edit_list = dest_list;
			item.server('server_store_interface', [item.id.value, info]);
		}
	
		info = item.server('server_load_interface', [item.id.value]);
		source_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		dest_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		title = item.task.language.editing + ' <span class="editor-title">' + item.f_item_name.value + '</span>';;
		item.task.sys_fields_editor.fields_editor(item, title, source_def, get_fields_list(item.task), dest_def, info.edit_list, save_edit);
	}
	
	function edit_code(item, field_name) {
		item.task.sys_code_editor.code_editor(item, field_name)
	}
	
	function edit_file(item, file_name) {
		item.task.sys_code_editor.file_editor(item, file_name)
	}
	
	function edit_client(item) {
		edit_code(item, 'f_web_client_module');
	}
	
	function edit_server(item) {
		edit_code(item, 'f_server_module');
	}
	
	function edit_index_html(item) {
		edit_file(item, 'index.html');
	}
	
	function edit_project_css(item) {
		edit_file(item, 'project.css');
	}
	
	function get_detail_source_list(item) {
		var result = [],
			tables = item.copy({handlers: false});
		tables.set_where({type_id: task.item_types.TABLE_TYPE});
		tables.open();
		tables.each(function(t) {
			result.push([t.id.value, t.f_item_name.value]);
		});
		return result
	}
	
	function get_detail_dest_list(item) {
		var result = [],
			details = item.copy({handlers: false});
		details.set_where({parent: item.id.value});
		details.open();
		details.each(function(d) {
			result.push([d.table_id.value]);
		});
		return result;
	}
	
	function details_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			source_list = get_detail_source_list(item),
			dest_list = get_detail_dest_list(item),
			title;
	
		function save_edit(item, result) {
			if (JSON.stringify(dest_list) !== JSON.stringify(result)) {
				item.server('server_update_details', [item.id.value, result]);
				item.task.refresh_tree(item.task);
			}
		}
	
		source_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		dest_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		title = item.task.language.details + ' <span class="editor-title">' + item.f_item_name.value + '</span>';;
		item.task.sys_fields_editor.fields_editor(item, title, source_def, source_list, dest_def, dest_list, save_edit, undefined, false);
	}
	
	function order_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			dest_list,
			title;
	
		function save_view(item, dest_list) {
			info.order_list = dest_list;
			item.server('server_store_interface', [item.id.value, info]);
		}
	
		info = item.server('server_load_interface', [item.id.value]);
		source_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		dest_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true, '80%'],
			['param1', item.task.language.caption_descening, true]
		];
		title = item.task.language.order + ' <span class="editor-title">' + item.f_item_name.value + '</span>';
		item.task.sys_fields_editor.fields_editor(item, title, source_def, get_fields_list(item.task), dest_def, info.order_list, save_view);
	}
	
	function get_reports_list(item) {
		var parent,
			result = [],
			items = item.copy({handlers: false});
		items.set_where({type_id: item.task.item_types.REPORTS_TYPE});
		items.open();
		parent = items.id.value
		items.set_where({parent: parent});
		items.open()
		items.each(function(it) {
			result.push([it.id.value, it.f_name.value]);
		});
		return result;
	}
	
	function reports_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			dest_list,
			title;
	
		function save_edit(item, dest_list) {
			info.reports_list = dest_list;
			item.server('server_store_interface', [item.id.value, info]);
		}
	
		info = item.server('server_load_interface', [item.id.value]);
		source_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		dest_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		title = item.task.language.reports + ' <span class="editor-title">' + item.f_item_name.value + '</span>';;
		item.task.sys_fields_editor.fields_editor(item, title, source_def, get_reports_list(item), dest_def, info.reports_list, save_edit);
	}
	
	function filters_setup(item) {
		item.task.sys_filters.filters.owner_rec_id.value = item.id.value;
		item.task.sys_filters.open();
		item.task.sys_filters.set_view_fields(['f_name', 'f_filter_name', 'f_type', 'f_field', 'f_visible']);
		item.task.sys_filters.set_edit_fields(['f_field', 'f_name', 'f_filter_name', 'f_type', 'f_multi_select_all', 'f_placeholder',
			'f_help', 'f_visible']);
		item.task.sys_filters.view_options.title = 'Filters <span class="editor-title">' + item.f_item_name.value + '</span>';
		item.task.sys_filters.view();
	}
	
	function indices_setup(item) {
		item.task.sys_indices.filters.owner_rec_id.value = item.id.value;
		item.task.sys_indices.filters.foreign_index.value = false;
		item.task.sys_indices.open();
		item.task.sys_indices.view_options.title = 'Indices <span class="editor-title">' + item.f_item_name.value + '</span>';
		item.task.sys_indices.view();
	}
	
	function foreign_keys_setup(item) {
		item.task.sys_indices.filters.owner_rec_id.value = item.id.value;
		item.task.sys_indices.filters.foreign_index.value = true;
		item.task.sys_indices.open();
		item.task.sys_indices.view_options.title = 'Foreign keys <span class="editor-title">' + item.f_item_name.value + '</span>';
		item.task.sys_indices.view();
	}
	
	function report_params_setup(item) {
		var fields = ['f_name', 'f_param_name','f_data_type', 'f_object', 'f_object_field', 'f_enable_typehead', 'f_multi_select',
			'f_lookup_values', 'f_required', 'f_alignment', 'f_visible'];
		item.task.sys_report_params.filters.owner_rec_id.value = item.id.value;
		item.task.sys_report_params.open();
		item.task.sys_report_params.view_options.fields = fields;
		fields = ['f_name', 'f_param_name','f_data_type', 'f_object', 'f_object_field', 'f_enable_typehead', 'f_multi_select',
			'f_multi_select_all', 'f_lookup_values', 'f_required', 'f_alignment', 'f_placeholder', 'f_help', 'f_visible'];
		item.task.sys_report_params.edit_options.fields = fields;
		item.task.sys_report_params.view_options.title = 'Params <span class="editor-title">' + item.f_item_name.value + '</span>';
		item.task.sys_report_params.view();
	}
	
	function privileges_setup(item) {
		var priv = item.task.sys_privileges;
		priv.view_options.fields = ['item_id', 'f_can_view', 'f_can_create', 'f_can_edit', 'f_can_delete']
		priv.view();
	}
	
	function on_view_form_keydown(item, event) {
		if (event.keyCode === 45 && event.ctrlKey === true){
			event.preventDefault();
			item.append_record();
		}
		else if (event.keyCode === 46 && event.ctrlKey === true){
			event.preventDefault();
			item.delete_record();
		}
	}
	
	function on_edit_form_keydown(item, event) {
		if (event.keyCode === 13 && event.ctrlKey === true){
			event.preventDefault();
			item.edit_form.find("#ok-btn").focus();
			item.apply_record();
		}
		if (event.keyCode === 45 && event.ctrlKey === true){
			event.preventDefault();
			item.sys_fields.append_record();
		}
		else if (event.keyCode === 46 && event.ctrlKey === true){
			event.preventDefault();
			item.sys_fields.delete_record();
		}
	}
	
	function on_after_apply(item) {
		item.refresh_record();
		on_after_scroll(item);
		if (item.cur_record_count && item.cur_record_count !== item.record_count()) {
			if (item.type_id.value === item.task.item_types.ITEMS_TYPE ||
				item.type_id.value === item.task.item_types.TABLES_TYPE ||
				item.type_id.value === item.task.item_types.REPORTS_TYPE) {
				item.task.refresh_tree(item.task);
			}
		}
	}
	
	function on_field_select_value(field, lookup_item) {
		var item = field.owner;
		if (lookup_item.item_name === 'sys_fields') {
			lookup_item.set_view_fields(['f_field_name', 'f_name']);
		}
		if (lookup_item.item_name === 'sys_fields') {
			lookup_item.set_order_by(['f_field_name']);
		}
		if (field.field_name === 'f_primary_key' ||
			field.field_name === 'f_deleted_flag' ||
			field.field_name === 'f_master_id' ||
			field.field_name === 'f_master_rec_id') {
			lookup_item.set_order_by(['f_field_name']);
			lookup_item.set_where({owner_rec_id__in: [item.parent.value],
				f_data_type__in: [item.task.consts.INTEGER, item.task.consts.TEXT]});
		}
		lookup_item.on_after_open = function(it) {
			var clone = item.sys_fields.clone()
			it.first();
			while (!it.eof()) {
				if (it.id.value === item.f_primary_key.value ||
					it.id.value === item.f_deleted_flag.value ||
					it.id.value === item.f_master_id.value ||
					it.id.value === item.f_master_rec_id.value) {
					it.delete();
				}
				else {
					it.next();
				}
			}
			clone.each(function(c) {
				if ((c.f_data_type.value === item.task.consts.INTEGER ||
					c.f_data_type.value === item.task.consts.TEXT) &&
					c.id.value !== item.f_primary_key.value &&
					c.id.value !== item.f_deleted_flag.value &&
					c.id.value !== item.f_master_id.value &&
					c.id.value !== item.f_master_rec_id.value) {
					it.append();
					it.id.value = c.id.value;
					it.f_field_name.value = c.f_field_name.value;
					it.f_name.value = c.f_name.value;
					it.f_data_type.value = c.f_data_type.value;
					it.post();
				}
			});
			it.first();
		}
	}
	
	function on_before_append(item) {
		item.cur_record_count = item.record_count();
	}
	
	
	function on_before_delete(item) {
		item.cur_record_count = item.record_count();
	}
	
	function on_before_apply(item) {
		return {'manual_update': item.task._manual_update};
	}
	this.init_fields = init_fields;
	this.init_buttons = init_buttons;
	this.tree_changed = tree_changed;
	this.get_type_id = get_type_id;
	this.save_order = save_order;
	this.append_group = append_group;
	this.can_delete = can_delete;
	this.edit_item = edit_item;
	this.init_view_table = init_view_table;
	this.on_view_form_created = on_view_form_created;
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_shown = on_edit_form_shown;
	this.on_edit_form_closed = on_edit_form_closed;
	this.update_sys_fields_read_only = update_sys_fields_read_only;
	this.on_after_append = on_after_append;
	this.on_field_validate = on_field_validate;
	this.on_field_changed = on_field_changed;
	this.valid_identifier = valid_identifier;
	this.on_after_scroll = on_after_scroll;
	this.get_fields_list = get_fields_list;
	this.view_setup = view_setup;
	this.edit_setup = edit_setup;
	this.edit_code = edit_code;
	this.edit_file = edit_file;
	this.edit_client = edit_client;
	this.edit_server = edit_server;
	this.edit_index_html = edit_index_html;
	this.edit_project_css = edit_project_css;
	this.get_detail_source_list = get_detail_source_list;
	this.get_detail_dest_list = get_detail_dest_list;
	this.details_setup = details_setup;
	this.order_setup = order_setup;
	this.get_reports_list = get_reports_list;
	this.reports_setup = reports_setup;
	this.filters_setup = filters_setup;
	this.indices_setup = indices_setup;
	this.foreign_keys_setup = foreign_keys_setup;
	this.report_params_setup = report_params_setup;
	this.privileges_setup = privileges_setup;
	this.on_view_form_keydown = on_view_form_keydown;
	this.on_edit_form_keydown = on_edit_form_keydown;
	this.on_after_apply = on_after_apply;
	this.on_field_select_value = on_field_select_value;
	this.on_before_append = on_before_append;
	this.on_before_delete = on_before_delete;
	this.on_before_apply = on_before_apply;
}

task.events.events3 = new Events3();

function Events2() { // admin.catalogs.sys_roles 

	function on_view_form_created(item) {
		var table_height = item.task.center_panel.height() - item.task.view_panel.height();
		if (item.view_form.hasClass('modal')) {
			table_height = 460;
			item.view_options.width = 560;
			item.view_form.find("#priv-panel").remove();
			item.view_form.find("#roles-panel").removeClass('span4').addClass('span12');
			item.view_form.find("#roles-footer").hide();
			item.view_table = item.create_table(item.view_form.find("#roles-panel .view-table"),
				{
					height: table_height,
					fields: ['id', 'f_name'],
					column_width: {id: '10%'}
				}
			);
		}
		else {
			item.view_form.find("#roles-panel #new-btn")
				.text(item.task.language['new'])
				.on('click.task', function() {append_role(item);});
			item.view_form.find("#roles-panel #delete-btn")
				.text(item.task.language['delete'])
				.on('click.task', function() {del_role(item);});
			item.view_form.find("#select-all-btn")
				.text(item.task.language.select_all)
				.on('click.task', function() {select_all_clicked(item);});
			item.view_form.find("#unselect-all-btn")
				.text(item.task.language.unselect_all)
				.on('click.task', function() {unselect_all_clicked(item);});
			item.set_view_fields(['f_name'], [item.task.language.roles]);
			item.view_table = item.create_table(item.view_form.find("#roles-panel .view-table"),
				{
					height: table_height,
					fields: ['id', 'f_name'],
					word_wrap: false,
					sortable: false
				}
			);
			item.sys_privileges.set_view_fields(['item_id', 'f_can_view', 'f_can_create', 'f_can_edit', 'f_can_delete'],
				[item.task.language.item, item.task.language.can_view, item.task.language.can_create,
				item.task.language.can_edit, item.task.language.can_delete]);
			item.detail_table = item.sys_privileges.create_table(item.view_form.find("#priv-panel .view-table"),
				{
					height: table_height,
					word_wrap: true,
					column_width: {item_id: '50%'},
					sortable: false,
					dblclick_edit: false
				}
			);
			item.detail_table.$table.on('click', 'td', function() {
				var $td = $(this),
					field_name = $td.data('field_name'),
					field = item.sys_privileges.field_by_name(field_name);
				if (field.field_type === "boolean") {
					if (!item.sys_privileges.is_changing()) {
						item.sys_privileges.edit();
					}
					field.value = !field.value
				}
			})
		}
	}
	
	function select_all_clicked(item, value) {
		var detail = item.details.sys_privileges,
			on_field_changed = detail.on_field_changed,
			rec_no = detail.rec_no;
	
		if (value === undefined) {
			value = true;
		}
		if (!item.is_changing()) {
			item.edit();
		}
		try {
			detail.on_field_changed = undefined;
			detail.disable_controls();
			detail.each(function(d) {
				d.edit();
				d.f_can_create.value = value;
				d.f_can_view.value = value;
				d.f_can_edit.value = value;
				d.f_can_delete.value = value;
				if (d.id.value) {
					d.record_status = item.task.consts.RECORD_MODIFIED;
				}
				else {
					d.record_status = item.task.consts.RECORD_INSERTED;
				}
				d.post();
			});
		}
		finally {
			detail.on_field_changed = on_field_changed
			detail.rec_no = rec_no
			detail.enable_controls();
		}
		if (item.is_changing()) {
			item.post();
			item.apply();
			item.edit();
		}
		detail.open();
	}
	
	function unselect_all_clicked(item) {
		select_all_clicked(item, false);
	}
	
	function del_role(item) {
		if (item.is_changing()) {
			item.cancel();
		}
		item.delete_record();
	}
	
	function append_role(item) {
		if (item.is_changing()) {
			item.post();
			item.apply();
		}
		item.append_record();
	}
	
	
	function on_before_scroll(item) {
		if (item.is_changing()) {
			item.post();
			item.apply();
		}
	}
	
	var ScrollTimeOut;
	
	function on_after_scroll(item) {
		clearTimeout(ScrollTimeOut);
		ScrollTimeOut = setTimeout(
			function() {
				item.sys_privileges.open();
				if (item.is_browsing()) {
					item.edit();
				}
			},
			50
		);
	}
	
	function on_after_apply(item) {
		item.server('roles_changed');
	}
	this.on_view_form_created = on_view_form_created;
	this.select_all_clicked = select_all_clicked;
	this.unselect_all_clicked = unselect_all_clicked;
	this.del_role = del_role;
	this.append_role = append_role;
	this.on_before_scroll = on_before_scroll;
	this.on_after_scroll = on_after_scroll;
	this.on_after_apply = on_after_apply;
}

task.events.events2 = new Events2();

function Events9() { // admin.catalogs.sys_tasks 

	function on_after_edit(item) {
		item.f_manual_update.value = item.task._manual_update;
	}
	
	function on_after_apply(item) {
		if (task.init_project && item.f_db_type.value) {
			item.task.server('server_create_task');
			item.task.on_page_loaded(item.task);
		}
		item.task.update_db_manual_mode(item.task)
	}
	
	function on_field_changed(field, lookup_item) {
		var item = field.owner,
			db_options;
		if (field == field.owner.f_db_type) {
			db_options = item.task.server('server_get_db_options', [field.owner.f_db_type.value]);
			task.db_options = db_options;
			if (field.owner.is_changing()) {
				field.owner.f_alias.value = null;
				field.owner.f_login.value = null;
				field.owner.f_password.value = null;
				field.owner.f_encoding.value = null;
				field.owner.f_host.value = null;
				field.owner.f_port.value = null;
			}
			field.owner.f_login.read_only = !db_options.NEED_DATABASE_NAME;
			field.owner.f_login.read_only = !db_options.NEED_LOGIN;
			field.owner.f_password.read_only = !db_options.NEED_PASSWORD;
			field.owner.f_encoding.read_only = !db_options.NEED_ENCODING
			field.owner.f_host.read_only = !db_options.NEED_HOST
			field.owner.f_port.read_only = !db_options.NEED_PORT
		}
	}
	
	function on_before_post(item) {
		var error = item.task.server('server_check_connection', [
				item.f_db_type.value, item.f_alias.value, item.f_login.value,
				item.f_password.value, item.f_host.value, item.f_port.value,
				item.f_encoding.value
			]);
		if (error) {
			item.warning(error);
			item.abort()
		}
		if (task.init_project) {
			item.task.server('server_set_task_name',
				[item.f_name.value, item.f_item_name.value]);
		}
		item.task._manual_update = item.f_manual_update.value
		item.f_manual_update.value = false;
	}
	
	function on_after_post(item) {
	}
	
	function on_field_validate(field) {
		var item = field.owner;
		if (field.field_name === 'f_item_name' && field.required) {
			if (!item.task.sys_items.valid_identifier(field.value)) {
				return item.task.language.invalid_name;
			}
		}
		if (field.field_name === 'f_port' && field.value) {
			if (isNaN(field.value)) {
				return 'The port must be an integer value.'
			}
		}
	}
	
	function on_edit_form_closed(item) {
		item.task.editing_finished();
	}
	this.on_after_edit = on_after_edit;
	this.on_after_apply = on_after_apply;
	this.on_field_changed = on_field_changed;
	this.on_before_post = on_before_post;
	this.on_after_post = on_after_post;
	this.on_field_validate = on_field_validate;
	this.on_edit_form_closed = on_edit_form_closed;
}

task.events.events9 = new Events9();

function Events14() { // admin.catalogs.sys_code_editor 

	function code_editor(item, field_name) {
		var editor = this.copy(),
			mess;
		editor.item = item;
		editor.field_name = field_name;
		editor.is_server = field_name === 'f_server_module';
		editor.doc_type = 'client_module';
		if (editor.is_server) {
			editor.doc_type = 'server_module';
		}
		editor.item_info = item.task.server('server_item_info', [item.task.sys_items.id.value,
			editor.is_server, editor.doc_type]);
		editor.view();
	}
	
	function file_editor(item, file_name) {
		var editor = this.copy(),
			mess;
		editor.item = item;
		editor.file_name = file_name;
		editor.doc_type = file_name;
		editor.item_info = item.task.server('server_get_file_info', [item.task.sys_items.id.value, file_name]);
		editor.view();
	}
	
	function on_view_form_created(item) {
		task.code_editor_item = item;
		if (item.field_name) {
			$("title").html(item.item_info.module_name);
			item.view_options.title = 'Code Editor <span class="editor-title">' + item.item_info.module_name + '</span>';
		}
		else if (item.file_name) {
			$("title").html(item.file_name);
			item.view_options.title = 'Code Editor <span class="editor-title">' + item.file_name + '</span>';
		}
		item.view_form.find("#left-box").width(250);
		item.view_form.find("#right-box").hide();
		item.view_form.find("#cancel-btn").attr("tabindex", 101).on('click', function(e) {
			cancel_edit(item);
		});
		item.view_form.find("#ok-btn").attr("tabindex", 100).on('click', function() {
			save_edit(item);
		});
		item.view_form.find("#find-btn").attr("tabindex", 99).on('click', function() {
			find_in_project(item);
		});
		update_size(item);
	}
	
	function on_view_form_shown(item) {
		if (item.field_name) {
			item.view_form.find('#editor-tabs ul')
				.append('<li id="module"><a href="#">Module</a></li>')
				.append('<li id="events"><a href="#">Events</a></li>')
				.append('<li id="task"><a href="#">Task</a></li>')
				.append('<li id="fields"><a href="#">Fields</a></li>');
	
			add_tree(item, "Module");
			add_tree(item, "Events");
			add_tree(item, "Task");
			add_tree(item, "Fields");
	
			item.view_form.find('#editor-tabs #info-grids').height(
				item.view_form.find('#left-box').innerHeight() - item.view_form.find('ul.nav-tabs').outerHeight() - 14
			)
			info_tab_clicked(item, item.view_form.find('li#module'));
	
			item.editor = ace.edit("editor");
			item.editor.$blockScrolling = Infinity;
			if (item.is_server) {
				item.is_server_module = true;
				item.editor.getSession().setMode("ace/mode/python");
				item.editor.getSession().setOption("tabSize", 4);
				item.editor.getSession().setUseSoftTabs(true);
			}
			else {
				item.editor.getSession().setMode("ace/mode/javascript");
			}
		}
		else if (item.file_name) {
			if (item.item_info.Templates) {
				item.view_form.find('#editor-tabs ul')
					.append('<li id="templates"><a href="#">Templates</a></li>');
				add_tree(item, "Templates");
				item.view_form.find('#editor-tabs #info-grids').height(
					item.view_form.find('#left-box').innerHeight() - item.view_form.find('ul.nav-tabs').outerHeight() - 14
				)
				info_tab_clicked(item, item.view_form.find('li#templates'));
			}
			else {
				item.view_form.find("#left-box").hide();
			}
	
			item.editor = ace.edit("editor");
			item.editor.$blockScrolling = Infinity;
			if (item.file_name === 'index.html') {
				item.editor.getSession().setMode("ace/mode/html");
			}
			else {
				item.editor.getSession().setMode("ace/mode/css");
			}
		}
		item.loaded = true;
		item.editor.session.setValue(item.item_info.code);
		item.editor.gotoLine(1);
	
		item.view_form.find('#ok-btn').prop("disabled", true);
	
		item.editor.on('input', function() {
			item.view_form.find("#error-info").text('');
			if (item.loaded) {
				item.loaded = false;
				mark_clean(item);
				return;
			}
			if (get_modified(item)) {
				item.view_form.find('#ok-btn').prop("disabled", false);
			}
			else {
				item.view_form.find('#ok-btn').prop("disabled", true);
			}
	
		});
	
		item.view_form.on('click', '#editor-tabs > .nav > li', function() {
			info_tab_clicked(item, $(this))
		});
		item.view_form.on('dblclick', '.dbtree ul li', function(e) {
			e.preventDefault();
			e.stopPropagation();
			tree_node_clicked(item, $(this))
		});
		$(item.editor).focus();
		setTimeout(function () {
			item.view_form.off('keyup.dismiss.modal');
			$(item.editor).focus();
			},  100
		);
	}
	
	function get_modified(item) {
		return !item.editor.session.getUndoManager().isClean();
	}
	
	function mark_clean(item) {
		item.editor.session.getUndoManager().markClean();
	}
	
	function on_view_form_close_query(item) {
		var result;
		if (get_modified(item)) {
			item.yes_no_cancel(task.language.save_changes,
				function() {
					save_edit(item);
					item.close_view_form();
				},
				function() {
					mark_clean(item);
					item.close_view_form();
				}
			)
			result = false;
		}
		else {
			task.code_editor_item = undefined;
			item.editor.destroy();
			result = true;
		}
		return result;
	}
	
	function on_view_form_closed(item) {
		item.task.editing_finished();
	}
	
	function save_to_field(item) {
		var text = item.editor.getValue(),
			info,
			error,
			line,
			module_info;
	
		if (item.is_server && text.indexOf('\t') !== -1) {
			text = text.split('\t').join(' ' + '   ');
			item.editor.setValue(text);
		}
		info = item.task.server('server_save_edit', [item.task.sys_items.id.value, text, item.is_server]),
		error = info[0],
		line = info[1],
		module_info = info[2];
	
		if (error && line && line < item.editor.session.getLength()) {
			item.editor.gotoLine(line);
		}
		if (!error) {
			item.item_info["Module"] = module_info;
			add_tree(item, "Module");
			update_tab_height(item);
		}
		return error;
	}
	
	function save_to_file(item) {
		var result =  item.task.server('server_save_file', [item.file_name, item.editor.getValue()]),
			error = result.error;
		if (result['Templates']) {
			item.item_info["Templates"] = result['Templates'];
			add_tree(item, "Templates");
			update_tab_height(item);
		}
	}
	
	function save_edit(item) {
		var error = false;
		if (item.field_name) {
			error = save_to_field(item);
		}
		else if (item.file_name) {
			error = save_to_file(item);
		}
		if (error) {
			item.view_form.find("#error-info").text(error);
		}
		else {
			item.view_form.find("#error-info").text('');
			mark_clean(item);
			item.view_form.find('#ok-btn').prop("disabled", true);
		}
	}
	
	function cancel_edit(item) {
		mark_clean(item);
		item.close_view_form();
	}
	
	function update_size(item) {
		var height;
		item.view_options.width = $(window).width() - 50;
		height = $(window).height() - 200;
		item.view_form.find("#editor-box").height(height);
	}
	
	function resize(item) {
		var height;
		height = $(window).height() - 200;
		item.view_options.width = $(window).width() - 50;
	//	item.view_options.height = height;
	//	item.view_form.find("#editor-box").height(height);
	//	item.view_form.find("#editor").height(height);
	//	item.view_form.find(".ace_content").height(height);
	//	item.view_form.find("#editor-tabs").height(height);
	//	item.view_form.find("#info-grids").height(height);
	//	update_tab_height(item);
		item.view_form.data('modal').layout();
	}
	
	function find_text(item, text) {
		return item.editor.find(text, {
			backwards: false,
			wrap: false,
			caseSensitive: true,
			wholeWord: true,
			regExp: false
		});
	}
	
	function tree_node_clicked(item, $li) {
		var tab = $li.closest('.info-tree').attr('id'),
			node_text = $li.find('span.tree-text:first').text(),
			text,
			result,
			params;
	
		if (tab === 'module') {
			item.editor.gotoLine(1);
			if (item.is_server_module) {
				text = 'def ' + node_text;
			}
			else {
				text = 'function ' + node_text;
			}
			result = find_text(item, text);
		}
		else if (tab === 'events') {
			item.editor.gotoLine(1);
			if (!find_text(item, node_text + '(')) {
				params = item.item_info.Events[node_text];
				item.editor.gotoLine(item.editor.session.getLength() + 1);
				if (item.is_server_module) {
					text = 'def ' + node_text + '(' + params + '):\n\tpass';
				}
				else {
					text = 'function ' + node_text + '(' + params + ') {\n\n}';
				}
				item.editor.insert('\n\n' + text);
			}
		}
		else if (tab === 'task' || tab === 'fields') {
			item.editor.insert(node_text);
		}
		else if (tab === 'templates') {
			item.editor.gotoLine(1);
			text = node_text;
			find_text(item, text);
		}
		item.editor.focus();
	}
	
	function update_tab_height(item) {
		var $li,
			dbtree,
			height;
		$li = item.view_form.find('#editor-tabs > .nav > li.active');
		if ($li.length) {
			height = item.view_form.find('#editor-tabs #info-grids').innerHeight();
			item.view_form.find('#editor-tabs div.info-tree').hide();
			item.view_form.find('#editor-tabs div.info-tree.' + $li.attr('id'))
				.show()
				.height(height)
				.find('.dbtree').height(height);
			dbtree = item.view_form.find('#editor-tabs div.info-tree.' + $li.attr('id')).find('.dbtree').data('tree');
			if (dbtree) {
				dbtree.scroll_into_view();
			}
		}
	}
	
	function info_tab_clicked(item, $li) {
		var height;
		item.view_form.find('#editor-tabs li').removeClass('active');
		$li.addClass('active');
		update_tab_height(item);
	}
	
	function add_tree(item, title) {
		var tree_item = item.copy(),
			info_name = title.toLowerCase(),
			$li = item.view_form.find('li#' + info_name),
			tree_info = item.item_info[title],
			tree_div;
	
		tree_div = item.view_form.find('#editor-tabs #info-grids > div.' + info_name);
		if (tree_div.length) {
			tree_div.empty();
		}
		else {
			tree_div = $('<div id="' + info_name + '" class="info-tree ' + info_name + '">');
			item.view_form.find('#editor-tabs #info-grids').append(tree_div);
		}
		tree_div.hide();
		tree_item.open({open_empty: true});
		build_tree(tree_item, tree_info, 0);
		tree_item.disable_controls();
		try {
			tree_item.create_tree(tree_div,
				{
					id_field: 'id',
					parent_field: 'parent',
					text_field: 'name',
					parent_of_root_value: 0
				}
			);
		}
		finally {
			tree_item.enable_controls();
		}
	}
	
	function build_tree(tree_item, tree_info, parent_id) {
		var keys = [],
			cur_id = 0;
		for(var key in tree_info){
			keys.push(key);
		}
		keys = keys.sort();
		cur_id = parent_id + 1;
		if (keys.length) {
			for (var i = 0; i < keys.length; i++) {
				tree_item.append();
				tree_item.id.value = cur_id;
				tree_item.parent.value = parent_id;
				tree_item.name.value = keys[i];
				tree_item.post();
				if (tree_info[keys[i]] !== null && typeof tree_info[keys[i]] === 'object') {
					cur_id = build_tree(tree_item, tree_info[keys[i]], cur_id);
				}
				cur_id++;
			}
		}
		return cur_id;
	}
	
	function find_in_project(item) {
		item.task.sys_search.find_in_task(task);
	}
	
	function on_view_form_keydown(item, e) {
		var code = (e.keyCode ? e.keyCode : e.which);
		if (code === 27) {
			if (!item.view_form.find('.ace_search').is(':visible')) {
				item.close_view_form();
			}
		}
		if (e.ctrlKey && code === 83) {
			e.preventDefault();
			e.stopPropagation();
			save_edit(item)
		}
		if (e.altKey && code === 70) {
			e.preventDefault();
			e.stopPropagation();
			find_in_project(item);
		}
	}
	this.code_editor = code_editor;
	this.file_editor = file_editor;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.get_modified = get_modified;
	this.mark_clean = mark_clean;
	this.on_view_form_close_query = on_view_form_close_query;
	this.on_view_form_closed = on_view_form_closed;
	this.save_to_field = save_to_field;
	this.save_to_file = save_to_file;
	this.save_edit = save_edit;
	this.cancel_edit = cancel_edit;
	this.update_size = update_size;
	this.resize = resize;
	this.find_text = find_text;
	this.tree_node_clicked = tree_node_clicked;
	this.update_tab_height = update_tab_height;
	this.info_tab_clicked = info_tab_clicked;
	this.add_tree = add_tree;
	this.build_tree = build_tree;
	this.find_in_project = find_in_project;
	this.on_view_form_keydown = on_view_form_keydown;
}

task.events.events14 = new Events14();

function Events15() { // admin.catalogs.sys_fields_editor 

	function fields_editor(item, title, source_def, source_list, dest_def, dest_list, save_func, cancel_func, can_move, read_only) {
		var editor = this.copy();
		editor.item = item;
		editor.title = title;
		editor.source_def = source_def;
		editor.source_list = source_list;
		editor.dest_def = dest_def;
		editor.dest_list = dest_list;
		editor.save_func = save_func;
		editor.cancel_func = cancel_func;
		if (can_move === undefined) {
			can_move = true;
		}
		editor.can_move = can_move;
		if (read_only === undefined) {
			read_only = false;
		}
		editor.read_only = read_only;
		editor.view();
		return editor;
	}
	
	function on_view_form_created(item) {
		var name_width = {},
			i,
			view_fields;
	
		if (item.dest_def[1].length === 4) {
			name_width = {'name': item.dest_def[1][3]};
		}
		item.source = item.copy(),
		item.dest = item.copy();
		item.view_options.width = 680;
		item.view_form.title = item.title;
	
		view_fields = [];
		for (i = 0; i < item.source_def.length; i++) {
			if (item.source_def[i][2]) {
				view_fields.push(item.source_def[i][0]);
			}
		}
		item.source.set_view_fields(view_fields);
	
		view_fields = []
		for (i = 0; i < item.dest_def.length; i++) {
			if (item.dest_def[i][2]) {
				view_fields.push(item.dest_def[i][0]);
			}
		}
		item.dest.set_view_fields(view_fields);
	
		item.left_grid = item.dest.create_table(item.view_form.find("#left-grid"), {
			height: 360,
			column_width: name_width,
			dblclick_edit: false
		});
		item.right_grid = item.source.create_table(item.view_form.find("#right-grid"), {
			height: 360,
			dblclick_edit: false
		});
	//	prepare_grids(item);
		item.left_grid.$table.keydown(function(e) {
			var code = (e.keyCode ? e.keyCode : e.which);
			if (code === 32) {
				e.preventDefault();
				move_right(item);
			}
		});
		item.right_grid.$table.keydown(function(e) {
			var code = (e.keyCode ? e.keyCode : e.which);
			if (code === 32) {
				e.preventDefault();
				move_left(item);
			}
		});
		if (!item.can_move) {
			item.view_form.find("#vert-btns-box").hide();
		}
		item.view_form.find("#up-btn").attr('tabindex', -1).click(function() {
			item.task.move_record_up(item.dest);
		});
		item.view_form.find("#down-btn").attr('tabindex', -1).click(function() {
			item.task.move_record_down(item.dest);
		});
		item.view_form.find("#left-btn").attr('tabindex', -1).click(function() {move_left(item);});
		item.view_form.find("#right-btn").attr('tabindex', -1).click(function() {move_right(item);});
		item.view_form.find("#cancel-btn")
			.attr("tabindex", 101)
			.text(item.task.language.cancel)
			.on('click.task', function(e) {item_cancel(item);});
		item.view_form.find("#ok-btn")
			.attr("tabindex", 100)
			.text(item.task.language.ok)
			.on('click.task', function() {save_result(item)});
		if (item.read_only) {
			item.view_form.find("button.arrow_btn").hide();
		}
		item.left_grid.$table.on('click', 'td', function() {
			var $td = $(this),
				field_name = $td.data('field_name'),
				field = item.dest.field_by_name(field_name);
			if (field.field_type === "boolean") {
				if (!item.dest.is_changing()) {
					item.dest.edit();
				}
				field.value = !field.value;
				item.dest.post();
			}
		})
	}
	
	function on_view_form_shown(item) {
		prepare_grids(item);
		item.right_grid.focus();
	}
	
	function prepare_grids(item) {
		var i,
			j,
			k,
			s,
			d,
			found;
		item.source.disable_controls();
		try {
			item.source.open({open_empty: true});
			for (i = 0; i < item.source_def.length; i++) {
				if (item.source_def[i][2]) {
					item.source.field_by_name(item.source_def[i][0]).field_caption = item.source_def[i][1];
				}
			}
			for (i = 0; i < item.source_list.length; i++) {
				s = item.source_list[i];
				found = false;
				for (j = 0; j < item.dest_list.length; j++) {
					d = item.dest_list[j];
					if (s[0] === d[0]) {
						found = true;
						break;
					}
				}
				if (!found) {
					item.source.append();
					for (k = 0; k < item.source_def.length; k++) {
						item.source.field_by_name(item.source_def[k][0]).value = s[k];
					}
					item.source.post();
				}
			}
			item.source.first();
		}
		finally {
			item.source.enable_controls();
		}
		item.source.update_controls();
	
		item.dest.disable_controls();
		try {
			item.dest.open({open_empty: true});
			for (i = 0; i < item.dest_def.length; i++) {
				if (item.dest_def[i][2]) {
					item.dest.field_by_name(item.dest_def[i][0]).field_caption = item.dest_def[i][1];
				}
			}
			for (i = 0; i < item.dest_list.length; i++) {
				d = item.dest_list[i];
				found = false;
				for (j = 0; j < item.source_list.length; j++) {
					s = item.source_list[j];
					if (s[0] === d[0]) {
						found = true;
						break;
					}
				}
				if (found) {
					item.dest.append();
					item.dest.id.value = s[0];
					item.dest.name.value = s[1];
					for (k = 2; k < item.dest_def.length; k++) {
						item.dest.field_by_name(item.dest_def[k][0]).value = d[k - 1];
					}
					item.dest.post();
				}
			}
			item.dest.first();
		}
		finally {
			item.dest.enable_controls();
		}
		item.dest.update_controls();
	}
	
	function move_hor(source, dest) {
		if (source.record_count()) {
			dest.append();
			dest.id.value = source.id.value;
			dest.name.value = source.name.value;
			dest.post();
			source.delete();
		}
	}
	
	function move_left(item) {
		move_hor(item.source, item.dest);
	}
	
	function move_right(item) {
		move_hor(item.dest, item.source);
	}
	
	function save_result(item) {
		var dest_list = [],
			rec = item.dest.rec_no;
		item.dest.disable_controls();
		try {
			item.dest.each(function(d) {
				var k,
					rec = []
				rec.push(d.id.value);
				for (k = 2; k < item.dest_def.length; k++) {
					rec.push(item.dest.field_by_name(item.dest_def[k][0]).value);
				}
				dest_list.push(rec);
			});
		}
		finally {
			item.dest.rec_no = rec;
			item.dest.enable_controls();
		}
	
		item.save_func(item.item, dest_list)
		item.close_view_form();
	}
	
	function on_view_form_close_query(item) {
		if (item.item.is_changing()) {
			if (item.cancel_func) {
				item.cancel_func(item.item);
			}
		}
	}
	
	function on_view_form_closed(item) {
		item.task.editing_finished();
	}
	
	function item_cancel(item) {
		item.close_view_form();
	}
	
	function on_view_form_keydown(item, event) {
		if (event.keyCode === 13){
			event.preventDefault();
			save_result(item);
		}
	}
	this.fields_editor = fields_editor;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.prepare_grids = prepare_grids;
	this.move_hor = move_hor;
	this.move_left = move_left;
	this.move_right = move_right;
	this.save_result = save_result;
	this.on_view_form_close_query = on_view_form_close_query;
	this.on_view_form_closed = on_view_form_closed;
	this.item_cancel = item_cancel;
	this.on_view_form_keydown = on_view_form_keydown;
}

task.events.events15 = new Events15();

function Events11() { // admin.catalogs.sys_params 

	function on_after_apply(item) {
		if (item.task.init_project && item.f_language.value) {
			item.task.server('server_set_project_langage', [item.f_language.value])
			location.reload();
		}
		else {
			if (item._safe_mode !== item.f_safe_mode.value) {
	//			item.task.editing_finished();
				item.task.logout();
				location.reload();
			}
			else {
				item.task.update_task_info(item.task);
			}
		}
	}
	
	function init_edit_options(item, options) {
		if (item.params === true) {
			item.edit_options.width = 460;
			options.controls_margin_left = 220;
			options.label_width = 200;
		}
		else if (item.params === false) {
			item.edit_options.width = 560;
			options.controls_margin_left = 380;
			options.label_width = 360;
		}
	}
	
	function on_field_validate(field) {
		if (field.field_name === 'f_con_pool_size' && field.value < 1) {
			return 'The Connection pool size value must be greater than zero';
		}
	}
	
	function on_before_apply(item) {
		item.task.editing_finished(item);
	}
	
	function on_after_edit(item) {
		item._safe_mode = item.f_safe_mode.value;
	}
	
	function on_edit_form_closed(item) {
		item.task.editing_finished();
	}
	this.on_after_apply = on_after_apply;
	this.init_edit_options = init_edit_options;
	this.on_field_validate = on_field_validate;
	this.on_before_apply = on_before_apply;
	this.on_after_edit = on_after_edit;
	this.on_edit_form_closed = on_edit_form_closed;
}

task.events.events11 = new Events11();

function Events16() { // admin.catalogs.sys_search 

	function find_in_task(task) {
		var search = task.sys_search.copy()
		search.open({open_empty: true});
		search.set_edit_fields(['find_text', 'case_sensitive', 'whole_words']);
		search.append_record();
	}
	
	function on_edit_form_created(item) {
		item.edit_form.title = task.language.find;
		item.edit_form.find("#cancel-btn")
			.text(task.language.close)
			.attr("tabindex", 101);
		item.edit_form.find("#ok-btn")
			.text(task.language.find)
			.attr("tabindex", 100)
			.off('click.task')
			.on('click', function() {find(item)});
	}
	
	function find(item) {
		var result,
			i,
			$p,
			lines,
			width = $(window).width() - 50,
			height = $(window).height() - 200,
			html = $('<div>');
		if (item.find_text.value) {
			result = item.task.server('server_find_in_task',
				[item.task.sys_tasks.task_id.value, item.find_text.value, item.case_sensitive.value, item.whole_words.value]);
			if (result) {
				html.append($('<h4>Client</h4>'));
				lines = result.client.split('\n')
				for (i = 0; i < lines.length; i++) {
					$p = $('<p style="margin: 0px;">').text(lines[i]);
					$p.css("font-family", "'Courier New', Courier, monospace")
					html.append($p);
				}
				html.append($('<h4>Server</h4>'));
				lines = result.server.split('\n')
				for (i = 0; i < lines.length; i++) {
					$p = $('<p style="margin: 0px;">').text(lines[i]);
					$p.css("font-family", "'Courier New', Courier, monospace")
					html.append($p);
				}
				task.message(html,
					{title: 'Search result', margin: 10, width: width, height: height,
						text_center: false, buttons: {"Close": undefined}, center_buttons: false, print: true}
				)
			}
		}
	}
	
	function on_edit_form_keydown(item, event) {
		if (event.keyCode === 13){
			event.preventDefault();
			item.edit_form.find("#ok-btn").focus();
			find(item);
		}
	}
	this.find_in_task = find_in_task;
	this.on_edit_form_created = on_edit_form_created;
	this.find = find;
	this.on_edit_form_keydown = on_edit_form_keydown;
}

task.events.events16 = new Events16();

function Events18() { // admin.catalogs.sys_lookup_lists 

	function init_view_table(item, options) {
		item.view_options.width = 400;
		options.height = 400;
	}
	
	function can_delete(item) {
		return item.task.server('server_can_delete_lookup_list', item.id.value);
	}
	
	function on_view_form_created(item) {
		item.view_form.find("#select-btn").hide();
		item.view_form.find('#delete-btn').off('click.task').on('click', function() {
			item.question(item.task.language.delete_record, function() {
				var error = can_delete(item);
				if (error) {
					item.warning(error);
				}
				else {
					item.delete();
					item.apply();
				}
			})
		});
	
	}
	
	function on_edit_form_created(item) {
		var lookups = item.task.sys_field_lookups.copy();
		item.lookups = lookups;
		init_lookups(item);
		item.edit_form.find("#new-btn").attr("tabindex", 92).on('click.task', function() {lookups.append_record()});
		item.edit_form.find("#edit-btn").attr("tabindex", 91).on('click.task', function() {lookups.edit_record()});
		item.edit_form.find("#delete-btn").attr("tabindex", 90).on('click', function() {lookups.delete_record()});
	
		item.edit_table = lookups.create_table(item.edit_form.find(".edit-detail"),
			{
				height: 300,
				tabindex: 90,
				column_width: {f_value: '15%'},
				sortable: true
			});
	}
	
	function init_lookups(item) {
		var list = [];
		item.lookups.open({open_empty: true});
		if (!item.is_new()) {
			list = JSON.parse(item.f_lookup_values_text.value);
			for (var i = 0; i < list.length; i++) {
				item.lookups.append();
				item.lookups.f_value.value = list[i][0];
				item.lookups.f_lookup.value = list[i][1];
				item.lookups.post();
			}
		}
	}
	
	function on_before_post(item) {
		var list = [];
		item.lookups.each(function(l) {
			list.push([l.f_value.value, l.f_lookup.value]);
		});
		item.f_lookup_values_text.value = JSON.stringify(list);
	}
	
	function on_view_form_closed(item) {
		item.task.editing_finished();
	}
	this.init_view_table = init_view_table;
	this.can_delete = can_delete;
	this.on_view_form_created = on_view_form_created;
	this.on_edit_form_created = on_edit_form_created;
	this.init_lookups = init_lookups;
	this.on_before_post = on_before_post;
	this.on_view_form_closed = on_view_form_closed;
}

task.events.events18 = new Events18();

function Events5() { // admin.tables.sys_filters 

	function on_view_form_created(item) {
		item.view_form.find('#up-btn').click(function() {
			item.task.move_record_up(item);
		});
		item.view_form.find('#down-btn').click(function() {
			item.task.move_record_down(item);
		});
	}
	
	function on_view_form_shown(item) {
	//	var btn_width = 0
	//	item.view_form.find('.btn').each(function() {
	//		btn_width += $(this).outerWidth();
	//	})
	//	item.view_form.find('#up-btn').css('margin-left', (item.view_form.find('.modal-footer').innerWidth() - btn_width) / 2 );
	}
	
	function on_edit_form_created(item) {
		item.edit_form.find('textarea.f_help').attr('rows', 3).height(40);
		update_multi_select_all(item);
	}
	
	function update_multi_select_all(item) {
		item.f_multi_select_all.read_only = item.f_type.value !== item.task.consts.FILTER_IN &&
			item.f_type.value !== item.task.consts.FILTER_NOT_IN;
		if (item.f_multi_select_all.read_only && item.is_changing()) {
			item.f_multi_select_all.value = false;
		}
	}
	
	function on_after_append(item) {
		item.task_id.value = item.task.sys_items.task_id.value;
		item.owner_id.value = 0;
		item.f_visible.value = true;
		item.f_index.value = item.record_count();
		item.f_type.value = 1;
	}
	
	
	function on_before_post(item) {
		item.owner_rec_id.value = item.task.sys_items.id.value
		item.owner.value = item.task.sys_items.ID
	}
	
	function on_field_changed(field, lookup_item) {
		var fields,
			item = field.owner;
		if (field.field_name === 'f_field') {
			fields = item.task.sys_fields.copy()
			fields.set_where({id: field.value});
			fields.open();
			item.f_name.value = fields.f_name.value;
			item.f_filter_name.value = fields.f_field_name.value;
			item.f_help.value = fields.f_help.value;
		}
		update_multi_select_all(item);
	}
	
	function on_field_select_value(field, lookup_item) {
		var items,
			item = field.owner;
		if (field.field_name === 'f_field') {
			items = item.copy();
			lookup_item.filters.owner_rec_id.value = [item.task.sys_items.id.value, item.task.sys_items.parent.value];
			lookup_item.filters.master_field_is_null.value = true;
			lookup_item.set_view_fields(['f_field_name', 'f_name']);
			lookup_item.set_order_by(['f_field_name']);
		}
	}
	
	function on_view_form_close_query(item) {
		var i = 0;
		item.each(function(it) {
			it.edit()
			it.f_index.value = i;
			it.post()
			i++;
		});
		item.apply();
		item.task.editing_finished();
	}
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.on_edit_form_created = on_edit_form_created;
	this.update_multi_select_all = update_multi_select_all;
	this.on_after_append = on_after_append;
	this.on_before_post = on_before_post;
	this.on_field_changed = on_field_changed;
	this.on_field_select_value = on_field_select_value;
	this.on_view_form_close_query = on_view_form_close_query;
}

task.events.events5 = new Events5();

function Events10() { // admin.tables.sys_indices 

	function on_view_form_created(item) {
		item.view_form.find("#edit-btn").text(item.task.language.view);
		if (item.filters.foreign_index.value) {
			item.f_index_name.field_caption = 'Foreign key';
			item.view_options.fields = ['f_foreign_field', 'f_index_name' ];
			item.edit_options.fields = item.view_options.fields;
			item.f_foreign_field.required = true;
			item.f_index_name.required = true;
		}
		else {
			item.f_index_name.field_caption = 'Index';
			item.view_options.fields = ['f_index_name', 'f_unique_index', 'descending'];
			item.edit_options.fields = item.view_options.fields;
			item.f_foreign_field.required = false;
			item.view_form.find("#new-btn")
				.off('click.task')
				.on('click.task', function() {
					edit_index(item, true);
				});
			item.view_form.find("#edit-btn")
				.off('click.task')
				.on('click.task', function() {
					edit_index(item, false);
				});
			item.view_table.on_dblclick = function() {
				edit_index(item, false);
			}
		}
	}
	
	function on_view_form_keydown(item, event) {
		if (event.keyCode === 45 && event.ctrlKey === true){
			event.preventDefault();
			if (item.filters.foreign_index.value) {
				item.append_record();
			}
			else {
				edit_index(item, true);
			}
		}
		else if (event.keyCode === 46 && event.ctrlKey === true){
			event.preventDefault();
			item.delete_record();
		}
	}
	
	function edit_index(item, is_new) {
		var editor,
			source_def = [],
			dest_def = [],
			index_list = [],
			title = '';
	
		function save_edit(item, dest_list) {
			var mess;
			if (is_new) {
				if (!item.f_index_name.value) {
					mess = item.task.language.index_name_required;
				}
				if (!dest_list.length) {
					mess = item.task.language.index_fields_required;
				}
				if (mess) {
					item.warning(mess);
					throw mess;
				}
				item.f_fields.value = item.server('server_dump_index_fields', [dest_list]);
				item.post()
				try {
					item.apply();
				}
				catch (e) {
					item.warning(e);
					throw e;
				}
			}
			else {
				item.read_only = false;
				item.cancel();
			}
		}
	
		function cancel_edit(item) {
			item.read_only = false;
			item.cancel();
		}
	
		function get_fields_list(task) {
			var item = task.sys_items,
				fields = item.task.sys_fields.copy(),
				parent,
				list = [];
			fields.set_where({owner_rec_id__in: [item.id.value, item.parent.value]});
			fields.set_order_by(['f_field_name']);
			fields.open({fields: ['id', 'f_field_name', 'f_master_field']});
			fields.each(function (f) {
				if (!f.f_master_field.value) {
					list.push([f.id.value, f.f_field_name.value]);
				}
			});
			return list;
		}
	
		if (is_new) {
			item.append();
			item.read_only = false;
		}
		else {
			if (item.record_count() > 0) {
				item.edit();
				item.read_only = true;
				index_list = item.server('server_load_index_fields', [item.f_fields.value]);
			}
			else {
				return
			}
		}
	
		source_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		dest_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
	
		editor = item.task.sys_fields_editor.fields_editor(item, title, source_def, get_fields_list(item.task), dest_def, index_list,
			save_edit, cancel_edit, undefined, !is_new);
		item.create_inputs(editor.view_form.find('div#fields-container'));
	}
	
	function on_after_append(item) {
		var task_name = item.task.task_name,
			item_name = item.task.sys_items.f_item_name.value;
		if (!item.filters.foreign_index.value) {
			item.f_index_name.value = task_name.toUpperCase() + '_' + item_name.toUpperCase() + '_' + 'IDX';
		}
		item.task_id.value = item.task.sys_items.task_id.value
		item.owner_rec_id.value = item.task.sys_items.id.value
		item.f_foreign_index.value = item.filters.foreign_index.value
	}
	
	function on_field_select_value(field, lookup_item) {
	
		function filter_record(item) {
			var clone,
				valid,
				soft_delete;
			if (item.f_object.value && !item.f_master_field.value) {
				soft_delete = item.task.sys_items.field_by_id(item.f_object.value, 'f_soft_delete')
				if (!soft_delete) {
					clone = field.owner.clone();
					valid = true
					clone.each(function(c) {
						if (c.f_foreign_field.value == item.id.value) {
							valid = false;
							return false;
						}
					});
					return valid;
				}
			}
		}
	
		lookup_item.view_options.fields = ['f_nane', 'f_field_name'];
		lookup_item.on_filter_record = filter_record;
		lookup_item.filtered = true;
	}
	
	function on_field_changed(field, lookup_item) {
		var item = field.owner;
		if (field.field_name === 'f_foreign_field') {
			item.f_index_name.value = 'FK_' + item.task.sys_items.f_table_name.value.toUpperCase() +
				'_' + field.display_text.toUpperCase();
		}
	}
	
	function on_field_validate(field) {
		var item = field.owner,
			error = '',
			clone;
		if (field.field_name === 'f_index_name') {
			clone = item.clone();
			clone.each(function(c) {
				if (item.rec_no !== c.rec_no && field.value === c.f_index_name.value) {
					error = 'There is index with this name';
					return false;
	
				}
			});
			if (error) {
				return error;
			}
		}
	}
	
	function on_before_apply(item) {
		return {'manual_update': item.task._manual_update};
	}
	
	function on_view_form_closed(item) {
		item.task.editing_finished();
	}
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_keydown = on_view_form_keydown;
	this.edit_index = edit_index;
	this.on_after_append = on_after_append;
	this.on_field_select_value = on_field_select_value;
	this.on_field_changed = on_field_changed;
	this.on_field_validate = on_field_validate;
	this.on_before_apply = on_before_apply;
	this.on_view_form_closed = on_view_form_closed;
}

task.events.events10 = new Events10();

function Events7() { // admin.tables.sys_privileges 

	function on_view_form_created(item) {
		item.view_options.width = 760;
		item.view_form.find("#select-all-btn")
			.text(item.task.language.select_all)
			.on('click.task', function() {select_all_clicked(item);});
		item.view_form.find("#unselect-all-btn")
			.text(item.task.language.unselect_all)
			.on('click.task', function() {unselect_all_clicked(item);});
		item.view_table.$table.on('click', 'td', function() {
			var $td = $(this),
				field_name = $td.data('field_name'),
				field = item.field_by_name(field_name);
			if (field.field_type === "boolean") {
				if (!item.is_changing()) {
					item.edit();
				}
				field.value = !field.value
			}
		})
	}
	
	function select_all_clicked(item, value) {
		var rec_no = item.rec_no;
	
		if (value === undefined) {
			value = true;
		}
		try {
			item.disable_controls();
			item.each(function(i) {
				i.edit();
				i.f_can_create.value = value;
				i.f_can_view.value = value;
				i.f_can_edit.value = value;
				i.f_can_delete.value = value;
				i.post();
			});
		}
		finally {
			item.rec_no = rec_no
			item.enable_controls();
			item.update_controls();
		}
	}
	
	function unselect_all_clicked(item) {
		select_all_clicked(item, false);
	}
	
	function on_view_form_close_query(item) {
		var copy = item.copy()
		copy.open({open_empty: true});
		item.first();
		while (!item.eof()) {
			if (item.id.value) {
				item.next();
			}
			else {
				copy.append();
				item.each_field(function(f) {
					copy.field_by_name(f.field_name).value = f.value;
					copy.id.value = null;
				})
				copy.post();
				item.delete();
			}
		};
		item.apply(function() {});
		copy.apply(function() {});
	}
	
	function on_view_form_closed(item) {
		item.task.editing_finished();
		item.task.sys_roles.server('roles_changed');
	}
	this.on_view_form_created = on_view_form_created;
	this.select_all_clicked = select_all_clicked;
	this.unselect_all_clicked = unselect_all_clicked;
	this.on_view_form_close_query = on_view_form_close_query;
	this.on_view_form_closed = on_view_form_closed;
}

task.events.events7 = new Events7();

function Events12() { // admin.tables.sys_report_params 

	function on_view_form_created(item) {
		item.task.sys_filters.on_view_form_created(item);
		item.on_field_validate = item.task.sys_items.sys_fields.on_field_validate;
	}
	
	function on_view_form_close_query(item) {
		item.task.sys_filters.on_view_form_close_query(item);
	}
	
	function on_before_post(item) {
		item.task.sys_filters.on_before_post(item);
	}
	
	function on_after_append(item) {
		item.task_id.value = item.task_id.value;
		item.f_data_type.read_only = false;
		item.f_visible.value = true;
	}
	
	function on_field_changed(field, lookup_item) {
		var item = field.owner;
		item.task.sys_items.sys_fields.on_field_changed(field, lookup_item);
		if (field.field_name === 'f_object_field') {
			if (!item.f_name.value) {
				item.f_name.value = lookup_item.f_name.value;
			}
			if (!item.f_param_name.value) {
				item.f_param_name.value = lookup_item.f_field_name.value;
			}
		}
	}
	
	function on_field_select_value(field, lookup_item) {
		field.owner.task.sys_items.sys_fields.on_field_select_value(field, lookup_item);
	}
	
	function on_edit_form_created(item) {
		item.edit_form.find('textarea.f_help').attr('rows', 3).height(40);
	}
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_close_query = on_view_form_close_query;
	this.on_before_post = on_before_post;
	this.on_after_append = on_after_append;
	this.on_field_changed = on_field_changed;
	this.on_field_select_value = on_field_select_value;
	this.on_edit_form_created = on_edit_form_created;
}

task.events.events12 = new Events12();

function Events17() { // admin.tables.sys_field_lookups 

	function on_field_validate(field) {
		if (field.field_name === 'f_value' && field.value <= 0) {
			return 'Value must be greater than zero'
		}
	}
	
	function on_view_form_closed(item) {
		item.task.editing_finished();
	}
	this.on_field_validate = on_field_validate;
	this.on_view_form_closed = on_view_form_closed;
}

task.events.events17 = new Events17();

function Events6() { // admin.catalogs.sys_items.sys_fields 

	function on_edit_form_created(item) {
	
		function check_in_foreign_index() {
			var result = false,
				indices;
			if (item.owner.id.value && item.id.value) {
				indices = item.task.sys_indices;
				indices.set_where({owner_rec_id: item.owner.id.value});
				indices.open();
				indices.each(function(ind) {
					if (ind.f_foreign_index.value && ind.f_foreign_field.value === item.id.value) {
						result = true;
					}
				});
			}
			return result;
		}
	
		item.f_field_name.read_only = item.f_field_name.value === 'id' || item.f_field_name.value === 'deleted' ||
			item.f_field_name.value === 'owner_id' || item.f_field_name.value === 'owner_rec_id';
		item.f_data_type.read_only = false;
		item.f_size.read_only = false;
		item.f_object.read_only = false;
		item.f_object_field.read_only = false;
		item.f_master_field.read_only = false;
		item.f_lookup_values.read_only = true;
	
		update_fields_read_only(item);
		if (check_in_foreign_index()) {
			item.f_object.read_only = true;
		}
		item.create_inputs(item.edit_form.find("#definition"),
			{fields: ['f_name', 'f_field_name', 'f_data_type', 'f_size', 'f_default_value', 'f_required', 'f_read_only']});
		item.create_inputs(item.edit_form.find("#lookups"),
			{fields: ['f_object', 'f_object_field', 'f_object_field1', 'f_object_field2', 'f_master_field',
				'f_enable_typehead', 'f_lookup_values']});
		item.create_inputs(item.edit_form.find("#interface"),
			{fields: ['f_alignment', 'f_placeholder', 'f_help', 'f_default']});
	
		item.edit_form.find('textarea.f_help').attr('rows', 3).height(40);
	
		item.edit_form.find("#cancel-btn")
			.text(item.task.language.cancel)
			.attr("tabindex", 101)
			.on('click.task', function(e) {item.cancel_edit(e); return false;});
		item.edit_form.find("#ok-btn")
			.attr("tabindex", 100)
			.html(item.task.language.ok + '<small class="muted">&nbsp;[Ctrl+Enter]</small>')
			.on('click.task', function() {item.apply_record()});
	}
	
	function on_edit_form_shown(item) {
		var caption = 'Field Editor';
	
		if (item.f_field_name.value) {
			item.edit_form.find('h4.modal-title').html(caption + ' <span class="editor-title">' + item.f_field_name.value + '</span>');
		}
		else {
			item.edit_form.find('h4.modal-title').html(caption);
		}
	}
	
	function on_after_open(item) {
		item._old_fields = {}
		item.disable_controls();
		try {
			item.each(function(i) {
				item._old_fields[i.id.value + ''] = true;
			})
		} finally {
			item.first()
			item.enable_controls();
		}
	}
	
	function new_field(item) {
		var result = true;
		if (item._old_fields) {
			result = !item._old_fields[item.id.value + ''];
		}
		return result;
	}
	
	function on_field_select_value(field, lookup_item) {
		var item = field.owner,
			fields,
			id_value,
			parent;
		if (lookup_item.item_name === 'sys_items') {
			lookup_item.set_view_fields(['id', 'f_item_name', 'f_name']);
			}
		else if (lookup_item.item_name === 'sys_fields') {
			lookup_item.set_order_by(['f_field_name']);
			lookup_item.set_view_fields(['f_field_name', 'f_name']);
		}
		else if (lookup_item.item_name === 'sys_lookup_lists') {
			lookup_item.set_view_fields(['f_name']);
		}
		if (field === item.f_object) {
			if (item.owner === item.task.sys_items) {
				lookup_item.filters.not_id.value = item.owner.id.value;
				if (item.owner.type_id.value === item.task.item_types.TASK_TYPE) {
					lookup_item.filters.task_id.value = item.owner.id.value;
				}
				else {
					lookup_item.filters.task_id.value = item.owner.task_id.value;
				}
			}
			lookup_item.set_order_by(['f_item_name']);
			lookup_item.filters.type_id.value = [item.task.item_types.ITEM_TYPE, item.task.item_types.TABLE_TYPE];
			lookup_item.filters.table_id.value = 0;
		}
		else if (field.field_name === 'f_master_field' && item.f_object.value) {
			id_value = item.owner.id.value;
			parent = item.task.sys_items.field_by_id(id_value, 'parent');
			if (parent) {
				lookup_item.filters.owner_rec_id.value = [parent];
				lookup_item.filters.not_id.value = item.id.value;
				lookup_item.filters.object.value = item.f_object.value;
				lookup_item.filters.master_field_is_null.value = true;
			}
			else {
				lookup_item.filters.owner_rec_id.value = [-1];
			}
			lookup_item.set_fields(['id', 'f_name', 'f_field_name'])
			lookup_item.on_after_open = function(it) {
				var clone = item.clone()
				it.first();
				clone.each(function(c) {
					if (c.id.value !== item.id.value &&
						c.f_object.value === item.f_object.value &&
						!c.f_master_field.value) {
						it.append();
						it.id.value = c.id.value;
						it.f_field_name.value = c.f_field_name.value;
						it.f_name.value = c.f_name.value;
						it.post();
					}
				});
				it.first();
			}
		}
		if (field.field_name === 'f_object_field') {
			if (item.f_object.value) {
				id_value = item.f_object.value;
				parent = item.task.sys_items.field_by_id(id_value, 'parent');
				lookup_item.filters.owner_rec_id.value = [id_value, parent];
				lookup_item.filters.master_field_is_null.value = true;
				lookup_item.set_order_by(['f_field_name']);
			}
			else {
				lookup_item.filters.owner_rec_id.value = [-1];
			}
		}
		if (field.field_name === 'f_object_field1') {
			fields = item.task.sys_fields.copy();
			fields.set_where({id: item.f_object_field.value})
			fields.open();
			if (fields.f_object.value) {
				id_value = fields.f_object.value;
				parent = fields.task.sys_items.field_by_id(id_value, 'parent');
				lookup_item.filters.owner_rec_id.value = [id_value, parent];
				lookup_item.filters.master_field_is_null.value = true;
				lookup_item.set_order_by(['f_field_name']);
			}
			else {
				lookup_item.filters.owner_rec_id.value = [-1];
			}
		}
		if (field.field_name === 'f_object_field2') {
			fields = item.task.sys_fields.copy();
			fields.set_where({id: item.f_object_field1.value})
			fields.open();
			if (fields.f_object.value) {
				id_value = fields.f_object.value;
				parent = fields.task.sys_items.field_by_id(id_value, 'parent');
				lookup_item.filters.owner_rec_id.value = [id_value, parent];
				lookup_item.filters.master_field_is_null.value = true;
				lookup_item.set_order_by(['f_field_name']);
			}
			else {
				lookup_item.filters.owner_rec_id.value = [-1];
			}
		}
	}
	
	function check_valid_field_name(item, field_name) {
		var error = '',
			clone,
			field,
			check_item;
		if (!item.owner.valid_identifier(field_name)) {
			error = item.task.language.invalid_field_name
		}
		clone = item.clone()
		clone.each(function(c) {
			if (item.rec_no !== c.rec_no && field_name === c.f_field_name.value) {
				error = 'There is a field with this name';
				return false;
			}
		});
		if (!error) {
			check_item = new item.task.constructors.item();
			if (check_item[field_name] !== undefined) {
				error = item.task.language.reserved_word;
			}
		}
		if (!error) {
			field = item.id;
			if (field_name === 'id') {
				field = item.deleted;
			}
			if (field[field_name] !== undefined) {
				error = item.task.language.reserved_word;
			}
		}
		return error;
	}
	
	function on_field_validate(field) {
		var item = field.owner,
			error = '';
		if (field.field_name === 'f_field_name') {
			error = check_valid_field_name(item, field.value);
			if (error) {
				return error;
			}
		}
		else if (field.field_name === 'f_object_field') {
			if (item.f_object.value && !field.value) {
				return item.task.language.object_field_required;
			}
		}
		else if (field.field_name === 'f_data_type' && item.f_data_type.value === 0) {
			return item.task.language.type_is_required;
		}
	}
	
	function on_field_changed(field) {
		var item = field.owner,
			ident;
		if (!item._field_changing) {
			item._field_changing = true;
			try {
				if (field.field_name === 'f_name') {
					if (item.f_field_name) {
						if (!item.f_field_name.value) {
							try {
								ident = field.text.replace(' ', '_').toLowerCase();
								if (item.owner.valid_identifier(ident)) {
									item.f_field_name.value = ident;
								}
							}
							catch (e) {
							}
						}
					}
					else if (item.f_param_name) {
						if (!item.f_param_name.value) {
							try {
								ident = field.text.replace(' ', '_').lower();
								if (item.owner.valid_identifier(ident)) {
									item.f_param_name.value = ident;
								}
							}
							catch (e) {
							}
						}
					}
				}
				else if (field.field_name === 'f_object') {
					item.f_object_field.value = null;
					item.f_object_field1.value = null;
					item.f_object_field2.value = null;
					item.f_lookup_values.value = null;
					item.f_master_field.value = null;
					if (item.f_object.value) {
						item.f_data_type.value = item.task.consts.INTEGER;
					}
				}
				else if (field.field_name === 'f_object_field') {
					item.f_object_field1.value = null;
					item.f_object_field2.value = null;
				}
				else if (field.field_name === 'f_object_field1') {
					item.f_object_field2.value = null;
				}
				else if (field.field_name === 'f_lookup_values') {
					item.f_object.value = null;
					item.f_object_field.value = null;
					item.f_master_field.value = null;
					if (item.f_lookup_values.value) {
						item.f_data_type.value = item.task.consts.INTEGER;
					}
				}
				else if (field === item.f_data_type) {
					if (item.f_data_type.value === item.task.consts.TEXT) {
						item.f_size.value = 10;
					}
					else {
						item.f_size.value = null;
					}
				}
				if (field === item.f_data_type || field === item.f_object || field === item.f_lookup_values) {
					item.f_alignment.value = get_alignment(item);
				}
				update_fields_read_only(item);
			}
			finally {
				item._field_changing = false;
			}
		}
	}
	
	function update_fields_read_only(item) {
		if (!new_field(item) && !item.owner.f_virtual_table.value && !item.task._manual_update) {
			item.f_data_type.read_only = !item.task.db_options.CAN_CHANGE_TYPE;
			item.f_size.read_only = true;
			if (item.f_data_type.value === item.task.consts.TEXT) {
				item.f_size.read_only = !item.task.db_options.CAN_CHANGE_SIZE;
			}
			item.f_object.read_only = true;
			item.f_object_field.read_only = true;
			item.f_master_field.read_only = true;
			item.f_lookup_values.read_only = true;
			if (item.f_data_type.value === item.task.consts.INTEGER) {
				item.f_object.read_only = false;
				item.f_object_field.read_only = false;
				item.f_master_field.read_only = false;
				item.f_lookup_values.read_only = false;
			}
		}
		else {
			if (!item.f_data_type.value) {
				item.f_data_type.read_only = false;
				item.f_lookup_values.read_only = false;
				item.f_object.read_only = false;
				item.f_object_field.read_only = false;
				item.f_master_field.read_only = false;
			}
			else if (item.f_data_type.value === item.task.consts.INTEGER) {
				if (item.f_object.value) {
					item.f_data_type.read_only = true;
				}
				else if (item.f_lookup_values.value) {
					item.f_data_type.read_only = true;
				}
				else {
					item.f_data_type.read_only = false;
					item.f_lookup_values.read_only = false;
					item.f_object.read_only = false;
					item.f_object_field.read_only = false;
					item.f_master_field.read_only = false;
				}
			}
			else {
				item.f_object.read_only = true;
				item.f_object_field.read_only = true;
				item.f_master_field.read_only = true;
				item.f_lookup_values.read_only = true;
			}
			if (item.f_data_type.value === item.task.consts.TEXT) {
				item.f_size.read_only = false;
			}
			else {
				item.f_size.read_only = true;
			}
		}
		update_lookup_attr(item);
	}
	
	function update_lookup_attr(item) {
		item.f_object_field.read_only = !item.f_object.value;
		item.f_object_field1.read_only = !item.f_object_field.value;
		item.f_object_field2.read_only = !item.f_object_field1.value;
		item.f_master_field.read_only = !item.f_object_field.value;
		item.f_multi_select.read_only = true;
		item.f_enable_typehead.read_only = true;
		if (item.f_object.value && !item.f_master_field.value) {
			item.f_multi_select.read_only = false;
			item.f_enable_typehead.read_only = false;
		}
		if (item.f_enable_typehead.value) {
			item.f_multi_select.read_only = true;
		}
		if (item.f_multi_select.value) {
			item.f_enable_typehead.read_only = true;
		}
		item.f_multi_select_all.read_only = !item.f_multi_select.value;
		if (item.is_changing()) {
			if (item.f_multi_select.read_only) {
				item.f_multi_select.value = null;
				item.f_multi_select_all.value = null;
			}
			if (!item.f_multi_select.value) {
				item.f_multi_select_all.value = null;
			}
			if (item.f_enable_typehead.read_only) {
				item.f_enable_typehead.value = null;
			}
		}
	}
	
	function get_alignment(item) {
		var data_type = item.f_data_type.value,
			result;
		if (data_type === item.task.consts.INTEGER ||
			data_type === item.task.consts.FLOAT ||
			data_type === item.task.consts.CURRENCY) {
			result = item.task.consts.ALIGN_RIGHT;
		}
		else if (data_type === item.task.consts.DATE ||
			data_type === item.task.consts.DATETIME) {
			result = item.task.consts.ALIGN_CENTER;
		}
		else {
			result = item.task.consts.ALIGN_LEFT;
		}
		if (item.f_object.value || item.f_lookup_values.value) {
			result = item.task.consts.ALIGN_LEFT;
		}
		return result;
	}
	
	function can_delete(item) {
		var error,
			clone;
		if (item.f_object.value) {
			clone = item.clone()
			clone.each(function(c) {
				if (c.f_object.value === item.f_object.value && c.f_master_field.value === item.id.value) {
					error = 'You can not delete the <b>' + item.f_field_name.value +
						'</b>field. It is a master field to the <b>' + c.f_field_name.value + '.</b> field';
					return false;
				}
			})
		}
		if (!error && !new_field(item)) {
			error = item.task.sys_fields.server('server_can_delete_field', [item.id.value]);
		}
		return error
	}
	
	function on_after_append(item) {
		item.f_data_type.read_only = false;
	}
	
	function on_before_delete(item) {
		if (item.id.value === item.owner.f_primary_key.value) {
			item.owner.f_primary_key.value = null;
		}
		else if (item.id.value === item.owner.f_deleted_flag.value) {
			item.owner.f_deleted_flag.value = null;
		}
		else if (item.id.value === item.owner.f_master_id.value) {
			item.owner.f_master_id.value = null;
		}
		else if (item.id.value === item.owner.f_master_rec_id.value) {
			item.owner.f_master_rec_id.value = null;
		}
	}
	
	function on_before_post(item) {
		if (item.f_data_type.value !== item.task.consts.TEXT) {
			item.f_size.value = null;
		}
		item.task_id.value = item.task.item_tree.task_id.value;
		if (!item.id.value) {
			item.id.value = item.task.server('get_fields_next_id');
		}
	}
	
	function on_before_edit(item) {
	
	}
	
	function on_get_field_text(field) {
		if (field.field_name === 'f_size' && field.value === 0) {
			return '';
		}
	}
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_shown = on_edit_form_shown;
	this.on_after_open = on_after_open;
	this.new_field = new_field;
	this.on_field_select_value = on_field_select_value;
	this.check_valid_field_name = check_valid_field_name;
	this.on_field_validate = on_field_validate;
	this.on_field_changed = on_field_changed;
	this.update_fields_read_only = update_fields_read_only;
	this.update_lookup_attr = update_lookup_attr;
	this.get_alignment = get_alignment;
	this.can_delete = can_delete;
	this.on_after_append = on_after_append;
	this.on_before_delete = on_before_delete;
	this.on_before_post = on_before_post;
	this.on_before_edit = on_before_edit;
	this.on_get_field_text = on_get_field_text;
}

task.events.events6 = new Events6();

function Events8() { // admin.catalogs.sys_roles.sys_privileges 

	function on_field_changed(field, lookup_item) {
		var item = field.owner;
		item.post();
		item.owner.post();
		if (item.id.value) {
			item.record_status = item.task.consts.RECORD_MODIFIED;
		}
		else {
			item.record_status = item.task.consts.RECORD_INSERTED;
		}
		item.owner.apply();
		item.owner.edit();
	}
	this.on_field_changed = on_field_changed;
}

task.events.events8 = new Events8();

})(jQuery, task)