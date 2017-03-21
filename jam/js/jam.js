
(function($) {
    "use strict";

    var settings,
        language,
        consts = {
            "RESPONSE": 1,
            "NOT_LOGGED": 2,
            "UNDER_MAINTAINANCE": 3,
            "NO_PROJECT": 4,

            "TEXT": 1,
            "INTEGER": 2,
            "FLOAT": 3,
            "CURRENCY": 4,
            "DATE": 5,
            "DATETIME": 6,
            "BOOLEAN": 7,
            "BLOB": 8,

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
            "REC_CONTROLS_INFO": 1,
            "REC_CHANGE_ID": 2,

            "UPDATE_OPEN": 0,
            "UPDATE_DELETE": 1,
            "UPDATE_CANCEL": 2,
            "UPDATE_APPEND": 3,
            "UPDATE_INSERT": 4,
            "UPDATE_SCROLLED": 5,
            "UPDATE_CONTROLS": 6,
            "UPDATE_REFRESH": 7,
            "UPDATE_CLOSE": 8,
            "UPDATE_STATE": 9
        },
        alignValue = ['', 'left', 'center', 'right'],
        filterValue = ['eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in', 'not_in',
            'range', 'isnull', 'exact', 'contains', 'startwith', 'endwith',
            'contains_all'
        ];


    /**********************************************************************/
    /*                        AbsrtactItem class                          */
    /**********************************************************************/

    function AbsrtactItem(owner, ID, item_name, caption, visible, type, js_filename) {
        if (visible === undefined) {
            visible = true;
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
        this.modal_options = {
            width: 560,
            left: undefined,
            top: undefined,
            close_focusout: false,
            transition: false,
            title: '',
            fields: [],
            close_button: true,
            close_caption: true,
            close_on_escape: true,
            show_history: false,
            print: false,
        };
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

    AbsrtactItem.prototype = {
        constructor: AbsrtactItem,

        types: ["root", "users", "roles", "tasks", 'task',
            "items", "items", "tables", "reports",
            "item", "item", "table", "report", "detail"
        ],

        get_master_field: function(fields, master_field) {
            var i = 0,
                len = fields.length;
            for (; i < len; i++) {
                if (fields[i].ID == master_field) {
                    return fields[i];
                }
            }
        },

        each_item: function(callback) {
            var i = 0,
                len = this.items.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.items[i], this.items[i], i);
                if (value === false) {
                    break;
                }
            }
        },

        all: function(func) {
            var i = 0,
                len = this.items.length;
            func.call(this, this);
            for (; i < len; i++) {
                this.items[i].all(func);
            }
        },

        find: function(item_name) {
            var i = 0,
                len = this.items.length;
            for (; i < len; i++) {
                if (this.items[i].item_name === item_name) {
                    return this.items[i];
                }
            }
        },

        item_by_ID: function(id_value) {
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
        },

        addChild: function(ID, item_name, caption, visible, type, js_filename) {
            var NewClass;
            if (this.getChildClass) {
                NewClass = this.getChildClass();
                if (NewClass) {
                    return new NewClass(this, ID, item_name, caption, visible, type, js_filename);
                }
            }
        },

        send_request: function(request, params, callback) {
            return this.task.process_request(request, this, params, callback);
        },

        init: function(info) {
            var i = 0,
                items = info.items,
                child,
                len = items.length,
                item_info;
            for (; i < len; i++) {
                item_info = items[i][1];
                child = this.addChild(item_info.id, item_info.name,
                    item_info.caption, item_info.visible, item_info.type, item_info.js_filename);
                child._default_order = item_info.default_order;
                child._primary_key = item_info.primary_key;
                child._deleted_flag = item_info.deleted_flag;
                child._master_id = item_info.master_id;
                child._master_rec_id = item_info.master_rec_id;
                child.keep_history = item_info.keep_history;
                child.lock_on_edit = item_info.lock_on_edit;
                child.prototype_ID = item_info.prototype_ID
                if (child.initAttr) {
                    child.initAttr(item_info);
                }
                child.init(item_info);
            }
        },

        bind_items: function() {
            var i = 0,
                len = this.items.length;
            if (this.bind_item) {
                this.bind_item();
            }
            for (; i < len; i++) {
                this.items[i].bind_items();
            }
        },

        script_loaded: function() {
            if (this.js_filename) {
                return this.task._script_cache[this.js_filename];
            } else {
                return true;
            }
        },

        _check_args: function(args) {
            var i,
                result = {};
            for (i = 0; i < args.length; i++) {
                result[typeof args[i]] = args[i];
            }
            return result;
        },

        load_script: function(js_filename, callback, onload) {
            var self = this,
                url,
                s0,
                s;
            if (js_filename && !this.task._script_cache[js_filename]) {
                s = document.createElement('script');
                s0 = document.getElementsByTagName('script')[0];
                url = js_filename;

                s.src = url;
                s.type = "text/javascript";
                s.async = true;
                s0.parentNode.insertBefore(s, s0);
                s.onload = function() {
                    self.task._script_cache[js_filename] = true;
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
        },

        load_module: function(callback) {
            this.load_modules([this], callback);
        },

        load_modules: function(item_list, callback) {
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
                if (!item.script_loaded()) {
                    list.push(item);
                }
                if (item.details && item.each_detail) {
                    item.each_detail(function(d) {
                        if (!d.script_loaded()) {
                            list.push(d);
                        }
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
        },

        bind_handlers: function() {
            var events = task.events['events' + this.ID];

            this._events = [];
            for (var event in events) {
                if (events.hasOwnProperty(event)) {
                    this[event] = events[event];
                    this._events.push([event, events[event]]);
                }
            }
        },

        bind_events: function() {
            var i = 0,
                len = this.items.length;

            this.bind_handlers();

            for (; i < len; i++) {
                this.items[i].bind_events();
            }
        },

        can_view: function() {
            return this.task.has_privilege(this, 'can_view');
        },

        _search_template: function(name, suffix) {
            var template,
                search = "." + name;
            if (suffix) {
                search = "." + name + "-" + suffix
            }
            template = this.task.templates.find(search);
            if (template.length) {
                return template;
            }
        },

        find_template: function(suffix, options) {
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
                    if (!template) {
                        template = this._search_template("default-details", suffix);
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
        },

        server: function(func_name, params, callback) {
            var args,
                res,
                err,
                result;
            if (!callback) {
                args = this._check_args(arguments);
                callback = args['function'];
            }
            if (params === undefined || params === callback) {
                params = [];
            } else if (!$.isArray(params)) {
                params = [params];
            }
            if (callback) {
                this.send_request('server_function', [func_name, params], function(result) {
                    res = result[0];
                    err = result[1];
                    callback.call(this, res, err);
                    if (err) {
                        throw err;
                    }
                });
            } else {
                result = this.send_request('server_function', [func_name, params]);
                res = result[0];
                err = result[1];
                if (err) {
                    throw err;
                } else {
                    return res;
                }
            }
        },

        makeFormModal: function(form, options, suffix) {
            var $doc,
                $form,
                $title,
                mouseX,
                mouseY,
                defaultOptions = {
                    title: this.item_caption,
                    close_caption: true,
                    close_button: true,
                    print: false
                };

            function captureMouseMove(e) {
                if (mouseX) {
                    e.preventDefault();
                    $title.css('cursor', 'auto');
                    $form.css('margin-left', parseInt($form.css('margin-left'), 10) + e.screenX - mouseX);
                    $form.css('margin-top', parseInt($form.css('margin-top'), 10) + e.screenY - mouseY);
                    mouseX = e.screenX;
                    mouseY = e.screenY;
                }
            }

            function releaseMouseMove(e) {
                mouseX = undefined;
                mouseY = undefined;
                $doc.off("mousemove.modalform");
                $doc.off("mouseup.modalform");
            }

            options = $.extend({}, defaultOptions, options);
            if (!options.title) {
                options.title = '&nbsp';
            }
            $form = $(
                '<div class="modal hide normal-modal-border" tabindex="-1" data-backdrop="static">' +
                '<div class="modal-header">' +
                '</div>' +
                '</div>'
            );
            $doc = $(document);
            this._set_form_options($form, options);
            $title = $form.find('.modal-title');
            $title.on("mousedown", function(e) {
                mouseX = e.screenX;
                mouseY = e.screenY;
                $doc.on("mousemove.modalform", captureMouseMove);
                $doc.on("mouseup.modalform", releaseMouseMove);
            });

            $title.on("mousemove", function(e) {
                $(this).css('cursor', 'move');
            });

            $form.append(form);
            return $form;
        },

        _set_form_options: function(form, options, form_name) {
            var self = this,
                header = form.find('.modal-header'),
                title = header.find('.modal-title'),
                closeCaption = '',
                close_button = '',
                printCaption = '',
                print_button = '',
                history_button = '';
            if (options.close_button) {
                if (language && options.close_caption) {
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
            if (options.show_history && this.keep_history) {
                history_button = '<i id="history-btn" class="icon-film" style="float: right; margin: 5px;"></i>';
            }
            if (!title.length) {
                title = ('<h4 class="modal-title">' + options.title + '</h4>');
            } else {
                title.detach();
                title.html(options.title);
            }
            header.empty();
            header.append(close_button + history_button + print_button);
            header.append(title);
            header.find("#close-btn").css('cursor', 'default').click(function(e) {
                if (form_name) {
                    self._close_form(form_name);
                }
            });
            header.find('#print-btn').css('cursor', 'default').click(function(e) {
                self.print_message(form.find(".modal-body").clone());
            });
            header.find('#history-btn').css('cursor', 'default').click(function(e) {
                self.show_history();
            });
        },

        _close_modeless_form: function(formName) {
            var self = this;
            if (this[formName]) {
                this._close_form(formName);
            }
            if (this[formName]) {
                this[formName].bind('destroyed', function() {
                    self._close_modeless_form(formName);
                });
                throw this.item_name + " - can't close form";
            }
        },

        _process_key_event: function(form, handler, event) {
            if (form._form_disabled) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
            }
            else {
                if (event.which !== 116) { //F5
                    event.stopPropagation();
                }
                if (handler) {
                    handler.call(this, event);
                }
            }
        },

        _create_form: function(suffix, options) {
            var self = this,
                formName = suffix + '_form',
                keySuffix = formName + '.' + this.item_name,
                item_options = this[suffix + '_options'];

            if (this[formName] && options.container) {
                this._close_modeless_form(formName);
            }
            if (options.container) {
                options.container.empty();
            }
            this[formName] = $("<div></div>").append(this.find_template(suffix, item_options));
            if (!options.container) {
                this[formName] = this.makeFormModal(this[formName], item_options);
            }
            if (this[formName]) {
                this[formName]._options = options;
                this[formName].tabindex = 1;
                if (options.container) {
                    $(window).on("keyup." + keySuffix, function(e) {
                        self._process_key_event(self[formName], options.onKeyUp, e);
                    });
                    $(window).on("keydown." + keySuffix, function(e) {
                        self._process_key_event(self[formName], options.onKeyDown, e);
                    });
                    options.container.append(this[formName]);
                    this[formName].bind('destroyed', function() {
                        self._close_modeless_form(formName);
                    });
                    if (options.beforeShow) {
                        options.beforeShow.call(this);
                    }
                    if (options.onShown) {
                        options.onShown.call(this);
                    }
                } else {
                    if (this[formName].hasClass("modal")) {
                        this[formName].on("show", function(e) {
                            e.stopPropagation();
                            if (options.beforeShow) {
                                options.beforeShow.call(self, e);
                            }
                            if (self[formName].title) {
                                item_options.title = self[formName].title;
                            }
                            if (self[formName].modal_width) {
                                item_options.width = self[formName].modal_width;
                            }
                            self._set_form_options(self[formName], item_options, formName);
                        });

                        this[formName].on("shown", function(e) {
                            e.stopPropagation();
                            if (options.onShown) {
                                options.onShown.call(self, e);
                            }
                        });

                        this[formName].on("hide", function(e) {
                            var canClose = true;
                            e.stopPropagation();
                            if (options.onHide) {
                                canClose = options.onHide.call(self, e);
                            }
                            if (canClose === false) {
                                e.preventDefault();
                                self[formName].data('_closing', false);
                            }
                        });

                        this[formName].on("hidden", function(e) {
                            e.stopPropagation();
                            if (options.onHidden) {
                                options.onHidden.call(self, e);
                            }
                            self[formName].remove();
                            self[formName] = undefined;
                        });

                        this[formName].on("keydown." + keySuffix, function(e) {
                            self._process_key_event(self[formName], options.onKeyDown, e);
                        });

                        this[formName].on("keyup." + keySuffix, function(e) {
                            self._process_key_event(self[formName], options.onKeyUp, e);
                        });

                        this[formName].modal({
                            item: this,
                            form_name: formName,
                            item_options: item_options
                        });
                    }
                }
            }
        },

        _close_form: function(formName) {
            var self = this,
                form = this[formName],
                canClose,
                keySuffix = formName + '.' + this.item_name;
            if (form) {
                form.data('_closing', true);
                if (form.hasClass('modal')) {
                    setTimeout(
                        function() {
                            form.modal('hide');
                        },
                        100
                    );
                } else {
                    if (form._options && form._options.onHide) {
                        canClose = form._options.onHide.call(self);
                    }
                    if (canClose !== false) {
                        form._options.onHidden.call(self);
                        $(window).off("keydown." + keySuffix);
                        $(window).off("keyup." + keySuffix);
                        this[formName] = undefined;
                        form.remove();
                    }
                }
            }
        },

        _disable_form: function(form) {
            if (form) {
                form.css('pointer-events', 'none');
                form._form_disabled = true;
            }
        },

        _enable_form: function(form) {
            if (form) {
                form.css('pointer-events', 'auto');
                form._form_disabled = false;
            }
        },

        print_message: function(html) {
            var win = window.frames["dummy"],
                css = $("link[rel='stylesheet']"),
                head = '<head>';
            css.each(function(i, e) {
                head += '<link href="' + e.href + '" rel="stylesheet">';
            });
            head += '</head>';
            win.document.write(head + '<body onload="window.print()">' + html.html() + '</body>');
            $("link[rel='stylesheet']").clone().appendTo($("dummy").contents().find("head"));
            win.document.close();
        },

        message: function(mess, options) {
            var tab = 1,
                self = this,
                default_options = {
                    title: '',
                    width: 400,
                    height: undefined,
                    margin: undefined,
                    buttons: undefined,
                    default_button: undefined,
                    print: false,
                    text_center: false,
                    button_min_width: 100,
                    center_buttons: false,
                    close_button: true,
                    close_on_escape: true
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

            $element = this.makeFormModal($(el), options);

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
                        .attr("tabindex", tab)
                        .css("min-width", options.button_min_width)
                        .html(key)
                        .click(function(e) {
                            var key = $(this).data('key');
                            setTimeout(function() {
                                    try {
                                        if (buttons[key]) {
                                            buttons[key].call(self);
                                        }
                                    }
                                    catch (e) {}
                                    $element.modal('hide');
                                },
                                0
                            );

                        })
                    );
                    tab++;
                }
            }

            $element.on("shown", function(e) {
                e.stopPropagation();
            });

            $element.on("hide", function(e) {
                e.stopPropagation();
            });

            $element.on("hidden", function(e) {
                e.stopPropagation();
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
                    self.print_message($element.find(".modal-body").clone());
                }
            });

            $element.modal({
                width: options.width,
                height: options.height,
                keyboard: options.close_on_escape
            });
            return $element;
        },

        question: function(mess, yesCallback, noCallback, options) {
            var buttons = {},
                default_options = {
                    buttons: buttons,
                    margin: "20px 20px",
                    text_center: true,
                    center_buttons: true
                };
            options = $.extend({}, default_options, options);
            buttons[language.yes] = yesCallback;
            buttons[language.no] = noCallback;
            return this.message(mess, options);
        },

        warning: function(mess, callback, options) {
            var buttons = {"OK": callback},
                default_options = {
                    buttons: buttons,
                    margin: "20px 20px",
                    text_center: true,
                    center_buttons: true
                }
            options = $.extend({}, default_options, options);
            return this.message(mess, options);
        },

        show_message: function(mess, options) {
            return this.message(mess, options);
        },

        hide_message: function($element) {
            $element.modal('hide');
        },

        yes_no_cancel: function(mess, yesCallback, noCallback, cancelCallback) {
            var buttons = {};
            buttons[language.yes] = yesCallback;
            buttons[language.no] = noCallback;
            buttons[language.cancel] = cancelCallback;
            return this.message(mess, {
                buttons: buttons,
                margin: "20px 20px",
                text_center: true,
                width: 500,
                center_buttons: true
            });
        },

        display_history: function(hist) {
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
                master = self.master.copy({handlers: false}),
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
                    field,
                    field_name,
                    changes = JSON.parse(h.changes.value),
                    field_arr,
                    details_arr;

                if (h.operation.value === consts.RECORD_DELETED) {
                    content = '<p>Record deleted</p>'
                }
                else if (h.operation.value === consts.RECORD_DETAILS_MODIFIED) {
                    content = '<p>Details modified</p>'
                }
                else if (changes) {
                    field_arr = changes[0];
                    details_arr = changes[1];
                    if (field_arr) {
                        for (i = 0; i < field_arr.length; i++) {
                            field = item.field_by_ID(field_arr[i][0]);
                            if (field && !field.system_field()) {
                                field_name = field.field_caption;
                                if (field.lookup_item) {
                                    if (!lookups[field.lookup_item.ID]) {
                                        lookups[field.lookup_item.ID] = [];
                                    }
                                    field.set_data(field_arr[i][1]);
                                    old_value = field.value;
                                    field.set_data(field_arr[i][2]);
                                    new_value = field.value;
                                    if (old_value) {
                                        lookups[field.lookup_item.ID].push([field.lookup_field, old_value]);
                                        old_value = '<span class="' + field.lookup_field + '_' + old_value + '">value is loading</span>';
                                    }
                                    if (new_value) {
                                        lookups[field.lookup_item.ID].push([field.lookup_field, new_value]);
                                        new_value = '<span class="' + field.lookup_field + '_' + new_value + '">value is loading</span>'
                                    }
                                }
                                else {
                                    field.set_data(field_arr[i][1]);
                                    old_value = field.display_text;
                                    if (field.raw_value === null) {
                                        old_value = ' '
                                    }
                                    field.set_data(field_arr[i][2]);
                                    new_value = field.display_text;
                                    if (field.raw_value === null) {
                                        new_value = ' '
                                    }
                                }
                                if (h.operation.value === consts.RECORD_INSERTED) {
                                    content += '<p>' + self.task.language.field + ' <b>' + field_name + '</b>: ' +
                                        self.task.language.new_value + ': <b>' + new_value + '</b></p>';
                                }
                                else if (h.operation.value === consts.RECORD_MODIFIED) {
                                    content += '<p>' + self.task.language.field + ' <b>' + field_name + '</b>: ' +
                                        self.task.language.old_value + ': <b>' + old_value + '</b> ' +
                                        self.task.language.new_value + ': <b>' + new_value + '</b></p>';
                                }
                            }
                        }
                    }
                }
                if (h.user.value) {
                    user = self.task.language.by_user + ' ' + h.user.value;
                }
                acc.find('.accordion-toggle').html(h.date.format_date_to_string(h.date.value, '%d.%m.%Y %H:%M:%S') + ': ' +
                    h.operation.display_text + ' ' + user);
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
                                        acc_div.find("." + f.field_name + '_' + l._primary_key_field.value).text(f.value);
                                    }
                                });
                            });
                        })
                    }
                }
            }
        },

        show_history: function() {
            var self = this,
                hist = this.task.history_item.copy();
            hist.set_where({item_id: this.ID, item_rec_id: this.field_by_name(this._primary_key).value})
            hist.set_order_by(['-date']);
            hist.open(function() {
                self.display_history(hist);
            });
        },

        is_empty_obj: function(obj) {
            for (var prop in obj) {
                if (obj.hasOwnProperty(prop))
                    return false;
            }
            return true;
        },

        emptyFunc: function() {},

        abort: function(message) {
            message = message ? ' - ' + message : '';
            throw 'execution aborted: ' + this.item_name + message;
        },

        log_message: function(message) {
            if (this.task.settings.DEBUGGING) {
                message = message ? ' message: ' + message : '';
                console.log(this.item_name + message);
            }
        }
    };

    /**********************************************************************/
    /*                             Task class                             */
    /**********************************************************************/

    Task.prototype = new AbsrtactItem();

    function Task(item_name, caption) {
        var self = this;
        AbsrtactItem.call(this, undefined, 0, item_name, caption, true);
        this.task = this;
        this.user_info = {};
        this._script_cache = {};
        this.gridId = 0;
        //~ $('body').on('mousedown.context_menu', function(e) {
            //~ if (self.$context_menu) {
                //~ self.$context_menu.hide();
                //~ self.$context_menu.detach();
                //~ self.$context_menu_parent.append(self.$context_menu);
                //~ self.$context_menu = undefined;
            //~ }
        //~ });
    }

    $.extend(Task.prototype, {
        constructor: Task,

        consts: consts,

        getChildClass: function() {
            return Group;
        },

        process_request: function(request, item, params, callback) {
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
                data: JSON.stringify([request, this.ID, item.ID, params, date]),
                statusCode: statusCode,
                success: function(data) {
                    var mess;
                    if (data.error) {
                        console.log(data);
                    } else {
                        if (data.result.status === consts.NO_PROJECT) {
                            $('body').empty();
                            item.warning('Creating a project is not finished yet. Run the Administrator to finish.');
                            return;
                        } else if (data.result.status === consts.UNDER_MAINTAINANCE) {
                            if (!self.task._under_maintainance) {
                                self.task._under_maintainance = true;
                                if (language) {
                                    mess = language.website_maintenance;
                                } else {
                                    mess = 'Web site currently under maintenance.';
                                }
                                item.warning(mess, function() {
                                    self.task._under_maintainance = undefined;
                                });
                            }
                            return;
                        } else if (data.result.status === consts.NOT_LOGGED) {
                            if (!self.logged_in) {
                                self.login();
                            } else {
                                location.reload();
                            }
                            return;
                        } else if (self.ID > 0 && data.result.version &&
                            self.version && data.result.version !== self.version) {
                            if (!self.task._version_changed) {
                                self.task._version_changed = true;
                                self.message('<h4>' + language.version_changed + '</h4>', {
                                    margin: '50px 0px',
                                    width: 500,
                                    text_center: true
                                });
                            }
                            return;
                        }
                    }
                    if (callback) {
                        callback.call(item, data.result.data);
                    } else {
                        reply = data.result.data;
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    if (jqXHR.responseText && self.ID !== 0) {
                        document.open();
                        document.write(jqXHR.responseText);
                        document.close();
                    } else if (language) {
                        if (!self.task._server_request_error) {
                            self.task._server_request_error = true;
                            self.warning(language.server_request_error, function() {
                                self.task._server_request_error = undefined;
                            });
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
        },

        _byteLength: function(str) {
            var s = str.length;
            for (var i = str.length - 1; i >= 0; i--) {
                var code = str.charCodeAt(i);
                if (code > 0x7f && code <= 0x7ff) s++;
                else if (code > 0x7ff && code <= 0xffff) s += 2;
                if (code >= 0xDC00 && code <= 0xDFFF) i--;
            }
            return s;
        },

        do_upload: function(path, file_info, options) {
            var self = this,
                i,
                file,
                files = [],
                content,
                header = '',
                body = [],
                div_chr = ';',
                xhr = new XMLHttpRequest(),
                user_info = this.ID + ';' + this.item_name;
            header += user_info.length + ';' + user_info + div_chr;
            header += file_info.length + div_chr;
            header += this._byteLength(path) + div_chr;
            for (i = 0; i < file_info.length; i++) {
                file = file_info[i][0];
                content = file_info[i][1];
                header += this._byteLength(file.name) + div_chr;
                header += content.byteLength + div_chr;
                files.push(file.name);
            }
            body.push(header);
            body.push(path);
            for (i = 0; i < file_info.length; i++) {
                file = file_info[i][0];
                content = file_info[i][1];
                body.push(file.name);
                body.push(content);
            }
            xhr.open('POST', 'upload', true);
            if (options.callback) {
                xhr.onload = function(e) {
                    if (options.multiple) {
                        options.callback.call(self, files);
                    } else {
                        options.callback.call(self, files[0]);
                    }
                };
            }
            if (options.on_progress) {
                xhr.upload.onprogress = function(e) {
                    options.on_progress.call(self, self, e);
                };
            }
            var blob = new Blob(body, {
                type: 'application/octet-stream'
            });
            xhr.send(blob);
        },

        upload: function(path, options) {
            var self = this,
                default_options = {
                    callback: undefined,
                    on_progress: undefined,
                    extension: undefined,
                    multiple: false
                },
                button = $('<input type="file" style="position: absolute; top: -100px"/>');
            options = $.extend({}, default_options, options);
            if (options.multiple) {
                button.attr('multiple', 'multiple');
            }
            $('body').append(button);
            button.on('change', function(e) {
                var files = e.target.files,
                    i,
                    parts,
                    ext,
                    f,
                    file,
                    file_info = [],
                    reader,
                    file_list = [];

                for (i = 0, f; f = files[i]; i++) {
                    ext = '';
                    if (options.extension) {
                        parts = f.name.split('.');
                        if (parts.length) {
                            ext = parts[parts.length - 1];
                        }
                        if (ext !== options.extension) {
                            continue;
                        }
                    }
                    file_list.push(f);
                }
                for (i = 0; i < file_list.length; i++) {
                    file = file_list[i];
                    reader = new FileReader();
                    reader.onload = (function(cur_file) {
                        return function(e) {
                            file_info.push([cur_file, e.target.result]);
                            if (file_info.length === file_list.length) {
                                self.do_upload(path, file_info, options);
                            }
                        };
                    })(file);
                    reader.readAsArrayBuffer(file);
                }
                button.remove();
            });
            button.click();
        },

        load: function() {
            var self = this,
                info;
            this.send_request('connect', null, function(success) {
                if (success) {
                    this.load_task();
                }
                else {
                    self.login();
                }
            });
        },

        login: function() {
            var self = this,
                info,
                $form;
            if (this.templates) {
                $form = this.templates.find("#login-form").clone();
            } else {
                $form = $("#login-form").clone();
            }

            $form = this.makeFormModal($form, {
                title: $form.data('caption'),
                transition: false
            });

            $form.find("#login-btn").click(function(e) {
                var login = $form.find("#inputLoging").val(),
                    passWord = $form.find("#inputPassword").val(),
                    pswHash = hex_md5(passWord);
                e.preventDefault();
                if (login && passWord) {
                    self.send_request('login', [login, pswHash], function(success) {
                        if (success) {
                            if ($form) {
                                $form.modal('hide');
                            }
                            self.load_task();
                        }
                    });
                }
            });

            $form.find("#close-btn").click(function(e) {
                $form.modal('hide');
            });

            $form.on("shown", function(e) {
                $form.find("#inputLoging").focus();
                e.stopPropagation();
            });

            $form.find('input').keydown(function(e) {
                var $this = $(this),
                    code = (e.keyCode ? e.keyCode : e.which);
                if (code === 40) {
                    if ($this.attr('id') === 'inputLoging') {
                        $form.find('#inputPassword').focus();
                    } else {
                        $form.find('#login-btn').focus();
                    }
                }
            });

            $form.modal({
                width: 500
            });
        },

        logout: function() {
            this.send_request('logout');
            location.reload();
        },

        load_task: function() {
            var self = this,
                info;
            this.send_request('init_client', null, function(data) {
                var info = data[0],
                    error = data[1],
                    templates;
                if (error) {
                    self.warning(error);
                    return;
                }
                self.logged_in = true;
                settings = info.settings;
                language = info.language;
                self.settings = info.settings;
                self.language = info.language;
                self.user_info = info.user_info;
                self.user_privileges = info.privileges;
                self.consts = consts;
                self.safe_mode = self.settings.SAFE_MODE;
                self.version = self.settings.VERSION;
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
                self.templates = $("<div></div>");
                templates = $(".templates");
                self.templates = templates.clone();
                templates.remove();
                self.init(info.task);
                self.bind_items();
                if (self.ID === 0) {
                    self.js_filename = 'jam/js/admin.js';
                    self.settings.DYNAMIC_JS = false;
                }
                if (self.static_js_modules) {
                    self.bind_events();
                    if (self.on_page_loaded) {
                        self.on_page_loaded.call(self, self);
                    }
                }
                else {
                    self.init_modules();
                }
                if (self.history_item) {
                    self._set_history_item(self.item_by_ID(self.history_item))
                }
            });
        },

        _set_history_item: function(item) {
            var self = this,
                doc_name;
            this.history_item = item;
            if (this.history_item) {
                this.history_item.read_only = true;
//                item.view_options.fields = ['item_id', 'item_rec_id', 'date', 'operation', 'user'];
                if (!item.on_field_get_text) {
                    item.on_field_get_text = function(field) {
                        var oper,
                            it;
                        if (field.field_name === 'operation') {
                            if (field.value === consts.RECORD_INSERTED) {
                                return self.language.created;
                            }
                            else if (field.value === consts.RECORD_MODIFIED || field.value === consts.RECORD_DETAILS_MODIFIED) {
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
                                if (it.master) {
                                    doc_name = it.master.item_caption + ' - ' + doc_name;
                                }
                                return doc_name;
                            }
                        }
                    }
                }
            }
        },

        init_modules: function() {
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
                                    if (self.on_page_loaded && !calcback_executing) {
                                        calcback_executing = true;
                                        self.on_page_loaded.call(self, self);
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
        },

        has_privilege: function(item, priv_name) {
            var priv_dic;
            if (item.task.ID === 0) {
                return true;
            }
            if (!this.user_privileges || item.master) {
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
        },

        create_cookie: function(name, value, days) {
            var expires;

            if (days) {
                var date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                expires = "; expires=" + date.toGMTString();
            } else {
                expires = "";
            }
            document.cookie = escape(name) + "=" + escape(value) + expires + "; path=/";
        },

        read_cookie: function(name) {
            var nameEQ = escape(name) + "=";
            var ca = document.cookie.split(';');
            for (var i = 0; i < ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) === ' ') c = c.substring(1, c.length);
                if (c.indexOf(nameEQ) === 0) return unescape(c.substring(nameEQ.length, c.length));
            }
            return null;
        },

        erase_cookie: function(name) {
            this.create_cookie(name, "", -1);
        },

        show_context_menu: function($menu, e) {
            if ($menu.length) {
                e.preventDefault();
                this.$context_menu = $menu;
                this.$context_menu_parent = $menu.parent();
                $menu.detach();
                $('body').prepend($menu);
                $menu.show();
                $menu.find('ul').css({
                        top: e.pageY + "px",
                        left: e.pageX + "px"
                    })
                    .show();
            }
        }
    });


    /**********************************************************************/
    /*                           Group class                              */
    /**********************************************************************/

    Group.prototype = new AbsrtactItem();
    Group.prototype.constructor = Group;

    function Group(owner, ID, item_name, caption, visible, type, js_filename) {
        AbsrtactItem.call(this, owner, ID, item_name, caption, visible, type, js_filename);
    }

    Group.prototype.getChildClass = function() {
        if (this.item_type === "reports") {
            return Report;
        } else {
            return Item;
        }
    };

    /**********************************************************************/
    /*                         ChangeLog class                            */
    /**********************************************************************/

    function ChangeLog(item) {
        this.item = item;
        this._change_id = 0;
        this.records = [];
        this.logs = {};
        this.fields = [];
        this.expanded = true;
    }

    ChangeLog.prototype = {
        constructor: ChangeLog,

        get_change_id: function() {
            this._change_id += 1;
            return this._change_id + '';
        },

        is_empty_obj: function(obj) {
            for (var prop in obj) {
                if (obj.hasOwnProperty(prop))
                    return false;
            }
            return true;
        },

        log_changes: function() {
            if (this.item.master) {
                return this.item.master.change_log.log_changes();
            } else {
                return this.item.log_changes;
            }
        },

        find_record_log: function() {
            var result,
                record_log,
                details,
                detail,
                i,
                len,
                fields = [],
                change_id;
            if (this.item.master) {
                record_log = this.item.master.change_log.find_record_log();
                if (record_log) {
                    details = record_log.details;
                    detail = details[this.item.ID];
                    if (this.is_empty_obj(detail)) {
                        len = this.item.fields.length;
                        for (i = 0; i < len; i++) {
                            fields.push(this.item.fields[i].field_name);
                        }
                        detail = {
                            logs: {},
                            records: this.item._dataset,
                            fields: fields,
                            expanded: this.item.expanded
                        };
                        details[this.item.ID] = detail;
                    }
                    this.logs = detail.logs;
                    this.records = detail.records;
                    this.fields = detail.fields;
                    this.expanded = detail.expanded;
                }
            }
            if (this.item.record_count()) {
                change_id = this.item._get_rec_change_id();
                if (!change_id) {
                    change_id = this.get_change_id()
                    this.item._set_rec_change_id(change_id);
                }
                result = this.logs[change_id];
                if (this.is_empty_obj(result)) {
                    result = {
                        old_record: null,
                        record: this.cur_record(),
                        details: {}
                    };
                    this.logs[change_id] = result;
                }
            }
            return result;
        },

        get_detail_log: function(detail_ID) {
            var result,
                record_log,
                details;
            record_log = this.find_record_log();
            details = record_log.details;
            if (!this.is_empty_obj(details)) {
                result = details[detail_ID];
            }
            if (result === undefined && this._is_delta) {
                result = {
                    records: [],
                    fields: [],
                    expanded: false,
                    logs: {}
                };
            }
            return result;
        },

        remove_record_log: function() {
            var change_id = this.item._get_rec_change_id();
            if (change_id) {
                this.find_record_log();
                delete this.logs[change_id];
                this.item._set_rec_change_id(null);
                this.item._set_record_status(consts.RECORD_UNCHANGED);
            }
        },

        cur_record: function() {
            return this.item._dataset[this.item._get_rec_no()];
        },

        record_modified: function(record_log) {
            var modified = false,
                old_rec = record_log.old_record,
                cur_rec = record_log.record;
            for (var i = 0; i < this.item._record_lookup_index; i++) {
                if (old_rec[i] !== cur_rec[i]) {
                    modified = true;
                    break;
                }
            }
            return modified;
        },

        copy_record: function(record, expanded) {
            var result = null,
                info;
            if (record) {
                if (expanded === undefined) {
                    expanded = true;
                }
                if (expanded) {
                    result = record.slice(0, this.item._record_info_index);
                } else {
                    result = record.slice(0, this.item._record_lookup_index);
                }
                info = this.item.get_rec_info(undefined, record);
                result.push([info[0], {},
                    info[2]
                ]);
            }
            return result;
        },

        can_log_changes: function() {
            var result = this.log_changes();
            if (this.item.item_state === consts.STATE_EDIT) {}
        },

        log_change: function() {
            var record_log;
            if (this.log_changes()) {
                record_log = this.find_record_log();
                if (this.item.item_state === consts.STATE_BROWSE) {
                    if ((this.item._get_record_status() === consts.RECORD_UNCHANGED) ||
                        (this.item._get_record_status() === consts.RECORD_DETAILS_MODIFIED && record_log.old_record === null)) {
                        record_log.old_record = this.copy_record(this.cur_record(), false);
                        return;
                    }
                } else if (this.item.item_state === consts.STATE_INSERT) {
                    this.item._set_record_status(consts.RECORD_INSERTED);
                } else if (this.item.item_state === consts.STATE_EDIT) {
                    if (this.item._get_record_status() === consts.RECORD_UNCHANGED) {
                        this.item.record_status = consts.RECORD_MODIFIED;
                    } else if (this.item._get_record_status() === consts.RECORD_DETAILS_MODIFIED) {
                        if (this.record_modified(record_log)) {
                            this.item._set_record_status(consts.RECORD_MODIFIED);
                        }
                    }
                } else if (this.item.item_state === consts.STATE_DELETE) {
                    if (this.item._get_record_status() === consts.RECORD_INSERTED) {
                        this.remove_record_log();
                    } else {
                        this.item._set_record_status(consts.RECORD_DELETED);
                    }
                } else {
                    throw this.item.item_name + ': change log invalid records state';
                }
                if (this.item.master) {
                    if (this.item.master._get_record_status() === consts.RECORD_UNCHANGED) {
                        this.item.master._set_record_status(consts.RECORD_DETAILS_MODIFIED);
                    }
                }
            }
        },

        get_changes: function(result) {
            var data = {},
                record_log,
                record,
                old_record = null,
                info,
                new_record,
                new_details,
                detail_id,
                detail,
                details,
                new_detail,
                detail_item;
            result.fields = this.fields;
            result.expanded = false;
            result.data = data;
            for (var key in this.logs) {
                if (this.logs.hasOwnProperty(key)) {
                    record_log = this.logs[key];
                    record = record_log.record;
                    info = this.item.get_rec_info(undefined, record);
                    if (info[consts.REC_STATUS] !== consts.RECORD_UNCHANGED) {
                        details = record_log.details;
                        if (this.item.keep_history) {
                            old_record = record_log.old_record;
                        }
                        new_record = this.copy_record(record, false)
                        new_details = {};
                        for (var detail_id in details) {
                            if (details.hasOwnProperty(detail_id)) {
                                detail = details[detail_id];
                                new_detail = {};
                                detail_item = this.item.item_by_ID(parseInt(detail_id, 10));
                                detail_item.change_log.logs = detail.logs;
                                detail_item.change_log.get_changes(new_detail);
                                new_details[detail_id] = new_detail;
                            }
                        }
                        data[key] = {
                            record: new_record,
                            details: new_details,
                            old_record: old_record
                        };
                    }
                }
            }
        },

        set_changes: function(changes) {
            var data = changes.data,
                record_log,
                record,
                record_details,
                details,
                detail,
                detail_item;
            this.records = [];
            this.logs = {};
            this.fields = changes.fields
            this.expanded = changes.expanded;
            this._change_id = 0;
            for (var key in data) {
                if (data.hasOwnProperty(key)) {
                    record_log = data[key];
                    if (this._change_id < parseInt(key, 10)) {
                        this._change_id = parseInt(key, 10);
                    }
                    record = record_log.record;
                    this.records.push(record);
                    details = {};
                    this.logs[key] = {
                        old_record: null,
                        record: record,
                        details: details
                    };
                    record_details = record_log.details;
                    for (var detail_id in record_details) {
                        if (record_details.hasOwnProperty(detail_id)) {
                            detail = record_details[detail_id];
                            detail_item = this.item.item_by_ID(parseInt(detail_id, 10));
                            detail_item.change_log.set_changes(detail);
                            details[detail_id] = {
                                logs: detail_item.change_log.logs,
                                records: detail_item.change_log.records,
                                fields: detail_item.change_log.fields,
                                expanded: detail_item.change_log.expanded
                            };
                        }
                    }
                }
            }
        },

        copy_records: function(records) {
            var i = 0,
                len = records.length,
                result = [];
            for (i = 0; i < len; i++) {
                result.push(records[i].slice(0));
            }
            return result;
        },

        store_details: function(source, dest) {
            var detail_item,
                cur_logs,
                record_log,
                logs,
                cur_records,
                records,
                cur_record,
                record,
                fields,
                expanded,
                index,
                detail,
                detail_id,
                details;
            for (var i = 0; i < this.item.details.length; i++) {
                detail_item = this.item.details[i];
                detail_id = detail_item.ID;
                detail = source[detail_id];
                logs = {};
                records = [];
                fields = [];
                expanded = true;
                if (detail) {
                    cur_logs = detail.logs;
                    cur_records = detail.records;
                    fields = detail.fields;
                    expanded = detail.expanded;
                    records = this.copy_records(cur_records);
                    for (var key in cur_logs) {
                        if (cur_logs.hasOwnProperty(key)) {
                            record_log = cur_logs[key];
                            cur_record = record_log.record;
                            record = detail_item.change_log.copy_record(cur_record);
                            index = cur_records.indexOf(cur_record);
                            if (index !== -1) {
                                records[index] = record;
                            }
                            details = {};
                            detail_item.change_log.store_details(record_log.details, details);
                            logs[key] = {
                                old_record: record_log.old_record,
                                record: record,
                                details: details
                            };
                        }
                    }
                } else {
                    if (detail_item._dataset) {
                        records = this.copy_records(detail_item._dataset);
                    }
                }
                dest[detail_id] = {
                    logs: logs,
                    records: records,
                    fields: fields,
                    expanded: expanded
                };
            }
        },

        store_record_log: function() {
            var record_log,
                details,
                detail,
                result;
            if (this.log_changes()) {
                record_log = this.find_record_log();
                details = {};
                this.store_details(record_log.details, details);
                result = {};
                result.old_record = record_log.old_record;
                result.record = this.copy_record(record_log.record);
                result.details = details;
            } else {
                result = {};
                result.record = this.copy_record(this.cur_record());
                details = {};
                for (var i = 0; i < this.item.details.length; i++) {
                    detail = this.item.details[i];
                    if (!detail.disabled && detail._dataset) {
                        details[detail.ID] = detail._dataset.slice(0);
                    }
                }
                result.details = details;
            }
            return result;
        },

        restore_record_log: function(log) {
            var record_log,
                record,
                detail,
                detail_log,
                cur_record,
                info_index;
            if (this.log_changes()) {
                record_log = this.find_record_log();
                record = log.record;
                cur_record = this.cur_record();
                info_index = this.item._record_info_index;
                for (var i = 0; i < info_index; i++) {
                    cur_record[i] = record[i];
                }
                record_log.old_record = log.old_record;
                record_log.record = cur_record;
                record_log.details = log.details;
                for (var i = 0; i < this.item.details.length; i++) {
                    detail = this.item.details[i];
                    detail_log = log.details[detail.ID];
                    if (!this.is_empty_obj(detail_log)) {
                        detail._dataset = detail_log.records;
                    }
                }
                if (this.item._get_record_status() === consts.RECORD_UNCHANGED) {
                    this.remove_record_log();
                }
            } else {
                record = log.record;
                cur_record = this.cur_record();
                info_index = this.item._record_info_index;
                for (var i = 0; i < info_index; i++) {
                    cur_record[i] = record[i];
                }
                for (var i = 0; i < this.item.details.length; i++) {
                    detail = this.item.details[i];
                    detail._dataset = log.details[detail.ID];
                }
            }
        },

        update: function(updates, master_rec_id) {
            var change,
                changes,
                log_id,
                rec_id,
                detail,
                details,
                record_log,
                record,
                record_details,
                len,
                ID,
                detail_item,
                item_detail,
                info,
                primary_key_field,
                master_rec_id_field;
            if (updates) {
                changes = updates.changes;
                for (var key in changes) {
                    if (changes.hasOwnProperty(key)) {
                        change = changes[key];
                        log_id = change.log_id;
                        rec_id = change.rec_id;
                        details = change.details;
                        record_log = this.logs[log_id];
                        if (record_log) {
                            record = record_log.record;
                            record_details = record_log.details;
                            len = details.length;
                            for (var i = 0; i < len; i++) {
                                detail = details[i];
                                ID = detail.ID;
                                detail_item = this.item.detail_by_ID(parseInt(ID, 10));
                                item_detail = record_details[ID];
                                if (!this.is_empty_obj(item_detail)) {
                                    detail_item.change_log.logs = item_detail.logs;
                                    detail_item.change_log.update(detail, rec_id);
                                }
                            }
                            if (rec_id) {
                                if (!record[this.item._primary_key_field.bind_index]) {
                                    record[this.item._primary_key_field.bind_index] = rec_id;
                                }
                            }
                            if (master_rec_id) {
                                if (!record[this.item._master_rec_id_field.bind_index]) {
                                    record[this.item._master_rec_id_field.bind_index] = master_rec_id;
                                }
                            }
                            info = this.item.get_rec_info(undefined, record);
                            info[consts.REC_STATUS] = consts.RECORD_UNCHANGED;
                            info[consts.REC_CHANGE_ID] = consts.RECORD_UNCHANGED;
                            delete this.logs[log_id];
                        }
                    }
                }
            }
        },

        prepare: function() {
            var log = this,
                i,
                len = this.item.fields.length;

            if (this.item.master) {
                log = this.item.master.change_log.get_detail_log(this.item.ID);
            }
            if (log) {
                log.records = [];
                log.logs = {};
                log.fields = [];
                for (i = 0; i < len; i++) {
                    if (!this.item.fields[i].master_field) {
                        log.fields.push(this.item.fields[i].field_name);
                    }
                }
                log.expanded = this.item.expanded;
            }
        }
    };


    /**********************************************************************/
    /*                            Item class                              */
    /**********************************************************************/

    Item.prototype = new AbsrtactItem();

    function Item(owner, ID, item_name, caption, visible, type, js_filename) {
        var self;
        AbsrtactItem.call(this, owner, ID, item_name, caption, visible, type, js_filename);
        if (this.task && type !== 0 && !(item_name in this.task)) {
            this.task[item_name] = this;
        }
        this.field_defs = [];
        this._fields = [];
        this.fields = [];
        this.filter_defs = [];
        this.filters = [];
        this.details = [];
        this.controls = [];
        this.change_log = new ChangeLog(this);
        this.paginate = false;
        this.disabled = false;
        this.expanded = true;
        this._log_changes = true;
        this._dataset = null;
        this._eof = false;
        this._bof = false;
        this._cur_row = null;
        this._old_row = 0;
        this._old_status = null;
        this._buffer = null;
        this._modified = null;
        this._state = 0;
        this._read_only = false;
        this._parent_read_only = true;
        this._active = false;
        this._disabled_count = 0;
        this._open_params = {};
        this._where_list = [];
        this._order_by_list = [];
        this._select_field_list = [];
        this._record_lookup_index = -1
        this._record_info_index = -1
        this._is_delta = false;
        this._limit = 20;
        this._offset = 0;
        this._selections = undefined;
        this.filter_selected = false;
        this.selection_limit = 1500;
        this.is_loaded = false;
        this.view_options = $.extend({}, this.modal_options);
        this.view_options.width = 960;
        this.edit_options = $.extend({}, this.modal_options);
        this.filter_options = $.extend({}, this.modal_options);
        Object.defineProperty(this, "rec_no", {
            get: function() {
                return this._get_rec_no();
            },
            set: function(new_value) {
                this._set_rec_no(new_value);
            }
        });
        Object.defineProperty(this, "rec_count", {
            get: function() {
                return this.record_count();
            },
        });
        Object.defineProperty(this, "active", {
            get: function() {
                return this._get_active();
            }
        });
        Object.defineProperty(this, "read_only", {
            get: function() {
                return this._get_read_only();
            },
            set: function(new_value) {
                this._set_read_only(new_value);
            }
        });
        Object.defineProperty(this, "filtered", {
            get: function() {
                return this._get_filtered();
            },
            set: function(new_value) {
                this._set_filtered(new_value);
            }
        });
        Object.defineProperty(this, "item_state", {
            get: function() {
                return this._get_item_state();
            },
            set: function(new_value) {
                this._set_item_state(new_value);
            }
        });
        Object.defineProperty(this, "record_status", {
            get: function() {
                return this._get_record_status();
            },
            set: function(new_value) {
                this._set_record_status(new_value);
            }
        });
        Object.defineProperty(this, "default_field", {
            get: function() {
                return this.get_default_field();
            }
        });
        Object.defineProperty(this, "log_changes", {
            get: function() {
                return this._get_log_changes();
            },
            set: function(new_value) {
                this._set_log_changes(new_value);
            }
        });
        Object.defineProperty(this, "dataset", {
            get: function() {
                return this.get_dataset();
            },
            set: function(new_value) {
                this.set_dataset(new_value);
            }
        });
        Object.defineProperty(this, "selections", {
            get: function() {
                return this.get_selections();
            },
            set: function(new_value) {
                this.set_selections(new_value);
            }
        });
    }

    // Item tree methods

    $.extend(Item.prototype, {

        constructor: Item,

        getChildClass: function() {
            return Detail;
        },

        initAttr: function(info) {
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
        },

        bind_item: function() {
            var i = 0,
                len,
                reports;

            this.prepare_fields();
            this.init_options();

            this.prepare_filters();

            len = this.reports.length;
            reports = this.reports;
            this.reports = [];
            for (i = 0; i < len; i++) {
                this.reports.push(this.task.item_by_ID(reports[i]));
            }
        },

        can_create: function() {
            return this.task.has_privilege(this, 'can_create');
        },

        can_edit: function() {
            return this.task.has_privilege(this, 'can_edit');
        },

        can_delete: function() {
            return this.task.has_privilege(this, 'can_delete');
        },

        prepare_fields: function() {
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
        },

        prepare_filters: function() {
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
        },

        init_options: function() {
            var i,
                view_fields = [],
                edit_fields = [],
                len = this._fields.length;
            for (i = 0; i < len; i++) {
                if (this._fields[i].view_visible && this._fields[i].view_index !== -1) {
                    view_fields.push(this._fields[i]);
                }
                if (this._fields[i].edit_visible && this._fields[i].edit_index !== -1) {
                    edit_fields.push(this._fields[i]);
                }
            }
            view_fields.sort(function(field1, field2) {
                if (field1.view_index > field2.view_index === 0) {
                    return 0;
                }
                if (field1.view_index > field2.view_index) {
                    return 1;
                } else {
                    return -1;
                }
            });
            edit_fields.sort(function(field1, field2) {
                if (field1.edit_index > field2.edit_index === 0) {
                    return 0;
                }
                if (field1.edit_index > field2.edit_index) {
                    return 1;
                } else {
                    return -1;
                }
            });

            this.view_options.fields = [];
            for (i = 0; i < view_fields.length; i++) {
                this.view_options.fields.push(view_fields[i].field_name);
            }
            this.edit_options.fields = [];
            for (i = 0; i < edit_fields.length; i++) {
                this.edit_options.fields.push(edit_fields[i].field_name);
            }
            this.edit_options.title = this.item_caption;
            this.view_options.title = this.item_caption;
            this._edit_options = $.extend({}, this.edit_options);
            this._view_options = $.extend({}, this.view_options);
        },

        each: function(callback) {
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
        },

        each_field: function(callback) {
            var i = 0,
                len = this.fields.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.fields[i], this.fields[i], i);
                if (value === false) {
                    break;
                }
            }
        },

        each_filter: function(callback) {
            var i = 0,
                len = this.filters.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.filters[i], this.filters[i], i);
                if (value === false) {
                    break;
                }
            }
        },

        each_detail: function(callback) {
            var i = 0,
                len = this.details.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.details[i], this.details[i], i);
                if (value === false) {
                    break;
                }
            }
        },

        _field_by_name: function(name) {
            return this.field_by_name(name, this._fields);
        },

        field_by_name: function(name, fields) {
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
        },

        _field_by_ID: function(ID) {
            return this.field_by_ID(ID, this._fields);
        },

        field_by_ID: function(ID, fields) {
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
        },

        filter_by_name: function(name) {
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
        },

        detail_by_name: function(name) {
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
        },

        get_dataset: function() {
            var i,
                len,
                result = [];
            if (this.active) {
                len = this._dataset.length;
                for (i = 0; i < len; i++)
                    result.push(this._dataset[i].slice(0, this._record_info_index))
                return result
            }
        },

        set_dataset: function(value) {
            this._dataset = value;
        },

        get_selections: function() {
            return this._selections;
        },

        set_selections: function(value) {
            this._selections = value;
            this.update_controls();
        },

        copy: function(options) {
            if (this.master) {
                throw 'A detail item can not be copied.';
            }
            return this._copy(options);
        },

        _copy: function(options) {
            var copyTable,
                i,
                len,
                copy,
                field,
                result,
                defaultOptions = {
                    filters: true,
                    details: true,
                    handlers: true
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
            result._primary_key = this._primary_key
            result._deleted_flag = this._deleted_flag
            result._master_id = this._master_id
            result._master_rec_id = this._master_rec_id
            result._default_order = this._default_order;
            result._edit_options = this._edit_options;
            result._view_options = this._view_options;
            result.edit_options = $.extend({}, this._edit_options);
            result.view_options = $.extend({}, this._view_options);
            result.keep_history = this.keep_history;

            len = result.field_defs.length;
            for (i = 0; i < len; i++) {
                new Field(result, result.field_defs[i]);
            }
            result.prepare_fields();
            if (options.filters) {
                len = result.filter_defs.length;
                for (i = 0; i < len; i++) {
                    new Filter(result, result.filter_defs[i]);
                }
                result.prepare_filters();
            }
            result._events = this._events;
            if (options.handlers) {
                len = this._events.length;
                for (i = 0; i < len; i++) {
                    result[this._events[i][0]] = this._events[i][1];
                }
            }
            if (options.handlers) {
                for (var name in this) {
                    if (this.hasOwnProperty(name)) {
                        if ((name.substring(0, 3) === "on_") && (typeof this[name] === "function")) {
                            result[name] = this[name];
                        }
                    }
                }
            }
            if (options.details) {
                this.each_detail(function(detail, i) {
                    copyTable = detail._copy(options);
                    copyTable.owner = result;
                    copyTable.expanded = detail.expanded;
                    copyTable.master = result;
                    copyTable.item_type = detail.item_type;
                    result.details.push(copyTable);
                    result.items.push(copyTable);
                    if (!(copyTable.item_name in result)) {
                        result[copyTable.item_name] = copyTable;
                    }
                    if (!(copyTable.item_name in result.details)) {
                        result.details[copyTable.item_name] = copyTable;
                    }
                });
            }
            return result;
        },

        clone: function(keep_filtered) {
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

            result.field_defs = this.field_defs;
            result.filter_defs = this.filter_defs;
            result._primary_key = this._primary_key
            result._deleted_flag = this._deleted_flag
            result._master_id = this._master_id
            result._master_rec_id = this._master_rec_id

            len = result.field_defs.length;
            for (i = 0; i < len; i++) {
                field = new Field(result, result.field_defs[i]);
            }
            result.prepare_fields();

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

            result.update_system_fields();

            result._bind_fields();
            result._dataset = this._dataset;
            if (keep_filtered) {
                result.on_filter_record = this.on_filter_record;
                result.filtered = this.filtered;
            }
            result._active = true;
            result._set_item_state(consts.STATE_BROWSE);
            result.first();
            return result;
        },

        store_handlers: function() {
            var result = {};
            for (var name in this) {
                if (this.hasOwnProperty(name)) {
                    if ((name.substring(0, 3) === "on_") && (typeof this[name] === "function")) {
                        result[name] = this[name];
                    }
                }
            }
            return result;
        },

        clear_handlers: function() {
            for (var name in this) {
                if (this.hasOwnProperty(name)) {
                    if ((name.substring(0, 3) === "on_") && (typeof this[name] === "function")) {
                        this[name] = undefined;
                    }
                }
            }
        },

        load_handlers: function(handlers) {
            for (var name in handlers) {
                if (handlers.hasOwnProperty(name)) {
                    this[name] = handlers[name];
                }
            }
        },

        _get_log_changes: function() {
            return this._log_changes;
        },

        _set_log_changes: function(value) {
            this._log_changes = value;
        },

        is_modified: function() {
            return this._modified;
        },

        _set_modified: function(value) {
            this._modified = value;
            if (this.master && value) {
                this.master._set_modified(value);
            }
        }
    });

    // Item server exchange methods

    $.extend(Item.prototype, {

        _bind_fields: function(expanded) {
            var j = 0;
            if (expanded === undefined) {
                expanded = true;
            }
            this.each_field(function(field, i) {
                field.bind_index = null;
                field.lookup_index = null;
            });
            this.each_field(function(field, i) {
                if (!field.master_field) {
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
                    if (field.lookup_item) {
                        field.lookup_index = j;
                        j += 1;
                    }
                });
            }
            this._record_info_index = j;
        },

        set_fields: function(field_list) {
            this._select_field_list = field_list;
        },

        set_order_by: function(fields) {
            this._order_by_list = this.get_order_by_list(fields);
        },

        get_order_by_list: function(fields) {
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
                    throw this.item_name + ': set_order_by method arument error - ' + field + ' ' + e;
                }
                result.push([fld.ID, desc]);
            }
            return result;
        },

        set_where: function(whereDef) {
            this._where_list = this.get_where_list(whereDef);
        },

        get_where_list: function(whereDef) {
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
                    filter_type = filterValue.indexOf(filter_str);
                    if (filter_type !== -1) {
                        filter_type += 1
                    } else {
                        throw this.item_name + ': set_where method arument error - ' + field_arg;
                    }
                    field = this._field_by_name(field_name);
                    if (!field) {
                        throw this.item_name + ': set_where method arument error - ' + field_arg;
                    }
                    if (value !== null) {
                        if (field.data_type === consts.DATETIME && filter_type !== consts.FILTER_ISNULL) {
                            value = field.format_date_to_string(value, '%Y-%m-%d %H:%M:%S')
                        }
                        result.push([field_name, filter_type, value])
                    }
                }
            }
            return result;
        },

        update_system_fields: function() {
            var i,
                len,
                field,
                sys_field,
                sys_field_name,
                sys_fields = ['_primary_key', '_deleted_flag', '_master_id', '_master_rec_id'];
            len = sys_fields.length;
            for (i = 0; i < len; i++) {
                sys_field_name = sys_fields[i];
                sys_field = this[sys_field_name];
                if (sys_field) {
                    field = this.field_by_name(sys_field)
                    if (field) {
                        this[sys_field_name + '_field'] = field;
                    }
                }
            }
        },

        _update_fields: function(fields) {
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
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i]
                if (this[field.field_name] === undefined) {
                    this[field.field_name] = field;
                }
            }
            this.update_system_fields();
        },

        _do_before_open: function(expanded, fields, where, order_by, open_empty, params,
            offset, limit, funcs, group_by) {
            var filters = [];

            if (this.on_before_open) {
                this.on_before_open.call(this, this, params);
            }

            params.__expanded = expanded;
            params.__fields = [];
            if (fields) {
                params.__fields = fields;
            }

            this._update_fields(fields);

            params.__open_empty = open_empty;
            params.__order = []
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
                        if (filter.get_value() !== null) {
                            filters.push([filter.field.field_name, filter.filter_type, filter.get_value()]);
                        }
                    });
                }
                if (params.__search !== undefined) {
                    var field_name = params.__search[0],
                        text = params.__search[1];
                    filters.push([field_name, consts.FILTER_CONTAINS_ALL, text]);
                }
                if (this.filter_selected) {
                    filters.push([this._primary_key, consts.FILTER_IN, this.selections]);
                }
                params.__filters = filters;
                if (order_by) {
                    params.__order = this.get_order_by_list(order_by);
                } else if (this._order_by_list.length) {
                    params.__order = this._order_by_list.slice(0);
                } else if (this._default_order) {
                    params.__order = this._default_order.slice();
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
        },

        _do_after_open: function() {
            if (this.on_after_open) {
                this.on_after_open.call(this, this);
            }
        },

        open_details: function(callback) {
            var self = this,
                details = 0;

            function afterOpen() {
                details -= 1;
                if (details === 0) {
                    callback.call(self);
                }
            }

            if (callback) {
                this.each_detail(function(detail, i) {
                    if (!detail.disabled) {
                        details += 1;
                    }
                });
                this.each_detail(function(detail, i) {
                    if (!detail.disabled) {
                        detail.open(afterOpen);
                    }
                });
            } else {
                this.each_detail(function(detail, i) {
                    if (!detail.disabled) {
                        detail.open();
                    }
                });
            }
        },

        find_change_log: function() {
            if (this.master) {
                if (this.master._get_record_status() !== consts.RECORD_UNCHANGED) {
                    return this.master.change_log.get_detail_log(this.ID)
                }
            }
        },

        _check_open_options: function(options) {
            if (options) {
                if (options.fields && !$.isArray(options.fields)) {
                    throw this.item_name + ': open method options error: the fields option must be an array.';
                }
                if (options.order_by && !$.isArray(options.order_by)) {
                    throw this.item_name + ': open method options error: the order_by option must be an array.';
                }
                if (options.group_by && !$.isArray(options.group_by)) {
                    throw this.item_name + ': open method options error: the group_by option must be an array.';
                }
            }
        },

        open: function() {
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
                rec_info,
                records,
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
            if (expanded === undefined) {
                expanded = this.expanded;
            } else {
                this.expanded = expanded;
            }
            if (!async) {
                async = callback ? true : false;
            }
            if (this.master) {
                if (!this.disabled && this.master.record_count() > 0) {
                    params.__master_id = this.master.ID;
                    params.__master_rec_id = this.master.field_by_name(this.master._primary_key).value;
                    if (this.master.is_new()) {
                        records = [];
                    } else {
                        log = this.find_change_log();
                        if (log) {
                            records = log['records']
                            fields = log['fields']
                            expanded = log['expanded']
                        }
                    }
                    if (records !== undefined) {
                        this._do_before_open(expanded, fields,
                            where, order_by, open_empty, params, offset,
                            limit, funcs, group_by)
                        this._bind_fields(expanded);
                        if (this.master.is_new()) {
                            this.change_log.prepare();
                        }
                        this._dataset = records;
                        this._active = true;
                        this._set_item_state(consts.STATE_BROWSE);
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
                    return;
                }
            }
            if (this.paginate && offset !== undefined) {
                params = this._open_params;
                params.__offset = offset;
                if (this.on_before_open) {
                    this.on_before_open.call(this, this, params);
                }
            } else {
                offset = 0
                this._do_before_open(expanded, fields,
                    where, order_by, open_empty, params, offset, limit, funcs, group_by);
                this._bind_fields(expanded);
            }
            if (this.paginate) {
                params.__limit = this._limit;
            }
            this.change_log.prepare();
            this._dataset = [];
            this.do_open(offset, async, params, open_empty, function() {
                self._active = true;
                self._set_item_state(consts.STATE_BROWSE);
                self._cur_row = null;
                self.first();
                self._do_after_open();
                if ((!self.paginate || self.paginate && offset === 0) && self.on_filters_applied) {
                    self.on_filters_applied.call(self, self);
                }
                self.update_controls(consts.UPDATE_OPEN);
                if (callback) {
                    callback.call(self, self);
                }
            });
        },

        do_open: function(offset, async, params, open_empty, callback) {
            var self = this,
                data;
            if (async && !open_empty) {
                this.send_request('open', params, function(data) {
                    self._do_after_load(data, offset, callback);
                });
            } else {
                if (open_empty) {
                    data = [
                        [], ''
                    ];
                } else {
                    data = this.send_request('open', params);
                }
                this._do_after_load(data, offset, callback);
            }
        },

        _do_after_load: function(data, offset, callback) {
            var rows,
                error_mes,
                i,
                len;
            if (data) {
                error_mes = data[1];
                if (error_mes) {
                    this.warning(error_mes);
                } else {
                    if (data[0]) {
                        rows = data[0];

                        len = rows.length;
                        this._dataset = rows;
                        if (this._limit && this.paginate && rows) {
                            this._offset = offset;
                            this.is_loaded = false;
                        }
                        if (len < this._limit) {
                            this.is_loaded = true;
                        }
                        callback.call(this, this);
                    }
                }
            } else {
                this._dataset = [];
                console.log(this.item_name + " error while opening table");
            }

        },

        _do_close: function() {
            this._active = false;
            this._dataset = null;
            this._cur_row = null;
        },

        close: function() {
            var len = this.details.length;
            this._do_close();
            for (var i = 0; i < len; i++) {
                this.details[i].close();
            }
            this.update_controls(consts.UPDATE_CLOSE);
        },

        sort: function(field_list) {
            var list = this.get_order_by_list(field_list)
            this._sort(list);
        },

        _sort: function(sort_fields) {
            var i,
                field_names = [],
                desc = [];
            for (i = 0; i < sort_fields.length; i++) {
                field_names.push(this.field_by_ID(sort_fields[i][0]).field_name);
                desc.push(sort_fields[i][1]);
            }
            this._sort_dataset(field_names, desc);
        },

        _sort_dataset: function(field_names, desc) {
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
                        value = new Date(0);
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
                    data_type = field.get_lookup_data_type();
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
            this.update_controls();
        },

        search: function(field_name, text, callback) {
            var searchText = text.trim(),
                params = {};

            if (searchText.length) {
                params.__search = [field_name, searchText];
                this.open({params: params}, callback);
            } else {
                this.open();
            }
        },

        total_records: function(callback) {
            var self = this;
            if (this._open_params.__open_empty && callback) {
                return 0;
            } else {
                this.send_request('get_record_count', this._open_params, function(data) {
                    if (data && callback) {
                        callback.call(self, data[0]);
                    }
                });
            }
        },

        new_record: function() {
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
        },

        _do_before_append: function() {
            if (this.on_before_append) {
                this.on_before_append.call(this, this);
            }
        },

        _do_after_append: function() {
            var i = 0,
                len = this.fields.length,
                field;
            for (; i < len; i++) {
                field = this.fields[i];
                if (field.default_value) {
                    try {
                        field.text = field.default_value;
                    }
                    catch (e) {
                    }
                }
            }
            this._modified = false;
            if (this.on_after_append) {
                this.on_after_append.call(this, this);
            }
        },

        append: function() {
            if (!this._active) {
                throw language.append_not_active.replace('%s', this.item_name);
            }
            if (this.master && !this.master.is_changing()) {
                throw language.append_master_not_changing.replace('%s', this.item_name);
            }
            if (this._get_item_state() !== consts.STATE_BROWSE) {
                throw language.append_not_browse.replace('%s', this.item_name);
            }
            this._do_before_append();
            this._do_before_scroll();
            this._old_row = this._get_rec_no();
            this._set_item_state(consts.STATE_INSERT);
            this._dataset.push(this.new_record());
            this._cur_row = this._dataset.length - 1;
            this._set_record_status(consts.RECORD_INSERTED);
            this.update_controls(consts.UPDATE_APPEND);
            this._do_after_scroll();
            this._do_after_append();
        },

        insert: function() {
            if (!this._active) {
                throw language.insert_not_active.replace('%s', this.item_name);
            }
            if (this.master && !this.master.is_changing()) {
                throw language.insert_master_not_changing.replace('%s', this.item_name);
            }
            if (this._get_item_state() !== consts.STATE_BROWSE) {
                throw language.insert_not_browse.replace('%s', this.item_name);
            }
            this._do_before_append();
            this._do_before_scroll();
            this._old_row = this._get_rec_no();
            this._set_item_state(consts.STATE_INSERT);
            this._dataset.splice(0, 0, this.new_record());
            this._cur_row = 0;
            this._modified = false;
            this._set_record_status(consts.RECORD_INSERTED);
            this.update_controls(consts.UPDATE_INSERT);
            this._do_after_scroll();
            this._do_after_append();
        },

        _do_before_edit: function() {
            if (this.on_before_edit) {
                this.on_before_edit.call(this, this);
            }
        },

        _do_after_edit: function() {
            if (this.on_after_edit) {
                this.on_after_edit.call(this, this);
            }
        },

        edit: function() {
            if (!this._active) {
                throw language.edit_not_active.replace('%s', this.item_name);
            }
            if (this.record_count() === 0) {
                throw language.edit_no_records.replace('%s', this.item_name);
            }
            if (this.master && !this.master.is_changing()) {
                throw language.edit_master_not_changing.replace('%s', this.item_name);
            }
            if (this._get_item_state() !== consts.STATE_BROWSE) {
                throw language.edit_not_browse.replace('%s', this.item_name);
            }
            this._do_before_edit();
            this.change_log.log_change();
            this._buffer = this.change_log.store_record_log();
            this._set_item_state(consts.STATE_EDIT);
            this._old_row = this._get_rec_no();
            this._old_status = this._get_record_status();
            this._modified = false;
            this._do_after_edit();
        },

        _do_before_cancel: function() {
            if (this.on_before_cancel) {
                this.on_before_cancel.call(this, this);
            }
        },

        _do_after_cancel: function() {
            if (this.on_after_cancel) {
                this.on_after_cancel.call(this, this);
            }
        },

        cancel: function() {
            var i,
                len,
                rec,
                prev_state;
            rec = this._get_rec_no();

            this._do_before_cancel();
            if (this._get_item_state() === consts.STATE_EDIT) {
                this.change_log.restore_record_log(this._buffer)
                this.update_controls(consts.UPDATE_CANCEL)
                for (var i = 0; i < this.details.length; i++) {
                    this.details[i].update_controls(consts.UPDATE_OPEN);
                }
            } else if (this._get_item_state() === consts.STATE_INSERT) {
                this.change_log.remove_record_log();
                this.update_controls(consts.UPDATE_DELETE);
                this._dataset.splice(rec, 1);
            } else {
                throw language.cancel_invalid_state.replace('%s', this.item_name);
            }

            prev_state = this._get_item_state();
            this._set_item_state(consts.STATE_BROWSE);
            if (prev_state === consts.STATE_INSERT) {
                this._do_before_scroll();
            }
            this._cur_row = this._old_row;
            if (prev_state === consts.STATE_EDIT) {
                this._set_record_status(this._old_status);
            }
            this._modified = false;
            if (prev_state === consts.STATE_INSERT) {
                this._do_after_scroll();
            }
            this._do_after_cancel();
            //~ if (this.details) {
                //~ this.each_detail(function(d) {
                    //~ console.log(d.record_count())
                //~ })
            //~ }
        },

        is_browsing: function() {
            return this._get_item_state() === consts.STATE_BROWSE;
        },

        is_changing: function() {
            return (this._get_item_state() === consts.STATE_INSERT) || (this._get_item_state() === consts.STATE_EDIT);
        },

        is_new: function() {
            return this._get_item_state() === consts.STATE_INSERT;
        },

        is_edited: function() {
            return this._get_item_state() === consts.STATE_EDIT;
        },

        is_deleting: function() {
            return this._get_item_state() === consts.STATE_DELETE;
        },


        _do_before_delete: function(callback) {
            if (this.on_before_delete) {
                this.on_before_delete.call(this, this);
            }
        },

        _do_after_delete: function() {
            if (this.on_after_delete) {
                this.on_after_delete.call(this, this);
            }
        },

        "delete": function() {
            var rec = this._get_rec_no();
            if (!this._active) {
                throw language.delete_not_active.replace('%s', this.item_name);
            }
            if (this.record_count() === 0) {
                throw language.delete_no_records.replace('%s', this.item_name);
            }
            if (this.master && !this.master.is_changing()) {
                throw language.delete_master_not_changing.replace('%s', this.item_name);
            }
            this._set_item_state(consts.STATE_DELETE);
            try {
                this._do_before_delete();
                this._do_before_scroll();
                this.update_controls(consts.UPDATE_DELETE);
                this.change_log.log_change();
                if (this.master) {
                    this.master._set_modified(true);
                }
                this._dataset.splice(rec, 1);
                this._set_rec_no(rec);
                this._do_after_scroll();
                this._set_item_state(consts.STATE_BROWSE);
                this._do_after_delete();
            } finally {
                this._set_item_state(consts.STATE_BROWSE);
            }
        },

        detail_by_ID: function(ID) {
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
        },

        post: function(callback) {
            var data,
                i,
                len,
                old_state = this._get_item_state();

            if (!this.is_changing()) {
                throw this.item_name + ' post method: dataset is not in edit or insert mode';
            }
            if (this.on_before_post) {
                this.on_before_post.call(this, this);
            }
            if (this.master && this._master_id) {
                this.field_by_name(this._master_id).set_data(this.master.ID);
            }
            this.check_record_valid();
            len = this.details.length;
            for (i = 0; i < len; i++) {
                if (this.details[i].is_changing()) {
                    this.details[i].post();
                }
            }
            if (this.is_modified() || this.is_new()) {
                this.change_log.log_change();
            } else if (this._get_record_status() === consts.RECORD_UNCHANGED) {
                this.change_log.remove_record_log();
            }
            this._modified = false;
            this._set_item_state(consts.STATE_BROWSE);
            if (this.on_after_post) {
                this.on_after_post.call(this, this);
            }
            if (!this._valid_record()) {
                this.update_controls(consts.UPDATE_DELETE);
                this._search_record(this._get_rec_no(), 0);
            }
        },

        apply: function() {
            var args = this._check_args(arguments),
                callback = args['function'],
                params = args['object'],
                self = this,
                changes = {},
                result,
                data,
                result = true;
            if (this.master) {
                if (callback) {
                    callback.call(this);
                }
                return;
            }
            if (this.is_changing()) {
                this.post();
            }
            this.change_log.get_changes(changes);
            if (!this.change_log.is_empty_obj(changes.data)) {
                if (this.on_before_apply) {
                    result = this.on_before_apply.call(this, this);
                    if (result) {
                        params = $.extend({}, params, result);
                    }
                }
                if (callback) {
                    this.send_request('apply_changes', [changes, params], function(data) {
                        self._process_apply(data, callback);
                    });
                } else {
                    data = this.send_request('apply_changes', [changes, params]);
                    result = this._process_apply(data);
                }
            }
            else if (callback) {
                callback.call(this);
            }
        },

        _process_apply: function(data, callback) {
            var res,
                err;
            if (data) {
                res = data[0]
                err = data[1]
                if (err) {
                    if (callback) {
                        callback.call(this, err);
                    }
                    throw err;
                } else {
                    this.change_log.update(res)
                    if (this.on_after_apply) {
                        this.on_after_apply.call(this, this);
                    }
                    if (callback) {
                        callback.call(this);
                    }
                }
            }
        },

        delta: function(changes) {
            var i,
                len,
                field,
                result;
            if (changes === undefined) {
                changes = {}
                this.change_log.get_changes(changes);
            }
            result = this.copy({
                filters: false,
                details: true,
                handlers: false
            });
            result.on_after_scroll = function(result) {
                result.open_details();
            }
            result.expanded = false;
            result._is_delta = true;
            len = result.details.length;
            for (i = 0; i < len; i++) {
                result.details[i].expanded = false;
                result.details[i]._is_delta = true;
            }
            result.change_log.set_changes(changes);
            result._dataset = result.change_log.records;
            result._update_fields(result.change_log.fields);
            result._bind_fields(result.change_log.expanded)
            result._set_item_state(consts.STATE_BROWSE);
            result._cur_row = null;
            result._active = true;
            result.first();
            return result;
        },

        field_by_id: function(id_value, fields, callback) {
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
        },

        locate: function(fields, values) {
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
    });

    // Item data navigation methods

    $.extend(Item.prototype, {

        _get_active: function() {
            return this._active;
        },

        _set_read_only: function(value) {
            var i,
                len;
            this._read_only = value;
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                this.fields[i].update_controls();
            }
            this.each_detail(function(detail, i) {
                detail._set_read_only(value);
            });

        },

        _get_read_only: function() {
            if (this.master && this._parent_read_only) {
                return this.master._get_read_only();
            } else {
                return this._read_only;
            }
        },

        _get_filtered: function() {
            return this._filtered;
        },

        _set_filtered: function(value) {
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
        },

        clear_filters: function() {
            this.each_filter(function(filter) {
                filter.value = null;
            })
        },

        assign_filters: function(item) {
            var self = this;
            item.each_filter(function(f) {
                if (f.value === null) {
                    self.filter_by_name(f.filter_name).field.value = null;
                } else {
                    self.filter_by_name(f.filter_name).field.value = f.field.value;
                }
            });
        },

        _set_item_state: function(value) {
            if (this._state !== value) {
                this._state = value;
                if (this.on_state_changed) {
                    this.on_state_changed.call(this, this);
                }
                this.update_controls(consts.UPDATE_STATE);
            }
        },

        _get_item_state: function() {
            return this._state;
        },

        _do_after_scroll: function() {
            var len = this.details.length;
            for (var i = 0; i < len; i++) {
                this.details[i]._do_close();
            }
            this.update_controls(consts.UPDATE_SCROLLED);
            if (this.on_after_scroll) {
                this.on_after_scroll.call(this, this);
            }
        },

        _do_before_scroll: function() {
            if (this._cur_row !== null) {
                if (this.is_changing()) {
                    this.post();
                }
                if (this.on_before_scroll) {
                    this.on_before_scroll.call(this, this);
                }
            }
        },

        skip: function(value) {
            var eof,
                bof,
                old_row,
                new_row;
            if (this.record_count() === 0) {
                this._do_before_scroll();
                this._eof = true;
                this._bof = true;
                this._do_after_scroll();
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
                    this._do_before_scroll();
                    this._cur_row = new_row;
                    this._do_after_scroll();
                } else if (eof || bof && this.is_new() && this.record_count() === 1) {
                    this._do_before_scroll();
                    this._do_after_scroll();
                }
            }
        },

        _set_rec_no: function(value) {
            if (this._active) {
                if (this.filter_active()) {
                    this._search_record(value, 0);
                } else {
                    this.skip(value);
                }
            }
        },

        _get_rec_no: function() {
            if (this._active) {
                return this._cur_row;
            }
        },

        filter_active: function() {
            if (this.on_filter_record && this.filtered) {
                return true;
            }
        },

        first: function() {
            if (this.filter_active()) {
                this.find_first();
            } else {
                this._set_rec_no(0);
            }
        },

        last: function() {
            if (this.filter_active()) {
                this.find_last();
            } else {
                this._set_rec_no(this._dataset.length);
            }
        },

        next: function() {
            if (this.filter_active()) {
                this.find_next();
            } else {
                this._set_rec_no(this._get_rec_no() + 1);
            }
        },

        prior: function() {
            if (this.filter_active()) {
                this.find_prior();
            } else {
                this._set_rec_no(this._get_rec_no() - 1);
            }
        },

        eof: function() {
            return this._eof;
        },

        bof: function() {
            return this._bof;
        },

        _valid_record: function() {
            if (this.on_filter_record && this.filtered) {
                return this.on_filter_record.call(this, this);
            } else {
                return true;
            }
        },

        _search_record: function(start, direction) {
            var row,
                cur_row,
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
                            return
                        }
                    } else {
                        this._cur_row = this._cur_row + direction;
                        update_position();
                    }
                }
            }
        },

        find_first: function() {
            this._search_record(-1, 1);
        },

        find_last: function() {
            this._search_record(this._dataset.length, -1);
        },

        find_next: function() {
            this._search_record(this._get_rec_no(), 1);
        },

        find_prior: function() {
            this._search_record(this._get_rec_no(), -1);
        },

        record_count: function() {
            if (this._dataset) {
                return this._dataset.length;
            } else {
                return 0;
            }
        },

        find_rec_info: function(rec_no, record) {
            if (record === undefined) {
                if (rec_no === undefined) {
                    rec_no = this._get_rec_no();
                    if (this.record_count() > 0) {
                        record = this._dataset[rec_no];
                    }
                }
            }
            if (record && (this._record_info_index > 0)) {
                if (record.length < this._record_info_index + 1) {
                    record.push([null, {},
                        null
                    ]);
                }
                return record[this._record_info_index];
            }
        },

        get_rec_info: function(rec_no, record) {
            return this.find_rec_info(rec_no, record);
        },

        _get_record_status: function() {
            var info = this.get_rec_info();
            if (info) {
                return info[consts.REC_STATUS];
            }
        },

        _set_record_status: function(value) {
            var info = this.get_rec_info();
            if (info && this.log_changes) {
                info[consts.REC_STATUS] = value;
            }
        },

        rec_controls_info: function() {
            var info = this.get_rec_info();
            if (info) {
                return info[consts.REC_CONTROLS_INFO];
            }
        },

        _get_rec_change_id: function() {
            var info = this.get_rec_info();
            if (info) {
                return info[consts.REC_CHANGE_ID];
            }
        },

        _set_rec_change_id: function(value) {
            var info = this.get_rec_info();
            if (info) {
                info[consts.REC_CHANGE_ID] = value;
            }
        },

        rec_unchanged: function() {
            return this._get_record_status() === consts.RECORD_UNCHANGED;
        },

        rec_inserted: function() {
            return this._get_record_status() === consts.RECORD_INSERTED;
        },

        rec_deleted: function() {
            return this._get_record_status() === consts.RECORD_DELETED;
        },

        rec_modified: function() {
            return this._get_record_status() === consts.RECORD_MODIFIED ||
                this._get_record_status() === consts.RECORD_DETAILS_MODIFIED;
        }

    });

    // Item interface methods

    $.extend(Item.prototype, {

        insert_record: function(args) {
            if (this.can_create()) {
                if (!this.is_changing()) {
                    this.insert();
                }
                this.create_edit_form(args);
            }
        },

        append_record: function(args) {
            if (this.can_create()) {
                if (!this.is_changing()) {
                    this.append();
                }
                this.create_edit_form(args);
            }
        },

        edit_record: function(args) {
            if (this.can_edit()) {
                if (!this.is_changing()) {
                    this.edit();
                }
                this.create_edit_form(args);
            }
        },

        copy_record: function(after_copy) {

            function get_record_values(it) {
                var record = {};
                it.each_field(function(f) {
                    if (!f.system_field()) {
                        record[f.field_name] = [f.value, f.lookup_value]
                    }
                })
                return record;
            }

            function set_record_values(it, values) {
                for (var field_name in values) {
                    if (values.hasOwnProperty(field_name)) {
                        it.field_by_name(field_name).value = values[field_name][0];
                        it.field_by_name(field_name).lookup_value = values[field_name][1];
                    }
                }
            }

            var record = {},
                details = [],
                i,
                d,
                records;
            if (this.can_create()) {
                record = get_record_values(this);
                this.each_detail(function(dt) {
                    var records = [];
                    if (dt.record_count()) {
                        dt.each(function(d) {
                            records.push(get_record_values(d));
                        });
                        details[dt.ID] = records
                    }
                });
                this.append();
                set_record_values(this, record);
                for (var ID in details) {
                    if (details.hasOwnProperty(ID)) {
                        d = this.item_by_ID(parseInt(ID, 10));
                        records = details[ID];
                        d.open();
                        for (i = 0; i < records.length; i++) {
                            d.append();
                            set_record_values(d, records[i]);
                            d.post();
                        }
                    }
                }
                if (after_copy) {
                    after_copy.call(this, this);
                }
                this.create_edit_form();
            }
        },

        cancel_edit: function() {
            this.close_edit_form();
            this.cancel();
        },

        delete_record: function(callback) {
            var self = this,
                rec_no = self._get_rec_no(),
                record = self._dataset[rec_no];
            if (this.can_delete()) {
                if (this.record_count() > 0) {
                    this.question(language.delete_record, function() {
                        self["delete"]();
                        this.apply(function(e) {
                            var error;
                            if (e) {
                                error = (e + '').toUpperCase();
                                if (error && (error.indexOf('FOREIGN KEY') !== -1 || error.indexOf('INTEGRITY CONSTRAINT') !== -1) &&
                                    (error.indexOf('VIOLAT') !== -1 || error.indexOf('FAIL') !== -1)) {
                                    self.warning(language.cant_delete_used_record);
                                } else {
                                    self.warning(e);
                                }
                                self._dataset.splice(rec_no, 0, record);
                                self._cur_row = rec_no;
                                self.change_log.remove_record_log();
                                self.update_controls();
                                self._do_after_scroll();
                                if (callback) {
                                    callback.call(this, this);
                                }
                            }
                        });
                    });
                } else {
                    this.warning(language.no_record);
                }
            }
        },

        check_record_valid: function() {
            var error;
            this.each_field(function(field, j) {
                try {
                    field.check_valid();
                } catch (e) {
                    field.update_control_state(e);
                    if (!error) {
                        error = 'Field "' + field.field_name + '": ' + e;
                    }
                }
            });
            if (error) {
                throw error;
            }
        },

        check_filters_valid: function() {
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
                throw error;
            }
        },

        post_record: function() {
            this.post();
            this.close_edit_form();
        },

        apply_record: function() {
            var args = this._check_args(arguments),
                callback = args['function'],
                params = args['object'],
                self = this;
            if (this.is_changing()) {
                this._disable_form(this.edit_form);
                try {
                    this.post();
                    this.apply(params, function(error) {
                        if (error) {
                            self.warning(error);
                            this._enable_form(this.edit_form);
                            if (!self.is_changing()) {
                                self.edit();
                            }
                        }
                        else {
                            if (callback) {
                                callback.call(self, self);
                            }
                            self.close_edit_form();
                        }
                    });
                }
                catch (e) {
                    if (this.edit_form._form_disabled) {
                        this._enable_form(this.edit_form);
                    }
                }
            }
        },

        do_on_view_keyup: function(e) {
            if (this.task.on_view_form_keyup) {
                this.task.on_view_form_keyup.call(this, this, e);
            }
            if (this.owner.on_view_form_keyup) {
                this.owner.on_view_form_keyup.call(this, this, e);
            }
            if (this.on_view_form_keyup) {
                this.on_view_form_keyup.call(this, this, e);
            }
        },

        do_on_view_keydown: function(e) {
            if (this.task.on_view_form_keydown) {
                this.task.on_view_form_keydown.call(this, this, e);
            }
            if (this.owner.on_view_form_keydown) {
                this.owner.on_view_form_keydown.call(this, this, e);
            }
            if (this.on_view_form_keydown) {
                this.on_view_form_keydown.call(this, this, e);
            }
        },


        view_modal: function(container) { // depricated
            this.is_lookup_item = true;
            this.view(container);
        },

        view: function(container) {
            var self = this;
            this.load_modules([this, this.owner], function() {
                self.create_view_form(container);
            })
        },

        create_view_form: function(container) {
            var self = this;
            this._create_form('view', {
                container: container,
                beforeShow: function() {
                    if (this.task.on_view_form_created) {
                        this.task.on_view_form_created.call(this, this);
                    }
                    if (!this.master && this.owner.on_view_form_created) {
                        this.owner.on_view_form_created.call(this, this);
                    }
                    if (this.on_view_form_created) {
                        this.on_view_form_created.call(this, this);
                    }
                },
                onShown: function() {
                    if (self.task.on_view_form_shown) {
                        self.task.on_view_form_shown.call(self, self);
                    }
                    if (!this.master && self.owner.on_view_form_shown) {
                        self.owner.on_view_form_shown.call(self, self);
                    }
                    if (self.on_view_form_shown) {
                        self.on_view_form_shown.call(self, self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_view_form_close_query) {
                        canClose = self.on_view_form_close_query.call(self, self);
                    }
                    if (!this.master && canClose === undefined && self.owner.on_view_form_close_query && !self.master) {
                        canClose = self.owner.on_view_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_view_form_close_query) {
                        canClose = self.task.on_view_form_close_query.call(self, self);
                    }
                    return canClose;
                },
                onHidden: function() {
                    if (self.task.on_view_form_closed) {
                        self.task.on_view_form_closed.call(self, self);
                    }
                    if (!this.master && self.owner.on_view_form_closed) {
                        self.owner.on_view_form_closed.call(self, self);
                    }
                    if (self.on_view_form_closed) {
                        self.on_view_form_closed.call(self, self);
                    }
                },
                onKeyUp: this.do_on_view_keyup,
                onKeyDown: this.do_on_view_keydown
            })
        },

        close_view_form: function() {
            this._close_form('view_form');
        },

        do_on_edit_keyup: function(e) {
            if (this.task.on_edit_form_keyup) {
                this.task.on_edit_form_keyup.call(this, this, e);
            }
            if (this.owner.on_edit_form_keyup) {
                this.owner.on_edit_form_keyup.call(this, this, e);
            }
            if (this.on_edit_form_keyup) {
                this.on_edit_form_keyup.call(this, this, e);
            }
        },

        do_on_edit_keydown: function(e) {
            if (this.task.on_edit_form_keydown) {
                this.task.on_edit_form_keydown.call(this, this, e);
            }
            if (this.owner.on_edit_form_keydown) {
                this.owner.on_edit_form_keydown.call(this, this, e);
            }
            if (this.on_edit_form_keydown) {
                this.on_edit_form_keydown.call(this, this, e);
            }
        },

        create_edit_form: function() {
            var self = this,
                args = this._check_args(arguments),
                callback = args['function'],
                container = args['object'];
            this.edit_options.show_history = true;
            this._create_form('edit', {
                container: container,
                beforeShow: function() {
                    if (self.task.on_edit_form_created) {
                        self.task.on_edit_form_created.call(self, self);
                    }
                    if (!self.master && self.owner.on_edit_form_created && !self.master) {
                        self.owner.on_edit_form_created.call(self, self);
                    }
                    if (self.on_edit_form_created) {
                        self.on_edit_form_created.call(self, self);
                    }
                },
                onShown: function() {
                    if (self.task.on_edit_form_shown) {
                        self.task.on_edit_form_shown.call(self, self);
                    }
                    if (!self.master && self.owner.on_edit_form_shown && !self.master) {
                        self.owner.on_edit_form_shown.call(self, self);
                    }
                    if (self.on_edit_form_shown) {
                        self.on_edit_form_shown.call(self, self);
                    }
                    if (callback) {
                        callback.call(self, self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_edit_form_close_query) {
                        canClose = self.on_edit_form_close_query.call(self, self);
                    }
                    if (!self.master && canClose === undefined && self.owner.on_edit_form_close_query && !self.master) {
                        canClose = self.owner.on_edit_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_edit_form_close_query) {
                        canClose = self.task.on_edit_form_close_query.call(self, self);
                    }
                    return canClose;
                },
                onHidden: function() {
                    if (self.task.on_edit_form_closed) {
                        self.task.on_edit_form_closed.call(self, self);
                    }
                    if (!this.master && self.owner.on_edit_form_closed) {
                        self.owner.on_edit_form_closed.call(self, self);
                    }
                    if (self.on_edit_form_closed) {
                        self.on_edit_form_closed.call(self, self);
                    }
                },
                onKeyUp: this.do_on_edit_keyup,
                onKeyDown: this.do_on_edit_keydown
            })
        },

        close_edit_form: function() {
            this._close_form('edit_form');
        },

        create_filter_form: function() {
            var self = this,
                args = this._check_args(arguments),
                container = args['object'];
            this._create_form('filter', {
                container: container,
                beforeShow: function() {
                    if (self.task.on_filter_form_created) {
                        self.task.on_filter_form_created.call(self, self);
                    }
                    if (!self.master && self.owner.on_filter_form_created) {
                        self.owner.on_filter_form_created.call(self, self);
                    }
                    if (self.on_filter_form_created) {
                        self.on_filter_form_created.call(self, self);
                    }
                },
                onShown: function() {
                    if (self.task.on_filter_form_shown) {
                        self.task.on_filter_form_shown.call(self, self);
                    }
                    if (!self.master && self.owner.on_filter_form_shown && !self.master) {
                        self.owner.on_filter_form_shown.call(self, self);
                    }
                    if (self.on_filter_form_shown) {
                        self.on_filter_form_shown.call(self, self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_filter_form_close_query) {
                        canClose = self.on_filter_form_close_query.call(self, self);
                    }
                    if (!self.master && canClose === undefined && self.owner.on_filter_form_close_query) {
                        canClose = self.owner.on_filter_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_filter_form_close_query) {
                        canClose = self.task.on_filter_form_close_query.call(self, self);
                    }
                    return canClose;
                },
                onHidden: function() {
                    if (self.task.on_filter_form_closed) {
                        self.task.on_filter_form_closed.call(self, self);
                    }
                    if (!this.master && self.owner.on_filter_form_closed) {
                        self.owner.on_filter_form_closed.call(self, self);
                    }
                    if (self.on_filter_form_closed) {
                        self.on_filter_form_closed.call(self, self);
                    }
                }
            })
        },

        close_filter_form: function() {
            this._close_form('filter_form');
        },

        apply_filters: function() {
            try {
                if (this.on_filters_apply) {
                    this.on_filters_apply.call(this, this);
                }
                this.check_filters_valid();
                this.open(function() {
                    this.close_filter_form();
                });
            }
            catch (e) {
            }
        },

        get_filter_text: function() {
            var result = '';
            this.each_filter(function(filter) {
                if (filter.text) {
                    result += ' ' + filter.text;
                }
            });
            if (result) {
                result = language.filter + ' -' + result;
            }
            return result;
        },

        close_filter: function() { // depricated
            this.close_filter_form();
        },

        disable_controls: function() {
            this._disabled_count -= 1;
        },

        enable_controls: function() {
            this._disabled_count += 1;
            if (this.controls_enabled()) {
                this.update_controls(consts.UPDATE_SCROLLED);
            }
        },

        controls_enabled: function() {
            return this._disabled_count === 0;
        },

        controls_disabled: function() {
            return !this.controls_enabled();
        },

        update_controls: function(state) {
            var i = 0,
                len = this.fields.length;
            if (state === undefined) {
                state = consts.UPDATE_CONTROLS;
            }
            if (this.controls_enabled()) {
                for (i = 0; i < len; i++) {
                    this.fields[i].update_controls(true);
                }
                len = this.controls.length;
                if (this.on_update_controls) {
                    this.on_update_controls.call(this, this);
                }
                for (i = 0; i < len; i++) {
                    this.controls[i].update(state);
                }
            }
        },

        create_table: function(container, options) {
            return new DBTable(this, container, options);
        },

        create_tree: function(container, parent_field, text_field, parent_of_root_value, options) {
            return new DBTree(this, container, parent_field, text_field, parent_of_root_value, options);
        },

        create_inputs: function(container, options) {
            var default_options,
                i, len, col,
                field,
                fields = [],
                visible_fields = [],
                cols = [],
                tabindex,
                form;

            default_options = {
                fields: [],
                col_count: 1,
                label_on_top: false,
                controls_margin_left: undefined,
                label_width: undefined,
                row_count: undefined,
                autocomplete: false,
                tabindex: undefined
            };

            if (!container) {
                return;
            }

            options = $.extend({}, default_options, options);

            if (options.fields.length) {
                visible_fields = options.fields
            } else {
                visible_fields = this.edit_options.fields;
            }
            len = visible_fields.length;
            for (i = 0; i < len; i++) {
                field = this.field_by_name(visible_fields[i]);
                if (field) {
                    fields.push(field);
                } else {
                    throw this.item_name + ' create_entries: there is not a field with field_name - "' + visible_fields.fields[i] + '"';
                }
            }

            container.empty();

            form = $('<form class="row-fluid" autocomplete="off"></form>').appendTo($("<div></div>").appendTo(container));
            if (options.autocomplete) {
                form.attr("autocomplete", "on")
            }
            if (!options.label_on_top) {
                form.addClass("form-horizontal");
            }
            len = fields.length;
            for (col = 0; col < options.col_count; col++) {
                cols.push($("<div></div>").addClass("span" + 12 / options.col_count).appendTo(form));
            }
            tabindex = options.tabindex;
            if (!tabindex && this.edit_form) {
                tabindex = this.edit_form.tabindex;
                this.edit_form.tabindex += len;
            }
            if (!options.row_count) {
                options.row_count = Math.ceil(len / options.col_count);
            }
            for (i = 0; i < len; i++) {
                new DBInput(fields[i], i + tabindex, cols[Math.floor(i / options.row_count)],
                    options.label_on_top, options.controls_margin_left, options.label_width);
            }
        },

        create_filter_inputs: function(container, options) {
            var default_options,
                i, len, col,
                filter,
                filters = [],
                cols = [],
                tabindex,
                form;

            default_options = {
                    filters: [],
                    col_count: 1,
                    label_on_top: false,
                    controls_margin_left: undefined,
                    label_width: undefined,
                    autocomplete: false,
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
            form = $('<form autocomplete="off"></form>').appendTo($("<div></div>").addClass("row-fluid").appendTo(container));
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
                        options.label_on_top, options.controls_margin_left, options.label_width,
                        filter.filter_caption + ' ' + language.range_from);
                    new DBInput(filter.field1, i + 1, cols[Math.floor(i % options.col_count)],
                        options.label_on_top, options.controls_margin_left, options.label_width,
                        filter.filter_caption + ' ' + language.range_to);
                }
                else {
                    new DBInput(filter.field, i + 1, cols[Math.floor(i % options.col_count)],
                        options.label_on_top, options.controls_margin_left, options.label_width,
                        filter.filter_caption);
                }
            }
        },

        _find_lookup_value: function(field, lookup_field) {
            if (lookup_field.field_kind === consts.ITEM_FIELD) {
                if (field.field_name === lookup_field.lookup_field &&
                    field.lookup_field === lookup_field.lookup_field1 &&
                    field.lookup_field1 === lookup_field.lookup_field2) {
                    return field.lookup_value;
                }
                else if (field.field_kind === consts.ITEM_FIELD &&
                    field.owner.ID === lookup_field.lookup_item.ID && field.lookup_field &&
                    field.lookup_field === lookup_field.lookup_field1 &&
                    field.lookup_field1 === lookup_field.lookup_field2) {
                    return field.lookup_value;
                }
            }
            else  if (field.field_name === lookup_field.lookup_field) {
                return field.lookup_value;
            }
        },

        set_lookup_field_value: function() {
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
                if (lookup_field.multi_select) {
                    lookup_field.set_value([this._primary_key_field.value], lookup_value);
                } else {
                    if (item) {
                        item.each_field(function(item_field) {
                            if (item_field.master_field === lookup_field) {
                                self.each_field(function(field) {
                                    var lookup_value = self._find_lookup_value(field, item_field);
                                    if (lookup_value) {
                                        slave_field_values[item_field.field_name] = lookup_value;
                                        return false;
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
        },

        get_default_field: function() {
            var i = 0;
            if (this._default_field === undefined) {
                this._default_field = null;
                for (i = 0; i < this.fields.length; i++) {
                    if (this.fields[i].is_default) {
                        this._default_field = this.fields[i];
                        break;
                    }
                }
            }
            return this._default_field;
        },

        set_edit_fields: function(fields) {
            this.edit_options.fields = fields;
        },

        set_view_fields: function(fields) {
            this.view_options.fields = fields;
        },

        round: function(num, dec) {
            //        return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
            return Number(num.toFixed(dec));
        },

        refresh: function(callback) {
        },

        _do_on_refresh_record: function(copy, callback) {
            var i, len;
            if (copy.record_count() === 1) {
                len = copy._dataset[0].length;
                for (i = 0; i < len; i++) {
                    this._dataset[this.rec_no][i] = copy._dataset[0][i];
                }
                this.update_controls(consts.UPDATE_CANCEL);
                if (callback) {
                    callback.call(this, this);
                }
            }
        },

        refresh_record: function(callback) {
            var self = this,
                fields = [],
                primary_key = this._primary_key,
                where = {},
                copy;
            if (this.master) {
                throw 'The refresh_record method can not be executed for a detail item';
            }
            copy = this.copy({filters: false, details: false, handlers: false});
            if (this._primary_key_field.value !== null) {
                self.each_field(function(field) {
                    fields.push(field.field_name)
                })
                where[primary_key] = this._primary_key_field.value;

                if (callback) {
                    copy.open({expanded: this.expanded, fields: fields, where: where}, function() {
                        self._do_on_refresh_record(copy, callback);
                    });
                } else {
                    copy.open({expanded: this.expanded, fields: fields, where: where});
                    this._do_on_refresh_record(copy);
                }
            }
        }
    });

    /**********************************************************************/
    /*                           Report class                             */
    /**********************************************************************/

    Report.prototype = new AbsrtactItem();

    function Report(owner, ID, item_name, caption, visible, type, js_filename) {
        AbsrtactItem.call(this, owner, ID, item_name, caption, visible, type, js_filename);
        if (this.task && !(item_name in this.task)) {
            this.task[item_name] = this;
        }
        this._fields = [];
        this.params = this._fields;
        this._state = consts.STATE_EDIT;
        this.param_options = $.extend({}, this.modal_options);
    }

    $.extend(Report.prototype, {
        constructor: Report,

        _set_item_state: function(value) {
            if (this._state !== value) {
                this._state = value;
            }
        },

        _get_item_state: function() {
            return this._state;
        },

        initAttr: function(info) {
            var i,
                params = info.fields,
                len;
            if (params) {
                len = params.length;
                for (i = 0; i < len; i++) {
                    new Param(this, params[i]);
                }
            }
        },

        bind_item: function() {
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
        },

        eachParam: function(callback) {
            var i = 0,
                len = this.params.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.params[i], this.params[i], i);
                if (value === false) {
                    break;
                }
            }
        },

        each_field: function(callback) {
            this.eachParam(callback);
        },

        param_by_name: function(name) {
            var i = 0,
                len = this.params.length;
            for (; i < len; i++) {
                if (this.params[i].param_name === name) {
                    return this.params[i];
                }
            }
        },

        create_param_form: function() {
            var self = this,
                args = this._check_args(arguments),
                container = args['object'];
            this._create_form('param', {
                container: container,
                beforeShow: function() {
                    if (self.task.on_param_form_created) {
                        self.task.on_param_form_created.call(self, self);
                    }
                    if (self.owner.on_param_form_created) {
                        self.owner.on_param_form_created.call(self, self);
                    }
                    if (self.on_param_form_created) {
                        self.on_param_form_created.call(self, self);
                    }
                },
                onShown: function() {
                    if (self.task.on_param_form_shown) {
                        self.task.on_param_form_shown.call(self, self);
                    }
                    if (self.owner.on_param_form_shown) {
                        self.owner.on_param_form_shown.call(self, self);
                    }
                    if (self.on_param_form_shown) {
                        self.on_param_form_shown.call(self, self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_param_form_close_query) {
                        canClose = self.on_param_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.owner.on_param_form_close_query) {
                        canClose = self.owner.on_param_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_param_form_close_query) {
                        canClose = self.task.on_param_form_close_query.call(self, self);
                    }
                    return canClose;
                },
                onHidden: function() {
                    if (self.task.on_param_form_closed) {
                        self.task.on_param_form_closed.call(self, self);
                    }
                    if (!this.master && self.owner.on_param_form_closed) {
                        self.owner.on_param_form_closed.call(self, self);
                    }
                    if (self.on_param_form_closed) {
                        self.on_param_form_closed.call(self, self);
                    }
                }
            })
        },

        close_param_form: function() {
            this._close_form('param_form');
        },

        print: function(p1, p2) {
            var self = this;
            this.load_modules([this, this.owner], function() {
                self._print(p1, p2);
            })
        },

        _print: function() {
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
        },

        checkParams: function() {
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
        },

        process_report: function(callback) {
            var self = this,
                host = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : ''),
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
                    param_values.push(this.params[i].get_raw_value());
                }
                this.send_request('print_report', [param_values, host, this.extension], function(result) {
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
        },

        create_param_inputs: function(container, options) {
            var default_options,
                i, len, col,
                params = [],
                cols = [],
                form,
                tabindex;

            default_options = {
                params: [],
                col_count: 1,
                label_on_top: false,
                controls_margin_left: undefined,
                label_width: undefined,
                autocomplete: false,
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
                params.sort(function(param1, param2) {
                    if (param1.edit_index > param2.edit_index === 0) {
                        return 0;
                    }
                    if (param1.edit_index > param2.edit_index) {
                        return 1;
                    } else {
                        return -1;
                    }
                });
            }
            container.empty();
            form = $('<form autocomplete="off"></form>').appendTo($("<div></div>").addClass("row-fluid").appendTo(container));
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
                new DBInput(params[i], i + tabindex, cols[Math.floor(i % options.col_count)],
                    options.label_on_top, options.controls_margin_left, options.label_width);
            }
        }
    });

    /**********************************************************************/
    /*                            Detail class                            */
    /**********************************************************************/

    Detail.prototype = new Item();
    Detail.prototype.constructor = Detail;

    function Detail(owner, ID, item_name, caption, visible, type, js_filename) {
        Item.call(this, owner, ID, item_name, caption, visible, type, js_filename);

        this.master = owner;
        owner.details.push(this);
        owner.details[item_name] = this;
        this.item_type = "detail";
    }

    Detail.prototype.getChildClass = function() {
        return undefined;
    };

    /**********************************************************************/
    /*                             Field class                            */
    /**********************************************************************/

    function Field(owner, info) {
        this.owner = owner;
        this.set_info(info);
        this.controls = [];
        this.bind_index = null;
        this.lookup_index = null;
        this.field_type = this.type_names[this.data_type];
        this.field_kind = consts.ITEM_FIELD;
        if (owner) {
            owner._fields.push(this);
        }
        Object.defineProperty(this, "value", {
            get: function() {
                return this.get_value();
            },
            set: function(new_value) {
                this.set_value(new_value);
            }
        });
        Object.defineProperty(this, "raw_value", {
            get: function() {
                return this.get_raw_value();
            },
        });
        Object.defineProperty(this, "text", {
            get: function() {
                return this.get_text();
            },
            set: function(new_value) {
                this.set_text(new_value);
            }
        });
        Object.defineProperty(this, "display_text", {
            get: function() {
                return this.get_display_text();
            }
        });
        Object.defineProperty(this, "lookup_text", {
            get: function() {
                return this.get_lookup_text();
            }
        });
        Object.defineProperty(this, "lookup_value", {
            get: function() {
                return this.get_lookup_value();
            },
            set: function(new_value) {
                this.set_lookup_value(new_value);
            }
        });
        Object.defineProperty(this, "alignment", {
            get: function() {
                return this.get_alignment();
            },
            set: function(new_value) {
                this.set_alignment(new_value);
            }
        });
        Object.defineProperty(this, "read_only", {
            get: function() {
                return this._get_read_only();
            },
            set: function(new_value) {
                this._set_read_only(new_value);
            }
        });
    }

    Field.prototype = {
        constructor: Field,

        attr: [
            "ID",
            "field_name",
            "field_caption",
            "data_type",
            "required",
            "lookup_item",
            "master_field",
            "lookup_field",
            "lookup_field1",
            "lookup_field2",
            "view_visible",
            "view_index",
            "edit_visible",
            "edit_index",
            "_read_only",
            "_expand",
            "_word_wrap",
            "field_size",
            "default_value",
            "is_default",
            "calculated",
            "editable",
            "_alignment",
            "lookup_values",
            "multi_select",
            "multi_select_all",
            "enable_typeahead",
            "field_help",
            "field_placeholder"
        ],

        type_names: ["", "text", "integer", "float", 'currency',
            "date", "datetime", "boolean", "blob"
        ],

        copy: function(owner) {
            var result = new Field(owner, this.get_info());
            result.lookup_item = this.lookup_item;
            result.lookup_field = this.lookup_field;
            return result;
        },

        get_info: function() {
            var i,
                len = this.attr.length,
                result = [];
            for (i = 0; i < len; i++) {
                result.push(this[this.attr[i]]);
            }
            return result;
        },

        set_info: function(info) {
            if (info) {
                var i,
                    len = this.attr.length;
                for (i = 0; i < len; i++) {
                    this[this.attr[i]] = info[i];
                }
            }
        },

        get_row: function() {
            if (this.owner._dataset) {
                return this.owner._dataset[this.owner._get_rec_no()];
            } else {
                throw language.value_in_empty_dataset.replace('%s', this.owner.item_name);
            }
        },

        get_data: function() {
            var row;
            if (this.field_kind === consts.ITEM_FIELD) {
                row = this.get_row();
                if (row && this.bind_index >= 0) {
                    return row[this.bind_index];
                }
            } else {
                return this._value;
            }
        },

        set_data: function(value) {
            var row;
            if (this.field_kind === consts.ITEM_FIELD) {
                row = this.get_row();
                if (row && this.bind_index >= 0) {
                    row[this.bind_index] = value;
                }
            } else {
                this._value = value;
            }
        },

        get_lookup_data: function() {
            var row;
            if (this.field_kind === consts.ITEM_FIELD) {
                row = this.get_row();
                if (row && this.lookup_index >= 0) {
                    return row[this.lookup_index];
                }
            } else {
                return this._lookup_value;
            }
        },

        set_lookup_data: function(value) {
            var row;
            if (this.field_kind === consts.ITEM_FIELD) {
                row = this.get_row();
                if (row && this.lookup_index >= 0) {
                    row[this.lookup_index] = value;
                }
            } else {
                this._lookup_value = value
            }
        },

        get_text: function() {
            var result = "",
                error = "";
            try {
                result = this.get_value();
                if (result !== null) {
                    switch (this.data_type) {
                        case consts.TEXT:
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
                            if (this.get_value()) {
                                result = language.yes;
                            } else {
                                result = language.no;
                            }
                            break;
                    }
                } else {
                    result = "";
                }
            } catch (e) {
                result = '';
                throw e;
            }
            if (typeof result !== 'string') {
                result = ''
            }
            return result;
        },

        set_text: function(value) {
            var error = "";

            if (value !== this.get_text()) {
                try {
                    switch (this.data_type) {
                        case consts.TEXT:
                            this.set_value(value);
                            break;
                        case consts.INTEGER:
                            this.set_value(this.str_to_int(value));
                            break;
                        case consts.FLOAT:
                            this.set_value(this.str_to_float(value));
                            break;
                        case consts.CURRENCY:
                            this.set_value(this.str_to_float(value));
                            break;
                        case consts.DATE:
                            this.set_value(this.str_to_date(value));
                            break;
                        case consts.DATETIME:
                            this.set_value(this.str_to_datetime(value));
                            break;
                        case consts.BOOLEAN:
                            if (language) {
                                if (value.length && value.toUpperCase().trim() === language.yes.toUpperCase().trim()) {
                                    this.set_value(true);
                                } else {
                                    this.set_value(false);
                                }
                            } else {
                                if (value.length && (value[0] === 'T' || value[0] === 't')) {
                                    this.set_value(true);
                                } else {
                                    this.set_value(false);
                                }
                            }
                            break;
                        default:
                            this.set_value(value);
                    }
                } catch (e) {
                    error = this.field_caption + ": " + this.type_error();
                    throw error;
                }
            }
        },

        convert_date_time: function(value) {
            if (value.search('.') !== -1) {
                value = value.split('.')[0];
            }
            return this.format_string_to_date(value, '%Y-%m-%d %H:%M:%S');
        },

        convert_date: function(value) {
            if (value.search(' ') !== -1) {
                value = value.split(' ')[0];
            }
            return this.format_string_to_date(value, '%Y-%m-%d');
        },

        get_raw_value: function() {
            var result = this.get_data();
            if (this.data_type === consts.DATETIME && result) {
                result = result.replace('T', ' ');
            }
            else if (this.multi_select) {
                if (result instanceof Array) {
                    if (!result.length) {
                        result = null;
                    }
                }
            }
            return result;
        },

        get_value: function() {
            var value = this.get_raw_value();
            if (value === null) {
                if (this.field_kind === consts.ITEM_FIELD) {
                    switch (this.data_type) {
                        case consts.INTEGER:
                            value = 0;
                            break;
                        case consts.FLOAT:
                            value = 0;
                            break;
                        case consts.CURRENCY:
                            value = 0;
                            break;
                        case consts.TEXT:
                            value = '';
                            break;
                        case consts.BOOLEAN:
                            value = false;
                            break;
                    }
                }
            }
            else {
                switch (this.data_type) {
                    case consts.DATE:
                        value = this.convert_date(value);
                        break;
                    case consts.DATETIME:
                        value = this.convert_date_time(value);
                        break;
                    case consts.BOOLEAN:
                        return value ? true : false;
                        break;
                }
            }
            return value;
        },

        _change_lookup_field: function(lookup_value, slave_field_values) {
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
        },

        _do_before_changed: function() {
            if (this.field_kind === consts.ITEM_FIELD) {
                if (this.owner._get_item_state() !== consts.STATE_INSERT && this.owner._get_item_state() !== consts.STATE_EDIT) {
                    throw language.not_edit_insert_state.replace('%s', this.owner.item_name);
                }
                if (this.owner.on_before_field_changed) {
                    this.owner.on_before_field_changed.call(this.owner, this);
                }
            }
        },

        _do_after_changed: function(lookup_item) {
            if (this.owner && this.owner.on_field_changed) {
                this.owner.on_field_changed.call(this.owner, this, lookup_item);
            }
            if (this.filter) {
                this.filter.update(this);
                if (this.filter.owner.on_filter_changed) {
                    this.filter.owner.on_filter_changed.call(this.filter.owner, this.filter);
                }
            }
        },

        _check_system_field_value: function(value) {
            if (this.field_kind === consts.ITEM_FIELD) {
                if (this.field_name === this.owner._primary_key && this.value && this.value !== value) {
                    throw language.no_primary_field_changing.replace('%s', this.owner.item_name);
                }
                if (this.field_name === this.owner._deleted_flag && this.value !== value) {
                    throw language.no_deleted_field_changing.replace('%s', this.owner.item_name);
                }
            }
        },

        set_value: function(value, lookup_value, slave_field_values, lookup_item) {
            if (value === undefined) {
                value = null;
            }
            this._check_system_field_value(value);
            this.new_value = null;
            this.new_lookup_value = lookup_value;
            if (value !== null) {
                this.new_value = value;
                if (!this.multi_select) {
                    switch (this.data_type) {
                        case consts.INTEGER:
                            this.new_value = value;
                            if (typeof(value) === "string") {
                                this.new_value = parseInt(value, 10);
                            }
                            break;
                        case consts.FLOAT:
                            this.new_value = value;
                            if (typeof(value) === "string") {
                                this.new_value = parseFloat(value);
                            }
                            break;
                        case consts.CURRENCY:
                            this.new_value = value;
                            if (typeof(value) === "string") {
                                this.new_value = parseFloat(value);
                            }
                            break;
                        case consts.BOOLEAN:
                            this.new_value = value ? 1 : 0;
                            break;
                        case consts.DATE:
                            this.new_value = this.format_date_to_string(value, '%Y-%m-%d');
                            break;
                        case consts.DATETIME:
                            this.new_value = this.format_date_to_string(value, '%Y-%m-%d %H:%M:%S');
                            break;
                        case consts.TEXT:
                            this.new_value = value + '';
                            break;
                    }
                }
            }
            if (this.get_raw_value() !== this.new_value) {
                this._do_before_changed();
                try {
                    this.set_data(this.new_value);
                } catch (e) {
                    throw this.field_name + ": " + this.type_error();
                }
                this._change_lookup_field(lookup_value, slave_field_values);
                this._set_modified(true);
                this._do_after_changed(lookup_item);
            } else if (lookup_value && lookup_value !== this.lookup_value) {
                this.lookup_value = lookup_value;
                this._do_after_changed(lookup_item, slave_field_values);
            }
            this.new_value = null;
            this.new_lookup_value = null;
            this.update_controls();
        },

        _set_modified: function(value) {
            if (this.field_kind === consts.ITEM_FIELD) {
                if (this.owner._set_modified && !this.calculated) {
                    this.owner._set_modified(value);
                }
            }
        },

        get_lookup_data_type: function() {
            if (this.lookup_values) {
                return consts.TEXT;
            } else if (this.lookup_item) {
                if (this.lookup_field2) {
                    return this.lookup_item2._field_by_name(this.lookup_field2).data_type;
                }
                else if (this.lookup_field1) {
                    return this.lookup_item1._field_by_name(this.lookup_field1).data_type;
                }
                else {
                    return this.lookup_item._field_by_name(this.lookup_field).data_type;
                }
            } else {
                return this.data_type
            }
        },

        get_lookup_value: function() {
            var value = null;
            if (this.lookup_item) {
                if (this.get_value()) {
                    value = this.get_lookup_data();
                    switch (this.get_lookup_data_type()) {
                        case consts.DATE:
                            if (typeof(value) === "string") {
                                value = this.convert_date(value);
                            }
                            break;
                        case consts.DATETIME:
                            if (typeof(value) === "string") {
                                value = this.convert_date_time(value);
                            }
                            break;
                        case consts.BOOLEAN:
                            if (value) {
                                return true;
                            } else {
                                return false;
                            }
                            break;
                    }
                }
            } else {
                value = this.get_value();
            }
            return value;
        },

        set_lookup_value: function(value) {
            if (this.lookup_item) {
                this.set_lookup_data(value);
                this.update_controls();
            }
        },

        get_lookup_text: function() {
            var self = this,
                data_type,
                result = '';
            try {
                if (this.lookup_item) {
                    if (this.get_value()) {
                        result = this.get_lookup_value();
                    }
                    if (result === null) {
                        result = '';
                    } else {
                        data_type = this.get_lookup_data_type()
                        if (data_type) {
                            switch (data_type) {
                                case consts.DATE:
                                    result = this.date_to_str(result);
                                    break;
                                case consts.DATETIME:
                                    result = this.datetime_to_str(result);
                                    break;
                                case consts.FLOAT:
                                    result = this.float_to_str(result);
                                    break;
                                case consts.CURRENCY:
                                    result = this.cur_to_str(result);
                                    break;
                            }
                        }
                    }
                }
            } catch (e) {}
            return result;
        },

        _get_value_in_list: function() {
            var i = 0,
                len = this.lookup_values.length,
                result = '';
            for (; i < len; i++) {
                if (this.lookup_values[i][0] === this.value) {
                    result = this.lookup_values[i][1];
                }
            }
            return result
        },

        get_display_text: function() {
            var res,
                len,
                value,
                result = '';
            if (this.multi_select) {
                value = this.raw_value;
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
            else if (this.lookup_values) {
                try {
                    result = this._get_value_in_list();
                } catch (e) {}
            } else if (this.lookup_item) {
                result = this.get_lookup_text();
            } else {
                if (this.data_type === consts.CURRENCY) {
                    if (this.raw_value !== null) {
                        result = this.cur_to_str(this.get_value());
                    }
                } else {
                    result = this.get_text();
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
            if (result === undefined) {
                result = '';
            }
            return result;
        },

        _set_read_only: function(value) {
            this._read_only = value;
            this.update_controls();
        },

        _get_read_only: function() {
            var result = this._read_only;
            if (this.owner && this.owner._parent_read_only && this.owner._get_read_only()) {
                result = this.owner._get_read_only();
            }
            return result;
        },

        set_visible: function(value) {
            this._visible = value;
            this.update_controls();
        },

        get_visible: function() {
            return this._visible;
        },

        set_alignment: function(value) {
            this._alignment = value;
            this.update_controls();
        },

        get_alignment: function() {
            return this._alignment;
        },

        set_expand: function(value) {
            this._expand = value;
            this.update_controls();
        },

        get_expand: function() {
            return this._expand;
        },

        set_word_wrap: function(value) {
            this._word_wrap = value;
            this.update_controls();
        },

        get_word_wrap: function() {
            return this._word_wrap;
        },

        check_type: function() {
            this.get_value();
            if ((this.data_type === consts.TEXT) && (this.field_size !== 0) && (this.get_text().length > this.field_size)) {
                throw this.field_caption + ': ' + language.invalid_length.replace('%s', this.field_size);
            }
            return true;
        },

        check_reqired: function() {
            if (!this.required) {
                return true;
            } else if (this.get_raw_value() !== null) {
                return true;
            } else {
                throw this.field_caption + ': ' + language.value_required;
            }
        },

        check_valid: function() {
            var err;
            if (this.check_reqired()) {
                if (this.check_type()) {
                    if (this.owner && this.owner.on_field_validate) {
                        err = this.owner.on_field_validate.call(this.owner, this);
                        if (err) {
                            throw err;
                            return;
                        }
                    }
                    if (this.filter) {
                        err = this.filter.check_value(this)
                        if (err) {
                            throw err;
                            return;
                        }
                    }
                    return true;
                }
            }
        },

        typeahead_options: function() {
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
                    if (self.owner && self.owner.on_param_select_value) {
                        self.owner.on_param_select_value.call(self.owner, self, lookup_item);
                    }
                    if (self.owner && self.owner.on_field_select_value) {
                        self.owner.on_field_select_value.call(self.owner, self, lookup_item);
                    }
                    if (self.filter && self.filter.owner.on_filter_select_value) {
                        self.filter.owner.on_filter_select_value.call(self.filter.owner, self.filter, lookup_item);
                    }
                    params.__search = [self.lookup_field, query];
                    lookup_item.open({limit: length, params: params}, function(item) {
                        var data = [],
                            field = item.field_by_name(self.lookup_field);
                        item.each(function(i) {
                            data.push([i.id.value, field.value]);
                        });
                        return process(data);
                    });
                }
            }
            return result;
        },

        get_typeahead_defs: function($input) {
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
                    if (self.owner && self.owner.on_param_select_value) {
                        self.owner.on_param_select_value.call(self.owner, self, lookup_item);
                    }
                    if (self.owner && self.owner.on_field_select_value) {
                        self.owner.on_field_select_value.call(self.owner, self, lookup_item);
                    }
                    if (self.filter && self.filter.owner.on_filter_select_value) {
                        self.filter.owner.on_filter_select_value.call(self.filter.owner, self.filter, lookup_item);
                    }
                    params.__search = [self.lookup_field, query];
                    lookup_item.open({limit: items, params: params}, function(item) {
                        var data = [],
                            field = item.field_by_name(self.lookup_field);
                        item.each(function(i) {
                            console.log(i.id.value, field.value);
//                            data.push(i.rec_no);
                            data.push([i.id.value, field.value]);
                        });
                        return process(data);
                    });
                },
            }
            return def;
        },

        system_field: function() {
            if (this.field_name === this.owner._primary_key ||
                this.field_name === this.owner._deleted_flag ||
                this.field_name === this.owner._master_id ||
                this.field_name === this.owner._master_rec_id) {
                return true;
            }
        },

        update_controls: function(owner_updating) {
            var i,
                len;
            len = this.controls.length;
            for (i = 0; i < len; i++) {
                this.controls[i].update();
            }
            if (!owner_updating && this.owner && this.owner.controls) {
                len = this.owner.controls.length;
                for (i = 0; i < len; i++) {
                    this.owner.controls[i].update_field(this);
                }
            }
        },

        update_control_state: function(error) {
            for (var i = 0; i < this.controls.length; i++) {
                this.controls[i].error = error;
                this.controls[i].updateState(false);
            }
        },

        type_error: function() {
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
        },

        valid_char_code: function(code) {
            var ch = String.fromCharCode(code),
                isDigit = code >= 48 && code <= 57,
                decPoint = ch === '.' || ch === settings.DECIMAL_POINT || ch === settings.MON_DECIMAL_POINT,
                sign = ch === '+' || ch === '-',
                data_type = this.get_lookup_data_type();
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
        },

        str_to_int: function(str) {
            var result = parseInt(str, 10);
            if (isNaN(result)) {
                throw "invalid integer value";
            }
            return result;
        },

        str_to_date: function(str) {
            return this.format_string_to_date(str, settings.D_FMT);
        },

        str_to_datetime: function(str) {
            return this.format_string_to_date(str, settings.D_T_FMT);
        },

        str_to_float: function(text) {
            var result;
            text = text.replace(settings.DECIMAL_POINT, ".")
            text = text.replace(settings.MON_DECIMAL_POINT, ".")
            result = parseFloat(text);
            if (isNaN(result)) {
                throw "invalid float value";
            }
            return result;
        },

        str_to_cur: function(val) {
            var result = '';
            if (value) {
                result = $.trim(val);
                if (settings.MON_THOUSANDS_SEP) {
                    result = result.replace(settings.MON_THOUSANDS_SEP, '');
                }
                if (settings.CURRENCY_SYMBOL) {
                    result = $.trim(result.replace(settings.CURRENCY_SYMBOL, ''));
                }
                if (settings.POSITIVE_SIGN) {
                    result = result.replace(settings.POSITIVE_SIGN, '');
                }
                if (settings.NEGATIVE_SIGN && result.indexOf(settings.NEGATIVE_SIGN) !== -1) {
                    result = result.replace(settings.NEGATIVE_SIGN, '')
                    result = '-' + result
                }
                result = $.trim(result.replace(settings.MON_DECIMAL_POINT, '.'));
                result = parseFloat(result);
            }
            return result;
        },

        int_to_str: function(value) {
            if (value || value === 0) {
                return value.toString();
            }
            else {
                return '';
            }
        },

        float_to_str: function(value) {
            var str,
                i,
                result = '';
            if (value || value === 0) {
                str = ('' + value.toFixed(6)).replace(".", settings.DECIMAL_POINT);
                i = str.length - 1;
                for (; i >= 0; i--) {
                    if ((str[i] === '0') && (result.length === 0)) {
                        continue;
                    } else {
                        result = str[i] + result;
                    }
                }
                if (result.slice(result.length - 1) === settings.DECIMAL_POINT) {
                    result = result + '0';
                }
            }
            return result;
        },

        date_to_str: function(value) {
            if (value) {
                return this.format_date_to_string(value, settings.D_FMT);
            }
            else {
                return '';
            }
        },

        datetime_to_str: function(value) {
            if (value) {
                return this.format_date_to_string(value, settings.D_T_FMT);
            }
            else {
                return '';
            }
        },

        cur_to_str: function(value) {
            var point,
                dec,
                digits,
                i,
                d,
                count = 0,
                len,
                result = '';

            if (value || value === 0) {
                result = value.toFixed(settings.FRAC_DIGITS);
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
                        result = settings.MON_THOUSANDS_SEP + result;
                    }
                }
                if (dec) {
                    result = result + settings.MON_DECIMAL_POINT + dec;
                }
                if (value < 0) {
                    if (settings.N_SIGN_POSN === 3) {
                        result = settings.NEGATIVE_SIGN + result;
                    } else if (settings.N_SIGN_POSN === 4) {
                        result = settings.result + settings.NEGATIVE_SIGN;
                    }
                } else {
                    if (settings.P_SIGN_POSN === 3) {
                        result = settings.POSITIVE_SIGN + result;
                    } else if (settings.P_SIGN_POSN === 4) {
                        result = result + settings.POSITIVE_SIGN;
                    }
                }
                if (settings.CURRENCY_SYMBOL) {
                    if (value < 0) {
                        if (settings.N_CS_PRECEDES) {
                            if (settings.N_SEP_BY_SPACE) {
                                result = settings.CURRENCY_SYMBOL + ' ' + result;
                            } else {
                                result = settings.CURRENCY_SYMBOL + result;
                            }
                        } else {
                            if (settings.N_SEP_BY_SPACE) {
                                result = result + ' ' + settings.CURRENCY_SYMBOL;
                            } else {
                                result = result + settings.CURRENCY_SYMBOL;
                            }
                        }
                    } else {
                        if (settings.P_CS_PRECEDES) {
                            if (settings.P_SEP_BY_SPACE) {
                                result = settings.CURRENCY_SYMBOL + ' ' + result;
                            } else {
                                result = settings.CURRENCY_SYMBOL + result;
                            }
                        } else {
                            if (settings.P_SEP_BY_SPACE) {
                                result = result + ' ' + settings.CURRENCY_SYMBOL;
                            } else {
                                result = result + settings.CURRENCY_SYMBOL;
                            }
                        }
                    }
                }
                if (value < 0) {
                    if (settings.N_SIGN_POSN === 0 && settings.NEGATIVE_SIGN) {
                        result = settings.NEGATIVE_SIGN + '(' + result + ')';
                    } else if (settings.N_SIGN_POSN === 1) {
                        result = settings.NEGATIVE_SIGN + result;
                    } else if (settings.N_SIGN_POSN === 2) {
                        result = result + settings.NEGATIVE_SIGN;
                    }
                } else {
                    if (settings.P_SIGN_POSN === 0 && settings.POSITIVE_SIGN) {
                        result = settings.POSITIVE_SIGN + '(' + result + ')';
                    } else if (settings.P_SIGN_POSN === 1) {
                        result = settings.POSITIVE_SIGN + result;
                    } else if (settings.P_SIGN_POSN === 2) {
                        result = result + settings.POSITIVE_SIGN;
                    }
                }
            }
            return result;
        },

        parseDateInt: function(str, digits) {
            var result = parseInt(str.substring(0, digits), 10);
            if (isNaN(result)) {
                //            result = 0
                throw 'invalid date';
            }
            return result;
        },

        format_string_to_date: function(str, format) {
            var ch = '',
                substr = str,
                day, month, year,
                hour = 0,
                min = 0,
                sec = 0;
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
            return new Date(year, month - 1, day, hour, min, sec);
        },

        leftPad: function(value, len, ch) {
            var result = value.toString();
            while (result.length < len) {
                result = ch + result;
            }
            return result;
        },

        format_date_to_string: function(date, format) {
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
        },

        select_value: function() {
            var copy = this.lookup_item.copy();
            copy.is_lookup_item = true; //depricated
            copy.lookup_field = this;
            if (this.owner && this.owner.on_param_select_value) {
                this.owner.on_param_select_value.call(this.owner, this, copy);
            }
            if (this.owner && this.owner.on_field_select_value) {
                this.owner.on_field_select_value.call(this.owner, this, copy);
            }
            if (this.filter && this.filter.owner.on_filter_select_value) {
                this.filter.owner.on_filter_select_value.call(this.filter.owner, this.filter, copy);
            }
            copy.view();
        }
    };

    /**********************************************************************/
    /*                            Filter class                            */
    /**********************************************************************/

    function Filter(owner, info) {
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
            }
        }
        Object.defineProperty(this, "value", {
            get: function() {
                return this.get_value();
            },
            set: function(new_value) {
                this.set_value(new_value);
            }
        });
        Object.defineProperty(this, "text", {
            get: function() {
                return this.get_text();
            }
        });
    }

    Filter.prototype = {
        constructor: Filter,

        attr: [
            "filter_name",
            "filter_caption",
            "field_name",
            "filter_type",
            "multi_select_all",
            "data_type",
            "visible",
            "filter_help",
            "filter_placeholder"
        ],

        create_field: function(field) {
            var result = new Field();
            result.set_info(field.get_info());
            result._read_only = false;
            result.filter = this;
            result._value = null;
            result._lookup_value = null;
            result.field_kind = consts.FILTER_FIELD;
            return result;
        },

        copy: function(owner) {
            var result = new Filter(owner, this.get_info());
            return result;
        },

        get_info: function() {
            var i,
                len = this.attr.length,
                result = [];
            for (i = 0; i < len; i++) {
                result.push(this[this.attr[i]]);
            }
            return result;
        },

        set_info: function(info) {
            if (info) {
                var i,
                    len = this.attr.length;
                for (i = 0; i < len; i++) {
                    this[this.attr[i]] = info[i];
                }
            }
        },

        get_value: function() {
            if (this.filter_type === consts.FILTER_RANGE) {
                if (this.field.raw_value !== null && this.field1.raw_value !== null) {
                    return [this.field.raw_value, this.field1.raw_value];
                }
                else {
                    return null;
                }
            }
            else {
                return this.field.raw_value;
            }
        },

        set_value: function(value, lookup_value) {
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
            else {
                this.field.set_value(value, lookup_value);
            }
        },

        update: function(field) {
            var other_field = this.field;
            if (this.filter_type === consts.FILTER_RANGE) {
                if (field.value !== null) {
                    if (field === this.field) {
                        other_field = this.field1;
                    }
                    if (other_field.raw_value === null) {
                        other_field.value = field.value;
                    }
                }
            }
        },

        check_valid: function() {
            var error = this.check_value(this.field);
            if (error) {
                throw error;
            }
        },

        check_value: function(field) {
            if (this.filter_type === consts.FILTER_RANGE) {
                if (this.field.raw_value === null && this.field1.raw_value !== null ||
                    this.field.raw_value !== null && this.field1.raw_value === null ||
                    this.field.value > this.field1.value) {
                    return language.invalid_range;
                }
            }
        },

        get_text: function() {
            var result = '';
            if (this.visible && this.value != null) {
                result = this.filter_caption + ': ';
                if (this.filter_type === consts.FILTER_RANGE) {
                    result += this.field.get_display_text() + ' - ' + this.field1.get_display_text();
                }
                else if (this.field.data_type === consts.BOOLEAN) {
                    if (this.field.value) {
                        result += 'x'
                    }
                    else {
                        result += '-'
                    }
                } else {
                    result += this.field.get_display_text();
                }
            }
            return result;
        }
    };

    /**********************************************************************/
    /*                             Param class                            */
    /**********************************************************************/

    Param.prototype = new Field();
    Param.prototype.constructor = Field;

    function Param(owner, info) {
        Field.call(this, owner, info);
        this.param_name = this.field_name;
        this.param_caption = this.field_caption;
        this.field_size = 0;
        this.report = owner;
        this._value = null;
        this._lookup_value = null;
        this.field_kind = consts.PARAM_FIELD;
        if (this.owner[this.param_name] === undefined) {
            this.owner[this.param_name] = this;
        }
    }

    /**********************************************************************/
    /*                            DBTree class                            */
    /**********************************************************************/

    function DBTree(item, container, parent_field, text_field, parent_of_root_value, options) {
        this.init(item, container, parent_field, text_field, parent_of_root_value, options);
    }

    DBTree.prototype = {
        constructor: DBTree,

        init: function(item, container, options) {
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
            this.item = item;
            this.$container = container;
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
            if (item._get_active() && this.$container.width()) {
                this.build();
            }
        },

        form_closing: function() {
            var $modal = this.$element.closest('.modal');
            if ($modal) {
                return $modal.data('_closing')
            }
            return false;
        },

        height: function(value) {
            if (value) {
                this.$element.height(value);
            } else {
                return this.$element.height();
            }
        },

        is_focused: function() {
            return this.$element.get(0) === document.activeElement;
        },

        scroll_into_view: function() {
            this.select_node(this.selected_node);
        },

        update: function(state) {
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
                case consts.UPDATE_CANCEL:
                    this.changed();
                    break;
                case consts.UPDATE_APPEND:
                    this.changed();
                    break;
                case consts.UPDATE_INSERT:
                    this.changed();
                    break;
                case consts.UPDATE_DELETE:
                    this.changed();
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
                case consts.UPDATE_REFRESH:
//                    this.build();
                    break;
            }
        },

        keydown: function(e) {
            var self = this,
                $li,
                code = (e.keyCode ? e.keyCode : e.which);
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
        },

        keyup: function(e) {
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
        },

        build_child_nodes: function(tree, nodes) {
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
        },

        collect_nodes: function(clone) {
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
        },

        build: function() {
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
                clone._set_rec_no(rec);
                this.item._cur_row = rec;
                $li.data("record", clone._dataset[rec]);
                info = clone.rec_controls_info();
                info[this.id] = $li.get();
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
        },

        toggle_expanded: function($li) {
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
        },

        expand: function($li) {
            if ($li.hasClass('parent') && $li.hasClass('collapsed')) {
                this.toggle_expanded($li);
            }
            $li = $li.parent().parent()
            if ($li.prop("tagName") === "LI") {
                this.expand($li);
            }
        },

        collapse: function($li) {
            if ($li.hasClass('parent') && !$li.hasClass('collapsed')) {
                this.toggle_expanded($li);
            }
        },

        select_node: function($li, update_node) {
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
                    this.item._set_rec_no(rec);
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
        },

        update_selected_node: function($li) {
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
        },

        update_field: function() {
        },

        syncronize: function() {
            var info,
                $li;
            if (this.item.record_count()) {
                try {
                    info = this.item.rec_controls_info(),
                        $li = $(info[this.id]);
                    this.select_node($li);
                } catch (e) {
                    console.log(e);
                }
            }
        },

        changed: function() {},
    }

    /**********************************************************************/
    /*                            DBTable class                           */
    /**********************************************************************/

    function DBTable(item, container, options) {
        this.init(item, container, options);
    }

    DBTable.prototype = {
        constructor: DBTable,

        init: function(item, container, options) {
            var self = this,
                default_options = {
                    table_class: undefined,
                    height: 480,
                    fields: [],
                    column_width: {},
                    title_word_wrap: false,
                    row_line_count: 1,
                    expand_selected_row: 0,
                    auto_fit_width: true,
                    selections: undefined,
                    select_all: true,
                    selection_limit: 1500,
                    tabindex: 0,
                    striped: true,
                    dblclick_edit: true,
                    on_click: undefined,
                    on_dblclick: undefined,
                    on_pagecount_update: undefined,
                    on_page_changed: undefined,
                    editable: false,
                    keypress_edit: true,
                    editable_fields: undefined,
                    selected_field: undefined,
                    append_on_lastrow_keydown: false,
                    sortable: false,
                    sort_fields: undefined,
                    sort_add_primary: false,
                    row_callback: undefined,
                    title_callback: undefined,
                    show_footer: undefined,
                    show_paginator: true,
                    paginator_container: undefined
                };

            this.item = item;
            if (!this.item.paginate) {
                default_options.striped = false;
            }
            this.id = item.task.gridId++;
            this.$container = container;
            this.options = $.extend({}, default_options, options);
            if (this.options.row_line_count < 1) {
                this.options.row_line_count = 1;
            }
            if (this.item.master) {
                this.options.select_all = false;
            }
            this.editMode = false;
            this._sorted_fields = [];
            this._multiple_sort = false;
            this.on_dblclick = this.options.on_dblclick;
            this.init_selections();
            this.page = 0;
            this.recordCount = 0;
            this.cellWidths = {};
            this.autoFieldWidth = true;
            this.fieldWidthUpdated = false;

            this.initFields();

            this.$element = $('<div class="dbtable ' + item.item_name + '" style="overflow-x:auto;"></div>');
            if (this.options.table_class) {
                this.$element.addClass(this.options.table_class);
            }
            this.$element.data('dbtable', this);
            this.item.controls.push(this);
            this.$element.bind('destroyed', function() {
                self.item.controls.splice(self.item.controls.indexOf(self), 1);
            });
            this.$container.empty();
            this.$element.appendTo(this.$container);
            this.createTable();
            if (item._get_active()) {
                setTimeout(function() {
                        self.init_table();
                    },
                    0
                );
            }
        },

        init_selections: function() {
            var value;
            if (this.options.selections && this.options.selections instanceof Array) {
                this.item.selections = this.options.selections;
            }
            if (this.item.lookup_field && this.item.lookup_field.multi_select) {
                value = this.item.lookup_field.raw_value;
                this.options.select_all = this.item.lookup_field.multi_select_all;
                if (value instanceof Array) {
                    this.item.selections = value;
                }
                else {
                    this.item.selections = [];
                }
            }
            this.item.select_all = this.options.select_all;
        },

        selections_update_selected: function() {
            var sel_count = this.$element.find('th .multi-select .sel-count');
            if (this.item.selections) {
                sel_count.text(this.item.selections.length);
                if (this.item.filter_selected) {
                    sel_count.addClass('selected-shown')
                }
                else {
                    sel_count.removeClass('selected-shown')
                }
                if (this.item.lookup_field && this.item.lookup_field.multi_select) {
                    if (this.item.selections.length === 1 && this.item._primary_key_field && this.item.selections.indexOf(this.item._primary_key_field.value) !== -1) {
                        this.item.lookup_field.set_value(this.item.selections, this.item.field_by_name(this.item.lookup_field.lookup_field).display_text);
                    }
                    else {
                        this.item.lookup_field.set_value(this.item.selections, '');
                    }
                }
            }
        },

        selections_get_selected: function() {
            return this.item.selections.indexOf(this.item._primary_key_field.value) !== -1;
        },

        selections_can_change: function(value) {
            var valid = true;
            if (value && this.options.selection_limit) {
                valid = (this.options.selection_limit &&
                    this.options.selection_limit >= this.item.selections.length + 1);
                if (!valid) {
                    this.item.warning(language.selection_limit_exceeded.replace('%s', this.options.selection_limit))
                }
            }
            return valid;
        },

        selections_set_selected: function(value) {
            var result = value,
                index,
                all_selected = false;
            if (this.selections_can_change(value)) {
                if (value) {
                    this.item.selections.push(this.item._primary_key_field.value);
                    all_selected = true;
                } else {
                    index = this.item.selections.indexOf(this.item._primary_key_field.value);
                    if (index !== -1) {
                        this.item.selections.splice(index, 1);
                        all_selected = this.selections_get_all_selected();
                    }
                }
                this.selections_update_selected();
                this.$element.find('input.multi-select-header').prop('checked', all_selected);
            }
            else {
                result = false;
            }
            return result;
        },

        selections_get_all_selected: function() {
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
        },

        selections_set_all_selected_ex: function(value) {
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
                    field = this.item.field_by_ID(copy._order_by_list[i][0]);
                    if (fields.indexOf(field.field_name) === -1) {
                        fields.push(field.field_name);
                    }
                }
                copy.open({fields: fields, limit: limit}, function() {
                    var dict = {};
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
                        self.item.selections.push(parseInt(id, 10));
                    }
                    self.$table.find('td input.multi-select').prop('checked', value);
                    self.$element.find('input.multi-select-header').prop('checked',
                        self.selections_get_all_selected());
                    self.selections_update_selected();
                })
            }
        },

        selections_set_all_selected: function(value) {
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
                        self.item.selections.push(c._primary_key_field.value);
                    } else {
                        index = self.item.selections.indexOf(c._primary_key_field.value);
                        if (index !== -1) {
                            self.item.selections.splice(index, 1);
                        }
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
        },

        initFields: function() {
            var i = 0,
                len,
                field,
                fields;
            this.fields = [];
            if (this.options.fields.length) {
                fields = this.options.fields
            } else {
                fields = this.item.view_options.fields;
            }
            if (fields.length) {
                len = fields.length;
                for (; i < len; i++) {
                    field = this.item.field_by_name(fields[i]);
                    if (field) {
                        this.fields.push(field);
                    }
                }
            }
            this.options.editable = this.options.editable && !this.item.read_only;
            if (this.options.editable) {
                this.options.striped = false;
            }
            this.editableFields = [];
            if (this.options.editable_fields) {
                len = this.options.editable_fields.length;
                for (i = 0; i < len; i++) {
                    field = this.item.field_by_name(this.options.editable_fields[i])
                    if (field && !field.read_only) {
                        this.editableFields.push(field);
                    }
                }
            } else {
                len = this.fields.length;
                for (i = 0; i < len; i++) {
                    if (!this.fields[i].read_only) {
                        this.editableFields.push(this.fields[i]);
                    }
                }
            }
            this.initSelectedField();
            this.colspan = this.fields.length;
            if (this.item.selections) {
                this.colspan += 1;
            }
        },

        initKeyboardEvents: function() {
            var self = this,
                timeOut;
            clearTimeout(timeOut);
            timeOut = setTimeout(function() {
                    self.$table.on('keydown', function(e) {
                        self.keydown(e);
                    });

                    self.$table.on('keyup', function(e) {
                        self.keyup(e);
                    });

                    self.$table.on('keypress', function(e) {
                        self.keypress(e);
                    });
                },
                400
            );
        },

        createTable: function() {
            var self = this,
                $doc = $(document),
                $selection,
                $th,
                $td,
                $thNext,
                delta = 0,
                mouseX;
            this.colspan = this.fields.length;
            if (this.item.selections) {
                this.colspan += 1;
            }
            this.$element.append($(
                '<table class="outer-table" style="width: 100%;">' +
                '   <thead>' +
                '       <tr><th>&nbsp</th></tr>' +
                '   </thead>' +
                '   <tfoot>' +
                '       <tr><th>&nbsp</th></tr>' +
                '   </tfoot>' +
                '   <tr>' +
                '       <td id="top-td" style="padding: 0; border: 0" colspan=' + this.colspan + '>' +
                '           <div class="overlay-div" style="height: 100px; width: 100%; overflow-y: auto; overflow-x: hidden;">' +
                '               <table class="inner-table" style="width: 100%"></table>' +
                '           </div>' +
                '       </td>' +
                '   </tr>' +
                '</table>'));

            this.$outer_table = this.$element.find("table.outer-table")
            this.$scroll_div = this.$element.find('div.overlay-div');
            this.$table = this.$element.find("table.inner-table");
            this.$head = this.$element.find("table.outer-table thead tr:first");
            this.$foot = this.$element.find("table.outer-table tfoot tr:first");

            this.$scroll_div.keydown(function(e) {
                var code = (e.keyCode ? e.keyCode : e.which);
                if (code == 32) {
                    e.preventDefault();
                }
            })

            this.$element.find('table.outer-table')
                .addClass("table table-condensed table-bordered")
                .css("margin", 0);

            this.$table.addClass("table table-condensed")
                .css("margin", 0)
                .attr("disabled", false);
            if (this.options.striped) {
                this.$table.addClass("table-striped");
            }

            this.$table.on('mousedown dblclick', 'td', function(e) {
                var td = this;
                if (this.nodeName !== 'TD') {
                    td = $(this).closest('td');
                }
                e.preventDefault();
                e.stopPropagation();
                self.clicked(e, td);
            });

            this.$element.on('mousewheel DOMMouseScroll', 'div.overlay-div, table.inner-table', function(e){
                if (e.originalEvent.wheelDelta > 0 || e.originalEvent.detail < 0) {
                    self.prior_record();
                }
                else {
                    self.next_record();
                }
                e.preventDefault();
                e.stopPropagation();
            });

            this.$table.on('click', 'td', function(e) {
                if (self.options.on_click) {
                    self.options.on_click.call(self.item, self.item);
                }
            });

            if (this.options.expand_selected_row && this.options.row_line_count !== this.options.expand_selected_row) {
                this.$table.on('mouseleave mousedown', 'td div', function() {
                    var $this = $(this),
                        tt = $this.data('tooltip');
                    if (tt && tt.$tip) {
                        tt.$tip.remove();
                    }
                });
            }

            this.$table.on('mouseenter mouseup', 'td div', function() {
                var $this = $(this),
                    tt = $this.data('tooltip');
                if (tt && tt.$tip) {
                    tt.$tip.remove();
                }
                if (Math.abs(this.offsetHeight - this.scrollHeight) > 1 ||
                    Math.abs(this.offsetWidth - this.scrollWidth) > 1) {
                    $this.tooltip({
                            'placement': 'right',
                            'title': $this.text()
                        })
                        .on('hide hidden show shown', function(e) { e.stopPropagation() })
                        .eq(0).tooltip('show');
                }
            });

            this.$table.on('mousedown', 'td input.multi-select', function(e) {
                var $this = $(this),
                    checked = $this.is(':checked');
                self.clicked(e, $this.closest('td'));
                self.selections_set_selected(!checked);
                $this.prop('checked', self.selections_get_selected());
            });

            this.$table.on('click', 'td input.multi-select', function(e) {
                var $this = $(this);
                e.stopPropagation();
                e.preventDefault();
                setTimeout(function() {
                        $this.prop('checked', self.selections_get_selected());
                    }, 0
                );
            });

            this.$element.on('click', 'input.multi-select-header', function(e) {
                self.selections_set_all_selected($(this).is(':checked'));
            });

            this.$table.attr("tabindex", this.options.tabindex);

            this.initKeyboardEvents();

            this.$element.on('mousemove.grid-title', 'table.outer-table thead tr:first th', function(e) {
                var $this = $(this),
                    field_name = $this.data('field_name'),
                    lastCell = self.$element.find("thead tr:first th:last").get(0);
                if ($this.outerWidth() - e.offsetX < 8 && !mouseX && this !== lastCell) {
                    $this.css('cursor', 'col-resize');
                } else if (self.options.sortable && //!self.item.master &&
                    (!self.options.sort_fields || self.options.sort_fields.indexOf(field_name) !== -1)) {
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
                    if (newDelta > -($th.innerWidth() - 30) && (!self.options.auto_fit_width || newDelta < ($thNext.innerWidth() - 30))) {
                        delta = newDelta;
                        $selection.css('left', left + e.screenX - mouseX);
                    }
                    mouseX = e.screenX;
                }
            }

            function changeFieldWidth($title, delta) {
                var field_name,
                    $td,
                    $tf,
                    oldCellWidth,
                    cellWidth;

                field_name = $title.data('field_name');
                $td = self.$table.find('td.' + field_name);
                $tf = self.$element.find("tfoot tr:first th." + field_name);
                oldCellWidth = self.getCellWidth(field_name);
                cellWidth = oldCellWidth + delta;

                $td.width(cellWidth);
                $td.find('div').width(cellWidth);
                $title.width(cellWidth);
                $title.find('div').width(cellWidth);
                $tf.width(cellWidth);
                $tf.find('div').width(cellWidth);

                self.syncColWidth();
                cellWidth = $title.width();
                self.setCellWidth(field_name, cellWidth);
                return cellWidth - oldCellWidth;
            }

            function releaseMouseMove(e) {
                var field_name,
                    $td,
                    $tf,
                    cellWidth;
                $doc.off("mousemove.grid-title");
                $doc.off("mouseup.grid-title");

                if (delta < 0) {
                    delta = changeFieldWidth($th, delta);
                    if (self.options.auto_fit_width) {
                        changeFieldWidth($thNext, -delta);
                    }
                } else {
                    if (self.options.auto_fit_width) {
                        delta = -changeFieldWidth($thNext, -delta);
                        changeFieldWidth($th, delta);
                    } else {
                        changeFieldWidth($th, delta);
                    }
                }

                mouseX = undefined;
                $selection.remove()
            }

            this.$element.on('mousedown.grid-title', 'table.outer-table thead tr:first th', function(e) {
                var $this = $(this),
                    index,
                    lastCell,
                    field_name = $this.data('field_name'),
                    cur_field_name,
                    field_ID,
                    new_fields = [],
                    index,
                    desc = false,
                    next_field_name,
                    field,
                    sorted_fields;
                lastCell = self.$element.find("thead tr:first th:last").get(0);
                if ($this.outerWidth() - e.offsetX < 8 && this !== lastCell) {
                    $this.css('cursor', 'default');
                    mouseX = e.screenX;
                    $th = $this;
                    index = self.fields.indexOf(self.item.field_by_name(field_name))
                    next_field_name = self.fields[index + 1].field_name
                    $thNext = self.$element.find("thead tr:first th." + next_field_name);
                    delta = 0;
                    $doc.on("mousemove.grid-title", captureMouseMove);
                    $doc.on("mouseup.grid-title", releaseMouseMove);
                    $selection = $('<div>')
                        .addClass('selection-box')
                        .css({
                            'width': 0,
                            'height': self.$outer_table.find('thead').innerHeight() + self.$scroll_div.innerHeight(),
                            'left': $this.position().left + $this.outerWidth(),
                            'top': self.$element.position().top
                        });
                    $selection.appendTo(self.$element);
                } else if (field_name && self.options.sortable &&
                    (!self.options.sort_fields || self.options.sort_fields.indexOf(field_name) !== -1)) {

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
                    field_ID = self.item.field_by_name(field_name).ID;
                    sorted_fields = self._sorted_fields.slice();
                    if (self._multiple_sort) {
                        index = -1;
                        for (var i = 0; i < sorted_fields.length; i++) {
                            if (sorted_fields[i][0] === field_ID) {
                                index = i;
                                break;
                            }
                        }
                        if (index === -1) {
                            sorted_fields.push([field_ID, false])
                        } else {
                            sorted_fields[index][1] = !sorted_fields[index][1];
                        }
                    } else {
                        if (sorted_fields.length && sorted_fields[0][0] === field_ID) {
                            sorted_fields[0][1] = !sorted_fields[0][1];
                        } else {
                            sorted_fields = [
                                [field_ID, false]
                            ];
                        }
                    }
                    self._sorted_fields = sorted_fields.slice();
                    if (self.item.master || !self.item.paginate) {
                        self.item._sort(self._sorted_fields);
                    } else {
                        if (self.options.sort_add_primary) {
                            field = self.item[self.item._primary_key]
                            desc = self._sorted_fields[self._sorted_fields.length - 1][1]
                            self._sorted_fields.push([field.ID, desc]);
                        }
                        self.item._open_params.__order = self._sorted_fields;
                        self.item.open({
                            params: self.item._open_params,
                            offset: 0
                        });
                    }
                }
            });

            this.$table.focus(function(e) {
                if (!this.syncronizing) {
                    this.syncronizing = true;
                    try {
                        self.syncronize();
                    } finally {
                        this.syncronizing = false;
                    }
                }
            });

            this.$table.blur(function(e) {
                self.syncronize();
            });

            this.createPager();
            this.createFooter();
            this.calculate();
        },

        calculate: function() {
            var i,
                $element,
                $table,
                row,
                $td,
                margin,
                fix,
                row_height,
                elementHeight,
                scrollDivHeight;
            $element = this.$element.clone()
                .css("float", "left")
                .css("position", "absolute")
                .css("top", -1000),
            $element.width(this.$container.width());
            this.fillTitle($element);
            this.createFooter($element);
            $table = $element.find("table.inner-table");
            if (this.item.selections && !this.item.master) {
                row = '<tr><td><div><input type="checkbox"></div></td><td><div>W</div></td></tr>';
            } else {
                row = '<tr><td><div>W</div></td></tr>';
            }
            for (i = 0; i < 10; i++) {
                $table.append(row);
            }
            $('body').append($element);
            $td = $table.find('tr:last td');
            this.textHeight = $td.find('div').height();
            row_height = $td.outerHeight(true);
            margin = row_height * 10 - $table.innerHeight();
            fix = Math.abs(Math.abs(margin) - 10); // fix for firebird
            if (fix && fix < 5 && margin < 0) {
                row_height += Math.round(fix);
                margin = row_height * 10 - $table.innerHeight();
            }
            this.row_height = row_height + (this.options.row_line_count - 1) * this.textHeight;
            this.selected_row_height = 0;
            elementHeight = $element.outerHeight();
            scrollDivHeight = $element.find('div.overlay-div').innerHeight();
            $element.remove();

            this.$scroll_div.height(this.options.height - (elementHeight - scrollDivHeight));

            if (this.item.paginate) {
                scrollDivHeight = this.$scroll_div.innerHeight() + margin;
                if (this.options.expand_selected_row) {
                    this.selected_row_height = row_height + (this.options.expand_selected_row - 1) * this.textHeight;
                    scrollDivHeight = this.$scroll_div.height() - this.selected_row_height + margin;
                }
                this.row_count = Math.floor(scrollDivHeight / this.row_height);
                if (this.options.expand_selected_row) {
                    this.row_count += 1;
                }
                if (this.row_count <= 0) {
                    this.row_count = 1;
                }
                this.item._limit = this.row_count;
            }
        },

        createPager: function($element) {
            var self = this,
                $pagination,
                $pager,
                tabindex,
                pagerWidth;
            if (this.item.paginate && this.options.show_paginator) {
                tabindex = -1;
                $pagination = $(
                    '<td class="pager" style="line-height: 0" colspan=' + this.colspan + '>' +
                    '   <div id="pager" style="margin: 0 auto">' +
                    '       <form class="form-inline" style="margin: 0">' +
                    '           <a class="btn btn-small" tabindex="-1" href="first"><i class="icon-backward"></i></a>' +
                    '           <a class="btn btn-small" tabindex="-1" href="prior"><i class="icon-chevron-left"></i></a>' +
                    '           <label  class="control-label" for="input-page" style="margin: 0px 4px">' + language.page + '</label>' +
                    '           <input class="pager-input input-mini" id="input-page" tabindex="' + tabindex + '" type="text">' +
                    '           <label id="page-count" class="control-label" for="input-page" style="margin: 0px 4px">' + language.of + '1000000 </label>' +
                    '           <a class="btn btn-small" tabindex="-1" href="next"><i class="icon-chevron-right"></i></a>' +
                    '           <a class="btn btn-small" tabindex="-1" href="last"><i class="icon-forward"></i></a>' +
                    '       </form>' +
                    '   </div>' +
                    '</td>');


                this.$fistPageBtn = $pagination.find('[href="first"]');
                this.$fistPageBtn.on("click", function(e) {
                    self.firstPage();
                    e.preventDefault();
                });
                this.$fistPageBtn.addClass("disabled");

                this.$priorPageBtn = $pagination.find('[href="prior"]');
                this.$priorPageBtn.on("click", function(e) {
                    self.priorPage();
                    e.preventDefault();
                });
                this.$priorPageBtn.addClass("disabled");

                this.$nextPageBtn = $pagination.find('[href="next"]');
                this.$nextPageBtn.on("click", function(e) {
                    self.nextPage();
                    e.preventDefault();
                });

                this.$lastPageBtn = $pagination.find('[href="last"]');
                this.$lastPageBtn.on("click", function(e) {
                    self.lastPage();
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
                            self.setPageNumber(page - 1);
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
                if (this.options.paginator_container) {
                    this.options.paginator_container.empty();
                    this.options.paginator_container.append($pagination);
                } else {
                    if ($element) {
                        $element.find('tfoot').append($pagination);
                    } else {
                        this.$element.find('tfoot').append($pagination);
                    }
                }
                this.$page_count.text(language.of + ' ');
                $pagination.find('#pager').width(pagerWidth);
            }
        },

        initSelectedField: function() {
            var field;
            if (!this.selectedField && this.editableFields.length) {
                this.selectedField = this.editableFields[0];
                if (this.options.selected_field) {
                    field = this.item.field_by_name(this.options.selected_field);
                    if (this.editableFields.indexOf(field) !== -1) {
                        this.selectedField = field;
                    }
                }
            }
        },

        setSelectedField: function(field) {
            var self = this,
                fieldChanged = this.selectedField !== field;
            if (this.editableFields.indexOf(field) !== -1) {
                if (fieldChanged && this.options.editable) {
                    this.flushEditor();
                    this.hideEditor();
                }
                this.hide_selection();
                this.selectedField = field
                if (fieldChanged && this.options.editable && this.editMode) {
                    clearTimeout(this.editorsTimeOut);
                    this.editorsTimeOut = setTimeout(function() {
                            self.showEditor();
                        },
                        75);
                    //~ this.showEditor();
                }
                this.show_selection();
            }
        },

        nextField: function() {
            var index;
            if (this.selectedField) {
                index = this.editableFields.indexOf(this.selectedField);
                if (index < this.editableFields.length - 1) {
                    this.setSelectedField(this.editableFields[index + 1]);
                }
            }
        },

        priorField: function() {
            var index;
            if (this.selectedField) {
                index = this.editableFields.indexOf(this.selectedField);
                if (index > 0) {
                    this.setSelectedField(this.editableFields[index - 1]);
                }
            }
        },

        hideEditor: function() {
            var width,
                field,
                $div,
                $td;
            $td;
            if (this.editing) {
                try {
                    this.editMode = false;
                    $td = this.editor.$controlGroup.parent();
                    field = this.editor.field
                    $div = $td.find('div.' + field.field_name);

                    width = $td.outerWidth();
                    $td.css("padding-left", this.editor.paddingLeft)
                    $td.css("padding-top", this.editor.paddingTop)
                    $td.css("padding-right", this.editor.paddingRight)
                    $td.css("padding-bottom", this.editor.paddingBottom)

                    this.editor.$controlGroup.remove();
                    this.editor.removed = true;
                    this.editor = undefined;

                    $td.outerWidth(width);

                    $div.show();
                } finally {
                    this.editing = false;
                }
                this.focus();
            }
        },

        flushEditor: function() {
            if (this.editor && this.editing) {
                this.editor.change_field_text();
            }
        },

        showEditor: function() {
            var width,
                editor,
                $div,
                $td,
                $row = this.itemRow();
            if ($row && !this.editing && this.selectedField && this.item.record_count()) {
                if (!this.item.is_changing()) {
                    this.item.edit();
                }
                this.editMode = true;
                this.editor = new DBTableInput(this, this.selectedField);
                this.editor.$controlGroup.find('.controls, .input-prepend, .input-append, input').css('margin-bottom', 0);
                this.editor.$controlGroup.css('margin-bottom', 0);

                $div = $row.find('div.' + this.editor.field.field_name);
                $div.hide();
                $td = $row.find('td.' + this.editor.field.field_name);

                this.editor.$input.css('font-size', $td.css('font-size'));

                width = $td.outerWidth();
                this.editor.paddingLeft = $td.css("padding-left");
                this.editor.paddingTop = $td.css("padding-top");
                this.editor.paddingRight = $td.css("padding-right");
                this.editor.paddingBottom = $td.css("padding-bottom");

                this.editor.padding = $td.css("padding");
                $td.css("padding", 0);
                $td.outerWidth(width);

                $td.append(this.editor.$controlGroup);

                width = 0;
                this.editor.$input.parent().children('*').each(function() {
                    width += $(this).outerWidth(true);
                });
                this.editor.$input.width(this.editor.$input.width() + this.editor.$controlGroup.width() - width);

                this.editor.update();

                if (this.is_focused()) {
                    this.editor.$input.focus();
                }
                this.editing = true;
            }
        },

        height: function(value) {
            if (value === undefined) {
                return this.$element.height();
            } else {
                this.$scroll_div.height(value - (this.$element.height() - this.$scroll_div.height()));
            }
        },

        fillTitle: function($element) {
            var i,
                len,
                self = this,
                field,
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
                shown_title,
                select_menu = '',
                cellWidth;
            if ($element === undefined) {
                $element = this.$element
            }

            len = this._sorted_fields.length;
            for (i = 0; i < len; i++) {
                try {
                    desc = this._sorted_fields[i][1];
                    field = this.item.field_by_ID(this._sorted_fields[i][0])
                    if (desc) {
                        order_fields[field.field_name] = 'icon-arrow-down';
                    } else {
                        order_fields[field.field_name] = 'icon-arrow-up';
                    }
                } catch (e) {}
            }

            heading = $element.find("table.outer-table thead tr:first");
            heading.empty();
            if (this.item.selections) {
                if (this.item.master) {
                    if (this.selections_get_all_selected()) {
                        checked = 'checked';
                    }
                    div = $('<div class="text-center multi-select" style="overflow: hidden"></div>');
                    sel_count = $('<p class="sel-count text-center">' + this.item.selections.length + '</p>')
                    div.append(sel_count);
                    input = $('<input class="multi-select-header" type="checkbox" ' + checked + '>');
                    div.append(input);
                    cell = $('<th class="bottom-border multi-select-header"></th>').append(div);
                    cellWidth = this.getCellWidth('multi-select');
                    if (cellWidth && this.fields.length) {
                        cell.width(cellWidth);
                        div.width(cellWidth);
                    }
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
                    if (self.item.filter_selected) {
                        shown_title = task.language.show_all
                    }
                    select_menu +=
                        '<li id="mshow-selected"><a tabindex="-1" href="#">' + shown_title + '</a></li>';
                    this.$element.find('#mselect-block').empty();
                    bl = $(
                        '<div style="height: 0; position: relative;">' +
                            '<div id="mselect-block" class="btn-group" style="position: absolute">' +
                                '<button type="button" class="btn mselect-btn">' +
                                    '<input class="multi-select-header" type="checkbox" style="margin: 0" ' + checked + '>' +
                                '</button>' +
                                '<a class="btn dropdown-toggle" data-toggle="dropdown" href="#" style="padding: 3px">' +
                                    '<span class="caret"></span>' +
                                '</a>' +
                                '<ul class="dropdown-menu">' +
                                    select_menu +
                                '</ul>' +
                            '</div>' +
                        '</div>'
                    );
                    input = bl.find('#mselect-block')
                    bl.find("#mselect-all").click(function(e) {
                        self.selections_set_all_selected_ex(true);
                    });
                    bl.find("#munselect-all").click(function(e) {
                        self.selections_set_all_selected_ex(false);
                    });
                    bl.find("#mshow-selected").click(function(e) {
                        self.item.filter_selected = !self.item.filter_selected;
                        self.item.open(function() {
                            self.selections_update_selected();
                        });
                    });
                    this.selection_block = bl;
                    this.$element.prepend(bl)
                    cell = $('<th class="bottom-border multi-select"></th>').append(div);
                    cellWidth = this.getCellWidth('multi-select');
                    if (cellWidth && this.fields.length) {
                        cell.width(cellWidth);
                        div.width(cellWidth);
                    }
                    heading.append(cell);
                    div.css('min-height', 46);
                    cell.css('padding-top', 0);
                    input.css('top', sel_count.outerHeight() + sel_count.position().top + 4);
                    input.css('left', (cell.outerWidth() - input.width()) / 2 + 1);
                }
            }
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                div = $('<div class="text-center ' + field.field_name +
                    '" style="overflow: hidden"><p>' + field.field_caption + '</p></div>');
                cell = $('<th class="' + field.field_name + '" data-field_name="' + field.field_name + '" bottom-border"></th>').append(div);
                if (!this.options.title_word_wrap) {
                    div.css('height', this.textHeight);
                    cell.css('height', this.textHeight);
                }
                cellWidth = this.getCellWidth(field.field_name);
                if (cellWidth && (i < this.fields.length - 1)) {
                    cell.width(cellWidth);
                    div.width(cellWidth);
                }
                if (order_fields[field.field_name]) {
                    cell.find('p').append('<i class="' + order_fields[field.field_name] + '"></i>');
                    cell.find('i').css('margin-left', 2)
                }
                heading.append(cell);
            }
            if (this.options.title_callback) {
                this.options.title_callback(heading, this.item)
            }
            this.selections_update_selected();
        },

        createFooter: function($element) {
            var i,
                len,
                field,
                footer,
                div,
                cell,
                cellWidth;
            if ($element === undefined) {
                $element = this.$element
            }
            footer = $element.find("table.outer-table tfoot tr:first");
            footer.empty();
            if (this.item.selections) {
                div = $('<div class="text-center multi-select" style="overflow: hidden"></div>')
                cell = $('<th class="multi-select"></th>').append(div);
                footer.append(cell);
            }
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                div = $('<div class="text-center ' + field.field_name +
                    '" style="overflow: hidden">&nbsp</div>');
                cell = $('<th class="' + field.field_name + '"></th>').append(div);
                footer.append(cell);
            }
            if (!this.options.show_footer) {
                footer.hide();
            }
        },

        show_footer: function() {
            this.$element.find("table.outer-table tfoot tr:first").show();
        },

        hideFooter: function() {
            this.$element.find("table.outer-table tfoot tr:first").hide();
        },

        getCellWidth: function(field_name) {
            return this.cellWidths[field_name];
        },

        setCellWidth: function(field_name, value) {
            this.cellWidths[field_name] = value;
        },

        init_table: function() {
            if (this.item._offset === 0) {
                this.initFields();
                this._sorted_fields = this.item._open_params.__order;
                if (this.item.paginate) {
                    this.page = 0;
                    this.updatePageInfo();
                    this.updatePageCount();
                } else {
                    this.fieldWidthUpdated = false;
                }
            }
            this.refresh();
        },

        form_closing: function() {
            var $modal = this.$element.closest('.modal');
            if ($modal) {
                return $modal.data('_closing')
            }
            return false;
        },

        update: function(state) {
            var recNo,
                self = this,
                row;
            if (this.form_closing()) {
                return;
            }
            switch (state) {
                case consts.UPDATE_OPEN:
                    this.init_table();
                    break;
                case consts.UPDATE_CANCEL:
                    this.refreshRow();
                    break;
                case consts.UPDATE_APPEND:
                    row = this.addNewRow();
                    this.$table.append(row);
                    this.syncronize();
                    this.syncColWidth();
                    if (this.item.controls_enabled() && this.item.record_count() === 1) {
                        this.build();
                    }
                    break;
                case consts.UPDATE_INSERT:
                    row = this.addNewRow();
                    this.$table.prepend(row);
                    this.syncronize();
                    this.syncColWidth();
                    break;
                case consts.UPDATE_DELETE:
                    this.deleteRow();
                    break;
                case consts.UPDATE_SCROLLED:
                    this.syncronize();
                    break;
                case consts.UPDATE_CONTROLS:
                    this.build();
                    break;
                case consts.UPDATE_CLOSE:
                    this.$table.empty();
                    break;
                case consts.UPDATE_REFRESH:
//                    this.build();
                    break;
            }
        },

        update_field: function(field, refreshingRow) {
            var self = this,
                row = this.itemRow(),
                update,
                build,
                text,
                div,
                span;
            if (this.item.active && this.item.controls_enabled() && this.item.record_count()) {
                div = row.find('div.' + field.field_name);
                if (div.length) {
                    span = div.find('span');
                    text = this.get_field_text(field);
                    if (text !== span.text()) {
                        span.text(text);
                        if (this.item.is_new() && this.item.record_count() < 10) {
                            update = true;
                        }
                        else if (this.$table.get(0).clientWidth > this.$scroll_div.innerWidth() ||
                            this.$table.get(0).clientWidth > this.$element.innerWidth()) {
                            update = true;
                        }
                        else if (this.$table.get(0).clientWidth > this.$scroll_div.innerWidth() ||
                            this.$table.get(0).clientWidth > this.$element.innerWidth()) {
                            update = true;
                        }
                        else if (this.$table.get(0).clientWidth > this.$scroll_div.innerWidth() ||
                            this.$table.get(0).clientWidth > this.$element.innerWidth()) {
                            update = true;
                        }
                        else if ((field.data_type === consts.INTEGER ||
                            field.data_type === consts.FLOAT ||
                            field.data_type === consts.CURRENCY) &&
                            Math.abs(div.get(0).offsetWidth - div.get(0).scrollWidth) > 1) {
                            update = true
                        }
                        if (update || build) {
                            clearTimeout(this._update_field_timeout);
                            this._update_field_timeout = setTimeout(
                                function() {
                                    if (self.item.record_count() <= 100) {
                                        self.build();
                                    } else {
                                        self.syncColWidth();
                                    }
                                },
                                0
                            )
                        }
                        if (!refreshingRow) {
                            this.update_selected(row);
                        }
                    }
                }
            }
        },

        syncColWidth: function() {
            var $row,
                field,
                $th,
                $td,
                i,
                width,
                len = this.fields.length;
            if (this.item.record_count()) {
                $row = this.$table.find("tr:first-child");
                if (this.item.selections) {
                    $th = this.$head.find('th.' + 'multi-select');
                    $td = $row.find('td.' + 'multi-select');
                    width = $th.find('div').width()
                    $th.find('div').width(width)
                    $td.find('div').width(width);
                    width = $th.width();
                    $th.width(width);
                    $td.width(width);
                }
                for (i = 0; i < len - 1; i++) {
                    field = this.fields[i];
                    $th = this.$head.find('th.' + field.field_name);
                    $td = $row.find('td.' + field.field_name);

                    width = $th.find('div').width()
                    $th.find('div').width(width)
                    $td.find('div').width(width);
                    width = $th.width();
                    $th.width(width);
                    $td.width(width);
                }
            }
        },

        update_selected: function(row) {
            if (!row) {
                row = this.itemRow();
            }
            if (this.options.row_callback) {
                this.options.row_callback(row, this.item);
            }
        },

        deleteRow: function() {
            var $row = this.itemRow();
            $row.remove();
            this.syncColWidth();
        },

        itemRow: function() {
            if (this.item.record_count()) {
                try {
                    var info = this.item.rec_controls_info(),
                        row = $(info[this.id]);
                    this.update_selected(row);
                    return row;
                } catch (e) {
                    console.log(e);
                }
            }
        },

        refreshRow: function() {
            var self = this;
            this.each_field(function(field, i) {
                self.update_field(field, true);
            });
        },

        do_on_edit: function(mouseClicked) {
            if (this.item.lookup_field) {
                this.item.set_lookup_field_value();
            } else if (!this.options.editable || (!this.editMode && mouseClicked)) {
                if (this.on_dblclick) {
                    this.on_dblclick.call(this.item, this.item);
                } else if (this.options.dblclick_edit) {
                    this.item.edit_record();
                }
            } else if (!this.editMode && !mouseClicked && this.options.editable) {
                this.showEditor();
            }
        },

        clicked: function(e, td) {
            var rec,
                field,
                $row = $(td).parent();
            if (this.options.editable) {
                this.setSelectedField(this.item.field_by_name($(td).data('field_name')));
            }
            rec = this.item._dataset.indexOf($row.data("record"));
            if (this.editMode && rec !== this.item.rec_no) {
                if (!this.item.is_edited()) {
                    this.item.edit();
                }
                this.flushEditor();
                this.item.post();
            }
            this.item._set_rec_no(rec);
            if (!this.editing && !this.is_focused()) {
                this.focus();
            }
            if (e.type === "dblclick") {
                this.do_on_edit(true);
            }
        },

        hide_selection: function() {
            if (this.selected_row) {
                if (this.options.editable && this.selectedField) {
                    this.selected_row.removeClass("selected-focused selected");
                    this.selected_row.find('td.' + this.selectedField.field_name)
                        .removeClass("field-selected-focused field-selected")
                } else {
                    this.selected_row.removeClass("selected-focused selected");
                }
            }
        },

        show_selection: function() {
            var selClassName = 'selected',
                selFieldClassName = 'field-selected';
            if (this.is_focused()) {
                selClassName = 'selected-focused';
                selFieldClassName = 'field-selected-focused';
            }
            if (this.selected_row) {
                if (this.options.editable && this.selectedField) {
                    this.selected_row.addClass(selClassName);
                    this.selected_row.find('td.' + this.selectedField.field_name)
                        .removeClass(selClassName)
                        .addClass(selFieldClassName);
                } else {
                    this.selected_row.addClass(selClassName);
                }
            }
        },

        select_row: function($row) {
            var divs,
                textHeight = this.textHeight,
                selClassName = 'selected';
            this.update_selected_row($row);
            if (this.is_focused()) {
                selClassName = 'selected-focused';
            }
            this.hide_selection();
            if (this.selected_row && this.options.expand_selected_row) {
                this.selected_row.find('tr, div').css('height', this.options.row_line_count * textHeight);
            }
            this.selected_row = $row;
            this.show_selection();
            if (this.options.expand_selected_row) {
                divs = this.selected_row.find('tr, div')
                divs.css('height', '');
                divs.css('height', this.options.expand_selected_row * textHeight);
            }
        },

        update_selected_row: function($row) {
            var containerTop,
                containerBottom,
                elemTop,
                elemBottom;
            if ($row.length) {
                containerTop = this.$scroll_div.scrollTop();
                containerBottom = containerTop + this.$scroll_div.height();
                elemTop = $row.get(0).offsetTop;
                elemBottom = elemTop + $row.height();
                if (elemTop < containerTop) {
                    this.$scroll_div.scrollTop(elemTop);
                } else if (elemBottom > containerBottom) {
                    this.$scroll_div.scrollTop(elemBottom - this.$scroll_div.height());
                }
            }
        },

        syncronize: function() {
            var self = this,
                rowChanged,
                $row;
            if (this.item.controls_enabled() && this.item.record_count() > 0) {
                $row = this.itemRow();
                rowChanged = !this.selected_row || (this.selected_row && $row && this.selected_row.get(0) !== $row.get(0));
                if (rowChanged && this.options.editable) {
                    this.hideEditor();
                }
                try {
                    this.select_row(this.itemRow());
                } catch (e) {}

                if (rowChanged && this.options.editable && this.editMode) {
                    clearTimeout(this.editorsTimeOut);
                    this.editorsTimeOut = setTimeout(function() {
                            self.showEditor();
                        },
                        75);
                    //~ this.showEditor();
                }
            }
        },

        get_field_text: function(field) {
            return field.get_lookup_data_type() === consts.BOOLEAN ? field.get_lookup_value() ? '×' : '' :
                field.get_display_text();
        },

        next_record: function() {
            this.item.next();
            if (this.item.eof()) {
                if (this.options.editable && this.options.append_on_lastrow_keydown) {
                    this.item.append();
                } else {
                    this.nextPage();
                }
            }
        },

        prior_record: function() {
            var self = this;
            this.item.prior();
            if (this.item.bof()) {
                this.priorPage(function() {
                    self.item.last();
                });
            }
        },

        keydown: function(e) {
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
                        e.preventDefault();
                        this.flushEditor();
                        this.hideEditor();
                        if (code === 33) {
                            this.priorPage();
                        } else if (code === 34) {
                            if (this.item.paginate && this.item.is_loaded) {
                                this.item.last();
                            } else {
                                this.nextPage();
                            }
                        } else if (code === 38) {
                            this.prior_record();
                        } else if (code === 40) {
                            this.next_record();
                        } else if (code === 36) {
                            this.firstPage();
                        } else if (code === 35) {
                            this.lastPage();
                        }
                        break;
                    case 37:
                        if (this.options.editable && !this.editMode) {
                            this.priorField();
                        }
                        break;
                    case 39:
                        if (this.options.editable && !this.editMode) {
                            this.nextField();
                        }
                        break;
                }
            }
        },

        keyup: function(e) {
            var self = this,
                multi_sel,
                code = (e.keyCode ? e.keyCode : e.which);
            if (e.target === this.$table.get(0) && !e.ctrlKey && !e.shiftKey) {
                switch (code) {
                    case 13:
                        e.preventDefault();
                        this.do_on_edit(false);
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
                        if (this.item.selections) {
                            multi_sel = this.itemRow().find('input.multi-select');
                            this.selections_set_selected(!multi_sel[0].checked);
                            multi_sel.prop('checked', this.selections_get_selected());
                        }
                        break
                }
            }
        },

        keypress: function(e) {
            var self = this,
                multi_sel,
                code = e.which;
            if (code > 32 && this.options.editable && this.options.keypress_edit && !this.editMode) {
                if (this.selectedField && this.selectedField.valid_char_code(code)) {
                    this.showEditor();
                }
            }
        },

        setPageNumber: function(value, callback) {
            var self = this;

            if (!this.item.paginate || this.loading) {
                return;
            }
            if (value < this.page_count || value === 0) {
                this.page = value;
                this.loading = true;
                this.item.open({
                    offset: this.page * this.item._limit
                }, function() {
                    if (callback) {
                        callback.call(self);
                    }
                    self.loading = false;
                    self.updatePageInfo();
                });
            }
        },

        reload: function(callback) {
            if (this.item.paginate) {
                this.setPageNumber(this.page, callback);
            } else {
                this.open(callback);
            }
        },

        updatePageInfo: function() {
            if (this.options.show_paginator) {
                this.$pageInput.val(this.page + 1);
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
            if (this.options.on_page_changed) {
                this.options.on_page_changed.call(this.item, this.item, this);
            }
        },

        updatePageCount: function(callback) {
            var self = this;
            this.item.total_records(function(count) {
                self.recordCount = count;
                self.page_count = Math.ceil(count / self.row_count);
                if (self.$page_count) {
                    self.$page_count.text(language.of + ' ' + self.page_count);
                }
                if (self.options.on_pagecount_update) {
                    self.options.on_pagecount_update.call(self.item, self.item, self);
                }
                if (self.options.on_page_changed) {
                    self.options.on_page_changed.call(self.item, self.item, self);
                }
            });
        },

        firstPage: function(callback) {
            if (this.item.paginate) {
                this.setPageNumber(0, callback);
            } else {
                this.item.first();
            }
        },

        nextPage: function(callback) {
            var lines,
                clone;
            if (this.item.paginate) {
                if (!this.item.is_loaded) {
                    this.setPageNumber(this.page + 1, callback);
                }
            } else {
                clone = this.item.clone();
                clone._set_rec_no(this.item._get_rec_no())
                lines = this.$scroll_div.innerHeight() / this.row_height - 1;
                for (var i = 0; i < lines; i++) {
                    if (!clone.eof()) {
                        clone.next();
                    } else {
                        break;
                    }
                }
                this.item._set_rec_no(clone._get_rec_no());
            }
        },

        priorPage: function(callback) {
            var lines,
                clone;
            if (this.item.paginate) {
                if (this.page > 0) {
                    this.setPageNumber(this.page - 1, callback);
                } else {
                    this.syncronize();
                }
            } else {
                clone = this.item.clone();
                clone._set_rec_no(this.item._get_rec_no());
                lines = this.$scroll_div.innerHeight() / this.row_height - 1;
                for (var i = 0; i < lines; i++) {
                    if (!clone.eof()) {
                        clone.prior();
                    } else {
                        break;
                    }
                }
                this.item._set_rec_no(clone._get_rec_no());
            }
        },

        lastPage: function(callback) {
            var self = this;
            if (this.item.paginate) {
                this.item.total_records(function(count) {
                    self.recordCount = count;
                    self.page_count = Math.ceil(count / self.row_count);
                    if (self.options.show_paginator) {
                        self.$page_count.text(language.of + ' ' + self.page_count);
                    }
                    self.setPageNumber(self.page_count - 1, callback);
                    if (self.options.on_pagecount_update) {
                        self.options.on_pagecount_update.call(this.item, this.item, this);
                    }
                });
            } else {
                this.item.last();
            }
        },

        each_field: function(callback) {
            var i = 0,
                len = this.fields.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.fields[i], this.fields[i], i);
                if (value === false) {
                    break;
                }
            }
        },

        addNewRow: function() {
            var $row = $(this.newRow()),
                rec = this.item._get_rec_no(),
                info;
            $row.data("record", this.item._dataset[rec]);
            info = this.item.rec_controls_info();
            info[this.id] = $row.get();
            if (this.options.row_callback) {
                this.options.row_callback($row, this.item);
            }
            return $row;
        },

        newColumn: function(columnName, align, text, index, setFieldWidth) {
            var cellWidth = this.getCellWidth(columnName),
                classStr = 'class="' + columnName + '"',
                dataStr = 'data-field_name="' + columnName + '"',
                tdStyleStr = 'style="text-align:' + align + ';overflow: hidden' + '"',
                divStyleStr = 'style="overflow: hidden';
            if (this.textHeight) {
                divStyleStr += '; height: ' + this.options.row_line_count * this.textHeight + 'px';
            }
            if (setFieldWidth && cellWidth && (index < this.fields.length - 1)) {
                divStyleStr += '; width: ' + cellWidth + 'px';
            }
            divStyleStr += '"';
            return '<td ' + classStr + ' ' + dataStr + ' ' + tdStyleStr + '>' +
                '<div ' + classStr + ' ' + divStyleStr + '>' +
                '<span ' + divStyleStr + '>' + text +
                '</span>' +
                '</div>' +
                '</td>';
        },

        newRow: function() {
            var f,
                i,
                len,
                field,
                align,
                text,
                rowStr,
                checked = '',
                setFieldWidth = !this.autoFieldWidth ||
                (this.autoFieldWidth && this.fieldWidthUpdated);
            len = this.fields.length;
            rowStr = '';
            if (this.item.selections) {
                if (this.selections_get_selected()) {
                    checked = 'checked';
                }
                rowStr += this.newColumn('multi-select', 'center', '<input class="multi-select" type="checkbox" ' + checked + '>', -1, setFieldWidth);
            }
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                f = this.item[field.field_name];
                if (!(f instanceof Field)) {
                    f = this.item.field_by_name(field.field_name);
                }
                text = this.get_field_text(f);
                align = f.data_type === consts.BOOLEAN ? 'center' : alignValue[f.alignment]
                rowStr += this.newColumn(f.field_name, align, text, i, setFieldWidth);
            }
            return '<tr class="inner">' + rowStr + '</tr>';
        },

        getElementWidth: function(element) {
            if (!element.length) {
                return 0;
            }
            if (element.is(':visible')) {
                return element.width()
            } else {
                return this.getElementWidth(element.parent())
            }
        },

        refresh: function(callback) {
            var i,
                len,
                field,
                row, tmpRow,
                cell,
                cellWidth,
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
                editable_val,
                clone = this.item.clone(),
                container = $('<div>');

            is_focused = this.is_focused();
            if (this.options.editable && this.editMode && this.editor) {
                if (!is_focused) {
                    is_focused = this.editor.$input.is(':focus');
                }
                editable_val = this.editor.$input.value;
                this.hideEditor();
            }

            container.css("position", "absolute")
                .css("top", -1000)
                .width(this.getElementWidth(this.$element));
            $('body').append(container);
            this.$element.detach();
            container.append(this.$element);

            this.$table.empty();
            this.$head.empty();
            if (this.selection_block) {
                this.selection_block.remove();
            }
            this.$foot.hide();
            this.$outer_table.find('#top-td').attr('colspan', this.colspan);

            clone.on_field_get_text = this.item.on_field_get_text;
            rows = ''
            item_rec_no = this.item.rec_no;
            try {
                while (!clone.eof()) {
                    this.item._cur_row = clone._cur_row;
                    rows += this.newRow();
                    rec_nos.push(clone._get_rec_no());
                    clone.next();
                }
                this.$table.html(rows);
                rows = this.$table.find("tr");
                len = rows.length;
                for (i = 0; i < len; i++) {
                    row = rows.eq(i);
                    rec = rec_nos[i]
                    clone._set_rec_no(rec);
                    this.item._cur_row = rec;
                    row.data("record", clone._dataset[rec]);
                    info = clone.rec_controls_info();
                    info[this.id] = row.get();
                    if (this.options.row_callback) {
                        this.options.row_callback(row, this.item);
                    }
                }
            } finally {
                this.item._cur_row = item_rec_no;
            }
            row = this.$table.find("tr:first");
            if (this.autoFieldWidth && !this.fieldWidthUpdated) {
                this.$table.css('table-layout', 'auto');
                this.$outer_table.css('table-layout', 'auto');
                tmpRow = '<tr>'
                if (this.item.selections) {
                    tmpRow = tmpRow + '<th class="multi-select">' +
                        '<div class="text-center multi-select" style="overflow: hidden"></div>' +
                        '</th>';
                }
                len = this.fields.length;
                for (i = 0; i < len; i++) {
                    tmpRow = tmpRow + '<th class="' + this.fields[i].field_name + '" ><div style="overflow: hidden">' +
                        this.fields[i].field_caption + '</div></th>';
                }
                tmpRow = $(tmpRow + '</tr>');
                this.$table.prepend(tmpRow);
                for (var field_name in this.options.column_width) {
                    if (this.options.column_width.hasOwnProperty(field_name)) {
                        tmpRow.find("." + field_name).css("width", this.options.column_width[field_name]);
                    }
                }
                if (this.item.selections) {
                    cell = row.find("td." + 'multi-select');
                    this.setCellWidth('multi-select', 38);
                }
                for (i = 0; i < len; i++) {
                    field = this.fields[i];
                    cell = row.find("td." + field.field_name);
                    this.setCellWidth(field.field_name, cell.width());
                }
                this.$table.css('table-layout', 'fixed');
                this.$outer_table.css('table-layout', 'fixed');
                this.fillTitle(container);
                if (this.item.selections) {
                    cell = row.find("td." + 'multi-select');
                    headCell = this.$head.find("th." + 'multi-select');
                    footCell = this.$foot.find("th." + 'multi-select');
                    cellWidth = this.getCellWidth('multi-select');
                    cell.find('div').width(cellWidth);
                    cell.width(cellWidth);
                    headCell.find('div').width(cellWidth);
                    headCell.width(cellWidth);
                    footCell.find('div').width(cellWidth);
                    footCell.width(cellWidth);
                }
                for (i = 0; i < len; i++) {
                    field = this.fields[i];
                    if (i < this.fields.length - 1) {
                        cell = row.find("td." + field.field_name);
                        headCell = this.$head.find("th." + field.field_name);
                        footCell = this.$foot.find("th." + field.field_name);
                        cellWidth = this.getCellWidth(field.field_name);
                        cell.find('div').width(cellWidth);
                        cell.width(cellWidth);
                        headCell.find('div').width(cellWidth);
                        headCell.width(cellWidth);
                        footCell.find('div').width(cellWidth);
                        footCell.width(cellWidth);
                    }
                }
                if (this.item.record_count() > 0 && is_visible) {
                    this.fieldWidthUpdated = true;
                }
                tmpRow.remove();
            } else {
                this.fillTitle(container);
                this.syncColWidth();
            }

            if (this.options.show_footer) {
                this.$foot.show();
            }
            this.$element.detach();
            this.$container.append(this.$element);

            container.remove();

            this.syncronize();
            if (is_focused) {
                this.focus();
            }
            if (this.options.editable && this.editMode && this.editor) {
                this.showEditor();
                this.editor.$input.value = editable_val;
            }
            if (callback) {
                callback.call(this);
            }
        },

        build: function() {
            var scroll_top = this.$scroll_div.scrollTop();
            this.initFields();
            this.fieldWidthUpdated = false;
            this.refresh();
            this.syncColWidth();
            this.$scroll_div.scrollTop(scroll_top);
            this.syncronize();
        },

        is_focused: function() {
            return this.$table.get(0) === document.activeElement;
        },

        focus: function() {
            if (!this.is_focused()) {
                this.$table.focus();
            }
        }
    };

    /**********************************************************************/
    /*                      DBAbstractInput class                         */
    /**********************************************************************/

    function DBAbstractInput(field) {
        var self = this;
        this.field = field;
        this.read_only = false;
        this.is_changing = true;
    }

    DBAbstractInput.prototype = {
        constructor: DBAbstractInput,

        create_input: function(field, tabIndex, container) {
            var self = this,
                align,
                height,
                width,
                $controlGroup,
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
                field_type;
            if (!field) {
                return;
            }
            if (this.label) {
                $label = $('<label class="control-label"></label>')
                    .attr("for", field.field_name).text(this.label).
                addClass(field.field_name);
                if (this.label_width) {
                    $label.width(this.label_width);
                }
            }
            if (field.get_lookup_data_type() === consts.BOOLEAN) {
                $input = $('<input>')
                    .attr("id", field.field_name)
                    .attr("type", "checkbox")
                    .attr("tabindex", tabIndex + "")
                    .click(function(e) {
                        self.field.value = !self.field.value;
                    });
            } else if (field.get_lookup_data_type() === consts.BLOB) {
                $input = $('<textarea>')
                    .attr("id", field.field_name)
                    .attr("tabindex", tabIndex + "")
                    .innerHeight(70);
            } else {
                $input = $('<input>')
                    .attr("id", field.field_name)
                    .attr("type", "text")
                    .attr("tabindex", tabIndex + "");
            }
            $controls = $('<div class="controls"></div>');
            if (this.controls_margin_left) {
                $controls.css('margin-left', this.controls_margin_left);
            }
            this.$input = $input;
            this.$input.addClass(field.field_name)
            this.$input.addClass('dbinput')
            this.$input.data('dbinput', this);
            this.$input.focus(function(e) {
                self.focusIn(e);
            });
            this.$input.blur(function(e) {
                self.focusOut();
            });
            this.$input.mousedown(function(e) {
                self.mouseIsDown = true;
            });
            this.$input.mouseup(function(e) {
                if (!self.mouseIsDown) {
                    self.$input.select();
                }
                self.mouseIsDown = false;
            });

            this.$input.keydown($.proxy(this.keydown, this));
            this.$input.keyup($.proxy(this.keyup, this));
            this.$input.keypress($.proxy(this.keypress, this));
            if (field.lookup_item && !field.master_field || field.lookup_values) {
                $btnCtrls = $('<div class="input-prepend input-append"></div>').addClass("input-with-buttons");
                $btn = $('<button class="btn input-button" type="button"><i class="icon-remove-sign"></button>');
                $btn.attr("tabindex", -1);
                $btn.click(function() {
                    field.set_value(null);
                });
                this.$firstBtn = $btn;
                $btnCtrls.append($btn);
                $btnCtrls.append($input);
                $btn = $('<button class="btn input-button" type="button"><i></button>');
                $btn.attr("tabindex", -1);
                $btn.click(function() {
                    if (field.lookup_values) {
                        self.dropdown.enter_pressed();
                    }
                    else {
                        self.selectValue();
                    }
                });
                this.$lastBtn = $btn;
                $btnCtrls.append($btn);
                $controls.append($btnCtrls);
                if (field.lookup_values) {
                    $input.addClass("input-lookupvalues");
                    this.$lastBtn.find('i').addClass("icon-chevron-down");
                    this.dropdown = new DropdownList(this.field, $input);
                }
                else {
                    $input.addClass("input-lookupitem");
                    this.$lastBtn.find('i').addClass("icon-folder-open");
                    if (this.field.enable_typeahead) {
                        this.dropdown = new DropdownTypeahead(this.field,
                            $input, this.field.typeahead_options());
                    }
                }
            } else {
                field_type = field.get_lookup_data_type();
                switch (field_type) {
                    case consts.TEXT:
                        $input.addClass("input-text");
                        $controls.append($input);
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
                        $btnCtrls = $('<div class="input-prepend input-append"></div>').addClass("input-with-buttons");
                        $btn = $('<button class="btn input-button" type="button"><i class="icon-remove-sign"></button>');
                        $btn.attr("tabindex", -1);
                        $btn.click(function() {
                            field.set_value(null);
                        });
                        this.$firstBtn = $btn;
                        $btnCtrls.append($btn);
                        $input.addClass("input-date");
                        if (field_type === consts.DATETIME) {
                            $input.addClass("input-datetime");
                        }
                        $btnCtrls.append($input);
                        $btn = $('<button class="btn input-button" type="button"><i class="icon-calendar"></button>');
                        $btn.attr("tabindex", -1);
                        $btn.click(function() {
                            self.showDatePicker();
                        });
                        this.$lastBtn = $btn;
                        $btnCtrls.append($btn);
                        $controls.append($btnCtrls);
                        break;
                    case consts.BOOLEAN:
                        $controls.append($input);
                        break;
                    case consts.BLOB:
                        $input.addClass("input-text");
                        $controls.append($input);
                        break;
                }
                align = field.data_type === consts.BOOLEAN ? 'center' : alignValue[field.alignment];
                this.$input.css("text-align", align);
            }
            if (this.label_on_top) {
                this.$controlGroup = $('<div class="input-container"></div>');
            } else {
                this.$controlGroup = $('<div class="control-group input-container"></div>');
            }
            if (this.label) {
                this.$controlGroup.append($label);
            }
            this.$controlGroup.append($controls);

            if (container) {
                container.append(this.$controlGroup);
            }

            this.$modalForm = this.$input.closest('.modal');
            this.field.controls.push(this);

            this.$input.on('mouseenter', function() {
                var $this = $(this);
                if (self.error) {
                    $this.tooltip('show');
                }
            });

            if (!this.grid && this.field.field_placeholder) {
                this.$input.attr('placeholder', this.field.field_placeholder);
            }

            if (!this.grid && this.field.field_help) {
                $help = $('<span class="badge help-badge">?</span>');

                $help.click(function() {
                    var deleted = false,
                        $title = $('<div><b>' + self.field.field_caption + '</b>' +
                        '<button type="button" id="close-btn" class="close" tabindex="-1" aria-hidden="true" style="padding: 0px 10px;"> ×</button></div>');
                        $title.find("#close-btn").click(function() {
                        $input.popover('destroy');
                        deleted = true;
                    });
                    $input.popover({
                        container: 'body',
                        placement: 'right',
                        html: true,
                        title: $title,
                        content: self.field.field_help
                    });
                    $input.popover('show');
                    setTimeout(
                        function() {
                            if (!deleted) {
                                $input.popover('destroy');
                            }
                        },
                        10 * 1000
                    );
                })
                if ($btnCtrls) {
                    $btnCtrls.append($help);
                }
                else {
                    $controls.append($help);
                }
            }
            this.$input.tooltip({
                    placement: 'bottom',
                    title: ''
                })
                .on('hide hidden show shown', function(e) { e.stopPropagation() });

            this.$input.bind('destroyed', function() {
                self.field.controls.splice(self.field.controls.indexOf(self), 1);
                if (!self.grid && self.field.field_help) {
                    if ($input.data('popover')) {
                        $input.data('popover').$tip.remove();
                    }
                }
                if (self.dropdown){
                    self.dropdown.destroy();
                }
            });

            this.update();
        },

        form_closing: function() {
            if (this.$modalForm) {
                return this.$modalForm.data('_closing')
            }
            return false;
        },

        set_read_only: function(value) {
            if (this.$firstBtn) {
                this.$firstBtn.prop('disabled', value);
            }
            if (this.$lastBtn) {
                this.$lastBtn.prop('disabled', value);
            }
            if (this.$input) {
                this.$input.prop('disabled', value);
            }
        },

        update: function() {
            var placeholder = this.field.field_placeholder,
                focused = this.$input.get(0) === document.activeElement,
                is_changing = this.is_changing;

            if (this.field.field_kind === consts.ITEM_FIELD) {
                is_changing = this.field.owner.is_changing();
                if (this.field.owner.record_count() === 0) {
                    this.read_only = true;
                    this.is_changing = false;
                    this.set_read_only(true);
                    return
                }
            }
            if (!this.removed && !this.form_closing()) {
                if (this.read_only !== this.field._get_read_only() || is_changing !== this.is_changing) {
                    this.read_only = this.field._get_read_only();
                    this.is_changing = is_changing;
                    this.set_read_only(this.read_only || !this.is_changing);
                }
                if (this.field.master_field) {
                    this.set_read_only(true);
                }
                if (this.field.get_lookup_data_type() === consts.BOOLEAN) {
                    if (this.field.get_lookup_value()) {
                        this.$input.prop("checked", true);
                    } else {
                        this.$input.prop("checked", false);
                    }
                }
                if (this.field.lookup_values) {
                    this.$input.val(this.field.display_text);
                } else {
                    if (focused && this.$input.val() !== this.field.get_text() ||
                        !focused && this.$input.val() !== this.field.get_display_text()) {
                        this.errorValue = undefined;
                        this.error = undefined;
                        if (focused && !this.field.lookup_item && !this.field.lookup_values) {
                            this.$input.val(this.field.get_text());
                        } else {
                            this.$input.val(this.field.get_display_text());
                        }
                    }
                }
                if (this.read_only || !this.is_changing || this.field.master_field) {
                    placeholder = '';
                }
                this.$input.attr('placeholder', placeholder);
                this.updateState(true);
            }
        },

        keydown: function(e) {
            var code = (e.keyCode ? e.keyCode : e.which);
            if (this.field.lookup_item && !this.field.enable_typeahead && !(code === 229 || code === 9 || code == 8)) {
                e.preventDefault();
            }
            if (e.ctrlKey === true) {
                if (code !== 67 && code !== 86 && code !== 88 && code != 90 &&
                    code != 8 && code != 37 && code != 39) { // Ctrl-V , C, X, Z, backspace, left arrow, right arrow
                    e.preventDefault();
                }
            }
            if (code === 9) {
                if (this.grid && this.grid.editMode) {
                    e.preventDefault();
                    if (e.shiftKey) {
                        this.grid.priorField();
                    } else {
                        this.grid.nextField();
                    }
                }
            }
        },

        keyup: function(e) {
            var typeahead,
                code = (e.keyCode ? e.keyCode : e.which);
            if (this.field.enable_typeahead) {
                typeahead = this.$input.data('jamtypeahead')
                if (typeahead && typeahead.shown) {
                    return;
                }
            }
            if (code === 13 && !e.ctrlKey && !e.shiftKey) {
                if (this.grid && this.grid.editMode) {
                    e.stopPropagation();
                    e.preventDefault();
                    if (!this.grid.item.is_changing()) {
                        this.grid.item.edit();
                    }
                    this.grid.flushEditor();
                    this.grid.hideEditor();
                    if (this.grid.item.is_changing()) {
                        this.grid.item.post();
                    }
                } else if (this.field.lookup_item && !this.field.enable_typeahead) {
                    e.stopPropagation();
                    e.preventDefault();
                    this.selectValue();
                } else if ((this.field.data_type === consts.DATE) || (this.field.data_type === consts.DATETIME)) {
                    e.stopPropagation();
                    e.preventDefault();
                    this.showDatePicker();
                }
            } else if (code === 27) {
                if (this.grid && this.grid.editMode) {
                    e.stopPropagation();
                    e.preventDefault();
                    this.grid.item.cancel();
                    this.grid.hideEditor();
                } else if (this.field.lookup_values) {
                    if (this.$input.parent().hasClass('open')) {
                        this.$input.parent().removeClass('open');
                        e.stopPropagation();
                    }
                }
            }
        },

        keypress: function(e) {
            var code = e.which;
            if (this.field.lookup_item && !this.field.enable_typeahead) {
                e.preventDefault();
            }
            if (this.$input.is('select')) {} else if (code && !this.field.valid_char_code(code)) {
                e.preventDefault();
            }
        },

        showDatePicker: function() {
            var self = this,
                format;

            if (this.field.data_type === consts.DATE) {
                format = settings.D_FMT;
            } else if (this.field.data_type === consts.DATETIME) {
                format = settings.D_T_FMT;
            }

            this.$input.datepicker({
                    weekStart: parseInt(language.week_start, 10),
                    format: format,
                    daysMin: language.days_min,
                    months: language.months,
                    monthsShort: language.months_short,
                    date: this.field.value
                })
                .on('show', function(e) {
                    e.stopPropagation();
                    self.$input.datepicker().attr('data-weekStart', 1);
                })
                .on('hide hidden shown', function(e) { e.stopPropagation() })
                .on('changeDate', function(e) {
                    self.field.set_value(e.date);
                    self.$input.datepicker('hide');
                });
            this.$input.datepicker('show');
        },

        selectValue: function() {
            if (this.field.on_entry_button_click) {
                this.field.on_entry_button_click.call(this.item, this.field);
            } else {
                this.field.select_value();
            }
        },

        change_field_text: function() {
            var result = true,
                text;
            if (this.field.owner && this.field.owner.is_changing &&
                !this.field.owner.is_changing()) {
                this.field.owner.edit();
            }
            this.errorValue = undefined;
            this.error = undefined;
            if (this.field.lookup_item) {
                if (this.$input.val() !== this.field.get_lookup_text()) {
                    this.$input.val(this.field.get_display_text());
                }
            } else {
                try {
                    text = this.$input.val();
                    if (text === '') {
                        this.field.set_value(null);
                    } else {
                        this.field.set_text(text);
                        this.field.check_valid();
                        if (this.$input.is(':visible')) {
                            this.$input.val(text);
                        }
                    }
                } catch (e) {
                    this.errorValue = text;
                    this.error = e;
                    this.updateState(false);
                    if (this.field && this.field.owner && this.field.owner.task.settings.DEBUGGING) {
                        throw 'change_field_text error: ' + e
                    }
                    result = false;
                }
            }
            return result;
        },

        focusIn: function(e) {
            this.hideError();
            if (this.field.lookup_item && !this.field.enable_typeahead) {
                this.$input.val(this.field.get_display_text());
            } else {
                if (this.errorValue) {
                    this.$input.val(this.errorValue);
                } else if (this.field.lookup_item || this.field.lookup_values) {
                    this.$input.val(this.field.get_display_text());
                } else {
                    this.$input.val(this.field.get_text());
                }
                if (!this.mouseIsDown) {
                    this.$input.select();
                    this.mouseIsDown = false;
                }
            }
            this.mouseIsDown = false;
        },

        focusOut: function(e) {
            var result = false;

            if (this.grid && this.grid.editMode) {
                if (this.grid.item.is_changing()) {
                    this.grid.flushEditor();
                    this.grid.item.post();
                }
            }
            if (this.field.data_type === consts.BOOLEAN) {
                result = true;
            } else if (this.field.lookup_values) {
                if (this.$input.parent().hasClass('open')) {
                    this.$input.parent().removeClass('open');
                }
                result = true;
            } else if (this.change_field_text()) {
                if (this.$input.is(':visible')) {
                    this.$input.val(this.field.get_display_text());
                }
                result = true;
            }
            this.updateState(result);
            return result;
        },

        updateState: function(value) {
            if (value) {
                if (this.$controlGroup) {
                    this.$controlGroup.removeClass('error');
                }
                this.errorValue = undefined;
                this.error = undefined;
                this.$input.tooltip('hide')
                    .attr('data-original-title', '')
                    .tooltip('fixTitle');
                this.hideError();
            } else {
                this.showError();
                if (this.$controlGroup) {
                    this.$controlGroup.addClass('error');
                }
                this.$input.tooltip('hide')
                    .attr('data-original-title', this.error)
                    .tooltip('fixTitle');
            }
        },

        showError: function(value) {},

        hideError: function(value) {},

        focus: function() {
            this.$input.focus();
        }

    };

    /**********************************************************************/
    /*                        DBTableInput class                           */
    /**********************************************************************/

    DBTableInput.prototype = new DBAbstractInput();
    DBTableInput.prototype.constructor = DBTableInput;

    function DBTableInput(grid, field) {
        DBAbstractInput.call(this, field);
        this.grid = grid;
        this.create_input(field, 0);
        this.$input.attr("autocomplete", "off");
        this.$input.addClass('dbtableinput');
    }

    $.extend(DBTableInput.prototype, {

    });

    /**********************************************************************/
    /*                           DBInput class                            */
    /**********************************************************************/

    DBInput.prototype = new DBAbstractInput();
    DBInput.prototype.constructor = DBInput;

    function DBInput(field, index, container, label_on_top,
        controls_margin_left, label_width, label) {
        DBAbstractInput.call(this, field);
        if (this.field.owner && this.field.owner.edit_form &&
            this.field.owner.edit_form.hasClass("modal")) {
            this.$edit_form = this.field.owner.edit_form;
        }
        this.label = label;
        this.controls_margin_left = controls_margin_left;
        this.label_width = label_width;
        this.label_on_top = label_on_top
        if (!this.label) {
            this.label = this.field.field_caption;
        }
        this.create_input(field, index, container);
    }

    $.extend(DBInput.prototype, {

        showError: function(value) {
            if (this.$edit_form && this.$edit_form.hasClass("normal-modal-border")) {
                this.$edit_form.removeClass("nomal-modal-border");
                this.$edit_form.addClass("error-modal-border");
            }
        },

        hideError: function(value) {
            if (this.$edit_form && this.$edit_form.hasClass("error-modal-border")) {
                this.$edit_form.removeClass("error-modal-border");
                this.$edit_form.addClass("nomal-modal-border");
            }
        },
    });

    /**********************************************************************/
    /*                           Dropdown class                           */
    /**********************************************************************/

    function Dropdown(field, element, options) {
        this.$element = element;
        this.field = field;
        this.options = options;
    }

    Dropdown.prototype = {
        constructor: Dropdown,

        init: function() {
            var default_options =
                {
                    menu: '<ul class="typeahead dropdown-menu"></ul>',
                    item: '<li><a href="#"></a></li>',
                    length: 10,
                    min_length: 1
                }
            this.options = $.extend({}, default_options, this.options);
            this.$menu = $(this.options.menu);
        },

        show: function() {
            var pos = $.extend({}, this.$element.offset(), {
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
            return this
        },

        hide: function() {
            this.$menu.hide();
            this.$menu.detach();
            this.shown = false;
            return this;
        },

        destroy: function() {
            this.$element = undefined;
            this.$menu.remove();
        },

        get_items: function(event) {
            var items;
            if (this.$element) {
                this.query = this.$element.val()
                if (!this.query || this.query.length < this.min_length) {
                    return this.shown ? this.hide() : this
                }
                items = $.isFunction(this.source) ? this.source(this.query, $.proxy(this.process, this)) : this.source
                return items ? this.process(items) : this
            }
        },

        lookup: function(event) {
            this.get_items(event);
        },

        process: function(items) {
            var that = this

            items = $.grep(items, function(item) {
                return that.matcher(item)
            })

            if (!items.length) {
                return this.shown ? this.hide() : this
            }

            return this.render(items.slice(0, this.length)).show()
        },

        matcher: function(item) {
            return true
        },

        highlighter: function(item) {
            var i = 0,
                query,
                result = item,
                strings;
            if (this.query) {
                strings = this.query.split(' ')
                for ( i = 0; i < strings.length; i++) {
                    query = strings[i];
                    if (query.indexOf('strong>') === -1 && query.length) {
                        query = query.replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, '\\$&')
                        result = result.replace(new RegExp('(' + query + ')', 'ig'), function($1, match) {
                            return '<strong>' + match + '</strong>'
                        })
                    }
                }
            }
            return result
        },

        render: function(items) {
            var that = this

            items = $(items).map(function(i, values) {
                i = $(that.options.item).data('id-value', values[0]);
                i.find('a').html(that.highlighter(values[1]))
                return i[0]
            })

            items.first().addClass('active')
            this.$menu.html(items)
            return this
        },

        next: function(event) {
            var active = this.$menu.find('.active').removeClass('active'),
                next = active.next()

            if (!next.length) {
                next = $(this.$menu.find('li')[0])
            }

            next.addClass('active')
        },

        prev: function(event) {
            var active = this.$menu.find('.active').removeClass('active'),
                prev = active.prev()

            if (!prev.length) {
                prev = this.$menu.find('li').last()
            }

            prev.addClass('active')
        },

        listen: function() {
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
        },

        eventSupported: function(eventName) {
            var isSupported = eventName in this.$element
            if (!isSupported) {
                this.$element.setAttribute(eventName, 'return;')
                isSupported = typeof this.$element[eventName] === 'function'
            }
            return isSupported
        },

        move: function(e) {
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
        },

        keydown: function(e) {
            this.suppressKeyPressRepeat = ~$.inArray(e.keyCode, [40, 38, 9, 13, 27])
            this.move(e)
        },

        keypress: function(e) {
            if (this.suppressKeyPressRepeat) return
            this.move(e)
        },

        keyup: function(e) {
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
                            if (e.keyCode === 13) {
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
                e.stopPropagation()
                e.preventDefault()
            }
        },

        focus: function(e) {
            this.focused = true
        },

        blur: function(e) {
            this.focused = false
            if (!this.mousedover && this.shown) this.hide()
        },

        click: function(e) {
            e.stopPropagation()
            e.preventDefault()
            this.select()
            this.$element.focus()
        },

        mouseenter: function(e) {
            this.mousedover = true
            this.$menu.find('.active').removeClass('active')
            $(e.currentTarget).addClass('active')
        },

        mouseleave: function(e) {
            this.mousedover = false
            if (!this.focused && this.shown) this.hide()
        }
    }

    /**********************************************************************/
    /*                        DropdownList class                          */
    /**********************************************************************/

    DropdownList.prototype = new Dropdown();
    DropdownList.prototype.constructor = DropdownList;

    function DropdownList(field, element, options) {
        Dropdown.call(this, field, element, options);
        this.init();
        this.source = this.field.lookup_values;
        this.options.length = this.source.length;
        this.listen();
    }

    $.extend(DropdownList.prototype, {

        matcher: function(item) {
            if (this.query) {
                return ~item[1].toLowerCase().indexOf(this.query.toLowerCase());
            }
            else {
                return true;
            }
        },

        select: function() {
            var $li = this.$menu.find('.active');
            this.field.value = $li.data('id-value');
            return this.hide();
        },

        enter_pressed: function() {
            this.query = '';
            this.$element.focus();
            this.process(this.source);
        }

    });

    /**********************************************************************/
    /*                     DropdownTypeahead class                        */
    /**********************************************************************/

    DropdownTypeahead.prototype = new Dropdown();
    DropdownTypeahead.prototype.constructor = DropdownTypeahead;

    function DropdownTypeahead(field, element, options) {
        Dropdown.call(this, field, element, options);
        this.init();
        this.source = this.options.source;
        this.lookup_item = this.options.lookup_item;
        this.listen();
    }

    $.extend(DropdownTypeahead.prototype, {

        lookup: function(event) {
            var self = this;
            clearTimeout(this.timeOut);
            this.timeOut = setTimeout(function() { self.get_items(event) }, 400);
        },

        select: function() {
            var $li = this.$menu.find('.active'),
                id_value = $li.data('id-value');
            this.lookup_item.locate('id', id_value);
            this.lookup_item.set_lookup_field_value();
            return this.hide();
        },

        enter_pressed: function() {
            this.field.select_value();
        }

    });

///////////////////////////////////////////////////////////////////////////

    $.event.special.destroyed = {
        remove: function(o) {
            if (o.handler) {
                o.handler();
            }
        }
    };

    window.task = new Task();
    window.task.events = {}
    window.task.constructors = {
        task: Task,
        group: Group,
        item: Item,
        detail: Detail
    };

})(jQuery);
