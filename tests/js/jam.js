
(function(window, undefined) {
    "use strict";

    var $ = window.$,
        settings,
        language,
        consts = {
            "RESPONSE": 1,
            "NOT_LOGGED": 2,
            "UNDER_MAINTAINANCE": 3,

            "TEXT": 1,
            "INTEGER": 2,
            "FLOAT": 3,
            "CURRENCY": 4,
            "DATE": 5,
            "DATETIME": 6,
            "BOOLEAN": 7,
            "BLOB": 8,

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
            "FILTER_SEARCH": 15,

            "ALIGN_LEFT": 1,
            "ALIGN_CENTER": 2,
            "ALIGN_RIGHT": 3,

            "STATE_NONE": 0,
            "STATE_BROWSE": 1,
            "STATE_INSERT": 2,
            "STATE_EDIT": 3,
            "STATE_DELETE": 4,

            "RECORD_UNCHANGED": null,
            "RECORD_INSERTED": 1,
            "RECORD_MODIFIED": 2,
            "RECORD_DETAILS_MODIFIED": 3,
            "RECORD_DELETED": 4,

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
            "UPDATE_CLOSE": 8
        },
        alignValue = ['', 'left', 'center', 'right'],
        filterValue = ['eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in', 'not_in',
            'range', 'isnull', 'exact', 'contains', 'startwith', 'endwith',
            'search'
        ];


    /**********************************************************************/
    /*                        AbsrtactItem class                          */
    /**********************************************************************/

    function AbsrtactItem(owner, ID, item_name, caption, visible, type) {
        if (visible === undefined) {
            visible = true;
        }
        this.owner = owner;
        this.item_name = item_name || '';
        this.item_caption = caption || '';
        this.visible = visible;
        this.ID = ID || undefined;
        this.item_type_id = type;
        this.item_type = "";
        if (type) {
            this.item_type = this.types[type - 1];
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

    AbsrtactItem.prototype = {
        constructor: AbsrtactItem,

        types: ["root", "users", "roles", "tasks", 'task',
            "catalogs", "journals", "tables", "reports",
            "catalog", "journal", "table", "report", "detail"
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

        eachItem: function(callback) {
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

        addChild: function(ID, item_name, caption, visible, type) {
            var NewClass;
            if (this.getChildClass) {
                NewClass = this.getChildClass();
                if (NewClass) {
                    return new NewClass(this, ID, item_name, caption, visible, type);
                }
            }
        },

        send_request: function(request, params, callback) {
            return this.task.process_request(request, this, params, callback);
        },

        init: function(info) {
            var i = 0,
                items = info[5],
                child,
                len = items.length,
                item_info;
            for (; i < len; i++) {
                item_info = items[i][1];
                child = this.addChild(item_info[0], item_info[1],
                    item_info[2], item_info[3], item_info[4]);
                if (child.initAttr) {
                    child.initAttr(item_info);
                }
                child.init(item_info);
            }
        },

        bindItems: function() {
            var i = 0,
                len = this.items.length;
            if (this.bindItem) {
                this.bindItem();
            }
            for (; i < len; i++) {
                this.items[i].bindItems();
            }
        },

        bindEvents: function() {
            var i = 0,
                len = this.items.length,
                events = window.task_events['events' + this.ID];

            this._events = [];
            for (var event in events) {
                if (events.hasOwnProperty(event)) {
                    this[event] = events[event];
                    this._events.push([event, events[event]]);
                }
            }
            for (; i < len; i++) {
                this.items[i].bindEvents();
            }
        },

        can_view: function() {
            return this.task.has_privilege(this, 'can_view');
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

        findTemplate: function(suffix) {
            var result,
                template,
                name,
                item = this;
            while (true) {
                name = item.item_name;
                if (item.item_type === "detail") {
                    name = item.owner.item_name + "-" + item.item_name;
                }
                template = this.task.templates.find("." + name + "-" + suffix);
                if (template.length) {
                    break;
                }
                item = item.owner;
                if (item === item.task) {
                    break;
                }
            }
            if (template) {
                result = template.clone();
            }
            return result;
        },

        server_function: function(func_name, params, callback) {
            if (!params) {
                params = [];
            }
            return this.send_request(func_name, params, callback);
        },

        makeFormModal: function(form, options) {
            var self = this,
                $doc,
                $form,
                $title,
                printCaption = '',
                print_button = '',
                mouseX,
                mouseY,
                fade = 'fade',
                closeCaption = '',
                defaultOptions = {
                    title: this.item_caption,
                    transition: false,
                    closeCaption: true,
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
            if (language && options.closeCaption) {
                closeCaption = '&nbsp;' + language.close + ' - [Esc]</small>';
            }
            if (language && options.print) {
                printCaption = '&nbsp;' + language.print + ' - [Ctrl-P]</small>',
                print_button = '<button type="button" id="print-btn" class="close" tabindex="-1" aria-hidden="true" style="padding: 0px 10px;">' + printCaption + '</button>'
            }
            if (!options.transition) {
                fade = ''
            }
            $form = $(
                '<div class="modal hide ' + fade + ' normal-modal-border" tabindex="-1" data-backdrop="static" data-item="' + this.item_name + '">' +
                    '<div class="modal-header">' +
                        '<button type="button" id="close-btn" class="close" tabindex="-1" aria-hidden="true" style="padding: 0px 10px;">' + closeCaption + ' ×</button>' +
                        print_button +
                        '<h4 class="modal-title">' + options.title + '</h4>' +
                    '</div>' +
                '</div>'
            );
            $doc = $(document);
            $form.find('#close-btn').css('cursor', 'default');
            $form.find('#print-btn')
                .css('cursor', 'default')
                .click(function(e) {
                    self.print_message($form.find(".modal-body").clone());
                });
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
            $form.isModal = true;
            return $form;
        },

        create_form: function(formName, options) {
            //~ container, form, beforeShow,
            //~ onShown, onHide, onHidden, onKeyDown, onKeyUp
            var self = this,
                keySuffix = formName + '.' + this.item_name;
            if (this[formName]) {
                this[formName].tabindex = 1;
                if (options.container) {
                    $(window).on("keyup." + keySuffix, function(e) {
                        e.stopPropagation();
                        if (options.onKeyUp) {
                            options.onKeyUp.call(self, e);
                        }
                    });
                    $(window).on("keydown." + keySuffix, function(e) {
                        e.stopPropagation();
                        if (options.onKeyDown) {
                            options.onKeyDown.call(self, e);
                        }
                    });
                    options.container.append(this[formName]);
                    if (options.beforeShow) {
                        options.beforeShow.call(this);
                    }
                    if (options.onShown) {
                        options.onShown.call(this);
                    }
                } else {
                    if (options.beforeShow) {
                        options.beforeShow.call(this);
                    }
                    if (this[formName].hasClass("modal")) {
                        this[formName].find("#close-btn").click(function(e) {
                            self.close_form(formName);
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
                                self[formName].data('closing', false)
                            }
                        });

                        this[formName].on("hidden", function(e) {
                            e.stopPropagation();
                            if (options.onHidden) {
                                options.onHidden.call(self, e);
                            }
                            self[formName] = undefined;
                        });

                        this[formName].on("keydown." + keySuffix, function(e) {
                            e.stopPropagation();
                            if (options.onKeyDown) {
                                options.onKeyDown.call(self, e);
                            }
                        });

                        this[formName].on("keyup." + keySuffix, function(e) {
                            e.stopPropagation();
                            if (options.onKeyUp) {
                                options.onKeyUp.call(self, e);
                            }
                        });
                        this[formName].find('.modal-title').html(this[formName].title);
                        this[formName].modal({
                            width: this[formName].modal_width,
                            height: this[formName].modal_height
                        });
                    }
                }
            }
        },

        close_form: function(formName) {
            var self = this,
                keySuffix = formName + '.' + this.item_name,
                timeOut;
            if (this[formName]) {
                this[formName].data('closing', true);
                if (this[formName].isModal) {
                    clearTimeout(timeOut);
                    timeOut = setTimeout(function() {
                        var form = self[formName];
                            if (form) {
                                form.modal('hide');
                            }
                        },
                        100
                    );
                } else {
                    $(window).off("keydown." + keySuffix);
                    $(window).off("keyup." + keySuffix);
                    this[formName].remove();
                    this[formName] = undefined;
                }
            }
        },

        show_edit_form: function(form_name, options) {
            var self = this,
                keyup = options.onKeyUp;
            options.onKeyUp = function(e) {
                if (keyup) {
                    keyup.call(self, e);
                }
                var datepicker,
                    code = (e.keyCode ? e.keyCode : e.which);
                if (self[form_name]) {
                    datepicker = self[form_name].find('.datepicker')
                    if (datepicker.length && datepicker.is(':visible') && code === 27 && !e.ctrlKey && !e.shiftKey) {
                        e.stopImmediatePropagation();
                        e.preventDefault();
                        datepicker.hide();
                    }
                }
            }
            this.create_form(form_name, options);
        },

        print_message: function(html) {
            var win = window.frames["dummy"];
            win.document.write('<body onload="window.print()">' + html.html() + '</body>');
            win.document.close();
        },

        message: function(mess, options) {
            var tab = 1,
                self = this,
                default_options = {
                    buttons: undefined,
                    title: '',
                    width: 400,
                    height: undefined,
                    margin: undefined,
                    print: false,
                    text_center: false,
                    button_min_width: 100,
                    center_buttons: false
                },
                buttons,
                key,
                el = '',
                $element,
                $modal_body,
                $button = $('<button type="button" class="btn">OK</button>'),
                timeOut;

            options = $.extend({}, default_options, options);
            buttons = options.buttons;

            el = '<div class="modal-body"></div>';
            if (!this.isEmptyObj(buttons)) {
                el += '<div class="modal-footer"></div>'
            }

            $element = this.makeFormModal($(el), options)

            $modal_body = $element.find('.modal-body');

            if (options.margin) {
                $modal_body.css('margin', options.margin);
            }

            $modal_body.html(mess)

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
                        $button.clone().attr("id", key).attr("tabindex", tab).html(key));
                    tab++;
                }
            }

            $element.on("shown", function(e) {
                e.stopPropagation();
                $element.find(".modal-footer").find('button.btn').each(function() {
                    if ($(this).outerWidth() < options.button_min_width) {
                        $(this).outerWidth(options.button_min_width);
                    }
                });
            });

            $element.on("hide", function(e) {
                e.stopPropagation();
            });

            $element.on("hidden", function(e) {
                e.stopPropagation();
            });

            //~ $element.on("keyup keydown", function(e) {
                //~ var code = (e.keyCode ? e.keyCode : e.which);
            //~ });

            $element.on("click", ".btn", function(e) {
                var button;
                e.preventDefault();
                e.stopImmediatePropagation();
                for (var key in buttons) {
                    if (buttons.hasOwnProperty(key)) {
                        if ($(e.target).attr("id") === key) {
                            if (buttons[key]) {
                                button = buttons[key];
                            }
                            clearTimeout(timeOut);
                            timeOut = setTimeout(function() {
                                    if (button) {
                                        button.call(self);
                                    }
                                    $element.modal('hide');
                                },
                                100);
                        }
                    }
                }
            });

            $element.modal({width: options.width, height: options.height});
            return $element;
        },

        question: function(mess, yesCallback, noCallback) {
            var buttons = {};
            buttons[language.yes] = yesCallback;
            buttons[language.no] = noCallback;
            this.message(mess, {buttons: buttons, margin: "20px 20px", text_center: true, center_buttons: true});
        },

        warning: function(mess, callback) {
            var buttons = {"OK": callback};
            this.message(mess, {buttons: buttons, margin: "20px 20px", text_center: true, center_buttons: true});
        },

        information: function(mess, options) {
            return this.message(mess, options);
        },

        show_message: function(mess, options) {
            return this.message(mess, options);
        },

        hide_message: function($element) {
            $element.modal('hide');
        },

        yesNoCancel: function(mess, yesCallback, noCallback, cancelCallback) {
            var buttons = {};
            buttons[language.yes] = yesCallback;
            buttons[language.no] = noCallback;
            buttons[language.cancel] = cancelCallback;
            this.message(mess, {buttons: buttons, margin: "20px 20px", text_center: true, width: 500, center_buttons: true});
        },

        isEmptyObj: function(obj) {
            for (var prop in obj) {
                if (obj.hasOwnProperty(prop))
                    return false;
            }
            return true;
        },

        emptyFunc: function() {},

        abort: function() {
            throw 'abort';
        }
    };

    /**********************************************************************/
    /*                             Task class                             */
    /**********************************************************************/

    Task.prototype = new AbsrtactItem();

    function Task(item_name, caption) {
        AbsrtactItem.call(this, undefined, 0, item_name, caption, true);
        this.task = this;
        this.user_info = {};
        this.gridId = 0;
        this.status = [];
        this.statusID = 0;
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

            function repeat_request() {
                return self.process_request(request, item, params, callback);
            }

            if (callback) {
                async = true;
            }
            if (this.ajaxStatusCode) {
                statusCode = this.ajaxStatusCode;
            }

            $.ajax({
                url: "/api",
                type: "POST",
                contentType: contentType,
                async: async,
                cache: false,
                data: ('1' + JSON.stringify({
                    'method': 'send_request',
                    'params': [request, this.user_id, this.ID, item.ID, params, date]
                })),
                statusCode: statusCode,
                success: function(data) {
                    var mess;
                    if (data.error) {
                        item.warning(item.item_name + ' error: ' + data.error)
                    }
                    else {
                        if (data.result.status === consts.UNDER_MAINTAINANCE) {
                            if (language) {
                                mess = language.website_maintenance;
                            } else {
                                mess = 'Web site currently under maintenance.';
                            }
                            item.warning(mess)
                            return
                        }
                        if (data.result.status === consts.NOT_LOGGED) {
//                            self.login(repeat_request);
                            self.login();
                            return
                        }
                        if (callback) {
                            callback.call(item, data.result.data);
                        } else {
                            reply = data.result.data;
                        }
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    if (language) {
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
            for (var i=str.length-1; i>=0; i--) {
                var code = str.charCodeAt(i);
                if (code > 0x7f && code <= 0x7ff) s++;
                else if (code > 0x7ff && code <= 0xffff) s+=2;
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
                xhr = new XMLHttpRequest();
            header += file_info.length + div_chr;
            header += this._byteLength(path) + div_chr;
            for (i = 0; i < file_info.length; i++) {
                file = file_info[i][0];
                content = file_info[i][1];
                header += this._byteLength(file.name) + div_chr;
                header += content.byteLength  + div_chr;
                files.push(file.name);
            }
            body.push(header);
            body.push(path);
            for (i = 0; i < file_info.length; i++) {
                file = file_info[i][0];
                content = file_info[i][1];
                body.push(file.name);
                body.push(content)
            }
            xhr.open('POST', '/upload', true);
            if (options.callback) {
                xhr.onload = function(e) {
                    if (options.multiple) {
                        options.callback.call(self, self, files)
                    }
                    else {
                        options.callback.call(self, self, files[0]);
                    }
                };
            }
            if (options.on_progress) {
                xhr.upload.onprogress = function(e) {
                    options.on_progress.call(self, self, e);
                }
            }
            var blob = new Blob(body, {type: 'application/octet-stream'});
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
                    counter = 0,
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
                    reader.onload = (function (cur_file) {
                        return function (e) {
                            file_info.push([cur_file, e.target.result])
                            if (file_info.length === file_list.length) {
                                self.do_upload(path, file_info, options);
                            }
                        };
                    })(file);
                    reader.readAsArrayBuffer(file);
                }
                button.remove();
            })
            button.click();
        },

        load: function(callback) {
            var logingInfo,
                self = this,
                info;
            if (!this.user_id) {
                this.user_id = this.readCookie('user_id');
            }
            this.send_request('init_client', null, function(info) {
                var templates;
                settings = info.settings;
                language = info.language;
                self.settings = info.settings;
                self.language = info.language;
                self.user_info = info.user_info;
                self.user_privileges = info.privileges;
                self.consts = consts;
                self.safe_mode = self.settings.SAFE_MODE;
                self.ID = info.task[0];
                self.item_name = info.task[1];
                self.item_caption = info.task[2];
                self.visible = info.task[3];
                self.item_type = "";
                if (info.task[4]) {
                    self.item_type = self.types[info.task[4] - 1];
                }
                self.task = self;
                self.init(info.task);
                self.bindItems();
                self.bindEvents();
                self.templates = $("<div></div>");
                templates = $(".templates");
                self.templates = templates.clone();
                templates.remove();
                if (self.on_before_show_main_form) {
                    self.on_before_show_main_form.call(self, self);
                }
                if (callback) {
                    callback.call(self);
                }
            });
        },

        login: function(callback) {
            var self = this,
                info,
                $form;
            if (this.on_login) {
                info = this.on_login.call(this, this);
                this.do_login(info, callback);
            } else {
                if (this.templates) {
                    $form = this.templates.find("#login-form").clone();
                } else {
                    $form = $("#login-form").clone();
                }

                $form = this.makeFormModal($form, {
                    title: $form.data('caption'),
                    transition: false
                })

                $form.find("#login-btn").click(function(e) {
                    var login = $form.find("#inputLoging").val(),
                        passWord = $form.find("#inputPassword").val(),
                        pswHash = hex_md5(passWord);
                    self.user_id = self.send_request('login', [login, pswHash]);
                    self.createCookie('user_id', self.user_id, 0.5);
                    if (self.user_id) {
                        if ($form) {
                            $form.modal('hide');
                        }
                        location.reload();
                        //~ if (callback) {
                            //~ callback.call(self);
                        //~ }
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
                            $form.find('#login-btn').focus()
                        }
                    }
                });

                $form.modal({
                    width: 500
                });
            }
        },

        logout: function(callback) {
            if (this.user_id) {
                this.send_request('logout', this.user_id);
                this.user_id = null;
                this.eraseCookie('user_id');
                location.reload();
            }
        },

        has_privilege: function(item, priv_name) {
            var priv_dic;
            if (item.task.item_name === "admin") {
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

        createCookie: function(name, value, days) {
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

        readCookie: function(name) {
            var nameEQ = escape(name) + "=";
            var ca = document.cookie.split(';');
            for (var i = 0; i < ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) === ' ') c = c.substring(1, c.length);
                if (c.indexOf(nameEQ) === 0) return unescape(c.substring(nameEQ.length, c.length));
            }
            return null;
        },

        eraseCookie: function(name) {
            this.createCookie(name, "", -1);
        }
    });


    /**********************************************************************/
    /*                           Group class                              */
    /**********************************************************************/

    Group.prototype = new AbsrtactItem();
    Group.prototype.constructor = Group;

    function Group(owner, ID, item_name, caption, visible, type) {
        AbsrtactItem.call(this, owner, ID, item_name, caption, visible, type);
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
            this._change_id += 1
            return this._change_id + ''
        },

        isEmptyObj: function(obj) {
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
            if (this.log_changes()) {
                if (this.item.master) {
                    record_log = this.item.master.change_log.find_record_log();
                    if (record_log) {
                        details = record_log['details'];
                        detail = details[this.item.ID];
                        if (this.isEmptyObj(detail)) {
                            len = this.item.fields.length;
                            for (i = 0; i < len; i++) {
                                fields.push(this.item.fields[i].field_name);
                                //~ if (!this.item.fields[i].master_field) {
                                    //~ fields.push(this.item.fields[i].field_name);
                                //~ }
                            }
                            detail = {
                                'logs': {},
                                'records': this.item._records,
                                'fields': fields,
                                'expanded': this.item.expanded
                            };
                            details[this.item.ID] = detail;
                        }
                        this.logs = detail['logs'];
                        this.records = detail['records'];
                        this.fields = detail['fields'];
                        this.expanded = detail['expanded'];
                    }
                }
                if (this.item.record_count()) {
                    change_id = this.item.get_rec_change_id();
                    if (!change_id) {
                        change_id = this.get_change_id()
                        this.item.set_rec_change_id(change_id);
                    }
                    result = this.logs[change_id]
                    if (this.isEmptyObj(result)) {
                        result = {
                            'unmodified_record': null,
                            'record': this.cur_record(),
                            'details': {}
                        }
                        this.logs[change_id] = result;
                    }
                }
                return result;
            }
        },

        get_detail_log: function(detail_ID) {
            var result = {'records': [], 'fields': [], 'expanded': false},
                record_log,
                details;
            if (this.log_changes()) {
                record_log = this.find_record_log();
                details = record_log['details'];
                if (!this.isEmptyObj(details)) {
                    result = details[detail_ID];
                }
                return result
            }
        },

        remove_record_log: function() {
            var change_id = this.item.get_rec_change_id();
            if (change_id) {
                this.find_record_log();
                delete this.logs[change_id];
                this.item.set_rec_change_id(null);
                this.item.set_record_status(consts.RECORD_UNCHANGED);
            }
        },

        cur_record: function() {
            return this.item._records[this.item.get_rec_no()];
        },

        record_modified: function(record_log) {
            var modified = false,
                old_rec = record_log['unmodified_record'],
                cur_rec = record_log['record'];
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

        log_change: function() {
            var record_log;
            if (this.log_changes()) {
                record_log = this.find_record_log();
                if (this.item.item_state === consts.STATE_BROWSE) {
                    if (this.item.get_record_status() === consts.RECORD_UNCHANGED) {
                        record_log['unmodified_record'] = this.copy_record(this.cur_record(), false);
                        return;
                    }
                } else if (this.item.item_state === consts.STATE_INSERT) {
                    this.item.set_record_status(consts.RECORD_INSERTED);
                } else if (this.item.item_state === consts.STATE_EDIT) {
                    if (this.item.get_record_status() === consts.RECORD_UNCHANGED) {
                        this.item.record_status = consts.RECORD_MODIFIED
                    } else if (this.item.get_record_status() === consts.RECORD_DETAILS_MODIFIED) {
                        if (this.record_modified(record_log)) {
                            this.item.set_record_status(consts.RECORD_MODIFIED);
                        }
                    }
                } else if (this.item.item_state === consts.STATE_DELETE) {
                    if (this.item.get_record_status() === consts.RECORD_INSERTED) {
                        this.remove_record_log();
                    } else {
                        this.item.set_record_status(consts.RECORD_DELETED);
                    }
                } else {
                    throw this.item.item_name + ': change log invalid records state';
                }
                if (this.item.master) {
                    if (this.item.master.get_record_status() === consts.RECORD_UNCHANGED) {
                        this.item.master.set_record_status(consts.RECORD_DETAILS_MODIFIED);
                    }
                }
            }
        },

        get_changes: function(result) {
            var data = {},
                record_log,
                record,
                info,
                new_record,
                new_details,
                detail_id,
                detail,
                details,
                new_detail,
                detail_item;
            result['fields'] = this.fields;
            result['expanded'] = false;
            result['data'] = data;
            for (var key in this.logs) {
                if (this.logs.hasOwnProperty(key)) {
                    record_log = this.logs[key];
                    record = record_log['record'];
                    info = this.item.get_rec_info(undefined, record);
                    if (info[consts.REC_STATUS] !== consts.RECORD_UNCHANGED) {
                        details = record_log['details'];
                        new_record = this.copy_record(record, false)
                        new_details = {};
                        for (var detail_id in details) {
                            if (details.hasOwnProperty(detail_id)) {
                                detail = details[detail_id];
                                new_detail = {};
                                detail_item = this.item.item_by_ID(parseInt(detail_id, 10));
                                detail_item.change_log.logs = detail['logs'];
                                detail_item.change_log.get_changes(new_detail);
                                new_details[detail_id] = new_detail;
                            }
                        }
                        data[key] = {
                            'unmodified_record': record_log['unmodified_record'],
                            'record': new_record,
                            'details': new_details
                        };
                    }
                }
            }
        },

        //~ for key, record_log in data.iteritems():
            //~ if self._change_id < int(key):
                //~ self._change_id = int(key)
            //~ record = record_log['record']
            //~ new_records.append([int(key), record])
            //~ details = {}
            //~ self.logs[key] = {
                //~ 'unmodified_record': record_log['unmodified_record'],
                //~ 'record': record,
                //~ 'details': details
            //~ }
            //~ for detail_id, detail in record_log['details'].iteritems():
                //~ detail_item = self.item.item_by_ID(int(detail_id))
                //~ detail_item.change_log.set_changes(detail)
                //~ details[detail_id] = {
                    //~ 'logs': detail_item.change_log.logs,
                    //~ 'records': detail_item.change_log.records,
                    //~ 'fields': detail_item.change_log.fields,
                    //~ 'expanded': detail_item.change_log.expanded
                //~ }
        //~ new_records.sort(key=lambda x: x[0])
        //~ self.records = [rec for key, rec in new_records]

        set_changes: function(changes) {
            var data = changes['data'],
                record_log,
                record,
                record_details,
                details,
                detail,
                detail_item;
            this.records = []
            this.logs = {}
            this.fields = changes['fields']
            this.expanded = changes['expanded']
            this._change_id = 0
            for (var key in data) {
                if (data.hasOwnProperty(key)) {
                    record_log = data[key];
                    if (this._change_id < parseInt(key, 10)) {
                        this._change_id = parseInt(key, 10)
                    }
                    record = record_log['record'];
                    this.records.push(record);
                    details = {};
                    this.logs[key] = {
                        'unmodified_record': record_log['unmodified_record'],
                        'record': record,
                        'details': details
                    }
                    record_details = record_log['details'];
                    for (var detail_id in record_details) {
                        if (record_details.hasOwnProperty(detail_id)) {
                            detail = record_details[detail_id];
                            detail_item = this.item.item_by_ID(parseInt(detail_id, 10));
                            detail_item.change_log.set_changes(detail);
                            details[detail_id] = {
                                'logs': detail_item.change_log.logs,
                                'records': detail_item.change_log.records,
                                'fields': detail_item.change_log.fields,
                                'expanded': detail_item.change_log.expanded
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
                    cur_logs = detail['logs'];
                    cur_records = detail['records'];
                    fields = detail['fields'];
                    expanded = detail['expanded'];
                    records = this.copy_records(cur_records);
                    for (var key in cur_logs) {
                        if (cur_logs.hasOwnProperty(key)) {
                            record_log = cur_logs[key];
                            cur_record = record_log['record'];
                            record = detail_item.change_log.copy_record(cur_record);
                            index = cur_records.indexOf(cur_record);
                            if (index !== -1) {
                                records[index] = record;
                            }
                            details = {};
                            detail_item.change_log.store_details(record_log['details'], details);
                            logs[key] = {
                                'unmodified_record': record_log['unmodified_record'],
                                'record': record,
                                'details': details
                            };
                        }
                    }
                } else {
                    if (detail_item._records) {
                        records = this.copy_records(detail_item._records);
                    }
                }
                dest[detail_id] = {
                    'logs': logs,
                    'records': records,
                    'fields': fields,
                    'expanded': expanded
                };
            }
        },

        store_record_log: function() {
            var record_log,
                details,
                detail,
                result;
            if (this.log_changes()) {
                record_log = this.find_record_log()
                details = {};
                this.store_details(record_log['details'], details);
                result = {};
                result['unmodified_record'] = record_log['unmodified_record'];
                result['record'] = this.copy_record(record_log['record']);
                result['details'] = details;
            } else {
                result = {};
                result['record'] = this.copy_record(this.cur_record());
                details = {};
                for (var i = 0; i < this.item.details.length; i++) {
                    detail = this.item.details[i];
                    if (detail._records) {
                        details[detail.ID] = detail._records.slice(0);
                    }
                }
                result['details'] = details;
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
                record = log['record'];
                cur_record = this.cur_record();
                info_index = this.item._record_info_index;
                for (var i = 0; i < info_index; i++) {
                    cur_record[i] = record[i];
                }
                record_log['unmodified_record'] = log['unmodified_record'];
                record_log['record'] = cur_record;
                record_log['details'] = log['details'];
                for (var i = 0; i < this.item.details.length; i++) {
                    detail = this.item.details[i];
                    detail_log = log['details'][detail.ID];
                    if (!this.isEmptyObj(detail_log)) {
                        detail._records = detail_log['records'];
                    }
                }
                if (this.item.get_record_status() === consts.RECORD_UNCHANGED) {
                    this.remove_record_log();
                }
            } else {
                record = log['record'];
                cur_record = this.cur_record();
                info_index = this.item._record_info_index;
                for (var i = 0; i < info_index; i++) {
                    cur_record[i] = record[i];
                }
                for (var i = 0; i < this.item.details.length; i++) {
                    detail = this.item.details[i];
                    detail._records = log['details'][detail.ID];
                }
            }
        },

        update: function(updates) {
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
                info;
            if (updates) {
                changes = updates['changes'];
                for (var key in changes) {
                    if (changes.hasOwnProperty(key)) {
                        change = changes[key];
                        log_id = change['log_id'];
                        rec_id = change['rec_id'];
                        details = change['details'];
                        record_log = this.logs[log_id];
                        record = record_log['record'];
                        record_details = record_log['details'];
                        len = details.length;
                        for (var i = 0; i < len; i++) {
                            detail = details[i];
                            ID = detail['ID'];
                            detail_item = this.item.detail_by_ID(parseInt(ID, 10));
                            item_detail = record_details[ID];
                            if (!this.isEmptyObj(item_detail)) {
                                detail_item.change_log.logs = item_detail['logs'];
                                detail_item.change_log.update(detail);
                            }
                        }
                        if (rec_id && !record[this.item.id.bind_index]) {
                            record[this.item.id.bind_index] = rec_id;
                        }
                        info = this.item.get_rec_info(undefined, record);
                        info[consts.REC_STATUS] = consts.RECORD_UNCHANGED;
                        info[consts.REC_CHANGE_ID] = consts.RECORD_UNCHANGED;
                        delete this.logs[log_id];
                    }
                }
            }
        },

        prepare: function() {
            var i,
                len = this.item.fields.length;
            this.records = [];
            this.logs = {};
            this.fields = [];
            for (i = 0; i < len; i++) {
                if (!this.item.fields[i].master_field) {
                    this.fields.push(this.item.fields[i].field_name)
                }
            }
            this.expanded = this.item.expanded;
        }
    };


    /**********************************************************************/
    /*                            Item class                              */
    /**********************************************************************/

    Item.prototype = new AbsrtactItem();

    function Item(owner, ID, item_name, caption, visible, type) {
        var self;
        AbsrtactItem.call(this, owner, ID, item_name, caption, visible, type);
        if (this.task && type !== 0 && !(item_name in this.task)) {
            this.task[item_name] = this;
        }
        this._fields = [];
        this.fields = [];
        this.filters = [];
        this.details = [];
        this.controls = [];
        this.change_log = new ChangeLog(this);
        this._log_changes = true;
        this._records = null;
        this._eof = false;
        this._bof = false;
        this._cur_row = null;
        this._old_row = 0;
        this._old_status = null;
        this._buffer = null;
        this._modified = null;
        this._state = 0;
        this._read_only = false;
        this.parent_read_only = true;
        this._active = false;
        this._disabled_count = 0;
        this._open_params = {};
        this._where_list = [];
        this._order_by_list = [];
        this.expanded = true;
        this._record_lookup_index = -1
        this._record_info_index = -1
        this.is_delta = false;
        this.limit = 100;
        this.post_local = false;
        this.offset = 0;
        this.is_loaded = false;
        this.details_active = false;
        this.disabled = false;
        this._filter_row = [];
        Object.defineProperty(this, "rec_no", {
            get: function() {
                return this.get_rec_no();
            },
            set: function(new_value) {
                this.set_rec_no(new_value);
            }
        });
        Object.defineProperty(this, "records", {
            get: function() {
                return this.get_records();
            },
            set: function(new_value) {
                this.set_records(new_value);
            }
        });
        Object.defineProperty(this, "active", {
            get: function() {
                return this.get_active();
            }
        });
        Object.defineProperty(this, "read_only", {
            get: function() {
                return this.get_read_only();
            },
            set: function(new_value) {
                this.set_read_only(new_value);
            }
        });
        Object.defineProperty(this, "modified", {
            get: function() {
                return this.get_modified();
            },
        });
        Object.defineProperty(this, "filtered", {
            get: function() {
                return this.get_filtered();
            },
            set: function(new_value) {
                this.set_filtered(new_value);
            }
        });
        Object.defineProperty(this, "item_state", {
            get: function() {
                return this.get_state();
            },
            set: function(new_value) {
                this.set_state(new_value);
            }
        });
        Object.defineProperty(this, "record_status", {
            get: function() {
                return this.get_record_status();
            },
            set: function(new_value) {
                this.set_record_status(new_value);
            }
        });
        Object.defineProperty(this, "default_field", {
            get: function() {
                return this.find_default_field();
            }
        });
        Object.defineProperty(this, "log_changes", {
            get: function() {
                return this.get_log_changes();
            },
            set: function(new_value) {
                this.set_log_changes(new_value);
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
                fields = info[6],
                filters = info[7],
                len;
            if (fields) {
                len = fields.length;
                for (i = 0; i < len; i++) {
                    new Field(this, fields[i]);
                }
            }
            if (filters) {
                len = filters.length;
                for (i = 0; i < len; i++) {
                    new Filter(this, filters[i]);
                }
            }
            this.reports = info[9];
        },

        bindItem: function() {
            var i = 0,
                len = this._fields.length,
                report_ids,
                field;
            for (; i < len; i++) {
                field = this._fields[i];
                if (field.lookup_item && (typeof field.lookup_item === "number")) {
                    field.lookup_item = this.task.item_by_ID(field.lookup_item);
                }
                if (field.master_field && (typeof field.master_field === "number")) {
                    field.master_field = this.get_master_field(this._fields, field.master_field);
                }
            }
            this.fields = this._fields.slice(0);
            len = this.filters.length;
            for (i = 0; i < len; i++) {
                field = this.filters[i].field;
                if (field.lookup_item && (typeof field.lookup_item === "number")) {
                    field.lookup_item = this.task.item_by_ID(field.lookup_item);
                }
                this._filter_row.push(null);
                this.filters[i].field.bind_index = i;
            }
            for (i = 0; i < len; i++) {
                field = this.filters[i].field;
                if (field.lookup_item) {
                    this._filter_row.push(null);
                    this.filters[i].field.lookup_index = this._filter_row.length - 1;
                }
            }
            len = this.reports.length;
            report_ids = this.reports;
            this.reports = [];
            for (i = 0; i < len; i++) {
                this.reports.push(this.task.item_by_ID(report_ids[i]));
            }
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

        eachRecord: function(callback) {
            this.each(callback);
        },

        eachField: function(callback) {
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

        eachFilter: function(callback) {
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

        eachDetail: function(callback) {
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
//            result = fields[name];
//            if (result === undefined) {
            for (; i < len; i++) {
                if (fields[i].field_name === name) {
                    return fields[i];
                }
            }
//            }
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

        system_field_name: function(name) {
            if (name === 'id' || name === 'deleted'
                || name === 'owner_id' || name === 'owner_rec_id') {
                return true;
            }
        },

        get_records: function() {
            var i,
                len,
                result = [];
            if (this.active) {
                len = this._records.length;
                for (i = 0; i < len; i++)
                    result.push(this._records[i].slice(0, this._record_info_index))
                return result
            }
        },

        set_records: function(value) {
            this._records = value;
        },

        copy: function(options) {
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
            result.limit = this.limit;
            options = $.extend({}, defaultOptions, options);
            result.ID = this.ID;
            result.item_name = this.item_name;
            result.expanded = this.expanded;
            len = this._fields.length;
            for (i = 0; i < len; i++) {
                copy = this._fields[i].copy(result);
                copy.lookup_item = this._fields[i].lookup_item;
            }
            for (i = 0; i < len; i++) {
                field = this._fields[i];
                if (field.master_field && (typeof field.master_field === "number")) {
                    field.master_field = result.get_master_field(result._fields, field.master_field);
                }
            }
            result.fields = result._fields.slice(0);
            for (i = 0; i < len; i++) {
                field = result.fields[i];
                if (result[field.field_name] === undefined) {
                    result[field.field_name] = field;
                }
            }
            //~ for (i = 0; i < len; i++) {
                //~ field = this.fields[i];
                //~ if (this[field.field_name] === undefined) {
                    //~ this[field.field_name] = field;
                //~ }
            //~ }
            if (options.filters) {
                this.eachFilter(function(filter, i) {
                    filter.copy(result);
                });
                result._filter_row = [];
                result.eachFilter(function(filter, i) {
                    result._filter_row.push(null);
                    filter.field.bind_index = i;
                });
                result.eachFilter(function(filter) {
                    if (filter.field.lookup_item) {
                        result._filter_row.push(null);
                        filter.field.lookup_index = result._filter_row.length - 1;
                    }
                });
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
                this.eachDetail(function(detail, i) {
                    copyTable = detail.copy(options);
                    copyTable.owner = result;
                    copyTable.expanded = detail.expanded;
                    copyTable.master = result;
                    copyTable.item_type = detail.item_type;
                    result.details.push(copyTable);
                    result.items.push(copyTable);
                    if (!(copyTable.item_name in result)) {
                        result[copyTable.item_name] = copyTable;
                    }
                });
            }
            return result;
        },

        clone: function(keep_filtered) {
            var result,
                i,
                len,
                copy,
                field;
            if (keep_filtered === undefined) {
                keep_filtered = true;
            }
            result = new Item(this.owner, this.ID, this.item_name,
                this.item_caption, this.visible, this.item_type_id);
            result.master = this.master;
            result.item_type = this.item_type;
            result.ID = this.ID;
            result.item_name = this.item_name;
            len = this._fields.length;
            for (i = 0; i < len; i ++) {
                copy = this._fields[i].copy(result);
                copy.lookup_item = this._fields[i].lookup_item;
            }
            for (i = 0; i < len; i++) {
                field = this._fields[i];
                if (field.master_field && (typeof field.master_field === "number")) {
                    field.master_field = result.get_master_field(result._fields, field.master_field);
                }
            }
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = result._field_by_name(this.fields[i].field_name);
                result.fields.push(field)
                if (!result[field.field_name]) {
                    result[field.field_name] = field
                }
            }
            result.bind_fields();
            result._records = this._records;
            if (keep_filtered) {
                result.on_filter_record = this.on_filter_record;
                result.filtered = this.filtered;
            }
            result._active = true;
            result.set_state(consts.STATE_BROWSE);
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

        get_log_changes: function() {
            return this._log_changes;
        },

        set_log_changes: function(value) {
            this._log_changes = value;
        },

        get_modified: function() {
            return this._modified;
        },

        set_modified: function(value) {
            this._modified = value;
            if (this.master && value) {
                this.master.set_modified(value);
            }
        }
    });

    // Item server exchange methods

    $.extend(Item.prototype, {

        bind_fields: function(expanded) {
            var j = 0;
            if (expanded === undefined) {
                expanded = true;
            }
            this.eachField(function(field, i) {
                field.bind_index = null;
                field.lookup_index = null;
            });
            this.eachField(function(field, i) {
                if (!field.master_field) {
                    field.bind_index = j;
                    j += 1;
                }
            });
            this.eachField(function(field, i) {
                if (field.master_field) {
                    field.bind_index = field.master_field.bind_index;
                }
            });
            this._record_lookup_index = j
            if (expanded) {
                this.eachField(function(field, i) {
                    if (field.lookup_item) {
                        field.lookup_index = j;
                        j += 1;
                    }
                });
            }
            this._record_info_index = j;
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
                        if (field.data_type === consts.DATETIME) {
                            value = field.format_date_to_string(value, '%Y-%m-%d %H:%M:%S')
                        }
                        result.push([field_name, filter_type, value])
                    }
                }
            }
            return result;
        },

        do_before_open: function(expanded, fields, where, order_by, open_empty, params) {
            var result,
                i,
                len,
                field,
                filters = [];
                params.__expanded = expanded;
                params.__fields = [];
            if (this.on_before_open) {
                result = this.on_before_open.call(this, this, params);
            }

            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i]
                if (this[field.field_name] !== undefined) {
                    delete this[field.field_name];
                }
            }
            this.fields = [];
            if (fields) {
                len = fields.length;
                for (i = 0; i < len; i++) {
                    this.fields.push(this._field_by_name(fields[i]));
                }
                params.__fields = fields;
            }
            else {
                this.fields = this._fields.slice(0);
            }
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i]
                if (this[field.field_name] === undefined) {
                    this[field.field_name] = field;
                }
            }

            params.__open_empty = open_empty;
            if (!open_empty && result !== false) {
                if (where) {
                    filters = this.get_where_list(where);
                } else if (this._where_list.length) {
                    filters = this._where_list.slice(0);
                } else {
                    this.eachFilter(function(filter, i) {
                        if (filter.get_value() !== null) {
                            filters.push([filter.field.field_name, filter.filter_type, filter.get_value()]);
                        }
                    });
                }
                if (params.__search !== undefined) {
                    var field_name = params.__search[0],
                        text = params.__search[1];
                    filters.push([field_name, consts.FILTER_SEARCH, text]);
                }
                params.__filters = filters;
                if (order_by) {
                    params.__order = this.get_order_by_list(order_by);
                } else if (this._order_by_list.length) {
                    params.__order = this._order_by_list.slice(0);
                }
                this._where_list = [];
                this._order_by_list = [];
            }
            this._sorted_fields = [];
            this._sorted_desc = false;
            this._open_params = params;
            return result
        },

        do_after_open: function() {
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

            if (!this.grid_keydown) {
                if (callback) {
                    this.eachDetail(function(detail, i) {
                        if (!detail.disabled) {
                            details += 1;
                        }
                    });
                    this.eachDetail(function(detail, i) {
                        if (!detail.disabled) {
                            detail.open(afterOpen);
                        }
                    });
                } else {
                    this.eachDetail(function(detail, i) {
                        if (!detail.disabled) {
                            detail.open();
                        }
                    });
                }
            } else {
                if (callback) {
                    callback.call(this);
                }
            }
        },

        find_change_log: function() {
            if (this.master) {
                if (this.master.get_record_status() !== consts.RECORD_UNCHANGED) {
                    return this.master.change_log.get_detail_log(this.ID)
                }
            }
        },

        open: function() {
            var result,
                i = 0,
                len = arguments.length,
                options,
                expanded,
                fields,
                where,
                order_by,
                open_empty,
                params,
                callback,
                async,
                log,
                offset,
                rec_info,
                records,
                details_active = this.details_active,
                self = this;
            if (len > 2) {
                throw item.item_name + ' open method error: invalid number of arguments'
            }
            for (; i < len; i++) {
                switch (typeof arguments[i]) {
                    case "function":
                        callback = arguments[i];
                        break;
                    case "object":
                        options = arguments[i];
                        break;
                }
            }
            if (options) {
                expanded = options.expanded;
                fields = options.fields;
                where = options.where;
                order_by = options.order_by;
                open_empty = options.open_empty;
                params = options.params;
                offset = options.offset;
            }
            if (!params) {
                params = {};
            }
            if (expanded === undefined) {
                expanded = this.expanded;
            } else {
                this.expanded = expanded;
            }
            async = callback ? true : false;
            if (this.master) {
                if (!this.disabled && this.master.record_count() > 0) {
                    params.__owner_id = this.master.ID;
                    if (this.master.id) {
                        params.__owner_rec_id = this.master.id.get_value();
                    }
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
                        if (this.do_before_open(expanded, fields, where, order_by, open_empty, params) !== false) {
                            this.bind_fields(expanded);
                            this._records = records;
                            this._active = true;
                            this.set_state(consts.STATE_BROWSE);
                            this.first();
                            this.do_after_open();
                            this.update_controls(consts.UPDATE_OPEN);
                            if (callback) {
                                callback.call(this, this);
                            }
                        }
                        return;
                    }
                }
                else {
                    return;
                }
            }
            if (offset !== undefined) {
                params = this._open_params;
            } else {
                offset = 0
                result = this.do_before_open(expanded, fields, where, order_by, open_empty, params);
                this.bind_fields(expanded);
            }
            if (result !== false) {
                this.change_log.prepare();
                this._records = [];
                this.load_next(offset, async, params, open_empty, function() {
                    self.details_active = false;
                    try {
                        //                self.expanded = expanded;
                        self._active = true;
                        self.set_state(consts.STATE_BROWSE);
                        self._cur_row = null;
                        self.first();
                        self.do_after_open();
                        self.update_controls(consts.UPDATE_OPEN);
                        if ((offset === 0) && self.on_filter_applied) {
                            self.on_filter_applied.call(self, self);
                        }
                    } finally {
                        self.details_active = details_active;
                    }
                    if (self.details_active) {
                        self.open_details(callback)
                    } else if (callback) {
                        callback.call(self, self);
                    }
                });
            }
        },

        load_next: function(offset, async, params, open_empty, callback) {
            var self = this,
                data;

            params.__loaded = 0;
            params.__limit = 0;
            if (this.auto_loading) {
                if (offset !== undefined) {
                    params.__loaded = offset;
                }
                params.__limit = this.limit;
            }
            if (async && !open_empty) {
                this.send_request('open', params, function(data) {
                    self.do_after_upload(data, offset, callback);
                });
            } else {
                if (open_empty) {
                    data = [[], ''];
                }
                else {
                    data = this.send_request('open', params);
                }
                this.do_after_upload(data, offset, callback);
            }
        },

        do_after_upload: function(data, offset, callback) {
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
                        if (offset !== undefined) {
                            this._records.length = 0;
                        }
                        for (i = 0; i < len; i++) {
                            this._records.push(rows[i]);
                        }
                        if (this.limit && this.auto_loading && rows) {
                            this.offset = offset;
                            this.is_loaded = false;
                        }
                        if (len < this.limit) {
                            this.is_loaded = true;
                        }
                        callback.call(this, this);
                    }
                }
            } else {
                this._records = [];
                console.log(this.item_name + " error while opening table");
            }

        },

        close: function() {
            this._active = false;
            this._records = null;
            this._cur_row = null;
            this.close_details();
            this.update_controls(consts.UPDATE_CLOSE);
        },

        close_details: function() {
            var len = this.details.length;
            if (!this.grid_keydown) {
                for (var i = 0; i < len; i++) {
                    this.details[i].close();
                }
            }
        },

            "TEXT": 1,
            "INTEGER": 2,
            "FLOAT": 3,
            "CURRENCY": 4,
            "DATE": 5,
            "DATETIME": 6,
            "BOOLEAN": 7,
            "BLOB": 8,

        sort: function(fields) {
            var self = this,
                i,
                field_name,
                field_names = [],
                desc = [],
                field;

            function convert_value(value, data_type) {
                if (value === null) {
                    if (data_type === consts.TEXT) {
                        value = ''
                    }
                    else if (data_type === consts.INTEGER || data_type === consts.FLOAT || data_type === consts.CURRENCY) {
                        value = 0;
                    }
                    else if (data_type === consts.DATE || data_type === consts.DATETIME) {
                        value = new Date(0);
                    }
                    else if (data_type === consts.BOOLEAN) {
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

            for (i = 0; i < fields.length; i++) {
                field_name = fields[i];
                if (field_name.charAt(0) === '-') {
                    field_names.push(field_name.substring(1));
                    desc.push(true);
                }
                else {
                    field_names.push(field_name);
                    desc.push(false);
                }
            }
            this._records.sort(compare_records);
            this.update_controls();
        },

        search: function(field_name, text) {
            var searchText = text.trim(),
                params = {};

            if (searchText.length) {
                params.__search = [field_name, searchText];
                this.open({
                    params: params
                });
            } else {
                this.open();
            }
        },

        total_records: function(callback) {
            var self = this;
            if (this._open_params.__open_empty && callback) {
                return 0;
            }
            else {
                this.send_request('get_record_count', this._open_params, function(data) {
                    if (data && callback) {
                        callback.call(self, data[0]);
                    }
                });
            }
        },

        new_record: function() {
            var result = [];
            this.eachField(function(field, i) {
                if (!field.master_field) {
                    result.push(null);
                }
            });
            if (this.expanded) {
                this.eachField(function(field, i) {
                    if (field.lookup_item) {
                        result.push(null);
                    }
                });
            }
            return result;
        },

        do_before_append: function() {
            if (this.on_before_append) {
                return this.on_before_append.call(this, this);
            }
        },

        do_after_append: function() {
            if (this.on_after_append) {
                this.on_after_append.call(this, this);
            }
        },

        append: function() {
            if (!this._active) {
                throw this.item_name + ": can't append record - item is not active";
            }
            if (this.master && !this.master.is_changing()) {
                throw this.item_name + ": can't append record - master item is not in edit or insert mode";
            }
            if (this.get_state() !== consts.STATE_BROWSE) {
                throw this.item_name + ": can't append record - item is not in browse mode";
            }
            if (this.do_before_append() !== false) {
                if (this.do_before_scroll() !== false) {
                    this._old_row = this.get_rec_no();
                    this.set_state(consts.STATE_INSERT);
                    this._records.push(this.new_record());
                    this._cur_row = this._records.length - 1;
                    this._modified = false;
                    this.set_record_status(consts.RECORD_INSERTED);
                    this.update_controls(consts.UPDATE_APPEND);
                    this.do_after_scroll();
                    this.do_after_append();
                }
            }
        },

        insert: function() {
            if (!this._active) {
                throw this.item_name + ": can't insert record - item is not active";
            }
            if (this.master && !this.master.is_changing()) {
                throw this.item_name + ": can't insert record - master item is not in edit or insert mode";
            }
            if (this.get_state() !== consts.STATE_BROWSE) {
                throw this.item_name + ": can't insert record - item is not in browse mode";
            }
            if (this.do_before_append() !== false) {
                if (this.do_before_scroll() !== false) {
                    this._old_row = this.get_rec_no();
                    this.set_state(consts.STATE_INSERT);
                    this._records.splice(0, 0, this.new_record());
                    this._cur_row = 0;
                    this._modified = false;
                    this.set_record_status(consts.RECORD_INSERTED);
                    this.update_controls(consts.UPDATE_INSERT);
                    this.do_after_scroll();
                    this.do_after_append();
                }
            }
        },

        copy_rec: function() {
            var i, len, rec;
            if (!this._active) {
                throw this.item_name + ": can't copy record - item is not active";
            }
            if (this.master && !this.master.is_changing()) {
                throw this.item_name + ": can't copy record - master item is not in edit or insert mode";
            }
            if (this.get_state() !== consts.STATE_BROWSE) {
                throw this.item_name + ": can't copy record - item is not in browse mode";
            }
            if (this.record_count() === 0) {
                throw this.item_name + ": can't edit record - item record list is empty";
            }
            rec = this.get_rec_no();
            if (this.do_before_append() !== false) {
                if (this.do_before_scroll() !== false) {
                    this._old_row = rec;
                    this.set_state(consts.STATE_INSERT);
                    this._buffer = this._records[rec].slice(0);
                    this._records.push(this.new_record());
                    this._cur_row = this._records.length - 1;
                    rec = this.get_rec_no();
                    len = this._records[rec].length;
                    for (i = 0; i < len; i++) {
                        if (i < this._record_info_index) {
                            this._records[rec][i] = this._buffer[i];
                        }
                    }
                    this._records[rec][this.id.bind_index] = null;
                    this._buffer = null;
                    this._modified = false;
                    this.set_record_status(consts.RECORD_INSERTED);
                    this.update_controls(consts.UPDATE_APPEND);
                    this.do_after_scroll();
                    this.do_after_append();
                }
            }
        },

        do_before_edit: function() {
            if (this.on_before_edit) {
                return this.on_before_edit.call(this, this);
            }
        },

        do_after_edit: function() {
            if (this.on_after_edit) {
                this.on_after_edit.call(this, this);
            }
        },

        edit: function() {
            if (!this._active) {
                throw this.item_name + ": can't edit record - item is not active";
            }
            if (this.master && !this.master.is_changing()) {
                throw this.item_name + ": can't edit record - master item is not in edit or insert mode";
            }
            if (this.get_state() !== consts.STATE_BROWSE) {
                throw this.item_name + ": can't edit record - item is not in browse mode";
            }
            if (this.record_count() === 0) {
                throw this.item_name + ": can't edit record - item record list is empty";
            }
            if (this.do_before_edit() !== false) {
                this.change_log.log_change();
                this._buffer = this.change_log.store_record_log();
                this.set_state(consts.STATE_EDIT);
                this._old_row = this.get_rec_no();
                this._old_status = this.get_record_status();
                this._modified = false;
                this.do_after_edit();
            }
        },

        do_before_cancel: function() {
            if (this.on_before_cancel) {
                return this.on_before_cancel.call(this, this);
            }
        },

        do_after_cancel: function() {
            if (this.on_after_cancel) {
                this.on_after_cancel.call(this, this);
            }
        },

        cancel: function() {
            var i,
                len,
                rec,
                prev_state,
                prev_modified = this._modified;
            rec = this.get_rec_no();

            if (this.do_before_cancel() !== false) {
                if (this.get_state() === consts.STATE_EDIT) {
                    this.change_log.restore_record_log(this._buffer)
                    this.update_controls(consts.UPDATE_CANCEL)
                    for (var i = 0; i < this.details.length; i++) {
                        this.details[i].update_controls(consts.UPDATE_OPEN);
                    }
                } else if (this.get_state() === consts.STATE_INSERT) {
                    this.change_log.remove_record_log();
                    this.update_controls(consts.UPDATE_DELETE);
                    this._records.splice(rec, 1);
                } else {
                    throw this.item_name + ' cancel error: invalid item state';
                }

                prev_state = this.get_state();
                this.set_state(consts.STATE_BROWSE);
                if (prev_state === consts.STATE_INSERT) {
                    this.do_before_scroll();
                }
                this._cur_row = this._old_row;
                if (prev_state === consts.STATE_EDIT) {
                    this.set_record_status(this._old_status);
                }
                this._modified = false;
                if (prev_state === consts.STATE_INSERT) {
                    this.do_after_scroll();
                }
                this.do_after_cancel();
            }
        },

        is_browsing: function() {
            return this.get_state() === consts.STATE_BROWSE;
        },

        is_changing: function() {
            return (this.get_state() === consts.STATE_INSERT) || (this.get_state() === consts.STATE_EDIT);
        },

        is_new: function() {
            return this.get_state() === consts.STATE_INSERT;
        },

        is_editing: function() {
            return this.get_state() === consts.STATE_EDIT;
        },

        is_deleting: function() {
            return this.get_state() === consts.STATE_DELETE;
        },


        do_before_delete: function(callback) {
            if (this.on_before_delete) {
                return this.on_before_delete.call(this, this);
            }
        },

        do_after_delete: function() {
            if (this.on_after_delete) {
                this.on_after_delete.call(this, this);
            }
        },

        "delete": function() {
            var rec = this.get_rec_no();
            if (this.master && !this.master.is_changing()) {
                throw this.item_name + ": can't delete record - master item is not in edit or insert mode";
            }
            this.set_state(consts.STATE_DELETE);
            try {
                if (this.record_count() > 0) {
                    if (this.do_before_delete() !== false) {
                        if (this.do_before_scroll() !== false) {
                            this.update_controls(consts.UPDATE_DELETE);
                            this.change_log.log_change();
                            if (this.master) {
                                this.master.set_modified(true);
                            }
                            this._records.splice(rec, 1);
                            this.set_rec_no(rec);
                            this.do_after_scroll();
                            this.set_state(consts.STATE_BROWSE);
                            this.do_after_delete();
                        }
                    }
                }
            } finally {
                this.set_state(consts.STATE_BROWSE);
            }
        },

        detail_by_ID: function(ID) {
            var result;
            if (typeof ID === "string") {
                ID = parseInt(ID, 10);
            }
            this.eachDetail(function(detail, i) {
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
                old_state = this.get_state(),
                on_before_result,
                result = false,
                request;
            if (!this.is_changing()) {
                throw this.item_name + ' post method: dataset is not in edit or insert mode';
            }
            if (this.get_modified()) {
                if (this.check_record_valid()) {
                    if (this.on_before_post) {
                        on_before_result = this.on_before_post.call(this, this);
                    }
                    if (on_before_result !== false) {
                        len = this.details.length;
                        for (i = 0; i < len; i++) {
                            if (this.details[i].is_changing()) {
                                if (!this.details[i].post()) {
                                    return result;
                                }
                            }
                        }
                        this.change_log.log_change();
                        this.set_modified(false);
                        if (this.master) {
                            this.master.set_modified(true);
                        }
                        this.set_state(consts.STATE_BROWSE);
                        if (!this.valid_record()) {
                            this.update_controls(consts.UPDATE_DELETE);
                            this.search_record(this.get_rec_no(), 0);
                        }
                        if (this.on_after_post) {
                            this.on_after_post.call(this, this);
                        }
                        result = true
                    }
                }
            } else {
                this.cancel();
                result = true;
            }
            return result
        },

        get_change_id: function() {
            this._change_id = this._change_id + 1;
            return this._change_id;
        },

        clear_log: function(log) {
            var rec,
                details,
                info,
                detail_changes,
                detail_expanded,
                detail_records;
            for (var key in log) {
                if (log.hasOwnProperty(key)) {
                    rec = log[key][0];
                    details = log[key][1];
                    info = rec[rec.length - 1];
                    info[consts.REC_STATUS] = null;
                    info[consts.REC_CHANGE_ID] = null;
                    for (var detail_id in details) {
                        if (details.hasOwnProperty(detail_id)) {
                            detail_changes = details[detail_id][0];
                            detail_expanded = details[detail_id][1];
                            detail_records = details[detail_id][2];
                            this.clear_log(detail_changes);
                        }
                    }
                }
            }
        },

        apply: function() {
            var i = 0,
                len = arguments.length,
                self = this,
                changes = {},
                callback,
                params,
                data,
                result = true;
            for (; i < len; i++) {
                switch (typeof arguments[i]) {
                    case "function":
                        callback = arguments[i];
                        break;
                    case "object":
                        params = arguments[i];
                        break;
                }
            }
            this.change_log.get_changes(changes);
            if (!this.master && !this.change_log.isEmptyObj(changes.data)) {
                if (this.item_state !== consts.STATE_BROWSE) {
                    this.warning('Item: ' + this.item_name + ' is not is browse state. Apply is only possible in browse state.');
                    return
                }
                if (this.on_before_apply) {
                    this.on_before_apply.call(this, this);
                }
                if (callback) {
                    this.send_request('apply_changes', [changes, params], function(data) {
                        self.process_apply(data);
                    });
                } else {
                    data = this.send_request('apply_changes', [changes, params]);
                    result = this.process_apply(data);
                }
            }
            return result;
        },

        process_apply: function(data) {
            if (data) {
                if (data.error) {
                    throw data.error;
                } else {
                    this.change_log.update(data.result)
                    if (this.on_after_apply) {
                        this.on_after_apply.call(this, this);
                    }
                    return true;
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
            result = this.copy({filters: false, details: true, handlers: false});
            result.expanded = false;
            result.is_delta = true;
            len = result.details.length;
            for (i = 0; i < len; i++) {
                result.details[i].expanded = false;
                result.details[i].is_delta = true;
            }
            result.details_active = true;
            result.change_log.set_changes(changes);
            result._records = result.change_log.records;
            result.bind_fields(result.change_log.expanded)
            result.set_state(consts.STATE_BROWSE);
            result._cur_row = null;
            result._active = true;
            result.first();
            return result;
        },

        field_by_id: function(id_value, field_name, callback) {
            return this.send_request('get_field_by_id', [id_value, field_name], callback);
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

        get_active: function() {
            return this._active;
        },

        set_read_only: function(value) {
            var i,
                len;
            this._read_only = value;
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                this.fields[i].update_controls();
            }
            this.eachDetail(function(detail, i) {
                detail.set_read_only(value);
            });

        },

        get_read_only: function() {
            if (this.master && this.parent_read_only) {
                return this.master.get_read_only();
            }
            else {
                return this._read_only;
            }
        },

        get_filtered: function() {
            return this._filtered;
        },

        set_filtered: function(value) {
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
            this.eachFilter(function(filter) {
                filter.value = null;
            })
        },

        set_state: function(value) {
            if (this._state !== value) {
                this._state = value;
                if (this.on_state_changed) {
                    this.on_state_changed.call(this, this);
                }
            }
        },

        get_state: function() {
            return this._state;
        },

        disable_detail_records: function() {
            var len = this.details.length;
            for (var i = 0; i < len; i++) {
                this.close_details();
            }
        },

        do_after_scroll: function() {
            this.update_controls(consts.UPDATE_SCROLLED);
            if (this.on_after_scroll) {
                this.on_after_scroll.call(this, this);
            }
            if (this.details_active) {
                this.open_details();
            } else {
                this.disable_detail_records()
            }
        },

        do_before_scroll: function() {
            if (this._cur_row !== null) {
                if ((this.get_state() === consts.STATE_INSERT) || (this.get_state() === consts.STATE_EDIT)) {
                    this.post();
                }
                if (this.on_before_scroll) {
                    return this.on_before_scroll.call(this, this);
                }
            }
        },

        skip: function(value) {
            var eof,
                bof,
                old_row,
                new_row;
            if (this.record_count() === 0) {
                this.do_before_scroll();
                this._eof = true;
                this._bof = true;
                this.do_after_scroll();
            } else {
                old_row = this._cur_row;
                eof = false;
                bof = false;
                new_row = value;
                if (new_row < 0) {
                    new_row = 0;
                    bof = true;
                }
                if (new_row >= this._records.length) {
                    new_row = this._records.length - 1;
                    eof = true;
                }
                this._eof = eof;
                this._bof = bof;
                if (old_row !== new_row) {
                    if (this.do_before_scroll() !== false) {
                        this._cur_row = new_row;
                        this.do_after_scroll();
                    }
                }
                else if (eof || bof && this.is_new() && this.record_count() === 1) {
                    this.do_before_scroll();
                    this.do_after_scroll();
                }
            }
        },

        set_rec_no: function(value) {
            if (this._active) {
                if (this.filter_active()) {
                    this.search_record(value, 0);
                } else {
                    this.skip(value);
                }
            }
        },

        get_rec_no: function() {
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
                this.set_rec_no(0);
            }
        },

        last: function() {
            if (this.filter_active()) {
                this.find_last();
            } else {
                this.set_rec_no(this._records.length);
            }
        },

        next: function() {
            if (this.filter_active()) {
                this.find_next();
            } else {
                this.set_rec_no(this.get_rec_no() + 1);
            }
        },

        prior: function() {
            if (this.filter_active()) {
                this.find_prior();
            } else {
                this.set_rec_no(this.get_rec_no() - 1);
            }
        },

        eof: function() {
            return this._eof;
        },

        bof: function() {
            return this._bof;
        },

        valid_record: function() {
            if (this.on_filter_record && this.filtered) {
                return this.on_filter_record.call(this, this);
            } else {
                return true;
            }
        },

        search_record: function(start, direction) {
            var row, self = this;
            direction = direction || 1;

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
                    if (self._cur_row >= self._records.length) {
                        self._cur_row = self._records.length - 1;
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
                this._cur_row = start + direction;
                update_position();
                if (direction === 0) {
                    if (this.valid_record()) {
                        this.skip(start);
                        return
                    }
                    direction = 1;
                }
                while (!check_record()) {
                    if (this.valid_record()) {
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
            this.search_record(-1, 1);
        },

        find_last: function() {
            this.search_record(this._records.length, -1);
        },

        find_next: function() {
            this.search_record(this.get_rec_no(), 1);
        },

        find_prior: function() {
            this.search_record(this.get_rec_no(), -1);
        },

        record_count: function() {
            if (this._records) {
                return this._records.length;
            } else {
                return 0;
            }
        },

        find_rec_info: function(rec_no, record) {
            if (record === undefined) {
                if (rec_no === undefined) {
                    rec_no = this.get_rec_no();
                    if (this.record_count() > 0) {
                        record = this._records[rec_no];
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

        get_record_status: function() {
            var info = this.get_rec_info();
            if (info) {
                return info[consts.REC_STATUS];
            }
        },

        set_record_status: function(value) {
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

        get_rec_change_id: function() {
            var info = this.get_rec_info();
            if (info) {
                return info[consts.REC_CHANGE_ID];
            }
        },

        set_rec_change_id: function(value) {
            var info = this.get_rec_info();
            if (info) {
                info[consts.REC_CHANGE_ID] = value;
            }
        },

        rec_unchanged: function() {
            return this.get_record_status() === consts.RECORD_UNCHANGED;
        },

        rec_inserted: function() {
            return this.get_record_status() === consts.RECORD_INSERTED;
        },

        rec_deleted: function() {
            return this.get_record_status() === consts.RECORD_DELETED;
        },

        rec_modified: function() {
            return this.get_record_status() === consts.RECORD_MODIFIED ||
                this.get_record_status() === consts.RECORD_DETAILS_MODIFIED;
        }

    });

    // Item interface methods

    $.extend(Item.prototype, {

        insert_record: function(args) {
            if (this.can_create()) {
                if (this.is_editing()) {
                    this.post();
                }
                if (!(this.is_new())) {
                    this.insert();
                }
                this.create_edit_form(args);
            }
        },

        append_record: function(args) {
            if (this.can_create()) {
                if (this.is_editing()) {
                    this.post();
                }
                if (!(this.is_new())) {
                    this.append();
                }
                this.create_edit_form(args);
            }
        },

        copy_record: function(args) {
            if (this.can_create() && this.record_count()) {
                if (!(this.is_changing())) {
                    this.copy_rec();
                    this.create_edit_form(args);
                }
            }
        },

        edit_record: function(args) {
            if (this.can_edit()) {
                if (this.record_count() > 0) {
                    if (!this.is_changing()) {
                        this.edit();
                    }
                    this.create_edit_form(args);
                }
            }
        },

        cancel_edit: function() {
            this.close_edit_form();
            this.cancel();
        },

        delete_record: function(callback) {
            var self = this,
                rec_no = self.get_rec_no(),
                record = self._records[rec_no],
                error;
            if (!this.read_only && this.can_delete()) {
                if (this.record_count() > 0) {
                    //            if ((this.get_state() === consts.STATE_BROWSE) && (this.record_count() > 0)) {
                    this.question(language.delete_record, function() {
                        self["delete"]();
                        try {
                            self.apply();
                        } catch (e) {
                            error = (e + '').toUpperCase();
                            if (error && error.indexOf('FOREIGN KEY') !== -1 &&
                                (error.indexOf('VIOLATION') !== -1 || error.indexOf('FAILED') !== -1)) {
                                self.warning(language.cant_delete_used_record);
                            } else {
                                self.warning(e);
                            }
                            self._records.splice(rec_no, 0, record);
                            self._cur_row = rec_no;
                            self.change_log.remove_record_log();
                            self.update_controls();
                            self.do_after_scroll();
                            if (callback) {
                                callback.call(this);
                            }
                        }
                    });
                } else {
                    this.warning('Record is not selected.');
                }
            }
        },

        check_record_valid: function() {
            var result = true;

            this.eachField(function(field, j) {
                var i,
                    len;
                len = field.controls.length;
                for (i = 0; i < len; i++) {
                    if (field.controls[i].errorValue || field.controls[i].error) {
                        field.controls[i].updateState(false);
                        result = false;
                    }
                }
                try {
                    field.check_valid();
                } catch (e) {
                    for (i = 0; i < len; i++) {
                        field.controls[i].error = e;
                        field.controls[i].updateState(false);
                    }
                    result = false;
                }
            });
            return result;
        },

        post_record: function() {
            if (this.check_record_valid()) {
                if (this.get_modified()) {
                    try {
                        if (this.is_changing()) {
                            this.post();
                            this.close_edit_form();
                        }
                    } catch (e) {}
                } else {
                    this.cancel();
                    this.close_edit_form();
                }
            }
        },

        apply_record: function(params) {
            var success;
            if (this.check_record_valid()) {
                if (this.get_modified()) {
                    if (this.is_changing()) {
                        if (this.post()) {
                            this.apply(params)
                            this.close_edit_form();
                            return true;
                        }
                    }
                } else {
                    if (this.is_changing()) {
                        this.cancel();
                    }
                    this.close_edit_form();
                }
            }
        },

        do_on_view_keyup: function(e) {
            if (this.task.on_view_keyup) {
                this.task.on_view_keyup.call(this, this, e);
            }
            if (this.owner.on_view_keyup) {
                this.owner.on_view_keyup.call(this, this, e);
            }
            if (this.on_view_keyup) {
                this.on_view_keyup.call(this, this, e);
            }
        },

        do_on_view_keydown: function(e) {
            if (this.task.on_view_keydown) {
                this.task.on_view_keydown.call(this, this, e);
            }
            if (this.owner.on_view_keydown) {
                this.owner.on_view_keydown.call(this, this, e);
            }
            if (this.on_view_keydown) {
                this.on_view_keydown.call(this, this, e);
            }
        },


        view_modal: function() {
            this.is_lookup_item = true;
            this.view();
        },

        view: function() {
            var self = this,
                container,
                options,
                argLen = arguments.length;
            if (argLen) {
                for (var i = 0; i < argLen; i++) {
                    if (!container && arguments[i] instanceof jQuery) {
                        container = arguments[i];
                    } else if (!options) {
                        options = arguments[i];
                    }
                }
            }
            this.view_form = $("<div></div>").append(this.findTemplate("view"));
            if (!container) {
                this.view_form = this.makeFormModal(this.view_form, options);
            }
            this.create_form('view_form', {
                container: container,
                beforeShow: function() {
                    if (this.task.on_before_show_view_form) {
                        this.task.on_before_show_view_form.call(this, this);
                    }
                    if (this.owner.on_before_show_view_form) {
                        this.owner.on_before_show_view_form.call(this, this);
                    }
                    if (this.on_before_show_view_form) {
                        this.on_before_show_view_form.call(this, this);
                    }
                },
                onShown: function() {
//                    this.open();
                    if (self.task.on_after_show_view_form) {
                        self.task.on_after_show_view_form.call(self, self);
                    }
                    if (self.owner.on_after_show_view_form) {
                        self.owner.on_after_show_view_form.call(self, self);
                    }
                    if (self.on_after_show_view_form) {
                        self.on_after_show_view_form.call(self, self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_view_form_close_query) {
                        canClose = self.on_view_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.owner.on_view_form_close_query && !self.master) {
                        canClose = self.owner.on_view_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_view_form_close_query) {
                        canClose = self.task.on_view_form_close_query.call(self, self);
                    }
                    return canClose;
                },
                onHidden: function() {
                    this.close();
                },
                onKeyUp: this.do_on_view_keyup,
                onKeyDown: this.do_on_view_keydown
            })
        },

        close_view_form: function() {
            this.close_form('view_form');
        },

        do_on_edit_keyup: function(e) {
            if (this.task.on_edit_keyup) {
                this.task.on_edit_keyup.call(this, this, e);
            }
            if (this.owner.on_edit_keyup) {
                this.owner.on_edit_keyup.call(this, this, e);
            }
            if (this.on_edit_keyup) {
                this.on_edit_keyup.call(this, this, e);
            }
        },

        do_on_edit_keydown: function(e) {
            if (this.task.on_edit_keydown) {
                this.task.on_edit_keydown.call(this, this, e);
            }
            if (this.owner.on_edit_keydown) {
                this.owner.on_edit_keydown.call(this, this, e);
            }
            if (this.on_edit_keydown) {
                this.on_edit_keydown.call(this, this, e);
            }
        },

        create_edit_form: function() {
            var self = this,
                options,
                container,
                onReady,
                argLen = arguments.length;
            if (argLen) {
                for (var i = 0; i < argLen; i++) {
                    if (!container && arguments[i] instanceof jQuery) {
                        container = arguments[i];
                    } else if (!onReady && typeof arguments[i] === "function") {
                        onReady = arguments[i];
                    } else if (!options) {
                        options = arguments[i];
                    }
                }
            }
            this.edit_form = $("<div></div>").append(this.findTemplate("edit"));
            if (!container) {
                this.edit_form = this.makeFormModal(this.edit_form, options);
            }
            this.show_edit_form('edit_form', {
                container: container,
                beforeShow: function() {
                    if (self.task.on_before_show_edit_form) {
                        self.task.on_before_show_edit_form.call(self, self);
                    }
                    if (self.owner.on_before_show_edit_form && !self.master) {
                        self.owner.on_before_show_edit_form.call(self, self);
                    }
                    if (self.on_before_show_edit_form) {
                        self.on_before_show_edit_form.call(self, self);
                    }
                },
                onShown: function() {
                    if (self.task.on_after_show_edit_form) {
                        self.task.on_after_show_edit_form.call(self, self);
                    }
                    if (self.owner.on_after_show_edit_form && !self.master) {
                        self.owner.on_after_show_edit_form.call(self, self);
                    }
                    if (self.on_after_show_edit_form) {
                        self.on_after_show_edit_form.call(self, self);
                    }
                    if (onReady) {
                        onReady.call(self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_edit_form_close_query) {
                        canClose = self.on_edit_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.owner.on_edit_form_close_query && !self.master) {
                        canClose = self.owner.on_edit_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_edit_form_close_query) {
                        canClose = self.task.on_edit_form_close_query.call(self, self);
                    }
                    return canClose;
                },
                onKeyUp: this.do_on_edit_keyup,
                onKeyDown: this.do_on_edit_keydown
            })
        },

        close_edit_form: function() {
            this.close_form('edit_form');
        },

        create_filter_form: function() {
            var self = this,
                options,
                container,
                onReady,
                argLen = arguments.length;
            if (argLen) {
                for (var i = 0; i < argLen; i++) {
                    if (!container && arguments[i] instanceof jQuery) {
                        container = arguments[i];
                    } else if (!onReady && typeof arguments[i] === "function") {
                        onReady = arguments[i];
                    } else if (!options) {
                        options = arguments[i];
                    }
                }
            }
            this.filter_form = $("<div></div>").append(this.findTemplate("filter"));
            if (!container) {
                this.filter_form = this.makeFormModal(this.filter_form, options);
            }
            this.show_edit_form('filter_form', {
                container: container,
                beforeShow: function() {
                    if (self.task.on_before_show_filter_form) {
                        self.task.on_before_show_filter_form.call(self, self);
                    }
                    if (self.owner.on_before_show_filter_form) {
                        self.owner.on_before_show_filter_form.call(self, self);
                    }
                    if (self.on_before_show_filter_form) {
                        self.on_before_show_filter_form.call(self, self);
                    }
                },
                onShown: function() {
                    if (self.task.on_after_show_filter_form) {
                        self.task.on_after_show_filter_form.call(self, self);
                    }
                    if (self.owner.on_after_show_filter_form && !self.master) {
                        self.owner.on_after_show_filter_form.call(self, self);
                    }
                    if (self.on_after_show_filter_form) {
                        self.on_after_show_filter_form.call(self, self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_filter_form_close_query) {
                        canClose = self.on_filter_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.owner.on_filter_form_close_query) {
                        canClose = self.owner.on_filter_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_filter_form_close_query) {
                        canClose = self.task.on_filter_form_close_query.call(self, self);
                    }
                    return canClose;
                },

            })
        },

        close_filter_form: function() {
            this.close_form('filter_form');
        },

        apply_filter: function() {
            this.open();
            this.close_filter_form();
        },

        get_status_text: function() {
            var result = '',
                status = '';
            this.eachFilter(function(filter, index) {
                if ((filter.visible) && filter.get_value()) {
                    if (filter.field.data_type === consts.BOOLEAN) {
                        if (filter.get_value()) {
                            status += filter.filter_caption + ' ';
                        }
                    } else {
                        if (status) {
                            status += ' ';
                        }
                        status += filter.filter_caption + ': ' + filter.field.get_display_text();
                    }
                }
            });
            if (status) {
                result = language.filter + ' - ' + status;
            }
            return result;
        },

        close_filter: function() {
            this.close_filter_form();
        },

        disable_controls: function() {
            this._disabled_count -= 1;
        },

        enable_controls: function() {
            this._disabled_count += 1;
            if (this.controls_enabled()) {
                this.update_controls(consts.UPDATE_CONTROLS);
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
                state = consts.UPDATE_REFRESH;
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

        create_grid: function(container, options) {
            return new DBGrid(this, container, options);
        },

        create_tree: function(container, parent_field, text_field, parent_of_root_value, options) {
            return new DBTree(this, container, parent_field, text_field, parent_of_root_value, options);
        },


        create_entries: function(container, options) {
            var default_options,
                i, len, col,
                //            colHeight,
                field,
                fields = [],
                cols = [],
                tabindex,
                form;

            default_options = {
                fields: [],
                col_count: 1,
                label_on_top: false,
                row_count: undefined,
                tabindex: undefined
            };

            if (!container) {
                return;
            }

            this.options = $.extend({}, default_options, options);

            if (this.options.fields.length) {
                len = this.options.fields.length;
                for (i = 0; i < len; i++) {
                    field = this.field_by_name(this.options.fields[i])
                    if (this.options.fields[i] && !field) {
                        throw  this.item_name + ' create_entries: there is not a field with field_name - "' + this.options.fields[i] + '"';
                    }
                    fields.push(field);
                }
            } else {
                this.eachField(function(field, i) {
                    if (field.edit_visible && field.edit_index !== -1) {
                        fields.push(field);
                    }
                });
                fields.sort(function(field1, field2) {
                    if (field1.edit_index > field2.edit_index === 0) {
                        return 0;
                    }
                    if (field1.edit_index > field2.edit_index) {
                        return 1;
                    } else {
                        return -1;
                    }
                });
            }
            container.empty();

            form = $("<form></form>").appendTo($("<div></div>").addClass("row-fluid").appendTo(container));
            if (!this.options.label_on_top) {
                form.addClass("form-horizontal");
            }
            len = fields.length;
            for (col = 0; col < this.options.col_count; col++) {
                cols.push($("<div></div>").addClass("span" + 12 / this.options.col_count).appendTo(form));
            }
            tabindex = this.options.tabindex;
            if (!tabindex && this.edit_form) {
                tabindex = this.edit_form.tabindex;
                this.edit_form.tabindex += len;
            }
            if (!this.options.row_count) {
                this.options.row_count = Math.ceil(len / this.options.col_count);
            }
            for (i = 0; i < len; i++) {
                new DBEntry(fields[i], i + tabindex, cols[Math.floor(i / this.options.row_count)],
                    this.options.label_on_top);
            }
        },

        create_filter_entries: function(container, options) {
            var default_options,
                i, len, col,
                filters = [],
                cols = [],
                tabindex,
                form;

            default_options = {
                    filters: [],
                    col_count: 1,
                    label_on_top: false,
                    tabindex: undefined
                },

                this.options = $.extend({}, default_options, options);

            if (this.options.filters.length) {
                len = this.options.filters.length;
                for (i = 0; i < len; i++) {
                    filters.push(this.filter_by_name(this.options.filters[i]));
                }
            } else {
                this.eachFilter(function(filter, i) {
                    if (filter.visible) {
                        filters.push(filter);
                    }
                });
            }
            container.empty();
            form = $("<form></form>").appendTo($("<div></div>").addClass("row-fluid").appendTo(container));
            if (!this.options.label_on_top) {
                form.addClass("form-horizontal");
            }
            len = filters.length;
            for (col = 0; col < this.options.col_count; col++) {
                cols.push($("<div></div>").addClass("span" + 12 / this.options.col_count).appendTo(form));
            }
            tabindex = this.options.tabindex;
            if (!tabindex && this.filter_form) {
                tabindex = this.filter_form.tabindex;
                this.filter_form.tabindex += len;
            }
            for (i = 0; i < len; i++) {
                new DBEntry(filters[i].field, i + 1, cols[Math.floor(i % this.options.col_count)],
                    this.options.label_on_top, filters[i].filter_caption);
            }
        },

        set_lookup_field_value: function(gridClicked) {
            if (this.record_count()) {
                var lookup_field = this.lookup_field,
                    object_field = this.field_by_name(lookup_field.lookup_field),
                    lookup_value = null,
                    lookup_field_item = this.lookup_field.owner,
                    slave_field_values = {},
                    ids = [],
                    self = this;

                if (object_field) {
                    lookup_value = object_field.get_value();
                }
                //        lookup_field.do_before_changed();
                if (this.lookup_selected_ids) {
                    lookup_field.value = null;
                    for (var id in this.lookup_selected_ids) {
                        if (this.lookup_selected_ids.hasOwnProperty(id)) {
                            ids.push(parseInt(id, 10));
                        }
                    }
                    if (ids.length) {
                        lookup_field.value = ids;
                    } else if (gridClicked) {
                        lookup_field.value = [this.id.value]
                    } else {
                        lookup_field.value = null;
                    }
                } else {
                    if (lookup_field_item) {
                        lookup_field_item.eachField(function(field) {
                            if (field.master_field === lookup_field) {
                                object_field = self.field_by_name(field.lookup_field)
                                if (object_field) {
                                    slave_field_values[field.field_name] = object_field.get_value();
                                }
                            }
                        })
                    }
                    lookup_field.set_value(this.id.get_value(), lookup_value, slave_field_values, this);
                }
            }
            if (this.is_lookup_item) {
                this.close_view_form();
            }
        },

        find_default_field: function() {
            var i = 0,
                len = this.fields.length;
            for (; i < len; i++) {
                if (this.fields[i].is_default) {
                    return this.fields[i];
                }
            }
        },

        set_edit_fields: function(fields, captions) {
            var i = 0,
                len = fields.length,
                field;
            this.eachField(function(field, i) {
                field.edit_visible = false;
                field.edit_index = -1;
            });
            for (; i < len; i++) {
                field = this.field_by_name(fields[i]);
                if (field) {
                    field.edit_visible = true;
                    field.edit_index = i + 1;
                    if (captions) {
                        try {
                            field.field_caption = captions[i];
                        }
                        catch (e) {
                        }
                    }
                } else {
                    throw this.item_name + " set_edit_fields: no field for field_name " + field[i];
                }
            }
        },

        set_view_fields: function(fields, captions) {
            var i = 0,
                len = fields.length,
                field;
            this.eachField(function(field, i) {
                field.view_visible = false;
                field.view_index = -1;
            });
            for (; i < len; i++) {
                field = this.field_by_name(fields[i]);
                if (field) {
                    field.view_visible = true;
                    field.view_index = i + 1;
                    if (captions) {
                        try {
                            field.field_caption = captions[i];
                        }
                        catch (e) {
                        }
                    }
                } else {
                    throw this.item_name + " set_edit_fields: no field for field_name " + field[i];
                }
            }
        },

        round: function(num, dec) {
            //        return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
            return Number(num.toFixed(dec));
        },

        refresh_record: function(callback) {
            var self = this,
                fields = [],
                copy = this.copy({
                    filters: false,
                    details: false,
                    handlers: false
                });
            if (this.id.value !== null) {
                self.eachField(function(field) {
                    fields.push(field.field_name)
                })
                copy.open({fields: fields, where: {id: this.id.value}})
                if (copy.record_count() === 1) {
                    self._records[self.rec_no] = copy._records[0].slice(0);
                    self.update_controls(consts.UPDATE_CANCEL);
                    if (callback) {
                        callback.call(this);
                    }
                }
            }
        }
    });

    /**********************************************************************/
    /*                           Report class                             */
    /**********************************************************************/

    Report.prototype = new AbsrtactItem();

    function Report(owner, ID, item_name, caption, visible, type) {
        AbsrtactItem.call(this, owner, ID, item_name, caption, visible, type);
        if (this.task && !(item_name in this.task)) {
            this.task[item_name] = this;
        }
        this._fields = [];
        this.params = this._fields;
        this.params_row = [];
        this._state = consts.STATE_EDIT;
    }

    $.extend(Report.prototype, {
        constructor: Report,

        set_state: function(value) {
            if (this._state !== value) {
                this._state = value;
            }
        },

        get_state: function() {
            return this._state;
        },

        initAttr: function(info) {
            var i,
                params = info[6],
                len;
            if (params) {
                len = params.length;
                for (i = 0; i < len; i++) {
                    new Param(this, params[i]);
                }
            }
        },

        bindItem: function() {
            var i = 0,
                param,
                len = this.params.length;
            for (i = 0; i < len; i++) {
                this.params_row.push(null);
                this.params[i].bind_index = i;
            }
            for (i = 0; i < len; i++) {
                param = this.params[i];
                if (param.lookup_item && (typeof param.lookup_item === "number")) {
                    param.lookup_item = this.task.item_by_ID(param.lookup_item);
                }
                this.params_row.push(null);
                param.lookup_index = this.params_row.length - 1;
            }
        },

        eachParam: function(callback) {
            var i = 0,
                len = this.params.length,
                value;
            for (; i < len; i++) {
                value = callback.call(this.params[i], i, this.params[i]);
                if (value === false) {
                    break;
                }
            }
        },

        eachField: function(callback) {
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

        create_params_form: function() {
            var self = this,
                options,
                container,
                onReady,
                argLen = arguments.length;
            if (argLen) {
                for (var i = 0; i < argLen; i++) {
                    if (!container && arguments[i] instanceof jQuery) {
                        container = arguments[i];
                    } else if (!onReady && typeof arguments[i] === "function") {
                        onReady = arguments[i];
                    } else if (!options) {
                        options = arguments[i];
                    }
                }
            }
            this.params_form = $("<div></div>").append(this.findTemplate("params"));
            if (!container) {
                this.params_form = this.makeFormModal(this.params_form, options);
            }
            this.show_edit_form('params_form', {
                container: container,
                beforeShow: function() {
                    if (self.task.on_before_show_params_form) {
                        self.task.on_before_show_params_form.call(self, self);
                    }
                    if (self.owner.on_before_show_params_form) {
                        self.owner.on_before_show_params_form.call(self, self);
                    }
                    if (self.on_before_show_params_form) {
                        self.on_before_show_params_form.call(self, self);
                    }
                },
                onShown: function() {
                    if (self.task.on_after_show_params_form) {
                        self.task.on_after_show_params_form.call(self, self);
                    }
                    if (self.owner.on_after_show_params_form) {
                        self.owner.on_after_show_params_form.call(self, self);
                    }
                    if (self.on_after_show_params_form) {
                        self.on_after_show_params_form.call(self, self);
                    }
                },
                onHide: function(e) {
                    var mess,
                        canClose;
                    if (self.on_params_form_close_query) {
                        canClose = self.on_params_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.owner.on_params_form_close_query) {
                        canClose = self.owner.on_params_form_close_query.call(self, self);
                    }
                    if (canClose === undefined && self.task.on_params_form_close_query) {
                        canClose = self.task.on_params_form_close_query.call(self, self);
                    }
                    return canClose;
                },
            })
        },

        close_params_form: function() {
            this.close_form('params_form');
        },

        print_report: function() {
            var i = 0,
                len = arguments.length,
                showParamsForm = true,
                callback;
            for (; i < len; i++) {
                switch (typeof arguments[i]) {
                    case "function":
                        callback = arguments[i];
                        break;
                    case "boolean":
                        showParamsForm = arguments[i];
                        break;
                }
            }
            if (!showParamsForm) {
                this.eachParam(function(i, param) {
                    if (param.edit_visible) {
                        showParamsForm = true;
                        return false;
                    }
                });
            }
            if (showParamsForm) {
                this.create_params_form();
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
                host = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port: ''),
                i,
                len,
                param_values = [];
            if (this.checkParams()) {
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
                this.send_request('print_report', [param_values, host, this.extension], function(url) {
                    var ext,
                        timeOut,
                        win;
                    if (url) {
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
                                            win.onfocus=function() { win.close();}
                                        },
                                        1000
                                    );
                                }
                                //~
                                //~ win.addEventListener('load', function() {win.print(false);});
                                //~ timeOut = setTimeout(function() {
                                        //~ win.close();
                                    //~ },
                                    //~ 100
                                //~ );
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

        create_params: function(container, options) {
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
                    tabindex: undefined
                },

                this.options = $.extend({}, default_options, options);

            if (this.options.params.length) {
                len = this.options.params.length;
                for (i = 0; i < len; i++) {
                    params.push(this.param_by_name(this.options.params[i]));
                }
            } else {
                this.eachParam(function(i, param) {
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
            form = $("<form></form>").appendTo($("<div></div>").addClass("row-fluid").appendTo(container));
            if (!this.options.label_on_top) {
                form.addClass("form-horizontal");
            }
            len = params.length;
            for (col = 0; col < this.options.col_count; col++) {
                cols.push($("<div></div>").addClass("span" + 12 / this.options.col_count).appendTo(form));
            }
            tabindex = this.options.tabindex;
            if (!tabindex && this.params_form) {
                tabindex = this.params_form.tabindex;
                this.params_form.tabindex += len;
            }
            for (i = 0; i < len; i++) {
                new DBEntry(params[i], i + tabindex, cols[Math.floor(i % this.options.col_count)], this.options.label_on_top)
            }
        }
    });

    /**********************************************************************/
    /*                            Detail class                            */
    /**********************************************************************/

    Detail.prototype = new Item();
    Detail.prototype.constructor = Detail;

    function Detail(owner, ID, item_name, caption, visible, type) {
        Item.call(this, owner, ID, item_name, caption, visible, type);

        //~ AbsrtactItem.call(this, owner, ID, item_name, caption, visible, type);
        //~ this.fields = [];
        //~ this.filters = [];
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
            },
            set: function(new_value) {
                this.set_display_text(new_value);
            }
        });
        Object.defineProperty(this, "lookup_text", {
            get: function() {
                return this.get_lookup_text();
            },
            set: function(new_value) {
                this.set_lookup_text(new_value);
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
                return this.get_read_only();
            },
            set: function(new_value) {
                this.set_read_only(new_value);
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
            "view_visible",
            "view_index",
            "edit_visible",
            "edit_index",
            "_read_only",
            "_expand",
            "_word_wrap",
            "field_size",
            "is_default",
            "calculated",
            "editable",
            "_alignment",
            "value_list"
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
            if (this.filter) {
                return this.filter.owner._filter_row;
            } else if (this.report) {
                return this.report.params_row;
            } else {
                if (this.owner._records) {
                    return this.owner._records[this.owner.get_rec_no()];
                }
            }
        },

        get_data: function() {
            var row;
            row = this.get_row();
            if (row && (this.bind_index >= 0)) {
                return row[this.bind_index];
            } else {
                return null;
            }
        },

        set_data: function(value) {
            var row;
            row = this.get_row();
            if (row && (this.bind_index >= 0)) {
                row[this.bind_index] = value;
            }
        },

        get_lookup_data: function() {
            var row;
            if (this.lookup_index) {
                row = this.get_row();
                if (row && (this.lookup_index >= 0)) {
                    return row[this.lookup_index];
                }
            } else {
                return null;
            }
        },

        set_lookup_data: function(value) {
            var row;
            if (this.lookup_index) {
                row = this.get_row();
                if (row && (this.lookup_index >= 0)) {
                    row[this.lookup_index] = value;
                }
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
                                result = language['yes']
                            } else {
                                result = language['no']
                            }
                            break;
                    }
                } else {
                    result = "";
                }
            } catch (e) {
                result = '';
                error = this.field_caption + ": " + this.type_error();
                this.do_on_error(error);
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
                                }
                                else {
                                    this.set_value(false);
                                }
                            }
                            else {
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
                    this.do_on_error(error);
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
            return result;
        },

        get_value: function() {
            var value = this.get_raw_value();
            if (value === null) {
                switch (this.data_type) {
                    case consts.TEXT:
                        value = '';
                        break;
                    case consts.INTEGER:
                        value = 0;
                        break;
                    case consts.FLOAT:
                        value = 0;
                        break;
                    case consts.CURRENCY:
                        value = 0;
                        break;
                    case consts.BOOLEAN:
                        value = false;
                        break;
                }
            } else {
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

        do_on_change_lookup_field: function(lookup_value, slave_field_values) {
            var self = this;
            if (lookup_value === undefined) {
                lookup_value = null;
            }
            if (this.lookup_item) {
                if (this.master_field) {
                    this.master_field.do_on_change_lookup_field(null);
                } else {
                    this.set_lookup_data(lookup_value);
                    if (this.owner) {
                        this.owner.eachField(function(field, i) {
                            if (self === field.master_field && slave_field_values !== undefined) {
                                field.set_lookup_data(slave_field_values[field.field_name]);
                                field.update_controls();
                            }
                        });
                    }
                }
            }
        },

        do_before_changed: function(new_value, new_lookup_value) {
            if (this.owner && !((this.owner.get_state() === consts.STATE_INSERT) || (this.owner.get_state() === consts.STATE_EDIT))) {
                throw this.owner.item_name + ' is not in edit or insert mode';
            }
            if (this.owner && this.owner.on_before_field_changed) {
                return this.owner.on_before_field_changed.call(this.owner, this, new_value, new_lookup_value);
            }
        },

        set_value: function(value, lookup_value, slave_field_values, lookup_item) {
            var error;
            if (((this.field_name === 'id' && this.value) || this.field_name === 'deleted') && this.owner && !this.filter && (self.value !== value)) {
                throw this.owner.item_name + ': can not change value of the system field - ' + this.field_name;
            }
            this.new_value = null;
            if (value !== null) {
                this.new_value = value;
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
                }
            }
            if (this.get_raw_value() !== this.new_value) {
                if (this.do_before_changed(this.new_value, lookup_value) !== false) {
                    try {
                        this.set_data(this.new_value);
                    } catch (e) {
                        error = this.field_caption + ": " + this.type_error();
                        this.do_on_error(error);
                    }
                    this.new_value = null;
                    this.do_on_change_lookup_field(lookup_value, slave_field_values);
                    this.set_modified(true);
                    this.do_after_changed(lookup_item);
                }
            } else if (lookup_value && lookup_value !== this.get_lookup_value()) {
                this.do_on_change_lookup_field(lookup_value, slave_field_values);
                this.do_after_changed(lookup_item);
            }
        },

        set_modified: function(value) {
            if (this.owner && this.owner.set_modified && !this.calculated) {
                this.owner.set_modified(value);
            }
        },

        get_lookup_data_type: function() {
            if (this.lookup_item) {
                return this.lookup_item._field_by_name(this.lookup_field).data_type;
            } else {
                return this.data_type
            }
        },

        get_lookup_value: function() {
            var value = null;
            if (this.lookup_item && this.get_value()) {
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
            else {
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

        set_lookup_text: function(text) {
            if (this.lookup_item) {
                if (text) {
                    switch (this.get_lookup_data_type()) {
                        case consts.DATE:
                            text = this.str_to_date(text);
                            break;
                        case consts.DATETIME:
                            text = this.str_to_datetime(text);
                            break;
                        case consts.FLOAT:
                            text = this.str_to_float(text);
                            break;
                        case consts.CURRENCY:
                            text = this.str_to_cur(text);
                            break;
                    }
                }
                this.set_lookup_data(text);
                this.update_controls();
            } else {
                this.set_text(text);
            }
        },

        get_display_text: function() {
            var res,
                result = '';
            if (this.filter && this.filter.filter_type === consts.FILTER_IN && this.filter.field.lookup_item && this.filter.value) {
                result = language.items_selected.replace('%d', this.filter.value.length);
            } else if (this.lookup_item) {
                result = this.get_lookup_text();
            } else if (this.value_list) {
                try {
                    result = this.value_list[this.get_value() - 1];
                } catch (e) {}
            } else {
                if (this.data_type === consts.CURRENCY) {
                    if (this.raw_value !== null) {
                        result = this.cur_to_str(this.get_value());
                    }
                } else {
                    result = this.get_text();
                }
            }
            if (this.owner && this.owner.on_get_field_text) {
                if (!this.on_get_field_text_called) {
                    this.on_get_field_text_called = true;
                    try {
                        res = this.owner.on_get_field_text.call(this.owner, this);
                        if (res !== undefined) {
                            result = res;
                        }
                    }
                    finally {
                        this.on_get_field_text_called = false;
                    }
                }
            }
            return result;
        },

        set_read_only: function(value) {
            this._read_only = value;
            this.update_controls();
        },

        get_read_only: function() {
            var result = this._read_only;
            if (this.owner && this.owner.parent_read_only && this.owner.get_read_only()) {
                result = this.owner.get_read_only();
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
                this.do_on_error(this.field_caption + ': ' + language.invalid_length.replace('%d', this.field_size));
            }
            return true;
        },

        check_reqired: function() {
            if (!this.required) {
                return true;
            } else if (this.get_raw_value() !== null) {
                return true;
            } else {
                this.do_on_error(this.field_caption + ': ' + language.value_required);
            }
        },

        check_valid: function() {
            var err;
            if (this.check_reqired()) {
                if (this.check_type()) {
                    if (this.owner && this.owner.on_field_validate) {
                        err = this.owner.on_field_validate.call(this.owner, this);
                        if (err) {
                            this.do_on_error(err);
                            return;
                        }
                    }
                    return true;
                }
            }
        },

        do_after_changed: function(lookup_item) {
            if (this.owner && this.owner.on_field_changed) {
                this.owner.on_field_changed.call(this.owner, this, lookup_item);
            }
            if (this.filter && this.filter.owner.on_filter_changed) {
                this.filter.owner.on_filter_changed.call(this.filter.owner, this.filter);
            }
            this.update_controls();
        },

        do_on_error: function(error) {
            throw error;
        },

        system_field: function() {
            if (this.field_name === 'id' || this.field_name === 'deleted'
                || this.field_name === 'owner_id' || this.field_name === 'owner_rec_id') {
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
                sign = ch === '+' || ch === '-';
            if (this.data_type === consts.INTEGER) {
                if (!isDigit && !sign) {
                    return false;
                }
            }
            if (this.data_type === consts.FLOAT || this.data_type === consts.CURRENCY) {
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
            var result = $.trim(val);
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
            return result;
        },

        int_to_str: function(value) {
            return value.toString();
        },

        float_to_str: function(value) {
            var str = ('' + value.toFixed(6)).replace(".", settings.DECIMAL_POINT),
                i = str.length - 1,
                result = '';
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
            return result;

        },

        date_to_str: function(value) {
            return this.format_date_to_string(value, settings.D_FMT);
        },

        datetime_to_str: function(value) {
            return this.format_date_to_string(value, settings.D_T_FMT);
        },

        cur_to_str: function(value) {
            var point,
                dec,
                digits,
                i,
                d,
                count = 0,
                len,
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

        select_from_view_form: function() {
            var copy = this.lookup_item.copy();
            copy.is_lookup_item = true;
            if (this.filter && this.filter.filter_type === consts.FILTER_IN && this.filter.field.lookup_item) {
                copy.lookup_selected_ids = {};
                if (this.filter.value) {
                    for (var i = 0; i < this.filter.value.length; i++) {
                        copy.lookup_selected_ids[this.filter.value[i]] = true;
                    }
                }
            }
            copy.details_active = false;
            copy.lookup_field = this;
            if (this.owner && this.owner.on_param_lookup_item_show) {
                this.owner.on_param_lookup_item_show.call(this.owner, this, copy);
            }
            if (this.owner && this.owner.on_field_lookup_item_show) {
                this.owner.on_field_lookup_item_show.call(this.owner, this, copy);
            }
            if (this.filter && this.filter.owner.on_filter_lookup_item_show) {
                this.filter.owner.on_filter_lookup_item_show.call(this.filter.owner, this.filter, copy);
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
                field = this.owner._field_by_name(this.field_name);
                this.field = new Field();
                this.field.set_info(field.get_info());
                this.field.read_only = false;
                this.field.filter = this;
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
    }

    Filter.prototype = {
        constructor: Filter,

        attr: [
            "filter_name",
            "filter_caption",
            "field_name",
            "filter_type",
            "data_type",
            "visible"
        ],

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
            return this.field.get_raw_value();
        },

        set_value: function(value, lookup_value) {
            this.field.set_value(value, lookup_value);
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
        this.report = owner;
        this.edit_value = null;
        this.param_lookup_value = null;
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
            this.$element = $('<div class="treeview DBTree" tabindex="0" style="overflow-x:auto; overflow-y:auto;"></div>')
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
//                self.select_node(self.selected_node);
            });
            this.$element.on('keyup', function(e) {
                self.keyup(e);
            })
            this.$element.on('keydown', function(e) {
                self.keydown(e);
            })
            if (item.get_active() && this.$container.width()) {
                this.build();
            }
        },

        form_closing: function() {
            var $modal = this.$element.closest('.modal');
            if ($modal) {
                return $modal.data('closing')
            }
            return false;
        },

        height: function(value) {
            if (value) {
                this.$element.height(value);
            }
            else {
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
                    this.syncronize();
                    break;
                case consts.UPDATE_CLOSE:
                    this.$element.empty();
                    break;
                case consts.UPDATE_REFRESH:
                    this.build();
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
                        }
                        else {
                            $li = this.selected_node.parent().parent()
                            if ($li.length && $li.prop("tagName") === "LI") {
                                this.select_node($li);
                            }
                        }
                        break;
                        break;
                    case 40: //down
                        e.preventDefault();
                        if (this.selected_node.hasClass('parent') && !this.selected_node.hasClass('collapsed')) {
                            $li = this.selected_node.find('ul:first li:first')
                            if ($li.length) {
                                this.select_node($li);
                            }
                        }
                        else {
                            $li = this.selected_node.next();
                            if ($li.length) {
                                this.select_node($li);
                            }
                            else {
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
                bullet = '&nbsp',
                parent_class = "",
                collapsed_class = "",
                children = this.child_nodes[id + ''];
                if (children && children.length) {
                    bullet = '+';
                    parent_class = ' parent';
                    collapsed_class = 'collapsed';
                }
                li = '<li class="' + collapsed_class + parent_class +'" style="list-style: none" data-rec="' + rec + '">' +
                    '<div><span class="tree-bullet">' + bullet + '</span>' +
                    '&nbsp&nbsp<span class="tree-text">' +  text + '<span></div>';
                tree += li;
                if (children && children.length) {
                    tree += '<ul style="display: none">';
                    tree = this.build_child_nodes(tree, children);
                    tree += '</ul>';
                }tree += '</li>';
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
                array.push({'id': id_field.value, 'text': text_field.display_text,
                    'rec': clone.rec_no});
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
                clone.set_rec_no(rec);
                this.item._cur_row = rec;
                $li.data("record", clone._records[rec]);
                info = clone.rec_controls_info();
                info[this.id] = $li.get();
                if (this.options.node_callback) {
                    this.options.node_callback($li, this.item);
                }
            }
            this.select_node($lis.eq(0));

            this.$element.on('click', 'li.parent > div span.tree-bullet', function(e) {
                var $span = $(this),
                    $li = $span.parent().parent(),
                    $ul;
                    self.toggle_expanded($li);
            });
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
                    $span.text('+');
                }
                else {
                    $span.text('-');
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

        select_node: function($li) {
            var self = this,
                $parent,
                rec;
            if (this.selected_node) {
                this.selected_node.removeClass('selected selected-focused');
            }
            if ($li && (!this.selected_node || $li.get(0) !== this.selected_node.get(0))) {
                this.selected_node = $li;
                rec = this.item._records.indexOf($li.data("record"));
                if (rec !== this.item.rec_no) {
                    this.item.set_rec_no(rec);
                }
                $parent = this.selected_node.parent().parent()
                if ($parent.prop("tagName") === "LI") {
                    this.expand($parent);
                }
            }
            if (this.is_focused()) {
                this.selected_node.addClass('selected-focused');
            }
            else {
                this.selected_node.addClass('selected');
            }
            this.update_selected_node(this.selected_node);
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

        changed: function() {
        },
    }

    /**********************************************************************/
    /*                            DBGrid class                            */
    /**********************************************************************/

    function DBGrid(item, container, options) {
        this.init(item, container, options);
    }

    DBGrid.prototype = {
        constructor: DBGrid,

        init: function(item, container, options) {
            var self = this,
                default_options = {
                    height: 480,
                    fields: [],
                    column_width: {},
                    row_count: 0,
                    word_wrap: false,
                    title_word_wrap: false,
                    expand_selected_row: 0,
                    auto_fit_width: true,
                    multi_select: false,
                    multi_select_title: '',
                    multi_select_colum_width: undefined,
                    multi_select_get_selected: undefined,
                    multi_select_set_selected: undefined,
                    multi_select_select_all: undefined,
                    tabindex: 0,
                    striped: true,
                    dblclick_edit: true,
                    on_dblclick: undefined,
                    on_pagecount_update: undefined,
                    editable: false,
                    always_show_editor: false,
                    keypress_edit: true,
                    editable_fields: undefined,
                    selected_field: undefined,
                    append_on_lastrow_keydown: false,
                    sortable: false,
                    sort_fields: undefined,
                    row_callback: undefined,
                    title_callback: undefined,
                    show_footer: undefined,
                    pagination_container: undefined
                };

            this.item = item;
            if (!this.item.auto_loading) {
                default_options.striped = false;
            }
            this.id = item.task.gridId++;
            this.$container = container;
            this.options = $.extend({}, default_options, options);
            this.editMode = this.options.always_show_editor;
            this._sorted_fields = [];
            this._multiple_sort = false;
            this.on_dblclick = this.options.on_dblclick;
            if (this.item.is_lookup_item && this.item.lookup_selected_ids) {
                this.options.multi_select = true;
                this.options.multi_select_get_selected = function(item) {
                        return item.lookup_selected_ids[item.id.value]
                    },
                    this.options.multi_select_set_selected = function(item, value) {
                        if (value) {
                            item.lookup_selected_ids[item.id.value] = true;
                        } else {
                            delete item.lookup_selected_ids[item.id.value];
                        }
                    }
            }
            this.page = 0;
            this.recordCount = 0;
            this.cellWidths = {};
            this.autoFieldWidth = true;
            this.fieldWidthUpdated = false;

            this.initFields();

            this.$element = $('<div class="DBGrid" style="overflow-x:auto;"></div>');
            this.$element.data('grid', this);
            this.item.controls.push(this);
            this.$element.bind('destroyed', function() {
                self.item.controls.splice(self.item.controls.indexOf(self), 1);
            });
            this.$element.appendTo(this.$container);
            this.createTable();
            if (item.get_active()) {
                setTimeout(function() {
                        if (self.$container.width()) {
                            self.initRows();
                        }
                    },
                    0
                );
            }
        },


        initFields: function() {
            var i = 0,
                len,
                field;
            this.fields = [];
            if (this.options.fields.length) {
                if (this.options.fields instanceof Array) {
                    len = this.options.fields.length;
                    for (; i < len; i++) {
                        this.fields.push(this.item.field_by_name(this.options.fields[i]));
                    }
                } else {
                    this.autoFieldWidth = false;
                    for (var field in this.options.fields) {
                        if (this.options.fields.hasOwnProperty(field)) {
                            this.fields.push(this.item.field_by_name(field));
                            this.setCellWidth(field, this.options.fields[field]);
                        }
                    }
                }
            } else {
                len = this.item.fields.length;
                for (; i < len; i++) {
                    if (this.item.fields[i].view_index !== -1) {
                        this.fields.push(this.item.fields[i]);
                    }
                }
                this.fields.sort(function(field1, field2) {
                    if (field1.view_index > field2.view_index === 0) {
                        return 0;
                    }
                    if (field1.view_index > field2.view_index) {
                        return 1;
                    } else {
                        return -1;
                    }
                });
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
                $thNext,
                delta = 0,
                mouseX,
                i,
                table,
                element,
                row,
                cell,
                div,
                scrollDivHeight,
                elementHeight;
            this.colspan = this.fields.length;
            if (this.options.multi_select) {
                this.colspan += 1;
            }
            this.$element.append($(
                '<table class="outer-table">' +
                '   <thead>' +
                '       <tr><th>&nbsp</th></tr>' +
                '   </thead>' +
                '   <tfoot>' +
                '       <tr><th>&nbsp</th></tr>' +
                '   </tfoot>' +
                '   <tr>' +
                '       <td id="top-td" style="padding: 0; border: 0" colspan=' + this.colspan + '>' +
                '           <div class="overlay-div" style="height:100px; width:100%; overflow-y:auto; overflow-x:hidden;">' +
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
                self.clicked(e, this);
            });

            if (!this.options.word_wrap) {
                this.$table.on('mouseenter', 'div', function() {
                    var $this = $(this);
                    if (this.offsetHeight < (this.scrollHeight - 2) ||
                        this.offsetWidth < (this.scrollWidth - 2)) {
                        $this.tooltip({
                                'placement': 'right',
                                'title': $this.text()
                            })
                            .on('hide', function(e) {
                                e.stopPropagation()
                            })
                            .on('hidden', function(e) {
                                e.stopPropagation()
                            })
                            .on('show', function(e) {
                                e.stopPropagation()
                            })
                            .on('shown', function(e) {
                                e.stopPropagation()
                            })
                            .eq(0).tooltip('show');
                    }
                });
            }

            if (this.options.multi_select) {
                var self = this;
                this.$table.on('mousedown', 'td input.multi_select', function(e) {
                    var $this = $(this),
                        checked = $this.is(':checked');
                    e.preventDefault();
                    e.stopPropagation();
                    self.clicked(e, $this.closest('td'));
                    if (self.options.multi_select_set_selected) {
                        self.options.multi_select_set_selected.call(self.item, self.item, !checked);
                        self.update_select_all_checkbox();
                    }
                });
            }

            if (this.options.multi_select_select_all) {
                var self = this;
                this.$outer_table.on('click', 'th input.multi_select', function(e) {
                    self.options.multi_select_select_all.call(self.item, self.item, $(this).is(':checked'));
                });
            }

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
                    }
                    else {
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
                    fields = [],
                    new_fields = [],
                    desc = [],
                    index,
                    desc = false,
                    next_field_name;
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
                } else if (self.options.sortable && //!self.item.master &&
                    (!self.options.sort_fields || self.options.sort_fields.indexOf(field_name) !== -1)) {

                    if (e.ctrlKey) {
                        if (!self._multiple_sort) {
                            self._multiple_sort = true;
                        }
                    }
                    else {
                        if (self._multiple_sort) {
                            self._sorted_fields = [];
                            self._multiple_sort = false;
                        }
                    }
                    desc = [];
                    fields = [];
                    for (var i = 0; i < self._sorted_fields.length; i++) {
                        cur_field_name = self._sorted_fields[i];
                        if (cur_field_name.charAt(0) === '-') {
                            desc.push(true);
                            fields.push(cur_field_name.substring(1));
                        }
                        else {
                            desc.push(false);
                            fields.push(cur_field_name);
                        }
                    }
                    if (self._multiple_sort) {
                        index = jQuery.inArray(field_name, fields);
                        if (index === -1) {
                            fields.push(field_name);
                            desc.push(false);
                        }
                        else {
                            desc[index] = !desc[index];
                        }
                    }
                    else {
                        if (fields.length && fields[0] === field_name) {
                            desc[0] = !desc[0];
                        }
                        else {
                            fields = [field_name];
                            desc = [false];
                        }
                    }
                    self._sorted_fields = [];
                    for (var i = 0; i < fields.length; i++) {
                        field_name = fields[i];
                        if (desc[i]) {
                            field_name = '-' + field_name;
                        }
                        self._sorted_fields.push(field_name);
                    }
                    if (self.item.master) {
                        self.item.sort(self._sorted_fields);
                    }
                    else {
                        self.item._open_params.__order = self.item.get_order_by_list(self._sorted_fields);
                        self.item.open({params: self.item._open_params});
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

            element = this.$element.clone()
                .css("float", "left")
                .css("position", "absolute")
                .css("top", -1000);
            element.width(this.$container.width())
            this.fillTitle(element);
            this.createFooter(element);
            table = element.find("table.inner-table");
            if (this.options.multi_select) {
                row = $('<tr><td><div><input type="checkbox"></div></td><td><div>W</div></td></tr>');
            } else {
                row = $("<tr><td><div>W</div></td></tr>");
            }
            for (i = 0; i < 10; i++) {
                table.append(row.clone());
            }
            $('body').append(element);
            this.rowHeight = table.height() / 10;
            this.textHeight = table.find('div').outerHeight();
            elementHeight = element.outerHeight();
            scrollDivHeight = element.find('div.overlay-div').height();
            element.remove();

            this.$scroll_div.height(this.options.height - (elementHeight - scrollDivHeight));

            if (!this.options.row_count && this.item.auto_loading) {
                if (this.options.expand_selected_row && !this.options.word_wrap) {
                    scrollDivHeight = this.$scroll_div.height() - this.rowHeight - (this.options.expand_selected_row - 1) * this.textHeight - 1;
                    this.row_count = Math.floor(scrollDivHeight / this.rowHeight) + 1;
                }
                else {
                    this.row_count = Math.floor((this.$scroll_div.height() - 1) / this.rowHeight);
                }
                if (this.row_count <= 0) {
                    this.row_count = 1;
                }
                this.item.limit = this.row_count;
            }
        },

        createPager: function($element) {
            var self = this,
                $pagination,
                $pager,
                tabindex,
                pagerWidth;
            if (this.item.auto_loading) {
                tabindex = -1;
                //~ if (this.options.tabindex > 0) {
                //~ tabindex = this.options.tabindex + 1;
                //~ }
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
                this.$pageCount = $pagination.find('#page-count');
                this.$pageCount.text(language.of + '1000000');
                $pager = $pagination.find('#pager').clone()
                    .css("float", "left")
                    .css("position", "absolute")
                    .css("top", -1000);
                $("body").append($pager);
                pagerWidth = $pager.width();
                $pager.remove();
                if (this.options.pagination_container) {
                    this.options.pagination_container.empty();
                    this.options.pagination_container.append($pagination);
                }
                else {
                    if ($element) {
                        $element.find('tfoot').append($pagination);
                    }
                    else {
                        this.$element.find('tfoot').append($pagination);
                    }
                }
                this.$pageCount.text(language.of + ' ');
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
                    if (!this.options.always_show_editor) {
                        this.editMode = false;
                    }
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
                //~ if (this.$table.modalCanFocus()) {
                    //~ this.$table.focus();
                //~ }
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
                //~ try {
                    //~ if (!this.item.is_changing()) {
                        //~ this.item.edit();
                    //~ }
                //~ } catch (e) {
                    //~ return
                //~ }
                this.editMode = true;
                this.editor = new DBGridEntry(this, this.selectedField);
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
//                this.syncColWidth();

                if (this.is_focused()) {
                    if (this.editor.$input.modalCanFocus()) {
                        this.editor.$input.focus();
                    }
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
                field,
                heading,
                div,
                cell,
                input,
                field_name,
                order_fields = {},
                title = '',
                cellWidth;
            if ($element === undefined) {
                $element = this.$element
            }

            len = this._sorted_fields.length;
            for (i = 0; i < len; i++) {
                field_name = this._sorted_fields[i];
                if (field_name.charAt(0) === '-') {
                    order_fields[field_name.substring(1)] = 'icon-arrow-down';
                }
                else {
                    order_fields[field_name] = 'icon-arrow-up';
                }
            }

            heading = $element.find("table.outer-table thead tr:first");
            heading.empty();
            if (this.options.multi_select) {
                if (this.options.multi_select_select_all) {
                    input = $('<input class="multi_select" type="checkbox">');
                }
                else if (this.options.multi_select_title) {
                    title = this.options.multi_select_title;
                }
                div = $('<div class="text-center multi_select" style="overflow: hidden">' + title + '</div>')
                if (input) {
                    div.append(input);
                }
                cell = $('<th class="bottom-border multi_select"></th>').append(div);
                cellWidth = this.getCellWidth('multi_select');
                if (cellWidth && this.fields.length) {
                    cell.width(cellWidth);
                    div.width(cellWidth);
                }
                heading.append(cell);
            }
            len = this.fields.length;
            for (i = 0; i < len; i++) {
                field = this.fields[i];
                div = $('<div class="text-center ' + field.field_name +
                    '" style="overflow: hidden"><p style="vertical-align: middle; margin: 0;">' +
                    field.field_caption + '</p></div>');
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
            if (this.options.multi_select) {
                div = $('<div class="text-center multi_select" style="overflow: hidden"></div>')
                cell = $('<th class="multi_select"></th>').append(div);
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

        initRows: function() {
            if (this.item.offset === 0) {
                this.initFields();
                if (this.item.auto_loading) {
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
                return $modal.data('closing')
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
                    this.initRows();
                    break;
                case consts.UPDATE_CANCEL:
                    this.refreshRow();
                    break;
                case consts.UPDATE_APPEND:
                    row = this.addNewRow();
                    this.$table.append(row);
                    this.syncronize();
                    if (this.item.controls_enabled() && this.item.record_count() === 1) {
                        this.resize();
                    }
                    break;
                case consts.UPDATE_INSERT:
                    row = this.addNewRow();
                    this.$table.prepend(row);
                    this.syncronize();
                    break;
                case consts.UPDATE_DELETE:
                    this.deleteRow();
                    break;
                case consts.UPDATE_SCROLLED:
                    this.syncronize();
                    break;
                case consts.UPDATE_CONTROLS:
                    this.syncronize();
                    break;
                case consts.UPDATE_CLOSE:
                    this.$table.empty();
                    break;
                case consts.UPDATE_REFRESH:
                    this.resize();
                    break;
            }
        },

        update_field: function(field, refreshingRow) {
            var row = this.itemRow(),
                update,
                text,
                span;
            if (this.item.active && this.item.controls_enabled() && this.item.record_count()) {
                span = row.find('div.' + field.field_name + ' span');
                text = this.get_field_text(field);
                if (text !== span.text()) {
                    span.text(text);
                    update = (this.$table.get(0).clientWidth > this.$scroll_div.innerWidth()) ||
                        (this.$table.get(0).clientWidth > this.$element.innerWidth()) ||
                        (this.$head.find('th.' + field.field_name).outerWidth() !== row.find('td.' + field.field_name).outerWidth() && field !== this.fields[this.fields.length - 1]) ||
                        (span.get(0) && span.get(0).clientWidth !== span.get(0).scrollWidth) ||
                        (this.item.is_new() && this.item.record_count() === 1);
                    if (update) {
                        if (this.item.record_count() < 100) {
                            this.resize();
                        }
                        else {
                            this.syncColWidth();
                        }
                    }
                    if (!refreshingRow) {
                        this.update_selected(row);
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
                len = this.fields.length;
            if (this.item.record_count()) {
                $row = this.$table.find("tr:first-child");
                if (this.options.multi_select) {
                    $th = this.$head.find('th.' + 'multi_select');
                    $td = $row.find('td.' + 'multi_select');
                    $td.width($th.width());
                }
                for (i = 0; i < len - 1; i++) {
                    field = this.fields[i];
                    $th = this.$head.find('th.' + field.field_name);
                    $td = $row.find('td.' + field.field_name);

                    $td.find('div').width($th.find('div').width());
                    $td.width($th.width());
                    //~ if ($td.width != $th.width()) {
                        //~ $th.width($td.width());
                    //~ };
                }
            }
        },

        update_selected: function(row) {
            var multi_sel,
                checked = false;
            if (!row) {
                row = this.itemRow();
            }
            if (this.options.multi_select && this.options.multi_select_get_selected) {
                if (this.options.multi_select_get_selected.call(this.item, this.item)) {
                    checked = true;
                }
                multi_sel = row.find('input.multi_select');
                if (multi_sel.length) {
                    multi_sel[0].checked = checked;
                }
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
            this.eachField(function(field, i) {
                self.update_field(field, true);
            });
        },

        do_on_edit: function(mouseClicked) {
            if (this.item.lookup_field) {
                this.item.set_lookup_field_value(true);
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
            rec = this.item._records.indexOf($row.data("record"));
            if (this.editMode && rec !== this.item.rec_no) {
                if (!this.item.is_editing()) {
                    this.item.edit();
                }
                this.flushEditor();
                this.item.post();
            }
            this.item.set_rec_no(rec);
            if (!this.editing && !this.is_focused()) {
//                this.$table.focus();
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
//                    this.selected_row.find('td').removeClass("selected-focused selected");
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
//                    this.selected_row.find('td').addClass(selClassName);
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
                rowHeight = this.rowHeight,
                selClassName = 'selected';
            this.update_selected_row($row);
            if (this.is_focused()) {
                selClassName = 'selected-focused';
            }
            this.hide_selection();
            if (this.selected_row && this.options.expand_selected_row && !this.options.word_wrap) {
                this.selected_row.find('tr, div').css('height', textHeight);
            }
            this.selected_row = $row;
            this.show_selection();
            if (this.options.expand_selected_row && !this.options.word_wrap) {
                divs = this.selected_row.find('tr, div')
                divs.css('height', '');
                if (divs.eq(0).height() < this.options.expand_selected_row * textHeight) {
                    divs.eq(0).css('height', this.options.expand_selected_row * textHeight);
                }
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
                        this.item.grid_keydown = true;
                        e.preventDefault();
                        this.flushEditor();
                        if (code === 33) {
                            this.priorPage();
                        } else if (code === 34) {
                            if (this.item.auto_loading && this.item.is_loaded) {
                                this.item.last();
                            } else {
                                this.nextPage();
                            }
                        } else if (code === 38) {
                            this.item.prior();
                            if (this.item.bof()) {
                                this.priorPage(function() {
                                    self.item.last();
                                });
                            }
                        } else if (code === 40) {
                            this.item.next();
                            if (this.item.eof()) {
                                if (this.options.editable && this.editMode && this.options.append_on_lastrow_keydown) {
                                    if (!this.item.is_editing()) {
                                        this.item.edit();
                                    }
                                    this.item.post();
                                    if (!this.item.is_new()) {
                                        this.item.append();
                                    }
                                } else {
                                    this.nextPage();
                                }
                            }
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
                        this.do_on_edit(false);
                        break;
                    case 33:
                    case 34:
                    case 35:
                    case 36:
                    case 38:
                    case 40:
                        this.item.grid_keydown = undefined;
                        e.preventDefault();
                        if (this.item.details_active && !this.loading) {
                            this.item.open_details();
                        }
                        break;
                    case 32:
                        e.preventDefault();
                        if (this.options.multi_select_set_selected) {
                            multi_sel = this.itemRow().find('input.multi_select');
                            if (multi_sel.length) {
                                multi_sel[0].checked = !multi_sel[0].checked;
                                this.options.multi_select_set_selected.call(this.item, this.item, multi_sel[0].checked);
                            }
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

            if (!this.item.auto_loading || this.loading) {
                return;
            }
            if (value < this.pageCount || value === 0) {
                this.page = value;
                this.loading = true;
                this.item.open({
                    offset: this.page * this.item.limit
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
            if (this.item.auto_loading) {
                this.setPageNumber(this.page, callback);
            }
            else {
                this.open(callback);
            }
        },

        updatePageInfo: function() {
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
        },

        updatePageCount: function(callback) {
            var self = this;
            this.item.total_records(function(count) {
                self.recordCount = count;
                self.pageCount = Math.ceil(count / self.row_count);
                self.$pageCount.text(language.of + ' ' + self.pageCount);
                if (self.options.on_pagecount_update) {
                    self.options.on_pagecount_update.call(self.item, self.item, self);
                }
            });
        },

        firstPage: function(callback) {
            if (this.item.auto_loading) {
                this.setPageNumber(0, callback);
            } else {
                this.item.first();
            }
        },

        nextPage: function(callback) {
            var lines,
                clone;
            if (this.item.auto_loading) {
                if (!this.item.is_loaded) {
                    this.setPageNumber(this.page + 1, callback);
                }
            } else {
                clone = this.item.clone();
                clone.set_rec_no(this.item.get_rec_no())
                lines = this.$scroll_div.innerHeight() / this.rowHeight - 1;
                for (var i = 0; i < lines; i++) {
                    if (!clone.eof()) {
                        clone.next();
                    } else {
                        break;
                    }
                }
                this.item.set_rec_no(clone.get_rec_no());
            }
        },

        priorPage: function(callback) {
            var lines,
                clone;
            if (this.item.auto_loading) {
                if (this.page > 0) {
                    this.setPageNumber(this.page - 1, callback);
                } else {
                    this.syncronize();
                }
            } else {
                clone = this.item.clone();
                clone.set_rec_no(this.item.get_rec_no());
                lines = this.$scroll_div.innerHeight() / this.rowHeight - 1;
                for (var i = 0; i < lines; i++) {
                    if (!clone.eof()) {
                        clone.prior();
                    } else {
                        break;
                    }
                }
                this.item.set_rec_no(clone.get_rec_no());
            }
        },

        lastPage: function(callback) {
            var self = this;
            if (this.item.auto_loading) {
                this.item.total_records(function(count) {
                    self.recordCount = count;
                    self.pageCount = Math.ceil(count / self.row_count);
                    self.$pageCount.text(language.of + ' ' + self.pageCount);
                    self.setPageNumber(self.pageCount - 1, callback);
                    if (self.options.on_pagecount_update) {
                        self.options.on_pagecount_update.call(this.item, this.item, this);
                    }
                });
            } else {
                this.item.last();
            }
        },

        eachField: function(callback) {
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
                rec = this.item.get_rec_no(),
                info;
            $row.data("record", this.item._records[rec]);
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
            if (!this.options.word_wrap && this.textHeight) {
                divStyleStr += '; height: ' + this.textHeight + 'px';
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
            if (this.options.multi_select) {
                if (this.options.multi_select_get_selected) {
                    if (this.options.multi_select_get_selected.call(this.item, this.item)) {
                        checked = 'checked';
                    }
                }
                rowStr += this.newColumn('multi_select', 'center', '<input class="multi_select" type="checkbox" ' + checked + '>', -1, setFieldWidth);
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
            }
            else {
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
            this.$outer_table.detach();
            container.append(this.$outer_table);

            clone.on_get_field_text = this.item.on_get_field_text;
            this.$head.empty();
            this.$table.empty();
            rows = ''
            item_rec_no = this.item.rec_no;
            try {
                while (!clone.eof()) {
                    this.item._cur_row = clone._cur_row;
                    rows += this.newRow();
                    rec_nos.push(clone.get_rec_no());
                    clone.next();
                }
                this.$table.html(rows);
                rows = this.$table.find("tr");
                len = rows.length;
                for (i = 0; i < len; i++) {
                    row = rows.eq(i);
                    rec = rec_nos[i]
                    clone.set_rec_no(rec);
                    this.item._cur_row = rec;
                    row.data("record", clone._records[rec]);
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
                tmpRow = '<tr>'
                if (this.options.multi_select) {
                    if (this.options.multi_select_title) {
                        title = this.options.multi_select_title
                    }
                    tmpRow = tmpRow + '<th class="multi_select">' +
                        '<div class="text-center multi_select" style="overflow: hidden">' + title +
                        '</div>' +
                        '</th>';
                }
                len = this.fields.length;
                for (i = 0; i < len; i++) {
                    tmpRow = tmpRow + '<th class="' + this.fields[i].field_name + '" ><div style="overflow: hidden">' +
                        this.fields[i].field_caption + '</div></th>';
                }
                tmpRow = $(tmpRow + '</tr>');
                this.$table.prepend(tmpRow);
                if (this.options.multi_select) {
                    if (this.options.multi_select_colum_width) {
                        tmpRow.find(".multi_select").css("width", this.options.multi_select_colum_width);
                    } else {
                        tmpRow.find(".multi_select").css("width", '3%');
                    }
                }
                for (var field_name in this.options.column_width) {
                    if (this.options.column_width.hasOwnProperty(field_name)) {
                        tmpRow.find("." + field_name).css("width", this.options.column_width[field_name]);
                    }
                }
                if (this.options.multi_select) {
                    cell = row.find("td." + 'multi_select');
                    this.setCellWidth('multi_select', cell.width())
                }
                for (i = 0; i < len; i++) {
                    field = this.fields[i];
                    cell = row.find("td." + field.field_name);
                    this.setCellWidth(field.field_name, cell.width());
                }
                tmpRow.remove();
                this.fillTitle(container);
                if (this.options.multi_select) {
                    cell = row.find("td." + 'multi_select');
                    headCell = this.$head.find("th." + 'multi_select');
                    footCell = this.$foot.find("th." + 'multi_select');
                    cellWidth = this.getCellWidth('multi_select');
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
            } else {
                this.fillTitle(container);
                this.syncColWidth();
            }

            this.$outer_table.detach();
            this.$element.append(this.$outer_table);

            this.update_select_all_checkbox();

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

        update_select_all_checkbox: function() {
            var self = this;
            if (this.options.multi_select_select_all) {
                setTimeout(function() {
                    self.$outer_table.find('th input.multi_select')
                        .prop('checked', self.$table.find('td input.multi_select').is(":checked"));
                    },
                    200
                );
            }
        },

        resize: function() {
            if (this.autoFieldWidth) {
                this.fieldWidthUpdated = false;
                this.refresh();
            }
        },

        is_focused: function() {
            return this.$table.get(0) === document.activeElement;
        },

        focus: function() {
            if (!this.is_focused()) {
                if (this.$table.modalCanFocus()) {
                    this.$table.focus();
                }
            }
        }
    };

    /**********************************************************************/
    /*                      DBAbstractEntry class                         */
    /**********************************************************************/

    function DBAbstractEntry(field) {
        var self = this;
        this.field = field;
        this.read_only = false;
    }

    DBAbstractEntry.prototype = {
        constructor: DBAbstractEntry,

        createEntry: function(field, tabIndex, container) {
            var self = this,
                align,
                height,
                width,
                $controlGroup,
                $label,
                $input,
                $btn,
                $controls,
                $btnCtrls;
            if (!field) {
                return;
            }
            if (this.label) {
                $label = $('<label class="control-label"></label>')
                    .attr("for", field.field_name).text(this.label).
                    addClass(field.field_name);
            }
            if (field.get_lookup_data_type() === consts.BOOLEAN) {
                $input = $('<input>')
                    .attr("id", field.field_name)
                    .attr("type", "checkbox")
                    .attr("tabindex", tabIndex + "")
                    .click(function(e) {
                        self.field.value = !self.field.value;
                    });
            } else if (field.data_type === consts.INTEGER && field.value_list) {
                $input = $('<select>');
                $input.append('<option value="0"></option>');
                for (var i = 0; i < field.value_list.length; i++) {
                    $input.append('<option value="' + (i + 1) + '">' + field.value_list[i] + '</option>');
                }
                $input.attr("id", field.field_name)
                    .attr("tabindex", tabIndex + "");
                $input.on('change', function() {
                    self.field.value = parseInt($input.val(), 10);
                })
            }
            else {
                $input = $('<input>')
                    .attr("id", field.field_name)
                    .attr("type", "text")
                    .attr("tabindex", tabIndex + "");
            }
            $input.addClass(field.field_name)
            $controls = $('<div></div>').addClass("controls");
            this.$input = $input;
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
            if (field.lookup_item && !field.master_field) {
                $btnCtrls = $('<div class="input-prepend input-append"></div>').addClass("input-with-buttons");
                $btn = $('<button class="btn input-button" type="button"><i class="icon-remove-sign"></button>');
                $btn.attr("tabindex", -1);
                $btn.click(function() {
                    field.set_value(null);
                });
                this.$firstBtn = $btn;
                $btnCtrls.append($btn);
                $btnCtrls.append($input);
                $btn = $('<button class="btn input-button" type="button"><i class="icon-folder-open"></button>');
                $btn.attr("tabindex", -1);
                $btn.click(function() {
                    self.selectValue();
                });
                this.$lastBtn = $btn;
                $btnCtrls.append($btn);
                $controls.append($btnCtrls);
                $input.addClass("input-item");
            } else {
                switch (field.get_lookup_data_type()) {
                    case consts.TEXT:
                        $input.addClass("input-text");
                        $controls.append($input);
                        break;
                    case consts.INTEGER:
                        if (this.field.value_list) {
                            $input.addClass("input-select");
                        }
                        else {
                            $input.addClass("input-integer");
                        }
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
                        $btnCtrls = $('<div class="input-append"></div>').addClass("input-with-buttons");
                        $input.addClass("input-date");
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
                        $input.addClass("input-xlarge");
                        $controls.append($input);
                        break;
                }
                align = field.data_type === consts.BOOLEAN ? 'center' : alignValue[field.alignment];
                this.$input.css("text-align", align);
            }
            if (this.label_on_top) {
                this.$controlGroup = $('<div class="input-container"></div>');
            }
            else {
                this.$controlGroup = $('<div class="control-group input-container"></div>');
            }
            if (this.label) {
                this.$controlGroup.append($label);
            }
            this.$controlGroup.append($controls);

            if (container) {
                container.append(this.$controlGroup);
            }
            this.field.controls.push(this);
            this.$input.bind('destroyed', function() {
                self.field.controls.splice(self.field.controls.indexOf(self), 1);
            });

            this.$input.on('mouseenter', function() {
                var $this = $(this);
                if (self.error) {
                    $this.tooltip('show');
                }
            });

            this.$input.tooltip({
                    'placement': 'bottom',
                    'title': ''
                })
                .on('hide', function(e) {
                    e.stopPropagation()
                })
                .on('hidden', function(e) {
                    e.stopPropagation()
                })
                .on('show', function(e) {
                    e.stopPropagation()
                })
                .on('shown', function(e) {
                    e.stopPropagation()
                });

            this.$modalForm = this.$input.closest('.modal');
            this.update();
        },

        form_closing: function() {
            if (this.$modalForm) {
                return this.$modalForm.data('closing')
            }
            return false;
        },

        update: function() {
            if (!this.removed && !this.form_closing()) {
                if (this.read_only !== this.field.get_read_only()) {
                    this.read_only = this.field.get_read_only();
                    if (this.$firstBtn) {
                        this.$firstBtn.prop('disabled', this.read_only);
                    }
                    if (this.$lastBtn) {
                        this.$lastBtn.prop('disabled', this.read_only);
                    }
                    if (this.$input) {
                        this.$input.prop('disabled', this.read_only);
                    }
                }
                if (this.field.master_field) {
                    if (this.$firstBtn) {
                        this.$firstBtn.prop('disabled', true);
                    }
                    if (this.$lastBtn) {
                        this.$lastBtn.prop('disabled', true);
                    }
                    if (this.$input) {
                        this.$input.prop('disabled', true);
                    }
                }
                if (this.field.get_lookup_data_type() === consts.BOOLEAN) {
                    if (this.field.get_lookup_value()) {
                        this.$input.attr("checked", "checked");
                    } else {
                        this.$input.removeAttr("checked", "checked");
                    }
                } if (this.field.value_list) {
                    this.$input.val(this.field.value + '');
                }
                else {
                    this.errorValue = undefined;
                    this.error = undefined;
                    this.$input.val(this.field.get_display_text());
                }
                this.updateState(true);
            }
        },

        keydown: function(e) {
            var code = (e.keyCode ? e.keyCode : e.which);
            if (this.field.lookup_item && !(code === 229 || code === 9)) {
                e.preventDefault();
            }
            if (e.ctrlKey === true) {
                if (code !== 67 && code !== 86 && code !== 88 && code != 90) { // Ctrl-V , C, X, Z
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
            var code = (e.keyCode ? e.keyCode : e.which);
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
                } else if (this.field.lookup_item) {
                    e.stopPropagation();
                    e.preventDefault();
                    this.selectValue();
                } else if ((this.field.data_type === consts.DATE) || (this.field.data_type === consts.DATETIME)) {
                    e.stopPropagation();
                    e.preventDefault();
                    this.showDatePicker();
                }
            } else if (code === 27 && this.grid && this.grid.editMode) {
                e.stopPropagation();
                e.preventDefault();
                this.grid.item.cancel();
                this.grid.hideEditor();
            }
        },

        keypress: function(e) {
            var code = e.which;
            if (this.field.lookup_item) {
                e.preventDefault();
            }
            if (this.$input.is('select')) {
            }
            else if (code && !this.field.valid_char_code(code)) {
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
                    weekStart: language.week_start,
                    format: format,
                    daysMin: language.days_min,
                    months: language.months,
                    monthsShort: language.months_short,
                })
                .on('show', function(e) {
                    e.stopPropagation();
                    self.$input.datepicker().attr('data-weekStart', 1);
                })
                .on('hide', function(e) {
                    e.stopPropagation();
                })
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
                this.field.select_from_view_form();
            }
        },

        change_field_text: function() {
            var result = true,
                text;
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
                        this.$input.val(text);
                    }
                } catch (e) {
                    if (this.field.owner && this.field.owner.task.settings.DEBUGGING) {
                        console.log('change_field_text error: ' + e);
                    }
                    this.errorValue = text;
                    this.error = e;
                    result = false;
                }
            }
            return result;
        },

        focusIn: function(e) {
            this.hideError();
            if (!this.field.lookup_item) {
                if (this.errorValue) {
                    this.$input.val(this.errorValue);
                } else {
                    this.$input.val(this.field.get_text());
                }
                if (!this.mouseIsDown) {
                    this.$input.select();
                    this.mouseIsDown = false;
                }
            } else {
                this.$input.val(this.field.get_display_text());
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
            }
            else if (this.field.value_list) {
                result = true;
            } else if (this.change_field_text()) {
                this.$input.val(this.field.get_display_text());
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
    /*                        DBGridEntry class                           */
    /**********************************************************************/

    DBGridEntry.prototype = new DBAbstractEntry();
    DBGridEntry.prototype.constructor = DBGridEntry;

    function DBGridEntry(grid, field) {
        DBAbstractEntry.call(this, field);
        this.grid = grid;
        this.createEntry(field, 0);
    }

    $.extend(DBGridEntry.prototype, {

    });

    /**********************************************************************/
    /*                           DBEntry class                            */
    /**********************************************************************/

    DBEntry.prototype = new DBAbstractEntry();
    DBEntry.prototype.constructor = DBEntry;

    function DBEntry(field, index, container, label_on_top, label) {
        DBAbstractEntry.call(this, field);
        if (this.field.owner && this.field.owner.edit_form &&
            this.field.owner.edit_form.hasClass("modal")) {
            this.$edit_form = this.field.owner.edit_form;
        }
        this.label = label;
        this.label_on_top = label_on_top
        if (!this.label) {
            this.label = this.field.field_caption;
        }
        this.createEntry(field, index, container);
    }

    $.extend(DBEntry.prototype, {

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

    //////////////////////////////////////////////

    $.event.special.destroyed = {
        remove: function(o) {
            if (o.handler) {
                o.handler();
            }
        }
    };

    window.task = new Task();
    window.task.constructors = {task: Task, group: Group, item: Item};
    $.ajaxSetup({
        cache: false
    });

})(window);
