(function($, task) {
"use strict";

function Events1() { // app_builder 

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
		};
	
	function tree_changed(item) {
		var div;
		task.btns_panel.show();
		item.task.cur_item_title = item.f_name.value;
		if (item.type_id.value === item_types.ROOT_TYPE) {
			task.view_panel.empty();
			task.view_panel.append('<div class="admin-task-info"></div>');
			update_task_info(task);
			task.right_panel.show();
			task.btns_panel.empty();
			create_params_btn(item.task);
		}
		else if (item.type_id.value === item_types.USERS_TYPE) {
			task.right_panel.hide();
			item.task.sys_users.view_options.fields = ['id', 'f_name', 'f_login', 'f_password', 'f_role', 'f_admin'];
			item.task.sys_users.edit_options.fields = ['f_name', 'f_login', 'f_password', 'f_role', 'f_admin'];
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
		task.item_tree.set_order_by(['f_index']);
		task.item_tree.open({fields: ['id', 'parent', 'f_name', 'f_item_name', 'type_id', 'task_id', 'f_index']});
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
		task._production = task.sys_params.f_production.value;
	}
	
	function refresh_task_dict(task) {
		task.server('server_get_task_dict', function(result) {
			task.task_dict = result[0];
			task.task_item_fields = result[1];
		});
	}
	
	function on_page_loaded(task)  {
		var items,
			error,
			fields;
	
		task._manual_update = false;
		task.init_project = true;
		task.item_types = item_types;
		task.old_forms = true;
	
		open_sys_params(task);
		if (!task.sys_params.f_language.value) {
			task.sys_params.edit_options.title = 'Project language';
			task.sys_params.edit_options.fields = ['f_language'];
			task.sys_params.edit_record();
			return;
		}
	
		task.sys_tasks.open();
		if (!task.sys_tasks.f_db_type.value) {
			fields = ['f_name', 'f_item_name', 'f_db_type', 'f_server', 'f_alias', 'f_login',
				'f_password', 'f_host', 'f_port', 'f_encoding'];
			task.sys_tasks.set_edit_fields(fields);
			task.server('server_set_project_langage', [task.sys_params.f_language.value]);
			task.sys_tasks.edit_options.help_link = 'http://jam-py.com/docs/intro/new_project.html'; 
			task.sys_tasks.edit_options.title = task.language.project_params;
			task.sys_tasks.edit_record();
			return;
		}
	
		if (task.sys_params.f_language.value && task.sys_tasks.f_db_type.value) {
			task.init_project = false;
			task.server('server_get_db_options', [task.sys_tasks.f_db_type.value], function(result) {
				task.db_options = result[0];
				error = result[1];
				if (error) {
					task.warning(error);
					return;
				}
			});
	
			task.buttons_info = {
				divider: {},
				project_params: {handler: set_project_params, short_cut: 'F2', key_code: 113, editor: true},
				db:			 {handler: edit_database, short_cut: 'F4', key_code: 115, editor: true},
				'export':		 {handler: export_task, short_cut: 'Ctrl-E', key_code: 69, key_ctrl: true},
				'import':		 {handler: import_task, short_cut: 'Ctrl-I', key_code: 73, key_ctrl: true},
				find:			 {handler: find_in_task, short_cut: 'Alt-F', key_code: 70, key_alt: true},
				print:		   {handler: print_code},
				client_module:   {handler: task.sys_items.edit_client, item: task.sys_items, short_cut: 'F8', key_code: 119, editor: true},
				server_module:   {handler: task.sys_items.edit_server, item: task.sys_items, short_cut: 'F9', key_code: 120, editor: true},
				'index.html':	 {handler: task.sys_items.edit_index_html, item: task.sys_items, short_cut: 'F10', key_code: 121, editor: true},
				'project.css':   {handler: task.sys_items.edit_project_css, item: task.sys_items, short_cut: 'F11', key_code: 122, editor: true},
				'Lookup lists': {handler: show_lookup_lists, editor: true},
				viewing:		   {handler: task.sys_items.view_setup, item: task.sys_items, editor: true},
				editing:		   {handler: task.sys_items.edit_setup, item: task.sys_items, editor: true},
				filters:		   {handler: task.sys_items.filters_setup, item: task.sys_items, editor: true},
				details:		   {handler: task.sys_items.details_setup, item: task.sys_items, editor: true},
				order:		   {handler: task.sys_items.order_setup, item: task.sys_items, editor: true},
				indices:		   {handler: task.sys_items.indices_setup, item: task.sys_items, editor: true},
				foreign_keys:	 {handler: task.sys_items.foreign_keys_setup, item: task.sys_items, editor: true},
				reports:		   {handler: task.sys_items.reports_setup, item: task.sys_items, editor: true},
				report_params:   {handler: task.sys_items.report_params_setup, item: task.sys_items, editor: true, short_cut: 'F7', key_code: 118, editor: true},
				privileges:	 {handler: task.sys_items.privileges_setup, item: task.sys_items, editor: true},
				'Prepare files': {handler: task.prepare_files}
			};
	
			$("#content").show();
			$("#title").html('Application builder');
			if (task.safe_mode) {
				$("#user-info").text(task.user_info.role_name + ' ' + task.user_info.user_name);
				$('#log-out').show().click(function(e) {
					e.preventDefault();
					task.logout();
				});
			}
	
			task.left_panel = $("#left-panel");
			task.center_panel = $("#center-panel");
			task.right_panel = $("#right-panel");
			task.btns_panel = $("#btns-panel");
			task.view_panel = $("#view-panel");
			task.tree_panel = $("#tree-panel");
			task.code_editor = $("#code-editor");
	
			task.sys_code_editor.init_tabs(task);
	
			task.item_tree = task.sys_items.copy({handlers: false, details: false});
	
			task.item_tree.on_field_get_text = function(f) {
				if (f.field_name === 'f_name') {
					if (f.owner.type_id.value === item_types.TASK_TYPE) {
						return task.language.groups;
					}
				}
			};
	//		task.item_tree.on_after_open = function(t) {
	//			t.locate('type_id', item_types.TASK_TYPE);
	//			t.edit();
	//			t.f_name.value = task.language.groups;
	//			t.post();
	//		};
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
			refresh_task_dict(task);
			update_db_manual_mode(task);
	
			$(window).on('focus.task', function(e) {
				update_task_info(task);
			});
			$(window).on('resize.task', function() {
				resize(task);
			});
	
			resize_elements(task);
		}
	}
	
	var timeOut;
	
	function resize(task) {
		clearTimeout(timeOut);
		timeOut = setTimeout(
			function() {
				resize_elements(task);
			},
			100
		);
	}
	
	function resize_elements(task) {
		var height = $(window).height() -
			($('#task-tabs').offset().top + $('#task-tabs').outerHeight(true)) - 15;
		resize_panels(task, height);
		resize_editor(task, height);
		if ($('ul#task-tabs li.active').attr('id') === 'admin') {
			resize_item(task, height);
			task.sys_items.update_controls();
		}
	}
	
	function resize_panels(task, height) {
		var dbtree = $('#left-panel #tree-panel .dbtree');
		if (task.tree_panel.outerHeight(true) !== height) {
			dbtree.hide();
			task.tree_panel.outerHeight(height, true);
			task.right_panel.outerHeight(height, true);
			height = task.tree_panel.height();
			dbtree.outerHeight(task.tree_panel.height(), true);
			dbtree.show();
			task.btns_panel.outerHeight(task.right_panel.height(), true);
		}
	}
	
	function resize_item(task, height) {
		var dbtable = $('#center-panel .dbtable'),
			header_height = $('#center-panel .title').outerHeight(true),
			footer_height = $('#center-panel .modal-footer').outerHeight(true),
			table;
		if (dbtable.length) {
			table = dbtable.data('dbtable');
			if (table.height() !== height - header_height - footer_height) {
				table.height(height - header_height - footer_height);
			}
		}
	}
	
	function resize_editor(task, height) {
		task.sys_code_editor.resize(task, height);
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
			handler.call(it, it, task.language[caption]);
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
		var btn_list =
			[
				'project_params',
				'divider',
				'db',
				'divider',
				'export',
				'import',
				'divider',
				'find',
				'print'
			];
		if (task.item_name !== 'admin') {
			btn_list.push('divider');
			btn_list.push('Prepare files');
		}
		add_buttons(task, btn_list);
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
			task.server_started = res[4];
			task.cur_task_info = '<h4 class="editor-title"><span>' +
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
	
		item.view_options.refresh_button = false;
	
		if (item.item_name === 'sys_fields_editor' || item.item_name === 'sys_code_editor' ||
			item.item_name === 'sys_lang') {
			return
		}
		item.paginate = false;
		if (item.view_form.hasClass('modal')) {
			item.view_form.find("#select-btn").on('click.task', function() {item.set_lookup_field_value();});
			item.view_options.width = 1170;
			table_height = 480;
			if (item.item_name === 'sys_items' || item.item_name === 'sys_fields') {
				item.view_options.width = 560;
				item.view_form.find('.title').hide();
				if (item.view_form.find('.sys_items_system').length) {
					item.task.sys_params.init_lookup_form(item);
				}
				else {
					item.view_form.find('.modal-footer').hide();
				}
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
			item.view_options.close_on_escape = false;
			task.cur_item = item;
			item.view_form.find(".modal-body").css('padding', 0);
			item.view_form.find("#title-left").html('<h4 class="editor-title">' + '<span>' + task.cur_item_title + '</span>' + '</h4>');
			item.view_form.find("#select-btn").hide()
			table_height = task.center_panel.height() - 104;
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
			if (!item.view_form.hasClass('modal') && item.item_name === 'sys_items') {
				resize_elements(task);
			}
		}
		create_print_btns(item);
	}
	
	function on_view_form_shown(item) {
		if (item.item_name === 'sys_fields_editor' || item.item_name === 'sys_code_editor') {
			return
		}
		if (item ===item.task.sys_privileges) {
			item.open({params: {item_id: item.task.sys_items.id.value}});
		}
		else if (item.item_name === 'sys_items') {
			item.open({fields: [
				'id', 'deleted', 'parent', 'task_id', 'type_id', 'table_id', 'has_children', 'f_index',
				'f_name', 'f_item_name', 'f_table_name', 'f_gen_name', 'f_view_template', 'f_visible', 
				'f_soft_delete', 'f_record_version', 'f_virtual_table', 'f_js_external',
				'f_primary_key', 'f_deleted_flag', 'f_master_id', 'f_master_rec_id',
				'f_keep_history', 'f_edit_lock', 'sys_id'
			]});
			resize_elements(task);
		}
		else {
			item.open();
		}
		if (item.active) {
			item.view_table.focus();
		}
	}
	
	function set_btn_lang(form) {
		var changes = ['Cancel', 'OK', 'Delete', 'Edit', 'New']
		form.find('button.btn').each(function() {
			var $this = $(this),
				text = $this.text(),
				i;
			for (i = 0; i < changes.length; i++) {
				if (text.indexOf(changes[i]) !== -1) {
					$this.text($this.text().replace(changes[i], task.language[changes[i].toLowerCase()]))
				}
			}
		});
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
				.on('click.task', function(e) {item.cancel_edit(e); return false;});
			item.edit_form.find("#ok-btn")
				.text(item.task.language.ok)
				.on('click.task', function() {item.apply_record()});
		}
		set_btn_lang(item.edit_form);
	}
	
	function on_edit_form_shown(item) {
		if (item.edit_options.help_link) {
			item.edit_form.find('h4.modal-title').html(item.edit_options.title + help_badge(item.edit_options.help_link));
		}
	}
	
	function help_badge(link) {
		return ' <span class="badge badge-info topic-badge"><a href="' + 
				link + '" target="_blank"> ? </a></span>'
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
		return result;
	}
	
	function on_filter_form_created(item) {
		item.filter_form.title = item.item_caption + ' - filter';
		item.create_filter_inputs(item.filter_form.find(".edit-body"));
		item.filter_form.find("#cancel-btn").on('click.task', function() {item.close_filter()});
		item.filter_form.find("#ok-btn").on('click.task', function() {item.apply_filter()});
	}
	
	function on_param_form_created(item) {
		item.create_param_inputs(item.param_form.find(".edit-body"));
		item.param_form.find("#cancel-btn").on('click.task', function() {item.close_param_form()});
		item.param_form.find("#ok-btn").on('click.task', function() {item.process_report()});
	}
	
	function set_project_params(task, caption) {
		open_sys_params(task);
		task.sys_params.edit_options.help_link = 'http://jam-py.com/docs/admin/project/parameters.html'; 
		task.sys_params.params = true;
		task.sys_params.edit_options.fields = ['id'];
		task.sys_params.edit_options.title = caption;
		task.sys_params.edit_record();
	}
	
	function edit_database(task, caption) {
		var fields = ['f_manual_update', 'f_db_type', 'f_server', 'f_alias', 'f_login', 'f_password',
			'f_host', 'f_port', 'f_encoding']
		task.sys_tasks.open()
		task.sys_tasks.edit_options.help_link = 'http://jam-py.com/docs/admin/project/database.html';
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
	
	function do_import(file_name) {
		var mess;
	
		mess = task.show_message(
			$('<h5>' + task.language.import_under_way + '</h5>'),
			{
				margin: "20px 20px",
				text_center: true,
			}
		);
		task._importing = true;
		task.server('server_import_task', ['static/internal/' + file_name, true], function(res) {
			var success = res[0],
				error = res[1],
				info = res[2],
				message,
				callback = function() { location.reload() },
				options = {text_center: false, width: 800, height: 400, title: 'Import result',
					close_button: false, margin: 0};
			task.hide_message(mess);
			task.warning(info, callback, options);
			task._importing = false;
		});
	}
	
	function import_task(task) {
		task.upload('static/internal', {multiple: false, callback: do_import});
	}
	
	function export_task(task) {
		var link,
			host = location.protocol + '/' +  '/' + location.hostname + (location.port ? ':' + location.port: ''),
			url = task.server('server_export_task', [host]);
		window.open(url, "_self");
	}
	
	function prepare_files(task) {
		if (task.server('prepare_files')) {
			task.alert('Files generated')
		}
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
	this.tree_changed = tree_changed;
	this.refresh_tree = refresh_tree;
	this.open_sys_params = open_sys_params;
	this.refresh_task_dict = refresh_task_dict;
	this.on_page_loaded = on_page_loaded;
	this.resize = resize;
	this.resize_elements = resize_elements;
	this.resize_panels = resize_panels;
	this.resize_item = resize_item;
	this.resize_editor = resize_editor;
	this.add_button = add_button;
	this.add_divider = add_divider;
	this.add_buttons = add_buttons;
	this.create_params_btn = create_params_btn;
	this.create_print_btns = create_print_btns;
	this.update_task_info = update_task_info;
	this.read_task_name = read_task_name;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.set_btn_lang = set_btn_lang;
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_shown = on_edit_form_shown;
	this.help_badge = help_badge;
	this.on_edit_form_close_query = on_edit_form_close_query;
	this.on_filter_form_created = on_filter_form_created;
	this.on_param_form_created = on_param_form_created;
	this.set_project_params = set_project_params;
	this.edit_database = edit_database;
	this.show_lookup_lists = show_lookup_lists;
	this.find_in_task = find_in_task;
	this.print_section = print_section;
	this.print_code = print_code;
	this.do_import = do_import;
	this.import_task = import_task;
	this.export_task = export_task;
	this.prepare_files = prepare_files;
	this.move_vert = move_vert;
	this.move_record_up = move_record_up;
	this.move_record_down = move_record_down;
	this.update_db_manual_mode = update_db_manual_mode;
	this.on_view_form_keydown = on_view_form_keydown;
	this.on_edit_form_keydown = on_edit_form_keydown;
}

task.events.events1 = new Events1();

function Events2() { // sys_roles 

	function on_view_form_created(item) {
		var w = '70px',
			table_height = item.task.center_panel.height() - item.task.view_panel.height();
		item.edit_options.fields = ['f_name'];
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
			item.sys_privileges.set_view_fields(['owner_item', 'item_id', 'f_can_view', 'f_can_create', 'f_can_edit', 'f_can_delete'],
				[item.task.language.item, item.task.language.can_view, item.task.language.can_create,
				item.task.language.can_edit, item.task.language.can_delete]);
			item.detail_table = item.sys_privileges.create_table(item.view_form.find("#priv-panel .view-table"),
				{
					height: table_height,
					word_wrap: true,
					column_width: {
						f_can_view: w,
						f_can_create: w,
						f_can_edit: w,
						f_can_delete: w
					},
					sortable: false,
					dblclick_edit: false
				}
			);
			item.detail_table.$table.on('click', 'td', function() {
				var $td = $(this),
					field_name = $td.data('field_name'),
					field = item.sys_privileges.field_by_name(field_name);
				if (field.field_type === "boolean") {
					if (!item.is_changing()) {
						item.edit();
					}
					if (!item.sys_privileges.is_changing()) {
						item.sys_privileges.edit();
					}
					field.value = !field.value;
				}
			});
		}
	}
	
	function select_all_clicked(item, value) {
		var detail = item.details.sys_privileges,
			on_field_changed = detail.on_field_changed,
			rec_no = detail.rec_no;
	
		if (!item.rec_count) {
			return;
		}
		if (value === undefined) {
			value = true;
		}
		if (!item.is_changing()) {
			item.edit();
		}
		try {
			if (!item.is_changing()) {
				item.edit();
			}
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
			detail.on_field_changed = on_field_changed;
			detail.rec_no = rec_no;
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
				if (item.rec_count) {
					item.sys_privileges.open();
					if (item.is_browsing()) {
						item.edit();
					}
				}
			},
			50
		);
	}
	
	function on_after_apply(item) {
		item.server('roles_changed');
	//	item.refresh_record();
		if (!item.sys_privileges.rec_count) {
			item.sys_privileges.open(function() {
				item.edit();
				//~ item.sys_privileges.edit();
			});
		}
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

function Events3() { // sys_items 

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
			if (item.task._manual_update) {
				item.sys_fields.view_options.fields = ['f_name', 'f_field_name', 'f_db_field_name',
					'f_data_type', 'f_size', 'f_required', 'f_read_only', 'f_object',
					'f_object_field', 'f_master_field', 'f_enable_typehead',
					'f_lookup_values'];//, 'f_alignment', 'f_default'];
			}
			else {
				item.sys_fields.view_options.fields = ['f_name', 'f_field_name', 'f_db_field_name',
					'f_data_type', 'f_size', 'f_required', 'f_read_only', 'f_object',
					'f_object_field', 'f_master_field', 'f_enable_typehead',
					'f_lookup_values'];//, 'f_alignment', 'f_default'];
			}
		}
		else if (task.item_tree.type_id.value === task.item_types.ITEMS_TYPE ||
			task.item_tree.type_id.value === task.item_types.TABLES_TYPE) {
			item.fields_editor = true;
			item.view_options.fields = ['id', 'f_name', 'f_item_name', 'f_table_name',
				'f_visible', 'f_keep_history', 'f_edit_lock'];
			item.edit_options.fields = ['f_name', 'f_item_name', 'f_table_name'];
			if (item.task._manual_update) {
				item.sys_fields.view_options.fields = ['f_name', 'f_field_name',  'f_db_field_name',
					'f_data_type', 'f_size', 'f_required', 'f_read_only', 'f_object',
					'f_object_field', 'f_master_field', 'f_enable_typehead',
					'f_lookup_values'];//, 'f_alignment', 'f_default'];
			}
			else {
				item.sys_fields.view_options.fields = ['f_name', 'f_field_name', 'f_db_field_name',
					'f_data_type', 'f_size', 'f_required', 'f_read_only', 'f_object',
					'f_object_field', 'f_master_field', 'f_enable_typehead',
					'f_lookup_values'];//, 'f_alignment', 'f_default'];
			}
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
		var task = item.task,
			btns;
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
		else if (task.item_tree.type_id.value === task.item_types.ITEMS_TYPE) {
			btns = [
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
			];
			task.add_buttons(task, btns);
		}
		else if (task.item_tree.type_id.value === task.item_types.TABLES_TYPE) {
			btns = [
				'client_module',
				'server_module',
				'divider',
				'viewing',
				'editing',
				'filters',
				'divider',
				'divider',
				'order',
				'indices',
				'foreign_keys',
				'divider',
				'reports',
				'divider',
				'privileges'
			];
			task.add_buttons(task, btns);
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
				'order',
				'divider',
				'privileges'
			]);
		}
		else if (task.item_tree.type_id.value === task.item_types.REPORTS_TYPE) {
			task.add_buttons(task, [
				'client_module',
				'server_module',
				'divider',
				'report_params',
				'privileges'
			]);
		}
	}
	
	function tree_changed(item) {
		var task = item.task,
			item_tree = item.task.item_tree,
			fields;
		item.set_where({parent: item_tree.id.value});
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
			rec = item.rec_no,
			handlers = item.store_handlers();
		item.clear_handlers();
		item.disable_controls();
		try {
			item.each(function(it) {
				it.edit();
				it.f_index.value = i;
				it.post();
				i++;
			})
		}
		finally {
			item.rec_no = rec;
			item.load_handlers(handlers);
			item.enable_controls();
		}
		item.apply();
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
	
	function on_view_form_created(item) {
		var parent_type_id = item.task.item_tree.type_id.value,
			types = item.task.item_types;
	
		item.cur_record_count = undefined;
		item.can_modify = !(task._production && !task._manual_update)
	
		item.view_options.enable_search = true;
		item.view_options.search_field = 'f_item_name';
		item.set_order_by(['f_index']);
	
		if (parent_type_id === types.TASKS_TYPE) {
			item.view_options.enable_search = false;
			item.view_form.find('#new-btn').hide();
			item.view_form.find('#delete-btn').hide();
			item.view_form.find('#up-btn').hide();
			item.view_form.find('#down-btn').hide();
		}
		if (get_type_id(item) === types.DETAIL_TYPE) {
			item.can_modify = true;
			item.view_form.find('#new-btn').hide();
			item.view_form.find('#delete-btn').hide();
		}
		if (!item.can_modify) {
			item.view_form.find('#new-btn').prop('disabled', true)
			item.view_form.find('#delete-btn').prop('disabled', true)
			item.view_form.find('#edit-btn').text(task.language.view)
		}
		item.view_form.find('#import-btn').hide();
		if ((parent_type_id === types.ITEMS_TYPE || parent_type_id === types.TABLES_TYPE) &&
			item.task._manual_update && item.task.db_options.IMPORT_SUPPORT) {
			item.view_form.find('#import-btn').show();
			item.view_form.find('#import-btn').on('click', function() {
				import_tables(item);
			});
		}
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
		if (item.sys_id.value) {
			item.read_only = true;
		}
		else {
			item.read_only = false;
			if (item.record_count() && item.f_table_name && item.f_virtual_table) {
				item.f_table_name.read_only = !item.is_new();
				item.f_gen_name.read_only = !item.is_new();
				item.f_virtual_table.read_only = !item.is_new();
			}
			if (item.f_soft_delete && item.f_deleted_flag) {
				item.f_soft_delete.read_only = !item.f_deleted_flag.value;
			}
			// if (item.f_record_version && item.f_edit_lock) {
			//	 item.f_edit_lock.read_only = !item.f_record_version.value;
			// }
		}
		item._import_info = undefined; //defined for imported items
		if (item.type_id.value === types.ITEM_TYPE || item.type_id.value === types.TABLE_TYPE) {
			item.fields_editor = true;
			if (item.task.db_options.NEED_GENERATOR) {
				fields = ['f_name', 'f_item_name', 'f_table_name', 'f_gen_name', 'f_primary_key', 'f_deleted_flag']
				if (item.type_id.value === types.TABLE_TYPE) {
					fields = fields.concat(['f_master_id', 'f_master_rec_id'])
				}
			}
			else {
				fields = ['f_name', 'f_item_name', 'f_table_name', 'f_primary_key', 'f_deleted_flag']
				if (item.type_id.value === types.TABLE_TYPE) {
					fields = fields.concat(['f_master_id', 'f_master_rec_id'])
				}
			}
			// fields = fields.concat(['f_record_version']);
			fields = fields.concat(['f_visible', 'f_soft_delete', 'f_virtual_table', 'f_keep_history', 'f_edit_lock'])
		}
		if (item.type_id.value === types.ITEMS_TYPE || item.type_id.value === types.TABLES_TYPE) {
			item.fields_editor = true;
			fields = ['f_name', 'f_item_name', 'f_visible', 'f_primary_key', 'f_deleted_flag']
			if (item.type_id.value === types.TABLES_TYPE) {
				fields = fields.concat(['f_master_id', 'f_master_rec_id'])
			}
			// fields = fields.concat(['f_record_version']);
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
		item.edit_form.find("#cancel-btn").on('click.task', function(e) {item.cancel_edit(e); return false;});
		item.edit_form.find("#ok-btn").on('click.task', function() {item.apply_record()});
		if (item.item_name === 'sys_items') {
			if (!item.can_modify) {
				item.edit_form.find('#ok-btn').hide()
				item.edit_form.find('#delete-btn').prop('disabled', true);
				item.edit_form.find('#new-btn').prop('disabled', true);
				item.edit_form.find('#edit-btn').text(task.language.view);
				item.edit_form.find('#cancel-btn').text(task.language.close);
			}
			if (item.fields_editor) {
				if (parent_type_id === types.TASK_TYPE) {
					height = $(window).height() - 400;
					if (height < 160) {
						height = 160;
					}
					else if (height > 520) {
						height = 520;
					}
					if (item.id.value && !item.server('server_group_is_empty', [item.id.value])) {
						item.edit_form.find("#new-btn").prop("disabled", true);
						item.edit_form.find("#delete-btn").prop("disabled", true);
						update_sys_fields_read_only(item, true, true);
					}
					else {
						item.edit_form.find("#new-btn").prop("disabled", false);
						item.edit_form.find("#delete-btn").prop("disabled", false);
						update_sys_fields_read_only(item, false);
					}
				}
				else {
					height = $(window).height() - 490;
					if (height < 200) {
						height = 200;
					}
					else if (height > 550) {
						height = 550;
					}
					if (parent_type_id === types.TABLES_TYPE) {
						height = $(window).height() - 530;
						if (height < 200) {
							height = 200;
						}
						else if (height > 500) {
							height = 500;
						}
					}
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
						sortable: true,
						title_line_count: 0,
						row_callback: field_colors
					});
				item.sys_fields.open({order_by: ['f_field_name']}, true);
				item.edit_form.find("#new-btn").on('click.task', function() {item.sys_fields.append_record()});
				item.edit_form.find("#edit-btn").on('click.task', function() {item.sys_fields.edit_record()});
				item.edit_form.find("#delete-btn").off('click.task')
					.on('click', function() {
						delete_field(item);
					});
			}
			else {
				item.edit_form.find('#edit-detail-footer').hide();
			}
		}
	}
	
	function delete_field(item) {
		item.question(item.task.language.delete_record, function() {
			do_delete_field(item);
		});
	}
	
	function do_delete_field(item) {
		var error = item.sys_fields.can_delete(item.sys_fields);
		if (error) {
			item.warning(error);
		}
		else {
			item.sys_fields.delete();
			item.sys_fields.apply();
		}
	}
	
	function field_colors(row, item) {
		var field,
			get_field = function() {
				var fields = item.owner._import_info.fields;
				for (var i = 0; i < fields.length; i++) {
					if (fields[i].field_name.toUpperCase() === item.f_field_name.value.toUpperCase()) {
						return fields[i];
					}
				}
			};
		if (item.owner._import_info) {
			if (item.f_data_type.data && typeof item.f_data_type.value !== "number") {
				field = get_field();
				if (field) {
					row.find('td.f_data_type div').text(field.data_type);
				}
				row.find('td.f_data_type').css("color", "#ff9999");
			}
			else {
				row.find('td.f_data_type div').text(item.f_data_type.display_text);
				row.find('td.f_data_type').css("color", "#333333");
			}
			if (!item.f_size.value) {
				field = get_field();
				if (field && field.size) {
					row.find('td.f_size div').text(field.size);
				}
				row.find('td.f_size').css("color", "#ff9999");
			}
			else {
				row.find('td.f_size div').text(item.f_size.display_text);
				row.find('td.f_size').css("color", "#333333");
	
			}
		}
	}
	
	function on_edit_form_shown(item) {
		var caption = '',
			help_link,
			link = '';
	
		if (item.type_id.value === item.task.item_types.REPORT_TYPE) {
			caption = 'Report Editor';
			help_link = '';
		}
		else if (item.type_id.value === item.task.item_types.ITEMS_TYPE) {
			caption = 'Item Group Editor';
			help_link = 'http://jam-py.com/docs/admin/groups/item_group_editor.html';
		}
		else if (item.type_id.value === item.task.item_types.TABLES_TYPE) {
			caption = 'Table Group Editor';
			help_link = 'http://jam-py.com/docs/admin/groups/table_group_editor.html';
		}
		else if (item.type_id.value === item.task.item_types.REPORTS_TYPE) {
			caption = 'Report Group Editor';
			help_link = 'http://jam-py.com/docs/admin/groups/report_group_editor.html';
		}
		else if (item.type_id.value !== item.task.item_types.TASK_TYPE) {
			caption = 'Item Editor';
			help_link = 'http://jam-py.com/docs/admin/items/item_editor_dialog.html';
		}
		if (help_link) {
			link = task.help_badge(help_link);
		}
		if (item.is_new()) {
			item.edit_form.find('h4.modal-title').html(caption + link);
		}
		else {
			item.edit_form.find('h4.modal-title').html(caption + 
				' <span class="editor-title">' + item.f_item_name.value + '</span>' + link);
		}
	}
	
	function update_sys_fields_read_only(item, value, group) {
		item.f_primary_key.read_only = value;
		item.f_deleted_flag.read_only = value;
		// if (group) {
		//	 item.f_record_version.read_only = value;
		// }
		// else {
		//	 item.f_record_version.read_only = false;
		// }
		item.f_virtual_table.read_only = value;
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
			// item.f_record_version.value = parent.f_record_version.value;
			// item.f_record_version.lookup_value = parent.f_record_version.lookup_value;
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
			check_detail,
			check_item,
			check_group,
			check_task,
			error;
		if (field.field_name === 'f_item_name') {
			if (!item.valid_identifier(field.value)) {
				return item.task.language.invalid_name
			}
			error = item.task.server('server_valid_item_name', [item.id.value, item.parent.value,
				field.value, item.type_id.value]);
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
	//		if (!field.value && !item.f_virtual_table.value && !item.task._manual_update && !item.sys_id.value &&
			if (!field.value && !item.f_virtual_table.value && !item.sys_id.value &&
				(item.type_id.value === types.ITEM_TYPE || item.type_id.value === types.TABLE_TYPE)) {
				return item.task.language.value_required;
			}
		}
		else if (field.field_name === 'f_master_id' && !item.task._manual_update && item.is_new()) {
			if (!field.value && !item.f_virtual_table.value && item.type_id.value === types.TABLE_TYPE) {
				return item.task.language.value_required;
			}
		}
		else if (field.field_name === 'f_master_rec_id') {
			if (!field.value && !item.f_virtual_table.value && item.type_id.value === types.TABLE_TYPE) {
				return item.task.language.value_required;
			}
		}
	}
	
	function on_field_changed(field, lookup_item) {
		var copy,
			ident,
			names,
			item = field.owner
		if (item.is_new() && item.type_id.value != item.task.item_types.DETAIL_TYPE) {
			if (field.field_name == 'f_item_name' && !item.f_virtual_table.value &&
				!task._manual_update && item.type_id.value !== item.task.item_types.ITEMS_TYPE) {
				names = item.task.server('get_new_table_name', field.value);
				item.f_table_name.value = names[0];
				if (item.task.db_options.NEED_GENERATOR) {
					item.f_gen_name.value = names[1];
				}
			}
			if (field.field_name === 'f_name' && !item.f_item_name.value) {
				try {
					ident = field.text.split(' ').join('_');
					ident = ident.toLowerCase();
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
		// else if (field.field_name === 'f_record_version') {
		//	 if (field.value) {
		//		 item.f_edit_lock.read_only = false;
		//		 // item.f_edit_lock.value = true;
		//	 }
		//	 else {
		//		 item.f_edit_lock.value = false;
		//		 item.f_edit_lock.read_only = true;
		//	 }
		// }
		else if (field.field_name === 'f_virtual_table') {
			if (field.value) {
				item.f_table_name.value = null;
				item.f_gen_name.value = null;
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
					task.btns_panel.find('button.indices').prop("disabled", item.f_virtual_table.value);
					task.btns_panel.find('button.foreign_keys').prop("disabled", item.f_virtual_table.value);
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
	
	function view_options_list(item) {
		var result = [
			['multiselect', false],
			['dblclick_edit', true],
			['height', 0],
			['row_count', 0],
			['title_line_count', 1],
			['row_line_count', 1],
			['expand_selected_row', 0],
			['freeze_count', 0],
			['sort_fields', []],
			['edit_fields', []],
			['summary_fields', []],
			['striped', false]
		];
		for (var i = 0; i < result.length; i++) {
			if (item.task.table_options[result[i][0]]) {
				result[i][1] = item.task.table_options[result[i][0]]
			}
		}
		return result;
	}
	
	function view_form_options_list(item) {
		var result = [
			['form_border', true],
			['form_header', true],
			['history_button', true],
			['refresh_button', true],
			['enable_search', true],
			['search_field', []],
			['enable_filters', true],
			['close_button', true],
			['close_on_escape', true],
			['width', 0],
			['view_detail', []],
			['detail_height', 0],
			['buttons_on_top', false]
		];
		if (item.table_id.value) {
			return [];
		}
		for (var i = 0; i < result.length; i++) {
			if (item.task.view_options[result[i][0]]) {
				result[i][1] = item.task.view_options[result[i][0]];
			}
		}
		return result;
	}
	
	function view_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			dest_list,
			list,
			view_object,
			help_link = task.help_badge('http://jam-py.com/docs/admin/items/view_form_dialog.html'),
			title;
	
		function save_view(item, dest_list) {
			info.view_list = dest_list;
			item.server('server_store_interface', [item.id.value, info]);
		}
	
		info = item.server('server_load_interface', [item.id.value]);
		source_def = [
			['id', '', false],
			['name', 'Field', true]
		];
		dest_def = [
			['id', '', false],
			['name', 'Field', true, '70%'],
			['param3', 'Width', true]
		];
	
		//~ info.view_list = [] //!!!!!!!
	
		view_object = info.view_list;
	
		if (view_object instanceof Array) {
			list = [];
			for (var i = 0; i < view_object.length; i++) {
				list.push([view_object[i][0], ''])
			}
			view_object = { 0: ['', {}, [], {}, list, []] };
		}
		title = item.task.language.viewing + ' <span class="editor-title">' + item.f_item_name.value + '</span>' + help_link;
		item.task.sys_fields_editor.fields_editor('view', item, title, source_def, get_fields_list(item.task), dest_def, view_object, save_view);
	}
	
	function edit_options_list(item) {
		return [
			['col_count', 1],
			['label_size', 3],
			['in_well', true]
		]
	}
	
	function edit_form_options_list(item) {
		var result = [
			['form_border', true],
			['form_header', true],
			['history_button', true],
			['close_button', true],
			['close_on_escape', true],
			['width', 0],
			['edit_details', []],
			['detail_height', 0],
			['buttons_on_top', false],
			['modeless', false]
		];
		for (var i = 0; i < result.length; i++) {
			if (item.task.edit_options[result[i][0]]) {
				result[i][1] = item.task.edit_options[result[i][0]];
			}
		}
		return result
	}
	
	function edit_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			dest_list,
			list,
			edit_object,
			help_link = task.help_badge('http://jam-py.com/docs/admin/items/edit_form_dialog.html'),
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
			['name', 'Field', true, '70%']
	//		['param3', 'Width', true]
		];
	
		//~ info.edit_list = [] //!!!!!!!
	
		edit_object = info.edit_list;
		if (edit_object instanceof Array) {
			list = [];
			for (var i = 0; i < edit_object.length; i++) {
				list.push([edit_object[i][0], ''])
			}
			edit_object = { 0: ['', {}, [], [['', [[{}, list, '']]]]] };
		}
	
		title = item.task.language.editing + ' <span class="editor-title">' + item.f_item_name.value + '</span>' + help_link;
		item.task.sys_fields_editor.fields_editor('edit', item, title, source_def, get_fields_list(item.task), dest_def, edit_object, save_edit);
	}
	
	
	function edit_code(item, is_server) {
		item.task.server('server_item_info', [item.id.value, is_server], function(info) {
			info.item_id = item.id.value;
			info.table_id = item.table_id.value;
		item.task.sys_code_editor.show_editor(item.task, info);
		});
	}
	
	function get_templates(doc) {
		var temp = $('<output>').append($.parseHTML(doc)),
			result = {}
		temp.find('.templates > div').each(function() {
			result[this.className] = null;
		});
		return result;
	}
	
	function edit_file(item, file_name) {
		item.task.server('server_file_info', [file_name], function(info) {
			var temp;
			if (file_name === 'index.html') {
				info.templates = get_templates(info.doc);
			}
			item.task.sys_code_editor.show_editor(item.task, info)
		});
	}
	
	function edit_client(item) {
		edit_code(item, false);
	}
	
	function edit_server(item) {
		edit_code(item, true);
	}
	
	function edit_index_html(item) {
		edit_file(item, 'index.html');
	}
	
	function edit_project_css(item) {
		edit_file(item, 'project.css');
	}
	
	function valid_detail(item, d) {
		var result = true,
			tables;
		if (!d.f_master_id.value) {
			tables = d.copy({handlers: false});
			tables.set_where({table_id: d.id.value});
			tables.open();
			if (tables.rec_count && item.id.value !== tables.parent.value) {
				result = false;
			}
		}
		return result;
	}
	
	function get_detail_source_list(item) {
		var result = [],
			tables = item.copy({handlers: false});
		tables.set_where({type_id: task.item_types.TABLE_TYPE});
		tables.set_order_by(['f_index']);
		tables.open();
		tables.each(function(t) {
			if (valid_detail(item, t)) {
				result.push([t.id.value, t.f_item_name.value]);
			}
		});
		return result
	}
	
	function get_detail_dest_list(item) {
		var result = [],
			details = item.copy({handlers: false});
		details.set_where({parent: item.id.value});
		details.set_order_by(['f_index']);
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
			help_link = task.help_badge('http://jam-py.com/docs/admin/items/details_dialog.html'),
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
		title = item.task.language.details + ' <span class="editor-title">' + item.f_item_name.value + '</span>' + help_link;
		item.task.sys_fields_editor.fields_editor('details', item, title, source_def, source_list, dest_def, dest_list, save_edit, undefined, true);
	}
	
	function order_setup(item) {
		var info,
			source_def = [],
			dest_def = [],
			dest_list,
			help_link = task.help_badge('http://jam-py.com/docs/admin/items/order_dialog.html'),
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
		title = item.task.language.order + ' <span class="editor-title">' + item.f_item_name.value + '</span>' + help_link;
		item.task.sys_fields_editor.fields_editor('order', item, title, source_def, get_fields_list(item.task), dest_def, info.order_list, save_view);
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
			help_link = task.help_badge('http://jam-py.com/docs/admin/items/reports_dialog.html'),
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
		title = item.task.language.reports + ' <span class="editor-title">' + item.f_item_name.value + '</span>' + help_link;
		item.task.sys_fields_editor.fields_editor('reports', item, title, source_def, get_reports_list(item), dest_def, info.reports_list, save_edit);
	}
	
	function filters_setup(item) {
		var help_link = task.help_badge('http://jam-py.com/docs/admin/items/filters_dialog.html');
		item.task.sys_filters.set_where({owner_rec_id: item.id.value});
		item.task.sys_filters.set_order_by(['f_index']);
		item.task.sys_filters.view_options.fields = ['f_name', 'f_filter_name', 'f_type', 'f_field', 'f_visible'];
		item.task.sys_filters.edit_options.fields = ['f_field', 'f_name', 'f_filter_name', 'f_type', 'f_placeholder',
			'f_help', 'f_visible'];
		item.task.sys_filters.view_options.title = 'Filters <span class="editor-title">' + 
			item.f_item_name.value + '</span>' + help_link;
		item.task.sys_filters.view();
	}
	
	function indices_setup(item) {
		var indices = item.task.sys_indices.copy(),
			help_link = task.help_badge('http://jam-py.com/docs/admin/items/indices_dialog.html');
		indices.foreign_index = false;
		indices.set_where({owner_rec_id: item.id.value, f_foreign_index: false});
		indices.view_options.title = 'Indices <span class="editor-title">' + 
			item.f_item_name.value + '</span>' + help_link;
		indices.view();
	}
	
	function foreign_keys_setup(item) {
		var indices = item.task.sys_indices.copy(),
			help_link = task.help_badge('http://jam-py.com/docs/admin/items/foreign_keys_dialog.html');	
		indices.foreign_index = true;
		indices.set_where({owner_rec_id: item.id.value, f_foreign_index: true});
		indices.view_options.title = 'Foreign keys <span class="editor-title">' + 
			item.f_item_name.value + '</span>' + help_link;
		indices.view();
	}
	
	function report_params_setup(item) {
		var fields = ['f_name', 'f_param_name','f_data_type', 'f_object', 'f_object_field', 'f_enable_typehead', 'f_multi_select',
			'f_lookup_values', 'f_required', 'f_alignment', 'f_visible'];
			// help_link = task.help_badge('');
		item.task.sys_report_params.set_where({owner_rec_id: item.id.value});
		item.task.sys_report_params.set_order_by(['f_index']);
		item.task.sys_report_params.view_options.fields = fields;
		fields = ['f_name', 'f_param_name','f_data_type', 'f_object', 'f_object_field', 'f_enable_typehead', 'f_multi_select',
			'f_multi_select_all', 'f_lookup_values', 'f_required', 'f_alignment', 'f_placeholder', 'f_help', 'f_visible'];
		item.task.sys_report_params.edit_options.fields = fields;
		item.task.sys_report_params.view_options.title = 'Params <span class="editor-title">' + 
			item.f_item_name.value + '</span>';
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
			delete_field(item);
		}
	}
	
	function on_after_apply(item) {
		item.refresh_record();
		on_after_scroll(item);
		if (item.record_count() && item.cur_record_count && item.cur_record_count !== item.record_count()) {
			if (item.type_id.value === item.task.item_types.ITEMS_TYPE ||
				item.type_id.value === item.task.item_types.TABLES_TYPE ||
				item.type_id.value === item.task.item_types.REPORTS_TYPE) {
				item.task.refresh_tree(item.task);
			}
		}
		if (item._import_info) {
	//		add_import_indexes(item, item._import_info.indexes)
			item._import_info = undefined;
		}
		item.task.refresh_task_dict(item.task);
	}
	
	function on_field_select_value(field, lookup_item) {
		var item = field.owner,
			data_type = [item.task.consts.INTEGER];
		if (lookup_item.item_name === 'sys_fields') {
			lookup_item.set_view_fields(['f_field_name', 'f_name']);
		}
		if (lookup_item.item_name === 'sys_fields') {
			lookup_item.set_order_by(['f_field_name']);
		}
		if (field.field_name === 'f_primary_key' ||
			field.field_name === 'f_deleted_flag' ||
			// field.field_name === 'f_record_version' ||
			field.field_name === 'f_master_id' ||
			field.field_name === 'f_master_rec_id') {
			lookup_item.set_order_by(['f_field_name']);
			if (field.field_name === 'f_primary_key') {
				data_type = [item.task.consts.INTEGER, item.task.consts.TEXT];
			}
			else if (field.field_name === 'f_deleted_flag') {
				data_type = [item.task.consts.BOOLEAN];
			}
			lookup_item.set_where(
				{
					owner_rec_id__in: [item.parent.value],
					f_data_type__in: data_type,
					f_object__isnull: true,
					f_lookup_values__isnull: true
				});
		}
		lookup_item.on_after_open = function(it) {
			var clone = item.sys_fields.clone()
			it.first();
			while (!it.eof()) {
				if (it.id.value === item.f_primary_key.value ||
					it.id.value === item.f_deleted_flag.value ||
					// it.id.value === item.f_record_version.value ||
					it.id.value === item.f_master_id.value ||
					it.id.value === item.f_master_rec_id.value) {
					it.delete();
				}
				else {
					it.next();
				}
			}
			clone.each(function(c) {
				if ($.inArray(c.f_data_type.value, data_type) !== -1 &&
					!c.f_object.value &&
					!c.f_lookup_values.value &&
					c.id.value !== item.f_primary_key.value &&
					c.id.value !== item.f_deleted_flag.value &&
					// c.id.value !== item.f_record_version.value &&
					c.id.value !== item.f_master_id.value &&
					c.id.value !== item.f_master_rec_id.value) {
					it.append();
					it.id.value = c.id.value;
					it.f_field_name.value = c.f_field_name.value;
					it.f_db_field_name.value = c.f_db_field_name.value;
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
	
	function on_before_apply(item, params) {
		params.manual_update = item.task._manual_update;
	}
	
	function add_import_indexes(item, indexes) {
		var inds = item.task.sys_indices,
			desc,
			field_found,
			field_id,
			field_name,
			found = 0,
			dest_list,
			mess;
		inds.open({open_empty: true});
		if (indexes.length) {
			for (var i = 0; i < indexes.length; i++) {
				inds.append();
				inds.f_index_name.value = indexes[i].index_name;
				inds.f_unique_index.value = indexes[i].unique;
				dest_list = []
				field_found = true;
				for (var j = 0; j < indexes[i].fields.length; j++) {
					field_name = indexes[i].fields[j][0];
					desc = indexes[i].fields[j][1];
					field_id = 0;
					item.sys_fields.each(function(r) {
						if (r.f_db_field_name.value.toUpperCase() === field_name.toUpperCase()) {
							field_id = r.id.value;
							return false;
						}
					});
					if (field_id) {
						dest_list.push([field_id, desc]);
					}
					else {
						field_found = false;
						break;
					}
				}
				inds.f_fields_list.value = inds.server('server_dump_index_fields', [dest_list]);
				if (field_found) {
					found += 1;
					inds.post();
				}
				else {
					inds.cancel();
				}
			}
			inds.apply();
			mess = 'Information about ' + found + ' index(es) have been added.'
			if (indexes.length - found) {
				mess += ' Information about ' + (indexes.length - found) + ' index(es) could not be added.'
			}
			item.warning(mess);
		}
	}
	
	function convert_field_type(field, types) {
		var data_type = field.data_type.toUpperCase(),
			field_type,
			field_size = field.size,
			type,
			types,
			i,
			j,
			pos1,
			pos2,
			check_types = [
				[task.consts.TEXT, ['CHAR', 'TEXT']],
				[task.consts.DATETIME, ['DATETIME']],
				[task.consts.DATE, ['DATE']],
				[task.consts.FLOAT, ['NUMBER']]
			];
		for (var type in types) {
			if (types[type] === data_type) {
				field_type = parseInt(type, 10);
				break;
			}
		}
		if (!field_type) {
			for (i = 0; i < check_types.length; i++) {
				type = check_types[i][0];
				types = check_types[i][1];
				for (j = 0; j < types.length; j++) {
					if (data_type.indexOf(types[j]) !== -1) {
						field_type = type;
						if (field_type === task.consts.TEXT) {
							pos1 = data_type.indexOf('(')
							pos2 = data_type.indexOf(')')
							if (pos1 > 0 && pos2 > 0) {
								field_size = parseInt(data_type.substring(pos1 + 1, pos2), 10);
							}
						}
						break;
					}
				}
			}
		}
		if (field_type) {
			field.data_type = field_type;
			field.size = field_size;
		}
		return field;
	}
	
	function import_table(item, imp) {
		var table_name = imp.f_table_name.value,
			res = item.task.server('server_import_table', table_name),
			fields,
			types,
			field_name,
			cur_id,
			handlers;
		if (res) {
			fields = res['fields'];
			types = res['field_types'];
			imp.close_view_form();
			item.append_record()
			handlers = item.sys_fields.store_handlers();
			item.sys_fields.disable_controls();
			try {
				item._import_info = res;
				item.sys_fields.clear_handlers();
				item.f_name.value = table_name.charAt(0).toUpperCase() + table_name.slice(1).toLowerCase();
				item.f_item_name.value = table_name.toLowerCase();
				item.f_table_name.value = table_name;
				item.f_gen_name.value = ''
				item.f_virtual_table.value = false;
				item.f_virtual_table.read_only = true;
				item.f_soft_delete.value = false;
				cur_id = item.task.server('get_fields_next_id', fields.length);
				for (var i = 0; i < fields.length; i++) {
					fields[i] = convert_field_type(fields[i], types)
					field_name = fields[i].field_name;
					item.sys_fields.append();
					item.sys_fields.id.value = cur_id;
					cur_id += 1;
					item.sys_fields.f_name.value = field_name;//field_name.charAt(0).toUpperCase() + field_name.slice(1).toLowerCase();
					item.sys_fields.f_field_name.value = field_name.toLowerCase();
					item.sys_fields.f_db_field_name.value = field_name;
					item.sys_fields.f_data_type.value = fields[i].data_type;
					item.sys_fields.f_size.value = fields[i].size;
					item.sys_fields.f_alignment.value = item.sys_fields.get_alignment(item.sys_fields);
					if (fields[i].pk) {
						item.f_primary_key.value = item.sys_fields.id.value;
						item.f_primary_key.lookup_value = item.sys_fields.f_field_name.value;
					}
	//			if (fields[i].default_value) {
	//				item.sys_fields.f_default_value.value = fields[i].default_value;
	//			}
					item.sys_fields.post();
				}
				item.sys_fields.first();
			}
			finally {
				item.sys_fields.load_handlers(handlers);
				item.sys_fields.enable_controls();
				item.sys_fields.update_controls();
			}
		}
	}
	
	function can_import_tables(item) {
		var fields = item.task.sys_fields.copy({handlers: false});
		fields.set_where({owner_rec_id: item.task.item_tree.id.value});
		fields.open({fields: ['id']});
		if (fields.record_count()) {
			item.warning(item.task.language.import_prohibited.replace('%s', item.task.item_tree.f_name.value));
			return false;
		}
		return true;
	}
	
	function import_tables(item) {
		var imp = item.copy({handlers: false});
		if (can_import_tables(item)) {
			imp.each_field(function(f) {
			f.required = false
			});
			imp.log_changes = false;
			imp.set_where({id__in: []})
			imp.init_view_table = function(imp, options) {
				options.on_dblclick = function() {
					import_table(item, imp);
				}
			}
			imp.on_view_form_shown = function(imp) {
				imp.view_form.find('.modal-footer').show();
				imp.view_form.find('#import-btn').click(function() {
					import_table(item, imp);
				});
				imp.task.server('server_get_table_names', function(table_names) {
					imp.disable_controls();
					try {
						for (var i = 0; i < table_names.length; i++) {
							imp.append()
							imp.f_table_name.value = table_names[i]
							imp.post()
						}
						imp.first();
					}
					finally {
						imp.enable_controls();
					}
				});
			}
			imp.view_options.template_class = 'import-tables-view';
			imp.view_options.title = 'Import';
			imp.view_options.fields = ['f_table_name'];
			imp.view();
		}
	}
	
	function on_before_post(item) {
		var clone = item.sys_fields.clone(),
			types = item.task.item_types,
			error = false;
		if (item._import_info) {
			let check_item = new item.task.constructors.item();
			clone.each(function(c) {
				if (typeof c.f_data_type.value !== "number") {
					error = c.f_field_name.value + ': the field type must be specified.';
				}
				else if (c.f_data_type.value === c.task.consts.TEXT && !c.f_size.value) {
					error = c.f_field_name.value + ': the field size must be specified.';
				}
				else if (!item.valid_identifier(c.f_field_name.value)) {
					error = c.f_field_name.value + ': ' + item.task.language.invalid_name
				}
				else if (check_item[c.f_field_name.value] !== undefined) {
					error = c.f_field_name.value + ': ' + item.task.language.reserved_word;
				}
				if (error) {
					return false;
				}
			});
			if (error) {
				// item.warning(error);
				throw error;
			}
			if (!item.f_primary_key.value) {
				if (!item.f_virtual_table.value && !item.sys_id.value &&
					(item.type_id.value === types.ITEM_TYPE || item.type_id.value === types.TABLE_TYPE)) {
					item.warning('You must specify primary field to use this item as a lookup item.')
				}
			}
		}
		else {
			if (!item.f_primary_key.value) {
				 item.f_gen_name.value = null;
			}
		}
	}
	this.init_fields = init_fields;
	this.init_buttons = init_buttons;
	this.tree_changed = tree_changed;
	this.get_type_id = get_type_id;
	this.save_order = save_order;
	this.append_group = append_group;
	this.can_delete = can_delete;
	this.on_view_form_created = on_view_form_created;
	this.on_edit_form_created = on_edit_form_created;
	this.delete_field = delete_field;
	this.do_delete_field = do_delete_field;
	this.field_colors = field_colors;
	this.on_edit_form_shown = on_edit_form_shown;
	this.update_sys_fields_read_only = update_sys_fields_read_only;
	this.on_after_append = on_after_append;
	this.on_field_validate = on_field_validate;
	this.on_field_changed = on_field_changed;
	this.valid_identifier = valid_identifier;
	this.on_after_scroll = on_after_scroll;
	this.get_fields_list = get_fields_list;
	this.view_options_list = view_options_list;
	this.view_form_options_list = view_form_options_list;
	this.view_setup = view_setup;
	this.edit_options_list = edit_options_list;
	this.edit_form_options_list = edit_form_options_list;
	this.edit_setup = edit_setup;
	this.edit_code = edit_code;
	this.get_templates = get_templates;
	this.edit_file = edit_file;
	this.edit_client = edit_client;
	this.edit_server = edit_server;
	this.edit_index_html = edit_index_html;
	this.edit_project_css = edit_project_css;
	this.valid_detail = valid_detail;
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
	this.add_import_indexes = add_import_indexes;
	this.convert_field_type = convert_field_type;
	this.import_table = import_table;
	this.can_import_tables = can_import_tables;
	this.import_tables = import_tables;
	this.on_before_post = on_before_post;
}

task.events.events3 = new Events3();

function Events8() { // app_builder.catalogs.sys_params 

	function on_after_apply(item) {
		if (item.task.init_project && item.f_language.value) {
			item.task.server('server_set_project_langage', [item.f_language.value])
			location.reload();
		}
		else {
			if (item._safe_mode !== item.f_safe_mode.value ||
				item._language !== item.f_language.value ||
				item._production != item.f_production.value) {
				item.task.logout();
				location.reload();
			}
			else {
				item.task.update_task_info(item.task);
			}
		}
	}
	
	function on_edit_form_created(item) {
		var edit_body = item.edit_form.find('.edit-body'),
			general,
			intface;
		if (item.task.init_project) {
			item.create_inputs(edit_body, {fields: ['f_language'], in_well: false});
		}
		else {
			item._safe_mode = item.f_safe_mode.value;
			item._language = item.f_language.value;
			item._theme = item.f_theme.value;
			item._production = item.f_production.value;
	
			item.edit_options.width = 620;
	
			task.init_tabs(edit_body);
			general = task.add_tab(edit_body, task.language.general);
			intface = task.add_tab(edit_body, task.language.interface);
	
			item.create_inputs(general, {
				fields: ['f_production', 'f_safe_mode', 'f_debugging', 'f_language', 'f_persist_con',
				'f_con_pool_size', 'f_compressed_js',
				'f_single_file_js', 'f_dynamic_js', 'f_history_item', 'f_lock_item', 'f_timeout',
				'f_ignore_change_ip', 'f_max_content_length', 'f_import_delay',
				'f_delete_reports_after', 'f_upload_file_ext', 'f_version'
				],
				in_well: false,
				label_width: 240
			});
			item.create_inputs(intface, {
				fields: ['f_theme', 'f_small_font', 'f_full_width', 'f_forms_in_tabs'],
				in_well: false,
				label_width: 240
			});
		}
	}
	
	function on_edit_form_shown(item) {
		var edit_body = item.edit_form.find('.edit-body');
		if (!item.task.init_project) {
			edit_body.css('min-height', edit_body.height());
		}
	}
	
	function on_field_changed(field) {
		var item = field.owner;
		if (field.field_name === 'f_con_pool_size') {
			if (field.value < 1) {
				field.value = 1;
			}
		}
		else if (field.field_name === 'f_production') {
			 if (field.value) {
				 item.f_safe_mode.value = true;
				 item.f_debugging.value = false;
				 item.f_import_delay.value = 180;
			 }
		}
	}
	
	function on_field_select_value(field, lookup_item) {
		if (field.field_name === 'f_history_item' || field.field_name === 'f_lock_item') {
			if (field.field_name === 'f_history_item') {
				lookup_item.set_where({sys_id: 1});
			}
			else if (field.field_name === 'f_lock_item') {
				lookup_item.set_where({sys_id: 2});
			}
			lookup_item.view_options.template_class = 'sys_items_system';
			lookup_item.view_options.fields = ['f_name', 'f_item_name'];
		}
	}
	
	function init_lookup_form(lookup_item) {
		var btn_caption;
		if (lookup_item.lookup_field.field_name === 'f_history_item') {
			btn_caption = task.language.create_history_item;
		}
		else if (lookup_item.lookup_field.field_name === 'f_lock_item') {
			btn_caption = 'Create lock item';
		}
		lookup_item.view_form.find('#create-btn').text(btn_caption).click(function() {
			create_system_item(lookup_item);
		});
	}
	
	function create_system_item(lookup_item) {
		var data = lookup_item.task.server('create_system_item', lookup_item.lookup_field.field_name),
			result = data[0],
			error = data[1];
		if (error) {
			lookup_item.warning(error);
		}
		else {
			lookup_item.warning(result, function() {
				location.reload();
			});
		}
	}
	
	function on_field_validate(field) {
		if (field.field_name === 'f_upload_file_ext' && field.value) {
			let valid = true,
				exts = field.value.split(',');
			exts.forEach(function(ext) {
				ext = ext.trim();
				if (ext[0] !== '.') {
					valid = false;
				}
			});
			if (!valid) {
				return 'Invalid upload file extensions';
			}
		}
	}
	this.on_after_apply = on_after_apply;
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_shown = on_edit_form_shown;
	this.on_field_changed = on_field_changed;
	this.on_field_select_value = on_field_select_value;
	this.init_lookup_form = init_lookup_form;
	this.create_system_item = create_system_item;
	this.on_field_validate = on_field_validate;
}

task.events.events8 = new Events8();

function Events9() { // app_builder.catalogs.sys_langs 

	function save_file(filename, text) {
		var el = document.createElement('a');
		el.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
		el.setAttribute('download', filename);
		el.style.display = 'none';
		document.body.appendChild(el);
		el.click();
		document.body.removeChild(el);
	}
	
	function on_view_form_created(item) {
		item.view_options.width = 500;
		item.view_options.fields = ['f_name'];
		item.set_order_by(['f_name']);
		item.view_form.find('#import-btn').click(function() {
			task.upload('static/reports', {multiple: false, callback: function(file_name) {
				item.server('import_lang', ['static/reports/' + file_name], function(error) {
					if (error) {
						item.warning(error);
					}
					else {
						item.set_order_by(['f_name']);
						item.open(true);
						item.alert('Language file imported.');
					}
				});
			}});
		});
		item.view_form.find('#export-btn').click(function() {
			var host = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port: '');
			item.server('export_lang', [item.id.value, host], function(res){
				save_file(res.file_name, res.content);
			});
		});
	}
	
	function on_view_form_shown(item) {
		item.locate('id', task.sys_params.f_language.value);
	}
	
	function on_edit_form_created(item) {
		var edit_body = item.edit_form.find('.edit-body'),
			locale,
			translation,
			lang_defined = item.f_language.value && item.f_country.value;
	
		item._language_changed = false;
		item.f_language.read_only = lang_defined;
		item.f_country.read_only = lang_defined;
	
		item.transl_table = task.sys_lang_keys_values.copy();
	
		item.edit_options.width = 1000;
	
		item.create_inputs(item.edit_form.find('.edit-title'), {fields: ['f_language', 'f_country'], col_count: 2});
	
		task.init_tabs(edit_body);
		locale = task.add_tab(edit_body, 'Locale');
		translation = task.add_tab(edit_body, 'Translation');
	
		item.create_inputs(locale, {
			fields: ['f_decimal_point', 'f_mon_decimal_point', 'f_mon_thousands_sep',
				'f_currency_symbol', 'f_frac_digits', 'f_p_cs_precedes', 'f_n_cs_precedes', 'f_p_sep_by_space',
				'f_n_sep_by_space', 'f_positive_sign', 'f_negative_sign',
				'f_p_sign_posn', 'f_n_sign_posn', 'f_d_fmt', 'f_d_t_fmt'],
			label_width: 500
		});
		locale.find('input.input-text').width(120);
		locale.find('input.input-integer').width(20);
	
		translation.append('<div id="table-div">');
		item.transl_table.open({open_empty: true});
		fill_table(item);
		item.transl_table.create_table(translation.find("#table-div"), {
			fields: ['f_key_str', 'f_eng_str', 'f_value'],
			height: 520,
			row_line_count: 1,
			expand_selected_row: 2,
			sortable: true,
			editable: true,
			editable_fields: ['f_value'],
			dblclick_edit: false,
			column_width: {f_key_str: '5%', f_eng_str: '50%', f_value: '50%'},
			show_hints: false
		});
		item.transl_table.create_inputs(translation.find("#inputs-div"), {
			fields: ['f_eng_str', 'f_value'],
		});
	
		item.edit_form.find('.modal-footer #new-btn').click(function() {
			var tr = item.transl_table.copy({handlers: false});
			tr.init_edit_options = function(tr, options) {
				options.fields = ['f_key_str'];
			};
			tr.on_edit_form_created = function(t) {
				t.edit_form.find('#ok-btn').off('click.task').on('click', function() {
					var key = t.f_key_str.value;
					t.cancel();
					item.server('add_key', key, function(res) {
						if (res) {
							item.warning(res);
						}
						else {
							t.close_edit_form();
							item.transl_table.on_field_changed = null;
							item.transl_table.open({open_empty: true});
							fill_table(item);
						}
					});
				});
			};
			tr.open({open_empty: true});
			tr.append_record();
		});
		item.edit_form.find('.modal-footer #delete-btn').click(function() {
			item.question('Delete the record?',
				function() {
					item.server('del_key', item.transl_table.f_key.value, function(res) {
						if (res) {
							item.transl_table.on_field_changed = null;
							item.transl_table.open({open_empty: true});
							fill_table(item);
						}
					});
				}
			);
		});
	}
	
	function on_edit_form_keyup(item, event) {
		if (event.keyCode === 77 && event.ctrlKey === true){
			item.edit_form.find('.modal-footer #new-btn').show();
			item.edit_form.find('.modal-footer #delete-btn').show();
		}
	}
	
	function get_lang_name(item) {
		var c = task.sys_countries.copy(),
			l = task.sys_languages.copy();
		c.open({where: {id: item.f_country.value}});
		l.open({where: {id: item.f_language.value}});
		return item.f_language.display_text + ' ' + l.f_abr.value + '-' + c.f_abr.value;
	}
	
	function get_lang_info(item) {
		var c = task.sys_countries.copy(),
			l = task.sys_languages.copy(),
			result = {};
		c.open({where: {id: item.f_country.value}});
		l.open({where: {id: item.f_language.value}});
		result.abr = l.f_abr.value + '-' + c.f_abr.value;
		result.name = l.f_name.value + ' ' + result.abr;
		result.rlt = l.f_rtl.value;
		return result;
	}
	
	function lang_exists(item) {
		var result = false,
			clone = item.clone();
		clone.each(function(c) {
			if (c.id.value &&
				c.f_language.value === item.f_language.value &&
				c.f_country.value === item.f_country.value) {
				result = true;
				return false;
			}
		});
		return result;
	}
	
	function find_lang(item) {
		var result = null,
			clone = item.clone();
		clone.each(function(c) {
			if (c.id.value && c.f_language.value === item.f_language.value) {
				result = c.id.value;
				return false;
			}
		})
		return result;
	}
	
	function on_field_changed(field, lookup_item) {
		var lang_info,
			item = field.owner;
		if (!item._field_changed) {
			item._field_changed = true;
			try {
				if (item.f_language.value && item.f_country.value) {
					if (!item.id.value) {
						if (lang_exists(item)) {
							item.warning('There is a language with this parameters.')
							field.value = null;
							return;
						}
						else {
							lang_info = get_lang_info(item);
							item.f_name.value = lang_info.name;
							item.f_abr.value = lang_info.abr;
							item.f_rtl.value = lang_info.rtl;
							item.apply();
							item.server('add_lang', [item.id.value, item.f_language.value,
								item.f_country.value, lang_info.name, lang_info.abr,
								lang_info.rtl, find_lang(item)]);
							item.refresh_record();
							item.edit();
							fill_table(item);
						}
					}
					item.apply();
					item.edit();
					item.server('save_lang_field', [item.id.value, field.field_name, field.value], true);
					item._language_changed = true;
				}
			}
			finally {
				item._field_changed = false;
			}
		}
	}
	
	function fill_table(item) {
		var langs_info;
		if (item.f_language.value && item.f_country.value) {
			item.transl_table.open({open_empty: true});
			item.server('get_lang_translation', [1, item.id.value], function(langs_info) {
				item.transl_table.disable_controls();
				try {
					for (var i = 0; i < langs_info.length; i++) {
						item.transl_table.append();
						item.transl_table.f_key.value = langs_info[i][0];
						item.transl_table.f_key_str.value = langs_info[i][1];
						item.transl_table.f_eng_str.value = langs_info[i][2];
						item.transl_table.f_value.value = langs_info[i][3];
						item.transl_table.post();
					}
				}
				finally {
					item.transl_table.enable_controls();
					item.transl_table.update_controls();
				}
				item.transl_table.on_after_scroll = function(t) {
					if (t.rec_count && !t.is_changing()) {
						t.edit();
					}
				}
				item.transl_table.first();
				item.transl_table.f_eng_str.read_only = true;
				item.transl_table.on_field_changed = function(field) {
					item.server('save_lang_translation',
						[item.id.value, item.transl_table.f_key.value, item.transl_table.f_value.value],
						function(res, err) {
							if (err) {
								item.warning(err);
							}
							else {
								item._language_changed = true;
							}
						}
					);
				}
			});
		}
	}
	
	function on_edit_form_close_query(item) {
		if (item.is_changing()) {
			item.cancel();
		}
		if (item._language_changed) {
			task.server('server_lang_modified');
		}
		return true;
	}
	this.save_file = save_file;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.on_edit_form_created = on_edit_form_created;
	this.on_edit_form_keyup = on_edit_form_keyup;
	this.get_lang_name = get_lang_name;
	this.get_lang_info = get_lang_info;
	this.lang_exists = lang_exists;
	this.find_lang = find_lang;
	this.on_field_changed = on_field_changed;
	this.fill_table = fill_table;
	this.on_edit_form_close_query = on_edit_form_close_query;
}

task.events.events9 = new Events9();

function Events10() { // app_builder.catalogs.sys_tasks 

	function on_after_edit(item) {
		item.f_manual_update.value = item.task._manual_update;
	}
	
	function on_after_apply(item) {
		if (task.init_project && item.f_db_type.value) {
			item.task.server('server_create_task');
			item.task.on_page_loaded(item.task);
		}
		item.task.update_db_manual_mode(item.task);
	}
	
	function update_db_type(item, db_type) {
		var res,
			db_options,
			error;
		if (db_type) {
			res = item.task.server('server_get_db_options', [db_type]);
			db_options = res[0];
			error = res[1];
			if (error) {
				item.warning(error);
				db_type = 0;
			}
		}
		if (db_type) {
			item.f_server.read_only = db_type !== 6;
			item.f_login.read_only = !db_options.NEED_DATABASE_NAME;
			item.f_login.read_only = !db_options.NEED_LOGIN;
			item.f_password.read_only = !db_options.NEED_PASSWORD;
			item.f_encoding.read_only = !db_options.NEED_ENCODING;
			item.f_host.read_only = !db_options.NEED_HOST;
			item.f_port.read_only = !db_options.NEED_PORT;
		}
		else {
			item.f_server.read_only = true;
			item.f_login.read_only = true;
			item.f_login.read_only = true;
			item.f_password.read_only = true;
			item.f_encoding.read_only = true;
			item.f_host.read_only = true;
			item.f_port.read_only = true;
		}
	}
	
	function on_edit_form_created(item) {
		update_db_type(item, item.f_db_type.value);
	}
	function on_edit_form_shown(item) {
	    $('input.f_password').prop("type", "password");  
	}
	function on_field_changed(field, lookup_item) {
		var item = field.owner,
			res,
			db_options,
			error;
		if (field === field.owner.f_db_type && field.value) {
			if (field.owner.is_changing()) {
				field.owner.f_alias.value = null;
				field.owner.f_login.value = null;
				field.owner.f_password.value = null;
				field.owner.f_encoding.value = null;
				field.owner.f_host.value = null;
				field.owner.f_port.value = null;
			}
			update_db_type(item, item.f_db_type.value);
		}
	}
	
	function on_before_post(item) {
		var error = item.task.server('server_check_connection', [
				item.f_db_type.value, item.f_alias.value, item.f_login.value,
				item.f_password.value, item.f_host.value, item.f_port.value,
				item.f_encoding.value, item.f_server.value
			]);
		if (error) {
			item.warning(error);
			item.abort();
		}
		if (task.init_project) {
			item.task.server('server_set_task_name',
				[item.f_name.value, item.f_item_name.value]);
		}
		item.task._manual_update = item.f_manual_update.value;
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
				return 'The port must be an integer value.';
			}
		}
	}
	this.on_after_edit = on_after_edit;
	this.on_after_apply = on_after_apply;
	this.update_db_type = update_db_type;
	this.on_edit_form_created = on_edit_form_created;
	this.on_field_changed = on_field_changed;
	this.on_before_post = on_before_post;
	this.on_after_post = on_after_post;
	this.on_field_validate = on_field_validate;
}

task.events.events10 = new Events10();

function Events11() { // app_builder.catalogs.sys_lookup_lists 

	function init_view_table(item, options) {
		item.view_options.width = 440;
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
			});
		});
	
	}
	
	function on_edit_form_created(item) {
		var lookups = item.task.sys_field_lookups.copy();
		lookups.edit_options.fields = ['f_value', 'f_lookup'];
		lookups.view_options.fields = ['f_value', 'f_lookup'];
		lookups.on_edit_form_created = function(l) {
			l.edit_form.find("#ok-btn").off('click.task').on('click', function() {
				l.post();
				l.close_edit_form();
			});
			l.edit_form.find("#cancel-btn").off('click.task').on('click', function() {
				l.cancel();
				l.close_edit_form();
			});
		};
		item.lookups = lookups;
		init_lookups(item);
		item.edit_form.find("#new-btn").on('click.task', function() {lookups.append_record()});
		item.edit_form.find("#edit-btn").on('click.task', function() {lookups.edit_record()});
		item.edit_form.find("#delete-btn").on('click', function() {
			item.question(task.language.delete_record, function() {
				lookups.delete();
			});
		});
	
		item.edit_table = lookups.create_table(item.edit_form.find(".edit-detail"),
			{
				height: 300,
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
			item.lookups.first();
		}
	}
	
	function on_before_post(item) {
		var list = [],
			rec = item.lookups.rec_no;
		item.lookups.each(function(l) {
			list.push([l.f_value.value, l.f_lookup.value]);
		});
		item.lookups.rec_no = rec;
		item.f_lookup_values_text.value = JSON.stringify(list);
	}
	this.init_view_table = init_view_table;
	this.can_delete = can_delete;
	this.on_view_form_created = on_view_form_created;
	this.on_edit_form_created = on_edit_form_created;
	this.init_lookups = init_lookups;
	this.on_before_post = on_before_post;
}

task.events.events11 = new Events11();

function Events14() { // app_builder.catalogs.sys_code_editor 

	var EditSession = require('ace/edit_session').EditSession;
	var UndoManager = require("ace/undomanager").UndoManager;
	
	function init_tabs(task) {
		$("#content").show();
		task.tabs = {};
		$('body').on('click', 'ul#task-tabs li', function(e) {
			e.preventDefault();
			e.stopPropagation();
			show_tab(task, $(this).attr('id'));
		});
		$('body').on('click', 'ul#task-tabs .close-editor-btn', function(e) {
			e.preventDefault();
			e.stopPropagation();
			close_editor(task, $(this).parent().parent().attr('id'));
		});
	}
	
	function resize(task, height) {
		if (task.code_editor.is(':visible')) {
			var footer = task.code_editor.find('.modal-footer'),
				center_box = task.code_editor.find("#center-box"),
				editor_box = task.code_editor.find("#editor-box"),
				left_box = task.code_editor.find('#left-box'),
				editor_tabs = task.code_editor.find('#editor-tabs'),
				info_grids = task.code_editor.find('#info-grids'),
				info_trees = task.code_editor.find('#editor-tabs div.info-tree'),
				dbtrees = task.code_editor.find('#editor-tabs div.info-tree .dbtree'),
				tabs_height = task.code_editor.find('ul.nav-tabs').outerHeight();
			if (footer.length) {
				height -= footer.outerHeight(true);
			}
			left_box.children().hide();
			left_box.hide();
			editor_box.hide();
			center_box.outerHeight(height, true);
			editor_box.outerHeight(center_box.height(), true);
			editor_box.show();
			left_box.outerHeight(height, true);
			left_box.show();
			editor_tabs.outerHeight(left_box.height(), true);
			editor_tabs.show();
			info_grids.outerHeight(left_box.height() - tabs_height, true);
			info_grids.show();
			info_trees.outerHeight(info_grids.height(), true);
			dbtrees.outerHeight(info_grids.height(), true);
			if (task.editor) {
				task.editor.resize();
			}
		}
	}
	
	function show_tab(task, tag) {
		$('ul#task-tabs li').removeClass('active');
		$('ul#task-tabs li#' + tag).addClass('active');
		if (tag === 'admin') {
			$('#tab-content #code-editor').hide();
			$('#tab-content #admin').show();
		}
		else {
			$('#tab-content #admin').hide();
			$('#tab-content #code-editor').show();
		}
		task.resize_elements(task);
		if (tag !== 'admin') {
			select_editor(task, tag);
		}
	}
	
	function show_editor(task, info) {
		var tag = info.tag;
		if (task.tabs[tag]) {
			show_tab(task, tag);
		}
		else {
			$('ul#task-tabs').append(
				'<li id="' + tag +
				'" class="active"><a href="#code-editor" data-toggle="tab"><span> ' +
			info.name + ' </span><i class="icon-remove close-editor-btn"></i></a></li>'
			);
			task.tabs[tag] = info;
			show_tab(task, tag);
		}
	}
	
	function close_editor(task, tag) {
		var tab = $('ul#task-tabs li#' + tag),
			new_tab;
			if (tab.next().length) {
				new_tab = tab.next();
			}
			else {
				new_tab = tab.prev();
			}
			show_tab(task, tag);
			close_query(task, tag, function () {
				show_tab(task, new_tab.attr('id'));
				delete task.tabs[tag];
				tab.remove();
			});
	}
	
	function close_query(task, tag, callback) {
		if (get_modified(task)) {
			task.yes_no_cancel(task.language.save_changes,
				function() {
					save_edit(task, tag);
					callback();
				},
				function() {
					mark_clean(task);
					callback();
				}
			);
		}
		else {
			callback();
		}
	}
	
	function init_editor(task) {
		task.editor = ace.edit("editor");
		task.editor.on('input', function() {
			$("#code-editor #error-info").text('');
			update_buttons(task);
		});
		task.code_editor.find('#ok-btn').click(function() {
			save_edit(task, $('ul#task-tabs li.active').attr('id'));
		});
		task.code_editor.find('#find-btn')
			.text(task.code_editor.find('#find-btn').text().replace('find_in_task', task.language.find_in_task))
			.click(function() {
				task.sys_search.find_in_task(task);
			}
		);
	
		task.code_editor.on('click', '#editor-tabs > .nav > li', function() {
			info_tab_clicked(task, $(this));
		});
		task.code_editor.on('dblclick', '.dbtree ul li', function(e) {
			e.preventDefault();
			e.stopPropagation();
			tree_node_clicked(task, $('ul#task-tabs li.active').attr('id'), $(this));
		});
	
		$(window).on('keydown.editor', function(e) {
			if (e.ctrlKey && e.which === 83) {
				var tag = $('ul#task-tabs li.active').attr('id');
				if (tag && tag !== 'admin') {
					e.preventDefault();
					save_edit(task, tag);
				}
			}
		});
	
		$(window).on('keyup.editor', function(e) {
			if (e.which === 27) {
				return;
				var tag = $('ul#task-tabs li.active').attr('id');
				if (tag && tag !== 'admin') {
					e.preventDefault();
					e.stopPropagation();
					e.stopImmediatePropagation();
					close_editor(task, tag);
				}
			}
		});
	}
	
	function select_editor(task, tag) {
		var info = task.tabs[tag],
			session;
		if (task.editor === undefined) {
			init_editor(task);
		}
		if (!info.session) {
			session = new EditSession(info.doc);
			session.setUndoManager(new UndoManager());
			if (info.ext === 'py') {
				session.setMode("ace/mode/python");
				session.setOption("tabSize", 4);
				session.setUseSoftTabs(true);
			}
			else if (info.ext === 'js') {
				session.setMode("ace/mode/javascript");
			}
			else if (info.ext === 'html') {
				session.setMode("ace/mode/html");
			}
			else if (info.ext === 'css') {
				session.setMode("ace/mode/css");
			}
			info.session = session;
			create_info_tabs(task, tag);
			$(task.editor).focus();
		}
		else {
			session = info.session;
		}
		task.editor.setSession(session);
		task.editor.$blockScrolling = Infinity;
		show_info_tabs(task, info);
		update_buttons(task);
		task.resize_elements(task);
		task.editor.focus();
	}
	
	function show_info_tabs(task, info) {
		task.code_editor.find("#editor-tabs").detach();
		task.code_editor.find('#left-box').append(info.editor_tabs);
		add_tree(task, task.task_dict, "task");
		if ($('#editor-tabs li#fields').length && info.item_id) {
			if (info.table_id) {
				info.fields = task.task_item_fields[info.table_id]
			}
			else {
				info.fields = task.task_item_fields[info.item_id]
			}
			add_tree(task, info.fields, "fields");
		}
		info_tab_clicked(task, $('#editor-tabs li.active'));
		if (info.name === 'project.css') {
			task.code_editor.find("#left-box").hide();
		}
		else {
			task.code_editor.find("#left-box").show();
		}
	}
	
	function update_buttons(task, info) {
		task.code_editor.find('#ok-btn').prop("disabled", !get_modified(task));
	}
	
	function update_error_message(task, mess) {
		task.code_editor.find('#error-info').text(mess);
	}
	
	function get_modified(task) {
		return !task.editor.session.getUndoManager().isClean();
	}
	
	function mark_clean(task) {
		task.editor.session.getUndoManager().markClean();
	}
	
	function save_module(task, info) {
		var text = task.editor.getValue(),
			result,
			error,
			line,
			module_info;
	
		if (info.doc_type === "server" && text.indexOf('\t') !== -1) {
			text = text.split('\t').join('  ');
			//task.editor.setValue(text);
		}
		result = task.task.server('server_save_edit', [info.rec_id, text, info.ext === 'py']);
	
		if (result.error && result.line && result.line < task.editor.session.getLength()) {
			task.editor.gotoLine(result.line);
		}
		if (!result.error) {
			info.module = result.module_info;
			add_tree(task, info.module, "module");
			update_tab_height(task);
		}
		return result.error;
	}
	
	function save_file(task, info) {
		var text = task.editor.getValue(),
			result =  task.server('server_save_file', [info.name, text]),
			error = result.error;
		if (info.name === 'index.html') {
			info.templates = task.sys_items.get_templates(text);
			add_tree(task, info.templates, "templates");
			update_tab_height(task);
		}
	}
	
	function save_edit(task, tag) {
		var error = '',
			info = task.tabs[tag];
		if (info.doc_type) {
			error = save_module(task, info);
		}
		else {
			error = save_file(task, info);
		}
		if (error) {
			update_error_message(task, error);
		}
		else {
			update_error_message(task, '');
			mark_clean(task);
			update_buttons(task)
		}
	}
	
	function create_info_tabs(task, tag) {
		var info = task.tabs[tag],
			editor_tabs;
		task.code_editor.find("#editor-tabs").detach();
		editor_tabs = $(
			'<div id="editor-tabs">' +
				'<ul class="nav nav-tabs editor">' +
				'</ul>' +
				'<div id="info-grids">' +
				'</div>' +
			'</div>'
		);
		task.code_editor.find('#left-box').append(editor_tabs);
		set_info_grids_height();
		if (info.doc_type) {
			task.code_editor.find('#editor-tabs ul')
				.append('<li id="module"><a href="#">Module</a></li>')
				.append('<li id="events"><a href="#">Events</a></li>')
				.append('<li id="task"><a href="#">Task</a></li>')
				.append('<li id="fields"><a href="#">Fields</a></li>');
	
			add_tree(task, info.module, "module");
			add_tree(task, info.events, "events");
			add_tree(task, task.task_dict, "task");
			add_tree(task, info.fields, "fields");
			info_tab_clicked(task, $('#editor-tabs li#module'));
		}
		else if (info.templates) {
			task.code_editor.find('#editor-tabs ul')
				.append('<li id="templates"><a href="#">templates</a></li>')
				.append('<li id="task"><a href="#">Task</a></li>');
			add_tree(task, info.templates, "templates");
			add_tree(task, task.task_dict, "task");
			info_tab_clicked(task, task.code_editor.find('#editor-tabs li#templates'));
		}
		else {
			task.code_editor.find('#editor-tabs ul')
				.append('<li id="task"><a href="#">Task</a></li>');
			add_tree(task, task.task_dict, "task");
			info_tab_clicked(task, task.code_editor.find('#editor-tabs li#task'));
		}
		info.editor_tabs = editor_tabs;
	}
	
	function add_tree(task, tree_info, info_name) {
		var tree_item = task.sys_code_editor.copy(),
			$li = task.code_editor.find('#editor-tabs ul li#' + info_name),
			tree_div;
	
		tree_div = task.code_editor.find('#editor-tabs #info-grids > div.' + info_name);
		if (tree_div.length) {
			tree_div.empty();
		}
		else {
			tree_div = $('<div id="' + info_name + '" class="info-tree ' + info_name + '">');
			task.code_editor.find('#editor-tabs #info-grids').append(tree_div);
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
	
	function info_tab_clicked(task, $li) {
		task.code_editor.find('#editor-tabs li').removeClass('active');
		$li.addClass('active');
		update_tab_height(task);
	}
	
	function tree_node_clicked(task, tag, $li) {
		var info = task.tabs[tag],
			tab = $li.closest('.info-tree').attr('id'),
			node_text = $li.find('span.tree-text:first').text(),
			text,
			result,
			params;
	
		if (tab === 'module') {
			task.editor.gotoLine(1);
			if (info.ext === 'py') {
				text = 'def ' + node_text;
			}
			else {
				text = 'function ' + node_text;
			}
			result = find_text(task, text);
		}
		else if (tab === 'events') {
			task.editor.gotoLine(1);
			if (!find_text(task, node_text + '(')) {
				params = info.events[node_text];
				task.editor.gotoLine(task.editor.session.getLength() + 1);
				if (info.ext === 'py') {
					text = 'def ' + node_text + '(' + params + '):\n\tpass';
				}
				else {
					text = 'function ' + node_text + '(' + params + ') {\n\n}';
				}
				task.editor.insert('\n\n' + text);
			}
		}
		else if (tab === 'task' || tab === 'fields') {
			task.editor.insert(node_text);
		}
		else if (tab === 'templates') {
			task.editor.gotoLine(1);
			text = node_text;
			find_text(task, text);
		}
		task.editor.focus();
	}
	
	function set_info_grids_height() {
		task.code_editor.find('#info-grids').height(
			task.code_editor.find('#left-box').innerHeight() - task.code_editor.find('ul.nav-tabs').outerHeight() - 14
		)
	}
	
	function update_tab_height(task) {
		var $li,
			dbtree,
			height;
		$li = task.code_editor.find('#editor-tabs > .nav > li.active');
		if ($li.length) {
			height = task.code_editor.find('#editor-tabs #info-grids').innerHeight();
			task.code_editor.find('#editor-tabs div.info-tree').hide();
			task.code_editor.find('#editor-tabs div.info-tree.' + $li.attr('id'))
				.show()
				.height(height)
				.find('.dbtree').height(height);
			dbtree = task.code_editor.find('#editor-tabs div.info-tree.' + $li.attr('id')).find('.dbtree').data('tree');
			if (dbtree) {
				dbtree.scroll_into_view();
			}
		}
	}
	
	function find_text(task, text) {
		return task.editor.find(text, {
			backwards: false,
			wrap: false,
			caseSensitive: true,
			wholeWord: true,
			regExp: false
		});
	}
	this.init_tabs = init_tabs;
	this.resize = resize;
	this.show_tab = show_tab;
	this.show_editor = show_editor;
	this.close_editor = close_editor;
	this.close_query = close_query;
	this.init_editor = init_editor;
	this.select_editor = select_editor;
	this.show_info_tabs = show_info_tabs;
	this.update_buttons = update_buttons;
	this.update_error_message = update_error_message;
	this.get_modified = get_modified;
	this.mark_clean = mark_clean;
	this.save_module = save_module;
	this.save_file = save_file;
	this.save_edit = save_edit;
	this.create_info_tabs = create_info_tabs;
	this.add_tree = add_tree;
	this.build_tree = build_tree;
	this.info_tab_clicked = info_tab_clicked;
	this.tree_node_clicked = tree_node_clicked;
	this.set_info_grids_height = set_info_grids_height;
	this.update_tab_height = update_tab_height;
	this.find_text = find_text;
}

task.events.events14 = new Events14();

function Events15() { // app_builder.catalogs.sys_fields_editor 

	var FORM_TEMPLATES = 0,
		FORM_OPTIONS = 1,
		FORM_ACTIONS = 2,
		TABLE_OPTIONS = 3,
		TABLE_FIELDS = 4,
		TABS = 3,
	
		TAB_NAME = 0,
		BANDS = 1,
		BAND_NAME = 2,
		BAND_OPTIONS = 0,
		BAND_FIELDS = 1;
	
	function fields_editor(type, item, title, source_def, source_list, dest_def, dest_object, save_func, cancel_func, can_move, read_only) {
		var editor = this.copy();
		editor.item = item;
		editor.type = type;
		editor.view_options.title = title;
		editor.source_def = source_def;
		editor.source_list = source_list;
		editor.dest_def = dest_def;
		editor.dest_object = dest_object;
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
	
	function set_cur_media(item, media) {
		var i,
			$tab,
			tabs;
		save_layout(item);
		//~ save_actions(item);
		if (item.dest_object.media = undefined) {
			if (item.type === 'view') {
				item.dest_object[media] = ['', {}, [], {}, []];
			} else if (item.type === 'edit') {
				item.dest_object[media] = { 0: ['', {}, [], [['', [[{}, [], '']]]]] };
			}
		}
		item.cur_media = item.dest_object[media];
		item.cur_media[FORM_OPTIONS] = set_form_options(item, item.cur_media[FORM_OPTIONS])
		if (item.type === 'view') {
			item.cur_media[TABLE_OPTIONS] = set_options(item, item.cur_media[TABLE_OPTIONS])
			item.dest_list = item.cur_media[TABLE_FIELDS];
		}
		else {
			tabs = item.cur_media[TABS];
			item.view_form.find('#field-tabs > li').remove();
			for (i = 0; i < tabs.length; i++) {
				$tab = $('<li><a href="#tab' + (i + 1) + '">' + item.cur_media[TABS][i][TAB_NAME] +  '</a></li>');
				$tab.data('tab', i);
				item.view_form.find('#field-tabs').append($tab);
			}
			if (tabs.length === 1 && tabs[0][TAB_NAME] === '') {
				item.view_form.find('#field-tabs > li').hide();
			}
			else {
				item.view_form.find('#field-tabs > li').show();
				item.view_form.find('#field-tabs > li').eq(0).addClass('active');
			}
			item.set_cur_tab(item, 0);
		}
		update_lists(item);
		//~ update_actions(item);
	}
	
	function set_cur_tab(item, tab) {
		var i,
			tabs = item.cur_media[TABS],
			band;
		item.cur_tab = tabs[tab];
		set_cur_band(item, item.cur_tab[BANDS][0]);
		item.view_form.find('#field-bands').empty();
		for (i = 0; i < item.cur_tab[BANDS].length; i++) {
			band = $('<li><a href="#band' + (i + 1) + '">' + item.cur_tab[BANDS][i][BAND_NAME] +  '</a></li>');
			band.data('band', item.cur_tab[BANDS][i]);
			item.view_form.find('#field-bands').append(band);
		}
		if (item.cur_tab[BANDS].length === 1 && item.cur_tab[BANDS][0][BAND_NAME] === '') {
			item.view_form.find('#field-bands > li').hide();
		}
		else {
			item.view_form.find('#field-bands > li').show();
			item.view_form.find('#field-bands > li').eq(0).addClass('active');
		}
	}
	
	function set_cur_band(item, band) {
		save_layout(item);
		item.cur_band = band;
		band[BAND_OPTIONS] = set_options(item, band[BAND_OPTIONS]);
		item.dest_list = item.cur_band[BAND_FIELDS];
		update_lists(item);
	}
	
	function set_editor_type(item) {
		var i,
			tab;
		if (item.type === 'edit' || item.type === 'view') {
			item.view_form.find('#section-tabs').show();
			item.view_form.find('#buttons').hide();
			item.view_form.find('#form').hide();
			item.view_form.on('click', '#section-tabs > li > a',
				function(e) {
					e.preventDefault();
					$('#section-tabs > li').removeClass('active');
					$(this).parent().addClass('active');
					if ($(this).attr("href") === '#layout') {
						item.view_form.find('#layout').show();
						item.view_form.find('#buttons').hide();
						item.view_form.find('#form').hide();
					}
					else if ($(this).attr("href") === '#buttons') {
						item.view_form.find('#layout').hide();
						item.view_form.find('#buttons').show();
						item.view_form.find('#form').hide();
						//~ refresh_actions(item);
					}
					else {
						item.view_form.find('#layout').hide();
						item.view_form.find('#buttons').hide();
						item.view_form.find('#form').show();
					}
				}
			);
			set_cur_media(item, 0);
			item.view_form.find('#media-tabs').show();
			item.view_form.on('click', '#media-tabs > li > a',
				function(e) {
					e.preventDefault();
					$('#media-tabs > li').removeClass('active');
					$(this).parent().addClass('active');
					set_cur_media(item, $(this).parent().data('media'));
				}
			);
			if (item.type === 'edit') {
				item.view_form.find('#media-tabs').show();
				item.view_form.find('#field-tabs').show();
				item.view_form.find('#bands-box').show();
				item.view_form.on('click', '#field-tabs > li > a',
					function(e) {
						e.preventDefault();
						$('#field-tabs > li').removeClass('active');
						$(this).parent().addClass('active');
						set_cur_tab(item, $(this).parent().data('tab'))
					}
				);
				item.view_form.on('click', '#field-bands > li > a',
					function(e) {
						e.preventDefault();
						$('#field-bands > li').removeClass('active');
						$(this).parent().addClass('active');
						set_cur_band(item, $(this).parent().data('band'));
					}
				);
				item.view_form.find('#add-tab-btn')
					.tooltip({placement: 'bottom', title: 'New tab', trigger: 'hover'})
					.click(function() {
						change_ed(item, 'new_tab');
					});
				item.view_form.find('#edit-tab-btn')
					.tooltip({placement: 'bottom', title: 'Edit tab', trigger: 'hover'})
					.click(function() {
						change_ed(item, 'edit_tab');
					});
				item.view_form.find('#delete-tab-btn')
					.tooltip({placement: 'bottom', title: 'Delete tab', trigger: 'hover'})
					.click(function() {
						change_ed(item, 'del_tab');
					});
				item.view_form.find('#add-band-btn')
					.tooltip({placement: 'top', title: 'New band', trigger: 'hover'})
					.click(function() {
						change_ed(item, 'new_band');
					});
				item.view_form.find('#delete-band-btn')
					.tooltip({placement: 'top', title: 'Delete band', trigger: 'hover'})
					.click(function() {
						change_ed(item, 'del_band');
					});
			}
		}
		else {
			item.dest_list = item.dest_object;
			update_lists(item);
		}
	}
	
	function change_ed(item, op) {
		var index,
			band,
			$band;
		if (op === 'del_tab') {
			if (item.cur_media[TABS].length === 1) {
				item.cur_media[TABS][0][TAB_NAME] = '';
				item.view_form.find('#field-tabs > li.active').hide();
			}
			else {
				index = item.cur_media[TABS].indexOf(item.cur_tab);
				item.cur_media[TABS].splice(index, 1);
				if (index === item.cur_media[TABS].length) {
					index -= 1;
				}
				item.view_form.find('#field-tabs > li.active').remove()
				item.view_form.find('#field-tabs > li').eq(index).addClass('active');
				set_cur_tab(item, index);
			}
		}
		else if (op === 'new_band') {
			if (item.cur_tab[BANDS].length === 1 && item.cur_tab[BANDS][0][BAND_NAME] === '') {
				item.cur_tab[BANDS][0][BAND_NAME] = 'Band 1';
				item.view_form.find('#field-bands > li > a').text('Band 1');
				item.view_form.find('#field-bands > li').show();
			}
			else {
				band = [{}, [], 'Band ' + (item.cur_tab[BANDS].length + 1)];
				$('#field-bands > li').removeClass('active');
				item.cur_tab[BANDS].push(band)
				$band = $('<li class="active"><a href="#band"' + (item.cur_tab[BANDS].length + 1) + '>' + band[BAND_NAME] +  '</a></li>');
				$band.data('band', band)
				item.view_form.find('#field-bands').append($band);
				set_cur_band(item, band);
			}
		}
		else if (op === 'del_band') {
			if (item.cur_tab[BANDS].length === 1) {
				item.cur_tab[BANDS][0][BAND_NAME] = '';
				item.view_form.find('#field-bands > li.active').hide();
			}
			else {
				index = item.cur_tab[BANDS].indexOf(item.cur_band);
				item.cur_tab[BANDS].splice(index, 1);
				if (index === item.cur_tab[BANDS].length) {
					index -= 1;
				}
				item.view_form.find('#field-bands > li.active').remove()
				item.view_form.find('#field-bands > li').eq(index).addClass('active');
				set_cur_band(item, item.cur_tab[BANDS][index]);
			}
		}
		else {
			var it = item.copy({handlers: false});
			it.open({open_empty: true});
			it.on_edit_form_created = function(item1) {
				item1.edit_form.find('#ok-btn')
					.off('click.task')
					.on('click', function() {
						var tab,
							$tab,
							band;
						if (it.name.value) {
							if (op === 'new_tab') {
								if (item.cur_media[TABS].length === 1 && item.cur_media[TABS][0][TAB_NAME] === '') {
									item.cur_media[TABS][0][TAB_NAME] = it.name.value;
									item.view_form.find('#field-tabs > li > a').text(it.name.value);
									item.view_form.find('#field-tabs > li').addClass('active').show();
								}
								else {
									tab = [it.name.value, [[{}, [], '']]];
									item.view_form.find('#field-tabs > li').removeClass('active');
									item.cur_media[TABS].push(tab)
									$tab = $('<li class="active"><a href="#tab' + (item.cur_media[TABS].length + 1) + '">' + tab[TAB_NAME] +  '</a></li>');
									$tab.data('tab', item.cur_media[TABS].length - 1);
									item.view_form.find('#field-tabs').append($tab);
									set_cur_tab(item, item.cur_media[TABS].length - 1);
								}
							}
							else if (op === 'edit_tab') {
								item.cur_tab[TAB_NAME] = it.name.value;
								item.view_form.find('#field-tabs > li.active a').text(it.name.value);
							}
							it.cancel_edit();
						}
					})
			};
			it.edit_options.fields = ['name'];
			it.edit_options.width = 400;
			it.append();
			if (op === 'new_tab') {
				it.edit_options.title = 'New tab';
			}
			else if (op === 'edit_tab') {
				if (item.cur_media[TABS].length === 1 && item.cur_media[TABS][0][TAB_NAME] === '') {
					return
				}
				else {
					it.edit_options.title = 'Edit tab';
					it.name.value = item.cur_tab[TAB_NAME];
				}
			}
			it.edit_record();
		}
	}
	
	function set_form_options(item, options) {
		return set_options(item, options, true);
	}
	
	function set_options(item, options, is_form) {
		var i,
			container,
			option_value,
			new_options,
			options_list,
			options_default,
			opt_fields = [];
		//~ if (options && !item._options_changing) {
		item._options_changing = true;
		try {
			item.on_field_get_text = function(field) {
				if (field.value === 0) {
					return ''
				}
			};
			if (is_form) {
				if (item.type === 'edit') {
					options_list = item.item.edit_form_options_list(item.item);
				}
				if (item.type === 'view') {
					options_list = item.item.view_form_options_list(item.item);
				}
				container = item.view_form.find('#form-options-div');
				item.view_form.find('#form-options-box').show();
			}
			else {
				if (item.type === 'edit') {
					options_list = item.item.edit_options_list(item.item);
				}
				if (item.type === 'view') {
					options_list = item.item.view_options_list(item.item);
				}
				container = item.view_form.find('#options-div');
				item.view_form.find('#options-box').show();
			}
			options_list = JSON.parse(JSON.stringify(options_list));
	
			if (!options_list.length) {
				return {};
			}
			if (!item.is_changing()) {
				item.open({open_empty: true});
				item.append();
			}
			new_options = {}
			for (i = 0; i < options_list.length; i++) {
				option_value = options_list[i][1];
				if (options[options_list[i][0]] !== undefined ) {
					option_value = options[options_list[i][0]]
					new_options[options_list[i][0]] = option_value;
				}
				item[options_list[i][0]].value = option_value;
				opt_fields.push(options_list[i][0]);
			}
			options = new_options;
			item.create_inputs(container,
				{fields: opt_fields, in_well: false, label_width: 140});
			item.on_field_changed = update_option;
			item.on_field_select_value = function(field, lookup_item) {
				if (field.field_name === 'edit_details' || field.field_name === 'view_detail') {
					lookup_item.set_where({parent: item.item.id.value});
					lookup_item.view_options.fields = ['f_item_name'];
					lookup_item.set_order_by(['f_item_name']);
					lookup_item.on_after_scroll = undefined;
					if (field.field_name === 'view_detail') {
						lookup_item.view_options.title = 'Select details to view';
					}
					else {
						lookup_item.view_options.title = 'Select details to edit';
					}
				}
				else {
					var ids = [],
						clone = item.dest.clone(),
						where = {id__in: ids};
					clone.each(function(c) {
						ids.push(c.id.value);
					})
					if (field.field_name === 'summary_fields') {
						lookup_item.view_options.title = 'Select summary fields';
					}
					else if (field.field_name === 'sort_fields') {
						lookup_item.view_options.title = 'Select fields to sort by';
					}
					else if (field.field_name === 'search_field') {
						where.f_data_type__not_in = [task.consts.DATE, task.consts.DATETIME, task.consts.BOOLEAN];
					}
					else {
						lookup_item.view_options.title = 'Select fields to edit';
						where['f_master_field__isnull'] = true;
					}
					lookup_item.set_where(where);
					lookup_item.view_options.fields = ['f_field_name'];
					lookup_item.set_order_by(['f_field_name']);
					if (field.field_name === 'search_field') {
						lookup_item.view_options.title = 'Select default search field';
						lookup_item.on_selection_changed = function(it, added, deleted) {
							if (!lookup_item.sel_changing) {
								lookup_item.sel_changing = true;
								try {
									if (it.selections.length > 1) {
										it.selections = added;
									}
								}
								finally {
									lookup_item.sel_changing = false;
								}
							}
						}
					}
				}
				lookup_item.view_options.width = 300;
			}
		}
		finally {
			item._options_changing = false;
		}
		return options;
	}
	
	function update_option(field) {
		var i,
			index,
			item = field.owner,
			form_options,
			options_list,
			options;
		if (!item._options_changing) {
			options = item.cur_media[FORM_OPTIONS];
			if (item.type === 'edit') {
				options_list = item.item.edit_form_options_list(item.item);
			}
			if (item.type === 'view') {
				options_list = item.item.view_form_options_list(item.item);
			}
			for (i = 0; i < options_list.length; i++) {
				if (options_list[i][0] === field.field_name) {
					form_options = true;
					break;
				}
			}
			if (!form_options) {
				if (item.type === 'edit') {
					options = item.cur_band[BAND_OPTIONS];
					options_list = item.item.edit_options_list(item.item);
				}
				if (item.type === 'view') {
					options = item.cur_media[TABLE_OPTIONS];
					options_list = item.item.view_options_list(item.item);
				}
			}
			delete options[field.field_name];
			if (field.value instanceof Array) {
				if (field.value.length !== 0) {
					options[field.field_name] = field.value;
				}
			}
			else {
				for (i = 0; i < options_list.length; i++) {
					if (options_list[i][0] === field.field_name) {
						if (options_list[i][1] !== field.value) {
							options[field.field_name] = field.value;
						}
					}
				}
			}
		}
	}
	
	function on_view_form_created(item) {
		if (item.type === 'edit') {
			item.view_options.width = 1080;
		}
		else if (item.type === 'view') {
			item.view_options.width = 960;
		}
		else {
			item.view_options.width = 660;
		}
		set_layout(item);
		//~ set_actions(item);
	}
	
	function on_view_form_shown(item) {
		set_editor_type(item);
	}
	
	function set_layout(item) {
		var name_width = {},
			i,
			view_fields;
	
		item.fields = item.copy()
	
		if (item.dest_def[1].length === 4) {
			name_width = {'name': item.dest_def[1][3]};
		}
		item.source = item.copy(),
		view_fields = [];
		for (i = 0; i < item.source_def.length; i++) {
			if (item.source_def[i][2]) {
				view_fields.push(item.source_def[i][0]);
			}
		}
		item.source.set_view_fields(view_fields);
		item.source.open({open_empty: true});
		for (i = 0; i < item.source_def.length; i++) {
			if (item.source_def[i][2]) {
				item.source.field_by_name(item.source_def[i][0]).field_caption = item.source_def[i][1];
			}
		}
	
		item.dest = item.copy();
		view_fields = []
		for (i = 0; i < item.dest_def.length; i++) {
			if (item.dest_def[i][2]) {
				view_fields.push(item.dest_def[i][0]);
			}
		}
		item.dest.set_view_fields(view_fields);
		item.dest.open({open_empty: true});
		for (i = 0; i < item.dest_def.length; i++) {
			if (item.dest_def[i][2]) {
				item.dest.field_by_name(item.dest_def[i][0]).field_caption = item.dest_def[i][1];
			}
		}
	
		item.left_grid = item.dest.create_table(item.view_form.find("#left-grid"), {
			height: 360,
			column_width: name_width,
			editable: true,
			editable_fields: ['param3'],
			dblclick_edit: false,
			striped: false
		});
		item.right_grid = item.source.create_table(item.view_form.find("#right-grid"), {
			height: 360,
			dblclick_edit: false,
			striped: false
		});
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
			.text(item.task.language.cancel)
			.on('click.task', function(e) {item_cancel(item);});
		item.view_form.find("#ok-btn")
			.text(item.task.language.ok)
			.on('click.task', function() {save_result(item)});
		if (item.read_only) {
			item.view_form.find("button.arrow_btn").hide();
		}
		item.left_grid.$table.on('click', 'td', function() {
			var $td = $(this),
				field_name = $td.data('field_name'),
				field = item.dest.field_by_name(field_name);
			if (field.field_type === "boolean" && !item.read_only) {
				if (!item.dest.is_changing()) {
					item.dest.edit();
				}
				field.value = !field.value;
				item.dest.post();
			}
		})
	}
	
	function get_source_list(item) {
		var i,
			j,
			k,
			m,
			s,
			d,
			found,
			tab,
			band,
			result = [];
		if (item.type === 'edit') {
			for (i = 0; i < item.source_list.length; i++) {
				s = item.source_list[i];
				found = false;
				for (j = 0; j < item.cur_media[TABS].length; j++) {
					tab = item.cur_media[TABS][j]
					for (k = 0; k < tab[BANDS].length; k++) {
						band = tab[BANDS][k];
						for (m = 0; m < band[BAND_FIELDS].length; m++) {
							d = band[BAND_FIELDS][m];
							if (s[0] === d[0]) {
								found = true;
								break;
							}
						}
						if (found) {
							break;
						}
					}
					if (found) {
						break;
					}
				}
				if (!found) {
					result.push(s.slice());
				}
			}
			return result;
		}
		else {
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
					result.push(s.slice());
				}
			}
		}
		return result;
	}
	
	function update_lists(item) {
		var i,
			j,
			k,
			found,
			f_names,
			s,
			d;
		item.s_list = get_source_list(item);
		item.d_list = []
		f_names = []
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
				f_names.push(s[1]);
				item.d_list.push(d.slice());
			}
		}
		item.source.disable_controls();
		try {
			item.source.first();
			while (!item.source.eof()) {
				item.source.delete();
			}
			for (i = 0; i < item.s_list.length; i++) {
				s = item.s_list[i];
				item.source.append();
				for (k = 0; k < item.source_def.length; k++) {
					item.source.field_by_name(item.source_def[k][0]).value = s[k];
				}
				item.source.post();
			}
			item.source.first();
		}
		finally {
			item.source.enable_controls();
		}
		item.source.update_controls();
	
		item.dest.disable_controls();
		try {
			item.dest.first();
			while (!item.dest.eof()) {
				item.dest.delete();
			}
			for (i = 0; i < item.d_list.length; i++) {
				d = item.d_list[i];
				item.dest.append();
				item.dest.id.value = d[0];
				item.dest.name.value = f_names[i];
				for (k = 2; k < item.dest_def.length; k++) {
					item.dest.field_by_name(item.dest_def[k][0]).value = d[k - 1];
				}
				item.dest.post();
			}
			item.dest.first();
		}
		finally {
			item.dest.enable_controls();
		}
		item.dest.update_controls();
	}
	
	function move_hor(item, source, dest) {
		if (source.record_count()) {
			dest.append();
			dest.id.value = source.id.value;
			dest.name.value = source.name.value;
			dest.post();
			source.delete();
			update_selected_fields(item);
		}
	}
	
	function update_selected_fields(item) {
		var i,
			field_names = ['sort_fields', 'edit_fields', 'summary_fields', 'search_field'],
			field,
			clone = item.dest.clone(),
			values,
			new_values;
		if (!item._options_changing) {
			for (i = 0; i < field_names.length; i++) {
				field = item.field_by_name(field_names[i]);
				if (field && field.value.length && field.field_type === 'keys') {
					values = field.value;
					new_values = []
					clone.each(function(c) {
						if (values.indexOf(c.id.value) !== -1) {
							new_values.push(c.id.value)
						}
					});
					if (!item.is_changing()) {
						item.edit();
					}
					field.value = new_values;
				}
			}
		}
	}
	
	function move_left(item) {
		move_hor(item, item.source, item.dest);
	}
	
	function move_right(item) {
		move_hor(item, item.dest, item.source);
	}
	
	function save_layout(item) {
		var dest_list = [],
			rec = item.dest.rec_no;
		if (item.dest_list) {
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
			if (item.type === 'edit') {
				item.cur_band[BAND_FIELDS] = dest_list;
			}
			else if (item.type === 'view') {
				item.cur_media[TABLE_FIELDS] = dest_list;
			}
			else {
				item.dest_object = dest_list;
			}
		}
	}
	
	function save_result(item) {
		save_layout(item);
		//~ save_actions(item);
		item.save_func(item.item, item.dest_object);
		item.close_view_form();
	}
	
	function on_view_form_close_query(item) {
		if (item.item.is_changing()) {
			if (item.cancel_func) {
				item.cancel_func(item.item);
			}
		}
	}
	
	function item_cancel(item) {
		item.close_view_form();
	}
	this.fields_editor = fields_editor;
	this.set_cur_media = set_cur_media;
	this.set_cur_tab = set_cur_tab;
	this.set_cur_band = set_cur_band;
	this.set_editor_type = set_editor_type;
	this.change_ed = change_ed;
	this.set_form_options = set_form_options;
	this.set_options = set_options;
	this.update_option = update_option;
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_shown = on_view_form_shown;
	this.set_layout = set_layout;
	this.get_source_list = get_source_list;
	this.update_lists = update_lists;
	this.move_hor = move_hor;
	this.update_selected_fields = update_selected_fields;
	this.move_left = move_left;
	this.move_right = move_right;
	this.save_layout = save_layout;
	this.save_result = save_result;
	this.on_view_form_close_query = on_view_form_close_query;
	this.item_cancel = item_cancel;
}

task.events.events15 = new Events15();

function Events16() { // app_builder.catalogs.sys_search 

	function find_in_task(task) {
		var search = task.sys_search.copy();
		search.open({open_empty: true});
		search.set_edit_fields(['find_text', 'case_sensitive', 'whole_words']);
		search.append_record();
	}
	
	function on_edit_form_created(item) {
		item.edit_form.title = task.language.find;
		item.edit_form.find("#cancel-btn")
			.text(task.language.close);
		item.edit_form.find("#ok-btn")
			.text(task.language.find)
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
				lines = result.client.split('\n');
				for (i = 0; i < lines.length; i++) {
					$p = $('<p style="margin: 0px;">').text(lines[i]);
					$p.css("font-family", "'Courier New', Courier, monospace");
					html.append($p);
				}
				html.append($('<h4>Server</h4>'));
				lines = result.server.split('\n');
				for (i = 0; i < lines.length; i++) {
					$p = $('<p style="margin: 0px;">').text(lines[i]);
					$p.css("font-family", "'Courier New', Courier, monospace");
					html.append($p);
				}
				task.message(html,
					{title: 'Search result', margin: 10, width: width, height: height,
						text_center: false, buttons: {"Close": undefined}, center_buttons: false, print: true}
				);
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

function Events18() { // app_builder.catalogs.sys_languages 

	function on_view_form_created(item) {
		item.view_options.width = 400;
		item.view_form.find("#select-btn").click(function() {
			item.lookup_field.value = item.id.value;
		});
	}
	this.on_view_form_created = on_view_form_created;
}

task.events.events18 = new Events18();

function Events19() { // app_builder.catalogs.sys_countries 

	function on_view_form_created(item) {
		item.view_options.width = 400;
		item.view_form.find("#select-btn").click(function() {
			item.lookup_field.value = item.id.value;
		});
	}
	this.on_view_form_created = on_view_form_created;
}

task.events.events19 = new Events19();

function Events21() { // app_builder.details.sys_report_params 

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
		if (field.field_name === 'f_object_field' && lookup_item) {
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
		task.sys_items.sys_fields.update_fields_read_only(item);
	}
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_close_query = on_view_form_close_query;
	this.on_before_post = on_before_post;
	this.on_after_append = on_after_append;
	this.on_field_changed = on_field_changed;
	this.on_field_select_value = on_field_select_value;
	this.on_edit_form_created = on_edit_form_created;
}

task.events.events21 = new Events21();

function Events22() { // app_builder.details.sys_indices 

	function on_view_form_created(item) {
		item.view_form.find("#edit-btn").text(item.task.language.view);
		if (item.foreign_index) {
			item.f_index_name.field_caption = 'Foreign key';
			item.view_options.fields = ['f_foreign_field', 'f_index_name' ];
			item.edit_options.fields = item.view_options.fields;
			item.f_foreign_field.required = true;
			item.f_index_name.required = true;
		}
		else {
			item.f_index_name.field_caption = 'Index';
			if (item.task.db_options.DATABASE === 'FIREBIRD') {
				item.view_options.fields = ['f_index_name', 'f_unique_index', 'descending'];
			}
			else {
				item.view_options.fields = ['f_index_name', 'f_unique_index'];
			}
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
			};
		}
		item.can_modify = !(task._production && !task._manual_update);
		if (!item.can_modify) {
			item.view_form.find('#delete-btn').prop('disabled', true);
			item.view_form.find('#new-btn').prop('disabled', true);
		}
	
	}
	
	function on_view_form_keydown(item, event) {
		if (event.keyCode === 45 && event.ctrlKey === true){
			event.preventDefault();
			if (item.foreign_index) {
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
				item.f_fields_list.value = item.server('server_dump_index_fields', [dest_list]);
				item.post();
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
				index_list = item.server('server_load_index_fields', [item.f_fields_list.value]);
			}
			else {
				return;
			}
		}
	
		source_def = [
			['id', '', false],
			['name', item.task.language.caption_name, true]
		];
		if (item.task.db_options.DATABASE === 'FIREBIRD') {
			dest_def = [
				['id', '', false],
				['name', item.task.language.caption_name, true]
			];
		}
		else {
			dest_def = [
				['id', '', false],
				['name', item.task.language.caption_name, true],
				['param1', item.task.language.caption_descening, true]
			];
		}
	
		editor = item.task.sys_fields_editor.fields_editor('indices', item, title, source_def, get_fields_list(item.task), dest_def, index_list,
			save_edit, cancel_edit, undefined, !is_new);
		item.create_inputs(editor.view_form.find('div#fields-container'));
	}
	
	function on_after_append(item) {
		var task_name = item.task.task_name,
			item_name = item.task.sys_items.f_item_name.value;
		if (!item.foreign_index) {
			item.f_index_name.value = item.task.server('server_set_literal_case', task_name + '_' + item_name + '_' + 'idx');
		}
		item.task_id.value = item.task.sys_items.task_id.value;
		item.owner_rec_id.value = item.task.sys_items.id.value;
		item.f_foreign_index.value = item.foreign_index;
	}
	
	function on_field_select_value(field, lookup_item) {
	
		function filter_record(item) {
			var clone,
				valid,
				soft_delete;
			if (item.f_object.value && !item.f_master_field.value) {
				soft_delete = item.task.sys_items.field_by_id(item.f_object.value, 'f_soft_delete');
				if (!soft_delete) {
					clone = field.owner.clone();
					valid = true;
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
	
		var item = task.sys_items;
		lookup_item.view_options.fields = ['f_name', 'f_field_name'];
		lookup_item.set_where({owner_rec_id__in: [item.id.value, item.parent.value]});
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
	
	function on_before_apply(item, params) {
		params.manual_update = item.task._manual_update;
	}
	this.on_view_form_created = on_view_form_created;
	this.on_view_form_keydown = on_view_form_keydown;
	this.edit_index = edit_index;
	this.on_after_append = on_after_append;
	this.on_field_select_value = on_field_select_value;
	this.on_field_changed = on_field_changed;
	this.on_field_validate = on_field_validate;
	this.on_before_apply = on_before_apply;
}

task.events.events22 = new Events22();

function Events23() { // app_builder.details.sys_filters 

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
		item.owner_rec_id.value = item.task.sys_items.id.value;
		item.owner.value = item.task.sys_items.ID;
	}
	
	function on_field_changed(field, lookup_item) {
		var fields,
			item = field.owner;
		if (field.field_name === 'f_field') {
			fields = item.task.sys_fields.copy();
			fields.set_where({id: field.value});
			fields.open();
			item.f_name.value = fields.f_name.value;
			item.f_filter_name.value = fields.f_field_name.value;
			item.f_help.value = fields.f_help.value;
		}
	//	update_multi_select_all(item);
	}
	
	function on_field_select_value(field, lookup_item) {
		var items,
			item = field.owner;
		if (field.field_name === 'f_field') {
			items = item.copy();
			lookup_item.set_where({
				owner_rec_id__in: [item.task.sys_items.id.value, item.task.sys_items.parent.value],
				f_master_field__isnull: true
			});
			lookup_item.set_view_fields(['f_field_name', 'f_name']);
			lookup_item.set_order_by(['f_field_name']);
		}
	}
	
	function on_view_form_close_query(item) {
		var i = 0;
		item.each(function(it) {
			it.edit();
			it.f_index.value = i;
			it.post();
			i++;
		});
		item.apply();
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

task.events.events23 = new Events23();

function Events24() { // app_builder.details.sys_privileges 

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
				field.value = !field.value;
			}
		});
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
			item.rec_no = rec_no;
			item.enable_controls();
			item.update_controls();
		}
	}
	
	function unselect_all_clicked(item) {
		select_all_clicked(item, false);
	}
	
	function on_view_form_close_query(item) {
		var copy = item.copy();
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
				});
				copy.post();
				item.delete();
			}
		}
		item.apply(function() {});
		copy.apply(function() {});
	}
	
	function on_view_form_closed(item) {
		item.task.sys_roles.server('roles_changed');
	}
	this.on_view_form_created = on_view_form_created;
	this.select_all_clicked = select_all_clicked;
	this.unselect_all_clicked = unselect_all_clicked;
	this.on_view_form_close_query = on_view_form_close_query;
	this.on_view_form_closed = on_view_form_closed;
}

