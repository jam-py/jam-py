(function($) {

    "use strict";

    const consts = {
            "PROJECT_NONE": 1,
            "PROJECT_NO_PROJECT": 2,
            "PROJECT_LOADING": 3,
            "PROJECT_ERROR": 4,
            "PROJECT_NOT_LOGGED": 5,
            "PROJECT_LOGGED": 6,
            "PROJECT_MAINTAINANCE": 7,
            "PROJECT_MODIFIED": 8,
            "RESPONSE": 9,

            "TEXT": 1,
            "INTEGER": 2,
            "FLOAT": 3,
            "CURRENCY": 4,
            "DATE": 5,
            "DATETIME": 6,
            "BOOLEAN": 7,
            "LONGTEXT": 8,
            "KEYS": 9,
            "FILE": 10,
            "IMAGE": 11,

            "ITEM_FIELD": 1,
            "FILTER_FIELD": 2,
            "PARAM_FIELD": 3,

            "FILTER_EQ": 1,
            "FILTER_NE": 2,
            "FILTER_LT": 3,
            "FILTER_LE": 4,
            "FILTER_GT": 5,
            "FILTER_GE": 6,
            "FILTER_IN": 7,
            "FILTER_NOT_IN": 8,
            "FILTER_RANGE": 9,
            "FILTER_ISNULL": 10,
            "FILTER_EXACT": 11,
            "FILTER_CONTAINS": 12,
            "FILTER_STARTWITH": 13,
            "FILTER_ENDWITH": 14,
            "FILTER_CONTAINS_ALL": 15,
            "FILTER_EQ_L": 16,
            "FILTER_NE_L": 17,
            "FILTER_LT_L": 18,
            "FILTER_LE_L": 19,
            "FILTER_GT_L": 20,
            "FILTER_GE_L": 21,
            "FILTER_IN_L": 22,
            "FILTER_NOT_IN_L": 23,
            "FILTER_RANGE_L": 24,
            "FILTER_ISNULL_L": 25,
            "FILTER_EXACT_L": 26,
            "FILTER_CONTAINS_L": 27,
            "FILTER_STARTWITH_L": 28,
            "FILTER_ENDWITH_L": 29,
            "FILTER_CONTAINS_ALL_L": 30,

            "ALIGN_LEFT": 1,
            "ALIGN_CENTER": 2,
            "ALIGN_RIGHT": 3,

            "STATE_INACTIVE": 0,
            "STATE_BROWSE": 1,
            "STATE_INSERT": 2,
            "STATE_EDIT": 3,
            "STATE_DELETE": 4,

            "RECORD_UNCHANGED": null,
            "RECORD_INSERTED": 1,
            "RECORD_MODIFIED": 2,
            "RECORD_DELETED": 3,
            "RECORD_DETAILS_MODIFIED": 4,

            "REC_STATUS": 0,
            "REC_LOG_REC": 1,

            "UPDATE_OPEN": 0,
            "UPDATE_RECORD": 1,
            "UPDATE_APPEND": 2,
            "UPDATE_INSERT": 3,
            "UPDATE_SCROLLED": 4,
            "UPDATE_CONTROLS": 5,
            "UPDATE_CLOSE": 6,
            "UPDATE_STATE": 7,
            "UPDATE_APPLIED": 8,
            "UPDATE_SUMMARY": 9
        },
        align_value = ['', 'left', 'center', 'right'],
        filter_value = [
            'eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in', 'not_in',
            'range', 'isnull', 'exact', 'contains', 'startwith', 'endwith',
            'contains_all',
            'eq_l', 'ne_l', 'lt_l', 'le_l', 'gt_l', 'ge_l', 'in_l', 'not_in_l',
            'range_l', 'isnull_l', 'exact_l', 'contains_l', 'startwith_l', 'endwith_l',
            'contains_all_l'
       ],
        field_attr = [
            "ID",
            "field_name",
            "field_caption",
            "data_type",
            "field_size",
            "required",
            "lookup_item",
            "lookup_field",
            "lookup_field1",
            "lookup_field2",
            "edit_visible",
            "_read_only",
            "default",
            "default_value",
            "master_field",
            "_alignment",
            "lookup_values",
            "multi_select",
            "multi_select_all",
            "enable_typeahead",
            "field_help",
            "field_placeholder",
            "field_interface",
            "field_image",
            "field_file",
            "reserved",
            "calculated"
        ],
        filter_attr = [
            "filter_name",
            "filter_caption",
            "field_name",
            "filter_type",
            "multi_select_all",
            "data_type",
            "visible",
            "filter_help",
            "filter_placeholder",
            "ID"
        ],
        field_type_names = ["", "text", "integer", "float", 'currency',
            "date", "datetime", "boolean", "longtext", "keys", "file", "image"
        ];

    var settings,
        locale,
        language;


    class AbortError extends Error {
        constructor(message) {
            super(message);
            this.name = "AbortError";
        }
    }

    class AbsrtactItem {
        constructor(owner, ID, item_name, caption, visible, type, js_filename) {
            this.types = ["root", "users", "roles", "tasks", 'task',
                "items", "items", "details", "reports",
                "item", "item", "detail_item", "report", "detail"
            ];
            if (visible === undefined) {
                visible = true;
            }
            if (owner === undefined) {
                owner = null;
            }
            this.owner = owner;
            this.item_name = item_name || '';
            this.item_caption = caption || '';
            this.visible = visible;
            this.ID = ID || null;
            this.item_type_id = type;
            this.item_type = '';
            if (type) {
                this.item_type = this.types[type - 1];
            }
            if (js_filename) {
                this.js_filename = 'js/' + js_filename;
            }
            this.items = [];
            if (owner) {
                if (!owner.find(item_name)) {
                    owner.items.push(this);
                }
                if (!(item_name in owner)) {
                    owner[item_name] = this;
                }
                this.task = owner.task;
            }
        }

        get_master_field(fields, master_field) {
            var i = 0,
                len = fields.length;
            for (; i < len; i++) {
                if (fields[i].ID == master_field) {
                    return fields[i];
                }
            }
        }

        each_item(callback) {
            var i = 0,
                len = this.items.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.items[i], this.items[i], i);
                if (value === false) {
                    break;
                }
            }
        }

        all(func) {
            var i = 0,
                len = this.items.length;
            func.call(this, this);
            for (; i < len; i++) {
                this.items[i].all(func);
            }
        }

        find(item_name) {
            var i = 0,
                len = this.items.length;
            for (; i < len; i++) {
                if (this.items[i].item_name === item_name) {
                    return this.items[i];
                }
            }
        }

        item_by_ID(id_value) {
            var result;
            if (this.ID === id_value) {
                return this;
            }
            var i = 0,
                len = this.items.length;
            for (; i < len; i++) {
                result = this.items[i].item_by_ID(id_value);
                if (result) {
                    return result;
                }
            }
        }

        addChild(ID, item_name, caption, visible, type, js_filename, master_field) {
            var NewClass;
            if (this.getChildClass) {
                NewClass = this.getChildClass();
                if (NewClass) {
                    return new NewClass(this, ID, item_name, caption,
                        visible, type, js_filename, master_field);
                }
            }
        }

        send_request(request, params, callback) {
            return this.task.process_request(request, this, params, callback);
        }

        init(info) {
            var i = 0,
                items = info.items,
                child,
                len = items.length,
                item_info;
            for (; i < len; i++) {
                item_info = items[i][1];
                child = this.addChild(item_info.id, item_info.name,
                    item_info.caption, item_info.visible, item_info.type,
                    item_info.js_filename, item_info.master_field);
                child._default_order = item_info.default_order;
                child._primary_key = item_info.primary_key;
                child._deleted_flag = item_info.deleted_flag;
                child._master_id = item_info.master_id;
                child._master_rec_id = item_info.master_rec_id;
                child.keep_history = item_info.keep_history;
                child.edit_lock = item_info.edit_lock;
                child._view_params = item_info.view_params;
                child._edit_params = item_info.edit_params;
                child._virtual_table = item_info.virtual_table;
                child.prototype_ID = item_info.prototype_ID
                child.master_applies = item_info.master_applies
                if (child.initAttr) {
                    child.initAttr(item_info);
                }
                child.init(item_info);
            }
        }

        bind_items() {
            var i = 0,
                len = this.items.length;
            if (this._bind_item) {
                this._bind_item();
            }
            for (; i < len; i++) {
                this.items[i].bind_items();
            }
        }

        _check_args(args) {
            var i,
                result = {};
            for (i = 0; i < args.length; i++) {
                if (args[i] instanceof jQuery) {
                    result['jquery'] = args[i]
                }
                else {
                    result[typeof args[i]] = args[i];
                }
            }
            return result;
        }

        _file_loaded(js_filename) {
            for (let i = 0; i < document.scripts.length; i++) {
                let script = document.scripts[i].src.split('?')[0],
                    file_name = js_filename.split('?')[0],
                    arr1 = js_filename.split('/'),
                    arr2 = script.split('/'),
                    found = true;
                for (let j = 0;  j < arr1.length; j++) {
                    if (arr1[arr1.length - 1 - j] !== arr2[arr2.length - 1 - j]) {
                        found = false;
                        break;
                    }
                }
                if (found) {
                    return true;
                }
            }
        }

        load_script(js_filename, callback, onload) {
            var self = this,
                url,
                s0,
                s;
            if (js_filename && !this._file_loaded(js_filename)) {
                s = document.createElement('script');
                s0 = document.getElementsByTagName('script')[0];
                url = js_filename;

                s.src = url;
                s.type = "text/javascript";
                s.async = true;
                s0.parentNode.insertBefore(s, s0);
                s.onload = function() {
                    if (onload) {
                        onload.call(self, self);
                    }
                    if (callback) {
                        callback.call(self, self);
                    }
                };
            } else {
                if (callback) {
                    callback.call(self, self);
                }
            }
        }

        load_module(callback) {
            this.load_modules([this], callback);
        }

        load_modules(item_list, callback) {
            var self = this,
                i = 0,
                len = item_list.length,
                item,
                list = [],
                mutex = 0,
                calcback_executing = false,
                load_script = function(item) {
                    item.load_script(
                        item.js_filename,
                        function() {
                            if (--mutex === 0) {
                                if (callback && !calcback_executing) {
                                    calcback_executing = true;
                                    callback.call(self, self);
                                }
                            }
                        },
                        function() {
                            item.bind_handlers();
                        }
                    );
                };
            for (; i < len; i++) {
                item = item_list[i];
                if (item.js_filename) list.push(item);
                if (item.details) {
                    item.each_detail(function(d) {
                        if (d.js_filename) list.push(d);
                    });
                }
            }
            len = list.length;
            mutex = len;
            if (len) {
                for (i = 0; i < len; i++) {
                    load_script.call(list[i], list[i]);
                }
            } else {
                if (callback) {
                    callback.call(this, this);
                }
            }
        }

        bind_handlers() {
            let events = task.events['events' + this.ID];
            if (this.master_field) {
                events = task.events['events' + this.prototype_ID];
            }
            this._events = [];
            for (var event in events) {
                if (events.hasOwnProperty(event)) {
                    //~ if (this[event]) {
                        //~ console.error(this.item_name + ' client module ' + ': method "' +
                            //~ event + '" will override existing attribute. Please, rename the function.');
                    //~ }
                    this[event] = events[event];
                    this._events.push([event, events[event]]);
                }
            }
        }

        bind_events() {
            var i = 0,
                len = this.items.length;

            this.bind_handlers();

            for (; i < len; i++) {
                this.items[i].bind_events();
            }
        }

        can_view() {
            return this.task.has_privilege(this, 'can_view');
        }

        _search_template(name, suffix) {
            var template,
                search = "." + name;
            if (suffix) {
                search = "." + name + "-" + suffix
            }
            template = task.templates.find(search);
            if (template.length) {
                return template;
            }
        }

        find_template(suffix, options) {
            var result,
                template,
                name,
                item = this;
            if (options.template_class) {
                template = this._search_template(options.template_class);
            }
            if (!template) {
                if (item.item_type === "detail") {
                    template = this._search_template(item.owner.item_name + "-" + item.item_name, suffix);
                    if (!template) {
                        template = this._search_template(item.owner.owner.item_name + "-details", suffix);
                    }
                    if (!template && options && options.buttons_on_top) {
                        template = this._search_template("default-top", suffix);
                    }
                    if (!template) {
                        template = this._search_template('default', suffix);
                    }
                    if (!template) {
                        item = item.owner;
                    }
                }
                if (!template) {
                    while (true) {
                        name = item.item_name;
                        template = this._search_template(item.item_name, suffix);
                        if (template) {
                            break;
                        }
                        item = item.owner;
                        if (item === item.task) {
                            break;
                        }
                    }
                }
            }
            if (!template && options && options.buttons_on_top) {
                template = this._search_template("default-top", suffix);
            }
            if (!template) {
                template = this._search_template('default', suffix);
            }
            if (template) {
                result = template.clone();
            }
            else {
                this.warning(this.item_caption + ': ' +  suffix + ' form template not found.')
            }
            return result;
        }

        server(func_name, params) {
            var args = this._check_args(arguments),
                callback = args['function'],
                async = args['boolean'],
                res,
                err,
                result;
            if (params !== undefined && (params === callback || params === async)) {
                params = undefined;
            }
            if (params === undefined) {
                params = [];
            } else if (!$.isArray(params)) {
                params = [params];
            }
            if (callback || async) {
                this.send_request('server', [func_name, params], function(result) {
                    res = result[0];
                    err = result[1];
                    if (callback) {
                        callback.call(this, res, err);
                    }
                    if (err) {
                        throw new Error(err);
                    }
                });
            } else {
                result = this.send_request('server', [func_name, params]);
                res = result[0];
                err = result[1];
                if (err) {
                    throw new Error(err);
                } else {
                    return res;
                }
            }
        }

        _focus_form(form) {
            this.task._focus_element(form);
        }

        _create_form_header(form, options, form_type, container) {
            var $doc,
                $form,
                $title,
                mouseX,
                mouseY,
                defaultOptions = {
                    title: this.item_caption,
                    close_button: true,
                    print: false
                },
                form_header,
                item_class = '';

            function captureMouseMove(e) {
                var $title = $form.find('.modal-header');
                if (mouseX) {
                    e.preventDefault();
                    $title.css('cursor', 'auto');
                    $form.css('margin-left', parseInt($form.css('margin-left'), 10) + e.screenX - mouseX);
                    $form.css('margin-top', parseInt($form.css('margin-top'), 10) + e.screenY - mouseY);
                    mouseX = e.screenX;
                    mouseY = e.screenY;
                }
            }

            function release_mouse_move(e) {
                mouseX = undefined;
                mouseY = undefined;
                $doc.off("mousemove.modalform");
                $doc.off("mouseup.modalform");
            }
            if (task.old_forms) {
                form_header = $('<div class="modal-header">');
                form_header.css('display', 'block');
            }
            else {
                if (options.form_header && (!form_header || !form_header.length)) {
                    form_header = $(
                        '<div class="modal-header">' +
                            '<div class="header-title"></div>' +
                            '<div class="header-refresh-btn"></div>' +
                            '<div class="header-history-btn"></div>' +
                            '<div class="header-filters"></div>' +
                            '<div class="header-search"></div>' +
                            '<div class="header-print-btn"></div>' +
                            '<div class="header-close-btn"></div>' +
                        '</div>'
                    );
                }
            }
            if (form_type) {
                if (this.master) {
                    item_class = this.master.item_name + '-' + this.item_name + ' ' + form_type + '-form';
                }
                else {
                    item_class = this.item_name + ' ' + form_type + '-form';
                }
            }
            options = $.extend({}, defaultOptions, options);
            if (!options.title) {
                options.title = '&nbsp';
            }

            if (container && container.length) {
                if (task.old_forms) {
                    form.addClass('jam-form');
                    form.addClass(item_class)
                    if (options.form_header && form_type === 'edit') {
                        form.prepend(form_header);
                    }
                    return form
                }
                else {
                    $form = $(
                        '<div class="form-frame ' + item_class + '" tabindex="-1">' +
                        '</div>'
                    );
                    if (options.form_header) {
                        $form.append(form_header);
                    }
                    if (!options.form_border) {
                        $form.addClass('no-border');
                    }
                }
            }
            else {
                $form = $(
                    '<div class="modal hide normal-modal-border ' + item_class + '" tabindex="-1" data-backdrop="static">' +
                    '</div>'
                );
                if (options.form_header) {
                    $form.append(form_header);
                }
                $doc = $(document);
                $form.on("mousedown", ".modal-header", function(e) {
                    mouseX = e.screenX;
                    mouseY = e.screenY;
                    $doc.on("mousemove.modalform", captureMouseMove);
                    $doc.on("mouseup.modalform", release_mouse_move);
                });

                $form.on("mousemove", ".modal-header", function(e) {
                    $(this).css('cursor', 'move');
                });
            }
            this._set_form_options($form, options);
            $form.append(form);
            $form.addClass('jam-form');
            return $form;
        }

        _set_old_form_options(form, options, form_type) {
            var self = this,
                form_name = form_type + '_form',
                body,
                header = form.find('.modal-header'),
                title = header.find('.modal-title'),
                closeCaption = '',
                close_button = '',
                printCaption = '',
                print_button = '',
                history_button = '';
            if (options.close_button) {
                if (language && options.close_on_escape) {
                    closeCaption = '&nbsp;' + language.close + ' - [Esc]</small>';
                }
                close_button = '<button type="button" id="close-btn" class="close" tabindex="-1" aria-hidden="true" style="padding: 0px 10px;">' +
                    closeCaption + ' ×</button>';
            }
            if (language && options.print) {
                printCaption = '&nbsp;' + language.print + ' - [Ctrl-P]</small>',
                    print_button = '<button type="button" id="print-btn" class="close" tabindex="-1" aria-hidden="true" style="padding: 0px 10px;">' +
                    printCaption + '</button>';
            }
            if (options.history_button && this.keep_history && task.history_item) {
                history_button = '<i id="history-btn" class="icon-film" style="float: right; margin: 5px;"></i>';
            }

            if (!title.text().length) {
                title = ('<h4 class="modal-title">' + options.title + '</h4>');
            } else {
                title.html(options.title);
            }
            header.empty();
            header.append(close_button + history_button + print_button);
            header.append(title);
            header.find("#close-btn").css('cursor', 'default').click(function(e) {
                if (form_name) {
                    self._close_form(form_type);
                }
            });
            header.find('#print-btn').css('cursor', 'default').click(function(e) {
                if (form.find(".form-body").length) {
                    body = form.find(".form-body");
                }
                else if (form.find(".modal-body").length) {
                    body = form.find(".modal-body");
                }
                self.print_html(body);
            });
            header.find('#history-btn').css('cursor', 'default').click(function(e) {
                self.show_history();
            });
        }

        _set_form_options(form, options, form_type) {
            var self = this,
                form_name = form_type + '_form',
                header = form.find('.modal-header'),
                close_caption = '',
                close_button = '',
                print_caption = '',
                print_button = '',
                filter_count = 0,
                body;
            if (task.old_forms) {
                this._set_old_form_options(form, options, form_type);
                return;
            }
            if (!options.title) {
                options.title = this.item_caption;
            }

            if (options.close_button) {
                if (language && options.close_on_escape) {
                    close_caption = '&nbsp;' + language.close + ' - [Esc]</small>';
                }
                close_button = '<button type="button" id="close-btn" class="close" tabindex="-1" aria-hidden="true" style="padding: 0px 10px;">' +
                    close_caption + ' ×</button>';
                header.find('.header-close-btn').html(close_button);
            }
            else {
                header.find('.header-close-btn').hide();
            }

            if (language && options.print) {
                print_caption = '&nbsp;' + language.print + ' - [Ctrl-P]</small>',
                    print_button = '<button type="button" id="print-btn" class="close" tabindex="-1" aria-hidden="true" style="padding: 0px 10px;">' +
                    print_caption + '</button>';
                header.find('.header-print-btn').html(print_button);
            }
            else {
                header.find('.header-print-btn').hide();
            }

            if (options.history_button && this.keep_history && task.history_item) {
                header.find('.header-history-btn')
                    .html('<a class="btn header-btn history-btn" href="#"><i class="icon-film"></i></a>')
                    .tooltip({placement: 'bottom', title: language.view_rec_history, trigger: 'hover'});
                header.find('.history-btn').css('cursor', 'default').click(function(e) {
                    e.preventDefault();
                    self.show_history();
                });
            }
            else {
                header.find('.header-history-btn').hide();
            }

            if (!this.virtual_table && options.refresh_button) {
                header.find('.header-refresh-btn')
                    .html('<a class="btn header-btn refresh-btn" href="#"><i class="icon-refresh"></i></a>')
                    .tooltip({placement: 'bottom', title: language.refresh_page, trigger: 'hover'});
                header.find(".refresh-btn").css('cursor', 'default').click(function(e) {
                    e.preventDefault();
                    self.refresh_page(true);
                });
            }
            else {
                header.find('.header-refresh-btn').hide();
            }

            if (this.each_filter) {
                this.each_filter(function(f) {
                    if (f.visible) {
                        filter_count += 1;
                    }
                })
            }
            if (options.enable_filters && filter_count) {
                header.find('.header-filters')
                    .html(
                        '<a class="btn header-btn header-filters-btn" href="#">' +
                        //~ '<i class="icon-filter"></i> ' +
                        language.filters + '</a>' +
                        '<span class="filters-text pull-left"></span>'
                    )
                header.find('.header-filters-btn')
                    .tooltip({placement: 'bottom', title: language.set_filters, trigger: 'hover'})
                    .css('cursor', 'default')
                    .click(function(e) {
                        e.preventDefault();
                        self.create_filter_form();
                    });
            }

            if (!options.enable_search) {
                header.find('.header-search').hide();
            }

            header.find('.header-title').html('<h4 class="modal-title">' + options.title + '</h4>')

            header.find("#close-btn").css('cursor', 'default').click(function(e) {
                if (form_name) {
                    self._close_form(form_type);
                }
            });
            header.find('#print-btn').css('cursor', 'default').click(function(e) {
                if (form.find(".form-body").length) {
                    body = form.find(".form-body");
                }
                else if (form.find(".modal-body").length) {
                    body = form.find(".modal-body");
                }
                self.print_html(body);
            });

            if (options.form_header) {
                header.css('display', 'flex');
            }
            else {
                header.remove();
            }
        }

        init_filters() {
            var self = this;
            this._on_filters_applied_internal = function() {
                if (self.view_form) {
                    self.view_form.find(".filters-text").html(self.get_filter_html());
                }
            };
        }

        init_search() {

            function can_search_on_field(field) {
                if (field && field.lookup_type !== "boolean" &&
                    field.lookup_type !== "image" &&
                    field.lookup_type !== "date" &&
                    field.lookup_type !== "datetime") {
                    return true;
                }
            }

            function isCharCode(code) {
                if (code >= 48 && code <= 57 || code >= 96 && code <= 105 ||
                    code >= 65 && code <= 90 || code >= 186 && code <= 192 ||
                    code >= 219 && code <= 222) {
                    return true;
                }
            }

            function do_search(item, input) {
                var field = item.field_by_name(search_field),
                    search_type = 'contains_all';
                item.set_order_by(item.view_options.default_order);
                item._search_params = item.search(search_field, input.val(), search_type, true, function() {
                    input.css('font-weight', 'bold');
                });
            }

            var timeOut,
                self = this,
                i,
                counter = 0,
                search_form,
                search,
                fields_menu,
                li,
                captions = [],
                field,
                field_btn,
                search_field,
                fields = [];

            if (this.view_options.search_field) {
                search_field = this.view_options.search_field;
            }
            for (i = 0; i < this.view_options.fields.length; i++) {
                field = this.field_by_name(this.view_options.fields[i]);
                if (field && can_search_on_field(field)) {
                    fields.push([field.field_name, field.field_caption])
                    if (!search_field) {
                        search_field = this.view_options.fields[i];
                    }
                    counter += 1;
                    if (counter > 20) {
                        break;
                    }
                }
            }
            if (search_field) {
                let input_class = 'input-medium';
                this.view_form.find('#search-form').remove() // for compatibility with previous verdions
                this.view_form.find('.header-search').append(
                    '<form id="search-form" class="form-inline pull-right">' +
                        '<div class="btn-group">' +
                            '<button class="field-btn btn btn-small">' + this.field_by_name(search_field).field_caption + '</button>' +
                            '<button class="btn btn-small dropdown-toggle" data-toggle="dropdown">' +
                                '<span class="caret"></span>' +
                            '</button>' +
                            '<ul class="dropdown-menu">' +
                            '</ul>' +
                        '</div>' +
                        ' <input id="search-input" type="text" class="' + input_class + ' search-query" autocomplete="off">' +
                    '</form>');
                search = this.view_form.find("#search-input");
                field_btn = this.view_form.find('#search-form .field-btn');
                field_btn.click(function(e) {
                    e.preventDefault();
                    search.focus();
                });
                fields_menu = this.view_form.find('#search-form .dropdown-menu')
                for (i = 0; i < fields.length; i++) {
                    li = $('<li><a href="#">' + fields[i][1] + '</a></li>')
                    li.data('field', fields[i]);
                    li.click(function(e) {
                        var field = $(this).data('field');
                        e.preventDefault();
                        search_field = field[0];
                        field_btn.text(field[1]);
                        search.focus();
                        search.val('');
                        do_search(self, search);
                    });
                    fields_menu.append(li)
                }
                search.on('input', function() {
                    var input = $(this);
                    input.css('font-weight', 'normal');
                    clearTimeout(timeOut);
                    timeOut = setTimeout(
                        function() {
                            do_search(self, input);
                        },
                        500
                    );
                });
                search.keyup(function(e) {
                    var code = e.which;
                    if (code === 13) {
                        e.preventDefault();
                    }
                    //~ else if (code === 40 || code === 27) {
                    else if (code === 27) {
                        self.view_form.find('.dbtable.' + self.item_name + ' .inner-table').focus();
                        e.preventDefault();
                        e.stopPropagation();
                    }
                });
                this.view_form.on('keydown', function(e) {
                    var code = e.keyCode || e.which;
                    if (code === 70 && e.ctrlKey) {
                        e.preventDefault();
                        search.focus();
                    }
                    return
                });
            }
            else {
                this.view_form.find("#search-form").hide();
            }
        }

        _process_key_event(form_type, event_type, e) {
            var i,
                form = this[form_type + '_form'],
                item_options = this[form_type + '_options'],
                forms;
            if (this._active_form(form_type)) {
                if (form._form_disabled) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                }
                else {
                    if (e.which !== 116) { //F5
                        e.stopPropagation();
                    }
                    this._process_event(form_type, event_type, e);
                    forms = form.find('.jam-form');
                    forms.each(function() {
                        var form = $(this),
                            options = form.data('options');
                        if (form.is(":visible")) {
                            options.item._process_event(options.form_type, event_type, e);
                        }
                    });
                }
            }
        }

        _process_event(form_type, event_type, e) {
            var event = 'on_' + form_type + '_form_' + event_type,
                can_close,
                index;
            if (event_type === 'close_query') {
                if (this[event]) {
                    can_close = this[event].call(this, this);
                }
                if (!(this.master || this.master_field) && can_close === undefined && this.owner[event]) {
                    can_close = this.owner[event].call(this, this);
                }
                if (can_close === undefined && this.task[event]) {
                    can_close = this.task[event].call(this, this);
                }
                return can_close;
            }
            else if (event_type === 'keyup' || event_type === 'keydown') {
                if (this[event]) {
                    if (this[event].call(this, this, e)) return;
                }
                if (!(this.master || this.master_field) && this.owner[event]) {
                    if (this.owner[event].call(this, this, e)) return;
                }
                if (this.task[event]) {
                    if (this.task[event].call(this, this, e)) return;
                }
            }
            else {
                if (this.task[event]) {
                    if (this.task[event].call(this, this)) return;
                }
                if (!(this.master || this.master_field) && this.owner[event]) {
                    if (this.owner[event].call(this, this)) return;
                }
                if (this[event]) {
                    if (this[event].call(this, this)) return;
                }
            }
            if (form_type === 'edit') {
                if (event_type === 'shown') {
                    task._edited_items.push(this);
                }
                else if (event_type === 'closed') {
                    index = task._edited_items.indexOf(this)
                    if (index > -1) {
                      task._edited_items.splice(index, 1);
                    }
                }
            }
        }

        _resize_form(form_type, container) {
            var form_name = form_type + '_form',
                form = this[form_name],
                item_options = this[form_type + '_options'],
                parent_width,
                width = item_options.width,
                container_width;
            parent_width = container.parent().parent().innerWidth();
            container.width(parent_width);
            container_width = container.innerWidth() -
                parseInt(form.css('border-left-width'), 10) -
                parseInt(form.css('border-right-width'), 10);
            if (!width) {
                width = form.width()
            }
            if (width < container_width) {
                form.width(width);
            }
            else {
                form.width(container_width);
            }
            this.resize_controls();
        }

        _active_form(form_type) {
            var self = this,
                form_name = form_type + '_form',
                form = this[form_name],
                cur_form = $(document.activeElement).closest('.jam-form.' + form_type + '-form'),
                result = false;
            if (cur_form.length) {
                if (form.get(0) === cur_form.get(0)) {
                    result = true;
                }
            }
            else {
                $('.jam-form').each(function() {
                    var form = $(this),
                        options;
                    if (form.is(':visible') && form.hasClass(form_type + '-form') &&
                        form.hasClass(self.item_name)) {
                        options = form.data('options');
                        if (self._tab_info) {
                            if (self._tab_info.tab_id === options.item_options.tab_id) {
                                result = true;
                                return false;
                            }
                        }
                        else {
                            result = true;
                            return false;
                        }

                    }
                })
            }
            return result;
        }

        _create_form(form_type, container) {
            var self = this,
                form,
                form_name = form_type + '_form',
                options = {},
                item_options = this[form_type + '_options'],
                key_suffix,
                resize_timeout,
                width;

            options.item = this;
            options.form_type = form_type;
            options.item_options = item_options;
            options.item_options.form_type = form_type;
            key_suffix = form_name + '.' + this.item_name;
            if (item_options.tab_id) {
                key_suffix += '.' + item_options.tab_id;
            }
            if (container) {
                container.empty();
                this.task.default_content_visible = false;
            }
            form = $("<div></div>").append(this.find_template(form_type, item_options));
            form = this._create_form_header(form, item_options, form_type, container);
            this[form_name] = form
            if (form) {
                options.form = form;
                form.data('options', options);
                form.tabindex = 1;
                if (container) {
                    $(window).on("keyup." + key_suffix, function(e) {
                        if (e.which === 27 && item_options.close_on_escape) {
                            if (self._active_form(form_type)) {
                                self._close_form(form_type);
                                e.stopPropagation();
                                e.stopImmediatePropagation();
                            }
                        }
                        else {
                            self._process_key_event(form_type, 'keyup', e);
                        }
                    });
                    $(window).on("keydown." + key_suffix, function(e) {
                        self._process_key_event(form_type, 'keydown', e)
                    });
                    container.append(form);
                    this[form_name].bind('destroyed', function() {
                        self._close_modeless_form(form_name);
                    });
                    this._process_event(form_type, 'created');
                    this._set_form_options(form, item_options, form_type);
                    this._focus_form(form);
                    if (form_type === 'edit') {
                        this._resize_form(form_type, container);
                        $(window).on("resize." + key_suffix, function(e) {
                            clearTimeout(resize_timeout);
                            resize_timeout = setTimeout(
                                function() {
                                    self._resize_form(form_type, container);
                                },
                                100
                            );
                        })
                    }
                    this._process_event(form_type, 'shown');
                } else {
                    if (form.hasClass("modal")) {
                        form.on("show", function(e) {
                            if (e.target === self[form_name].get(0)) {
                                e.stopPropagation();
                                self._process_event(form_type, 'created');
                                self._set_form_options(self[form_name], item_options, form_type);
                            }
                        });
                        form.on("shown", function(e) {
                            if (e.target === self[form_name].get(0)) {
                                self._focus_form(self[form_name]);
                                if (form_type === 'edit') {
                                    self.resize_controls();
                                }
                                e.stopPropagation();
                                self._process_event(form_type, 'shown');
                            }
                        });
                        form.on("hide", function(e) {
                            if (e.target === self[form_name].get(0)) {
                                var canClose = true;
                                e.stopPropagation();
                                canClose = self._process_event(form_type, 'close_query');
                                if (canClose === false) {
                                    e.preventDefault();
                                    self[form_name].data('_closing', false);
                                }
                            }
                        });
                        form.on("hidden", function(e) {
                            if (e.target === self[form_name].get(0)) {
                                e.stopPropagation();
                                self._process_event(form_type, 'closed');
                                self[form_name].remove();
                                self[form_name] = undefined;
                            }
                        });
                        form.on("keydown." + key_suffix, function(e) {
                            self._process_key_event(form_type, 'keydown', e)
                        });
                        form.on("keyup." + key_suffix, function(e) {
                            self._process_key_event(form_type, 'keyup', e)
                        });

                        form.modal({
                            item: this,
                            form_name: form_name,
                            item_options: item_options
                        });
                    }
                }
            }
        }

        _close_modeless_form(form_type) {
            var self = this,
                form_name = form_type + '_form';
            if (this[form_name]) {
                this._close_form(form_type);
            }
            if (this[form_name]) {
                this[form_name].bind('destroyed', function() {
                    self._close_modeless_form(form_type);
                });
                throw new Error(this.item_name + " - can't close form");
            }
        }

        _close_form(form_type) {
            var self = this,
                form_name = form_type + '_form',
                form = this[form_name],
                options,
                canClose,
                key_suffix;

            if (form) {
                options = form.data('options'),
                key_suffix = form_name + '.' + this.item_name;
                if (options.item_options.tab_id) {
                    key_suffix += '.' + options.item_options.tab_id;
                }
                form.data('_closing', true);
                form.find('.jam-form').data('_closing', true);
                if (form.hasClass('modal')) {
                    setTimeout(
                        function() {
                            form.modal('hide');
                        },
                        100
                    );
                } else {
                    canClose = self._process_event(options.form_type, 'close_query');
                    if (canClose !== false) {
                        $(window).off("keydown." + key_suffix);
                        $(window).off("keyup." + key_suffix);
                        $(window).off("resize." + key_suffix);
                        this[form_name] = undefined;
                        if (this._tab_info) {
                            this.task.close_tab(this._tab_info.container, this._tab_info.tab_id);
                            this._tab_info = undefined;
                        }
                        self._process_event(options.form_type, 'closed');
                        form.remove();
                        let forms = $(".jam-form:not('.modal')");
                        if (forms.length === 0) {
                            this.task.default_content_visible = true;
                        }
                    }
                }
            }
        }

        update_form(form) {
            form.modal('layout');
        }

        disable_edit_form() {
            this._disable_form(this.edit_form);
        }

        enable_edit_form() {
            this._enable_form(this.edit_form);
        }

        edit_form_disabled() {
            return this.edit_form._form_disabled;
        }

        _disable_form(form) {
            if (form) {
                form.css('pointer-events', 'none');
                form._form_disabled = true;
            }
        }

        _enable_form(form) {
            if (form) {
                form.css('pointer-events', 'auto');
                form._form_disabled = false;
            }
        }

        print_html(html) {
            var win = window.frames["dummy"],
                css = $("link[rel='stylesheet']"),
                body,
                head = '<head>';
            css.each(function(i, e) {
                head += '<link href="' + e.href + '" rel="stylesheet">';
            });
            head += '</head>';
            body = html.clone();
            win.document.write(head + '<body onload="window.print()">' + body.html() + '</body>');
            win.document.close();
        }

        alert(message, options) {
            var default_options = {
                    type: 'info',
                    header: undefined,
                    align: 'right',
                    replace: true,
                    pulsate: true,
                    click_close: true,
                    body_click_hide: false,
                    show_header: true,
                    duration: 5,
                    timeout: 0
                },
                pos = 0,
                width = 0,
                container = $('body'),
                $alert;
            options = $.extend({}, default_options, options);
            if (!options.replace && $('body').find('.alert-absolute').length) {
                return;
            }
            if (!options.header) {
                options.header = task.language[options.type];
            }
            if (!options.header) {
                options.show_header = false;
            }
            $alert = $(
            '<div class="alert alert-block alert-absolute">' +
              '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
              '<h4>' + options.header + '</h4>' +
              '<p>' + message + '</p>' +
            '</div>'
            );
            if (task.forms_container && task.forms_container.length) {
                container = task.forms_container;
            }
            else {
                $('body').children().each(function() {
                    var $this = $(this);
                    if ($this.width() > width && $this.css('z-index') === 'auto') {
                        width = $this.width();
                        container = $this;
                    }
                });
            }
            $('body').find('.alert-absolute').remove();
            if (options.body_click_hide) {
                $('body')
                    .off('mouseup.alert-absolute')
                    .on('mouseup.alert-absolute', function(e) {
                    $('body').find('.alert-absolute').remove();
                });
            }
            $(window)
                .off('resize.alert-absolute')
                .on('resize.alert-absolute', function(e) {
                $('body').find('.alert-absolute').remove();
            })

            $alert.addClass('alert-' + options.type)
            if (options.pulsate) {
                $alert.find('h4').addClass('pulsate');
            }
            if (!options.show_header) {
                $alert.find('h4').hide();
            }
            $('body').append($alert);
            $alert.css('top', 0);
            if (options.align === 'right') {
                if (container) {
                    pos = $(window).width() - (container.offset().left + container.width())
                }
                $alert.css('right', pos);
            }
            else {
                if (container) {
                    pos = container.offset().left;
                }
                $alert.css('left', pos);
            }
            $alert.show();
            if (options.duration) {
                setTimeout(function() {
                        $alert.hide(100);
                        setTimeout(function() {
                                $alert.remove();
                            },
                            100
                        );
                    },
                    options.duration * 1000
                );
            }
        }

        alert_error(message, options) {
            options = $.extend({}, options);
            options.type = 'error';
            this.alert(message, options);
        }

        alert_success(message, options) {
            options = $.extend({}, options);
            options.type = 'success';
            this.alert(message, options);
        }

        message(mess, options) {
            var self = this,
                default_options = {
                    title: '',
                    width: 400,
                    form_header: true,
                    height: undefined,
                    margin: undefined,
                    buttons: undefined,
                    default_button: undefined,
                    print: false,
                    text_center: false,
                    button_min_width: 100,
                    center_buttons: false,
                    close_button: true,
                    close_on_escape: true,
                    focus_last_btn: false,
                    hide: true
                },
                buttons,
                key,
                el = '',
                $element,
                $modal_body,
                $button = $('<button type="button" class="btn">OK</button>'),
                timeOut;

            if (mess instanceof jQuery) {
                mess = mess.clone()
            }
            options = $.extend({}, default_options, options);
            buttons = options.buttons;

            el = '<div class="modal-body"></div>';
            if (!this.is_empty_obj(buttons)) {
                el += '<div class="modal-footer"></div>';
            }

            $element = this._create_form_header($(el), options);

            $modal_body = $element.find('.modal-body');

            if (options.margin) {
                $modal_body.css('margin', options.margin);
            }

            $modal_body.html(mess);

            if (!options.title) {
                $element.find('.modal-header').remove();
            }

            if (options.text_center) {
                $modal_body.html(mess).addClass("text-center");
            }
            if (options.center_buttons) {
                $element.find(".modal-footer").css("text-align", "center");
            }

            $element.find("#close-btn").click(function(e) {
                $element.modal('hide');
            });

            for (key in buttons) {
                if (buttons.hasOwnProperty(key)) {
                    $element.find(".modal-footer").append(
                        $button.clone()
                        .data('key', key)
                        .css("min-width", options.button_min_width)
                        .html(key)
                        .click(function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            var key = $(this).data('key');
                            setTimeout(function() {
                                    try {
                                        if (buttons[key]) {
                                            buttons[key].call(self);
                                        }
                                    }
                                    catch (e) {
                                        console.error(e);
                                    }
                                    if (options.hide) {
                                        $element.modal('hide');
                                    }
                                },
                                100
                            );
                        })
                    );
                }
            }

            $element.on("show hide hidden", function(e) {
                if (e.target === $element.get(0)) {
                    e.stopPropagation();
                }
            });

            $element.on("shown", function(e) {
                if (e.target === $element.get(0)) {
                    self._focus_form($element);
                    if (options.focus_last_btn) {
                        $element.find(".modal-footer button.btn:last").focus();
                    }
                    e.stopPropagation();
                }
            });

            $element.on("keyup keydown", function(e) {
                var event;
                e.stopPropagation();
                if (e.which === 37 || e.which === 39) {
                    event = jQuery.Event(e.type);
                    event.which = e.which + 1;
                    $(e.target).trigger(event);
                }
                else if (e.which === 80 && e.ctrlKey) {
                    e.preventDefault();
                    self.print_html($element.find(".modal-body"));
                }
            });

            $element.modal({
                width: options.width,
                height: options.height,
                keyboard: options.close_on_escape
            });
            return $element;
        }

        question(mess, yesCallback, noCallback, options) {
            var buttons = {},
                default_options = {
                    buttons: buttons,
                    margin: "40px 20px",
                    text_center: true,
                    center_buttons: true,
                    focus_last_btn: true
                };
            options = $.extend({}, default_options, options);
            buttons[language.yes] = yesCallback;
            buttons[language.no] = noCallback;
            return this.message(mess, options);
        }

        warning(mess, callback, options) {
            var buttons = {"OK": callback},
                default_options = {
                    buttons: buttons,
                    margin: "40px 20px",
                    text_center: true,
                    center_buttons: true,
                    focus_last_btn: true,
                }
            options = $.extend({}, default_options, options);
            return this.message(mess, options);
        }

        show_message(mess, options) {
            return this.message(mess, options);
        }

        hide_message($element) {
            $element.modal('hide');
        }

        yes_no_cancel(mess, yesCallback, noCallback, cancelCallback) {
            var buttons = {};
            buttons[language.yes] = yesCallback;
            buttons[language.no] = noCallback;
            buttons[language.cancel] = cancelCallback;
            return this.message(mess, {
                buttons: buttons,
                margin: "40px 20px",
                text_center: true,
                width: 500,
                center_buttons: true,
                focus_last_btn: true
            });
        }

        display_history(hist) {
            var self = this,
                html = '',
                acc_div = $('<div class="accordion history-accordion" id="history_accordion">'),
                item,
                master,
                lookups = {},
                lookup_keys,
                lookup_fields,
                keys,
                fields,
                where,
                lookup_item,
                mess;
            if (self.master) {
                master = self.master.copy({handlers: false});
                item = master.item_by_ID(self.ID);
                master.open({open_empty: true});
                master.append();
            }
            else {
                item = self.copy({handlers: false, details: false});
            }
            item.open({open_empty: true});
            item.append();
            hist.each(function(h) {
                var acc = $(
                    '<div class="accordion-group history-group">' +
                        '<div class="accordion-heading history-heading">' +
                            '<a class="accordion-toggle history-toggle" data-toggle="collapse" data-parent="#history_accordion" href="#history_collapse' + h.rec_no + '">' +
                            '</a>' +
                        '</div>' +
                        '<div id="history_collapse' + h.rec_no + '" class="accordion-body collapse">' +
                            '<div class="accordion-inner history-inner">' +
                            '</div>' +
                        '</div>' +
                     '</div>'
                    ),
                    i,
                    user = '',
                    content = '',
                    old_value,
                    new_value,
                    val_index,
                    field,
                    field_name,
                    changes,
                    operation,
                    field_arr;
                changes = h.changes.value;
                if (changes && changes[0] === '0') {
                    changes = changes.substring(1);
                    changes = JSON.parse(changes);
                }
                if (h.operation.value === consts.RECORD_DELETED) {
                    content = '<p>Record deleted</p>'
                }
                else if (changes) {
                    field_arr = changes;
                    if (field_arr) {
                        for (i = 0; i < field_arr.length; i++) {
                            field = item.field_by_ID(field_arr[i][0]);
                            val_index = 1;
                            if (field_arr[i].length === 3) {
                                val_index = 2;
                            }
                            if (field && !field.system_field()) {
                                field_name = field.field_caption;
                                if (field.lookup_item) {
                                    if (!lookups[field.lookup_item.ID]) {
                                        lookups[field.lookup_item.ID] = [];
                                    }
                                    field.data = field_arr[i][val_index];
                                    new_value = field.value;
                                    if (new_value) {
                                        lookups[field.lookup_item.ID].push([field.lookup_field, new_value]);
                                        new_value = '<span class="' + field.lookup_field + '_' + new_value + '">' + language.value_loading + '</span>'
                                    }
                                }
                                else {
                                    field.data = field_arr[i][val_index];
                                    new_value = field.sanitized_text;
                                    if (field.data === null) {
                                        new_value = ' '
                                    }
                                }
                                if (h.operation.value === consts.RECORD_INSERTED) {
                                    content += '<p>' + self.task.language.field + ' <b>' + field_name + '</b>: ' +
                                        self.task.language.new_value + ': <b>' + new_value + '</b></p>';
                                }
                                else if (h.operation.value === consts.RECORD_MODIFIED) {
                                    content += '<p>' + self.task.language.field + ' <b>' + field_name + '</b>: ' +
                                        self.task.language.new_value + ': <b>' + new_value + '</b></p>';
                                }
                            }
                        }
                    }
                }
                if (h.user.value) {
                    user = self.task.language.by_user + ' ' + h.user.value;
                }
                if (h.operation.value === consts.RECORD_INSERTED) {
                    operation = self.task.language.created;
                }
                else if (h.operation.value === consts.RECORD_MODIFIED ||
                    h.operation.value === consts.RECORD_DETAILS_MODIFIED) {
                    operation = self.task.language.modified;
                }
                else if (h.operation.value === consts.RECORD_DELETED) {
                    operation = self.task.language.deleted;
                }

                acc.find('.accordion-toggle').html(h.date.format_date_to_string(h.date.value, '%d.%m.%Y %H:%M:%S') + ': ' +
                    operation + ' ' + user);
                acc.find('.accordion-inner').html(content);
                if (h.rec_no === 0) {
                    acc.find('.accordion-body').addClass('in');
                }
                acc_div.append(acc)
            })
            if (hist.record_count()) {
                html = acc_div;
            }
            mess = self.task.message(html, {width: 700, height: 600,
                title: hist.item_caption + ': ' + self.item_caption, footer: false, print: true});
            acc_div = mess.find('#history_accordion.accordion');
            for (var ID in lookups) {
                if (lookups.hasOwnProperty(ID)) {
                    lookup_item = self.task.item_by_ID(parseInt(ID, 10));
                    if (lookup_item) {
                        lookup_item = lookup_item.copy({handlers: false});
                        lookup_keys = {};
                        lookup_fields = {};
                        lookup_fields[lookup_item._primary_key] = true;
                        for (var i = 0; i < lookups[ID].length; i++) {
                            lookup_fields[lookups[ID][i][0]] = true;
                            lookup_keys[lookups[ID][i][1]] = true;
                        }
                        keys = [];
                        for (var key in lookup_keys) {
                            if (lookup_keys.hasOwnProperty(key)) {
                                keys.push(parseInt(key, 10));
                            }
                        }
                        fields = [];
                        for (var field in lookup_fields) {
                            if (lookup_fields.hasOwnProperty(field)) {
                                fields.push(field);
                            }
                        }
                        where = {}
                        where[lookup_item._primary_key + '__in'] = keys
                        lookup_item.open({where: where, fields: fields}, function() {
                            var lookup_item = this;
                            lookup_item.each(function(l) {
                                l.each_field(function(f) {
                                    if (!f.system_field()) {
                                        acc_div.find("." + f.field_name + '_' + l._primary_key_field.value).text(f.sanitized_text);
                                    }
                                });
                            });
                        })
                    }
                }
            }
        }

        show_history() {
            var self = this,
                item_id = this.ID,
                hist = this.task.history_item.copy();
            if (!this.rec_count) {
                this.warning(language.no_record);
                return;
            }
            if (this.master) {
                item_id = this.prototype_ID;
            }
            hist.set_where({item_id: item_id, item_rec_id: this.field_by_name(this._primary_key).value})
            hist.set_order_by(['-date']);
            hist.open({limit: 100}, function() {
                self.display_history(hist);
            });
        }

        is_empty_obj(obj) {
            for (var prop in obj) {
                if (obj.hasOwnProperty(prop))
                    return false;
            }
            return true;
        }

        abort(message) {
            message = message ? ' - ' + message : '';
            throw new AbortError(this.item_name + message);
        }

        log_message(message) {
            if (this.task.settings.DEBUGGING) {
                message = message ? ' message: ' + message : '';
                console.log(this.item_name + message);
            }
        }

        round(num, dec) {
            return round(num, dec);
        }

        str_to_int(str) {
            var result = parseInt(str, 10);
            if (isNaN(result)) {
                throw new Error(language.invalid_int.replace('%s', ''));
            }
            return result;
        }

        str_to_date(str) {
            return this.format_string_to_date(str, locale.D_FMT);
        }

        str_to_datetime(str) {
            return this.format_string_to_date(str, locale.D_T_FMT);
        }

        str_to_float(text) {
            var result;
            text = text.replace(locale.DECIMAL_POINT, ".")
            text = text.replace(locale.MON_DECIMAL_POINT, ".")
            result = parseFloat(text);
            if (isNaN(result)) {
                throw new Error(language.invalid_float.replace('%s', ''));
            }
            return result;
        }

        str_to_cur(val) {
            var result = '';
            if (val) {
                result = $.trim(val);
                result = result.replace(' ', '')
                if (locale.MON_THOUSANDS_SEP.length) {
                    //~ result = result.replace(new RegExp(locale.MON_THOUSANDS_SEP, 'g'), '');
                    result = result.replace(new RegExp('\\' + locale.MON_THOUSANDS_SEP, 'g'), '');
                }
                if (locale.CURRENCY_SYMBOL) {
                    result = $.trim(result.replace(locale.CURRENCY_SYMBOL, ''));
                }
                if (locale.POSITIVE_SIGN) {
                    result = result.replace(locale.POSITIVE_SIGN, '');
                }
                if (locale.N_SIGN_POSN === 0 || locale.P_SIGN_POSN === 0) {
                    result = result.replace('(', '').replace(')', '')
                }
                if (locale.NEGATIVE_SIGN && result.indexOf(locale.NEGATIVE_SIGN) !== -1) {
                    result = result.replace(locale.NEGATIVE_SIGN, '')
                    result = '-' + result
                }
                result = $.trim(result.replace(locale.MON_DECIMAL_POINT, '.'));
                result = parseFloat(result);
            }
            return result;
        }

        int_to_str(value) {
            if (value || value === 0) {
                return value.toString();
            }
            else {
                return '';
            }
        }

        float_to_str(value) {
            var str,
                i,
                result = '';
            if (value || value === 0) {
                str = ('' + value.toFixed(6)).replace(".", locale.DECIMAL_POINT);
                i = str.length - 1;
                for (; i >= 0; i--) {
                    if ((str[i] === '0') && (result.length === 0)) {
                        continue;
                    } else {
                        result = str[i] + result;
                    }
                }
                if (result.slice(result.length - 1) === locale.DECIMAL_POINT) {
                    result = result + '0';
                }
            }
            return result;
        }

        date_to_str(value) {
            if (value) {
                return this.format_date_to_string(value, locale.D_FMT);
            }
            else {
                return '';
            }
        }

        datetime_to_str(value) {
            if (value) {
                return this.format_date_to_string(value, locale.D_T_FMT);
            }
            else {
                return '';
            }
        }

        cur_to_str(value) {
            var point,
                dec,
                digits,
                i,
                d,
                count = 0,
                len,
                result = '';

            if (value || value === 0) {
                result = round(value, locale.FRAC_DIGITS).toFixed(locale.FRAC_DIGITS);
                if (isNaN(result[0])) {
                    result = result.slice(1, result.length);
                }
                point = result.indexOf('.');
                dec = '';
                digits = result;
                if (point >= 0) {
                    digits = result.slice(0, point);
                    dec = result.slice(point + 1, result.length);
                }
                result = '';
                len = digits.length;
                for (i = 0; i < len; i++) {
                    d = digits[len - i - 1];
                    result = d + result;
                    count += 1;
                    if ((count % 3 === 0) && (i !== len - 1)) {
                        result = locale.MON_THOUSANDS_SEP + result;
                    }
                }
                if (dec) {
                    result = result + locale.MON_DECIMAL_POINT + dec;
                }
                if (value < 0) {
                    if (locale.N_SIGN_POSN === 3) {
                        result = locale.NEGATIVE_SIGN + result;
                    } else if (locale.N_SIGN_POSN === 4) {
                        result = result + locale.NEGATIVE_SIGN;
                    }
                } else {
                    if (locale.P_SIGN_POSN === 3) {
                        result = locale.POSITIVE_SIGN + result;
                    } else if (locale.P_SIGN_POSN === 4) {
                        result = result + locale.POSITIVE_SIGN;
                    }
                }
                if (locale.CURRENCY_SYMBOL) {
                    if (value < 0) {
                        if (locale.N_CS_PRECEDES) {
                            if (locale.N_SEP_BY_SPACE) {
                                result = locale.CURRENCY_SYMBOL + ' ' + result;
                            } else {
                                result = locale.CURRENCY_SYMBOL + result;
                            }
                        } else {
                            if (locale.N_SEP_BY_SPACE) {
                                result = result + ' ' + locale.CURRENCY_SYMBOL;
                            } else {
                                result = result + locale.CURRENCY_SYMBOL;
                            }
                        }
                    } else {
                        if (locale.P_CS_PRECEDES) {
                            if (locale.P_SEP_BY_SPACE) {
                                result = locale.CURRENCY_SYMBOL + ' ' + result;
                            } else {
                                result = locale.CURRENCY_SYMBOL + result;
                            }
                        } else {
                            if (locale.P_SEP_BY_SPACE) {
                                result = result + ' ' + locale.CURRENCY_SYMBOL;
                            } else {
                                result = result + locale.CURRENCY_SYMBOL;
                            }
                        }
                    }
                }
                if (value < 0) {
                    if (locale.N_SIGN_POSN === 0 && locale.NEGATIVE_SIGN) {
                        result = locale.NEGATIVE_SIGN + '(' + result + ')';
                    } else if (locale.N_SIGN_POSN === 1) {
                        result = locale.NEGATIVE_SIGN + result;
                    } else if (locale.N_SIGN_POSN === 2) {
                        result = result + locale.NEGATIVE_SIGN;
                    }
                } else {
                    if (locale.P_SIGN_POSN === 0 && locale.POSITIVE_SIGN) {
                        result = locale.POSITIVE_SIGN + '(' + result + ')';
                    } else if (locale.P_SIGN_POSN === 1) {
                        result = locale.POSITIVE_SIGN + result;
                    } else if (locale.P_SIGN_POSN === 2) {
                        result = result + locale.POSITIVE_SIGN;
                    }
                }
            }
            return result;
        }

        parseDateInt(str, digits) {
            var result = parseInt(str.substring(0, digits), 10);
            if (isNaN(result)) {
                throw new Error(language.invalid_date.replace('%s', ''))
            }
            return result;
        }

        format_string_to_date(str, format) {
            var ch = '',
                substr = str,
                day, month, year,
                hour = 0,
                min = 0,
                sec = 0;
            if (str) {
                for (var i = 0; i < format.length; ++i) {
                    ch = format.charAt(i);
                    switch (ch) {
                        case "%":
                            break;
                        case "d":
                            day = this.parseDateInt(substr, 2);
                            substr = substr.slice(2);
                            break;
                        case "m":
                            month = this.parseDateInt(substr, 2);
                            substr = substr.slice(2);
                            break;
                        case "Y":
                            year = this.parseDateInt(substr, 4);
                            substr = substr.slice(4);
                            break;
                        case "H":
                            hour = this.parseDateInt(substr, 2);
                            substr = substr.slice(2);
                            break;
                        case "M":
                            min = this.parseDateInt(substr, 2);
                            substr = substr.slice(2);
                            break;
                        case "S":
                            sec = this.parseDateInt(substr, 2);
                            substr = substr.slice(2);
                            break;
                        default:
                            substr = substr.slice(ch.length);
                    }
                }
                if (month < 1 || month > 12 || day < 1 || day > 31 || hour < 0 || hour > 24 ||
                    min < 0 || min > 60 || sec < 0 || sec > 60) {
                        throw new Error(language.invalid_date.replace('%s', str));
                }
                return new Date(year, month - 1, day, hour, min, sec);
            }
            else {
                return str;
            }
        }

        leftPad(value, len, ch) {
            var result = value.toString();
            while (result.length < len) {
                result = ch + result;
            }
            return result;
        }

        format_date_to_string(date, format) {
            var ch = '',
                result = '';
            for (var i = 0; i < format.length; ++i) {
                ch = format.charAt(i);
                switch (ch) {
                    case "%":
                        break;
                    case "d":
                        result += this.leftPad(date.getDate(), 2, '0');
                        break;
                    case "m":
                        result += this.leftPad(date.getMonth() + 1, 2, '0');
                        break;
                    case "Y":
                        result += date.getFullYear();
                        break;
                    case "H":
                        result += this.leftPad(date.getHours(), 2, '0');
                        break;
                    case "M":
                        result += this.leftPad(date.getMinutes(), 2, '0');
                        break;
                    case "S":
                        result += this.leftPad(date.getSeconds(), 2, '0');
                        break;
                    default:
                        result += ch;
                }
            }
            return result;
        }

        sanitize_html(text) {
            let element = document.createElement('div');
            element.innerText = text;
            return element.innerHTML;
        }
    }


    class Task extends AbsrtactItem {
        constructor(item_name, caption) {
            super(undefined, 0, item_name, caption, true);
            this.consts = consts;
            this.task = this;
            this.user_info = {};
            this._grid_id = 0;
            this._edited_items = [];
            this.events = {};
            this.form_options = {
                left: undefined,
                top: undefined,
                title: '',
                fields: [],
                form_header: true,
                form_border: false,
                close_button: true,
                close_on_escape: true,
                close_focusout: false,
                print: false,
                width: 0,
                tab_id: ''
            };
            this.edit_options = $.extend({}, this.form_options, {
                history_button: true,
                edit_details: [],
                detail_height: 0,
                buttons_on_top: false,
                modeless: false
            });
            this.view_options = $.extend({}, this.form_options, {
                history_button: true,
                refresh_button: true,
                enable_search: true,
                search_field: undefined,
                enable_filters: true,
                view_detail: undefined,
                detail_height: 0,
                buttons_on_top: false
            });
            this.table_options = {
                multiselect: false,
                dblclick_edit: true,
                height: 0,
                striped: false,
                row_count: 0,
                row_line_count: 1,
                title_line_count: 1,
                expand_selected_row: 0,
                freeze_count: 0,
                sort_fields: [],
                edit_fields: [],
                summary_fields: []
            };
            this.constructors = {
                task: Task,
                group: Group,
                item: Item,
                detail: Detail
            };
        }

        getChildClass() {
            return Group;
        }

        process_request(request, item, params, callback) {
            var self = this,
                date = new Date().getTime(),
                async = false,
                statusCode = {},
                contentType = "application/json;charset=utf-8",
                reply;

            if (callback) {
                async = true;
            }
            if (this.ajaxStatusCode) {
                statusCode = this.ajaxStatusCode;
            }

            $.ajax({
                url: "api",
                type: "POST",
                contentType: contentType,
                async: async,
                cache: false,
                data: JSON.stringify([request, this.ID, item.ID, params, self.modification]),
                statusCode: statusCode,
                success: function(data) {
                    var mess;
                    if (data.result.status === consts.RESPONSE || data.error) {
                        if (data.error) {
                            console.error(data.error);
                        }
                        if (callback) {
                            callback.call(item, data.result.data);
                        } else {
                            reply = data.result.data;
                        }
                    } else {
                        if (data.result.status === consts.PROJECT_NOT_LOGGED) {
                            location.reload();
                        } else if (self.ID && data.result.status === consts.PROJECT_MODIFIED) {
                            if (!self.task._version_changed) {
                                self.task._version_changed = true;
                                self.message('<h4 class="text-info">' + language.version_changed + '</h4>', {
                                    margin: '50px 50px',
                                    width: 500,
                                    text_center: true
                                });
                            }
                            return;
                        } else if (data.result.status === consts.PROJECT_MAINTAINANCE) {
                            if (!self._under_maintainance) {
                                self._under_maintainance = true;
                                if (language) {
                                    mess = language.website_maintenance;
                                } else {
                                    mess = 'Web site currently under maintenance.';
                                }
                                item.warning(mess, function() {
                                    self._under_maintainance = undefined;
                                });
                            }
                            setTimeout(function() { self.load() }, 1000);
                            return;
                        }
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    if (jqXHR.responseText && self.ID !== 0) {
                        document.open();
                        document.write(jqXHR.responseText);
                        document.close();
                    } else if (language) {
                        task.alert_error(language.server_request_error);
                        if (callback) {
                            callback.call(item, [null, language.server_request_error]);
                        }
                    }
                },
                fail: function(jqXHR, textStatus, errorThrown) {
                    console.log('ajax fail: ', jqXHR, textStatus, errorThrown);
                }
            });
            if (reply !== undefined) {
                return reply;
            }
        }

        upload_file(options, form, event) {
            var xhr = new XMLHttpRequest(),
                formData = new FormData(form.get(0)),
                self = this,
                message;
            if (options.blob) {
                formData.append("file", options.blob);
            }
            formData.append("file_name", options.file_name);
            formData.append("path", options.path);
            formData.append("task_id", self.ID);
            formData.append("item_id", options.item_id);
            formData.append("field_id", options.field_id);
            xhr.open('POST', 'upload', true);
            if (options.callback) {
                xhr.onload = function(e) {
                    var response,
                        data;
                    if (e.currentTarget.status === 200) {
                        response = JSON.parse(e.currentTarget.response);
                        if (response.error) {
                            self.alert_error(response.error, {duration: 10});
                        }
                        else if (options.callback) {
                            data = response.result.data;
                            options.callback.call(self, data.file_name, options.file_name, data.path);
                        }
                    }
                    else {
                        self.alert_error(e.currentTarget.statusText, {duration: 10})
                        if (message) {
                            self.hide_message(message);
                        }
                    }
                };
            }
            if (options.show_progress) {
                xhr.upload.onprogress = function(e) {
                    var percent,
                        pb =
                        '<div class="progress">' +
                            '<div class="bar" style="width: 0%;"></div>' +

                        '</div>' +
                        '<div class="percent text-center"></div>';
                    if (e.loaded === e.total) {
                        if (message) {
                            self.hide_message(message);
                        }
                    }
                    else {
                        if (!message) {
                            message = self.message(pb,
                                {margin: "20px 20px", text_center: true, width: 500});
                        }
                        else {
                            percent = parseInt(100 * e.loaded / e.total, 10) + '%';
                            message.find('.bar').width(percent);
                            message.find('.percent').html('<b>' + percent + '</b>');
                        }
                    }
                }
            }

            if (event) {
                event.preventDefault();
            }
            xhr.send(formData);
        }

        upload() {
            var self = this,
                args = this._check_args(arguments),
                options = args['object'],
                path = args['string'],
                default_options = {
                    callback: undefined,
                    show_progress: true,
                    accept: undefined,
                    blob: undefined,
                    file_name: undefined,
                    item_id: -1,
                    field_id: -1
                },
                accept = '',
                form,
                file,
                button,
                submit_button;

            options = $.extend({}, default_options, options);
            if (options.accept) {
                accept = 'accept="' + options.accept + '"';
            }
            if (path === undefined) {
                path = '';
            }
            options.path = path;
            $('body').find('#upload-file-form').remove();
            form = $(
                '<form id="upload-file-form" enctype="multipart/form-data" method="post" style="position: absolute; top: -1000px; z-index: 10000;">' +
                    '<input id="inp-btn" type="file" name="file" ' + accept + ' required />' +
                    '<input id="submit-btn" type="submit" value="Submit" />' +
                '</form>'
            );
            button = form.find('#inp-btn');
            submit_button = form.find('#submit-btn');
            $('body').append(form);
            if (options.blob) {
                self.upload_file(options, form);
                form.remove();
            }
            else {
                button.on('change', function(e) {
                    options.file_name = e.target.files[0].name;
                    submit_button.submit();
                });
            }
            submit_button.on('submit', function(e) {
                self.upload_file(options, form, e);
                form.remove();
            })
            button.click();
        }

        logout() {
            this.send_request('logout', undefined, function() {
                location.reload();
            });
        }

        load(callback) {
            var self = this,
                info;
            this.send_request('load', null, function(data) {
                if (self._loaded) {
                    return;
                }
                self._loaded = true;
                var info = data[0],
                    error = data[1],
                    templates;
                if (error) {
                    self.warning(error);
                    return;
                }
                settings = info.settings;
                locale = info.locale;
                language = info.language;
                self.settings = settings;
                self.language = language;
                self.locale = locale;
                self.user_info = info.user_info;
                self.user_privileges = info.privileges;
                self.consts = consts;
                self.safe_mode = self.settings.SAFE_MODE;
                self.forms_in_tabs = self.settings.FORMS_IN_TABS;
                self.full_width = self.settings.FULL_WIDTH;
                self.version = self.settings.VERSION;
                self.modification = self.settings.MODIFICATION;
                self.ID = info.task.id;
                self.item_name = info.task.name;
                self.item_caption = info.task.caption;
                self.visible = info.task.visible;
                self.lookup_lists = info.task.lookup_lists;
                self.history_item = info.task.history_item;
                self.item_type = "";
                if (info.task.type) {
                    self.item_type = self.types[info.task.type - 1];
                }
                if (info.task.js_filename) {
                    self.js_filename = 'js/' + info.task.js_filename;
                }
                self.task = self;
                self.init_templates(info);
                self.init(info.task);
                self.bind_items();
                if (self.ID === 0) {
                    self.js_filename = 'jam/js/admin.js';
                    self.settings.DYNAMIC_JS = false;
                }
                self.init_modules(callback);
                if (self.history_item) {
                    self._set_history_item(self.item_by_ID(self.history_item))
                }
                window.onbeforeunload = function() {
                    var i,
                        item;
                    for (i = 0; i < self._edited_items.length; i++) {
                        item = self._edited_items[i];
                        if (item.is_changing() && item.is_modified()) {
                            if (item._tab_info) {
                                self.show_tab(item._tab_info.container, item._tab_info.tab_id);
                            }
                            return 'You have unsaved changes!';
                        }
                    }
                }
            });
        }

        init_templates(info) {
            let self = this,
                class_list = {},
                div = $('<div class="templates">'),
                temp = $('<output>').append(div);
            div.append($.parseHTML(info.templates));
            this.templates = temp.find('.templates');
            temp.find('.templates > div').each(function() {
                for (let i=0; i < this.classList.length; i++) {
                    class_list[this.classList[i]] = true;
                }
            })
            $(".templates > div").each(function() {
                let not_found = false;
                for (let i=0; i < this.classList.length; i++) {
                    if (!class_list[this.classList[i]]) {
                        not_found = true;
                        break;
                    }
                }
                if (not_found) {
                    self.templates.append($(this));
                }
            })
        }

        init_modules(callback) {
            var self = this,
                mutex = 0,
                calcback_executing = false,
                calc_modules = function(item) {
                    if (item.js_filename) {
                        mutex++;
                    }
                },
                load_script = function(item) {
                    if (item.js_filename) {
                        item.load_script(
                            item.js_filename,
                            function() {
                                if (--mutex === 0) {
                                    self.bind_events();
                                    if (!calcback_executing) {
                                        calcback_executing = true;
                                        self._page_loaded(callback);
                                    }
                                }
                            }
                        );
                    }
                };

            if (this.settings.DYNAMIC_JS) {
                mutex = 1;
                load_script(this);
            } else {
                this.all(calc_modules);
                this.all(load_script);
            }
        }

        _page_loaded(callback) {
            if (locale.RTL) {
                $('html').attr('dir', 'rtl')
            }
            if (this.on_page_loaded) {
                this.on_page_loaded.call(this, this);
            }
            if (callback) {
                callback.call(this)
            }
        }

        _set_history_item(item) {
            var self = this,
                doc_name;
            this.history_item = item;
            if (this.history_item) {
                this.history_item.read_only = true;
                item.view_options.fields = ['item_id', 'item_rec_id', 'date', 'operation', 'user'];
                if (!item.on_field_get_text) {
                    item.on_field_get_text = function(field) {
                        var oper,
                            it;
                        if (field.field_name === 'operation') {
                            if (field.value === consts.RECORD_INSERTED) {
                                return self.language.created;
                            }
                            else if (field.value === consts.RECORD_MODIFIED ||
                                field.value === consts.RECORD_DETAILS_MODIFIED) {
                                return self.language.modified;
                            }
                            else if (field.value === consts.RECORD_DELETED) {
                                return self.language.deleted;
                            }
                        }
                        else if (field.field_name === 'item_id') {
                            it = self.item_by_ID(field.value);
                            if (it) {
                                doc_name = it.item_caption;
                                return doc_name;
                            }
                        }
                    }
                }
                this.history_item.edit_record = function() {
                    var it = item.task.item_by_ID(item.item_id.value),
                        hist = item.task.history_item.copy();
                    hist.set_where({item_id: item.item_id.value, item_rec_id: item.item_rec_id.value});
                    hist.set_order_by(['-date']);
                    hist.open({limit: 100}, function() {
                    //~ hist.open(function() {
                        it.display_history(hist);
                    });
                }
            }
        }

        has_privilege(item, priv_name) {
            var priv_dic;
            if (item.task.ID === 0) {
                return true;
            }
            if (item.master) {
                if (!item.master.can_edit() && !item.master.can_create()) {
                    return false;
                }
            }
            if (!this.user_privileges) {
                return true;
            } else {
                if (!this.user_privileges) {
                    return false;
                }
                try {
                    priv_dic = this.user_privileges[item.ID];
                } catch (e) {
                    priv_dic = null;
                }
                if (priv_dic) {
                    return priv_dic[priv_name];
                } else {
                    return false;
                }
            }
        }

        create_cookie(name, value, days) {
            var expires;

            if (days) {
                var date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                expires = "; expires=" + date.toGMTString();
            } else {
                expires = "";
            }
            document.cookie = escape(name) + "=" + escape(value) + expires + "; path=/";
        }

        read_cookie(name) {
            var nameEQ = escape(name) + "=";
            var ca = document.cookie.split(';');
            for (var i = 0; i < ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) === ' ') c = c.substring(1, c.length);
                if (c.indexOf(nameEQ) === 0) return unescape(c.substring(nameEQ.length, c.length));
            }
            return null;
        }

        erase_cookie(name) {
            this.create_cookie(name, "", -1);
        }

        set default_content_visible(value) {
            let default_content = $('#container > #default-content');
            if (value) {
                default_content.show();
            }
            else {
                default_content.hide();
            }
        }

        set_forms_container(container, options) {
            if (container && container.length) {
                let default_content = $('#default-content');
                this.forms_container = container;
                if (!default_content.length) {
                    default_content = $('<div id="default-content">')
                    default_content.insertBefore(container);
                }
                if (options && options.splash_screen) {
                    default_content.append(options.splash_screen)
                }
                if (this.forms_in_tabs) {
                    this.init_tabs(container, 'tabs-top', true);
                }
            }
        }

        create_menu_item(menu_item, parent, options) {
            if (menu_item.items.length) {
                if (menu_item.items.length === 1 && !options.create_group_for_single_item) {
                    this.create_menu_item(menu_item.items[0], parent, options);
                }
                else {
                    let li,
                        ul;
                    if (parent.hasClass('dropdown-menu')) {
                        li = $('<li class="dropdown-submenu"><a tabindex="-1" href="#">' +
                            menu_item.caption + '</a></li>');
                    }
                    else {
                        li = $('<li class="dropdown"><a class="dropdown-toggle" data-toggle="dropdown" href="#">' +
                            menu_item.caption + ' <b class="caret"></b></a></li>');
                    }
                    parent.append(li);
                    ul = $('<ul class="dropdown-menu">');
                    li.append(ul);
                    for (let i = 0; i < menu_item.items.length; i++) {
                        this.create_menu_item(menu_item.items[i], ul, options)
                    }
                }
            }
            else {
                if (menu_item.caption) {
                    parent.append($('<li>')
                        .append($('<a class="item-menu" href="#">' + menu_item.caption + '</a>')
                        .data('action', menu_item.action)));
                }
                else {
                    parent.append($('<li class="divider"></li>'));
                }
            }
        }

        add_menu_item(custom_item, parent) {
            let menu_item = {},
                item = custom_item,
                sub_items = [];
            if (custom_item instanceof Array) {
                item = custom_item[0];
                if (custom_item.length > 1) {
                    sub_items = custom_item[1]
                }
            }
            else if (custom_item instanceof Object && !(item instanceof AbsrtactItem)) {
                for (item in custom_item) {
                    if (custom_item[item] instanceof Array) {
                        sub_items = custom_item[item];
                    }
                    else if (custom_item[item] instanceof AbsrtactItem) {
                        sub_items[0] = custom_item[item];
                    }
                    else if (typeof custom_item[item] === "function") {
                        menu_item.action = custom_item[item];
                    }
                }
            }
            menu_item.items = [];
            if (item instanceof AbsrtactItem) {
                menu_item.caption = item.item_caption;
                if (item instanceof Group) {
                    if (item.visible) {
                        item.each_item(function(i) {
                            if (i.visible && i.can_view()) {
                                sub_items.push(i);
                            }
                        });
                    }
                    else {
                        return;
                    }
                }
                else {
                    if (item.visible && item.can_view()) {
                        if (item instanceof Item) {
                            menu_item.action = function() {
                                item.view(this.forms_container);
                            }
                        }
                        else if (item instanceof Report) {
                            menu_item.action = function() {
                                item.print(false);
                            }
                        }
                    }
                    else {
                        return;
                    }
                }
            }
            else {
                menu_item.caption = item;
            }
            parent.items.push(menu_item)
            for (let i = 0; i < sub_items.length; i++) {
                this.add_menu_item(sub_items[i], menu_item);
            }
        }

        create_menu() {
            var self = this,
                $menu = arguments[0],
                forms_container = arguments[1],
                options = arguments[2],
                custom_menu,
                menu_items = {},
                default_options = {
                    custom_menu: undefined,
                    forms_container: undefined,
                    splash_screen: undefined,
                    view_first: false,
                    create_single_group: false,
                    create_group_for_single_item: false
                };
            if (arguments.length === 2) {
                options = arguments[1];
                forms_container = options.forms_container;
            }
            options = $.extend({}, default_options, options);

            this.set_forms_container(forms_container, {splash_screen: options.splash_screen});

            custom_menu = options.custom_menu;
            if (!custom_menu) {
                custom_menu = [];
                task.each_item(function(group) {
                    if (group.visible) {
                        let item_count = 0;
                        group.each_item(function(item) {
                            if (item.visible) {
                                item_count += 1;
                            }
                        });
                        if (item_count > 0) {
                            custom_menu.push(group);
                        }
                    }
                });
                if (custom_menu.length === 1 && !options.create_single_group) {
                    let group = custom_menu[0]
                    custom_menu = []
                    group.each_item(function(item) {
                        if (item.visible) {
                            custom_menu.push(item);
                        }
                    });
                }
            }
            menu_items.items = [];
            for (let i = 0; i < custom_menu.length; i++) {
                this.add_menu_item(custom_menu[i], menu_items);
            }
            for (let i = 0; i < menu_items.items.length; i++) {
                this.create_menu_item(menu_items.items[i], $menu, options);
            }
            $menu.find('.item-menu').on('click', (function(e) {
                var action = $(this).data('action');
                e.preventDefault();
                if (action) {
                    action.call(self);
                }
            }));
            if (options.view_first) {
                $menu.find('.item-menu:first').click();
            }
        }

        view_form_created(item) {
        }

        edit_form_created(item) {
            //~ let new_details = false;
            //~ item.each_detail(function(d) {
                //~ if (d.master_field) {
                    //~ new_details = true;
                    //~ return false;
                //~ }
            //~ })
            //~ if (new_details) {
                //~ item.edit_form.find('.form-footer').hide();
            //~ }
        }

        _tab_content(tab) {
            var item_name = tab.find('a').attr('href').substr(1);
            return tab.parent().parent().find('> div.tab-content > div.' + item_name)
        }

        _focus_element(element) {
            var focused = false;
            element.find(':input:not(:button):enabled:visible').each(function(el) {
                if (this.tabIndex !== -1) {
                    this.focus();
                    focused = true;
                    return false;
                }
            })
            if (!focused) {
                element.focus();
            }
        }

        _show_tab(tab) {
            var item_name = tab.find('a').attr('href').substr(1),
                el,
                tab_content = this._tab_content(tab),
                tab_div = tab.parent().parent().parent();
            tab_div.find('> .tabbable > div.tab-content > div.tab-pane').removeClass('active');
            tab_content.addClass('active').trigger('tab_active_changed');
            tab_div.find('> .tabbable > ul.nav-tabs > li').removeClass('active');
            tab.addClass('active');
            el = tab_content.data('active_el');
            if (el) {
                el.focus();
            }
            else {
                this._focus_element(tab_content);
            }
            tab_content.on('tab_active_changed', function() {
                var form = tab_content.find('.jam-form:first');
                if (form.length) {
                    form.trigger('active_changed');
                }
            });
        }

        _check_tabs_empty(container) {
            var tabs = container.find('> .tabbable');
            if (tabs.find('> ul.nav-tabs > li').length) {
                tabs.show();
            }
            else {
                tabs.hide();
            }
        }

        show_tab(container, tab_id) {
            var tab = container.find('> .tabbable > ul.nav-tabs > li a[href="#' + tab_id + '"]');
            if (tab.length) {
                this._show_tab(tab.parent());
            }
            this._check_tabs_empty(container);
        }

        _close_tab(tab) {
            var tabs = tab.parent(),
                tab_content = this._tab_content(tab),
                new_tab;
            this._show_tab(tab);
            if (tab.prev().length) {
                new_tab = tab.prev()
            }
            else {
                new_tab = tab.next()
            }
            this._tab_content(tab).remove()
            tab.remove();
            if (new_tab.length) {
                this._show_tab(new_tab);
            }
            if (!tabs.children().length) {
                tabs.parent().hide();
            }
        }

        close_tab(container, tab_id) {
            var tab = container.find('> .tabbable > ul.nav-tabs > li a[href="#' + tab_id + '"]');
            if (tab.length) {
                this._close_tab(tab.parent());
            }
            this._check_tabs_empty(container);
        }

        init_tabs(container, tabs_position, hide) {
            var self = this,
                div;
            if (!tabs_position) {
                tabs_position = 'tabs-top'
            }
            div = $('<div class="tabbable ' + tabs_position + '">');
            container.empty();
            container.append(div);
            if (hide) {
                div.hide();
            }
            if (tabs_position === 'tabs-below') {
                div.append('<div class="tab-content">');
                div.append('<ul class="nav nav-tabs">');
            }
            else {
                div.append('<ul class="nav nav-tabs">');
                div.append('<div class="tab-content">');
            }
            div.hide();
        }

        can_add_tab(container) {
            return container.find('> .tabbable  > ul.nav-tabs').length > 0
        }

        add_tab(container, tab_name, options) {
            var self = this,
                div,
                tabs,
                active_tab,
                tab_content,
                tab_text,
                cur_tab,
                cur_tab_content;
            if (!container.length) {
                this.warning('Container must be specified.')
            }
            if (!tab_name) {
                this.warning('Tab name must be specified.')
            }
            if (!options) {
                options = {};
            }
            tabs = container.find('> .tabbable > ul.nav-tabs');
            if (tabs.length) {
                active_tab = tabs.find('> li.active');
                if (options.tab_id === undefined) {
                    options.tab_id = 'tab' + tabs.find('> li').length + 1;
                }
                cur_tab = tabs.find('> li a[href="#' + options.tab_id + '"]');
                if (cur_tab.length) {
                    cur_tab = cur_tab.parent();
                }
                else {
                    tab_content = container.find('> .tabbable > div.tab-content');
                    if (options.show_close_btn) {
                        tab_name = '<span> ' + tab_name + ' </span><i class="icon-remove close-tab-btn"></i>';
                    }
                    cur_tab = $('<li><a href="#' + options.tab_id + '">' +
                        tab_name + '</a></li>');
                    cur_tab_content = $('<div class="tab-pane ' + options.tab_id + '"></div>');
                    if (options.insert_after_cur_tab) {
                        cur_tab.insertAfter(active_tab)
                    }
                    else {
                        tabs.append(cur_tab);
                    }
                    tab_content.append(cur_tab_content);
                    cur_tab.on('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        self._show_tab($(this));
                        if (options.on_click) {
                            options.on_click.call(self, options.tab_id);
                        }
                    });
                    cur_tab_content.on('focusout', function(e) {
                        var found;
                        $(e.target).parents().each(function() {
                            if (this === cur_tab_content.get(0)) {
                                cur_tab_content.data('active_el', e.target);
                                return false;
                            }
                        })
                    });
                    if (options.show_close_btn) {
                        cur_tab.on('click', '.close-tab-btn', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            if (options.on_close) {
                                options.on_close.call();
                            }
                            else {
                                self.close_tab(container, options.tab_id);
                            }
                        });
                    }
                }
                if (options.set_active || !active_tab.length) {
                    this.show_tab(container, options.tab_id);
                }
                return cur_tab_content
            }
        }
    }


    class Group extends AbsrtactItem {
        constructor(owner, ID, item_name, caption, visible, type, js_filename) {
            super(owner, ID, item_name, caption, visible, type, js_filename);
        }

        getChildClass() {
            if (this.item_type === "reports") {
                return Report;
            } else {
                return Item;
            }
        }
    }

    class RecInfo {
        constructor(item) {
            this.item = item;
            this.expanded = item.expanded;
            this.record_status = consts.RECORD_UNCHANGED;
            this.log_index = null;
            this.details = {};
        }

        add_detail(detail_change_log) {
            this.details[detail_change_log.item.ID] = detail_change_log;
        }

        get_changes() {
            let result = {};
            for (let ID in this.details) {
                let detail = this.details[ID],
                    detail_changes = {};
                detail.get_changes(detail_changes);
                result[ID] = detail_changes;
            }
            return result;
        }

        update(details) {
            this.log_index = null;
            for (let ID in details) {
                this.details[ID].update(details[ID]);
            }
        }

        copy() {
            let result = new RecInfo(this.item);
            result.record_status  = this.record_status;
            result.log_index = this.log_index;
            result.details = {};
            for (let ID in this.details) {
                result.details[ID] = this.details[ID].copy();
            }
            return result;
        }

        restore() {
            for (let ID in this.details) {
                this.details[ID].restore();
            }
        }
    }

    class ChangeLog {
        constructor(item, copy) {
            let self = this;
            this.item = item;
            this.expanded = item.expanded
            this.logs = [];
            this.dataset = item._dataset;
            this.fields = [];
            this.item.each_field(function(field) {
                self.fields.push(field.field_name);
            });
            if (this.item.master && !copy) {
                this.item.master.change_log.record_info.add_detail(this);
            }
        }

        detail_change_log(detail) {
            return this.record_info[detail.ID];
        }

        get cur_record() {
            return this.item._dataset[this.item.rec_no];
        }

        set cur_record(value) {
            this.item._dataset[this.item.rec_no] = value;
        }

        get record_info() {
            return this.get_record_info();
        }

        get_record_info(record) {
            if (!record) {
                record = this.cur_record;
            }
            if (record.length < this.item._record_info_index + 1) {
                record.push(new RecInfo(this.item));
            }
            return record[this.item._record_info_index];
        }

        get record_status() {
            return this.record_info.record_status;
        }

        set record_status(value) {
            if (this.record_info.log_index === null) {
                if (value !== consts.RECORD_UNCHANGED) {
                    this.logs.push(this.cur_record);
                    this.record_info.log_index = this.logs.length - 1;
                }
            }
            else {
                if (value === consts.RECORD_UNCHANGED) {
                    this.logs[this.record_info.log_index] = null;
                    this.cur_record[this.item._record_info_index] = new RecInfo(this.item);
                }
                else {
                    this.logs[this.record_info.log_index] = this.cur_record;
                }
            }
            this.record_info.record_status = value;
        }

        get empty() {
            for (let i = 0; i < this.logs.length; i++) {
                if (this.logs[i]) {
                    return false;
                }
            }
            return true;
        }

        detail_modified() {
            if (this.record_status === consts.RECORD_UNCHANGED) {
                this.record_status = consts.RECORD_DETAILS_MODIFIED;
            }
            if (this.item.master) {
                this.item.master.change_log.detail_modified();
            }
        }

        log_change() {
            let state = this.item.item_state;
            if (this.item.log_changes) {
                if (state === consts.STATE_INSERT) {
                    this.record_status = consts.RECORD_INSERTED;
                } else if (state === consts.STATE_EDIT) {
                    if (this.record_status === consts.RECORD_UNCHANGED) {
                        this.record_status = consts.RECORD_MODIFIED;
                    } else if (this.record_status === consts.RECORD_DETAILS_MODIFIED) {
                        this.record_status = consts.RECORD_MODIFIED;
                    }
                } else if (state === consts.STATE_DELETE) {
                    if (this.record_status === consts.RECORD_INSERTED) {
                        this.record_status = consts.RECORD_UNCHANGED;
                    } else {
                        this.record_status = consts.RECORD_DELETED;
                    }
                } else {
                    throw new Error(this.item.item_name + ': change log invalid records state');
                }
                if (this.item.master) {
                    this.item.master.change_log.detail_modified();
                }
            }
        }

        copy_record(record) {
            return record.slice(0, this.item._record_info_index);
        }

        get_changes(result) {
            let logs = [],
                counter = 0;
            result.fields = this.fields;
            result.expanded = this.expanded;
            result.logs = logs;
            for (let i = 0; i < this.logs.length; i++) {
                let record = this.logs[i];
                if (record) {
                    let record_info = this.get_record_info(record);
                    if (record_info.record_status !== consts.RECORD_UNCHANGED) {
                        let new_record = this.copy_record(record);
                        logs.push({
                            record_status: record_info.record_status,
                            log_index: record_info.log_index,
                            record: new_record,
                            details: record_info.get_changes()
                        });
                        counter += 1;
                    }
                }
            };
            return counter;
        }

        update(updates) {
            if (updates) {
                let self = this,
                    logs = updates.logs;
                for (let i = 0; i < logs.length; i++) {
                    let log_index = logs[i].log_index,
                        record = logs[i].record,
                        log_record = this.logs[log_index],
                        rec_info = this.get_record_info(log_record);
                    if (logs[i].record_status !== consts.RECORD_DELETED) {
                        Array.prototype.splice.apply(log_record, [0, record.length].concat(record));
                    }
                    rec_info.record_status = consts.RECORD_UNCHANGED;
                    rec_info.update(logs[i].details);
                }
                this.logs = [];
                this.item.update_controls();
            }
        }

        copy() {
            let self = this,
                result = new ChangeLog(this.item, true);
            result.logs = [];
            result.fields = this.fields.slice();
            result.dataset = [];
            result.rec_no = null;
            if (this.dataset) {
                result.rec_no = this.item.rec_no;
                this.dataset.forEach(function(record) {
                    let rec_info_copy = self.get_record_info(record).copy(),
                        rec_copy = record.slice();
                    rec_copy[self.item._record_info_index] = rec_info_copy;
                    if (rec_info_copy.log_index !== null) {
                        result.logs.push(rec_copy);
                        rec_info_copy.log_index = result.logs.length - 1;
                    }
                    result.dataset.push(rec_copy);
                });
            }
            return result;
        }

        restore() {
            this.item._dataset = this.dataset;
            if (this.rec_no !== null) {
                this.item.rec_no = this.rec_no;
            }
            this.record_info.restore();
        }

        store_record() {
            let result = this.cur_record.slice();
            result[this.item._record_info_index] = this.record_info.copy();
            return result;
        }

        restore_record(data) {
            this.record_status = consts.RECORD_UNCHANGED
            this.cur_record = data;
            this.rec_no = null;
            this.restore();
            this.record_status = this.record_status;
        }
    }

    class Item extends AbsrtactItem {
        constructor(owner, ID, item_name, caption, visible, type, js_filename) {
            super(owner, ID, item_name, caption, visible, type, js_filename);
            if (this.task && this.item_type !== 'detail' && !(item_name in this.task)) {
                this.task[item_name] = this;
            }
            this.field_defs = [];
            this._fields = [];
            this.fields = [];
            this.filter_defs = [];
            this.filters = [];
            this.details = [];
            this.controls = [];
            this._paginate = undefined;
            this.disabled = false;
            this.expanded = true;
            this.permissions = {
                can_create: true,
                can_edit: true,
                can_delete: true
            };
            this._log_changes = true;
            this._dataset = null;
            this._eof = false;
            this._bof = false;
            this._cur_row = null;
            this._old_row = 0;
            this._buffer = null;
            this._modified = null;
            this._state = 0;
            this._read_only = false;
            this.owner_read_only = true;
            this._can_modify = true;
            this._active = false;
            this._virtual_table = false;
            this._disabled_count = 0;
            this._open_params = {};
            this._where_list = [];
            this._order_by_list = [];
            this._select_field_list = [];
            this._record_lookup_index = -1
            this._record_info_index = -1
            this._limit = 10;
            this._offset = 0;
            this._selections = undefined;
            this._show_selected = false;
            this.selection_limit = 1500;
            this.is_loaded = false;
            this.lookup_field = null;
            if (this.task) {
                this.view_options = $.extend({}, this.task.view_options);
                this.table_options = $.extend({}, this.task.table_options);
                this.edit_options = $.extend({}, this.task.edit_options);
                this.filter_options = $.extend({}, this.task.form_options);
            }
        }

        getChildClass() {
            return Detail;
        }

        initAttr(info) {
            var i,
                field_defs = info.fields,
                filter_defs = info.filters,
                len;
            if (field_defs) {
                len = field_defs.length;
                for (i = 0; i < len; i++) {
                    this.field_defs.push(field_defs[i]);
                    new Field(this, field_defs[i]);
                }
            }
            if (filter_defs) {
                len = filter_defs.length;
                for (i = 0; i < len; i++) {
                    this.filter_defs.push(filter_defs[i]);
                    new Filter(this, filter_defs[i]);
                }
            }
            this.reports = info.reports;
        }

        _bind_item() {
            var i = 0,
                len,
                reports;

            this._prepare_fields();
            this._prepare_filters();

            len = this.reports.length;
            reports = this.reports;
            this.reports = [];
            for (i = 0; i < len; i++) {
                this.reports.push(this.task.item_by_ID(reports[i]));
            }
            this.init_params();
        }

        _can_do(operation) {
            if (this.master && !this.master.is_changing()) {
                return false;
            }
            return this.task.has_privilege(this, operation) &&
                this.permissions[operation] && this.can_modify;
        }

        can_create() {
            return this._can_do('can_create')
        }

        can_edit() {
            return this._can_do('can_edit')
        }

        can_delete() {
            return this._can_do('can_delete')
        }

        _prepare_fields() {
            var i = 0,
                len = this._fields.length,
                field,
                lookup_field,
                lookup_field1;
            for (; i < len; i++) {
                field = this._fields[i];
                if (field.lookup_item && (typeof field.lookup_item === "number")) {
                    field.lookup_item = this.task.item_by_ID(field.lookup_item);
                    if (field.lookup_field && (typeof field.lookup_field === "number")) {
                        lookup_field = field.lookup_item._field_by_ID(field.lookup_field);
                        field.lookup_field = lookup_field.field_name;
                        if (lookup_field.lookup_item && field.lookup_field1) {
                            field.lookup_item1 = lookup_field.lookup_item
                            if (typeof field.lookup_item1 === "number") {
                                field.lookup_item1 = this.task.item_by_ID(field.lookup_item1);
                            }
                            if (typeof field.lookup_field1 === "number") {
                                lookup_field1 = field.lookup_item1._field_by_ID(field.lookup_field1)
                                field.lookup_field1 = lookup_field1.field_name
                            }
                            if (lookup_field1.lookup_item && field.lookup_field2) {
                                field.lookup_item2 = lookup_field1.lookup_item;
                                if (typeof field.lookup_item2 === "number") {
                                    field.lookup_item2 = self.task.item_by_ID(field.lookup_item2);
                                }
                                if (typeof field.lookup_field2 === "number") {
                                    field.lookup_field2 = field.lookup_item2._field_by_ID(field.lookup_field2).field_name;
                                }
                            }

                        }
                    }
                }
                if (field.master_field && (typeof field.master_field === "number")) {
                    field.master_field = this.get_master_field(this._fields, field.master_field);
                }
                if (field.lookup_values && (typeof field.lookup_values === "number")) {
                    field.lookup_values = self.task.lookup_lists[field.lookup_values];
                }

            }
            this.fields = this._fields.slice(0);
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                if (this[field.field_name] === undefined) {
                    this[field.field_name] = field;
                }
            }
        }

        dyn_fields(fields) {
            var i,
                j,
                attr,
                val,
                field_type,
                data_type,
                field_def;
            this._fields = [];
            this.fields = [];
            this.field_defs = [];
            for (var i = 0; i < fields.length; i++) {
                field_def = []
                for (var j = 0; j < field_attr.length; j++) {
                    attr = field_attr[j];
                    if (attr.charAt(0) === '_') {
                        attr = attr.substr(1);
                    }
                    if (attr === 'data_type') {
                        attr = 'field_type'
                    }
                    val = fields[i][attr]
                    switch (attr) {
                        case 'ID':
                            val = i + 1;
                            break;
                        case 'field_type':
                            field_type = fields[i]['field_type']
                            val = field_type_names.indexOf(field_type);
                            if (val < 1) {
                                val = 1;
                            }
                            data_type = val;
                            break;
                        case 'field_size':
                            if (data_type === 1 && !val) {
                                val = 99999;
                            }
                            break;
                        case 'lookup_item':
                            if (val) {
                                lookup_item = val;
                                val = val.ID
                            }
                            break;
                    }
                    field_def.push(val);
                }
                this.field_defs.push(field_def);
            }
            for (i = 0; i < this.field_defs.length; i++) {
                new Field(this, this.field_defs[i]);
            }
            this._prepare_fields();
        }

        _prepare_filters() {
            var i = 0,
                len,
                field;
            len = this.filters.length;
            for (i = 0; i < len; i++) {
                field = this.filters[i].field;
                if (field.lookup_item && (typeof field.lookup_item === "number")) {
                    field.lookup_item = this.task.item_by_ID(field.lookup_item);
                }
                if (field.lookup_field && (typeof field.lookup_field === "number")) {
                    field.lookup_field = field.lookup_item._field_by_ID(field.lookup_field).field_name;
                }
            }
        }

        ids_to_field_names(ids) {
            var i,
                field,
                result = [];
            if (ids && ids.length) {
                for (i = 0; i < ids.length; i++) {
                    field = this._field_by_ID(ids[i]);
                    if (field) {
                        result.push(field.field_name);
                    }
                }
            }
            return result;
        }

        ids_to_item_names(ids) {
            var i,
                item,
                result = [];
            if (ids && ids.length) {
                for (i = 0; i < ids.length; i++) {
                    item = this.item_by_ID(ids[i]);
                    if (item) {
                        result.push(item.item_name);
                    }
                }
            }
            if (result.length) {
                return result;
            }
        }

        _process_view_params() {
            var i,
                index = 0,
                field_name,
                field,
                fields = [],
                order,
                table_options,
                table_fields,
                actions,
                form_template,
                form_options,
                column_width = {};
            if (this._view_params instanceof Array) { // for compatibility with previous versions
                for (i = 0; i < this._view_params.length; i++) {
                    field = this._field_by_ID(this._view_params[i][0]);
                    if (field) {
                        fields.push([field.ID, '']);
                    }
                }
                this._view_params = {0: ['', {}, [], {}, fields]};
            }

            if (this._view_params[index] === undefined) {
                index = 0;
            }

            form_template = this._view_params[index][0];
            form_options = this._view_params[index][1];
            actions = this._view_params[index][2];
            table_options = this._view_params[index][3];
            table_fields = this._view_params[index][4];

            fields = []
            for (i = 0; i < table_fields.length; i++) {
                field = this._field_by_ID(table_fields[i][0]);
                if (field) {
                    field_name = field.field_name;
                    fields.push(field_name);
                    if (table_fields[i][1]) {
                        column_width[field_name] = table_fields[i][1];
                    }
                }
            }
            this.view_options.fields = fields;

            form_options.default_order = [];
            if (this._default_order) {
                for (i = 0; i < this._default_order.length; i++) {
                    field = this._field_by_ID(this._default_order[i][0]);
                    if (field) {
                        order = field.field_name;
                        if (this._default_order[i][1]) {
                            order = '-' + order
                        }
                        form_options.default_order.push(order);
                    }
                    else {
                        form_options.default_order = [];
                        break;
                    }
                }
            }
            this._default_order = undefined;

            form_options.view_detail = this.ids_to_item_names(form_options.view_detail);
            form_options.view_details = form_options.view_detail; // for compatibility with previous versions
            form_options.search_field = this.ids_to_field_names(form_options.search_field);
            form_options.search_field = form_options.search_field.length ? form_options.search_field[0] : undefined;
            table_options.column_width = column_width;
            table_options.summary_fields = this.ids_to_field_names(table_options.summary_fields);
            table_options.editable_fields = this.ids_to_field_names(table_options.edit_fields);
            delete table_options.edit_fields;
            table_options.sort_fields = this.ids_to_field_names(table_options.sort_fields);

            this.view_options.title = this.item_caption;
            this.view_options = $.extend(this.view_options, form_options);
            this._view_options = $.extend({}, this.view_options);
            this.table_options = $.extend(this.table_options, table_options);
            this._table_options = $.extend({}, this.table_options);
        }

        _process_edit_params() {
            var i,
                j,
                k,
                index = 0,
                field_name,
                field,
                fields = [],
                tab,
                tabs,
                band,
                bands,
                form_tabs,
                actions,
                form_template,
                form_options,
                input_width;
            if (this._edit_params instanceof Array) { // for compatibility with previous versions
                for (i = 0; i < this._edit_params.length; i++) {
                    field = this._field_by_ID(this._edit_params[i][0]);
                    if (field) {
                        fields.push([field.ID, '']);
                    }
                }
                this._edit_params = { 0: ['', {}, [], [['', [[{}, fields, '']]]]] };
            }

            if (this._edit_params[index] === undefined) {
                index = 0;
            }
            this.edit_options.fields = [];
            form_template = this._edit_params[index][0];
            form_options = this._edit_params[index][1];
            actions = this._edit_params[index][2];
            form_tabs = this._edit_params[index][3];

            tabs = [];
            fields = [];
            for (i = 0; i < form_tabs.length; i++) {
                tab = {}
                tab.name = form_tabs[i][0];
                tab.bands = [];
                bands = form_tabs[i][1];
                for (j = 0; j < bands.length; j++) {
                    band = {}
                    band.fields = [];
                    input_width = {}
                    band.options = bands[j][0]
                    band.options.input_width = input_width;
                    fields = bands[j][1]
                    band.name = bands[j][2]
                    for (k = 0; k < fields.length; k++) {
                        field = this._field_by_ID(fields[k][0]);
                        if (field) {
                            field_name = field.field_name;
                            band.fields.push(field_name);
                            if (fields[k][1]) {
                                input_width[field_name] = fields[k][1];
                            }
                        }
                    }
                    tab.bands.push(band);
                }
                tabs.push(tab)
            }
            form_options.edit_details = this.ids_to_item_names(form_options.edit_details);
            this.edit_options.title = this.item_caption;
            this.edit_options = $.extend(this.edit_options, form_options);
            this.edit_options.tabs = tabs;
            this._edit_options = $.extend(true, {}, this.edit_options);
        }

        init_params() {
            this._process_view_params();
            this._process_edit_params();
        }

        each(callback) {
            var value;

            if (this._active) {
                this.first();
                while (!this.eof()) {
                    value = callback.call(this, this);
                    if (value === false) {
                        break;
                    } else {
                        this.next();
                    }
                }
            }
        }

        each_field(callback) {
            var i = 0,
                len = this.fields.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.fields[i], this.fields[i], i);
                if (value === false) {
                    break;
                }
            }
        }

        each_filter(callback) {
            var i = 0,
                len = this.filters.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.filters[i], this.filters[i], i);
                if (value === false) {
                    break;
                }
            }
        }

        each_detail(callback) {
            var i = 0,
                len = this.details.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.details[i], this.details[i], i);
                if (value === false) {
                    break;
                }
            }
        }

        _field_by_name(name) {
            return this.field_by_name(name, this._fields);
        }

        field_by_name(name, fields) {
            var i = 0,
                len,
                result;
            if (fields === undefined) {
                fields = this.fields;
            }
            len = fields.length;
            for (; i < len; i++) {
                if (fields[i].field_name === name) {
                    return fields[i];
                }
            }
            return result;
        }

        _field_by_ID(ID) {
            return this.field_by_ID(ID, this._fields);
        }

        field_by_ID(ID, fields) {
            var i = 0,
                len;
            if (fields === undefined) {
                fields = this.fields;
            }
            len = fields.length;
            for (; i < len; i++) {
                if (fields[i].ID === ID) {
                    return fields[i];
                }
            }
        }

        filter_by_name(name) {
            var i = 0,
                len = this.filters.length;
            try {
                return this.filters[name];
            } catch (e) {
                for (; i < len; i++) {
                    if (this.filters[i].filter_name === name) {
                        return this.filters[i];
                    }
                }
            }
        }

        detail_by_name(name) {
            var i = 0,
                len = this.details.length;
            try {
                return this.details[name];
            } catch (e) {
                for (; i < len; i++) {
                    if (this.details[i].item_name === name) {
                        return this.details[i];
                    }
                }
            }
        }

        get dataset() {
            var i,
                len,
                result = [];
            if (this.active) {
                len = this._dataset.length;
                for (i = 0; i < len; i++)
                    result.push(this._dataset[i].slice(0, this._record_info_index))
                return result
            }
        }

        set dataset(value) {
            this._dataset = value;
        }

        get selections() {
            return this._selections;
        }

        process_selection_changed(value) {
            var added = value[0],
                deleted = value[1];
            if (added && !added.length) {
                added = undefined;
            }
            if (deleted && !deleted.length) {
                deleted = undefined;
            }
            if (this.on_selection_changed && (added || deleted)) {
                this.on_selection_changed.call(this, this, added, deleted)
            }
        }

        set selections(value) {
            var self = this;

            if (!value || !(value instanceof Array)) {
                value = undefined;
            }
            if (this._selections) {
                this.process_selection_changed([undefined, this._selections.slice(0)]);
            }
            this._selections = value;

            if (this._selections instanceof Array) {
                this._selections.add = function() {
                    var index = self._selections.indexOf(arguments[0]);
                    if (index === -1) {
                        Array.prototype.push.apply(this, arguments);
                        self.process_selection_changed([[arguments[0]], undefined]);
                    }
                }
                this._selections.push = function() {
                    Array.prototype.push.apply(this, arguments);
                    self.process_selection_changed([[arguments[0]], undefined]);
                };
                this._selections.remove = function() {
                    var index = self._selections.indexOf(arguments[0]),
                        val,
                        removed = [];
                    if (index !== -1) {
                        val = [self._selections[index]];
                        Array.prototype.splice.call(this, index, 1);
                        self.process_selection_changed([undefined, val]);
                    }
                };
                this._selections.splice = function() {
                    var deleted = self._selections.slice(arguments[0], arguments[0] + arguments[1]);
                    Array.prototype.splice.apply(this, arguments);
                    self.process_selection_changed([undefined, deleted]);
                };
                this._selections.pop = function() {
                    throw new Error('Item selections do not support pop method');
                };
                this._selections.shift = function() {
                    throw new Error('Item selections do not support shift method');
                }
                this._selections.unshift = function() {
                    throw new Error('Item selections do not support unshift method');
                }

                this.process_selection_changed([this._selections.slice(0), undefined]);
            }
            this.update_controls();
        }

        copy(options) {
            if (this.master) {
                throw new Error('A detail can not be copied.');
            }
            return this._copy(options);
        }

        _copy(options) {
            var detail_copy,
                i,
                len,
                copy,
                field,
                result,
                defaultOptions = {
                    filters: true,
                    details: true,
                    handlers: true,
                    paginate: false
                };
            result = new Item(this.owner, this.ID, this.item_name,
                this.item_caption, this.visible, this.item_type_id);
            result.master = this.master;
            result.item_type = this.item_type;
            options = $.extend({}, defaultOptions, options);
            result.ID = this.ID;
            result.item_name = this.item_name;
            result.expanded = this.expanded;
            result.field_defs = this.field_defs;
            result.filter_defs = this.filter_defs;
            result.prototype_ID = this.prototype_ID;
            result.master_field = this.master_field
            result.master_applies = this.master_applies
            result._primary_key = this._primary_key
            result._deleted_flag = this._deleted_flag
            result._master_id = this._master_id
            result._master_rec_id = this._master_rec_id
            result._edit_options = this._edit_options;
            result._view_options = this._view_options;
            result._table_options = this._table_options;
            result._virtual_table = this._virtual_table;
            result.keep_history = this.keep_history;
            result.edit_lock = this.edit_lock;
            result._view_params = this._view_params;
            result._edit_params = this._edit_params;
            result.js_filename = this.js_filename;


            len = result.field_defs.length;
            for (i = 0; i < len; i++) {
                new Field(result, result.field_defs[i]);
            }
            result._prepare_fields();
            if (options.filters) {
                len = result.filter_defs.length;
                for (i = 0; i < len; i++) {
                    new Filter(result, result.filter_defs[i]);
                }
                result._prepare_filters();
            }
            result._events = this._events;
            if (options.handlers) {
                len = this._events.length;
                for (i = 0; i < len; i++) {
                    result[this._events[i][0]] = this._events[i][1];
                }
                result.edit_options = $.extend(true, {}, this._edit_options);
                result.view_options = $.extend(true, {}, this._view_options);
                result.table_options = $.extend(true, {}, this._table_options);
            }
            else {
                result.edit_options = $.extend(true, {}, this.task.edit_options);
                result.view_options = $.extend(true, {}, this.task.view_options);
                result.table_options = $.extend(true, {}, this.task.table_options);
            }
            if (options.paginate) {
                result._paginate = this._paginate;
            }
            if (options.details) {
                this.each_detail(function(detail, i) {
                    detail_copy = detail._copy(options);
                    detail_copy.owner = result;
                    detail_copy.expanded = detail.expanded;
                    if (detail.master) {
                        detail_copy.master = result;
                    }
                    detail_copy.item_type = detail.item_type;
                    if (options.paginate) {
                        detail_copy._paginate = detail._paginate;
                    }
                    result.details.push(detail_copy);
                    result.items.push(detail_copy);
                    if (!(detail_copy.item_name in result)) {
                        result[detail_copy.item_name] = detail_copy;
                    }
                    if (!(detail_copy.item_name in result.details)) {
                        result.details[detail_copy.item_name] = detail_copy;
                    }
                });
            }
            return result;
        }

        clone(keep_filtered) {
            var result,
                i,
                len,
                field,
                new_field;
            if (keep_filtered === undefined) {
                keep_filtered = true;
            }
            result = new Item(this.owner, this.ID, this.item_name,
                this.item_caption, this.visible, this.item_type_id);
            result.master = this.master;
            result.item_type = this.item_type;
            result.ID = this.ID;
            result.item_name = this.item_name;
            result.expanded = this.expanded;

            result.field_defs = this.field_defs;
            result.filter_defs = this.filter_defs;
            result.master_field = this.master_field
            result._primary_key = this._primary_key
            result._deleted_flag = this._deleted_flag
            result._master_id = this._master_id
            result._master_rec_id = this._master_rec_id

            len = result.field_defs.length;
            for (i = 0; i < len; i++) {
                field = new Field(result, result.field_defs[i]);
            }
            result._prepare_fields();

            len = result.fields.length;
            for (i = 0; i < len; i++) {
                field = result.fields[i]
                if (result[field.field_name] !== undefined) {
                    delete result[field.field_name];
                }
            }
            result.fields = []
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                new_field = result._field_by_name(field.field_name)
                result.fields.push(new_field)
                if (result[new_field.field_name] === undefined) {
                    result[new_field.field_name] = new_field;
                }
            }

            result._update_system_fields();

            result._bind_fields(result.expanded);
            result._dataset = this._dataset;
            if (keep_filtered) {
                result.on_filter_record = this.on_filter_record;
                result.filtered = this.filtered;
            }
            result._active = true;
            result.item_state = consts.STATE_BROWSE;
            result.first();
            return result;
        }

        _copy_record_fields(source, dest) {
            dest.each_field(function(field) {
                if (source[field.field_name]) {
                    field.data = source[field.field_name].data;
                    field.lookup_data = source[field.field_name].lookup_data;
                }
            });
        }

        update_record(data, detail) {
            let self = this;
            if (data && data.ID === this.ID) {
                let source = this.copy({handlers: false, details: false}),
                    dest = this.clone(false);
                dest.log_changes = false;
                source.open({expanded: data.expanded, fields: data.fields, open_empty:true});
                source._dataset = data.dataset;
                source.first();
                dest.rec_no = this.rec_no;
                if (detail) {
                    let pks = {};
                    source.each(function(c) {
                        pks[c._primary_key_field.value] = [c.rec_no, null]
                    });
                    dest.each(function(d) {
                        if (pks[d._primary_key_field.value] !== undefined) {
                            pks[d._primary_key_field.value][1] = [d.rec_no];
                        }
                        else {
                            pks[d._primary_key_field.value] = [null, d.rec_no];
                        }
                    });
                    dest.first()
                    while (!dest.eof()) {
                        let rec_info = pks[dest._primary_key_field.value]
                        if (rec_info[0] === null) {
                            dest.delete();
                        }
                        else {
                            source.rec_no = rec_info[0];
                            self._copy_record_fields(source, dest)
                            dest.next();
                        }
                    }
                    for (let rec_info in pks) {
                        if (pks.hasOwnProperty(rec_info)) {
                            if (rec_info[1] === null) {
                                dest.append();
                                self._copy_record_fields(source, dest)
                                dest.post();
                            }
                        }
                    }
                }
                else {
                    if (source.rec_count === 1 &&
                        dest._primary_key_field.value === source._primary_key_field.value) {
                        this._copy_record_fields(source, dest)
                    }
                    else {
                        throw new Error('Can not update the record.');
                    }
                }
                this.update_controls();
                if (data.details) {
                    data.details.forEach(function(detail_data) {
                        let detail = self.item_by_ID(detail_data.ID)
                        if (detail.active) {
                            detail.update_record(detail_data, true)
                        }
                    })
                }
            }
        }

        store_handlers() {
            var result = {};
            for (var name in this) {
                if (this.hasOwnProperty(name)) {
                    if ((name.substring(0, 3) === "on_") && (typeof this[name] === "function")) {
                        result[name] = this[name];
                    }
                }
            }
            return result;
        }

        clear_handlers() {
            for (var name in this) {
                if (this.hasOwnProperty(name)) {
                    if ((name.substring(0, 3) === "on_") && (typeof this[name] === "function")) {
                        this[name] = undefined;
                    }
                }
            }
        }

        load_handlers(handlers) {
            for (var name in handlers) {
                if (handlers.hasOwnProperty(name)) {
                    this[name] = handlers[name];
                }
            }
        }

        get log_changes() {
            if (this.master) {
                return this.master.log_changes;
            } else {
                return this._log_changes
            }
        }

        set log_changes(value) {
            this._log_changes = value;
        }

        is_modified() {
            if (this.on_get_modified) {
                return this.on_get_modified.call(this, this);
            }
            else {
                return this._modified;
            }
        }

        _store_modified(result) {
            if (result === undefined) {
                result = {};
            }
            result[this.ID] = this._modified;
            if (this.master) {
                this.master._store_modified(result)
            }
            return result
        }

        _restore_modified(value) {
            this._modified = value[this.ID];
            if (this.master) {
                this.master._restore_modified(value);
            }
        }

        _set_modified(value) {
            this._modified = value;
            if (this.master && value) {
                this.master._set_modified(value);
            }
        }

        _bind_fields(expanded) {
            var j = 0;
            if (expanded === undefined) {
                expanded = true;
            }
            this.each_field(function(field, i) {
                field.bind_index = null;
                field.lookup_index = null;
            });
            this.each_field(function(field, i) {
                if (!field.master_field && !field.calculated) {
                    field.bind_index = j;
                    j += 1;
                }
            });
            this.each_field(function(field, i) {
                if (field.master_field) {
                    field.bind_index = field.master_field.bind_index;
                }
            });
            this._record_lookup_index = j
            if (expanded) {
                this.each_field(function(field, i) {
                    if (field.calculated) {
                        field.bind_index = j;
                        j += 1;
                    }
                });
                this.each_field(function(field, i) {
                    if (field.lookup_item) {
                        field.lookup_index = j;
                        j += 1;
                    }
                });
            }
            this._record_info_index = j;
        }

        set_fields(field_list) {
            this._select_field_list = field_list;
        }

        set_order_by(fields) {
            this._order_by_list = [];
            if (fields) {
                this._order_by_list = this.get_order_by_list(fields);
            }
        }

        get_order_by_list(fields) {
            var field,
                field_name,
                desc,
                fld,
                i,
                len,
                result = [];
            len = fields.length;
            for (i = 0; i < len; i++) {
                field = fields[i];
                field_name = field;
                desc = false;
                if (field[0] === '-') {
                    desc = true;
                    field_name = field.substring(1);
                }
                try {
                    fld = this.field_by_name(field_name);
                } catch (e) {
                    console.error(e);
                    throw new Error(this.item_name + ': set_order_by method argument error - ' + field + ' ' + e);
                }
                result.push([fld.field_name, desc]);
            }
            return result;
        }

        set_where(whereDef) {
            this._where_list = this.get_where_list(whereDef);
        }

        get_where_list(whereDef) {
            var field,
                field_name,
                field_arg,
                filter_type,
                filter_str,
                value,
                pos,
                result = [];
            for (field_name in whereDef) {
                if (whereDef.hasOwnProperty(field_name)) {
                    field_arg = field_name
                    value = whereDef[field_name];
                    pos = field_name.indexOf('__');
                    if (pos > -1) {
                        filter_str = field_name.substring(pos + 2);
                        field_name = field_name.substring(0, pos);
                    } else {
                        filter_str = 'eq';
                    }
                    filter_type = filter_value.indexOf(filter_str);
                    if (filter_type !== -1) {
                        filter_type += 1
                    } else {
                        throw new Error(this.item_name + ': set_where method argument error - ' + field_arg);
                    }
                    field = this._field_by_name(field_name);
                    if (!field) {
                        console.trace();
                        throw new Error(this.item_name + ': set_where method argument error - ' + field_arg);
                    }
                    if (value !== null) {
                        if (value instanceof Date) {
                            if (field.data_type === consts.DATE) {
                                value = task.format_date_to_string(value, '%Y-%m-%d')
                            }
                            else if (field.data_type === consts.DATETIME) {
                                value = task.format_date_to_string(value, '%Y-%m-%d %H:%M:%S')
                            }
                        }
                        result.push([field_name, filter_type, value, -1])
                    }
                }
            }
            return result;
        }

        _update_system_fields() {
            let self = this,
                sys_fields = ['_primary_key', '_deleted_flag', '_master_id', '_master_rec_id', '_master_field'];
            this._master_field = this.master_field;
            sys_fields.forEach(function(sys_field_name) {
                let sys_field = self[sys_field_name];
                if (sys_field) {
                    self[sys_field_name + '_field'] = self.field_by_name(sys_field);
                }
            });
        }

        _update_fields(fields) {
            var i,
                len,
                field;
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i]
                if (this[field.field_name] !== undefined) {
                    delete this[field.field_name];
                }
            }
            this.fields = [];
            if (fields === undefined && this._select_field_list.length) {
                fields = this._select_field_list;
            }
            if (fields) {
                len = fields.length;
                for (i = 0; i < len; i++) {
                    this.fields.push(this._field_by_name(fields[i]));
                }
            } else {
                this.fields = this._fields.slice(0);
            }
            fields = []
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i]
                if (this[field.field_name] === undefined) {
                    this[field.field_name] = field;
                }
                fields.push(field.field_name);
            }
            this._update_system_fields();
            return fields
        }

        _do_before_open(expanded, fields, where, order_by, open_empty, params,
            offset, limit, funcs, group_by) {
            var i,
                j,
                filters = [];

            if (this.on_before_open) {
                this.on_before_open.call(this, this, params);
            }

            params.__expanded = expanded;
            params.__fields = [];

            fields = this._update_fields(fields);
            this._select_field_list = [];

            if (fields) {
                params.__fields = fields;
            }

            params.__open_empty = open_empty;
            if (!params.__order) {
                params.__order = []
            }
            if (!params.__filters) {
                params.__filters = []
            }
            if (!open_empty) {
                params.__limit = 0;
                params.__offset = 0;
                if (limit) {
                    params.__limit = limit;
                    if (offset) {
                        params.__offset = offset;
                    }
                }
                if (where) {
                    filters = this.get_where_list(where);
                } else if (this._where_list.length) {
                    filters = this._where_list.slice(0);
                } else {
                    this.each_filter(function(filter, i) {
                        if (filter.value !== null) {
                            filters.push([filter.field.field_name, filter.filter_type, filter.value, filter.ID]);
                        }
                    });
                }
                if (params.__search !== undefined) {
                    var s = params.__search;
                    filters.push([s[0], s[2], s[1], -2]);
                }
                if (this._show_selected) {
                    filters.push([this._primary_key, consts.FILTER_IN, this.selections, -3]);
                }
                params.__filters = filters;
                if (order_by) {
                    params.__order = this.get_order_by_list(order_by);
                } else if (this._order_by_list.length) {
                    params.__order = this._order_by_list.slice(0);
                }
                this._where_list = [];
                this._order_by_list = [];
                if (funcs) {
                    params.__funcs = funcs;
                }
                if (group_by) {
                    params.__group_by = group_by;
                }
            }
            this._open_params = params;
        }

        _do_after_open(err) {
            if (this.on_after_open) {
                this.on_after_open.call(this, this, err);
            }
            this.each_detail(function(d) {
                d.update_controls();
            })
        }

        open_details() {
            var i,
                self = this,
                args = this._check_args(arguments),
                callback = args['function'],
                options = args['object'],
                async = args['boolean'],
                details = this.details,
                d,
                detail_count = 0,
                store_rec_no = function(d) {
                    if (options.master_refresh_record && d.active) {
                        d._prev_rec_no = d.rec_no
                    }
                    if (options.filters && options.filters[d.item_name]) {
                        d._where_list = options.filters[d.item_name];
                    }
                },
                restore_rec_no = function(d) {
                    if (d._prev_rec_no) {
                        d.rec_no = d._prev_rec_no
                        d._prev_rec_no = undefined;
                    }
                },
                after_open = function(d) {
                    detail_count -= 1;
                    if (detail_count === 0 && callback) {
                        callback.call(self);
                    }
                    restore_rec_no(d);
                };
            if (!options) {
                options = {};
            }

            if (options.details) {
                for (i = 0; i < options.details; i++) {
                    details.push(this.find(options.details[i]));
                }
            }

            if (callback || async) {
                for (i = 0; i < details.length; i++) {
                    detail_count += 1;
                }
                for (i = 0; i < details.length; i++) {
                    d = details[i];
                    if (!d.disabled) {
                        if (options.default_order) {
                            d.set_order_by(d.view_options.default_order);
                        }
                        store_rec_no(d);
                        d.open(after_open);
                    }
                    else {
                        after_open(d)
                    }
                }
            } else {
                for (i = 0; i < details.length; i++) {
                    d = details[i];
                    if (!d.disabled) {
                        if (options.default_order) {
                            d.set_order_by(d.view_options.default_order);
                        }
                        store_rec_no(d);
                        try {
                            d.open();
                        }
                        finally {
                            restore_rec_no(d);
                        }
                    }
                }
            }
        }

        _update_params(params, new_params) {
            var i,
                s,
                old_filters = params.__filters,
                filters = [],
                filter,
                search_filter,
                sel_filter;
            for (i = 0; i < params.__filters.length; i++) {
                filter = params.__filters[i];
                switch (filter[3]) {
                    case -1:
                        filters.push(filter)
                        break;
                    case -2:
                        search_filter = filter;
                        break;
                    case -3:
                        sel_filter = filter;
                        break;
                }
            }
            this.each_filter(function(filter, i) {
                if (filter.value !== null) {
                    filters.push([filter.field.field_name, filter.filter_type, filter.value, filter.ID]);
                }
            });
            if (new_params.hasOwnProperty('__search')) {
                s = new_params.__search;
                params.__search = new_params.__search;
                if (s !== undefined) {
                    filters.push([s[0], s[2], s[1], -2]);
                }
            }
            else if (search_filter) {
                filters.push(search_filter)
            }
            if (new_params.hasOwnProperty('__show_selected_changed')) {
                if (this._show_selected) {
                    filters.push([this._primary_key, consts.FILTER_IN, this.selections, -3]);
                }
            }
            else if (sel_filter) {
                filters.push(sel_filter);
            }

            params.__filters = filters;
            return params;
        }

        _check_open_options(options) {
            if (options) {
                if (options.fields && !$.isArray(options.fields)) {
                    throw new Error(this.item_name + ': open method options error: the fields option must be an array.');
                }
                if (options.order_by && !$.isArray(options.order_by)) {
                    throw new Error(this.item_name + ': open method options error: the order_by option must be an array.');
                }
                if (options.group_by && !$.isArray(options.group_by)) {
                    throw new Error(this.item_name + ': open method options error: the group_by option must be an array.');
                }
            }
        }

        open() {
            var args = this._check_args(arguments),
                callback = args['function'],
                options = args['object'],
                async = args['boolean'],
                expanded,
                fields,
                where,
                order_by,
                open_empty,
                funcs,
                group_by,
                params,
                callback,
                log,
                limit,
                offset,
                field_name,
                self = this;
            this._check_open_options(options);
            if (options) {
                expanded = options.expanded;
                fields = options.fields;
                where = options.where;
                order_by = options.order_by;
                open_empty = options.open_empty;
                params = options.params;
                offset = options.offset;
                limit = options.limit;
                funcs = options.funcs;
                group_by = options.group_by;
            }
            if (!params) {
                params = {};
            }
            if (this.virtual_table) {
                open_empty = true;
            }
            if (expanded === undefined) {
                expanded = this.expanded;
            } else {
                this.expanded = expanded;
            }
            if (!async) {
                async = callback ? true : false;
            }
            if (this.master_field) {
                if (this.owner.rec_count && !this.owner.is_new()) {
                    params.__master_field = this.owner._primary_key_field.value;
                }
                else {
                    open_empty = true;
                }
            }
            if (this.master) {
                if (!this.disabled && this.master.record_count() > 0) {
                    let dataset;
                    params.__master_id = null
                    if (this._master_id) {
                        params.__master_id = this.master.ID;
                    }
                    params.__master_rec_id = this.master.field_by_name(this.master._primary_key).value;
                    if (this.master.is_new()) {
                        dataset = [];
                        this.change_log = new ChangeLog(this);
                    } else {
                        let change_log = this.master.change_log.detail_change_log(this);
                        if (change_log && !change_log.empty) {
                            this.change_log = change_log;
                            dataset = this.change_log.dataset;
                            fields = this.change_log.fields;
                        }
                    }
                    if (dataset !== undefined) {
                        this._do_before_open(expanded, fields,
                            where, order_by, open_empty, params, offset,
                            limit, funcs, group_by)
                        this._bind_fields(expanded);
                        this._dataset = dataset;
                        this.change_log.dataset = dataset;
                        this._active = true;
                        this.item_state = consts.STATE_BROWSE;
                        this.first();
                        this._do_after_open();
                        this.update_controls(consts.UPDATE_OPEN);
                        if (callback) {
                            callback.call(this, this);
                        }
                        return;
                    }
                } else {
                    this.close();
                    this.update_controls(consts.UPDATE_OPEN);
                    return;
                }
            }

            if (this._paginate && offset !== undefined) {
                params = this._update_params(this._open_params, params);
                params.__offset = offset;
                if (this.on_before_open) {
                    this.on_before_open.call(this, this, params);
                }
                this._open_params = params;
            } else {
                if (offset === undefined) {
                    offset = 0;
                }
                this._do_before_open(expanded, fields,
                    where, order_by, open_empty, params, offset, limit, funcs, group_by);
                this._bind_fields(expanded);
            }
            if (this._paginate) {
                params.__limit = this._limit;
            }
            this._dataset = [];
            this._do_open(offset, async, params, open_empty, callback);
        }

        _do_open(offset, async, params, open_empty, callback) {
            var self = this,
                i,
                filters,
                data;
            params = $.extend(true, {}, params);
            for (i = 0; i < params.__filters.length; i++) {
                params.__filters[i].length = 3;
            }
            if (this.on_open && !open_empty) {
                if (this.on_open) {
                    this.on_open.call(this, this, params, function(data) {
                        self._do_after_load(data, offset, params, callback);
                    });
                }
            }
            else if (async && !open_empty) {
                this.send_request('open', params, function(data) {
                    self._do_after_load(data, offset, params, callback);
                });
            } else {
                if (open_empty) {
                    data = [
                        [], ''
                    ];
                } else {
                    data = this.send_request('open', params);
                }
                this._do_after_load(data, offset, params, callback);
            }
        }

        _do_after_load(data, offset, params, callback) {
            var rows,
                error_mes,
                i,
                len;
            if (data) {
                error_mes = data[1];
                if (error_mes) {
                    this.alert_error(error_mes)
                } else {
                    if (data[0]) {
                        rows = data[0];
                        len = rows.length;
                        this._dataset = rows;
                        this.change_log = new ChangeLog(this);
                        if (this._limit && this._paginate && rows) {
                            this._offset = offset;
                            this.is_loaded = false;
                        }
                        if (len < this._limit) {
                            this.is_loaded = true;
                        }
                        this._active = true;
                        this.item_state = consts.STATE_BROWSE;
                        this._cur_row = null;
                        this.first();
                        this._do_after_open(error_mes);
                        if (!this._paginate || this._paginate && offset === 0) {
                            if (this.on_filters_applied) {
                                this.on_filters_applied.call(this, this);
                            }
                            if (this._on_filters_applied_internal) {
                                this._on_filters_applied_internal.call(this, this);
                            }
                        }
                        this.update_controls(consts.UPDATE_OPEN);
                        if (callback) {
                            callback.call(this, this);
                        }
                    }
                }
            } else {
                this._dataset = [];
                console.log(this.item_name + " error while opening table");
            }
        }

        _do_on_refresh_page(rec_no, callback) {
            if (rec_no !== null) {
                this.rec_no = rec_no;
            }
            if (callback) {
                callback.call(this);
            }
        }

        refresh_page(call_back) {
            var args = this._check_args(arguments),
                callback = args['function'],
                async = args['boolean'],
                self = this,
                rec_no = this.rec_no;
            if (!this.master) {
                if (callback || async) {
                    this.reopen(this._open_params.__offset, {}, function() {
                        self._do_on_refresh_page(rec_no, callback);
                    });
                }
                else {
                    this.reopen(this._open_params.__offset, {});
                    this._do_on_refresh_page(rec_no, callback);
                }
            }
        }

        reopen(offset, params, callback) {
            var options = {};
            if (this.paginate) {
                this.open({offset: offset, params: params}, callback);
            }
            else {
                options.params = params;
                params = this._update_params(this._open_params, params);
                this._where_list = this._open_params.__filters;
                this._order_by_list = this._open_params.__order;
                options.expanded = this._open_params.__expanded;
                options.open_empty = this._open_params.__open_empty;
                options.offset = this._open_params.__offset;
                options.limit = this._open_params.__limit;
                this.open(options, callback);
            }
        }

        _do_close() {
            this._dataset = null;
            this._cur_row = null;
            this._active = false;
            this.each_detail(function(d) {
                d._do_close();
            });
        }

        close() {
            this._do_close();
            this.update_controls(consts.UPDATE_CLOSE);
        }

        sort(field_list) {
            var list = this.get_order_by_list(field_list)
            this._sort(list);
        }

        _sort(sort_fields) {
            var i,
                field_names = [],
                desc = [];
            for (i = 0; i < sort_fields.length; i++) {
                field_names.push(this.field_by_name(sort_fields[i][0]).field_name);
                desc.push(sort_fields[i][1]);
            }
            this._sort_dataset(field_names, desc);
        }

        _sort_dataset(field_names, desc) {
            var self = this,
                i,
                field_name,
                field;

            function convert_value(value, data_type) {
                if (value === null) {
                    if (data_type === consts.TEXT) {
                        value = ''
                    } else if (data_type === consts.INTEGER || data_type === consts.FLOAT || data_type === consts.CURRENCY) {
                        value = 0;
                    } else if (data_type === consts.DATE || data_type === consts.DATETIME) {
                        value = '';
                    } else if (data_type === consts.BOOLEAN) {
                        value = false;
                    }
                }
                if (data_type === consts.FLOAT) {
                    value = Number(value.toFixed(10));
                }
                if (data_type === consts.CURRENCY) {
                    value = Number(value.toFixed(2));
                }
                return value;
            }

            function compare_records(rec1, rec2) {
                var i,
                    field,
                    data_type,
                    index,
                    result,
                    val1,
                    val2;
                for (var i = 0; i < field_names.length; i++) {
                    field = self.field_by_name(field_names[i]);
                    index = field.bind_index;
                    if (field.lookup_item) {
                        index = field.lookup_index;
                    }
                    data_type = field.lookup_data_type;
                    val1 = convert_value(rec1[index], data_type);
                    val2 = convert_value(rec2[index], data_type);
                    if (val1 < val2) {
                        result = -1;
                    }
                    if (val1 > val2) {
                        result = 1;
                    }
                    if (result) {
                        if (desc[i]) {
                            result = -result;
                        }
                        return result;
                    }
                }
                return 0;
            }

            this._dataset.sort(compare_records);
            this._do_after_scroll();
            this.update_controls();
        }

        search() {
            var args = this._check_args(arguments),
                callback = args['function'],
                paginating = args['boolean'],
                field_name = arguments[0],
                text = arguments[1].trim(),
                search_text = text,
                filter,
                field,
                filter,
                filter_type,
                i, j,
                index,
                ids,
                substr,
                str,
                found,
                lookup_values,
                params = {};
            if (arguments.length > 2 && typeof arguments[2] === "string") {
                filter = arguments[2];
                filter_type = filter_value.indexOf(filter) + 1;
            }
            else {
                filter_type = consts.FILTER_CONTAINS_ALL;
            }
            field = this.field_by_name(field_name);
            if (field) {
                if (text && field.lookup_values) {
                    lookup_values = this.field_by_name(field_name).lookup_values;
                    ids = [];
                    if (text.length) {
                        for (i = 0; i < lookup_values.length; i++) {
                            str = lookup_values[i][1].toLowerCase();
                            substr = text.toLowerCase().split(' ');
                            found = true;
                            for (j = 0; j < substr.length; j++) {
                                if (substr[j]) {
                                    if (str.indexOf(substr[j]) === -1) {
                                        found = false;
                                        break;
                                    }
                                }
                            }
                            if (found) {
                                ids.push(lookup_values[i][0])
                            }
                        }
                    }
                    if (!ids.length) {
                        ids.push(-1);
                    }
                    text = ids;
                    filter_type = consts.FILTER_IN;
                }
                else if (field.numeric_field() && (
                    filter_type === consts.FILTER_CONTAINS ||
                    filter_type === consts.FILTER_STARTWITH ||
                    filter_type === consts.FILTER_ENDWITH ||
                    filter_type === consts.FILTER_CONTAINS_ALL)) {
                    text = text.replace(locale.DECIMAL_POINT, ".");
                    text = text.replace(locale.MON_DECIMAL_POINT, ".");
                    if (text && isNaN(text)) {
                        this.alert_error(language.invalid_value.replace('%s', ''));
                        throw new Error(language.invalid_value.replace('%s', ''));
                    }
                }
                params.__search = undefined;
                if (text.length) {
                    params.__search = [field_name, text, filter_type, search_text];
                }
                if (paginating) {
                    this.reopen(0, params, callback);
                }
                else {
                    this.open({params: params}, callback);
                }
                return [field_name, text, filter_value[filter_type - 1]];
            }
        }

        new_record() {
            var result = [];
            this.each_field(function(field, i) {
                if (!field.master_field) {
                    result.push(null);
                }
            });
            if (this.expanded) {
                this.each_field(function(field, i) {
                    if (field.lookup_item) {
                        result.push(null);
                    }
                });
            }
            return result;
        }

        append(index) {
            this._edit_masters();
            this._append(index);
        }

        _append(index) {
            if (!this._active) {
                throw new Error(language.append_not_active.replace('%s', this.item_name));
            }
            if (this._applying) {
                throw new Error('Can not perform this operation. Item is applying data to the database');
            }
            if (this.master && !this.master.is_changing()) {
                throw new Error(language.append_master_not_changing.replace('%s', this.item_name));
            }
            if (this.item_state !== consts.STATE_BROWSE) {
                throw new Error(language.append_not_browse.replace('%s', this.item_name));
            }
            if (this.on_before_append) {
                this.on_before_append.call(this, this);
            }
            this._do_before_scroll();
            this.item_state = consts.STATE_INSERT;
            if (index === 0) {
                this._dataset.splice(0, 0, this.new_record());
            }
            else {
                this._dataset.push(this.new_record());
                index = this._dataset.length - 1;
            }
            this.skip(index, false);
            this._do_after_scroll();
            this.record_status = consts.RECORD_INSERTED;
            if (this.master_field) {
                this._master_field_field.data = this.owner._primary_key_field.value;
            }
            for (var i = 0; i < this.fields.length; i++) {
                if (this.fields[i].default_value !== undefined) {
                    this.fields[i].assign_default_value();
                }
            }
            this._modified = false;
            if (this.on_after_append) {
                this.on_after_append.call(this, this);
            }
            this.update_controls();
        }

        insert() {
            this.append(0);
        }

        _do_before_edit() {
            if (this.on_before_edit) {
                this.on_before_edit.call(this, this);
            }
        }

        _do_after_edit() {
            if (this.on_after_edit) {
                this.on_after_edit.call(this, this);
            }
        }

        _edit_masters() {
            if (this.master) {
                this.master._edit_masters();
                if (!this.master.is_changing()) {
                    this.master._edit();
                }
            }
        }

        edit() {
            this._edit_masters();
            this._edit();
        }

        _edit() {
            if (this.item_state === consts.STATE_EDIT) {
                return
            }
            if (!this._active) {
                throw new Error(language.edit_not_active.replace('%s', this.item_name));
            }
            if (this._applying) {
                throw new Error('Can not perform this operation. Item is applying data to the database');
            }
            if (this.record_count() === 0) {
                throw new Error(language.edit_no_records.replace('%s', this.item_name));
            }
            if (this.master && !this.master.is_changing()) {
                throw new Error(language.edit_master_not_changing.replace('%s', this.item_name));
            }
            if (this.item_state !== consts.STATE_BROWSE) {
                throw new Error(language.edit_not_browse.replace('%s', this.item_name));
            }
            this._do_before_edit();
            this._buffer = this.change_log.store_record();
            this._modified_buffer = this._store_modified()
            this.item_state = consts.STATE_EDIT;
            this._do_after_edit();
        }

        cancel() {
            var i,
                len,
                modified = this._modified,
                self = this,
                prev_state;
            if (this.on_before_cancel) {
                this.on_before_cancel.call(this, this);
            }
            this._canceling = true;
            try {
                if (this.item_state === consts.STATE_EDIT) {
                    this.change_log.restore_record(this._buffer)
                    this.update_controls();
                    for (var i = 0; i < this.details.length; i++) {
                        this.details[i].update_controls(consts.UPDATE_OPEN);
                    }
                } else if (this.item_state === consts.STATE_INSERT) {
                    this.change_log.record_status = consts.RECORD_UNCHANGED;
                    this._dataset.splice(this.rec_no, 1);
                } else {
                    throw new Error(language.cancel_invalid_state.replace('%s', this.item_name));
                }

                prev_state = this.item_state;
                this.item_state = consts.STATE_BROWSE;
                this.skip(this._old_row, false);
                if (prev_state === consts.STATE_EDIT) {
                    this._restore_modified(this._modified_buffer);
                }
                else if (prev_state === consts.STATE_INSERT) {
                    this.modified = false;
                    this._do_after_scroll();
                }
                if (this.on_after_cancel) {
                    this.on_after_cancel.call(this, this);
                }
                if (modified && this.details.length) {
                    this.each_detail(function(d) {
                        self._detail_changed(d);
                    });
                }
                this.update_controls();
            }
            finally {
                this._canceling = false;
            }
        }

        delete() {
            var rec = this.rec_no;
            if (!this._active) {
                throw new Error(language.delete_not_active.replace('%s', this.item_name));
            }
            if (this._applying) {
                throw new Error('Can not perform this operation. Item is applying data to the database');
            }
            if (this.record_count() === 0) {
                throw new Error(language.delete_no_records.replace('%s', this.item_name));
            }
            if (this.master && !this.master.is_changing()) {
                throw new Error(language.delete_master_not_changing.replace('%s', this.item_name));
            }
            try {
                if (this.on_before_delete) {
                    this.on_before_delete.call(this, this);
                }
                this._do_before_scroll();
                this.item_state = consts.STATE_DELETE;
                this.change_log.log_change();
                if (this.master) {
                    this.master._set_modified(true);
                }
                this._dataset.splice(rec, 1);
                this.skip(rec, false);
                this.item_state = consts.STATE_BROWSE;
                this._do_after_scroll();
                if (this.on_after_delete) {
                    this.on_after_delete.call(this, this);
                }
                if (this.master || this.master_field) {
                    this.owner._detail_changed(this, true);
                }
            } catch (e) {
                console.error(e);
                throw new Error(e);
            } finally {
                this.item_state = consts.STATE_BROWSE;
            }
            this.update_controls();
        }

        is_browsing() {
            return this.item_state === consts.STATE_BROWSE;
        }

        is_changing() {
            return (this.item_state === consts.STATE_INSERT) || (this.item_state === consts.STATE_EDIT);
        }

        is_new() {
            return this.item_state === consts.STATE_INSERT;
        }

        is_edited() {
            return this.item_state === consts.STATE_EDIT;
        }

        is_deleting() {
            return this.item_state === consts.STATE_DELETE;
        }

        detail_by_ID(ID) {
            var result;
            if (typeof ID === "string") {
                ID = parseInt(ID, 10);
            }
            this.each_detail(function(detail, i) {
                if (detail.ID === ID) {
                    result = detail;
                    return false;
                }
            });
            return result;
        }

        post(callback) {
            var data,
                i,
                len,
                old_state = this.item_state,
                was_modified = this._modified;

            if (!this.is_changing()) {
                throw new Error(this.item_name + ' post method: dataset is not in edit or insert mode');
            }
            this.check_record_valid();
            if (this.on_before_post) {
                this.on_before_post.call(this, this);
            }
            if (this.master && this._master_id) {
                this.field_by_name(this._master_id).data = this.master.ID;
            }
            len = this.details.length;
            for (i = 0; i < len; i++) {
                if (this.details[i].is_changing()) {
                    this.details[i].post();
                }
            }
            if (this.is_modified() || this.is_new()) {
                this.change_log.log_change();
            }
            this._modified = false;
            this.item_state = consts.STATE_BROWSE;
            if (this.on_after_post) {
                this.on_after_post.call(this, this);
            }
            if (!this._valid_record()) {
                this._search_record(this.rec_no, 0);
                this.update_controls(consts.UPDATE_CONTROLS);
            }
            if ((this.master || this.master_field) && was_modified) {
                this.owner._detail_changed(this, true);
            }
        }

        apply() {
            let args = this._check_args(arguments),
                callback = args['function'],
                params = args['object'],
                async = args['boolean'],
                self = this,
                changes = {},
                result,
                data;
            if (this.master) {
                if(this.master_applies || this.virtual_table || this._applying) {
                    if (callback) {
                        callback.call(this);
                    }
                    return;
                }
                let item = this;
                while (item.master) {
                    if (item.is_changing()) {
                        item.post();
                    }
                    item = item.master;
                }
                item.apply();
                //~ return;
            }
            if (this.is_changing()) {
                this.post();
            }
            if (this.change_log && this.change_log.get_changes(changes)) {
                params = $.extend({}, params);
                if (this.on_before_apply) {
                    this.on_before_apply.call(this, this, params);
                }
                this._applying = true;
                if (callback || async) {
                    this.send_request('apply', [changes, params], function(data) {
                        self._process_apply(data, params, callback);
                    });
                } else {
                    data = this.send_request('apply', [changes, params]);
                    result = this._process_apply(data, params);
                }
            }
            else if (callback) {
                if (callback) {
                    callback.call(this);
                }
            }
            return result;
        }

        _process_apply(response, params, callback) {
            this._applying = false;
            if (response) {
                let data = response[0],
                    error = response[1];
                if (error) {
                    if (callback) {
                        callback.call(this, error);
                    }
                    throw new Error(error);
                }
                else {
                    this.change_log.update(data);
                    if (this.on_after_apply) {
                        this.on_after_apply.call(this, this);
                    }
                    if (callback) {
                        callback.call(this);
                    }
                    this.update_controls(consts.UPDATE_APPLIED);
                    return data;
                }
            }
        }

        field_by_id(id_value, fields, callback) {
            var copy,
                values,
                result;
            if (typeof fields === 'string') {
                fields = [fields];
            }
            copy = this.copy();
            copy.set_where({
                id: id_value
            });
            if (callback) {
                copy.open({
                    expanded: false,
                    fields: fields
                }, function() {
                    values = copy._dataset[0];
                    if (fields.length === 1) {
                        values = values[0];
                    }
                    return values
                });
            } else {
                copy.open({
                    expanded: false,
                    fields: fields
                });
                if (copy.record_count() === 1) {
                    values = copy._dataset[0];
                    if (fields.length === 1) {
                        values = values[0];
                    }
                    return values
                }
            }
        }

        locate(fields, values) {
            var clone = this.clone();

            function record_found() {
                var i,
                    len;
                if (fields instanceof Array) {
                    len = fields.length;
                    for (i = 0; i < len; i++) {
                        if (clone.field_by_name(fields[i]).value !== values[i]) {
                            return false;
                        }
                    }
                    return true;
                } else {
                    if (clone.field_by_name(fields).value === values) {
                        return true;
                    }
                }
            }

            clone.first();
            while (!clone.eof()) {
                if (record_found()) {
                    this.rec_no = clone.rec_no;
                    return true;
                }
                clone.next();
            }
        }

        get active() {
            return this._active;
        }

        get virtual_table() {
            return this._virtual_table;
        }

        get paginate() {
            return this._paginate
        }

        set paginate(value) {
            this._paginate = value;
        }

        set read_only(value) {
            var self = this;
            this._read_only = value;
            this.each_field(function(field) {
                field.update_controls();
            });
            this.each_detail(function(detail) {
                detail.update_controls();
            });
        }

        get read_only() {
            if ((this.master || this.master_field) && this.owner.owner_read_only) {
                return this.owner.read_only;
            } else {
                return this._read_only;
            }
        }

        get can_modify() {
            var result = this._can_modify;
            if (this.master && !this.master._can_modify) {
                result = false;
            }
            return result;
        }

        set can_modify(value) {
            this._can_modify = value;
        }

        get filtered() {
            return this._filtered;
        }

        set filtered(value) {
            if (value) {
                if (!this.on_filter_record) {
                    value = false;
                }
            }
            if (this._filtered !== value) {
                this._filtered = value;
                this.first();
                this.update_controls(consts.UPDATE_OPEN);
            }
        }

        clear_filters() {
            this.each_filter(function(filter) {
                filter.value = null;
            })
        }

        assign_filters(item) {
            var self = this;
            item.each_filter(function(f) {
                if (f.value === null) {
                    self.filter_by_name(f.filter_name).field.value = null;
                } else {
                    self.filter_by_name(f.filter_name).field.value = f.field.value;
                }
            });
        }

        set item_state(value) {
            if (this._state !== value) {
                this._state = value;
                if (this.on_state_changed) {
                    this.on_state_changed.call(this, this);
                }
                this.update_controls(consts.UPDATE_STATE);
            }
        }

        get item_state() {
            return this._state;
        }

        _do_after_scroll() {
            var len = this.details.length,
                detail;
            for (var i = 0; i < len; i++) {
                this.details[i]._do_close();
            }
            this.update_controls(consts.UPDATE_SCROLLED);
            if (this.on_after_scroll) {
                this.on_after_scroll.call(this, this);
            }
            if (this._on_after_scroll_internal) {
                this._on_after_scroll_internal.call(this, this);
            }
        }

        _do_before_scroll() {
            if (this.is_changing()) {
                this.post();
            }
            if (this.on_before_scroll) {
                this.on_before_scroll.call(this, this);
            }
            if (this._on_before_scroll_internal) {
                this._on_before_scroll_internal.call(this, this);
            }
        }

        skip(value, trigger_events) {
            var eof,
                bof,
                old_row,
                new_row;
            if (trigger_events === undefined) {
                trigger_events = true;
            }
            if (this.record_count() === 0) {
                if (trigger_events) this._do_before_scroll();
                this._cur_row = null;
                this._eof = true;
                this._bof = true;
                if (trigger_events) this._do_after_scroll();
            } else {
                old_row = this._cur_row;
                eof = false;
                bof = false;
                new_row = value;
                if (new_row < 0) {
                    new_row = 0;
                    bof = true;
                }
                if (new_row >= this._dataset.length) {
                    new_row = this._dataset.length - 1;
                    eof = true;
                }
                this._eof = eof;
                this._bof = bof;
                if (old_row !== new_row) {
                    if (trigger_events) this._do_before_scroll();
                    this._cur_row = new_row;
                    if (trigger_events) this._do_after_scroll();
                }
            }
            this._old_row = this._cur_row;
        }

        set rec_no(value) {
            if (this._active) {
                if (this.filter_active()) {
                    this._search_record(value, 0);
                } else {
                    this.skip(value);
                }
            }
        }

        get rec_no() {
            return this._cur_row;
        }

        filter_active() {
            if (this.on_filter_record && this.filtered) {
                return true;
            }
        }

        first() {
            if (this.filter_active()) {
                this.find_first();
            } else {
                this.rec_no = 0;
            }
        }

        last() {
            if (this.filter_active()) {
                this.find_last();
            } else {
                this.rec_no = this._dataset.length - 1;
            }
        }

        next() {
            if (this.filter_active()) {
                this.find_next();
            } else {
                this.rec_no = this.rec_no + 1;
            }
        }

        prior() {
            if (this.filter_active()) {
                this.find_prior();
            } else {
                this.rec_no = this.rec_no - 1;
            }
        }

        eof() {
            if (this.active) {
                return this._eof;
            }
            else {
                return true;
            }
        }

        bof() {
            if (this.active) {
                return this._bof;
            }
            else {
                return true;
            }
        }

        _valid_record() {
            if (this.on_filter_record && this.filtered) {
                return this.on_filter_record.call(this, this);
            } else {
                return true;
            }
        }

        _search_record(start, direction) {
            var row,
                cur_row,
                found,
                self = this;
            if (direction === undefined) {
                direction = 1;
            }

            function update_position() {
                if (self.record_count() === 0) {
                    self._eof = true;
                    self._bof = true;
                } else {
                    self._eof = false;
                    self._bof = false;
                    if (self._cur_row < 0) {
                        self._cur_row = 0;
                        self._bof = true;
                    }
                    if (self._cur_row >= self._dataset.length) {
                        self._cur_row = self._dataset.length - 1;
                        self._eof = true;
                    }
                }
            }

            function check_record() {
                if (direction === 1) {
                    return self.eof();
                } else {
                    return self.bof();
                }
            }

            if (this.active) {
                if (this.record_count() === 0) {
                    this.skip(start);
                    return;
                }
                cur_row = this._cur_row;
                this._cur_row = start + direction;
                update_position();
                if (direction === 0) {
                    if (this._valid_record()) {
                        this._cur_row = cur_row;
                        this.skip(start);
                        return
                    }
                    direction = 1;
                }
                while (!check_record()) {
                    if (this._valid_record()) {
                        if (start !== this._cur_row) {
                            row = this._cur_row;
                            this._cur_row = start;
                            this.skip(row);
                            found = true;
                            break
                        }
                    } else {
                        this._cur_row = this._cur_row + direction;
                        update_position();
                    }
                }
                if (!found) {
                    this._cur_row = cur_row;
                }
            }
        }

        find_first() {
            this._search_record(-1, 1);
        }

        find_last() {
            this._search_record(this._dataset.length, -1);
        }

        find_next() {
            this._search_record(this.rec_no, 1);
        }

        find_prior() {
            this._search_record(this.rec_no, -1);
        }

        _count_filtered() {
            var clone = this.clone(true),
                result = 0;
            clone.each(function() {
                result += 1;
            })
            return result;
        }

        get rec_count() {
            if (this._dataset) {
                if (this.filtered) {
                    return this._count_filtered();
                }
                else {
                    return this._dataset.length;
                }
            } else {
                return 0;
            }
        }

        record_count() {
            if (this._dataset) {
                return this._dataset.length;
            } else {
                return 0;
            }
        }

        //~ get record_info() {
            //~ return this.get_record_info()
        //~ }

        //~ get_record_info(record) {
            //~ if (this._record_info_index >= 0) {
                //~ if (!record) {
                    //~ record = this._dataset[this.rec_no];
                //~ }
                //~ if (record.length < this._record_info_index + 1) {
                    //~ record.push([null, null]);
                //~ }
                //~ return record[this._record_info_index];
            //~ }
        //~ }

        //~ get record_status() {
            //~ return this.record_info[consts.REC_STATUS];
        //~ }

        //~ set record_status(value) {
            //~ if (this.log_changes) {
                //~ this.record_info[consts.REC_STATUS] = value;
            //~ }
        //~ }

        //~ get record_log_rec() {
            //~ return this.record_info[consts.REC_LOG_REC];
        //~ }

        //~ set record_log_rec(value) {
            //~ this.record_info[consts.REC_LOG_REC] = value;
        //~ }

        //~ rec_unchanged() {
            //~ return this.record_status === consts.RECORD_UNCHANGED;
        //~ }

        //~ rec_inserted() {
            //~ return this.record_status === consts.RECORD_INSERTED;
        //~ }

        //~ rec_deleted() {
            //~ return this.record_status === consts.RECORD_DELETED;
        //~ }

        //~ rec_modified() {
            //~ return this.record_status === consts.RECORD_MODIFIED ||
                //~ this.record_status === consts.RECORD_DETAILS_MODIFIED;
        //~ }

        get _record_copy() {
            let self = this,
                fields = {},
                details = {},
                result = {record: fields, details: details};
            this.each_field(function(f) {
                if (!f.system_field()) {
                    let field = self.field_by_name(f.field_name);
                    fields[f.field_name] = [field.data, field.lookup_data]
                }
            });
            this.each_detail(function(d) {
                let records = [],
                    clone = d.clone();
                details[d.ID] = records;
                clone.each(function(c) {
                    records.push(c._record_copy);
                });
            });
            return result;
        }

        set _record_copy(copy) {
            let self = this,
                handlers = this.store_handlers();
            try {
                this.clear_handlers();
                this.each_field(function(f) {
                    let vals = copy.record[f.field_name];
                    if (vals) {
                        f.data = vals[0];
                        f.lookup_data = vals[1];
                    }
                });
                this.each_detail(function(d) {
                    let records = copy.details[d.ID],
                        handlers = d.store_handlers();
                    d.clear_handlers();
                    d.disable_controls();
                    try {
                        records.forEach(function(record) {
                            if (!d.active) {
                                d.open();
                            }
                            d.append();
                            d._record_copy = record;
                            d.post();
                        });
                        d.first();
                    }
                    finally {
                        d.enable_controls();
                        d.load_handlers(handlers);
                    }
                })
            }
            finally {
                this.load_handlers(handlers);
            }
        }

        copy_record() {
            let args = this._check_args(arguments),
                options = args['object'],
                container = args['jquery'],
                on_detail_changed = this.on_detail_changed,
                on_after_scroll_internal = this._on_after_scroll_internal;
            options = $.extend({}, options);
            options.rec_copy = this._record_copy;
            this.on_detail_changed = function() {};
            this._on_after_scroll_internal = undefined;
            try {
                this.insert_record(container, options);
            }
            finally {
                this._on_after_scroll_internal = on_after_scroll_internal;
                this.on_detail_changed = on_detail_changed;
            }
        }

        insert_record() {
            let args = this._check_args(arguments),
                options = args['object'],
                container = args['jquery'];
            this._do_append_record(container, options, 0);
        }

        append_record() {
            let args = this._check_args(arguments),
                options = args['object'],
                container = args['jquery'];
            this._do_append_record(container, options);
        }


        _do_append_record(container, options, index) {
            container = this._check_container(container);
            if (container && this.task.can_add_tab(container) && $('.modal').length === 0) {
                this._append_record_in_tab(container, options);
            }
            else {
                this._append_record(container, options, index);
            }
        }

        _append_record(container, options, index) {
            if (this.can_create()) {
                options = $.extend({}, options);
                this.append(index);
                if (options.rec_copy) {
                    this._record_copy = options.rec_copy;
                    if (options.after_record_copied) {
                        options.after_record_copied.call(this, this);
                    }
                }
                else {
                    this.open_details({details: this.edit_options.edit_details});
                }
                this.create_edit_form(container);
            }
        }

        _append_record_in_tab(container, options) {
            var tab_id = this.item_name + 0,
                tab,
                tab_name,
                self = this,
                copy = this.copy(),
                content;
            options = $.extend({}, options);
            if (options) {
                tab_name = options.tab_name;
            }
            container = this._check_container(container);
            if (this.can_create()) {
                if (!tab_name) {
                    tab_name = '<i class="icon-plus-sign"></i> ' + this.item_caption;
                }
                content = task.add_tab(container, tab_name,
                    {
                        tab_id: tab_id,
                        insert_after_cur_tab: true,
                        show_close_btn: true,
                        set_active: true,
                        on_close: function() {
                            task.show_tab(container, tab_id);
                            copy.close_edit_form();
                        }
                    });
                if (content) {
                    copy._source_item = this;
                    copy._tab_info = {container: container, tab_id: tab_id}
                    copy.open({open_empty: true}, function() {
                        let on_after_apply = copy.on_after_apply;
                        this.edit_options.edit_details
                        copy.edit_options.tab_id = tab_id;
                        copy._append_record(content, options);
                        copy.on_after_apply = function(item) {
                            if (on_after_apply) {
                                on_after_apply(copy, copy);
                            }
                            self.refresh_page(true);
                        }
                    });
                }
            }
        }

        _check_container(container) {
            if (container && container.length) {
                return container;
            }
            else if (!container && this.edit_options.modeless &&
                this.task.forms_in_tabs && this.task.forms_container) {
                return this.task.forms_container;
            }
        }

        edit_record(container, options) {
            if (this.rec_count) {
                container = this._check_container(container);
                if ($('.modal').length === 0 && container && this.task.can_add_tab(container)) {
                    this._edit_record_in_tab(container, options)
                }
                else {
                    this._edit_record()
                }
            }
        }

        _edit_record(container, in_tab) {
            var self = this,
                options = {},
                create_form = function() {
                    if (self.can_edit() && !self.is_changing()) {
                        self.edit();
                    }
                    self.create_edit_form(container);
                };
            if (this.master) {
                create_form();
            }
            else {
                options.details = this.edit_options.edit_details;
                options.default_order = true;
                if (!in_tab) {
                    if (this.log_changes) {
                        this.refresh_record(options, function(error) {
                            create_form()
                        });
                    }
                    else (
                        create_form()
                    )
                }
                else if (this.edit_options.edit_details.length) {
                    options.filters = this.edit_options.edit_detail_filters;
                    this.open_details(options, function(error) {
                        create_form()
                    });
                }
                else {
                    create_form();
                }
            }
        }

        _edit_record_in_tab(container, options) {
            var pk = this._primary_key,
                pk_value = this.field_by_name(pk).value,
                where = {},
                params = {},
                tab_name,
                tab_id = this.item_name + pk_value,
                tab,
                self = this,
                copy = this.copy(),
                content;
            options = $.extend({}, options);
            if (options) {
                tab_name = options.tab_name;
            }
            if (!tab_name) {
                tab_name = '<i class="icon-edit"></i> ' + this.item_caption;
            }
            content = task.add_tab(container, tab_name,
            {
                tab_id: tab_id,
                insert_after_cur_tab: true,
                show_close_btn: true,
                set_active: true,
                on_close: function() {
                    task.show_tab(container, tab_id);
                    copy.close_edit_form();
                }
            });
            if (content) {
                copy._source_item = this;
                copy._read_only = this._read_only;
                copy.owner_read_only = this.owner_read_only;
                copy.each_field(function(f) {
                    f._read_only = self.field_by_name(f.field_name)._read_only;
                });
                copy._tab_info = {container: container, tab_id: tab_id}
                copy.can_modify = this.can_modify;
                where[pk] = pk_value;
                copy.set_where(where);
                copy.edit_options.edit_detail_filters = {};
                this.each_detail(function(d) {
                    if (d._open_params.__filters) {
                        copy.edit_options.edit_detail_filters[d.item_name] = d._open_params.__filters.slice();
                    }
                });
                copy.open({params: params}, function() {
                    var on_after_apply = copy.on_after_apply;
                    copy.edit_options.tab_id = tab_id;
                    copy._edit_record(content, true);
                    copy.on_after_apply = function(item) {
                        if (on_after_apply) {
                            on_after_apply(copy, copy);
                        }
                        self.refresh_page(true);
                        self.update_controls(consts.UPDATE_APPLIED);
                    }
                });
            }
        }

        record_is_edited(show) {
            var pk = this._primary_key,
                pk_value = this.field_by_name(pk).value,
                tab_id = this.item_name + pk_value,
                i,
                item;
            for (i = 0; i < task._edited_items.length; i++) {
                item = task._edited_items[i];
                if (item.ID === this.ID) {
                    if (item._tab_info.tab_id === tab_id) {
                        if (show) {
                            task.show_tab(item._tab_info.container, item._tab_info.tab_id);
                        }
                        return true;
                    }
                }
            }
        }

        cancel_edit() {
            var self = this,
                refresh = !this.master && this.log_changes &&
                    this.item_state === consts.STATE_EDIT &&
                    this.change_log.record_status;
            if (this.is_changing()) {
                this.cancel();
            }
            if (this._source_item) {
                this.close_edit_form();
            }
            else {
                if (refresh) {
                    this.disable_edit_form();
                    this.refresh_page(function() {
                        self.close_edit_form();
                    })
                }
                else {
                    this.close_edit_form();
                }
            }
        }

        delete_record() {
            var self = this,
                rec_no = self.rec_no,
                record = self._dataset[rec_no],
                args = this._check_args(arguments),
                callback = args['function'],
                refresh_page = args['boolean'];
            if (refresh_page === undefined) {
                refresh_page = true;
            }
            if (!this.paginate) {
                refresh_page = false;
            }
            if (this.can_delete()) {
                if (this.rec_count > 0) {
                    let mess = this.question(language.delete_record,
                        function() {
                            self.delete();
                            self.apply(function(e) {
                                var error;
                                self.hide_message(mess);
                                if (e) {
                                    error = (e + '').toUpperCase();
                                    if (error && (error.indexOf('FOREIGN KEY') !== -1 ||
                                        error.indexOf('INTEGRITY CONSTRAINT') !== -1 ||
                                        error.indexOf('REFERENCE CONSTRAINT') !== -1
                                        )
                                    ) {
                                        self.alert_error(language.cant_delete_used_record);
                                    } else {
                                        self.alert_error(e);
                                    }
                                    self.refresh_page(true);
                                }
                                else {
                                    if (callback) {
                                        callback.call(this, this);
                                    }
                                    else if (refresh_page) {
                                        self.refresh_page(true);
                                    }
                                }
                            });
                        },
                        function() {
                            self.hide_message(mess);
                        },
                        null,
                        {hide: false}
                    );
                } else {
                    this.warning(language.no_record);
                }
            }
        }

        check_record_valid() {
            var error;
            this.each_field(function(field, j) {
                let e = field.check_valid();
                if (e) {
                    field.update_control_state(e);
                    if (!error) {
                        error = e;
                    }
                }
            });
            if (error) {
                throw new Error(error);
            }
        }

        check_filters_valid() {
            var error;
            this.each_filter(function(filter, j) {
                try {
                    filter.check_valid();
                } catch (e) {
                    filter.field.update_control_state(e);
                    if (filter.field1) {
                        filter.field1.update_control_state(e);
                    }
                    if (!error) {
                        error = e;
                    }
                }
            });
            if (error) {
                throw new Error(error);
            }
        }

        post_record() {
            this.post();
            this.close_edit_form();
        }

        apply_record() {
            let args = this._check_args(arguments),
                callback = args['function'],
                options = args['object'],
                self = this,
                default_options = {
                    close_form: true,
                    apply_params: {}
                };
            options = $.extend({}, default_options, options);
            if (this.is_changing()) {
                this.disable_edit_form();
                try {
                    this.post();
                    this.apply(options.apply_params, function(error) {
                        if (error && error.indexOf('aborted:') !== 0) {
                            self.alert_error(error, {duration: 10});
                            this.enable_edit_form();
                            self.edit();
                        }
                        else {
                            if (callback) {
                                callback.call(self, self);
                            }
                            if (options.close_form) {
                                if (self.master) {
                                    self.master.edit();
                                }
                                self.close_edit_form();
                            }
                            else {
                                this.enable_edit_form();
                                self.edit();
                            }
                        }
                    });
                }
                catch (e) {
                    console.error(e);
                    if (!(e.name && e.name === 'AbortError')) {
                        this.alert_error(e);
                    }
                    if (this.edit_form_disabled()) {
                        this.enable_edit_form();
                        if (!this.is_changing()) {
                            this.edit();
                        }
                    }
                }
            }
            else {
                if (options.close_form) {
                    this.close_edit_form();
                }
            }
        }

        view_modal(container) { // depricated
            this.is_lookup_item = true;
            this.view(container);
        }

        view(container, options) {
            this._show_selected = false;
            if (container && this.task.can_add_tab(container)) {
                this._view_in_tab(container, options);
            }
            else {
                this._view(container);
            }
        }

        _view(container) {
            var self = this;
            this.load_modules([this, this.owner], function() {
                if (!self._order_by_list.length && self.view_options.default_order) {
                    self.set_order_by(self.view_options.default_order);
                }
                if (self.paginate === undefined) {
                    if (self.master) {
                        self.paginate = false;
                    }
                    else {
                        self.paginate = true;
                    }
                }
                self.create_view_form(container);
                if (self.view_options.enable_search) {
                    self.init_search();
                }
                if (self.view_options.enable_filters) {
                    self.init_filters();
                }
            })
        }

        _view_in_tab(container, options) {
            var self = this,
                tab_id = this.item_name,
                content,
                default_options = {
                    tab_id: undefined,
                    caption: this.item_caption,
                    show_close_btn: true
                };

            options = $.extend({}, default_options, options);
            if (options.tab_id) {
                tab_id = tab_id + '_' + options.tab_id;
            }
            content = this.task.add_tab(container, options.caption,
            {
                tab_id: tab_id,
                show_close_btn: options.show_close_btn,
                set_active: true,
                on_close: function() {
                    task.show_tab(container, tab_id);
                    self.close_view_form();
                }
            });
            if (content) {
                this._tab_info = {container: container, tab_id: tab_id}
                this.view_options.tab_id = tab_id;
                this._view(content);
            }
        }

        create_view_form(container) {
            this._create_form('view', container);
        }

        close_view_form() {
            this._close_form('view');
        }

        create_edit_form(container) {
            this._create_form('edit', container);
        }

        close_edit_form() {
            this._close_form('edit');
        }

        create_filter_form(container) {
            this._create_form('filter', container);
        }

        close_filter_form() {
            this._close_form('filter');
        }

        apply_filters(search_params) {
            var self = this,
                params = {},
                search_field,
                search_value,
                search_type;
            try {
                if (this.on_filters_apply) {
                    this.on_filters_apply.call(this, this);
                }
                this.check_filters_valid();
                try {
                    if (search_params) {
                        search_field = search_params[0];
                        search_value = search_params[1];
                        search_type = search_params[2];
                        search_type = filter_value.indexOf(search_type) + 1;
                        if (search_value) {
                            params.__search = [search_field, search_value, search_type];
                        }
                    }
                }
                catch (e) {
                    params = {};
                }
                this.reopen(0, params, function() {
                    self.close_filter_form();
                });
            }
            catch (e) {
            }
        }

        get_filter_text() {
            var result = '';
            this.each_filter(function(filter) {
                if (filter.text) {
                    result += ' ' + filter.text;
                }
            });
            if (result && task.old_forms) {
                result = language.filter + ' -' + result;
            }
            result = this.item.sanitize_html(result);
            return result;
        }

        get_filter_html() {
            var result = '';
            this.each_filter(function(filter) {
                if (filter.get_html()) {
                    result += ' ' + filter.get_html();
                }
            });
            return result;
        }

        close_filter() { // depricated
            this.close_filter_form();
        }

        disable_controls() {
            this._disabled_count += 1;
        }

        enable_controls() {
            this._disabled_count -= 1;
            if (this.controls_enabled()) {
                this.update_controls();
            }
        }

        controls_enabled() {
            return this._disabled_count === 0;
        }

        controls_disabled() {
            return !this.controls_enabled();
        }

        update_controls(state) {
            if (state === undefined) {
                state = consts.UPDATE_CONTROLS;
            }
            if (this.controls_enabled()) {
                this.each_field(function(field) {
                    field.update_controls(state, true);
                });
                if (this.on_update_controls) {
                    this.on_update_controls.call(this, this);
                }
                for (var i = 0; i < this.controls.length; i++) {
                    this.controls[i].update(state);
                }
            }
        }

        resize_controls() {
            for (var i = 0; i < this.controls.length; i++) {
                if (this.controls[i].resize) {
                    this.controls[i].resize();
                }
            }
            this.each_detail(function(d) {
                d.resize_controls();
            });
        }

        create_view_tables() {
            var table_container = this.view_form.find('.' + this.view_options.table_container_class),
                height,
                details = this.view_options.view_details,
                detail,
                detail_container,
                self = this;
            if (table_container && table_container.length) {
                if (!this.lookup_field && details && details.length) {
                    detail_container = this.view_form.find('.' + this.view_options.detail_container_class);
                    if (detail_container) {
                        height = this.view_options.detail_height;
                        if (!height) {
                            height = 232;
                        }
                        this.create_detail_table(detail_container, {height: height});
                        this.table_options.height -= height;
                        if (this.table_options.height < 180) {
                            this.table_options.height = 180;
                        }
                    }
                }
                if (this.master || this.master_field) {
                    this.table_options.height = this.owner.edit_options.detail_height;
                    if (!this.table_options.height) {
                        this.table_options.height = 262;
                    }
                }
                this.create_table(table_container);
            }
        }

        create_detail_table(container, options) {
            var self = this,
                i,
                detail,
                detail_container,
                content,
                details = this.view_options.view_details,
                after_scroll = this.on_after_scroll,
                scroll_timeout,
                tab_changed = function(index) {
                    var table_options = {
                        editable_fields: [],
                        multiselect: false,
                        height: options.height
                    }
                    if (details.length > 1) {
                        table_options.height -= 38;
                    }
                    if (self._visible_detail) {
                        self._visible_detail.close();
                    }
                    self._visible_detail = self.find(details[index]);
                    self._visible_detail.create_table(detail_container, table_options);
                    self._visible_detail.open(true);
                    detail_container.show();
                };
            if (details && details.length && container && container.length) {
                detail_container = container;
                if (details.length > 1) {
                    this.task.init_tabs(container)
                }
                for (i = 0; i < details.length; i++) {
                    detail = this.find(details[i]);
                    if (details.length > 1) {
                        content = task.add_tab(container, detail.item_caption, {tab_id: i, on_click: tab_changed});
                        if (i === 0) {
                            detail_container = content;
                        }
                        else {
                            content.remove();
                        }
                    }
                }
                this._on_after_scroll_internal = function() {
                    if (self.view_form) {
                        clearTimeout(scroll_timeout);
                        scroll_timeout = setTimeout(
                            function() {
                                var detail = self._visible_detail;
                                detail.set_order_by(detail.view_options.default_order);
                                detail.open(true);
                            },
                            100
                        );
                    }
                }
                tab_changed(0);
            }
        }

        create_detail_views(container, options) {
            var self = this,
                i,
                detail,
                detail_container,
                details;

            if (!container || !container.length) {
                return;
            }

            if (options) {
                details = options.details
            }
            if (!details) {
                details = this.edit_options.edit_details;
            }

            if (details.length) {
                if (details.length > 1) {
                    this.task.init_tabs(container)
                }
                for (i = 0; i < details.length; i++) {
                    detail = this.find(details[i]);
                    detail_container = container;
                    if (details.length > 1) {
                        detail_container = task.add_tab(container, detail.item_caption);
                    }
                    detail.view_options.form_header = false;
                    detail.view_options.form_border = false;
                    detail.view_options.close_on_escape = false;
                    detail.view(detail_container);
                }
            }
        }

        add_view_button(text, options) {
            var container;
            options = $.extend({}, options);
            if (!options.parent_class_name) {
                if (this.view_form.find('.default-top-view').length) {
                    options.parent_class_name = 'form-header';
                }
                else {
                    options.parent_class_name = 'form-footer';
                }
            }
            container = this.view_form.find('.' + options.parent_class_name);
            return this.add_button(container, text, options);
        }

        add_edit_button(text, options) {
            var container;
            options = $.extend({}, options);
            if (!options.parent_class_name) {
                if (this.edit_form.find('.default-top-edit').length) {
                    options.parent_class_name = 'form-header';
                }
                else {
                    options.parent_class_name = 'form-footer';
                }
            }
            container = this.edit_form.find('.' + options.parent_class_name);
            return this.add_button(container, text, options);
        }

        add_button(container, text, options) {
            var default_options = {
                    btn_id: undefined,
                    btn_class: undefined,
                    image: undefined,
                    type: undefined,
                    secondary: false,
                    expanded: true,
                    shortcut: undefined
                },
                right_aligned,
                btn,
                result;
            if (!container.length) {
                return $();
            }
            right_aligned = container.hasClass('form-footer');
            options = $.extend({}, default_options, options);
            if (options.pull_left) { // for compatibility with previous versions
                options.secondary = options.pull_left;
            }
            if (!text) {
                text = 'Button';
            }
            result = $('<button class="btn" type="button"></button>')
            if (options.expanded) {
                result.addClass('expanded-btn')
            }
            if (options.btn_id) {
                result.attr('id', options.btn_id);
            }
            if (options.btn_class) {
                result.addClass(options.btn_class);
            }
            if (options.secondary) {
                if (right_aligned) {
                    result.addClass('pull-left');
                }
                else {
                    result.addClass('pull-right');
                }
            }
            if (options.type) {
                result.addClass('btn-' + options.type);
            }
            if (options.image && options.shortcut) {
                result.html('<i class="' + options.image + '"></i> ' + text + '<small class="muted">&nbsp;[' + options.shortcut + ']</small>')
            }
            else if (options.image) {
                result.html('<i class="' + options.image + '"></i> ' + text)
            }
            else if (options.shortcut) {
                result.html(' ' + text + '<small class="muted">&nbsp;[' + options.shortcut + ']</small>')
            }
            else {
                result.html(' ' + text)
            }
            if (right_aligned) {
                if (options.secondary) {
                    container.append(result);
                }
                else {
                    btn = container.find('> .btn:not(.pull-left):first');
                    if (btn.length) {
                        btn.before(result);
                    }
                    else {
                        container.append(result)
                    }
                }
            }
            else {
                if (options.secondary) {
                    btn = container.find('> .btn.pull-right:last');
                    if (btn.length) {
                        btn.after(result);
                    }
                    else {
                        container.append(result)
                    }
                }
                else {
                    btn = container.find('> .btn:not(.pull-right):last');
                    if (btn.length) {
                        btn.after(result);
                    }
                    else {
                        container.append(result);
                    }
                }
            }
            return result;
        }

        select_records(field_name, all_records) {
            let self = this;
            if (this.master_field && !this.owner._primary_key_field.value && this.owner.is_new()) {
                try {
                    this.owner.post();
                    this.owner.apply(function() {
                        self.owner.edit();
                        self._select_records(field_name, all_records)
                    });
                }
                catch (e) {
                }
            }
            else {
                this._select_records(field_name, all_records)
            }
        }

        _select_records(field_name, all_records) {
            var self = this,
                field = this.field_by_name(field_name),
                source,
                can_select = this.can_create();
            if (this.read_only) {
                can_select = false;
            }
            if (this.master && this.master.read_only) {
                can_select = false;
            }
            if (can_select) {
                source = field.lookup_item.copy()
                source.selections = [];
                source.on_view_form_close_query = function() {
                    var copy = source.copy(),
                        pk_in = copy._primary_key + '__in',
                        where = {};
                    if (source.selections.length) {
                        where[pk_in] = source.selections;
                        copy.set_where(where);
                        copy.lookup_field = field
                        copy.open(function() {
                            var rec_no = self.rec_no,
                                last_rec_no,
                                found,
                                existing_recs = {},
                                pk_field = copy.field_by_name(copy._primary_key),
                                clone = self.clone();
                            self.disable_controls();
                            self.last();
                            self._records_selected = true;
                            last_rec_no = self.rec_no;
                            try {
                                if (!all_records) {
                                    clone.each(function(c) {
                                        existing_recs[c[field_name].value] = true;
                                    });
                                }
                                copy.each(function(c){
                                    if (all_records || !existing_recs[pk_field.value]) {
                                        found = true;
                                        self.append();
                                        c.set_lookup_field_value();
                                        self.post();
                                    }
                                });
                            }
                            catch (e) {
                                console.error(e);
                            }
                            finally {
                                if (found) {
                                    if (last_rec_no) {
                                        self.rec_no = last_rec_no + 1;
                                    }
                                    else {
                                        self.first();
                                    }
                                }
                                else {
                                    self.rec_no = rec_no;
                                }
                                self._records_selected = false;
                                if (self.master) {
                                    self.owner._detail_changed(self, true);
                                }
                                self.enable_controls();
                            }
                        })
                    }
                }
                source.lookup_field = field;
                field._do_select_value(source);
                source.view();
            }
        }

        _detail_changed(detail, modified) {
            if (!detail._records_selected) {
                if (modified && !detail.paginate && this.on_detail_changed ||
                    detail.controls.length && detail.table_options.summary_fields.length) {
                    detail._fields_summary_info = undefined;
                    if (modified && this.on_detail_changed) {
                        this.on_detail_changed.call(this, this, detail);
                    }
                    if (detail._fields_summary_info === undefined) {
                        let self = this;
                        clearTimeout(this._detail_changed_time_out);
                        this._detail_changed_time_out = setTimeout(
                            function() {
                                self.calc_summary(detail);
                            },
                            100
                        );
                    }
                }
            }
        }

        calc_summary(detail, fields, callback, summary_fields) {
            var i,
                clone,
                obj,
                field_name,
                field,
                func,
                master_field_name,
                master_field,
                value,
                text,
                sums = [];
            if (detail.paginate) {
                return;
            }
            if (summary_fields === undefined) {
                summary_fields = detail.table_options.summary_fields;
            }
            detail._fields_summary_info = {};
            clone = detail.clone();
            if (this.on_detail_changed) {
                if (fields instanceof Array && fields.length) {
                    for (i = 0; i < fields.length; i++) {
                        master_field_name = Object.keys(fields[i])[0];
                        obj = fields[i][master_field_name];
                        field = undefined;
                        if (typeof obj === 'function') {
                            func = obj;
                        }
                        else {
                            field = clone.field_by_name(obj);
                        }
                        master_field = this.field_by_name(master_field_name);
                        sums.push({sum: 0, field: field, func: func, master_field: master_field});
                    }
                }
            }
            if (detail.controls.length && summary_fields.length) {
                for (i = 0; i < summary_fields.length; i++) {
                    field_name = summary_fields[i];
                    field = clone.field_by_name(field_name);
                    if (field) {
                        if (clone.rec_count || field.data_type !== consts.CURRENCY) {
                            sums.push({sum: 0, field: field, field_name: field_name});
                        }
                        else {
                            sums.push({sum: null, field: field, field_name: field_name});
                        }
                    }
                }
            }
            if (sums.length) {
                clone.each(function(c) {
                    for (i = 0; i < sums.length; i++) {
                        if (sums[i].field) {
                            if (sums[i].field.numeric_field()) {
                                sums[i].sum += sums[i].field.value;
                            }
                            else {
                                sums[i].sum += 1;
                            }
                        }
                        else if (sums[i].func) {
                            sums[i].sum += sums[i].func(c);
                        }
                    }
                });
                for (i = 0; i < sums.length; i++) {
                    master_field = sums[i].master_field;
                    if (master_field && this.is_changing()) {
                        value = sums[i].sum;
                        if (master_field.value !== value) {
                            master_field.value = value;
                        }
                    }
                    else {
                        field_name = sums[i].field_name;
                        field = sums[i].field;
                        value = sums[i].sum;
                        if (field_name) {
                            text = value + '';
                            if (field.data_type === consts.CURRENCY) {
                                text = field.cur_to_str(value)
                            }
                            else if (field.data_type === consts.FLOAT) {
                                text = field.float_to_str(value)
                            }
                            detail._fields_summary_info[field_name] = {text: text, value: value};
                        }
                    }
                }
                if (!$.isEmptyObject(detail._fields_summary_info)) {
                    detail.update_controls(consts.UPDATE_SUMMARY);
                }
                if (callback) {
                    callback.call(this, this);
                }
            }
        }

        create_table(container, options) {
            return new DBTable(this, container, options);
        }

        create_tree(container, parent_field, text_field, parent_of_root_value, options) {
            return new DBTree(this, container, parent_field, text_field, parent_of_root_value, options);
        }

        create_bands(tab, container) {
            var i,
                j,
                band,
                field,
                fields,
                div,
                options;
            for (i = 0; i < tab.bands.length; i++) {
                fields = tab.bands[i].fields
                if (fields.length) {
                    options = tab.bands[i].options;
                    options.fields = fields;
                    div = $('<div>')
                    container.append(div)
                    this.create_inputs(div, options);
                }
            }
        }

        create_tabs(container) {
            var i,
                tabs = this.edit_options.tabs;
            this.task.init_tabs(container);
            for (i = 0; i < tabs.length; i++) {
                this.create_bands(tabs[i], task.add_tab(container, tabs[i].name))
            }
        }

        create_controls(container) {
            var tabs = this.edit_options.tabs;
            container.empty();
            if (tabs.length > 1 || tabs.length === 1 && tabs[0].name) {
                this.create_tabs(container);
            }
            else {
                this.create_bands(tabs[0], container);
            }
        }

        create_inputs(container, options) {
            var default_options,
                i, len, col,
                field,
                fields = [],
                visible_fields = [],
                cols = [],
                tabindex,
                form,
                tabs;

            if (!container.length) {
                return;
            }

            default_options = {
                fields: [],
                col_count: 1,
                label_on_top: false,
                label_width: undefined,
                label_size: 3,
                row_count: undefined,
                autocomplete: false,
                in_well: true,
                tabindex: undefined
            };

            if (options && options.fields && options.fields.length) {
                visible_fields = options.fields
            } else {
                visible_fields = this.edit_options.fields;
            }
            if (visible_fields.length == 0) {
                tabs = this.edit_options.tabs;
                if (tabs) {
                    if (tabs.length === 1 && !tabs[0].name && tabs[0].bands.length === 1) {
                        visible_fields = tabs[0].bands[0].fields;
                        default_options = $.extend({}, default_options, tabs[0].bands[0].options);
                    }
                    else {
                        this.create_controls(container);
                        return;
                    }
                }
                else {
                    this.each_field(function(f) {
                        if (f.field_name !== f.owner._primary_key && f.field_name !== f.owner._deleted_flag) {
                            visible_fields.push(f.field_name);
                        }
                    });
                }
            }
            len = visible_fields.length;
            for (i = 0; i < len; i++) {
                field = this.field_by_name(visible_fields[i]);
                if (field) {
                    fields.push(field);
                } else {
                    console.error(this.item_name + ' create_entries: there is not a field with field_name - "' + visible_fields[i] + '"');
                }
            }

            options = $.extend({}, default_options, options);

            container.empty();

            form = $('<form class="row-fluid" autocomplete="off"></form>').appendTo(container);
            if (options.in_well) {
                form.addClass('well');
            }
            if (options.autocomplete) {
                form.attr("autocomplete", "on")
            }
            else {
                form.attr("autocomplete", "off")
            }
            if (!options.label_on_top) {
                form.addClass("form-horizontal");
            }
            len = fields.length;
            for (col = 0; col < options.col_count; col++) {
                cols.push($("<div></div>").addClass("span" + 12 / options.col_count).appendTo(form));
            }
            tabindex = options.tabindex;
            //~ if (!tabindex && this.edit_form) {
                //~ tabindex = this.edit_form.tabindex;
                //~ this.edit_form.tabindex += len;
            //~ }
            if (!options.row_count) {
                options.row_count = Math.ceil(len / options.col_count);
            }
            for (i = 0; i < len; i++) {
                new DBInput(fields[i], i + tabindex,
                    cols[Math.floor(i / options.row_count)], options);
            }
        }

        create_filter_inputs(container, options) {
            var default_options,
                i, len, col,
                filter,
                filters = [],
                cols = [],
                tabindex,
                form;

            if (!container.length) {
                return;
            }

            default_options = {
                    filters: [],
                    col_count: 1,
                    label_on_top: false,
                    label_width: undefined,
                    autocomplete: false,
                    in_well: true,
                    tabindex: undefined
            };

            options = $.extend({}, default_options, options);

            if (options.filters.length) {
                len = options.filters.length;
                for (i = 0; i < len; i++) {
                    filters.push(this.filter_by_name(options.filters[i]));
                }
            } else {
                this.each_filter(function(filter, i) {
                    if (filter.visible) {
                        filters.push(filter);
                    }
                });
            }
            container.empty();
            form = $('<form form class="row-fluid" autocomplete="off"></form>').appendTo($("<div></div>").addClass("row-fluid").appendTo(container));
            if (options.in_well) {
                form.addClass('well');
            }
            if (options.autocomplete) {
                form.attr("autocomplete", "on")
            }
            if (!options.label_on_top) {
                form.addClass("form-horizontal");
            }
            len = filters.length;
            for (col = 0; col < options.col_count; col++) {
                cols.push($("<div></div>").addClass("span" + 12 / options.col_count).appendTo(form));
            }
            tabindex = options.tabindex;
            if (!tabindex && this.filter_form) {
                tabindex = this.filter_form.tabindex;
                this.filter_form.tabindex += len;
            }
            for (i = 0; i < len; i++) {
                filter = filters[i];
                if (filter.filter_type === consts.FILTER_RANGE) {
                    new DBInput(filter.field, i + 1, cols[Math.floor(i % options.col_count)],
                        options, filter.filter_caption + ' ' + language.range_from);
                    new DBInput(filter.field1, i + 1, cols[Math.floor(i % options.col_count)],
                        options, filter.filter_caption + ' ' + language.range_to);
                }
                else {
                    new DBInput(filter.field, i + 1, cols[Math.floor(i % options.col_count)],
                        options, filter.filter_caption);
                }
            }
        }

        _find_lookup_value(field, lookup_field) {
            if (lookup_field._owner_is_item()) {
                if (field.lookup_field && field.lookup_field1 &&
                    lookup_field.lookup_item1 && lookup_field.lookup_item2) {
                    if (field.owner.ID === lookup_field.lookup_item.ID &&
                        field.lookup_item.ID === lookup_field.lookup_item1.ID &&
                        field.lookup_field === lookup_field.lookup_field1 &&
                        field.lookup_item1.ID === lookup_field.lookup_item2.ID &&
                        field.lookup_field1 === lookup_field.lookup_field2) {
                        return field.lookup_value;
                    }
                }
                else if (field.lookup_field) {
                    if (field.owner.ID === lookup_field.lookup_item.ID &&
                        field.lookup_field === lookup_field.lookup_field1 &&
                        field.lookup_item.ID === lookup_field.lookup_item1.ID) {
                        return field.lookup_value;
                    }
                }
                else if (field.field_name === lookup_field.lookup_field &&
                    field.owner.ID === lookup_field.lookup_item.ID) {
                    return field.lookup_value;
                }
            }
            else  if (field.field_name === lookup_field.lookup_field) {
                return field.lookup_value;
            }
        }

        set_lookup_field_value() {
            if (this.record_count()) {
                var lookup_field = this.lookup_field,
                    item_field = this.field_by_name(lookup_field.lookup_field),
                    lookup_value = null,
                    item = this.lookup_field.owner,
                    ids = [],
                    slave_field_values = {},
                    self = this;

                if (item_field) {
                    lookup_value = this._find_lookup_value(item_field, lookup_field);
                }
                if (lookup_field.owner && lookup_field.owner.is_changing && !lookup_field.owner.is_changing()) {
                    lookup_field.owner.edit();
                }
                if (this.lookup_field.data_type === consts.KEYS) {
                    this.selections = [this._primary_key_field.value];
                }
                else if (lookup_field.multi_select) {
                    lookup_field.set_value([this._primary_key_field.value], lookup_value);
                } else {
                    if (item) {
                        item.each_field(function(item_field) {
                            if (item_field.master_field === lookup_field) {
                                self.each_field(function(field) {
                                    var lookup_value
                                    if (field.lookup_value) {
                                        lookup_value = self._find_lookup_value(field, item_field);
                                        if (lookup_value) {
                                            slave_field_values[item_field.field_name] = lookup_value;
                                            return false;
                                        }
                                    }
                                })
                            }
                        });
                    }
                    lookup_field.set_value(this._primary_key_field.value, lookup_value, slave_field_values, this);
                }
            }
            if (this.lookup_field) {
                this.close_view_form();
            }
        }

        get default_field() { // depricated
            var i = 0;
            if (this._default_field === undefined) {
                this._default_field = null;
                for (i = 0; i < this.fields.length; i++) {
                    if (this.fields[i].default) {
                        this._default_field = this.fields[i];
                        break;
                    }
                }
            }
            return this._default_field;
        }

        set_edit_fields(fields) {
            this.edit_options.fields = fields;
        }

        set_view_fields(fields) {
            this.view_options.fields = fields;
        }

        _do_on_refresh_record(copy, options, callback, async) {
            var i,
                len,
                default_options = {
                    details: [],
                    filters: {},
                    default_order: true
                },
            options = $.extend(true, {}, default_options, options);
            if (copy.rec_count === 1 && this.rec_count &&
                copy._primary_key_field.value === this._primary_key_field.value) {
                len = copy._dataset[0].length;
                for (i = 0; i < len; i++) {
                    this._dataset[this.rec_no][i] = copy._dataset[0][i];
                }
                this.each_detail(function(d) {
                    if (d.active) {
                        if ($.inArray(d.item_name, options.details) === -1)  {
                            options.details.push(d.item_name);
                            if (d._open_params.__filters) {
                                options.filters[d.item_name] = d._open_params.__filters.slice();
                            }
                        }
                    }
                });
                this.change_log.record_status = consts.RECORD_UNCHANGED;
                this.update_controls(consts.UPDATE_RECORD);
                if (options.details.length) {
                    options.master_refresh_record = true;
                    this.open_details(options, callback, async);
                }
                else if (callback) {
                    callback.call(this);
                }
            }
            else {
                this.change_log.record_status = consts.RECORD_UNCHANGED;
                for (var i = 0; i < len; i++) {
                    this.details[i]._do_close();
                }
                this._dataset.splice(this.rec_no, 1);
                this.rec_no = this.rec_no;
                this.update_controls()
                console.error('Refresh record, the record is not found in the database table.')
            }
        }

        refresh_record(callback) {
            var args = this._check_args(arguments),
                callback = args['function'],
                async = args['boolean'],
                options = args['object'],
                self = this,
                fields = [],
                primary_key = this._primary_key,
                copy;
            if (this.master) {
                console.trace();
                throw new Error('The refresh_record method can not be executed for a detail item');
            }
            if (!this.rec_count) {
                return
            }
            options = $.extend({}, options);
            copy = this.copy({filters: false, details: false, handlers: false});
            if (this._primary_key_field.value) {
                self.each_field(function(field) {
                    fields.push(field.field_name)
                })
                copy._where_list = [[primary_key, consts.FILTER_EQ, this._primary_key_field.value, -2]];
                if (callback || async) {
                    copy.open({expanded: this.expanded, fields: fields, params: options.params}, function() {
                        self._do_on_refresh_record(copy, options, callback, async);
                    });
                } else {
                    copy.open({expanded: this.expanded, fields: fields, params: options.params});
                    this._do_on_refresh_record(copy, options);
                }
            }
            else if (callback) {
                callback.call(this);
            }
        }

        format_string(str, value) {
            var result = str;
            if (typeof value === 'object') {
                for (var key in value) {
                    if (value.hasOwnProperty(key)) {
                        result = result.replace('%(' + key + ')s', value[key] + '')
                    }
                }
            }
            else {
                result = result.replace('%s', value + '')
            }
            return result
        }
    }

    class Report extends AbsrtactItem {
        constructor(owner, ID, item_name, caption, visible, type, js_filename) {
            super(owner, ID, item_name, caption, visible, type, js_filename);
            if (this.task && !(item_name in this.task)) {
                this.task[item_name] = this;
            }
            this._fields = [];
            this.params = this._fields;
            this._state = consts.STATE_EDIT;
            this.param_options = $.extend({}, this.task.form_options);
        }

        _set_item_state(value) {
            if (this._state !== value) {
                this._state = value;
            }
        }

        _get_item_state() {
            return this._state;
        }

        initAttr(info) {
            var i,
                params = info.fields,
                len;
            if (params) {
                len = params.length;
                for (i = 0; i < len; i++) {
                    new Param(this, params[i]);
                }
            }
        }

        _bind_item() {
            var i = 0,
                param,
                len = this.params.length;
            for (i = 0; i < len; i++) {
                param = this.params[i];
                if (param.lookup_item && (typeof param.lookup_item === "number")) {
                    param.lookup_item = this.task.item_by_ID(param.lookup_item);
                }
                if (param.lookup_field && (typeof param.lookup_field === "number")) {
                    param.lookup_field = param.lookup_item._field_by_ID(param.lookup_field).field_name;
                }
                if (param.lookup_values && (typeof param.lookup_values === "number")) {
                    param.lookup_values = self.task.lookup_lists[param.lookup_values];
                }
            }
            this.param_options.title = this.item_caption;
        }

        eachParam(callback) {
            var i = 0,
                len = this.params.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.params[i], this.params[i], i);
                if (value === false) {
                    break;
                }
            }
        }

        each_field(callback) {
            this.eachParam(callback);
        }

        param_by_name(name) {
            var i = 0,
                len = this.params.length;
            for (; i < len; i++) {
                if (this.params[i].param_name === name) {
                    return this.params[i];
                }
            }
        }

        create_param_form(container) {
            this._create_form('param', container);
        }

        close_param_form() {
            this._close_form('param');
        }

        print(p1, p2) {
            var self = this;
            this.load_modules([this, this.owner], function() {
                self._print(p1, p2);
            })
        }

        _print() {
            var args = this._check_args(arguments),
                callback = args['function'],
                create_form = args['boolean'];
            if (!create_form) {
                this.eachParam(function(param) {
                    if (param.edit_visible) {
                        create_form = true;
                        return false;
                    }
                });
            }
            if (create_form) {
                this.create_param_form();
            } else {
                this.process_report(callback);
            }
        }

        checkParams() {
            var i,
                len = this.params.length;
            for (i = 0; i < len; i++) {
                try {
                    this.params[i].check_valid();
                } catch (e) {
                    this.warning(e);
                    return false;
                }
            }
            return true;
        }

        process_report(callback) {
            var self = this,
                host = [location.protocol, '//', location.host, location.pathname].join(''),
                i,
                len,
                param_values = [];
            if (this.checkParams()) {
                if (this.task.on_before_print_report) {
                    this.task.on_before_print_report.call(this, this);
                }
                if (this.owner.on_before_print_report) {
                    this.owner.on_before_print_report.call(this, this);
                }
                if (this.on_before_print_report) {
                    this.on_before_print_report.call(this, this);
                }
                len = this.params.length;
                for (i = 0; i < len; i++) {
                    param_values.push(this.params[i].data);
                }
                this.send_request('print', [param_values, host, this.extension], function(result) {
                    var url,
                        error,
                        ext,
                        timeOut,
                        win;
                    if (result) {
                        url = result[0],
                        error = result[1];
                    }
                    if (error) {
                        self.warning(error);
                    }
                    if (url) {
                        if (self.on_open_report) {
                            self.on_open_report.call(self, self, url);
                        } else if (self.owner.on_open_report) {
                            self.owner.on_open_report.call(self.owner, self, url);
                        } else {
                            ext = url.split('.').pop();
                            if (ext === 'ods') {
                                window.open(url, "_self");
                            } else {
                                win = window.open(url, "_blank")
                                if (self.send_to_printer) {
                                    win.onload = function() {
                                        win.print();
                                        timeOut = setTimeout(
                                            function() {
                                                win.onfocus = function() {
                                                    win.close();
                                                }
                                            },
                                            1000
                                        );
                                    }
                                }
                            }
                        }
                    }
                    if (callback) {
                        callback.call(self, self, url);
                    }
                });
                return true;
            }
        }

        create_param_inputs(container, options) {
            var default_options,
                i, len, col,
                params = [],
                cols = [],
                form,
                tabindex;

            if (!container.length) {
                return;
            }

            default_options = {
                params: [],
                col_count: 1,
                label_on_top: false,
                label_width: undefined,
                autocomplete: false,
                in_well: true,
                tabindex: undefined
            }

            options = $.extend({}, default_options, options);

            if (options.params.length) {
                len = options.params.length;
                for (i = 0; i < len; i++) {
                    params.push(this.param_by_name(options.params[i]));
                }
            } else {
                this.eachParam(function(param) {
                    if (param.edit_visible && param.edit_index !== -1) {
                        params.push(param);
                    }
                });
            }
            container.empty();
            form = $('<form form class="row-fluid" autocomplete="off"></form>').appendTo($("<div></div>").addClass("row-fluid").appendTo(container));
            if (options.in_well) {
                form.addClass('well');
            }
            if (options.autocomplete) {
                form.attr("autocomplete", "on")
            }
            if (!options.label_on_top) {
                form.addClass("form-horizontal");
            }
            len = params.length;
            for (col = 0; col < options.col_count; col++) {
                cols.push($("<div></div>").addClass("span" + 12 / options.col_count).appendTo(form));
            }
            tabindex = options.tabindex;
            if (!tabindex && this.param_form) {
                tabindex = this.param_form.tabindex;
                this.param_form.tabindex += len;
            }
            for (i = 0; i < len; i++) {
                new DBInput(params[i], i + tabindex,
                    cols[Math.floor(i % options.col_count)], options);
            }
        }
    }


    class Detail extends Item {
        constructor(owner, ID, item_name, caption, visible, type, js_filename, master_field) {
            super(owner, ID, item_name, caption, visible, type, js_filename);
            if (owner) {
                this.master_field = master_field;
                this.master = owner;
                owner.details.push(this);
                owner.details[item_name] = this;
            }
        }

        getChildClass() {
            return Detail;
        }
    }


    class Field {
        constructor(owner, info) {
            this.owner = owner;
            this.set_info(info);
            this.controls = [];
            this.bind_index = null;
            this.lookup_index = null;
            this.field_type = field_type_names[this.data_type];
            this.field_kind = consts.ITEM_FIELD;
            if (owner) {
                owner._fields.push(this);
            }
        }

        copy(owner) {
            var result = new Field(owner, this.get_info());
            result.lookup_item = this.lookup_item;
            result.lookup_field = this.lookup_field;
            return result;
        }

        get_info() {
            var i,
                len = field_attr.length,
                result = [];
            for (i = 0; i < len; i++) {
                result.push(this[field_attr[i]]);
            }
            return result;
        }

        set_info(info) {
            if (info) {
                var i,
                    len = field_attr.length;
                for (i = 0; i < len; i++) {
                    this[field_attr[i]] = info[i];
                }
            }
        }

        get field_mask() {
            return this.field_interface.field_mask;
        }

        set field_mask(value) {
            this.field_interface.field_mask = value;
        }

        get field_textarea() {
            return this.field_interface.textarea;
        }

        get field_do_not_sanitize() {
            return this.field_interface.do_not_sanitize;
        }

        get_row() {
            if (this.owner._dataset && this.owner._dataset.length) {
                return this.owner._dataset[this.owner.rec_no];
            } else {
                var mess = language.value_in_empty_dataset.replace('%s', this.owner.item_name);
                if (this.owner) {
                    this.owner.alert_error(mess, {duration: 0});
                }
                throw new Error(mess);
            }
        }

        get data() {
            var row,
                result;
            if (this._owner_is_item()) {
                row = this.get_row();
                if (row && this.bind_index >= 0) {
                    result = row[this.bind_index];
                    if (this.data_type === consts.DATETIME && result) {
                        result = result.replace('T', ' ');
                    }
                    return result;
                }

            } else {
                return this._value;
            }
        }

        set data(value) {
            var row;
            if (this._owner_is_item()) {
                row = this.get_row();
                if (row && this.bind_index >= 0) {
                    row[this.bind_index] = value;
                }
            } else {
                this._value = value;
            }
        }

        get raw_value() {
            return this.data;
        }

        get lookup_type() {
            return field_type_names[this.lookup_data_type];
        }

        get lookup_data() {
            var row,
                result;
            if (this._owner_is_item()) {
                row = this.get_row();
                if (row && this.lookup_index >= 0) {
                    result = row[this.lookup_index];
                    if (this.data_type === consts.DATETIME && result) {
                        result = result.replace('T', ' ');
                    }
                    return result
                }
            } else {
                return this._lookup_value;
            }
        }

        set lookup_data(value) {
            var row;
            if (this._owner_is_item()) {
                row = this.get_row();
                if (row && this.lookup_index >= 0) {
                    row[this.lookup_index] = value;
                }
            } else {
                this._lookup_value = value
            }
        }

        _value_to_text(data, value, data_type) {
            let result = '';
            if (data === null) {
                if (data_type === consts.BOOLEAN) {
                    result = language.false;
                }
            }
            else {
                result = value;
                switch (data_type) {
                    case consts.TEXT:
                    case consts.LONGTEXT:
                    case consts.IMAGE:
                        result = value + '';
                        break;
                    case consts.INTEGER:
                        result = this.int_to_str(result);
                        break;
                    case consts.FLOAT:
                        result = this.float_to_str(result);
                        break;
                    case consts.CURRENCY:
                        result = this.float_to_str(result);
                        break;
                    case consts.DATE:
                        result = this.date_to_str(result);
                        break;
                    case consts.DATETIME:
                        result = this.datetime_to_str(result);
                        break;
                    case consts.BOOLEAN:
                        if (result) {
                            result = language.true;
                        } else {
                            result = language.false;
                        }
                        break;
                    case consts.KEYS:
                        if (result.length) {
                            result = language.items_selected.replace('%s', result.length);
                        }
                        break;
                    case consts.FILE:
                        result = this.get_secure_file_name(result);
                        break;
                    default:
                        result = ''
                }
            }
            return result;
        }

        get text() {
            return this._value_to_text(this.data, this.value, this.data_type);
        }

        set text(value) {
            var error = "";
            if (value !== this.text) {
                switch (this.data_type) {
                    case consts.TEXT:
                        this.value = value + '';
                        break;
                    case consts.INTEGER:
                        this.value = this.str_to_int(value);
                        break;
                    case consts.FLOAT:
                        this.value = this.str_to_float(value);
                        break;
                    case consts.CURRENCY:
                        this.value = this.str_to_float(value);
                        break;
                    case consts.DATE:
                        this.value = this.str_to_date(value);
                        break;
                    case consts.DATETIME:
                        this.value = this.str_to_datetime(value);
                        break;
                    case consts.BOOLEAN:
                        if (value.toUpperCase() === language.yes.toUpperCase() ||
                            value.toUpperCase() === language.true.toUpperCase()) {
                            this.value = true;
                        } else {
                            this.value = false;
                        }
                        break;
                    case consts.KEYS:
                        break;
                    default:
                        this.value = value;
                }
            }
        }

        get value() {
            var value = this.data;
            if (value === null) {
                if (this._owner_is_item()) {
                    switch (this.data_type) {
                        case consts.INTEGER:
                            if (!this.lookup_item && !this.lookup_values) {
                                value = 0;
                            }
                            break;
                        case consts.FLOAT:
                        case consts.CURRENCY:
                            value = 0;
                            break;
                        case consts.TEXT:
                        case consts.LONGTEXT:
                            value = '';
                            break;
                        case consts.BOOLEAN:
                            value = false;
                            break;
                        case consts.KEYS:
                            value = [];
                            break;
                    }
                }
            }
            else {
                switch (this.data_type) {
                    case consts.TEXT:
                    case consts.LONGTEXT:
                        value = value + '';
                        break;
                    case consts.DATE:
                        value = task.format_string_to_date(value, '%Y-%m-%d');
                        break;
                    case consts.DATETIME:
                        value = task.format_string_to_date(value, '%Y-%m-%d %H:%M:%S');
                        break;
                    case consts.BOOLEAN:
                        value = Boolean(value);
                        break;
                    case consts.KEYS:
                        value = this._parse_keys(value);
                        break;
                    case consts.FILE:
                        value = this.get_secure_file_name(value);
                        break;
                }
            }
            return value;
        }

        _parse_keys(value) {
            if (value) {
                return value.split(';').map(function(i) { return parseInt(i, 10) });
            }
            else {
                return [];
            }
        }

        set value(value) {
            this.set_value(value);
        }

        _change_lookup_field(lookup_value, slave_field_values) {
            var self = this,
                item = this.owner,
                master_field;
            if (this.lookup_item) {
                if (this.owner) {
                    master_field = this;
                    if (this.master_field) {
                        master_field = this.master_field
                    }
                    master_field.lookup_value = null;
                    this.owner.each_field(function(field) {
                        if (field.master_field === master_field) {
                            if (master_field === self && slave_field_values && slave_field_values[field.field_name]) {
                                field.lookup_value = slave_field_values[field.field_name]
                            }
                            else {
                                field.lookup_value = null;
                            }
                        }
                    });
                }
                if (lookup_value) {
                    this.lookup_value = lookup_value;
                }
            }
        }

        _do_before_changed() {
            if (this._owner_is_item()) {
                if (!this.owner.is_changing()) {
                    throw new Error(language.not_edit_insert_state.replace('%s', this.owner.item_name));
                }
                if (this.owner.on_before_field_changed) {
                    this.owner.on_before_field_changed.call(this.owner, this);
                }
            }
        }

        _do_after_changed(lookup_item) {
            if (this.owner && this.owner.on_field_changed) {
                this.owner.on_field_changed.call(this.owner, this, lookup_item);
            }
            if (this.filter) {
                this.filter.update(this);
                if (this.filter.owner.on_filter_changed) {
                    this.filter.owner.on_filter_changed.call(this.filter.owner, this.filter);
                }
            }
        }

        _check_system_field_value(value) {
            if (this._owner_is_item()) {
                if (this.field_name === this.owner._primary_key && this.value && this.value !== value) {
                    throw new Error(language.no_primary_field_changing.replace('%s', this.owner.item_name));
                }
                if (this.field_name === this.owner._deleted_flag && this.value !== value) {
                    throw new Error(language.no_deleted_field_changing.replace('%s', this.owner.item_name));
                }
            }
        }

        set_value(value, lookup_value, slave_field_values, lookup_item) {
            if (value === undefined) {
                value = null;
            }
            this._check_system_field_value(value);
            if (this.field_kind === consts.ITEM_FIELD && !this.owner.is_changing()) {
                this.owner.edit();
            }
            this.new_value = null;
            if (value !== null) {
                if (this.multi_select) {
                    this.new_value = value;
                }
                else {
                    switch (this.data_type) {
                        case consts.TEXT:
                        case consts.LONGTEXT:
                            value = value + '';
                            break;
                        case consts.CURRENCY:
                            value = task.round(value, locale.FRAC_DIGITS);
                            break;
                        case consts.BOOLEAN:
                            value = value ? 1 : 0;
                            break;
                        case consts.DATE:
                            value = task.format_date_to_string(value, '%Y-%m-%d');
                            break;
                        case consts.DATETIME:
                            value = task.format_date_to_string(value, '%Y-%m-%d %H:%M:%S');
                            break;
                        case consts.KEYS:
                            value = value.join(';');
                            break;
                    }
                    this.new_value = value;
                }
            }
            if (this.data !== this.new_value) {
                this._do_before_changed();
                this.data = this.new_value;
                this._change_lookup_field(lookup_value, slave_field_values);
                this._set_modified(true);
                this._do_after_changed(lookup_item);
            } else if (lookup_value && lookup_value !== this.lookup_value) {
                this.lookup_value = lookup_value;
                this._do_after_changed(lookup_item, slave_field_values);
            }
            this.new_value = null;
            this.update_controls();
        }

        _owner_is_item() {
            return this.field_kind === consts.ITEM_FIELD;
        }

        _set_modified(value) {
            if (this._owner_is_item()) {
                if (this.owner._set_modified) {
                    this.owner._set_modified(value);
                }
            }
        }

        get _lookup_field() {
            if (this.lookup_item) {
                if (this.lookup_field2) {
                    return this.lookup_item2._field_by_name(this.lookup_field2);
                }
                else if (this.lookup_field1) {
                    return this.lookup_item1._field_by_name(this.lookup_field1);
                }
                else {
                    return this.lookup_item._field_by_name(this.lookup_field);
                }
            }
        }

        get lookup_data_type() {
            if (this.lookup_values) {
                return consts.TEXT;
            }
            else if (this.lookup_item) {
                return this._lookup_field.data_type;
            }
            else {
                return this.data_type;
            }
        }

        _get_value_in_list(value) {
            let i = 0,
                len = this.lookup_values.length,
                result = '';
            if (typeof value === 'string') {
                return value;
            }
            try {
                for (; i < len; i++) {
                    if (this.lookup_values[i][0] === value) {
                        result = this.lookup_values[i][1];
                    }
                }
            } catch (e) {}
            return result
        }

        get_secure_file_name(data) {
            let result = data;
            if (result === null) {
                result = ''
            }
            else {
                let sep_pos = data.indexOf('?');
                if (sep_pos !== -1) {
                    result = result.substr(0, sep_pos);
                }
            }
            return result;
        }

        get_file_name(data) {
            let result = data;
            if (result === null) {
                result = ''
            }
            else {
                let sep_pos = data.indexOf('?');
                if (sep_pos !== -1) {
                    result = result.substr(sep_pos + 1);
                }
            }
            return result;
        }

        get lookup_value() {
            let result = null;
            if (this.data_type === consts.KEYS) {
                result = this.value
            }
            else if (this.lookup_item && (!this._owner_is_item() || this.owner.expanded)) {
                let lookup_field = this._lookup_field,
                    data_type = this.lookup_data_type;
                result = this.lookup_data;
                switch (data_type) {
                    case consts.DATE:
                        if (typeof(result) === "string") {
                            result = task.format_string_to_date(result, '%Y-%m-%d');
                        }
                        break;
                    case consts.DATETIME:
                        if (typeof(result) === "string") {
                            result = task.format_string_to_date(result, '%Y-%m-%d %H:%M:%S');
                        }
                        break;
                    case consts.BOOLEAN:
                        result = Boolean(result);
                        break;
                    case consts.KEYS:
                        result = this._parse_keys(result);
                        break;
                    case consts.FILE:
                        result = this.get_secure_file_name(result);
                        break;
                }
            }
            else {
                result = this.value;
            }
            return result;
        }

        set lookup_value(value) {
            if (this.lookup_item) {
                this.lookup_data = value;
                this.update_controls();
            }
        }

        get lookup_text() {
            if (this.data_type === consts.KEYS) {
                return this.text;
            }
            else if (this.lookup_item && (!this._owner_is_item() || this.owner.expanded)) {
                return this._value_to_text(this.lookup_data, this.lookup_value, this.lookup_data_type);
            }
            else {
                return this.text;
            }
        }

        _get_image_size(edit_image) {
            var width,
                height,
                value,
                field_image,
                result = {};
            if (this.lookup_data_type === consts.IMAGE) {
                field_image = this.field_image;
                value = this.value;
                if (this.lookup_item) {
                    field_image = this.lookup_item[this.lookup_field].field_image;
                    value = this.lookup_value;
                }
                width = field_image.view_width;
                height = field_image.view_height;
                if (edit_image) {
                    width = field_image.edit_width;
                    height = field_image.edit_height;
                }
                if (!width) {
                    width = 'auto';
                }
                else {
                    width += 'px';
                }
                if (!height) {
                    height = 'auto';
                }
                else {
                    height += 'px';
                }
            }
            result.width = width;
            result.height = height;
            return result
        }

        _get_image(edit_image) {
            var size,
                field_image,
                value,
                src,
                placeholder;
            if (this.lookup_data_type === consts.IMAGE) {
                size = this._get_image_size(edit_image),
                field_image = this.field_image;
                value = this.value;
                if (this.lookup_item) {
                    field_image = this.lookup_item[this.lookup_field].field_image;
                    value = this.lookup_value;
                }
                if (field_image.placeholder) {
                    placeholder = 'static/builder/' + field_image.placeholder;
                }
                else {
                    placeholder = 'jam/img/placeholder.png';
                }
                if (task.ID) {
                    src = 'static/files/' + value;
                }
                else {
                    src = 'static/builder/' + value;
                }
                if (value) {
                    return '<img src="' + src + '" alt="Image" style="width:' + size.width + ';height:' + size.height + '">';
                }
                else {
                    return '<img src="' + placeholder + '" alt="Image placeholder" style="width:' + size.width + ';height:' + size.height + '">';
                }
            }
        }

        get_html() {
            let result = '';
            if (this.owner && this.owner.on_field_get_html) {
                result = this.owner.on_field_get_html.call(this.owner, this);
            }
            if (!result && this.lookup_data_type === consts.IMAGE) {
                result = this._get_image();
            }
            return result;
        }

        get display_text() {
            var res,
                len,
                value,
                result = '';
            if (this.multi_select) {
                value = this.data;
                if (value instanceof Array) {
                    len = value.length;
                }
                if (len) {
                    if (len === 1 && this.lookup_value) {
                        result = this.lookup_value;
                    }
                    else {
                        result = language.items_selected.replace('%s', len);
                    }
                }
            }
            else if (this.lookup_item && (!this._owner_is_item() || this.owner.expanded)) {
                let lookup_field = this._lookup_field,
                    data_type = lookup_field.data_type;
                if (lookup_field.lookup_values) {
                    result = lookup_field._get_value_in_list(this.lookup_data);
                }
                else if (data_type === consts.CURRENCY) {
                    result = this.cur_to_str(this.lookup_data);
                }
                else if (data_type === consts.FILE) {
                    result = this.get_file_name(this.lookup_data);
                }
                else {
                    result = this.lookup_text;
                }
            }
            else {
                if (this.data_type === consts.CURRENCY) {
                    result = this.cur_to_str(this.data)
                }
                else if (this.data_type === consts.FILE) {
                    result = this.get_file_name(this.data);
                }
                else if (this.lookup_values) {
                    result = this._get_value_in_list(this.data);
                }
                else {
                    result = this.lookup_text;
                }
            }
            if (this.owner && (this.owner.on_field_get_text || this.owner.on_get_field_text)) {
                if (!this.on_field_get_text_called) {
                    this.on_field_get_text_called = true;
                    try {
                        if (this.owner.on_field_get_text) {
                            res = this.owner.on_field_get_text.call(this.owner, this);
                        }
                        else if (this.owner.on_get_field_text) {
                            res = this.owner.on_get_field_text.call(this.owner, this);
                        }
                        if (res !== undefined) {
                            result = res;
                        }
                    } finally {
                        this.on_field_get_text_called = false;
                    }
                }
            }
            return result;
        }

        get sanitized_text() {
            let result = this.display_text;
            if (this._owner_is_item() && !this.field_do_not_sanitize) {
                result = this.owner.sanitize_html(result);
            }
            return result;
        }

        assign_default_value() {
            if (this.default_value !== null) {
                try {
                    switch (this.data_type) {
                        case consts.INTEGER:
                            this.data = parseInt(this.default_value, 10)
                            break;
                        case consts.FLOAT:
                        case consts.CURRENCY:
                            this.data = parseFloat(this.default_value)
                            break;
                        case consts.DATE:
                            if (this.default_value === 'current date') {
                                this.data = task.format_date_to_string(new Date(), '%Y-%m-%d');
                            }
                            break;
                        case consts.DATETIME:
                            if (this.default_value === 'current datetime') {
                                this.data = task.format_date_to_string(new Date(), '%Y-%m-%d %H:%M:%S');
                            }
                            break;
                        case consts.BOOLEAN:
                            if (this.default_value === 'true') {
                                this.data = true;
                            }
                            else if (this.default_value === 'false') {
                                this.data = false;
                            }
                            break;
                        case consts.TEXT:
                        case consts.LONGTEXT:
                        case consts.IMAGE:
                        case consts.FILE:
                        case consts.KEYS:
                            this.data = this.default_value + '';
                            break;
                    }
                }
                catch (e) {
                    console.error(e)
                }
            }
        }

        upload_image() {
            var self = this;
            this.owner.task.upload(
                {
                    accept: 'image/*',
                    item_id: self.owner.ID,
                    field_id: self.ID,
                    callback: function(server_file_name, file_name) {
                        self.value = server_file_name;
                    }
                }
            );
        }

        upload() {
            var self = this;
            this.owner.task.upload(
                {
                    accept: this.field_file.accept,
                    item_id: self.owner.ID,
                    field_id: self.ID,
                    callback: function(server_file_name, file_name) {
                        if (file_name.length > 255) {
                            let ext = file_name.split('.').pop();
                            file_name = file_name.substr(0, 255 - ext.length - 1) + '.' + ext;
                        }
                        self.value = server_file_name + '?' +  file_name;
                    }
                }
            );
        }

        open() {
            var url,
                link = document.createElement('a');
            if (this.data) {
                url = [location.protocol, '//', location.host, location.pathname].join('');
                url += 'static/files/' + this.value;
                window.open(encodeURI(url));
            }
        }

        download() {
            var url,
                link = document.createElement('a');
            if (this.data) {
                url = [location.protocol, '//', location.host, location.pathname].join('');
                url += 'static/files/';
                if (typeof link.download === 'string') {
                    link = document.createElement('a');
                    link.href = encodeURI(url + this.value);
                    link.download = this.display_text;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                } else {
                    this.open();
                }
            }
        }

        check_valid() {
            if (this.required && this.data === null) {
                return this.field_caption + ': ' + language.value_required;
            }
            if (this.data_type === consts.TEXT && this.field_size !== 0 && this.text.length > this.field_size) {
                return this.field_caption + ': ' + language.invalid_length.replace('%s', this.field_size);
            }
            if (this.owner && this.owner.on_field_validate) {
                let err = this.owner.on_field_validate.call(this.owner, this);
                if (err) {
                    return err;
                }
            }
            if (this.filter) {
                let err = this.filter.check_value(this)
                if (err) {
                    return err;
                }
            }
        }

        set read_only(value) {
            this._read_only = value;
            this.update_controls();
        }

        get read_only() {
            var result = this._read_only;
            if (this.owner && this.owner.owner_read_only && this.owner.read_only) {
                result = true;
            }
            if (this.calculated) {
                result = true;
            }
            return result;
        }

        set alignment(value) {
            this._alignment = value;
            this.update_controls();
        }

        get alignment() {
            return this._alignment;
        }

        get_mask() {
            var ch = '',
                format,
                result = '';
            if (this.data_type === consts.DATE) {
                format = locale.D_FMT;
            }
            else if (this.data_type === consts.DATETIME) {
                format = locale.D_T_FMT;
            }
            if (format) {
                for (var i = 0; i < format.length; ++i) {
                    ch = format.charAt(i);
                    switch (ch) {
                        case "%":
                            break;
                        case "d":
                        case "m":
                            result += '99';
                            break;
                        case "Y":
                            result += '9999';
                            break;
                        case "H":
                        case "M":
                        case "S":
                            result += '99';
                            break;
                        default:
                            result += ch;
                    }
                }
            }
            return result;
        }

        typeahead_options() {
            var self = this,
                length = 10,
                lookup_item = self.lookup_item.copy(),
                result;
            lookup_item.lookup_field = this,
            result = {
                length: length,
                lookup_item: lookup_item,
                source: function(query, process) {
                    var params = {}
                    self._do_select_value(lookup_item);
                    params.__search = [self.lookup_field, query, consts.FILTER_CONTAINS_ALL];
                    lookup_item.open({limit: length, params: params}, function(item) {
                        var data = [],
                            field = item.field_by_name(self.lookup_field);
                        item.each(function(i) {
                            data.push([i._primary_key_field.value, field.value]);
                        });
                        return process(data);
                    });
                }
            }
            return result;
        }

        get_typeahead_defs($input) {
            var self = this,
                lookup_item,
                items = 10,
                def;

            lookup_item = self.lookup_item.copy(),
            lookup_item.lookup_field = this,
            def = {
                items: items,
                lookup_item: lookup_item,
                field: this,
                source: function(query, process) {
                    var params = {};
                    self._do_select_value(lookup_item);
                    params.__search = [self.lookup_field, query, consts.FILTER_CONTAINS_ALL];
                    lookup_item.open({limit: items, params: params}, function(item) {
                        var data = [],
                            field = item.field_by_name(self.lookup_field);
                        item.each(function(i) {
                            data.push([i._primary_key_field.value, field.value]);
                        });
                        return process(data);
                    });
                },
            }
            return def;
        }

        numeric_field() {
            if (!this.lookup_item && (
                this.data_type === consts.INTEGER ||
                this.data_type === consts.FLOAT ||
                this.data_type === consts.CURRENCY)) {
                return true;
            }
        }

        system_field() {
            if (this.field_name === this.owner._primary_key ||
                this.field_name === this.owner._deleted_flag ||
                this.field_name === this.owner._master_id ||
                this.field_name === this.owner._master_rec_id) {
                return true;
            }
        }

        _check_args(args) {
            var i,
                result = {};
            for (i = 0; i < args.length; i++) {
                result[typeof args[i]] = args[i];
            }
            return result;
        }

        update_controls() {
            var i,
                len,
                args = this._check_args(arguments),
                owner_updating = args['boolean'],
                state = args['number'];

            len = this.controls.length;
            for (i = 0; i < len; i++) {
                this.controls[i].update(state);
            }
            if (!owner_updating && this.owner && this.owner.controls) {
                len = this.owner.controls.length;
                for (i = 0; i < len; i++) {
                    this.owner.controls[i].update_field(this);
                }
            }
        }

        update_control_state(error) {
            for (var i = 0; i < this.controls.length; i++) {
                this.controls[i].error = error;
                this.controls[i].updateState(false);
            }
        }

        type_error() {
            switch (this.data_type) {
                case consts.INTEGER:
                    return language.invalid_int.replace('%s', '');
                case consts.FLOAT:
                    return language.invalid_float.replace('%s', '');
                case consts.CURRENCY:
                    return language.invalid_cur.replace('%s', '');
                case consts.DATE:
                    return language.invalid_date.replace('%s', '');
                case consts.DATE_TIME:
                    return language.invalid_date.replace('%s', '');
                case consts.BOOLEAN:
                    return language.invalid_bool.replace('%s', '');
                default:
                    return language.invalid_value.replace('%s', '');
            }
        }

        valid_char_code(code) {
            var ch = String.fromCharCode(code),
                isDigit = code >= 48 && code <= 57,
                decPoint = ch === '.' || ch === locale.DECIMAL_POINT || ch === locale.MON_DECIMAL_POINT,
                sign = ch === '+' || ch === '-',
                data_type = this.lookup_data_type;
            if (data_type === consts.INTEGER) {
                if (!isDigit && !sign) {
                    return false;
                }
            }
            if (data_type === consts.FLOAT || data_type === consts.CURRENCY) {
                if (!isDigit && !sign && !decPoint) {
                    return false;
                }
            }
            return true;
        }

        hide(update_form) {
            this.controls.forEach(function(control) {
                if (control.hide) {
                    control.hide(update_form);
                }
            })
        }

        show(update_form) {
            this.controls.forEach(function(control) {
                if (control.show) {
                    control.show(update_form);
                }
            })
        }

        round(num, dec) {
            return task.round(num, dec);
        }

        str_to_int(str) {
            return task.str_to_int(str);
        }

        str_to_date(str) {
            return task.str_to_date(str);
        }

        str_to_datetime(str) {
            return task.str_to_datetime(str);
        }

        str_to_float(str) {
            return task.str_to_float(str);
        }

        str_to_cur(str) {
            return task.str_to_cur(str);
        }

        int_to_str(value) {
            return task.int_to_str(value);
        }

        float_to_str(value) {
            return task.float_to_str(value);
        }

        date_to_str(value) {
            return task.date_to_str(value);
        }

        datetime_to_str(value) {
            return task.datetime_to_str(value);
        }

        cur_to_str(value) {
            return task.cur_to_str(value);
        }

        format_string_to_date(value, format) {
            return task.format_string_to_date(value, format);
        }

        format_date_to_string(value, format) {
            return task.format_date_to_string(value, format);
        }

        _do_select_value(lookup_item) {
            if (this.owner && this.owner.on_param_select_value) {
                this.owner.on_param_select_value.call(this.owner, this, lookup_item);
            }
            if (this.owner && this.owner.on_field_select_value) {
                this.owner.on_field_select_value.call(this.owner, this, lookup_item);
            }
            if (this.filter && this.filter.owner.on_filter_select_value) {
                this.filter.owner.on_filter_select_value.call(this.filter.owner, this.filter, lookup_item);
            }
        }

        select_value() {
            var self = this,
                copy = this.lookup_item.copy(),
                on_view_form_closed = copy.on_view_form_closed;
            if (!copy.can_view()) {
                task.alert(task.language.cant_view.replace('%s', copy.item_caption));
                return;
            }
            copy.is_lookup_item = true; //depricated
            copy.lookup_field = this;
            if (this.data_type === consts.KEYS) {
                copy.selections = this.value;
                copy.on_view_form_closed = function(item) {
                    if (on_view_form_closed) {
                        on_view_form_closed(item);
                    }
                    self.value = copy.selections;
                }
            }
            this._do_select_value(copy);
            copy.view();
        }
    }


    class Filter {
        constructor (owner, info) {
            var self = this,
                field;

            this.owner = owner;
            this.set_info(info);
            if (owner) {
                owner.filters.push(this);
                if (!(this.filter_name in owner.filters)) {
                    owner.filters[this.filter_name] = this;
                }
                if (this.field_name) {
                    field = this.owner._field_by_ID(this.field_name);
                    this.field = this.create_field(field);
                    this.field.required = false;
                    if (this.field.lookup_values && (typeof this.field.lookup_values === "number")) {
                        this.field.lookup_values = this.owner.task.lookup_lists[this.field.lookup_values];
                    }
                    this.field.field_help = this.filter_help;
                    this.field.field_placeholder = this.filter_placeholder;
                    this.field.multi_select_all = this.multi_select_all;
                    if (this.filter_type === consts.FILTER_IN || this.filter_type === consts.FILTER_NOT_IN) {
                        this.field.multi_select = true;
                    }
                    if (this.filter_type === consts.FILTER_RANGE) {
                        this.field1 = this.create_field(field);
                        this.field1.field_help = undefined;
                    }
                    if (this.field.data_type === consts.BOOLEAN || this.filter_type === consts.FILTER_ISNULL) {
                        this.field.bool_filter = true;
                        this.field.data_type = consts.INTEGER;
                        this.field.lookup_values = [[null, ''], [0, language.no], [1, language.yes]];
                    }
                }
            }
        }

        create_field(field) {
            var result = new Field();
            result.set_info(field.get_info());
            result._read_only = false;
            result.filter = this;
            result._value = null;
            result._lookup_value = null;
            result.field_kind = consts.FILTER_FIELD;
            return result;
        }

        copy(owner) {
            var result = new Filter(owner, this.get_info());
            return result;
        }

        get_info() {
            var i,
                len = filter_attr.length,
                result = [];
            for (i = 0; i < len; i++) {
                result.push(this[filter_attr[i]]);
            }
            return result;
        }

        set_info(info) {
            if (info) {
                var i,
                    len = filter_attr.length;
                for (i = 0; i < len; i++) {
                    this[filter_attr[i]] = info[i];
                }
            }
        }

        get value() {
            var result;
            if (this.filter_type === consts.FILTER_RANGE) {
                if (this.field.data !== null && this.field1.data !== null) {
                    return [this.field.data, this.field1.data];
                }
                else {
                    return null;
                }
            }
            else {
                return this.field.data;
            }
        }

        set value(value) {
            this.set_value(value);
        }

        set_value(value, lookup_value) {
            var new_value;
            if (this.filter_type === consts.FILTER_RANGE) {
                if (value === null) {
                    this.field.value = null;
                    this.field1.value = null;
                }
                else {
                    this.field.value = value[0];
                    this.field1.value = value[1];
                }
            }
            else if (this.field.bool_filter) {
                if (value !== null) {
                    value = value ? 1 : 0;
                }
                this.field.set_value(value, lookup_value);
            }
            else {
                this.field.set_value(value, lookup_value);
            }
        }

        get lookup_value() {
            return this.field.lookup_value;
        }

        set lookup_value(value) {
            this.field.lookup_value = value
        }

        update(field) {
            var other_field = this.field,
                value;
            if (this.filter_type === consts.FILTER_RANGE) {
                if (field.value !== null) {
                    if (field === this.field) {
                        other_field = this.field1;
                    }
                    if (other_field.data === null) {
                        other_field.value = field.value;
                    }
                }
            }
        }

        check_valid() {
            var error = this.check_value(this.field);
            if (error) {
                throw new Error(error);
            }
        }

        check_value(field) {
            if (this.filter_type === consts.FILTER_RANGE) {
                if (this.field.data === null && this.field1.data !== null ||
                    this.field.data !== null && this.field1.data === null ||
                    this.field.value > this.field1.value) {
                    return language.invalid_range;
                }
            }
        }

        get text() {
            var result = '';
            if (this.visible && this.value != null) {
                result = this.filter_caption + ': ';
                if (this.filter_type === consts.FILTER_RANGE) {
                    result += this.field.display_text + ' - ' + this.field1.display_text;
                } else {
                    result += this.field.display_text;
                }
            }
            return result;
        }

        get_html() {
            var val,
                result = '';
            if (this.visible && this.value != null) {
                result = this.filter_caption + ': ';
                if (this.filter_type === consts.FILTER_RANGE) {
                    val = this.field.display_text + ' - ' + this.field1.display_text;
                } else {
                    val = this.field.display_text;
                }
                result += '<b>' + val + '</b>';
            }
            return result;
        }
    }


    class Param extends Field {
        constructor(owner, info) {
            super(owner, info);
            this.param_name = this.field_name;
            this.param_caption = this.field_caption;
            this.field_size = 0;
            this.report = owner;
            this._value = null;
            this._lookup_value = null;
            this.field_interface = {};
            this.field_kind = consts.PARAM_FIELD;
            if (this.owner[this.param_name] === undefined) {
                this.owner[this.param_name] = this;
            }
        }
    }


    class DBTree {
        constructor(item, container, parent_field, text_field, parent_of_root_value, options) {
            this.init(item, container, parent_field, text_field, parent_of_root_value, options);
        }

        init(item, container, options) {
            var self = this,
                default_options = {
                    id_field: undefined,
                    parent_field: undefined,
                    text_field: undefined,
                    parent_of_root_value: undefined,
                    text_tree: undefined,
                    on_click: undefined,
                    on_dbl_click: undefined
                };
            this.id = item.task.controlId++;
            this.links = {};
            this.item = item;
            this.$container = container;
            this.form = container.closest('.jam-form');
            this.options = $.extend({}, default_options, options);
            this.$element = $('<div class="dbtree ' + this.item.item_name + '" tabindex="0" style="overflow-x:auto; overflow-y:auto;"></div>')
            this.$element.css('position', 'relative');
            this.$element.data('tree', this);
            this.$element.tabindex = 0;
            this.item.controls.push(this);
            this.$element.bind('destroyed', function() {
                self.item.controls.splice(self.item.controls.indexOf(self), 1);
            });
            this.$element.appendTo(this.$container);
            this.height(container.height());
            this.$element.on('focus blur', function(e) {
                self.select_node(self.selected_node, false);
            });
            this.$element.on('keyup', function(e) {
                self.keyup(e);
            })
            this.$element.on('keydown', function(e) {
                self.keydown(e);
            })
            if (item.active && this.$container.width()) {
                this.build();
            }
        }

        form_closing() {
            if (this.form) {
                return this.form.data('_closing');
            }
        }

        height(value) {
            if (value) {
                this.$element.height(value);
            } else {
                return this.$element.height();
            }
        }

        is_focused() {
            return this.$element.get(0) === document.activeElement;
        }

        scroll_into_view() {
            this.select_node(this.selected_node);
        }

        update(state) {
            var recNo,
                self = this,
                row;
            if (this.form_closing()) {
                return;
            }
            switch (state) {
                case consts.UPDATE_OPEN:
                    this.build();
                    break;
                case consts.UPDATE_SCROLLED:
                    this.syncronize();
                    break;
                case consts.UPDATE_CONTROLS:
                    this.build();
                    break;
                case consts.UPDATE_CLOSE:
                    this.$element.empty();
                    break;
            }
        }

        keydown(e) {
            var self = this,
                $li,
                code = e.keyCode || e.which;
            if (this.selected_node && !e.ctrlKey && !e.shiftKey) {
                switch (code) {
                    case 13: //return
                        e.preventDefault();
                        this.toggle_expanded(this.selected_node);
                        break;
                    case 38: //up
                        e.preventDefault();
                        $li = this.selected_node.prev();
                        if ($li.length) {
                            this.select_node($li);
                        } else {
                            $li = this.selected_node.parent().parent()
                            if ($li.length && $li.prop("tagName") === "LI") {
                                this.select_node($li);
                            }
                        }
                        break;
                    case 40: //down
                        e.preventDefault();
                        if (this.selected_node.hasClass('parent') && !this.selected_node.hasClass('collapsed')) {
                            $li = this.selected_node.find('ul:first li:first')
                            if ($li.length) {
                                this.select_node($li);
                            }
                        } else {
                            $li = this.selected_node.next();
                            if ($li.length) {
                                this.select_node($li);
                            } else {
                                $li = this.selected_node.find('ul:first li:first')
                                if ($li.length) {
                                    this.select_node($li);
                                }
                            }
                        }
                        break;
                }
            }
        }

        keyup(e) {
            var self = this,
                code = (e.keyCode ? e.keyCode : e.which);
            if (!e.ctrlKey && !e.shiftKey) {
                switch (code) {
                    case 13:
                        break;
                    case 38:
                        break;
                    case 40:
                        break;
                }
            }
        }

        build_child_nodes(tree, nodes) {
            var i = 0,
                len = nodes.length,
                node,
                id,
                text,
                rec,
                bullet,
                parent_class,
                collapsed_class,
                li,
                ul,
                info,
                children,
                child_len;
            for (i = 0; i < len; i++) {
                node = nodes[i];
                id = node.id;
                text = node.text;
                rec = node.rec;
                bullet = '<span class="empty-bullet"></span>',
                    parent_class = "",
                    collapsed_class = "",
                    children = this.child_nodes[id + ''];
                if (children && children.length) {
                    bullet = '<i class="icon-chevron-right bullet"></i>'
                    parent_class = ' parent';
                    collapsed_class = 'collapsed';
                }
                li = '<li class="' + collapsed_class + parent_class + '" style="list-style: none" data-rec="' + rec + '">' +
                    '<div><span class="tree-bullet">' + bullet + '</span>' +
                    '<span class="tree-text">' + text + '<span></div>';
                tree += li;
                if (children && children.length) {
                    tree += '<ul style="display: none">';
                    tree = this.build_child_nodes(tree, children);
                    tree += '</ul>';
                }
                tree += '</li>';
                tree += '</li>';
            }
            return tree
        }

        collect_nodes(clone) {
            var id_field = clone[this.options.id_field],
                parent_field = clone[this.options.parent_field],
                text_field = clone[this.options.text_field],
                array;
            this.child_nodes = {};
            clone.first();
            while (!clone.eof()) {
                array = this.child_nodes[parent_field.value + ''];
                if (array === undefined) {
                    array = []
                    this.child_nodes[parent_field.value + ''] = array;
                }
                array.push({
                    'id': id_field.value,
                    'text': text_field.display_text,
                    'rec': clone.rec_no
                });
                clone.next();
            }
        }

        build() {
            var self = this,
                clone = this.item.clone(),
                tree = '<ul>',
                i,
                len,
                rec,
                info,
                $li,
                $lis,
                nodes;
            clone.on_field_get_text = this.item.on_field_get_text;
            this.collect_nodes(clone);
            this.$element.empty();
            nodes = this.child_nodes[this.options.parent_of_root_value + ''];
            if (nodes && nodes.length) {
                tree = this.build_child_nodes(tree, nodes);
            }
            tree += '</ul>'
            this.$element.append($(tree));
            $lis = this.$element.find('li');
            len = $lis.length;
            for (i = 0; i < len; i++) {
                $li = $lis.eq(i);
                rec = $li.data('rec');
                clone.rec_no = rec;
                this.item._cur_row = rec;
                $li.data("record", clone._dataset[rec]);
                this.links[clone.rec_no] = $li.get(0);
                if (this.options.node_callback) {
                    this.options.node_callback($li, this.item);
                }
            }
            this.select_node($lis.eq(0));

            this.$element.off('click', 'li.parent > div span.tree-bullet');
            this.$element.on('click', 'li.parent > div span.tree-bullet', function(e) {
                var $span = $(this),
                    $li = $span.parent().parent(),
                    $ul;
                self.toggle_expanded($li);
                e.preventDefault();
                e.stopPropagation();
            });
            this.$element.off('click', 'li > div span.tree-text');
            this.$element.on('click', 'li > div span.tree-text', function(e) {
                var $li = $(this).parent().parent();
                self.select_node($li);
            });
        }

        toggle_expanded($li) {
            var $span = $li.find('div:first span.tree-bullet'),
                $ul;
            if ($li.hasClass('parent')) {
                $ul = $li.find('ul:first'),
                    $li.toggleClass('collapsed');
                if ($li.hasClass('collapsed')) {
                    $span.html('<i class="icon-chevron-right bullet"></i>');
                } else {
                    $span.html('<i class="icon-chevron-down bullet"></i>');
                }
                $ul.slideToggle(0);
            }
        }

        expand($li) {
            if ($li.hasClass('parent') && $li.hasClass('collapsed')) {
                this.toggle_expanded($li);
            }
            $li = $li.parent().parent()
            if ($li.prop("tagName") === "LI") {
                this.expand($li);
            }
        }

        collapse($li) {
            if ($li.hasClass('parent') && !$li.hasClass('collapsed')) {
                this.toggle_expanded($li);
            }
        }

        select_node($li, update_node) {
            var self = this,
                $parent,
                rec;
            if (update_node === undefined) {
                update_node = true;
            }
            if (this.selected_node) {
                this.selected_node.removeClass('selected selected-focused');
            }
            if ($li && (!this.selected_node || $li.get(0) !== this.selected_node.get(0))) {
                this.selected_node = $li;
                rec = this.item._dataset.indexOf($li.data("record"));
                if (rec !== this.item.rec_no) {
                    this.item.rec_no = rec;
                }
                $parent = this.selected_node.parent().parent()
                if ($parent.prop("tagName") === "LI") {
                    this.expand($parent);
                }
            }
            if (this.is_focused()) {
                this.selected_node.addClass('selected-focused');
            } else {
                this.selected_node.addClass('selected');
            }
            if (update_node) {
                this.update_selected_node(this.selected_node);
            }
        }

        update_selected_node($li) {
            var containerTop,
                containerBottom,
                elemTop,
                elemBottom,
                parent;
            if ($li.length) {
                containerTop = this.$element.scrollTop();
                containerBottom = containerTop + this.$element.height();
                elemTop = $li.get(0).offsetTop;
                elemBottom = elemTop + $li.height();
                if (elemTop < containerTop) {
                    this.$element.scrollTop(elemTop);
                } else if (elemBottom > containerBottom) {
                    this.$element.scrollTop(elemBottom - this.$element.height());
                }
            }
        }

        update_field() {
        }

        syncronize() {
            var info,
                li;
            if (this.item.record_count()) {
                try {
                    li = this.links[this.item.rec_no]
                    if (li) {
                        this.select_node($(li));
                    }
                } catch (e) {
                    console.error(e);
                }
            }
        }

        changed() {}
    }


    class DBTable {
        constructor(item, container, options, master_table) {
            this.init(item, container, options, master_table);
        }

        init(item, container, options, master_table) {
            var self = this;

            if (!container.length) {
                return;
            }
            this.item = item;
            this.item._page_changed = false;
            this.id = item.task._grid_id++;
            this.datasource = [];
            this.$container = container;
            this.form = container.closest('.jam-form');
            this.$container.css('position', 'relative');
            this.master_table = master_table;
            this.is_mac = navigator.platform.toLowerCase().indexOf('mac') + 1;

            this.edit_mode = false;
            this._editable_fields = [];
            this._sorted_fields = [];
            this._multiple_sort = false;
            this.page = 0;
            this.record_count = 0;
            this.cell_widths = {};
            this.scrollLeft = 0;

            this.init_options(options);
            this.init_selections();
            this.init_fields();

            this.$element = $('<div class="dbtable">');

            this.$element.addClass(item.item_name);
            this.$element.append($('<div class="table-container" style="overflow-x:auto;">'));
            this.$element.append($('<div class="paginator text-center">'));

            if (this.options.table_class) {
                this.$element.addClass(this.options.table_class);
            }
            this.$element.data('dbtable', this);
            this.item.controls.push(this);

            this.resize_id = 'resize.dbtable-' + this.item.item_name + this.id;
            if (this.master_table) {
                this.$element.addClass('freezed');
                this.resize_id = 'resize.dbtable.freezed-' + this.item.item_name + this.id;
            }
            $(window).on(this.resize_id, function() {
                self.resize();
            });
            this.$element.bind('destroyed', function() {
                $(window).off(self.resize_id);
                self.item.controls.splice(self.item.controls.indexOf(self), 1);
            });

            this.$container.empty();
            this.$element.appendTo(this.$container);
            this.create_table();
            this.create_pager();

            this.sync_freezed();

            if (item.active) {
                setTimeout(function() { self.do_after_open() }, 0);
            }
        }

        init_options(options) {
            var default_options = {
                table_class: undefined,
                multiselect: false,
                height: undefined,
                exact_height: false,
                row_count: undefined,
                fields: [],
                column_width: {},
                title_line_count: 1,
                row_line_count: 1,
                expand_selected_row: 0,
                selections: undefined,
                select_all: true,
                selection_limit: undefined,
                tabindex: 0,
                striped: true,
                dblclick_edit: true,
                on_click: undefined,
                on_dblclick: undefined,
                on_pagecount_update: undefined,
                on_page_changed: undefined,
                editable: false,
                editable_fields: undefined,
                keypress_edit: true,
                selected_field: undefined,
                append_on_lastrow_keydown: false,
                sortable: false,
                sort_fields: {},
                sort_add_primary: false,
                row_callback: undefined,
                title_callback: undefined,
                summary_fields: [],
                show_footer: undefined,
                show_paginator: true,
                show_scrollbar: false,
                paginator_container: undefined,
                freeze_count: 0,
                exact_height: false,
                show_hints: true,
                hint_fields: undefined,
                auto_page_scroll: true
            };

            this.options = $.extend(true, {}, default_options, this.item.table_options);
            this.options = $.extend({}, this.options, options);
            if (!this.options.height && !this.options.row_count) {
                this.options.height = 480;
            }
            if (this.options.row_line_count < 1) {
                this.options.row_line_count = 0;
            }
            if (!this.options.row_line_count && !this.options.row_count) {
                this.options.row_count = 10;
            }
            if (options && options.title_word_wrap) {
                this.options.title_line_count = 0;
            }
            else if (this.options.title_line_count < 0 || this.options.title_line_count === undefined) {
                this.options.title_line_count = 1;
            }
            if (this.item.master) {
                this.options.select_all = false;
            }
            if (this.options.summary_fields && this.options.summary_fields.length) {
                this.options.show_footer = true
            }
            if (this.options.editable_fields && this.options.editable_fields.length) {
                this.options.editable = true;
            }
            if (this.options.sort_fields && this.options.sort_fields.length) {
                this.options.sortable = true;
            }

            this.on_dblclick = this.options.on_dblclick;
        }

        resize() {
            var self = this;
            clearTimeout(this.timeOut);
            self.timeOut = setTimeout(
                function() {
                    if (self.master_table && !self.master_table.freezed_table) {
                        return;
                    }
                    self.build();
                    self.sync_freezed();
                },
                100
            );
        }

        get editable_fields() {
            var i,
                field,
                result = [];
            for (i = 0; i < this._editable_fields.length; i++) {
                field = this._editable_fields[i];
                if (!field.read_only && !field.master_field) {
                    result.push(field)
                }
            }
            if (this.freezed_table) {
                let index;
                for (i = 0; i < this.options.freeze_count; i++) {
                    index = result.indexOf(this.fields[i]);
                    if (index !== -1) {
                        result.splice(index, 1);
                    }
                }
            }
            return result;
         }

        init_fields() {
            var i = 0,
                len,
                field,
                fields = [];
            this.fields = [];
            if (this.options.fields.length) {
                fields = this.options.fields
            } else if (this.item.view_options.fields && this.item.view_options.fields.length) {
                fields = this.item.view_options.fields;
            } else if (!fields.length) {
                this.item.each_field(function(f) {
                    if (f.field_name !== f.owner._primary_key && f.field_name !== f.owner._deleted_flag) {
                        fields.push(f.field_name);
                    }
                });
            }
            if (fields.length) {
                len = fields.length;
                for (i = 0; i < len; i++) {
                    field = this.item.field_by_name(fields[i]);
                    if (field) {
                        this.fields.push(field);
                    }
                }
            }

            this._editable_fields = [];
            if (this.options.editable_fields) {
                len = this.fields.length;
                for (i = 0; i < len; i++) {
                    if (this.options.editable_fields.indexOf(this.fields[i].field_name) !== -1) {
                        this._editable_fields.push(this.fields[i]);
                    }
                }
            } else {
                len = this.fields.length;
                for (i = 0; i < len; i++) {
                    if (!this.fields[i].read_only) {
                        this._editable_fields.push(this.fields[i]);
                    }
                }
            }
            this.init_selected_field();
            this.colspan = this.fields.length;
            if (this.options.multiselect) {
                this.colspan += 1;
            }
         }

        can_edit() {
            if (this.item.read_only) {
                return false;
            }
            if (this.item.master && !this.item.master.is_changing()) {
                return false;
            }
            return this.options.editable;
         }

        get_freezed_fields(len) {
            var i,
                result = [];
            if (!len) {
                len = this.options.freeze_count;
            }
            for (i = 0; i < len; i++) {
                result.push(this.fields[i].field_name);
            }
            return result;
         }

        create_freezed_table() {
            var i,
                options,
                container;
            options = $.extend({}, this.options)
            options.show_paginator = false;
            options.fields = [];
            options.freeze_count = 0;
            options.fields = this.get_freezed_fields();
            container = $('<div>')
            this.freezed_table = new DBTable(this.item, container, options, this)
            this.freezed_table.$element.detach()
            this.freezed_table.$element.css('position', 'absolute');
            this.freezed_table.$element.css('left', '0');
            this.freezed_table.$element.css('top', '0');
            this.freezed_table.$element.css('overflow', 'hidden');
            this.freezed_table.$table_container.css('overflow', 'hidden');
            this.freezed_table.$outer_table.css('overflow', 'hidden');
            this.freezed_table.$overlay_div.css('overflow', 'hidden');

            this.freezed_table.$container = this.$container;
            this.$container.append(this.freezed_table.$element);
         }

        delete_freezed_table() {
            this.freezed_table.$element.remove();
            delete this.freezed_table
            this.freezed_table = undefined;
         }

        sync_freezed() {
            var i,
                col,
                $th,
                $td,
                $tf,
                cell_width,
                field_name,
                fields1,
                fields2,
                valid_fields,
                scroll_left,
                title_height,
                width;
            if (this.options.freeze_count) {
                if (this.freezed_table) {
                    fields1 = this.get_freezed_fields();
                    fields2 = this.freezed_table.get_freezed_fields(this.options.freeze_count);
                    valid_fields = fields1.length === fields2.length;
                    if (valid_fields) {
                        for (i = 0; i < fields1.length; i++) {
                            if (fields1[i] !== fields2[i]) {
                                valid_fields = false;
                                break;
                            }
                        }
                    }
                    if (!valid_fields) {
                        this.delete_freezed_table();
                    }
                }
                if (this.$overlay_div.get(0).scrollWidth > this.$element.innerWidth()) {
                    if (!this.freezed_table) {
                        this.create_freezed_table();
                    }
                    col = this.options.freeze_count - 1;
                    if (this.options.multiselect) {
                        col += 1;
                    }
                    $th = this.$head.find('th').eq(col);
                    width = ($th.position().left + $th.outerWidth(true) + 2);

                    this.freezed_table.$element.width(width);
                }
                else if (this.freezed_table) {
                    this.delete_freezed_table();
                }
            }
            else {
                if (this.master_table) {
                    this.$head.height(this.master_table.$head.height());
                    this.$foot.height(this.master_table.$foot.height());
                    for (i = 0; i < this.fields.length; i++) {
                        field_name = this.fields[i].field_name;
                        cell_width = this.master_table.$head.find('th.' + field_name).outerWidth();
                         this.set_сell_width(field_name, cell_width);
                    }
                    this.sync_col_width();
                }
            }
         }

        init_selections() {
            var value;
            if (this.options.multiselect && !this.item.selections) {
                this.item.selections = [];
            }
            //~ if (this.item.selections && this.item.selections.length) {
            if (this.item.selections) {
                this.options.multiselect = true;
            }
            if (this.options.selections && this.options.selections.length) {
                this.item.selections = this.options.selections;
                this.options.multiselect = true;
            }
            if (this.item.lookup_field && this.item.lookup_field.multi_select) {
                value = this.item.lookup_field.data;
                this.options.select_all = this.item.lookup_field.multi_select_all;
                if (value instanceof Array) {
                    this.item.selections = value;
                }
                else {
                    this.item.selections = [];
                }
                this.options.multiselect = true;
            }
            this.item.select_all = this.options.select_all;
         }

        selections_update_selected() {
            var sel_count = this.$element.find('th .multi-select .sel-count');
            if (this.options.multiselect) {
                sel_count.text(this.item.selections.length);
                if (this.item._show_selected) {
                    sel_count.addClass('selected-shown')
                }
                else {
                    sel_count.removeClass('selected-shown')
                }
                if (this.item.lookup_field && this.item.lookup_field.multi_select) {
                    if (this.item.rec_count && this.item.selections.length === 1 &&
                        this.item._primary_key_field && this.item.selections.indexOf(this.item._primary_key_field.value) !== -1) {
                        this.item.lookup_field.set_value(this.item.selections, this.item.field_by_name(this.item.lookup_field.lookup_field).display_text);
                    }
                    else {
                        this.item.lookup_field.set_value(this.item.selections, '');
                    }
                }
            }
         }

        selections_get_selected() {
            return this.item.selections.indexOf(this.item._primary_key_field.value) !== -1;
         }

        selections_can_change(value) {
            var valid = true;
            if (value && this.options.selection_limit) {
                valid = (this.options.selection_limit &&
                    this.options.selection_limit >= this.item.selections.length + 1);
                if (!valid) {
                    this.item.warning(language.selection_limit_exceeded.replace('%s', this.options.selection_limit))
                }
            }
            return valid;
         }

        selections_set_selected(value) {
            var self = this,
                result = value,
                index,
                clone,
                selected = false;
            if (this.selections_can_change(value)) {
                if (value) {
                    this.item.selections.add(this.item._primary_key_field.value);
                    selected = true;
                } else {
                    this.item.selections.remove(this.item._primary_key_field.value)
                    clone = this.item.clone();
                    clone.each(function(c) {
                        if (self.item.selections.indexOf(c._primary_key_field.value) !== -1) {
                            selected = true;
                            return false;
                        }
                    })
                }
                this.selections_update_selected();
                this.$element.find('input.multi-select-header').prop('checked', selected);
            }
            else {
                result = false;
            }
            return result;
         }

        selections_get_all_selected() {
            var self = this,
                clone = this.item.clone(),
                result = false;
            clone.each(function(c) {
                if (self.item.selections.indexOf(c._primary_key_field.value) !== -1) {
                    result = true;
                    return false;
                }
            })
            return result;
         }

        selections_set_all_selected_ex(value) {
            var self = this,
                i,
                field,
                fields = [],
                limit,
                exceeded,
                mess,
                copy,
                clone;
            if (this.options.select_all) {
                copy = this.item.copy({handlers: false})
                copy._where_list = this.item._open_params.__filters;
                copy._order_by_list = this.item._open_params.__order;
                if (this.options.selection_limit) {
                    limit = this.options.selection_limit;// - this.item.selections.length;
                }
                fields.push(copy._primary_key);
                for (i = 0; i < copy._where_list.length; i++) {
                    field = this.item.field_by_name(copy._where_list[i][0]);
                    if (field.lookup_item) {
                        fields.push(field.field_name);
                    }
                }
                for (i = 0; i < copy._order_by_list.length; i++) {
                    field = this.item.field_by_name(copy._order_by_list[i][0]);
                    if (fields.indexOf(field.field_name) === -1) {
                        fields.push(field.field_name);
                    }
                }
                copy.open({fields: fields, limit: limit}, function() {
                    var dict = {}, sel = [];
                    for (i = 0; i < self.item.selections.length; i++) {
                        dict[self.item.selections[i]] = true;
                    }
                    self.item.selections.length = 0;
                    copy.each(function(c) {
                        if (value) {
                            dict[c._primary_key_field.value] = true;
                        }
                        else {
                            delete dict[c._primary_key_field.value];
                        }
                    });
                    for (var id in dict) {
                        sel.push(parseInt(id, 10))
                    }
                    self.item.selections = sel;
                    self.$table.find('td input.multi-select').prop('checked', value);
                    self.$element.find('input.multi-select-header').prop('checked',
                        self.selections_get_all_selected());
                    self.selections_update_selected();
                })
            }
         }

        selections_set_all_selected(value) {
            var self = this,
                i,
                field,
                fields = [],
                limit,
                exceeded,
                mess,
                copy,
                clone;
            clone = this.item.clone();
            clone.each(function(c) {
                var index;
                if (self.selections_can_change(value)) {
                    if (value) {
                        self.item.selections.add(c._primary_key_field.value);
                    } else {
                        self.item.selections.remove(c._primary_key_field.value);
                    }
                }
                else {
                    exceeded = true;
                    return false;
                }
            })
            if (exceeded) {
                this.build();
            }
            else {
                self.$table.find('td input.multi-select').prop('checked', value);
            }
            this.selections_update_selected();
         }

        initKeyboardEvents() {
            var self = this,
                timeout;
            this.$table.on('keydown', function(e) {
                let code = (e.keyCode ? e.keyCode : e.which);
                if (self.selected_field && (code === 37 || code === 39)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                clearTimeout(timeout);
                timeout = setTimeout( function() { self.keydown(e) }, 10 );
            });

            this.$table.on('keyup', function(e) {
                clearTimeout(timeout);
                timeout = setTimeout( function() { self.keyup(e) }, 10 );
            });

            this.$table.on('keypress', function(e) {
                self.keypress(e);
            });
         }

        create_table() {
            var self = this,
                $doc = $(document),
                $selection,
                $th,
                $td,
                $thNext,
                delta = 0,
                mouseX;
            this.colspan = this.fields.length;
            if (this.options.multiselect) {
                this.colspan += 1;
            }
            this.$element.find('.table-container').append($(
                '<table class="outer-table table table-condensed table-bordered" style="width: 100%;">' +
                '   <thead>' +
                '       <tr><th>&nbsp</th></tr>' +
                '   </thead>' +
                '   <tr>' +
                '       <td id="top-td" style="padding: 0; border: 0;" colspan=' + this.colspan + '>' +
                '           <div class="overlay-div" style="position: relative; width: 100%; height: 100%; overflow-y: auto; overflow-x: hidden;">' +
                '               <div class="scroll-div" style="position: relative; height: auto;">' +
                '                   <table class="inner-table table table-condensed table-bordered" style="position: absolute; width: 100%">' +
                '                       <tbody></tbody>' +
                '                   </table>' +
                '               </div>' +
                '           </div>' +
                '       </td>' +
                '   </tr>' +
                '   <tfoot class="outer-table">' +
                '       <tr><th>&nbsp</th></tr>' +
                '   </tfoot>' +
                '</table>'));
            this.$table_container = this.$element.find(".table-container")
            this.$outer_table = this.$element.find("table.outer-table")
            this.$overlay_div = this.$element.find('div.overlay-div');
            this.$scroll_div = this.$element.find('div.scroll-div');
            this.$table = this.$element.find("table.inner-table");
            this.$head = this.$element.find("table.outer-table thead tr:first");
            this.$foot = this.$element.find("table.outer-table tfoot tr:first");
            this.is_modal = this.$element.closest('.modal').length > 0;

            if (this.item._paginate && !this.options.show_scrollbar) {
                this.$overlay_div.css('overflow-y', 'hidden');
            }
            if (this.options.row_count && !this.options.row_line_count) {
                this.$table.css('position', 'relative');
            }

            this.$overlay_div.scroll(function(e) {
                self.scroll(e);
            });

            this.$overlay_div.on('mousewheel', function(e) {
                e.preventDefault();
            });

            this.$overlay_div.on('keydown', function(e) {
                if ([32, 33, 34, 35, 36, 38, 40].indexOf(e.keyCode) > -1) {
                    if (!self.editor) {
                        e.preventDefault();
                    }
                }
            });

            this.$outer_table.css("margin", 0)

            this.$table.css("outline", "none")
                .css("margin", 0)
                .css("border", 0)

            if (this.options.striped) {
                this.$element.addClass("striped");
            }

            this.$table.on('mousedown dblclick', 'td', function(e) {
                var td = $(this);
                if (this.nodeName !== 'TD') {
                    td = $(this).closest('td');
                }
                if (!(self.editing && td.find('input').length)) {
                    e.preventDefault();
                    //~ e.stopPropagation();
                    self.clicked(e, td);
                }
            });

            this.$element.on('mousewheel DOMMouseScroll', 'div.overlay-div, table.inner-table', function(e){
                e.stopPropagation();
                if (e.originalEvent.wheelDelta > 0 || e.originalEvent.detail < 0) {
                    self.prior_record();
                }
                else {
                    self.next_record();
                }
            });

            this.$table.on('click', 'td', function(e) {
                if (self.options.on_click) {
                    self.options.on_click.call(self.item, self.item);
                }
            });

            this.$table.on('mouseenter mouseup', 'td div', function() {
                var $this = $(this),
                    $td = $this.parent(),
                    field_name = $td.data('field_name'),
                    tt = $this.data('tooltip'),
                    show,
                    placement = 'right',
                    container;
                show = self.options.show_hints;
                if ($.isArray(self.options.hint_fields)) {
                     show = $.inArray(field_name, self.options.hint_fields) > -1;
                }
                if (show) {
                    self.remove_tooltip();
                    container = self.$element[0];
                    if (Math.abs(this.offsetHeight - this.scrollHeight) > 1 ||
                        Math.abs(this.offsetWidth - this.scrollWidth) > 1) {
                        let table_width = self.$table.width();
                        if (self.master_table) {
                            table_width = self.master_table.$table.width();
                            container = self.master_table.$element[0];
                        }
                        if (table_width - ($this.offset().left + $this.width()) < 200) {
                            placement = 'left';
                        }
                        $td.tooltip({
                                'placement': placement,
                                'container': container,
                                //~ 'container': 'body',
                                'title': $this.text()
                            })
                            .on('hide hidden show shown', function(e) {
                                if (e.target === $this.get(0)) {
                                    e.stopPropagation()
                                }
                            })
                            .eq(0).tooltip('show');
                        try {
                            $td.data('tooltip').$tip.addClass('table-tooltip');
                        }
                        catch (e) {}
                    }
                }
            });

            this.$table.on('mousedown', 'td input.multi-select', function(e) {
                var $this = $(this),
                    checked = $this.is(':checked');
                self.clicked(e, $this.closest('td'));
                self.selections_set_selected(!checked);
                $this.prop('checked', self.selections_get_selected());
                if (e.shiftKey && self.prev_selected_rec_no !== undefined) {
                    let sels = [],
                        clone = self.item.clone(),
                        min = self.prev_selected_rec_no,
                        max = self.item.rec_no;
                    if (self.prev_selected_rec_no > self.item.rec_no) {
                        min = self.item.rec_no;
                        max = self.prev_selected_rec_no;
                    }
                    while (min < max) {
                        min += 1;
                        clone.rec_no = min;
                        if ($this.is(':checked')) {
                            self.item.selections.add(clone._primary_key_field.value);
                        }
                        else {
                            self.item.selections.remove(clone._primary_key_field.value);
                        }
                    }
                    self.refresh();
                }
                self.prev_selected_rec_no = self.item.rec_no;
            });

            this.$table.on('click', 'td input.multi-select', function(e) {
                var $this = $(this);
                e.stopPropagation();
                e.preventDefault();
                $this.prop('checked', self.selections_get_selected());
            });

            this.$element.on('click', 'input.multi-select-header', function(e) {
                self.selections_set_all_selected($(this).is(':checked'));
            });

            this.$table.attr("tabindex", this.options.tabindex);

            this.initKeyboardEvents();

            this.$element.on('mousemove.table-title', 'table.outer-table thead tr:first th', function(e) {
                var $this = $(this),
                    field_name = $this.data('field_name'),
                    lastCell = self.$element.find("thead tr:first th:last").get(0);
                if ($this.outerWidth() - e.offsetX < 8 && !mouseX && (this !== lastCell || self.master_table)) {
                    $this.css('cursor', 'col-resize');
                } else if (self.options.sortable && //!self.item.master &&
                    (!self.options.sort_fields.length || self.options.sort_fields.indexOf(field_name) !== -1)) {
                    $this.css('cursor', 'pointer');
                } else {
                    $this.css('cursor', 'default');
                }
            });

            function captureMouseMove(e) {
                var newDelta = delta + e.screenX - mouseX,
                    left = parseInt($selection.css("left"), 10);
                if (mouseX) {
                    e.preventDefault();
                    if (newDelta > -($th.innerWidth() - 30)) {
                        delta = newDelta;
                        $selection.css('left', left + e.screenX - mouseX);
                    }
                    mouseX = e.screenX;
                }
            }

            function change_field_width($title, delta) {
                var field_name = $title.data('field_name');
                self.change_field_width(field_name, delta);
            }

            function release_mouse_move(e) {
                var field_name,
                    $td,
                    $tf,
                    cell_width;
                $doc.off("mousemove.table-title");
                $doc.off("mouseup.table-title");

                change_field_width($th, delta);

                mouseX = undefined;
                $selection.remove()
            }

            this.$element.on('mousedown.table-title', 'table.outer-table thead tr:first th', function(e) {
                var $this = $(this),
                    index,
                    lastCell,
                    field_name = $this.data('field_name'),
                    cur_field_name,
                    new_fields = [],
                    index,
                    desc = false,
                    next_field_name,
                    field,
                    parent,
                    top,
                    left,
                    sorted_fields;
                lastCell = self.$element.find("thead tr:first th:last").get(0);
                if ($this.outerWidth() - e.offsetX < 8 && (this !== lastCell || self.master_table)) {
                    $this.css('cursor', 'default');
                    mouseX = e.screenX;
                    $th = $this;
                    index = self.fields.indexOf(self.item.field_by_name(field_name))
                    delta = 0;
                    $doc.on("mousemove.table-title", captureMouseMove);
                    $doc.on("mouseup.table-title", release_mouse_move);
                    parent = self.$container.closest('.modal');
                    if (parent.length) {
                        left = $this.offset().left - parent.offset().left;
                        top = self.$element.offset().top - parent.offset().top;
                    }
                    else {
                        parent = $('body');
                        left = $this.offset().left;
                        top = self.$element.offset().top;
                    }
                    $selection = $('<div>')
                        .addClass('selection-box')
                        .css({
                            'width': 0,
                            'height': self.$outer_table.find('thead').innerHeight() + self.$overlay_div.innerHeight(),
                            'left': left + $this.outerWidth(),
                            'top': top
                        });

                    $selection.appendTo(parent);
                } else if (field_name && self.options.sortable &&
                    (!self.options.sort_fields.length || self.options.sort_fields.indexOf(field_name) !== -1)) {

                    if (e.ctrlKey) {
                        if (!self._multiple_sort) {
                            self._multiple_sort = true;
                        }
                    } else {
                        if (self._multiple_sort) {
                            self._sorted_fields = [];
                            self._multiple_sort = false;
                        }
                    }
                    sorted_fields = self._sorted_fields.slice();
                    if (self._multiple_sort) {
                        index = -1;
                        for (var i = 0; i < sorted_fields.length; i++) {
                            if (sorted_fields[i][0] === field_name) {
                                index = i;
                                break;
                            }
                        }
                        if (index === -1) {
                            sorted_fields.push([field_name, false])
                        } else {
                            sorted_fields[index][1] = !sorted_fields[index][1];
                        }
                    } else {
                        if (sorted_fields.length && sorted_fields[0][0] === field_name) {
                            sorted_fields[0][1] = !sorted_fields[0][1];
                        } else {
                            sorted_fields = [
                                [field_name, false]
                            ];
                        }
                    }
                    self._sorted_fields = sorted_fields.slice();
                    if (!self.item._paginate) {
                        self.item._sort(self._sorted_fields);
                    } else {
                        if (self.options.sort_add_primary) {
                            field = self.item[self.item._primary_key]
                            desc = self._sorted_fields[self._sorted_fields.length - 1][1]
                            self._sorted_fields.push([field.field_name, desc]);
                        }
                        self.item._open_params.__order = self._sorted_fields;
                        self.item.open({
                            params: self.item._open_params,
                            offset: 0
                        }, true);
                    }
                }
            });

            this.$table.focus(function(e) {
                if (self.master_table) {
                    self.master_table.close_editor();
                }
                if (self.freezed_table) {
                    self.freezed_table.close_editor();
                }
                self.syncronize(true);
            });

            this.$table.blur(function(e) {
                self.syncronize(true);
            });

            this.fill_footer();
            this.calculate();
        }

        change_field_width(field_name, delta) {
            var cell_width;
            cell_width = this.get_cell_width(field_name) + delta;

            this.set_сell_width(field_name, cell_width);

            if (this.master_table) {
                this.$element.width(this.$element.width() + delta)
                this.master_table.set_сell_width(field_name, cell_width);
                this.master_table.sync_col_width();
                this.master_table.sync_freezed();
            }
            else {
                this.sync_col_width(delta > 0);
            }
            this.sync_freezed();
        }

        remove_tooltip() {
            try {
                $('body').find('.tooltip.table-tooltip').remove();
            }
            catch (e) {}
        }

        calculate() {
            var self = this,
                i,
                row_line_count,
                $element,
                $table,
                row,
                $td,
                margin,
                fix,
                row_height,
                elementHeight,
                selected_row_height,
                overlay_div_height;
            if (this.options.row_count && !this.options.row_line_count) {
                this.item.paginate = true;
                this.row_count = this.options.row_count;
                this.item._limit = this.row_count;
                return;
            }
            row_line_count  = this.options.row_line_count
            if (!row_line_count) {
                row_line_count = 1;
            }
            if (this.master_table) {
                this.row_count = this.master_table.row_count;
                this.text_height = this.master_table.text_height;
                this.row_height = this.master_table.row_height;
                this.selected_row_height = this.master_table.selected_row_height;

                this.height(this.master_table.height());
                this.$overlay_div.height(this.master_table.$overlay_div.height());
                return;
            }
            $element = this.$element.clone()
                .css("float", "left")
                .css("position", "absolute")
                .css("top", 100);
                //~ .css("top", -1000);
            $element.width(this.$container.width());
            if (!$element.width()) {
                $element.width($('body').width());
            }
            $('body').append($element);
            this.fill_title($element);
            this.fill_footer($element);
            this.create_pager($element)
            $table = $element.find("table.inner-table");
            if (this.item.selections && !this.item.master) {
                row = '<tr><td><div><input type="checkbox"></div></td><td><div>W</div></td></tr>';
            } else {
                row = '<tr><td><div>W</div></td></tr>';
            }
            for (i = 0; i < 10; i++) {
                $table.append(row);
            }
            $element.find('th > div > p').css('margin', 0);
            //~ $('body').append($element);
            $td = $table.find('tr:last td');
            this.text_height = $td.find('div').height();
            row_height = $td.outerHeight(true);
            margin = row_height * 10 - $table.innerHeight();
            fix = Math.abs(Math.abs(margin) - 10); // fix for firebird
            if (fix && fix < 5 && margin < 0) {
                row_height += Math.round(fix);
                margin = row_height * 10 - $table.innerHeight();
            }
            this.row_margin = margin;
            this.row_height = row_height + (row_line_count - 1) * this.text_height;
            this.selected_row_height = 0;
            elementHeight = $element.outerHeight();
            overlay_div_height = $element.find('div.overlay-div').innerHeight();
            $element.remove();
            if (this.options.expand_selected_row) {
                this.selected_row_height = row_height + (this.options.expand_selected_row - 1) * this.text_height;
            }
            this.$overlay_div.height(this.options.height - (elementHeight - overlay_div_height) - $element.find('.paginator').outerHeight(true));
            if (this.options.row_count) {
                this.row_count = this.options.row_count;
                this.$overlay_div.height(this.row_height * this.options.row_count);
                if (this.options.expand_selected_row) {
                    this.$overlay_div.height(this.row_height * (this.options.row_count - 1) + this.selected_row_height + margin);
                }
            }
            else {
                this.calc_row_count();
            }
            if (this.item._paginate) {
                this.item._limit = this.row_count;
            }
            else if (this.form.hasClass('modal')) {
                setTimeout(
                    function() {
                        if (self.row_count !== self.calc_row_count()) {
                            self.field_width_updated = false;
                            self.datasource = [];
                            self.refresh();
                        }
                    },
                    300
                );
            }
        }

        calc_row_count() {
            if (this.master_table) {
                return this.master_table.row_count;
            }
            var overlay_div_height = this.$overlay_div.innerHeight() + this.row_margin,
                selected_row_height = this.selected_row_height;
            if (this.options.expand_selected_row) {
                overlay_div_height = this.$overlay_div.height() - selected_row_height + this.row_margin;
            }
            else {
                selected_row_height = this.row_height;
            }
            this.row_count = Math.floor(overlay_div_height / this.row_height);
            if (this.options.expand_selected_row) {
                this.row_count += 1;
            }
            if (this.row_count <= 0) {
                this.row_count = 1;
            }
            if (!this.options.exact_height) {
                this.$overlay_div.height(this.row_height * this.row_count);
                if (this.options.expand_selected_row) {
                    this.$overlay_div.height(this.row_height * (this.row_count - 1) + this.selected_row_height + this.row_margin);
                }
            }
            return this.row_count;
        }

        create_pager($element) {
            var self = this,
                $pagination,
                $pager,
                tabindex,
                pagerWidth;
            if (this.item._paginate) {
                tabindex = -1;
                if (this.options.show_paginator) {
                    $pagination = $(
                        '   <div id="pager" style="margin: 0 auto">' +
                        '       <form class="form-inline" style="margin: 0">' +
                        '           <a class="btn btn-small" tabindex="-1" href="first"><i class="icon-backward"></i></a>' +
                        '           <a class="btn btn-small" tabindex="-1" href="prior"><i class="icon-chevron-left"></i></a>' +
                        '           <label  class="control-label" for="input-page">' + language.page + '</label>' +
                        '           <input class="pager-input input-mini" id="input-page" tabindex="' + tabindex + '" type="text">' +
                        '           <label id="page-count" class="control-label" for="input-page">' + language.of + '1000000 </label>' +
                        '           <a class="btn btn-small" tabindex="-1" href="next"><i class="icon-chevron-right"></i></a>' +
                        '           <a class="btn btn-small" tabindex="-1" href="last"><i class="icon-forward"></i></a>' +
                        '       </form>' +
                        '   </div>'
                        );


                    this.$fistPageBtn = $pagination.find('[href="first"]');
                    this.$fistPageBtn.on("click", function(e) {
                        self.first_page(true);
                        e.preventDefault();
                    });
                    this.$fistPageBtn.addClass("disabled");

                    this.$priorPageBtn = $pagination.find('[href="prior"]');
                    this.$priorPageBtn.on("click", function(e) {
                        self.prior_page(true);
                        e.preventDefault();
                    });
                    this.$priorPageBtn.addClass("disabled");

                    this.$nextPageBtn = $pagination.find('[href="next"]');
                    this.$nextPageBtn.on("click", function(e) {
                        self.next_page(true);
                        e.preventDefault();
                    });

                    this.$lastPageBtn = $pagination.find('[href="last"]');
                    this.$lastPageBtn.on("click", function(e) {
                        self.last_page(true);
                        e.preventDefault();
                    });
                    this.$pageInput = $pagination.find('input');
                    this.$pageInput.val(1);
                    this.$pageInput.on("keydown", function(e) {
                        var page,
                            code = (e.keyCode ? e.keyCode : e.which);
                        if (code === 13) {
                            page = parseInt(self.$pageInput.val(), 10);
                            e.preventDefault();
                            if (!isNaN(page) && (page > 0)) {
                                self.$pageInput.val(page);
                                self.set_page_number(page - 1);
                            }
                        }
                    });
                    this.$page_count = $pagination.find('#page-count');
                    this.$page_count.text(language.of + '1000000');
                    $pager = $pagination.find('#pager').clone()
                        .css("float", "left")
                        .css("position", "absolute")
                        .css("top", -1000);
                    $("body").append($pager);
                    pagerWidth = $pager.width();
                    $pager.remove();
                }
                else if (this.options.show_scrollbar) {
                    $pagination = $(
                        '<div class="text-right" style="line-height: normal;">' +
                            //~ '<span class="label">' +
                            '<span class="small-pager">' +
                                '<span>' + language.page + ' </span>' +
                                '<span id="page-number"></span>' +
                                '<span id="page-count"></span>' +
                            '</span>' +
                        '</div>'
                    )
                    this.$page_count = $pagination.find('#page-count');
                    this.$page_number = $pagination.find('#page-number');
                }
                if ($pagination) {
                    if (this.options.paginator_container) {
                        this.options.paginator_container.empty();
                        this.options.paginator_container.append($pagination);
                    } else {
                        if ($element) {
                            $element.find('.paginator').append($pagination);
                        } else {
                            this.$element.find('.paginator').append($pagination);
                        }
                    }
                    this.$page_count.text(language.of + ' ');
                    if (pagerWidth) {
                        $pagination.find('#pager').width(pagerWidth);
                    }
                }
            }
        }

        init_selected_field() {
            var field;
            if (!this.selected_field && this.editable_fields.length) {
                this.selected_field = this.editable_fields[0];
                if (this.options.selected_field) {
                    field = this.item.field_by_name(this.options.selected_field);
                    if (this.editable_fields.indexOf(field) !== -1) {
                        this.selected_field = field;
                    }
                }
            }
        }

        set_selected_field(field) {
            var self = this,
                field_changed = this.selected_field !== field;
            if (field_changed && this.can_edit()) {
                this.close_editor();
            }
            if (this.editable_fields.indexOf(field) !== -1) {
                this.hide_selection();
                this.selected_field = field
                this.show_selection();
            }
        }

        next_field() {
            var index;
            if (this.selected_field) {
                index = this.editable_fields.indexOf(this.selected_field);
                if (index < this.editable_fields.length - 1) {
                    this.set_selected_field(this.editable_fields[index + 1]);
                }
                else {
                    if (this.master_table && this.master_table.editable_fields.length) {
                        this.master_table.set_selected_field(this.master_table.editable_fields[0]);
                        this.master_table.focus();
                    }
                }
            }
        }

        prior_field() {
            var index;
            if (this.selected_field) {
                index = this.editable_fields.indexOf(this.selected_field);
                if (index > 0) {
                    this.set_selected_field(this.editable_fields[index - 1]);
                }
                else {
                    if (this.freezed_table && this.freezed_table.editable_fields.length) {
                        this.freezed_table.set_selected_field(this.freezed_table.editable_fields[0]);
                        this.freezed_table.focus();
                    }
                }
            }
        }

        hide_editor() {
            var width,
                field,
                $div,
                $td;
            $td;
            if (this.editing) {
                try {
                    this.edit_mode = false;
                    $td = this.editor.$control_group.parent();
                    field = this.editor.field
                    $div = $td.find('div.' + field.field_name);

                    width = $td.outerWidth();
                    $td.css("padding-left", this.editor.paddingLeft)
                    $td.css("padding-top", this.editor.paddingTop)
                    $td.css("padding-right", this.editor.paddingRight)
                    $td.css("padding-bottom", this.editor.paddingBottom)

                    this.editor.$control_group.remove();
                    this.editor.removed = true;
                    this.editor = undefined;

                    $td.outerWidth(width);

                    $div.show();
                } finally {
                    this.editing = false;
                }
                this.focus();
            }
        }

        close_editor() {
            if (this.editor) {
                let self = this;
                if (!this.item.is_changing()) {
                    this.item.edit();
                }
                this.flush_editor();
                this.hide_editor();
                if (this.item.is_changing()) {
                    this.item.post();
                }
                this.item.apply(function() {
                    if (self.item.master) {
                        self.item.master.edit();
                    }
                });
            }
        }

        flush_editor() {
            if (this.editor && this.editing) {
                this.editor.change_field_text();
            }
        }

        show_editor() {
            var self = this,
                width,
                height,
                min_width,
                editor,
                $div,
                $td,
                $row = this.row_by_record(),
                freezed_table = this.freezed_table;
            if ($row && this.can_edit() && !this.editing && this.selected_field && this.item.rec_count) {
                if (this.item._applying) {
                    let cell = $row.find('td.' + this.selected_field.field_name);
                    cell.addClass('alert-error')
                    setTimeout(
                        function() {
                            cell.removeClass('alert-error');
                        },
                        1000
                    );
                    return;
                }
                if (!this.item.is_changing()) {
                    this.item.edit();
                }
                this.edit_mode = true;
                this.editor = new DBTableInput(this, this.selected_field);
                this.editor.$control_group.find('.controls, .input-prepend, .input-append, input').css('margin', 0);
                this.editor.$control_group.css('margin', 0);

                $div = $row.find('div.' + this.editor.field.field_name);
                $div.hide();
                $td = $row.find('td.' + this.editor.field.field_name);

                this.editor.$input.css('font-size', $td.css('font-size'));

                height = $td.innerHeight();
                width = $td.innerWidth();
                this.editor.paddingLeft = $td.css("padding-left");
                this.editor.paddingTop = $td.css("padding-top");
                this.editor.paddingRight = $td.css("padding-right");
                this.editor.paddingBottom = $td.css("padding-bottom");

                this.editor.padding = $td.css("padding");
                $td.css("padding", 0);
                $td.innerWidth(width);

                this.editor.$input.css('max-width', 'initial');
                $td.append(this.editor.$control_group);
                min_width = parseInt(this.editor.$input.css('min-width'), 10);
                if (min_width) {
                    width = 2;
                    this.editor.$input.parent().children('*').each(function() {
                        width += $(this).outerWidth(true);
                    });
                    if (width > $td.outerWidth()) {
                        this.set_сell_width(this.selected_field.field_name, $td.outerWidth());
                        this.change_field_width(this.selected_field.field_name, width - $td.outerWidth());
                        if (freezed_table !== this.freezed_table && this.freezed_table.fields.indexOf(self.selected_field) !== -1) {
                            this.editor.$control_group.remove();
                            this.editor.removed = true;
                            this.editor = undefined;
                            setTimeout(
                                function() {
                                    self.edit_mode = false;
                                    self.freezed_table.focus();
                                    self.freezed_table.selected_field = self.selected_field;
                                    self.freezed_table.show_editor();
                                }, 0);
                            return;
                        }
                    }
                }

                width = 0;
                this.editor.$input.parent().children('*').css('border', '0').each(function() {
                    width += $(this).outerWidth(true);
                });
                if (this.editor.$btn_ctrls) {
                    width += 2
                }
                this.editor.$input.width(this.editor.$input.width() + this.editor.$control_group.width() - width);
                if (this.editor.$btn_ctrls && this.editor.$btn_ctrls.width()) {
                    this.editor.$btn_ctrls.width('auto');
                }
                if (this.selected_field.lookup_item || this.selected_field.lookup_values) {
                    this.editor.$control_group.css('margin-left', 1);
                }
                this.editor.update();

                if (this.is_focused()) {
                    this.editor.$input.focus();
                }
                this.editing = true;
            }
        }

        height(value) {
            if (value === undefined) {
                return this.$element.height();
            } else {
                this.$overlay_div.height(value - (this.$element.height() - this.$overlay_div.height()));
            }
        }

        fill_title($element) {
            var i,
                self = this,
                field,
                caption,
                heading,
                div,
                cell,
                input,
                bl,
                checked = '',
                field_name,
                sel_count,
                desc,
                order_fields = {},
                sortable_fields = {},
                shown_title,
                select_menu = '';
            if ($element === undefined) {
                $element = this.$element
            }
            if (!this._sorted_fields) {
                this._sorted_fields = [];
            }
            for (i = 0; i < this.fields.length; i++) {
                if (this.options.sortable) {
                    field = this.fields[i];
                    if (!this.options.sort_fields.length || this.options.sort_fields.indexOf(field.field_name) !== -1) {
                        sortable_fields[field.field_name] = '<span style="font-size: xx-small;">&varr;</span>';
                    }
                }
            }
            for (i = 0; i < this._sorted_fields.length; i++) {
                try {
                    desc = this._sorted_fields[i][1];
                    field = this.item.field_by_name(this._sorted_fields[i][0])
                    if (desc) {
                        order_fields[field.field_name] = '<span style="font-size: large;">&darr;</span>';
                    } else {
                        order_fields[field.field_name] = '<span style="font-size: large;">&uarr;</span>';
                    }
                } catch (e) {}
            }

            heading = $element.find("thead tr:first");
            heading.empty();
            if (this.options.multiselect) {
                if (this.item.master || !this.item._paginate) {
                    if (this.selections_get_all_selected()) {
                        checked = 'checked';
                    }
                    div = $('<div class="text-center multi-select" style="overflow: hidden"></div>');
                    sel_count = $('<p class="sel-count text-center">' + this.item.selections.length + '</p>')
                    div.append(sel_count);
                    input = $('<input class="multi-select-header" type="checkbox" ' + checked + ' tabindex="-1">');
                    div.append(input);
                    cell = $('<th class="multi-select-header"></th>').append(div);
                    heading.append(cell);
                }
                else {
                    if (this.selections_get_all_selected()) {
                        checked = 'checked';
                    }
                    div = $('<div class="text-center multi-select" style="overflow: hidden"></div>');
                    sel_count = $('<p class="sel-count text-center">' + this.item.selections.length + '</p>')
                    div.append(sel_count);
                    if (this.options.select_all) {
                        select_menu +=
                            '<li id="mselect-all"><a tabindex="-1" href="#">' + task.language.select_all + '</a></li>' +
                            '<li id="munselect-all"><a tabindex="-1" href="#">' + task.language.unselect_all + '</a></li>'
                    }
                    shown_title = task.language.show_selected
                    if (self.item._show_selected) {
                        shown_title = task.language.show_all
                    }
                    select_menu +=
                        '<li id="mshow-selected"><a tabindex="-1" href="#">' + shown_title + '</a></li>';
                    bl = $(
                            '<div id="mselect-block" class="btn-group" style="position: relative">' +
                                '<button type="button" class="btn mselect-btn" tabindex="-1">' +
                                    '<input class="multi-select-header" type="checkbox" tabindex="-1" style="margin: 0" ' + checked + '>' +
                                '</button>' +
                                '<a class="btn dropdown-toggle" data-toggle="dropdown" href="#" tabindex="-1" style="padding: 3px">' +
                                    '<span class="caret"></span>' +
                                '</a>' +
                                '<ul class="dropdown-menu">' +
                                    select_menu +
                                '</ul>' +
                            '</div>'
                    );
                    input = bl.find('#mselect-block')
                    bl.find("#mselect-all").click(function(e) {
                        e.preventDefault();
                        self.selections_set_all_selected_ex(true);
                        self.$table.focus();
                    });
                    bl.find("#munselect-all").click(function(e) {
                        e.preventDefault();
                        self.selections_set_all_selected_ex(false);
                        self.$table.focus();
                    });
                    bl.find("#mshow-selected").click(function(e) {
                        e.preventDefault();
                        self.item._show_selected = !self.item._show_selected;
                        self.item.reopen(0, {__show_selected_changed: true}, function() {
                            self.selections_update_selected();
                            self.$table.focus();
                        });
                    });
                    cell = $('<th class="multi-select"></th>').append(div);
                    heading.append(cell);
                    cell.css('padding-top', 0);
                    input.css('top', sel_count.outerHeight() + sel_count.position().top + 4);
                    input.css('left', (cell.outerWidth() - input.width()) / 2 + 1);
                    cell.append(bl);
                }
            }
            for (i = 0; i < this.fields.length; i++) {
                field = this.fields[i];
                caption = field.field_caption;
                if (order_fields[field.field_name]) {
                    caption = order_fields[field.field_name] + caption;
                }
                else if (sortable_fields[field.field_name]) {
                    caption = sortable_fields[field.field_name] + caption;
                }
                div = $('<div class="th-container"><div class="th-table"><div class="text-center th-text ' + field.field_name +
                    '" style="overflow: hidden">' + caption + '</div></div></div>');
                cell = $('<th class="' + field.field_name + '" data-field_name="' + field.field_name + '"></th>').append(div);
                heading.append(cell);
                if (this.options.title_line_count !== 0) {
                    div.css('height', parseInt(cell.css('line-height'), 10) * this.options.title_line_count);
                    cell.css('height', parseInt(cell.css('line-height'), 10) * this.options.title_line_count);
                }
            }
            heading.append('<th class="fake-column" style="display: None;></th>');
            if (this.options.title_callback) {
                this.options.title_callback(heading, this.item)
            }
            this.selections_update_selected();
        }

        fill_footer($element) {
            var i,
                len,
                field,
                footer,
                old_footer,
                div,
                old_div,
                cell,
                cell_width;
            if ($element === undefined) {
                $element = this.$element
            }
            footer = $element.find("tfoot tr:first");
            old_footer = footer.clone();
            footer.empty();
            if (this.options.multiselect) {
                div = $('<div class="text-center multi-select" style="overflow: hidden; width: 100%"></div>')
                cell = $('<th class="multi-select"></th>').append(div);
                footer.append(cell);
            }
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                div = $('<div class="text-center ' + field.field_name +
                    '" style="overflow: hidden; width: 100%">&nbsp</div>');
                old_div = old_footer.find('div.' + field.field_name)
                if (old_div.length) {
                    div.html(old_div.html());
                }
                cell = $('<th class="' + field.field_name + '"></th>').append(div);
                footer.append(cell);
            }
            footer.append('<th class="fake-column" style="display: None;></th>');
            if (!this.options.show_footer) {
                footer.hide();
            }
        }

        show_footer() {
            this.$element.find("table.outer-table tfoot tr:first").show();
        }

        hideFooter() {
            this.$element.find("table.outer-table tfoot tr:first").hide();
        }

        get_cell_width(field_name) {
            return this.cell_widths[field_name];
        }

        set_сell_width(field_name, value) {
            value = parseInt(value, 10)
            this.cell_widths[field_name] = value;
        }

        init_table() {
            if (!this.item._page_changed) {
                this.init_fields();
                this._sorted_fields = this.item._open_params.__order;
                if (this.item._paginate) {
                    if (this.item._offset === 0) {
                        this.page = 0;
                        this.update_page_info();
                    }
                    this.update_totals();
                } else {
                    this.calc_summary();
                }
            }
            this.datasource = [];
            this.refresh();
        }

        form_closing() {
            if (this.form) {
                return this.form.data('_closing');
            }
        }

        do_after_open() {
            var self = this;
            this.prev_selected_rec_no = undefined;
            if (this.$table.is(':visible')) {
                this.init_table();
                this.sync_freezed();
            }
            else if (this.item.rec_count) {
                setTimeout(
                    function() {
                        self.init_table();
                        self.sync_freezed();
                    },
                    1
                );
            }
        }

        update(state) {
            var self = this;
            if (this.form_closing()) {
                return;
            }
            switch (state) {
                case consts.UPDATE_OPEN:
                    this.do_after_open();
                    break;
                case consts.UPDATE_RECORD:
                    this.refresh_row();
                    break;
                case consts.UPDATE_SCROLLED:
                    this.syncronize();
                    break;
                case consts.UPDATE_CONTROLS:
                    this.syncronize();
                    this.build(true);
                    break;
                case consts.UPDATE_CLOSE:
                    this.$table.empty();
                    break;
                case consts.UPDATE_APPLIED:
                    this.update_totals();
                    break;
                case consts.UPDATE_SUMMARY:
                    this.update_summary();
                    break;
            }
        }

        update_summary() {
            var field_name;
            for (field_name in this.item._fields_summary_info) {
                let field = this.item.field_by_name(field_name),
                    text = this.item._fields_summary_info[field_name].text,
                    value = this.item._fields_summary_info[field_name].value,
                    new_text = '';
                if (this.item.on_field_get_summary) {
                    if (field.data_type === consts.CURRENCY) {
                        value = round(value, locale.FRAC_DIGITS);//.toFixed(locale.FRAC_DIGITS);
                    }
                    new_text = this.item.on_field_get_summary.call(this.item, field, text);
                }
                if (!new_text) {
                    new_text = text;
                }
                this.$foot.find('div.' + field_name).text(new_text);
            }

        }

        calc_summary(callback) {
            var self = this,
                i,
                copy,
                field_name,
                field,
                fields,
                count_field,
                sum_fields,
                count_fields,
                total_records = 0,
                //~ expanded = false,
                search_field,
                funcs,
                params = {};
            if (!this.item._paginate || this.item.virtual_table) {
                this.item.calc_summary(this.item, undefined, undefined, this.options.summary_fields);
            }
            else {
                if (this.item.master) {
                    copy = task.item_by_ID(this.item.prototype_ID).copy({handlers: false, details: false});
                }
                else {
                    copy = this.item.copy({handlers: false, details: false});
                }
                count_field = copy.fields[0].field_name,
                fields = [];
                count_fields = [];
                sum_fields = [];
                funcs = {};
                sum_fields.push(count_field);
                funcs[count_field] = 'count';
                for (i = 0; i < this.options.summary_fields.length; i++) {
                    field_name = this.options.summary_fields[i];
                    field = this.item.field_by_name(field_name);
                    if (field && this.fields.indexOf(field) !== -1) {
                        fields.push(field_name);
                        if (field.numeric_field()) {
                            sum_fields.push(field_name);
                            funcs[field_name] = 'sum';
                        }
                        else {
                            count_fields.push(field_name);
                        }
                    }
                }
                if (self.item._open_params.__search) {
                    search_field = this.item._open_params.__search[0];
                    field = this.item.field_by_name(search_field);
                    //~ if (field.lookup_item) {
                        //~ expanded = true;
                    //~ }
                    if (sum_fields.indexOf(search_field) === -1) {
                        sum_fields.push(search_field);
                        funcs[search_field] = 'count';
                    }
                    else {
                        search_field = '';
                    }
                }
                for (var key in self.item._open_params) {
                    if (self.item._open_params.hasOwnProperty(key)) {
                        if (key.substring(0, 2) !== '__') {
                            params[key] = self.item._open_params[key];
                        }
                    }
                }
                params.__summary = true;
                if (self.item._open_params.__filters) {
                    copy._where_list = self.item._open_params.__filters;
                }
                if (this.item.master) {
                    copy.ID = this.item.ID
                    params.__master_id = this.item.master.ID;
                    params.__master_rec_id = this.item.master.field_by_name(this.item.master._primary_key).value;
                }
                this.item._fields_summary_info = {};
                copy.open({fields: sum_fields, funcs: funcs, params: params},
                    function() {
                        var i,
                            text;
                        copy.each_field(function(f, i) {
                            if (i == 0) {
                                total_records = f.data;
                            }
                            else if (f.field_name !== search_field) {
                                self.item._fields_summary_info[f.field_name] =
                                    {text: f.display_text, value: f.value};
                            }
                        });
                        for (i = 0; i < count_fields.length; i++) {
                            self.item._fields_summary_info[count_fields[i]] =
                                {text: total_records + '', value: total_records};
                        }
                        self.update_summary()
                        if (callback) {
                            callback.call(this, total_records);
                        }
                    }
                );
            }
        }

        update_field(field, refreshingRow) {
            var self = this,
                row = this.row_by_record(),
                update,
                build,
                html,
                div;
            if (row && this.item.active && this.item.controls_enabled() && this.item.record_count()) {
                div = row.find('div.' + field.field_name);
                if (div.length) {
                    html = this.get_field_html(field)
                    if (html !== div.html()) {
                        div.html(html);
                        if (this.item.record_count() < 3 && (!this.item.paginate || this.item.paginate && this.page_count === 0)) {
                            this.build();
                        }
                        if (!refreshingRow) {
                            this.update_selected(row);
                        }
                    }
                }
            }
        }

        update_selected(row) {
            if (!row) {
                row = this.row_by_record();
            }
            if (this.options.row_callback) {
                this.options.row_callback(row, this.item);
            }
        }

        record_by_row(row) {
            for (var i = 0; i < this.datasource.length; i++) {
                if (this.datasource[i][1] === row[0]) {
                    return this.datasource[i][0]
                }
            }
        }

        row_by_record() {
            if (this.item.rec_count) {
                for (var i = 0; i < this.datasource.length; i++) {
                    if (this.datasource[i][0] === this.item.rec_no) {
                        return $(this.datasource[i][1])
                    }
                }
            }
        }

        refresh_row() {
            var self = this;
            this.each_field(function(field, i) {
                self.update_field(field, true);
            });
        }

        do_on_edit(field) {
            if (this.item.lookup_field) {
                this.item.set_lookup_field_value();
            } else {
                if (this.can_edit()) {
                    if (field) {
                        this.set_selected_field(field);
                    }
                    if (!this.edit_mode && (!field || this.editable_fields.indexOf(field) !== -1)) {
                        this.show_editor();
                    }
                }
                if (!this.edit_mode) {
                    if (this.on_dblclick) {
                        this.on_dblclick.call(this.item, this.item);
                    } else if (this.options.dblclick_edit) {
                        this.item.edit_record();
                    }
                }
            }
        }

        clicked(e, td) {
            var rec,
                field = this.item.field_by_name(td.data('field_name')),
                $row = td.parent();
            rec = this.record_by_row($row);
            if (rec !== undefined) {
                if (this.edit_mode && rec !== this.item.rec_no) {
                    this.close_editor();
                }
                this.item.rec_no = rec;
                if (!this.editing && !this.is_focused()) {
                    this.focus();
                }
                if (field) {
                    this.set_selected_field(field);
                }
                if (e.type === "dblclick") {
                    this.do_on_edit(field);
                }
            }
        }

        hide_selection() {
            if (this.selected_row) {
                if (this.selected_field) {
                    this.selected_row.removeClass("selected-focused selected");
                    this.selected_row.find('td.' + this.selected_field.field_name)
                        .removeClass("field-selected-focused field-selected")
                } else {
                    this.selected_row.removeClass("selected-focused selected");
                }
            }
        }

        table_focused() {
            var focused = this.is_focused();
            if (this.master_table && !focused) {
                focused = this.master_table.is_focused()
            }
            if (this.freezed_table && !focused) {
                focused = this.freezed_table.is_focused()
            }
            return focused;
        }

        show_selection() {
            var selClassName = 'selected',
                selFieldClassName = 'field-selected';
            if (!this.is_showing_selection) {
                this.is_showing_selection = true;
                try {
                    if (this.table_focused()) {
                        selClassName = 'selected-focused';
                        selFieldClassName = 'field-selected-focused';
                    }
                    if (this.selected_row) {
                        if (this.can_edit() && this.selected_field) {
                            this.selected_row.addClass(selClassName);
                            this.selected_row.find('td.' + this.selected_field.field_name)
                                .removeClass(selClassName)
                                .addClass(selFieldClassName);
                        } else {
                            this.selected_row.addClass(selClassName);
                        }
                    }
                    if (this.master_table) {
                        this.master_table.show_selection()
                    }
                    if (this.freezed_table) {
                        this.freezed_table.show_selection()
                    }
                }
                finally {
                    this.is_showing_selection = false;
                }
            }
        }

        select_row($row) {
            var divs,
                textHeight = this.text_height;
            this.hide_selection();
            if (this.options.row_line_count && this.selected_row && this.options.expand_selected_row) {
                this.selected_row.find('tr, div').css('height', this.options.row_line_count * textHeight);
            }
            this.selected_row = $row;
            this.show_selection();
            if (this.options.row_line_count && this.options.expand_selected_row) {
                divs = this.selected_row.find('tr, div')
                divs.css('height', '');
                divs.css('height', this.options.expand_selected_row * textHeight);
            }
        }

        cancel_sync() {
            this.set_sync(true);
        }

        resume_sync() {
            this.set_sync(false);
        }

        set_sync(value) {
            this.syncronizing = value;
            if (this.freezed_table) {
                this.freezed_table.syncronizing = value;
            }
            if (this.master_table) {
                this.master_table.syncronizing = value;
            }
        }

        syncronize(noscroll) {
            var self = this,
                page_rec,
                row_changed,
                clone,
                row = this.row_by_record();
            if (this.syncronizing) {
                if (row) {
                    this.select_row(row);
                }
            }
            else if (this.item.controls_enabled() && this.item.record_count() > 0) {
                this.syncronizing = true;
                try {
                    if (!row && this.datasource.length && !this.item.paginate) {
                        this.datasource = [];
                        if (this.item.filter_active()) {
                            page_rec = this.item.rec_no;
                        }
                        else {
                            page_rec = Math.floor((this.item.rec_no) / this.row_count) * this.row_count;
                        }
                        this.fill_datasource(page_rec)
                        if (this.datasource.length < this.row_count && this.item.rec_count > this.row_count) {
                            clone = this.item.clone(true);
                            clone.last();
                            for (var i = 1; i < this.row_count; i++) {
                                if (!clone.bof()) {
                                    clone.prior();
                                }
                            }
                            page_rec = clone.rec_no;
                            this.datasource = [];
                            this.fill_datasource(page_rec)
                        }
                        this.refresh();
                        row = this.row_by_record();
                    }
                    row_changed = !this.selected_row || (this.selected_row && row && this.selected_row.get(0) !== row.get(0));
                    if (row_changed && this.can_edit()) {
                        this.hide_editor();
                    }
                    try {
                        this.select_row(this.row_by_record());
                    } catch (e) {}
                    if (!noscroll) {
                        this.table_scroll = true;
                        this.$overlay_div.scrollTop(this.scroll_pos_by_rec());
                    }
                }
                finally {
                    this.syncronizing = false;
                }
            }
        }

        get_field_text(field) {
            if (field.lookup_data_type === consts.BOOLEAN) {
                let res;
                if (field.owner && (field.owner.on_field_get_text || field.owner.on_get_field_text)) {
                    if (field.owner.on_field_get_text) {
                        res = field.owner.on_field_get_text.call(field.owner, field);
                    }
                    else if (field.owner.on_get_field_text) {
                        res = field.owner.on_get_field_text.call(field.owner, field);
                    }
                }
                if (!res) {
                    return field.lookup_value ? '×' : ''
                }
            }
            return field.sanitized_text;
        }

        get_field_html(field) {
            var result;
            result = field.get_html();
            if (!result) {
                result = this.get_field_text(field);
                if (field._owner_is_item() && this.item._open_params.__search) {
                    if (field.field_name === this.item._open_params.__search[0]) {
                        var text = this.item._open_params.__search[1];
                        if (this.item._open_params.__search.length === 4) {
                            text = this.item._open_params.__search[3];
                        }
                        result = highlight(result, text);
                    }
                }
            }
            return result;
        }

        scroll(e) {
            var self = this,
                scroll_el,
                table_el;
            if (this.is_mac) {
                scroll_el = this.$scroll_div[0];
                table_el = this.$table[0];
                if (!this.pointer_events_set) {
                    scroll_el.style.pointerEvents = 'none';
                    table_el.style.pointerEvents = 'none';
                }
                this.pointer_events_set = true;
                clearTimeout(this.scroll_debounce);
                this.scroll_debounce = setTimeout(function () {
                    scroll_el.style.pointerEvents = 'auto';
                    table_el.style.pointerEvents = 'auto';
                    self.pointer_events_set = false;
                }, 50);

            }
            if (this.table_scroll) {
                this.table_scroll = false;
            }
            else {
                this.scroll_table(e);
            }
            this.$table.css({'top': this.$overlay_div.scrollTop() + 'px'});
        }

        scroll_datasource(page_rec) {
            this.datasource = [];
            this.fill_datasource(page_rec)
        }

        scroll_table(e) {
            var self = this,
                page_rec = Math.round(this.$overlay_div.scrollTop() / this.row_height);
            if (this.item.paginate) {
                var page = Math.round(page_rec / this.row_count);
                this.$table.addClass('paginate-scroll');
                this.update_page_info(page);
                clearTimeout(this.scroll_timeout);
                this.scroll_timeout = setTimeout(
                    function() {
                        self.$table.removeClass('paginate-scroll');
                        if (page !== self.page) {
                            self.table_scroll = true;
                            self.set_page_number(page);
                        }
                    },
                    200
                );
            }
            else {
                this.scroll_datasource(page_rec);
                if (this.freezed_table) {
                    this.freezed_table.scroll_datasource(page_rec);
                }
                if (this.master_table) {
                    this.master_table.scroll_datasource(page_rec);
                }
                this.cancel_sync();
                try {
                    this.refresh();
                    if (this.freezed_table) {
                        this.freezed_table.refresh();
                    }
                    if (this.master_table) {
                        this.master_table.refresh();
                    }
                }
                finally {
                    this.resume_sync();
                }
            }
        }

        scroll_height() {
            var delta = this.$overlay_div.innerHeight() - this.row_count * this.row_height;
            if (this.item.paginate) {
                return Math.ceil(this.record_count / this.row_count) * this.row_count * this.row_height;
            }
            else {
                return this.item.record_count() * this.row_height + delta;
            }
        }

        scroll_pos_by_rec() {
            if (this.item.paginate) {
                return Math.round((this.page * this.row_count + this.item.rec_no) * this.row_height);
            }
            else {
                return Math.round(this.item.rec_no * this.row_height);
            }
        }

        keydown(e) {
            this.scroll_delta = 0;
            var self = this,
                code = (e.keyCode ? e.keyCode : e.which);
            if (!e.ctrlKey && !e.shiftKey) {
                switch (code) {
                    case 33:
                    case 34:
                    case 35:
                    case 36:
                    case 38:
                    case 40:
                        if (this.editing && code !== 38 && code !== 40) {
                            return
                        }
                        e.preventDefault();
                        this.close_editor();
                        if (code === 33) {
                            this.prior_page();
                        } else if (code === 34) {
                            if (this.item._paginate && this.item.is_loaded) {
                                this.item.last();
                            } else {
                                this.next_page();
                            }
                        } else if (code === 38) {
                            this.prior_record();
                        } else if (code === 40) {
                            this.next_record();
                        } else if (code === 36) {
                            this.first_page();
                        } else if (code === 35) {
                            this.last_page();
                        }
                        break;
                    case 37:
                        if (this.can_edit() && !this.edit_mode) {
                            this.prior_field();
                        }
                        break;
                    case 39:
                        if (this.can_edit() && !this.edit_mode) {
                            this.next_field();
                        }
                        break;
                }
            }
        }

        keyup(e) {
            var self = this,
                multi_sel,
                code = (e.keyCode ? e.keyCode : e.which);
            if (e.target === this.$table.get(0) && !e.ctrlKey && !e.shiftKey) {
                switch (code) {
                    case 13:
                        e.preventDefault();
                        this.do_on_edit();
                        break;
                    case 33:
                    case 34:
                    case 35:
                    case 36:
                    case 38:
                    case 40:
                        e.preventDefault();
                        break;
                    case 32:
                        e.preventDefault();
                        if (this.options.multiselect) {
                            multi_sel = this.row_by_record().find('input.multi-select');
                            this.selections_set_selected(!multi_sel[0].checked);
                            multi_sel.prop('checked', this.selections_get_selected());
                        }
                        break
                }
            }
        }

        keypress(e) {
            var self = this,
                multi_sel,
                code = e.which;
            if (code > 32 && this.can_edit() && this.options.keypress_edit && !this.edit_mode) {
                if (this.selected_field && this.selected_field.valid_char_code(code)) {
                    this.show_editor();
                }
            }
        }

        set_page_number(value, callback, chech_last_page) {
            var self = this;

            if (chech_last_page === undefined) {
                chech_last_page = true;
            }
            if (!this.item._paginate || this.loading) {
                return;
            }
            if (value < this.page_count || value === 0) {
                this.remove_tooltip();
                this.page = value;
                this.scrollLeft = this.$element.find('.table-container').get(0).scrollLeft;
                if (this.master_table) {
                    this.master_table.scrollLeft = this.master_table.$element.find('.table-container').get(0).scrollLeft;
                }
                this.loading = true;
                if (this.item.record_count()) {
                    this.item._do_before_scroll();
                }
                this.item._page_changed = true;
                this.item.open({offset: this.page * this.item._limit}, function() {
                    self.item._page_changed = false;
                    if (callback) {
                        callback.call(self);
                    }
                    self.loading = false;
                    self.update_page_info();
                    self.$element.find('.table-container').get(0).scrollLeft = self.scrollLeft;
                    if (self.master_table) {
                        self.master_table.$element.find('.table-container').get(0).scrollLeft = self.master_table.scrollLeft;
                    }
                    if (value === this.page_count - 1 && self.item.rec_count === 0 && chech_last_page) {
                        self.update_totals(function() {
                            self.set_page_number(self.page_count - 1, callback, false)
                        })
                    }
                    else if (callback) {
                        callback.call(this);
                    }
                });
            }
        }

        reload(callback) {
            if (this.item._paginate) {
                this.set_page_number(this.page, callback);
            } else {
                this.open(callback);
            }
        }

        update_page_info(page) {
            var cur_page;
            if (page === undefined) {
                cur_page = this.page;
            }
            else {
                cur_page = page
            }
            if (this.options.show_paginator) {
                if (this.$pageInput) {
                    this.$pageInput.val(cur_page + 1);
                    if (this.page === 0) {
                        this.$fistPageBtn.addClass("disabled");
                        this.$priorPageBtn.addClass("disabled");
                    } else {
                        this.$fistPageBtn.removeClass("disabled");
                        this.$priorPageBtn.removeClass("disabled");
                    }
                    if (this.item.is_loaded) {
                        this.$lastPageBtn.addClass("disabled");
                        this.$nextPageBtn.addClass("disabled");
                    } else {
                        this.$lastPageBtn.removeClass("disabled");
                        this.$nextPageBtn.removeClass("disabled");
                    }
                }
            }
            else if (this.options.show_scrollbar) {
                this.$page_number.text(cur_page + 1 + ' ');
            }

            if (this.options.on_page_changed && page === undefined) {
                this.options.on_page_changed.call(this.item, this.item, this);
            }
        }

        update_totals(callback) {
            var self = this;
            this.calc_summary(function(count) {
                self.update_page_count(count);
                if (callback) {
                    callback();
                }
            })
        }

        update_page_count(count) {
            if (this.item._paginate && self.record_count !== count) {
                this.record_count = count;
                this.$scroll_div.height(this.scroll_height())
                this.page_count = Math.ceil(count / this.row_count);
                if (this.$page_count) {
                    this.$page_count.text(language.of + ' 1');
                    if (this.page_count) {
                        this.$page_count.text(language.of + ' ' + this.page_count);
                    }
                    else {
                        this.$page_count.text(language.of + ' ' + 1);
                    }
                }
                if (this.options.on_pagecount_update) {
                    this.options.on_pagecount_update.call(this.item, this.item, this);
                }
                if (this.options.on_page_changed) {
                    this.options.on_page_changed.call(this.item, this.item, this);
                }
            }
        }

        show_next_record() {
            var self = this,
                row = this.row_by_record();
            if (!row) {
                row = this.datasource[0][1];
                row.remove();
                this.datasource.splice(0, 1);
                row = $(this.new_row());
                if (this.options.row_callback) {
                    this.options.row_callback(row, this.item);
                }
                this.$table.append(row);
                this.datasource.push([this.item.rec_no, row[0]]);
            }

        }

        next_record(btn_click) {
            this.cancel_sync();
            try {
                this.item.next();
                if (this.item.eof()) {
                    if (this.can_edit() && this.options.append_on_lastrow_keydown) {
                        this.item.append();
                    } else if (this.item.paginate) {
                        let page_scroll = btn_click || this.options.auto_page_scroll;
                        if (page_scroll) {
                            this.next_page();
                        }
                    }
                }
                else if (!this.item.paginate) {
                    this.show_next_record();
                    if (this.master_table) {
                        this.master_table.show_next_record()
                    }
                    if (this.freezed_table) {
                        this.freezed_table.show_next_record()
                    }
                }
            }
            finally {
                this.resume_sync();
            }
            this.syncronize();
            if (this.master_table) {
                this.master_table.syncronize();
            }
            if (this.freezed_table) {
                this.freezed_table.syncronize();
            }
        }

        show_prior_record() {
            var row = this.row_by_record(),
                index;
            if (!row) {
                if (this.datasource.length === this.row_count) {
                    index = this.datasource.length - 1;
                    row = this.datasource[index][1];
                    row.remove();
                    this.datasource.splice(index, 1);
                    row = $(this.new_row());
                    if (this.options.row_callback) {
                        this.options.row_callback(row, this.item);
                    }
                    this.$table.prepend(row);
                    this.datasource.splice(0, 0, [this.item.rec_no, row[0]]);
                }
            }
        }

        prior_record(btn_click) {
            var self = this;
            this.cancel_sync();
            try {
                this.item.prior();
                if (this.item.bof()) {
                    if (this.item.paginate) {
                        let page_scroll = btn_click || this.options.auto_page_scroll;
                        if (page_scroll) {
                            this.prior_page(function() {
                                self.item.last();
                            });
                        }
                    }
                }
                else if (!this.item.paginate) {
                    this.show_prior_record();
                    if (this.master_table) {
                        this.master_table.show_prior_record();
                    }
                    if (this.freezed_table) {
                        this.freezed_table.show_prior_record();
                    }
                }
            }
            finally {
                this.resume_sync();
            }
            this.syncronize();
            if (this.master_table) {
                this.master_table.syncronize();
            }
            if (this.freezed_table) {
                this.freezed_table.syncronize();
            }
        }

        first_page() {
            let args = this.item._check_args(arguments),
                callback = args['function'],
                btn_click = args['boolean'],
                page_scroll = btn_click || this.options.auto_page_scroll;
            if (this.item._paginate && page_scroll) {
                this.set_page_number(0, callback);
            } else {
                this.item.first();
            }
        }

        next_page() {
            let args = this.item._check_args(arguments),
                callback = args['function'],
                btn_click = args['boolean'];
            if (this.item._paginate) {
                let page_scroll = btn_click || this.options.auto_page_scroll
                if (!this.item.is_loaded && page_scroll) {
                    this.set_page_number(this.page + 1, callback);
                }
            } else {
                let clone = this.item.clone();
                clone.rec_no = this.item.rec_no;
                for (var i = 0; i < this.row_count; i++) {
                    if (!clone.eof()) {
                        clone.next();
                    } else {
                        break;
                    }
                }
                this.item.rec_no = clone.rec_no;
            }
        }

        prior_page() {
            let args = this.item._check_args(arguments),
                callback = args['function'],
                btn_click = args['boolean'];
            if (this.item._paginate) {
                if (this.page > 0) {
                    let page_scroll = btn_click || this.options.auto_page_scroll
                    if (page_scroll) {
                        this.set_page_number(this.page - 1, callback);
                    }
                } else {
                    this.syncronize();
                }
            } else {
                let clone = this.item.clone();
                clone.rec_no = this.item.rec_no;
                for (var i = 0; i < this.row_count; i++) {
                    if (!clone.eof()) {
                        clone.prior();
                    } else {
                        break;
                    }
                }
                this.item.rec_no = clone.rec_no;
            }
        }

        last_page() {
            let args = this.item._check_args(arguments),
                callback = args['function'],
                btn_click = args['boolean'],
                page_scroll = btn_click || this.options.auto_page_scroll;
            var self = this;
            if (this.item._paginate && page_scroll) {
                this.set_page_number(this.page_count - 1, callback);
            } else {
                this.item.last();
            }
        }

        each_field(callback) {
            var i = 0,
                len = this.fields.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.fields[i], this.fields[i], i);
                if (value === false) {
                    break;
                }
            }
        }

        new_column(columnName, align, text, index) {
            var cell_width = this.get_cell_width(columnName),
                classStr = 'class="' + columnName + '"',
                dataStr = 'data-field_name="' + columnName + '"',
                tdStyleStr = 'style="text-align:' + align + ';overflow: hidden',
                divStyleStr = 'style="overflow: hidden';
            if (this.text_height && this.options.row_line_count) {
                divStyleStr += '; height: ' + this.options.row_line_count * this.text_height + 'px; width: auto';
            }
            tdStyleStr +=  '""';
            divStyleStr += '"';
            return '<td ' + classStr + ' ' + dataStr + ' ' + tdStyleStr + '>' +
                '<div ' + classStr + ' ' + divStyleStr + '>' + text +
                '</div>' +
                '</td>';
        }

        new_row() {
            var f,
                i,
                len,
                field,
                align,
                text,
                rowStr,
                checked = '';
            len = this.fields.length;
            rowStr = '';
            if (this.options.multiselect) {
                if (this.selections_get_selected()) {
                    checked = 'checked';
                }
                rowStr += this.new_column('multi-select', 'center', '<input class="multi-select" type="checkbox" ' + checked + ' tabindex="-1" style="margin: 0">', -1);
            }
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                f = this.item[field.field_name];
                if (!(f instanceof Field)) {
                    f = this.item.field_by_name(field.field_name);
                }
                text = this.get_field_html(f);
                align = f.data_type === consts.BOOLEAN ? 'center' : align_value[f.alignment]
                rowStr += this.new_column(f.field_name, align, text, i);
            }
            rowStr += '<td class="fake-column" style="display: None;"></td>'
            return '<tr class="inner">' + rowStr + '</tr>';
        }

        get_element_width(element) {
            if (!element.length) {
                return 0;
            }
            if (element.is(':visible')) {
                return element.width()
            } else {
                return this.get_element_width(element.parent())
            }
        }

        sync_col_width(fake_column) {
            var $row,
                field,
                $td;
            if (this.item.record_count()) {
                $row = this.$table.find("tr:first-child");
                this.set_saved_width($row)
                if (this.fields.length && this.$table.is(':visible')) {
                    field = this.fields[this.fields.length - 1];
                    $td = this.$table.find('tr:first td.' + field.field_name)
                    if ($td.width() <= 0 || fake_column) {
                        this.$head.find('th.' + 'fake-column').show();
                        this.$table.find('td.' + 'fake-column').show();
                        this.set_saved_width($row, true);
                    }
                    else {
                        this.$head.find('th.' + 'fake-column').hide();
                        this.$table.find('td.' + 'fake-column').hide();
                    }
                }
            }
        }

        remove_saved_width() {
            this.$outer_table.find('colgroup').remove();
            this.$table.find('colgroup').remove();
        }

        set_saved_width(row, all_cols) {
            var i,
                col_group = '<colgroup>',
                len = this.fields.length,
                count = len - 1,
                field,
                width;
            this.remove_saved_width();
            if (this.options.multiselect) {
                col_group += '<col style="width: 48px">'
            }
            if (all_cols || this.master_table) {
                count = len;
            }
            for (i = 0; i < count; i++) {
                field = this.fields[i];
                width = this.get_cell_width(field.field_name);
                col_group += '<col style="width: ' + width + 'px">';
            }
            col_group += '</colgroup>',
            this.$outer_table.prepend(col_group)
            this.$table.prepend(col_group);
        }

        fill_datasource(start_rec) {
            var self = this,
                counter = 0,
                clone = this.item.clone(true);
            if (!this.datasource.length || this.item.paginate) {
                this.datasource = [];
                if (start_rec === undefined) {
                    start_rec = 0;
                }
                clone.rec_no = start_rec;
                while (!clone.eof()) {
                    self.datasource.push([clone.rec_no, null]);
                    clone.next();
                    counter += 1;
                    if (counter >= self.row_count) {
                        break;
                    }
                }
            }
        }

        fill_rows() {
            var i,
                len,
                row,
                rows,
                rec,
                item_rec_no;
            rows = ''
            item_rec_no = this.item.rec_no;
            try {
                len = this.datasource.length;
                for (i = 0; i < len; i++) {
                    this.item._cur_row = this.datasource[i][0];
                    row = this.new_row();
                    rows += row;
                }
                this.$table.html(rows);
                rows = this.$table.find("tr");
                for (i = 0; i < len; i++) {
                    this.datasource[i][1] = rows[i];
                    if (this.options.row_callback) {
                        this.item._cur_row = this.datasource[i][0];
                        this.options.row_callback($(rows[i]), this.item);
                    }
                }
            } finally {
                this.item._cur_row = item_rec_no;
            }
        }

        refresh() {
            var i,
                len,
                field,
                row, tmpRow,
                cell,
                cell_width,
                headCell,
                footCell,
                table,
                rows,
                title = '',
                rec,
                item_rec_no,
                rec_nos = [],
                info,
                is_focused,
                is_visible = this.$table.is(':visible'),
                scroll_left = this.$table_container.scrollLeft(),
                editable_val,
                container,
                self = this;

            is_focused = this.is_focused();
            if (this.options.editable && this.edit_mode && this.editor) {
                if (!is_focused) {
                    is_focused = this.editor.$input.is(':focus');
                }
                editable_val = this.editor.$input.value;
                this.hide_editor();
            }

            if (!this.item.paginate) {
                if (this.options.row_count !== this.row_count) {
                    this.calc_row_count();
                }
                this.$scroll_div.height(this.scroll_height());
            }
            this.$table.empty();
            if (this.selection_block) {
                this.selection_block.remove();
            }
            this.$outer_table.find('#top-td').attr('colspan', this.colspan);

            this.fill_datasource();
            this.fill_rows();

            row = this.$table.find("tr:first");
            if (!this.field_width_updated) {
                container = $('<div>');
                container.css("position", "absolute")
                    //~ .css("top", 0)
                    .css("top", -1000)
                    .width(this.get_element_width(this.$element));
                $('body').append(container);
                this.$element.detach();
                container.append(this.$element);

                this.$table.css('table-layout', 'auto');
                this.$outer_table.css('table-layout', 'auto');
                tmpRow = '<tr>'
                if (this.options.multiselect) {
                    tmpRow = tmpRow + '<th class="multi-select">' +
                        '<div class="text-center multi-select" style="overflow: hidden"></div>' +
                        '</th>';
                }
                len = this.fields.length;
                for (i = 0; i < len; i++) {
                    tmpRow = tmpRow + '<th class="' + this.fields[i].field_name + '" ><div style="overflow: hidden">' +
                        '<span style="font-size: xx-small;">&darr;</span>' + this.fields[i].field_caption + '</div></th>';
                }
                tmpRow = $(tmpRow + '</tr>');
                this.$table.prepend(tmpRow);
                for (var field_name in this.options.column_width) {
                    if (this.options.column_width.hasOwnProperty(field_name)) {
                        tmpRow.find("." + field_name).css("width", this.options.column_width[field_name]);
                    }
                }
                for (i = 0; i < len; i++) {
                    field = this.fields[i];
                    cell = row.find("td." + field.field_name);
                    this.set_сell_width(field.field_name, cell.outerWidth());
                }

                tmpRow.remove();

                this.$element.detach();
                this.$container.append(this.$element);

                container.remove();

                this.$table.css('table-layout', 'fixed');
                this.$outer_table.css('table-layout', 'fixed');


                this.fill_title(this.$element);
                this.fill_footer(this.$element);
                this.set_saved_width();
                if (this.item.record_count() > 0 && is_visible) {
                    this.field_width_updated = true;
                }
            } else {
                this.fill_title(this.$element);
                this.fill_footer(this.$element);
            }

            if (this.options.show_footer) {
                this.$foot.show();
            }
            this.$container.find('tfoot .pager').attr('colspan', this.colspan);

            this.syncronize();
            if (is_focused) {
                this.focus();
            }
            if (this.can_edit() && this.edit_mode && this.editor) {
                this.show_editor();
                this.editor.$input.value = editable_val;
            }
            this.update_summary();
            this.sync_col_width();
            this.$table_container.scrollLeft(scroll_left);
            if (!this.item.rec_count) {
                this.$head.find('th')
                    .css('borderBottomWidth', this.$outer_table.css('borderTopWidth'))
                    .css('borderBottomStyle', this.$outer_table.css('borderTopStyle'))
                    .css('borderBottomColor', this.$outer_table.css('borderTopColor'));
            }
        }

        check_datasource() {
            var clone = this.item.clone(),
                first_rec = undefined;
            if (this.item._dataset) {
                for (var i = 0; i < this.datasource.length; i++) {
                    if (this.item._dataset[this.datasource[i][0]] !== undefined) {
                        first_rec = this.datasource[i][0]
                        break;
                    }
                }
            }
            this.datasource = [];
            this.fill_datasource(first_rec);
        }

        build(same_field_width) {
            this.init_fields();
            this.check_datasource();
            if (this.field_width_updated !== undefined) {
                this.field_width_updated = same_field_width;
            }
            if (!this.item.selections) {
                this.options.multiselect = this.item.selections;
            }
            this.refresh();
            this.sync_col_width();
            this.syncronize();
        }

        is_focused() {
            return this.$table.get(0) === document.activeElement;
        }

        focus() {
            if (!this.is_focused()) {
                this.$table.focus();
            }
        }
    }


    class DBAbstractInput {
        constructor(field) {
            var self = this;
            this.field = field;
            this.read_only = false;
            this.is_changing = true;
        }

        create_input(field, tabIndex, container) {
            var self = this,
                align,
                height,
                width,
                $control_group,
                $label,
                $input,
                $div,
                $ul,
                $li,
                $a,
                $btn,
                $controls,
                $btnCtrls,
                $help,
                field_type = field.lookup_data_type,
                field_mask,
                inpit_btn_class = '';
            if ($('body').css('font-size') === '12px') {
                inpit_btn_class = ' btn12'
            }
            else {
                inpit_btn_class = ' btn14'
            }
            if (!field) {
                return;
            }
            if (this.label) {
                $label = $('<label class="control-label"></label>')
                    .attr("for", field.field_name).text(this.label).
                addClass(field.field_name);
                if (this.field.required) {
                    $label.addClass('required');
                }
                if (this.label_width) {
                    $label.width(this.label_width);
                }
            }
            if (field.lookup_data_type === consts.BOOLEAN) {
                $input = $('<input>')
                    .attr("type", "checkbox")
                    .click(function(e) {
                        self.field.value = !self.field.value;
                    });
            } else if (field_type === consts.IMAGE) {
                $input = $('<div>');
            } else if (field.lookup_data_type === consts.LONGTEXT || field.field_textarea) {
                $input = $('<textarea>').height('4.5em');
            } else if (!field.field_textarea) {
                $input = $('<input>').attr("type", "text")
            }
            if (tabIndex) {
                $input.attr("tabindex", tabIndex + "");
            }
            $controls = $('<div class="controls"></div>');
            if (this.label_width && !this.label_on_top) {
                $controls.css('margin-left', this.label_width + 20 + 'px');
            }
            field_mask = this.field.field_mask;
            if (!field_mask) {
                field_mask = this.field.get_mask()
            }
            if (field_mask) {
                try {
                    $input.mask(field_mask);
                } catch (e) {}
            }
            this.$input = $input;
            this.$input.addClass(field.field_name)
            if (task.old_forms) {
                this.$input.attr("id", field.field_name);
            }
            this.$input.addClass('dbinput');
            this.$input.data('dbinput', this);
            this.$input.on('focus', function(e) {
                self.focus_in(e);
            });
            this.$input.on('blur', function(e) {
                self.focus_out();
            });
            this.$input.on('mousedown', function(e) {
                self.mouseIsDown = true;
            });
            this.$input.on('mouseup', function(e) {
                if (!self.mouseIsDown) {
                    self.$input.select();
                }
                self.mouseIsDown = false;
            });
            this.$input.on('keydown', function(e) {
                self.keydown(e);
            });
            this.$input.on('keyup', function(e) {
                self.keyup(e);
            });
            this.$input.on('keypress', function(e) {
                self.keypress(e)
            });
            if (field.lookup_item && !field.master_field || field.lookup_values || field_type === consts.FILE) {
                $btnCtrls = $('<div class="input-prepend input-append"></div>');
                $btn = $('<button class="btn' + inpit_btn_class + '"type="button"><i class="icon-remove-sign"></button>');
                $btn.attr("tabindex", -1);
                $btn.click(function() {
                    field.value = null;
                });
                this.$firstBtn = $btn;
                $btnCtrls.append($btn);
                $btnCtrls.append($input);
                $btn = $('<button class="btn' + inpit_btn_class + '" type="button"><i></button>');
                $btn.attr("tabindex", -1);
                $btn.click(function() {
                    if (field.lookup_values) {
                        self.dropdown.enter_pressed();
                    }
                    else if (field.lookup_item){
                        self.select_value();
                    }
                    else {
                        if (self.field.owner.is_changing() && !self.field.owner.read_only) {
                            self.field.upload();
                        }
                    }
                });
                this.$lastBtn = $btn;
                $btnCtrls.append($btn);
                $controls.append($btnCtrls);
                if (field.lookup_values) {
                    $btnCtrls.addClass("lookupvalues-input-container");
                    $input.addClass("input-lookupvalues");
                    this.$lastBtn.find('i').addClass("icon-chevron-down");
                    this.dropdown = new DropdownList(this.field, $input);
                    if (field.filter && field.bool_filter) {
                        $input.width(36);
                    }
                }
                else if (field.lookup_item && field_type !== consts.FILE){
                    $btnCtrls.addClass("lookupfield-input-container");
                    $input.addClass("input-lookupitem");
                    this.$lastBtn.find('i').addClass("icon-list");
                    if (this.field.enable_typeahead) {
                        this.dropdown = new DropdownTypeahead(this.field,
                            $input, this.field.typeahead_options());
                    }
                }
                else {
                    var field_file;
                    if (this.field.data_type === consts.FILE) {
                        field_file = this.field.field_file;
                    }
                    else {
                        field_file = this.field.lookup_item[this.field.lookup_field].field_file;
                    }
                    $btnCtrls.addClass("lookupfield-input-container");
                    this.$lastBtn.find('i').addClass("icon-file");
                    this.$uploadBtn = this.$lastBtn
                    if (field_file.download_btn) {
                        $btn = $('<button class="btn' + inpit_btn_class + '" type="button"><i></button>');
                        $btn.attr("tabindex", -1);
                        this.$downloadBtn = $btn;
                        $btnCtrls.append($btn);
                        $controls.append($btnCtrls);
                        $btn.find('i').addClass("icon-download-alt");
                        $btn.click(function() {
                            self.field.download();
                        });
                        this.$lastBtn = $btn;
                    }

                    if (field_file.open_btn) {
                        $btn = $('<button class="btn' + inpit_btn_class + '" type="button"><i></button>');
                        $btn.attr("tabindex", -1);
                        this.$openBtn = $btn;
                        $btnCtrls.append($btn);
                        $controls.append($btnCtrls);
                        $btn.find('i').addClass("icon-play");
                        $btn.click(function() {
                            self.field.open();
                        });
                        this.$lastBtn = $btn;
                    }
                    if (field_file.open_btn && field_file.download_btn) {
                        $input.addClass("input-file3");
                    }
                    else if (field_file.open_btn || field_file.download_btn) {
                        $input.addClass("input-file2");
                    }
                    else {
                        $input.addClass("input-file");
                    }
                }
            } else {
                switch (field_type) {
                    case consts.TEXT:
                        if (field.field_textarea) {
                            $input.addClass("input-longtext");
                            $controls.append($input);
                        }
                        else {
                            $input.addClass("input-text");
                            $controls.append($input);
                        }
                        break;
                    case consts.INTEGER:
                        $input.addClass("input-integer");
                        $controls.append($input);
                        break;
                    case consts.FLOAT:
                        $input.addClass("input-float");
                        $controls.append($input);
                        break;
                    case consts.CURRENCY:
                        $input.addClass("input-currency");
                        $controls.append($input);
                        break;
                    case consts.DATE:
                    case consts.DATETIME:
                        $btnCtrls = $('<div class="input-prepend input-append"></div>');
                        $btn = $('<button class="btn' + inpit_btn_class + '" type="button"><i class="icon-remove-sign"></button>');
                        $btn.attr("tabindex", -1);
                        $btn.click(function() {
                            field.value = null;
                        });
                        this.$firstBtn = $btn;
                        $btnCtrls.append($btn);
                        if (field_type === consts.DATETIME) {
                            $btnCtrls.addClass("datetime-input-container");
                            $input.addClass("input-datetime");
                        }
                        else {
                            $btnCtrls.addClass("date-input-container");
                            $input.addClass("input-date");
                        }
                        $btnCtrls.append($input);
                        $btn = $('<button class="btn' + inpit_btn_class + '" type="button"><i class="icon-calendar"></button>');
                        $btn.attr("tabindex", -1);
                        $btn.click(function() {
                            self.show_date_picker();
                        });
                        this.$lastBtn = $btn;
                        $btnCtrls.append($btn);
                        $controls.append($btnCtrls);
                        break;
                    case consts.BOOLEAN:
                        $controls.append($input);
                        break;
                    case consts.LONGTEXT:
                        $input.addClass("input-longtext");
                        $controls.append($input);
                        break;
                    case consts.IMAGE:
                        $controls.append($input);
                        $input.dblclick(function(e) {
                            if (!self.field.read_only && self.field.data_type === consts.IMAGE && self.field.owner.is_changing() &&
                                !self.field.owner.read_only) {
                                if (e.ctrlKey || e.metaKey) {
                                    self.field.value = null;
                                }
                                else {
                                    if (self.field.field_image && self.field.field_image.camera) {
                                        self.init_camera(true);
                                    }
                                    else {
                                        self.field.upload_image();
                                    }
                                }
                            }
                        })
                        break;
                }
                align = field.data_type === consts.BOOLEAN ? 'center' : align_value[field.alignment];
                this.$input.css("text-align", align);
            }
            this.$btn_ctrls = $btnCtrls;

            if (this.label_on_top) {
                this.$control_group = $('<div class="input-container"></div>');
            } else {
                this.$control_group = $('<div class="control-group input-container"></div>');
            }
            if (this.label) {
                this.$control_group.append($label);
                if (!this.label_width) {
                    this.$control_group.addClass('label-size' + this.label_size);
                }
            }
            this.$control_group.append($controls);

            if (container) {
                container.append(this.$control_group);
            }

            $controls.find('.add-on').css('padding-top',
                parseInt($controls.find('.add-on').css('padding-top')) +
                parseInt($controls.find('.add-on').css('border-top-width')) - 1 +
                'px')
            $controls.find('.add-on').css('padding-bottom',
                parseInt($controls.find('.add-on').css('padding-bottom')) +
                parseInt($controls.find('.add-on').css('border-bottom-width')) - 1 +
                'px')

            this.form = this.$input.closest('.jam-form');
            this.field.controls.push(this);

            if (field_type !== consts.IMAGE) {
                this.$input.on('mouseenter', function() {
                    var $this = $(this);
                    if (self.error) {
                        $this.tooltip('show');
                    }
                });

                if (!this.table && this.field.field_placeholder) {
                    this.$input.attr('placeholder', this.field.field_placeholder);
                }

                if (!this.table && this.field.field_help) {
                    $help = $('<a href="#" tabindex="-1"><span class="badge help-badge">?</span></a>');
                    this.$help = $help;
                    $help.find('span')
                        .popover({
                            container: 'body',
                            placement: 'right',
                            trigger: 'hover',
                            html: true,
                            title: self.field.field_caption,
                            content: self.field.field_help
                        })
                        .click(function(e) {
                            e.preventDefault();
                        });
                    if ($btnCtrls) {
                        $controls.append($('<span class="help-badge-divider">'));
                        $controls.append($help);
                        $help.find('span').addClass('btns-help-badge')
                    }
                    else {
                        $controls.append($help);
                    }
                }
                this.$input.tooltip({
                        container: 'body',
                        placement: 'bottom',
                        title: ''
                    })
                    .on('hide hidden show shown', function(e) {
                        if (e.target === self.$input.get(0)) {
                            e.stopPropagation()
                        }
                    });
            }

            this.$input.bind('destroyed', function() {
                self.field.controls.splice(self.field.controls.indexOf(self), 1);
                try {
                    if (self.dropdown){
                        self.dropdown.destroy();
                    }
                    if (self.$help) {
                        self.$help.find('span').popover('destroy');
                    }
                    if (self.datepicker_shown) {
                        self.$input.datepicker('hide');
                    }
                }
                catch (e) {
                    console.error(e);
                }
            });

            this.update();
        }

        form_closing() {
            if (this.form) {
                return this.form.data('_closing')
            }
        }

        set_read_only(value) {
            if (this.$firstBtn) {
                this.$firstBtn.prop('disabled', value);
            }
            if (this.$lastBtn) {
                this.$lastBtn.prop('disabled', value);
            }
            if (this.$uploadBtn) {
                this.$uploadBtn.prop('disabled', value);
            }
            if (this.$downloadBtn) {
                this.$downloadBtn.prop('disabled', value);
            }
            if (this.$input) {
                this.$input.prop('disabled', value);
            }
            if (this.field.lookup_data_type === consts.FILE) {
                this.$input.prop('disabled', true);
                if (this.field.lookup_value) {
                    if (this.$openBtn) {
                        this.$openBtn.prop('disabled', false);
                    }
                    if (this.$downloadBtn) {
                        this.$downloadBtn.prop('disabled', false);
                    }
                }
            }
        }

        init_camera(dblclick) {
            var self = this;
            if (this.field.field_image && this.field.field_image.camera && !this.$video) {
                if (task._getUserMediaError && dblclick) {
                    this.field.upload_image();
                    return;
                }
                if (navigator.mediaDevices.getUserMedia) {
                    navigator.mediaDevices.getUserMedia({video: true})
                        .then(function(stream) {
                            var vid,
                                size = self.field._get_image_size(true);
                            if (!self.$video) {
                                self.$video = $('<video width="'+ size.width + ' height="'+ size.height + '" autoplay>');
                                self.$input.bind('destroyed', function() {
                                    try {
                                        self.$video[0].srcObject.getVideoTracks().forEach(
                                            function(video_track) {
                                                return video_track.stop();
                                            }
                                            //~ video_track => video_track.stop()
                                        );
                                    }
                                    catch (e) {}
                                });
                                self.$input.parent().append(self.$video)
                                self.$input.hide();
                                vid = self.$video[0];
                                vid.srcObject = stream
                                $(vid).on('dblclick', function() {
                                    var $canvas = $('<canvas id="canvas" width="' + self.$video.width() + '" height="' + self.$video.height() + '">'),
                                        context = $canvas[0].getContext('2d');
                                    $canvas.css('position', 'absolute');
                                    $canvas.css('top', -1000);
                                    $('body').append($canvas);
                                    context.drawImage(vid, 0, 0, $canvas.width(), $canvas.height());
                                    $canvas[0].toBlob(function(blob) {
                                        $canvas.remove()
                                        self.field.owner.task.upload(
                                            {
                                                blob: blob,
                                                file_name: self.field.field_name + '.png',
                                                callback: function(server_file_name, file_name) {
                                                    self.field.value = server_file_name;
                                                    self.$video.hide();
                                                    self.$input.show();
                                                    vid.srcObject.getVideoTracks().forEach(
                                                        function(video_track) {
                                                            return video_track.stop();
                                                        }
                                                        //~ video_track => video_track.stop()
                                                    );
                                                    self.$video.remove();
                                                    self.$video = undefined;
                                                }
                                            }
                                        );
                                    });
                                });
                            }
                        })
                        .catch(function(err) {
                            if (!task._getUserMediaError) {
                                task._getUserMediaError = true;
                                task.alert_error('Can not connect to the camera');
                                console.error('The following error occurred when trying to use getUserMedia: ' + err);
                                if (dblclick) {
                                    self.field.upload_image();
                                }
                            }
                        });
                }
                else {
                    alert('Sorry, your browser does not support getUserMedia');
                }
            }
        }

        update(state) {
            var placeholder,
                focused,
                self = this,
                is_changing = this.is_changing;
            if (this.field._owner_is_item()) {
                if (this.field.owner._canceling) {
                    return;
                }
                is_changing = this.field.owner.is_changing();
                if (!this.field.owner.active || this.field.owner.record_count() === 0) {
                    this.read_only = true;
                    this.is_changing = false;
                    this.set_read_only(true);
                    this.$input.val('');
                    return
                }
            }
            if (!this.removed && !this.form_closing()) {
                if (this.field.lookup_data_type === consts.IMAGE) {
                    if (this.$input.html() != this.field.get_html()) {
                        this.$input.html(this.field._get_image(true));
                    }
                    if (!this.field.value) {
                        this.init_camera();
                    }
                }
                else {
                    placeholder = this.field.field_placeholder;
                    focused = this.$input.get(0) === document.activeElement;

                    if (this.read_only !== this.field.read_only || is_changing !== this.is_changing) {
                        this.read_only = this.field.read_only;
                        this.is_changing = is_changing;
                        this.set_read_only(this.read_only || !this.is_changing);
                    }
                    if (this.field.master_field) {
                        this.set_read_only(true);
                    }
                    if (this.field.lookup_data_type === consts.BOOLEAN) {
                        if (this.field.lookup_value) {
                            this.$input.prop("checked", true);
                        } else {
                            this.$input.prop("checked", false);
                        }
                    }
                    if (this.field.lookup_values) {
                        this.$input.val(this.field.display_text);
                    } else {
                        if (focused && this.$input.val() !== this.field.text ||
                            !focused && this.$input.val() !== this.field.display_text) {
                            this.errorValue = undefined;
                            this.error = undefined;
                            if (focused && !this.field.lookup_item && !this.field.lookup_values) {
                                this.$input.val(this.field.text);
                            } else {
                                this.$input.val(this.field.display_text);
                            }
                        }
                    }
                    if (this.read_only || !this.is_changing || this.field.master_field) {
                        placeholder = '';
                    }
                    this.$input.attr('placeholder', placeholder);
                    this.updateState(true);
                }
            }
            if (state === consts.UPDATE_CLOSE) {
                this.$input.val('');
                this.set_read_only(true);
            }
        }

        keydown(e) {
            var code = (e.keyCode ? e.keyCode : e.which);
            if (code === 13 && !(this.$input.get(0).tagName === 'TEXTAREA')) {
                e.preventDefault();
            }
            if (this.field.lookup_item && !this.field.enable_typeahead && !(code === 229 || code === 9 || code == 8)) {
                e.preventDefault();
            }
            if (code === 9) {
                if (this.table && this.table.edit_mode) {
                    e.preventDefault();
                    if (e.shiftKey) {
                        this.table.prior_field();
                    } else {
                        this.table.next_field();
                    }
                }
            }
        }

        enter_pressed(e) {
            if (this.field.lookup_item && !this.field.enable_typeahead) {
                e.stopPropagation();
                e.preventDefault();
                this.select_value();
            } else if ((this.field.data_type === consts.DATE) || (this.field.data_type === consts.DATETIME)) {
                e.stopPropagation();
                e.preventDefault();
                this.show_date_picker();
            }
        }

        changed() {
            if (this.field.field_kind !== consts.ITEM_FIELD ||
                this.field.owner.active && this.field.owner.rec_count) {
                if (this.field.lookup_item || this.field.lookup_values) {
                    if (this.$input.val() !== this.field.display_text) {
                        return true
                    }
                } else {
                    if (this.$input.val() !== this.field.text) {
                        return true
                    }
                }
            }
        }

        keyup(e) {
            var typeahead,
                code = (e.keyCode ? e.keyCode : e.which);
            if (this.field.enable_typeahead) {
                typeahead = this.$input.data('jamtypeahead')
                if (typeahead && typeahead.shown) {
                    return;
                }
            }
            if (code === 13 && !e.ctrlKey && !e.shiftKey) {
                if (this.table && this.table.edit_mode) {
                    if (this.dropdown && this.dropdown.shown) {
                        return;
                    }
                    e.stopPropagation();
                    e.preventDefault();
                    this.table.close_editor();
                } else if (!(this.$input.get(0).tagName === 'TEXTAREA')){
                    this.focus_out();
                    this.$input.select();
                    this.enter_pressed(e);
                }
            } else if (code === 27) {
                if (this.table && this.table.edit_mode) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.table.item.cancel();
                    this.table.hide_editor();
                } else if (this.field.lookup_values) {
                    if (this.$input.parent().hasClass('open')) {
                        this.$input.parent().removeClass('open');
                        e.stopPropagation();
                    }
                }
                else if (this.changed()) {
                    this.update();
                    this.$input.select();
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        }

        keypress(e) {
            var code = e.which;
            if (code === 13 && !(this.$input.get(0).tagName === 'TEXTAREA')) {
                e.preventDefault();
            }
            else {
                if (this.field.lookup_item && !this.field.enable_typeahead) {
                    e.preventDefault();
                }
                if (this.$input.is('select')) {

                }
                else if (code && !this.field.valid_char_code(code)) {
                    e.preventDefault();
                }
            }
        }

        show_date_picker() {
            var self = this,
                format;
            if (this.field.data_type === consts.DATE) {
                format = locale.D_FMT;
            } else if (this.field.data_type === consts.DATETIME) {
                format = locale.D_T_FMT;
            }

            this.$input.datepicker(
                {
                    weekStart: parseInt(language.week_start, 10),
                    format: format,
                    daysMin: language.days_min.slice(1, -1).split(','),
                    months: language.months.slice(1, -1).split(','),
                    monthsShort: language.months_short.slice(1, -1).split(','),
                    date: this.field.value
                })
                .on('show', function(e) {
                    if (e.target === self.$input.get(0)) {
                        e.stopPropagation();
                        self.$input.datepicker().attr('data-weekStart', 1);
                    }
                })
                .on('hide hidden shown', function(e) {
                    if (e.target === self.$input.get(0)) {
                        e.stopPropagation()
                    }
                })
                .on('changeDate', function(e) {
                    self.field.value = e.date;
                    self.$input.datepicker('hide');
                });
            this.$input.datepicker('show');
            this.datepicker_shown = true;
        }

        select_value() {
            if (this.field.on_entry_button_click) {
                this.field.on_entry_button_click.call(this.item, this.field);
            } else {
                this.field.select_value();
            }
        }

        change_field_text() {
            var result = true,
                data_type = this.field.data_type,
                text;
            this.errorValue = undefined;
            this.error = undefined;
            if (this.field.lookup_item || this.field.lookup_values) {
                if (this.$input.val() !== this.field.lookup_text) {
                    this.$input.val(this.field.display_text);
                }
            } else {
                try {
                    text = this.$input.val();
                    if (text !== this.field.text) {
                        if (this.field._owner_is_item() && !this.field.owner.is_changing()) {
                            this.field.owner.edit();
                        }
                        if (text === '') {
                            this.field.value = null;
                        } else {
                            this.field.text = text;
                            if (!(this.field._owner_is_item() && !this.field.owner.rec_count)) {
                                let err = this.field.check_valid();
                                if (err) {
                                    throw new Error(err);
                                }
                                if (this.$input.is(':visible')) {
                                    this.$input.val(text);
                                }
                            }
                        }
                    }
                } catch (e) {
                    this.errorValue = text;
                    this.error = e;
                    if (!(e.name && e.name === 'AbortError')) {
                        this.updateState(false);
                    }
                    if (e.stack) {
                        console.error(e.stack);
                    }
                    else {
                        console.error(e);
                    }
                    result = false;
                }
            }
            return result;
        }

        focus_in(e) {
            if (!this.form_closing()) {
                this.hideError();
                if (this.field.lookup_item && !this.field.enable_typeahead) {
                    this.$input.val(this.field.display_text);
                } else {
                    if (this.errorValue) {
                        this.$input.val(this.errorValue);
                    } else if (this.field.lookup_item || this.field.lookup_values) {
                        this.$input.val(this.field.display_text);
                    } else {
                        this.$input.val(this.field.text);
                    }
                    if (!this.mouseIsDown) {
                        this.$input.select();
                        this.mouseIsDown = false;
                    }
                }
                this.mouseIsDown = false;
                this.updateState(true);
            }
        }

        focus_out(e) {
            var result = false;
            if (!this.changed()) {
                if (this.field.field_kind !== consts.ITEM_FIELD || this.field.owner.rec_count) {
                    this.$input.val(this.field.display_text);
                }
                return;
            }
            if (this.table && this.table.edit_mode) {
                if (this.dropdown && this.dropdown.shown) {
                    return;
                }
                this.table.close_editor();
                result = true;
            }
            if (this.field.data_type === consts.BOOLEAN) {
                result = true;
            } else if (!this.table && this.change_field_text()) {
                if (this.$input.is(':visible')) {
                    this.$input.val(this.field.display_text);
                }
                result = true;
            }
            this.updateState(result);
        }

        update_form(update) {
            if (update) {
                let form = this.$input.closest('.jam-form');
                if (form.hasClass('modal')) {
                    this.field.owner.update_form(form);
                }
            }
        }

        hide(update_form) {
            this.$input.closest('.control-group').hide();
            this.update_form(update_form);
        }

        show(update_form) {
            this.$input.closest('.control-group').show();
            this.update_form(update_form);
        }

        updateState(value) {
            if (value) {
                if (this.$control_group) {
                    this.$control_group.removeClass('error');
                }
                this.errorValue = undefined;
                this.error = undefined;
                this.$input.tooltip('hide')
                    .attr('data-original-title', '')
                    .tooltip('fixTitle');
                this.hideError();
            } else {
                task.alert_error(this.error, {replace: false});
                this.showError();
                if (this.$control_group) {
                    this.$control_group.addClass('error');
                }
                this.$input.tooltip('hide')
                    .attr('data-original-title', this.error)
                    .tooltip('fixTitle');
            }
        }

        showError(value) {}

        hideError(value) {}

        focus() {
            this.$input.focus();
        }
    }


    class DBTableInput extends DBAbstractInput {
        constructor(table, field) {
            super(field);
            this.table = table;
            this.create_input(field, 0);
            this.$input.attr("autocomplete", "off");
            this.$input.addClass('dbtableinput');
        }
    }


    class DBInput extends DBAbstractInput {
        constructor(field, index, container, options, label) {
            super(field);
            if (this.field.owner && this.field.owner.edit_form &&
                this.field.owner.edit_form.hasClass("modal")) {
                this.$edit_form = this.field.owner.edit_form;
            }
            this.label = label;
            this.label_width = options.label_width;
            this.label_on_top = options.label_on_top;
            this.label_size = options.label_size;
            if (!this.label_size) {
                this.label_size = 3;
            }
            if (!this.label) {
                this.label = this.field.field_caption;
            }
            this.create_input(field, index, container);
        }

        showError(value) {
            if (this.$edit_form && this.$edit_form.hasClass("normal-modal-border")) {
                this.$edit_form.removeClass("nomal-modal-border");
                this.$edit_form.addClass("error-modal-border");
            }
        }

        hideError(value) {
            if (this.$edit_form && this.$edit_form.hasClass("error-modal-border")) {
                this.$edit_form.removeClass("error-modal-border");
                this.$edit_form.addClass("nomal-modal-border");
            }
        }
    }


    class Dropdown {
        constructor(field, element, options) {
            this.$element = element;
            this.field = field;
            this.options = options;
        }

        init() {
            var default_options =
                {
                    menu: '<ul class="typeahead dropdown-menu"></ul>',
                    item: '<li><a href="#"></a></li>',
                    length: 10,
                    min_length: 1
                }
            this.options = $.extend({}, default_options, this.options);
            this.$menu = $(this.options.menu);
        }

        show() {
            var pos;
            if (this.$element) {
                pos = $.extend({}, this.$element.offset(), {
                    height: this.$element[0].offsetHeight
                });

                this.$menu
                    .appendTo($('body'))
                    .css({
                        top: pos.top + pos.height,
                        left: pos.left,
                        "min-width": this.$element.innerWidth(),
                        "max-width": $(window).width() - this.$element.offset().left - 20,
                        "overflow": "hidden"
                    })
                    .show()

                this.shown = true
                this.mousedover = false
                return this
            }
        }

        hide() {
            this.$menu.hide();
            this.$menu.detach();
            this.shown = false;
            return this;
        }

        destroy() {
            this.$element = undefined;
            this.$menu.remove();
        }

        get_items(event) {
            var items;
            if (this.$element) {
                this.query = this.$element.val()
                if (!this.query || this.query.length < this.min_length) {
                    return this.shown ? this.hide() : this
                }
                items = $.isFunction(this.source) ? this.source(this.query, $.proxy(this.process, this)) : this.source
                return items ? this.process(items) : this
            }
        }

        lookup(event) {
            this.get_items(event);
        }

        process(items) {
            var that = this

            items = $.grep(items, function(item) {
                return that.matcher(item)
            })

            if (!items.length) {
                return this.shown ? this.hide() : this
            }

            return this.render(items.slice(0, this.length)).show()
        }

        matcher(item) {
            return true
        }

        highlighter(item) {
            return highlight(item, this.query);
        }

        render(items) {
            var that = this

            items = $(items).map(function(i, values) {
                var str;
                i = $(that.options.item).data('id-value', values[0]);
                str = that.highlighter(values[1]);
                if (str.trim() === '') {
                    str = '&nbsp';
                }
                i.find('a').html(str);
                return i[0]
            })

            items.first().addClass('active')
            this.$menu.html(items)
            return this
        }

        next(event) {
            var active = this.$menu.find('li.active').removeClass('active'),
                next = active.next()

            if (!next.length) {
                next = $(this.$menu.find('li')[0])
            }

            next.addClass('active')
        }

        prev(event) {
            var active = this.$menu.find('.active').removeClass('active'),
                prev = active.prev()

            if (!prev.length) {
                prev = this.$menu.find('li').last()
            }

            prev.addClass('active')
        }

        listen() {
            this.$element
                .on('focus', $.proxy(this.focus, this))
                .on('blur', $.proxy(this.blur, this))
                .on('keypress', $.proxy(this.keypress, this))
                .on('keyup', $.proxy(this.keyup, this))

            if (this.eventSupported('keydown')) {
                this.$element.on('keydown', $.proxy(this.keydown, this))
            }

            this.$menu
                .on('click', $.proxy(this.click, this))
                .on('mouseenter', 'li', $.proxy(this.mouseenter, this))
                .on('mouseleave', 'li', $.proxy(this.mouseleave, this))
        }

        eventSupported(eventName) {
            var isSupported = eventName in this.$element
            if (!isSupported) {
                this.$element.setAttribute(eventName, 'return;')
                isSupported = typeof this.$element[eventName] === 'function'
            }
            return isSupported
        }

        move(e) {
            if (!this.shown) return

            switch (e.keyCode) {
                case 9: // tab
                case 13: // enter
                case 27: // escape
                    e.preventDefault()
                    break

                case 38: // up arrow
                    e.preventDefault()
                    this.prev()
                    break

                case 40: // down arrow
                    e.preventDefault()
                    this.next()
                    break
            }

            e.stopPropagation()
        }

        keydown(e) {
            this.suppressKeyPressRepeat = ~$.inArray(e.keyCode, [40, 38, 9, 13, 27])
            this.move(e)
        }

        keypress(e) {
            if (this.suppressKeyPressRepeat) return
            this.move(e)
        }

        keyup(e) {
            if (!e.ctrlKey && !e.shiftKey) {
                switch (e.keyCode) {
                    case 40: // down arrow
                    case 38: // up arrow
                    case 16: // shift
                    case 17: // ctrl
                    case 18: // alt
                        break

                    case 9: // tab
                    case 13: // enter
                        if (!this.shown) {
                            if (e.keyCode === 13 && this.$element && !this.$element.table) {
                                this.enter_pressed();
                            }
                        }
                        else {
                            this.select()
                        }
                        break

                    case 27: // escape
                        if (!this.shown) return
                        this.field.update_controls();
                        if (this.$element) {
                            this.$element.select();
                        }
                        this.hide();
                        break

                    default:
                        this.lookup()
                }
                e.stopPropagation();
                e.preventDefault();
            }
        }

        focus(e) {
            this.focused = true
        }

        blur(e) {
            this.focused = false
            if (!this.mousedover && this.shown) {
            //~ if (this.shown) {
                this.hide();
            }
        }

        click(e) {
            e.stopPropagation()
            e.preventDefault()
            this.select()
            this.$element.focus()
        }

        mouseenter(e) {
            this.mousedover = true
            this.$menu.find('li.active').removeClass('active')
            $(e.currentTarget).addClass('active')
        }

        mouseleave(e) {
            this.mousedover = false
            if (!this.focused && this.shown) this.hide()
        }
    }

    class DropdownList extends Dropdown {
        constructor(field, element, options) {
            super(field, element, options);
            this.init();
            this.listen();
        }

        matcher(item) {
            if (this.query) {
                return ~item[1].toLowerCase().indexOf(this.query.toLowerCase());
            }
            else {
                return true;
            }
        }

        select() {
            var $li = this.$menu.find('.active');
            if (this.field.owner && this.field.owner.is_changing && !this.field.owner.is_changing()) {
                this.field.owner.edit();
            }
            this.field.value = $li.data('id-value');
            return this.hide();
        }

        enter_pressed() {
            this.query = '';
            if (this.$element) {
                this.$element.focus();
            }
            this.process(this.field.lookup_values);
        }

        source(query, process) {
            let data = [];
            this.field.lookup_values.forEach(function(item) {
                if (item[1].toLowerCase().indexOf(query.toLowerCase()) !== -1) {
                    data.push(item);
                }
                return process(data);
            });
        }
    }


    class DropdownTypeahead extends Dropdown {
        constructor(field, element, options) {
            super(field, element, options);
            this.init();
            this.source = this.options.source;
            this.lookup_item = this.options.lookup_item;
            this.listen();
        }

        lookup(event) {
            var self = this;
            clearTimeout(this.timeOut);
            this.timeOut = setTimeout(function() { self.get_items(event) }, 400);
        }

        select() {
            var $li = this.$menu.find('.active'),
                id_value = $li.data('id-value');
            this.lookup_item.locate(this.lookup_item._primary_key, id_value);
            this.lookup_item.set_lookup_field_value();
            return this.hide();
        }

        enter_pressed() {
            this.field.select_value();
        }
    }

    function round(num, dec) {
        if (dec === undefined) {
            dec = 0;
        }
        let result = Number(Math.round(Math.abs(num) + 'e' + dec) + 'e-' + dec);
        if (isNaN(result)) {
            result = 0;
        }
        if (num < 0) {
            result = -result;
        }
        return result;
    }

    function highlight(text, search) {
        var i = 0,
            result = text,
            substr,
            start,
            str,
            strings,
            pos,
            p = [];
        if (search) {
            text += '';
            strings = search.toUpperCase().split(' ')
            for ( i = 0; i < strings.length; i++) {
                str = text.toUpperCase();
                substr = strings[i];
                if (substr) {
                    start = 0;
                    while (true) {
                        pos = str.indexOf(substr);
                        if (pos === -1) {
                            break;
                        }
                        else {
                            p.push([start + pos, substr.length]);
                            str = str.substr(pos + substr.length)
                            start += pos + substr.length;
                        }
                    }
                }
            }
            if (p.length) {
                p.sort(function(a, b) {
                    return a[0] - b[0]
                });
                result = '';
                start = 0
                for (i = 0; i < p.length; i++) {
                    if (p[i][0] < start) {
                        if (p[i][0] + p[i][1] < start) {
                            continue;
                        }
                        else {
                            p[i][1] = start - p[i][0];
                            p[i][0] = start;
                        }
                    }
                    result += text.substr(start, p[i][0] - start)
                    result += '<strong class="search-highlighted">' + text.substr(p[i][0], p[i][1]) + '</strong>';
                    start = p[i][0] + p[i][1];
                }
                if (start) {
                    result += text.substr(start);
                }
            }
        }
        return result
    }

    $.event.special.destroyed = {
        remove: function(o) {
            if (o.handler) {
                o.handler();
            }
        }
    };

    window.task = new Task();
    window.task.Item = Item;

})(jQuery);