task.events.events24 = new Events24();

function Events25() { // app_builder.details.sys_field_lookups 

	// function on_field_validate(field) {
	//	 if (field.field_name === 'f_value' && field.value <= 0) {
	//		 return 'Value must be greater than zero';
	//	 }
	// }
}

task.events.events25 = new Events25();

function Events26() { // app_builder.catalogs.sys_items.sys_fields 

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
	
		var fields;
	
		item.edit_form.find('#field-edit a').click(function (e) {
			e.preventDefault();
			$(this).tab('show');
		});
	
		item.f_field_name.read_only = item.f_field_name.value === 'id' || item.f_field_name.value === 'deleted' ||
			item.f_field_name.value === 'owner_id' || item.f_field_name.value === 'owner_rec_id';
		item.f_data_type.read_only = false;
		item.f_size.read_only = false;
		item.f_object.read_only = false;
		item.f_object_field.read_only = false;
		item.f_master_field.read_only = false;
		item.f_lookup_values.read_only = true;
		item.f_default_lookup_value.lookup_values = [];
	
		update_fields_read_only(item);
		if (check_in_foreign_index()) {
			item.f_object.read_only = true;
		}
		if (item.task._manual_update) {
			fields = ['f_name', 'f_field_name',  'f_db_field_name', 'f_data_type', 'f_size', 'f_default_value', 'f_default_lookup_value', 'f_required', 'f_read_only'];
		}
		else {
			fields = ['f_name', 'f_field_name',  'f_data_type', 'f_size', 'f_default_value', 'f_default_lookup_value', 'f_required', 'f_read_only'];
		}
		item.create_inputs(item.edit_form.find("#definition"), {fields: fields});
		item.create_inputs(item.edit_form.find("#lookups"),
			{fields: ['f_object', 'f_object_field', 'f_object_field1', 'f_object_field2', 'f_master_field',
				'f_enable_typehead', 'f_lookup_values']});
		item.create_inputs(item.edit_form.find("#interface"),
			{fields: ['f_alignment', 'f_mask', 'f_do_not_sanitize', 'f_placeholder', 'f_help']});
		item.create_inputs(item.edit_form.find("#text-interface"),
			{fields: ['f_alignment', 'f_mask', 'f_textarea', 'f_do_not_sanitize', 'f_placeholder', 'f_help']});
		item.create_inputs(item.edit_form.find("#file-interface"),
			{fields: ['f_file_download_btn', 'f_file_open_btn', 'f_file_accept', 'f_help']});
		item.create_inputs(item.edit_form.find("#image-interface1"),
			{fields: ['f_image_view_width', 'f_image_view_height', 'f_image_edit_width', 'f_image_edit_height'], col_count: 2, label_size: 2});
		item.create_inputs(item.edit_form.find("#image-interface2"),
			{fields: ['f_image_camera'], col_count: 1, label_size: 2});
		item.create_inputs(item.edit_form.find("#image-interface3"),
			{fields: ['f_image_placeholder']});
		item.create_inputs(item.edit_form.find("#calc"), {fields: ['f_calc_item', 'f_calc_field', 'f_calc_op', 'f_do_not_sanitize']});
	
		update_iterface_tab(item);
	
		update_default_value(item);
	
		item.edit_form.find('textarea.f_help').attr('rows', 3).height(120);
	
		item.edit_form.find("#cancel-btn")
			.text(item.task.language.cancel)
			.on('click.task', function(e) {item.cancel_edit(e); return false;});
		item.edit_form.find("#ok-btn")
			.html(item.task.language.ok + '<small class="muted">&nbsp;[Ctrl+Enter]</small>')
			.on('click.task', function() {item.apply_record()});
	}
	
	function update_iterface_tab(item) {
		if (item.f_data_type.value === item.task.consts.TEXT) {
			item.edit_form.find("#interface").hide();
			item.edit_form.find("#text-interface").show();				
			item.edit_form.find("#image-interface").hide();
			item.edit_form.find("#file-interface").hide();
		}
		else if (item.f_data_type.value === item.task.consts.FILE) {
			item.edit_form.find("#interface").hide();
			item.edit_form.find("#text-interface").hide();		
			item.edit_form.find("#image-interface").hide();
			item.edit_form.find("#file-interface").show();
			if (item.is_changing()) {
				if (!item.f_file_download_btn.value && !item.f_file_open_btn.value) {
					item.f_file_download_btn.value = true;
					item.f_file_open_btn.value = true;
				}
			}
		}
		else if (item.f_data_type.value === item.task.consts.IMAGE) {
			item.edit_form.find("#interface").hide();
			item.edit_form.find("#text-interface").hide();				
			item.edit_form.find("#image-interface").show();
			item.edit_form.find("#file-interface").hide();
			if (item.is_changing()) {
				if (!item.f_image_view_width.value && !item.f_image_view_height.value) {
					item.f_image_view_width.value = 100;
				}
				if (!item.f_image_edit_width.value && !item.f_image_edit_height.value) {
					item.f_image_edit_width.value = 200;
				}
			}
		}
		else {
			item.edit_form.find("#interface").show();
			item.edit_form.find("#text-interface").hide();				
			item.edit_form.find("#image-interface").hide();
			item.edit_form.find("#file-interface").hide();
		}
	}
	
	function on_edit_form_shown(item) {
		let caption = 'Field Editor',
			link = task.help_badge('http://jam-py.com/docs/admin/items/field_editor_dialog.html');
		if (item.f_field_name.value) {
			item.edit_form.find('h4.modal-title')
				.html(caption + ' <span class="editor-title">' + item.f_field_name.value + '</span>' + link);
		}
		else {
			item.edit_form.find('h4.modal-title').html(caption + link);
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
			where,
			parent;
		lookup_item.table_options.sortable = true;
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
			where = {}
			if (item.owner === item.task.sys_items) {
				if (item.owner.type_id.value === item.task.item_types.TASK_TYPE) {
					where.task_id = item.owner.id.value;
				}
				else {
					where.task_id = item.owner.task_id.value;
				}
			}
			where.type_id__in = [item.task.item_types.ITEM_TYPE, item.task.item_types.TABLE_TYPE];
			where.table_id = 0;
			lookup_item.set_where(where)
			lookup_item.set_order_by(['f_item_name']);
		}
		else if (field.field_name === 'f_master_field' && item.f_object.value) {
			id_value = item.owner.id.value;
			parent = item.task.sys_items.field_by_id(id_value, 'parent');
			if (parent) {
				lookup_item.set_where({
					owner_rec_id: parent,
					id__ne: item.id.value,
					f_object: item.f_object.value,
					f_master_field__isnull: true
				})
			}
			else {
				lookup_item.set_where({owner_rec_id: -1});
			}
			lookup_item.set_fields(['id', 'f_name', 'f_field_name', 'f_db_field_name'])
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
						it.f_db_field_name.value = c.f_db_field_name.value;
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
				lookup_item.set_where({
					owner_rec_id__in: [id_value, parent],
					f_master_field__isnull: true
				});
				lookup_item.set_order_by(['f_field_name']);
			}
			else {
				lookup_item.set_where({owner_rec_id: -1});
			}
		}
		if (field.field_name === 'f_object_field1') {
			fields = item.task.sys_fields.copy();
			fields.set_where({id: item.f_object_field.value})
			fields.open();
			if (fields.f_object.value) {
				id_value = fields.f_object.value;
				parent = fields.task.sys_items.field_by_id(id_value, 'parent');
				lookup_item.set_where({
					owner_rec_id__in: [id_value, parent],
					f_master_field__isnull: true
				});
				lookup_item.set_order_by(['f_field_name']);
			}
			else {
				lookup_item.set_where({owner_rec_id: -1});
			}
		}
		if (field.field_name === 'f_object_field2') {
			fields = item.task.sys_fields.copy();
			fields.set_where({id: item.f_object_field1.value})
			fields.open();
			if (fields.f_object.value) {
				id_value = fields.f_object.value;
				parent = fields.task.sys_items.field_by_id(id_value, 'parent');
				lookup_item.set_where({
					owner_rec_id__in: [id_value, parent],
					f_master_field__isnull: true
				});
				lookup_item.set_order_by(['f_field_name']);
			}
			else {
				lookup_item.set_where({owner_rec_id: -1});
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
		else if (field.field_name === 'f_object') {
			if (item.f_data_type.value === item.task.consts.KEYS && !field.value) {
				return 'For keys field a lookup item must be set';
			}
		}
		else if (field.field_name === 'f_object_field') {
			if (item.f_object.value && !field.value) {
				return item.task.language.object_field_required;
			}
		}
		else if (field.field_name === 'f_data_type') {
			if (item.f_data_type.value === 0) {
				return item.task.language.type_is_required;
			}
		}
		else if (field.field_name === 'f_size' && item.f_data_type.value === item.task.consts.TEXT && !field.value) {
			return item.task.language.size_is_required;
		}
		else if (field.field_name === 'f_default_value' && field.value) {
			if (item.f_data_type.value === item.task.consts.INTEGER) {
				if (!(Math.floor(field.value) == field.value && $.isNumeric(field.value))) {
					return task.language.invalid_value.replace('%s', '');
				}
			}
			else if (item.f_data_type.value === item.task.consts.FLOAT || item.f_data_type.value === item.task.consts.CURRENCY) {
				if (!($.isNumeric(field.value))) {
					return task.language.invalid_value.replace('%s', '');
				}
			}
		}
		else if (field.field_name === 'f_file_accept') {
			if (item.f_data_type.value === task.consts.FILE) {
				if (!field.value) {
					return field.field_caption + ' - ' + task.language.value_required;   
				}
				else {
					if (!task.server('server_valid_field_accept_value', [field.value])) {
						return field.field_caption + ' - ' + task.language.invalid_value.replace('%s', '');
					}
				}
			}
		}
	}
	
	function on_field_changed(field, lookup_item) {
		var item = field.owner,
			fields,
			res,
			ident;
		if (!item._field_changing) {
			item._field_changing = true;
			try {
				if (field.field_name === 'f_name') {
					if (item.f_field_name) {
						if (!item.f_field_name.value) {
							try {
								ident = field.text.split(' ').join('_').toLowerCase();
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
								ident = field.text.split(' ').join('_').toLowerCase();
								if (item.task.sys_items.valid_identifier(ident)) {
									item.f_param_name.value = ident;
								}
							}
							catch (e) {
							}
						}
					}
				}
				if ((field.field_name === 'f_field_name' || field.field_name === 'f_name') && (!item.task._manual_update || new_field(item))) {
					if (item.f_field_name && item.f_field_name.value && !item.task._manual_update) {
						item.f_db_field_name.value = item.task.server('server_set_literal_case', item.f_field_name.value);
					}
				}
				if (field.field_name === 'f_object') {
					update_default_value(item, true);
					item.f_object_field.value = null;
					item.f_object_field1.value = null;
					item.f_object_field2.value = null;
					item.f_lookup_values.value = null;
					item.f_master_field.value = null;
					if (item.f_object.value) {
						res = item.task.server('server_get_primary_key_type', field.value);
						if (item.f_data_type.value === item.task.consts.KEYS) {
							item.f_object_field.set_value(res.field_id, res.field_name);
						}
						else {
							item.f_data_type.value = res.data_type;
							item.f_size.value = res.size;
						}
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
					update_default_value(item, true);
				}
				else if (field === item.f_data_type) {
					update_iterface_tab(item);
					update_default_value(item, true);
					if (item.f_data_type.value === item.task.consts.TEXT) {
						item.f_size.value = 100;
					}
					else if (item.f_data_type.value === item.task.consts.BOOLEAN) {
						item.f_default_lookup_value.value = 0;
					}
					else {
						item.f_size.value = null;
					}
				}
				else if (field.field_name === 'f_default_lookup_value') {
					item.f_default_value.value = field.lookup_value.toLowerCase();
					if (item.f_lookup_values.value) {
						item.f_default_value.text = field.data;
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
	
	function update_default_value(item, clear) {
		if (item.edit_form && item.f_default_value) {
			if (clear) {
				item.f_default_value.value = null;
				item.f_default_lookup_value.value = null;
			}
	
			item.edit_form.find('input.f_default_value').width('55%');
			if (item.f_data_type.value === item.task.consts.DATE ||
				item.f_data_type.value === item.task.consts.DATETIME ||
				item.f_data_type.value === item.task.consts.BOOLEAN || item.f_lookup_values.value) {
				item.edit_form.find('input.f_default_value').closest('.control-group.input-container').hide();
				item.edit_form.find('input.f_default_lookup_value').closest('.control-group.input-container').show();
			}
			else {
				item.edit_form.find('input.f_default_value').closest('.control-group.input-container').show();
				item.edit_form.find('input.f_default_lookup_value').closest('.control-group.input-container').hide();
			}
	
			if (item.f_data_type.value === item.task.consts.DATE) {
				item.f_default_lookup_value.lookup_values = [[0, ''], [1, 'CURRENT DATE']];
			}
			else if (item.f_data_type.value === item.task.consts.DATETIME) {
				item.f_default_lookup_value.lookup_values = [[0, ''], [1, 'CURRENT DATETIME']];
			}
			else if (item.f_data_type.value === item.task.consts.BOOLEAN) {
				item.f_default_lookup_value.lookup_values = [[null, ''], [0, 'FALSE'], [1, 'TRUE']]
			}
			else if (item.f_lookup_values.value) {
				item.f_default_lookup_value.lookup_values = task.server('get_lookup_list', [item.f_lookup_values.value]);
			}
			item.f_default_lookup_value.update_controls();
		}
	}
	
	function update_fields_read_only(item) {
		var default_read_only = (item.f_data_type.value === item.task.consts.KEYS) ||
			(item.f_data_type.value === item.task.consts.FILE) ||
			(item.f_data_type.value === item.task.consts.IMAGE) ||
			Boolean(item.f_object.value) ||
			!(item.f_data_type.value) ||
			Boolean(item.f_master_field.value);
		if (item.f_default_value) {
			item.f_default_value.read_only = default_read_only
			item.f_default_lookup_value.read_only = default_read_only
		}
		if (!new_field(item) && !item.owner.f_virtual_table.value && !item.task._manual_update) {
			item.f_data_type.read_only = !item.task.db_options.CAN_CHANGE_TYPE;
			item.f_size.read_only = true;
			if (item.f_data_type.value === item.task.consts.TEXT) {
				item.f_size.read_only = !item.task.db_options.CAN_CHANGE_SIZE;
				if (item.f_object.value || item.owner.f_primary_key.value === item.id.value) {
					item.f_size.read_only = true;
				}
			}
			item.f_lookup_values.read_only = true;
			item.f_object.read_only = true;
			item.f_multi_select.read_only = false;
			item.f_object_field.read_only = !item.f_object.value;
			item.f_master_field.read_only = !item.f_object.value;
			item.f_object_field1.read_only = !item.f_object_field.value;
			item.f_object_field2.read_only = !item.f_object_field1.value;
			item.f_enable_typehead.read_only = !(item.f_object.value && !item.f_master_field.value);
		}
		else {
			if (item.f_data_type.value) {
				if (item.f_object.value || item.f_lookup_values.value) {
					item.f_data_type.read_only = true;
				}
				else {
					item.f_data_type.read_only = false;
				}
			}
			else {
				item.f_data_type.read_only = false;
			}
			if (item.f_data_type.value === item.task.consts.TEXT && !item.f_object.value) {
				item.f_size.read_only = false;
			}
			else {
				item.f_size.read_only = true;
			}
			update_lookup_attr(item);
		}
	}
	
	function update_lookup_attr(item, is_new) {
		item.f_object.read_only = false;
		item.f_lookup_values.read_only = item.f_object.value
		item.f_object.read_only = item.f_lookup_values.value
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
		if (item.f_data_type.value === item.task.consts.KEYS && item.f_object.value) {
			item.f_object_field.read_only = true;
			item.f_object_field1.read_only = true;
			item.f_object_field2.read_only = true;
			item.f_master_field.read_only = true;
			item.f_multi_select.read_only = true;
			item.f_lookup_values.read_only = true;
			item.f_enable_typehead.read_only = false;
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
					error = item.format_string(task.language.cant_delete_master_field,
						{field1: item.f_field_name.value, field2: c.f_field_name.value});
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
	
	function on_field_get_text(field) {
		if (field.field_name === 'f_size' && field.value === 0) {
			return '';
		}
	}
	
	function on_edit_form_keydown(item, event) {
		if (event.keyCode === 13 && event.ctrlKey === true){
			event.preventDefault();
			item.edit_form.find("#ok-btn").focus();
			item.apply_record();
		}
	}
	this.on_edit_form_created = on_edit_form_created;
	this.update_iterface_tab = update_iterface_tab;
	this.on_edit_form_shown = on_edit_form_shown;
	this.on_after_open = on_after_open;
	this.new_field = new_field;
	this.on_field_select_value = on_field_select_value;
	this.check_valid_field_name = check_valid_field_name;
	this.on_field_validate = on_field_validate;
	this.on_field_changed = on_field_changed;
	this.update_default_value = update_default_value;
	this.update_fields_read_only = update_fields_read_only;
	this.update_lookup_attr = update_lookup_attr;
	this.get_alignment = get_alignment;
	this.can_delete = can_delete;
	this.on_after_append = on_after_append;
	this.on_before_delete = on_before_delete;
	this.on_before_post = on_before_post;
	this.on_before_edit = on_before_edit;
	this.on_field_get_text = on_field_get_text;
	this.on_edit_form_keydown = on_edit_form_keydown;
}

task.events.events26 = new Events26();

function Events27() { // app_builder.catalogs.sys_roles.sys_privileges 

	function on_view_form_created(item) {
		item.view_options.width = 900;
	}
	
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
	this.on_view_form_created = on_view_form_created;
	this.on_field_changed = on_field_changed;
}

task.events.events27 = new Events27();

})(jQuery, task)
