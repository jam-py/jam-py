import consts from "./consts.js";


class DBAbstractInput {
    constructor(field) {
        this.field = field;
        this.read_only = false;
        this.is_changing = true;
    }

    add_to_dom(field, tabIndex, container) {
        let field_type = field.lookup_data_type;
        if (!field) {
            return;
        }
        let input = '<input type="text" class="form-control"">',
            label = '<label class="form-label input-centered-label"></label>';
        if (field.lookup_item && !field.master_field || field.lookup_values ||
            field_type === consts.DATE || field_type === consts.DATETIME || field.bool_filter) {
            let icon_name = 'bi-chevron-down';
            if (field.lookup_item && !field.bool_filter) {
                icon_name = 'bi-search';
            } else if (field_type === consts.DATE || field_type === consts.DATETIME) {
                icon_name = 'bi-calendar';
            }
            input = '<div class="input-group">' +
                '<button type="button" class="first-btn btn btn-outline-secondary" tabindex="-1"><i class="bi bi-x-circle"></i></button>' +
                '<input type="text" class="form-control">' +
                '<button type="button" class="last-btn btn btn-outline-secondary" tabindex="-1"><i class="bi ' + icon_name + '"></i></button>' +
            '</div>'
        }
        else if (field_type === consts.FILE) {
            let field_file;
            if (this.field.data_type === consts.FILE) {
                field_file = this.field.field_file;
            }
            else {
                field_file = this.field.lookup_item[this.field.lookup_field].field_file;
            }
            input = '<div class="input-group">' +
              '<button type="button" class="first-btn btn btn-outline-secondary" tabindex="-1""><i class="bi bi-x-circle"></i></button>' +
              '<input type="text" class="form-control">' +
              '<button type="button" class="upload-btn btn btn-outline-secondary" tabindex="-1"><i class="bi bi-upload"></i></button>'
            if (field_file.download_btn) {
                input += '<button type="button" class="download-btn btn btn-outline-secondary" tabindex="-1""><i class="bi bi-download"></i></button>'
            }
            if (field_file.open_btn) {
                input += '<button type="button" class="open-btn btn btn-outline-secondary" tabindex="-1"><i class="bi bi-play-btn"></i></button>'
            }
            input += '</div>'
        }
        else if (field_type === consts.IMAGE) {
            input = '<div class="image-div">';
        }
        if (field.lookup_data_type === consts.BOOLEAN) {
            input = '<input class="form-check-input check-box-centered-input" type="checkbox" value="">';
            label = '<label class="form-check-label checkbox-centered-label">';
        } else if (field.lookup_data_type === consts.LONGTEXT || field.field_textarea) {
            input = '<textarea class="form-control" rows="3"></textarea>';
        }
        if (this.label_on_top) {
            this.$container = $('<div class="mb-2">' + label + input + '</div>');
        }
        else {
            if (field.lookup_data_type === consts.BOOLEAN) {
                this.$container = $('<div class="mb-2 row">' +
                    '<div class="overflow-hidden col-' + this.label_size + '">' +
                        label +
                    '</div>' +
                    '<div class="col-' + (12 -this.label_size) + '">' +
                        input +
                    '</div>' +
                '</div>');
            }
            else {
                this.$container = $('<div class="mb-2 row">' +
                    '<div class="overflow-hidden col-md-' + this.label_size + '">' +
                        label +
                    '</div>' +
                    '<div class="col-md-' + (12 -this.label_size) + '">' +
                        input +
                    '</div>' +
                '</div>');
            }
        }
        if (this.field.field_help) {
            this.$container.append(
                '<div class="form-text field-help" style="display: none;">' + this.field.field_help + '</div>'
            );
        }
        if (container) {
            container.append(this.$container);
        }
        this.$label = this.$container.find('label');
        this.$input = this.$container.find('input');
        this.$first_btn = this.$container.find('button.first-btn');
        this.$last_btn = this.$container.find('button.last-btn');
        this.$upload_btn = this.$container.find('button.upload-btn');
        this.$download_btn = this.$container.find('button.download-btn');
        this.$open_btn = this.$container.find('button.open-btn');
        if (field_type === consts.IMAGE) {
            this.$input = this.$container.find('div.image-div');
        }
        if (this.field.lookup_data_type === consts.LONGTEXT || this.field.field_textarea) {
            this.$input = this.$container.find('textarea')
        }
        this.$form = this.$input.closest('.jam-form');

        this.$label
            .text(this.label)
            .addClass(this.field.field_name);
        if (this.field.required) {
            this.$label.addClass('required');
        }
        this.$input.addClass(this.field.field_name);
        if (this.field.owner && this.field.owner.item_name) {
            let id = this.field.owner.item_name + '-' + this.field.field_name + '-id';
            this.$label.attr("for", id);
            this.$input.attr("id", id);
        }

    }

    init_buttons() {
        let self = this,
            field_type = this.field.lookup_data_type;
        this.$first_btn.click(function() {
            self.field.value = null;
        });
        this.$last_btn.click(function() {
            if (self.field.lookup_values) {
                self.dropdown.enter_pressed();
            }
            else if (self.field.lookup_item){
                self.select_value();
            }
            else if (self.field.data_type === consts.DATE ||
                self.field.data_type === consts.DATETIME) {
                self.show_date_picker();
            }
        });
        this.$upload_btn.click(function() {
            if (self.field.owner.is_changing() && !self.field.owner.read_only) {
                self.field.upload();
            }
        });
        this.$download_btn.click(function() {
            self.field.download();
        });
        this.$open_btn.click(function() {
            self.field.open();
        });
    }

    add_events() {
        let self = this,
            field_type = this.field.lookup_data_type;

        let field_mask = this.field.field_mask;
        if (!field_mask) {
            field_mask = this.field.get_mask()
        }
        if (field_mask) {
            try {
                self.$input.mask(field_mask);
            } catch (e) {}
        }

        this.$input.on('focus', function(e) {
            self.focus_in(e);
        });
        this.$input.on('blur', function(e) {
            self.focus_out(e);
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
        if (this.field.lookup_values) {
            this.dropdown = new DropdownList(this.field, this.$input);
            if (this.field.filter && this.field.bool_filter) {
                this.$input.parent().width(150);
            }
        }
        else if (this.field.lookup_item && field_type !== consts.FILE){
            if (this.field.enable_typeahead) {
                this.dropdown = new DropdownTypeahead(this.field,
                    this.$input, this.field.typeahead_options());
            }
        }
        if (this.field.data_type === consts.BOOLEAN) {
            this.$input.click(function(e) {
                self.field.value = !self.field.value;
            });
        }
        else if (this.field.data_type === consts.FILE) {
            this.$input.prop('disabled', true);
        }
        else if (this.field.data_type === consts.IMAGE) {
            this.$input.dblclick(function(e) {
                if (!self.field.read_only && self.field.data_type === consts.IMAGE &&
                    self.field.owner.is_changing() && !self.field.owner.read_only) {
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
        }

        this.field.controls.push(this);
        this.$input.bind('destroyed', function() {
            self.field.controls.splice(self.field.controls.indexOf(self), 1);
            //~ try {
                //~ if (self.dropdown){
                    //~ self.dropdown.destroy();
                //~ }
                //~ if (self.datepicker_shown) {
                    //~ self.$input.datepicker('hide');
                //~ }
            //~ }
            //~ catch (e) {
                //~ console.error(e);
            //~ }
        });
    }

    create_input(field, tabIndex, container) {
        this.add_to_dom(field, tabIndex, container);
        this.init_buttons();
        this.add_events();
        this.update();
    }

    form_closing() {
        if (this.$form) {
            return this.$form.data('_closing')
        }
    }

    set_read_only(value) {
        this.$first_btn.prop('disabled', value);
        this.$last_btn.prop('disabled', value);
        this.$upload_btn.prop('disabled', value);
        this.$download_btn.prop('disabled', value);
        this.$input.prop('disabled', value);
        if (this.field.lookup_data_type === consts.FILE) {
            this.$input.prop('disabled', true);
            if (this.field.lookup_value) {
                if (this.$open_btn) {
                    this.$open_btn.prop('disabled', false);
                }
                if (this.$download_btn) {
                    this.$download_btn.prop('disabled', false);
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
            //~ } else if (this.field.lookup_values) {
                //~ if (this.$input.parent().hasClass('open')) {
                    //~ this.$input.parent().removeClass('open');
                    //~ e.stopPropagation();
                //~ }
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
            format = task.locale.D_FMT;
        } else if (this.field.data_type === consts.DATETIME) {
            format = task.locale.D_T_FMT;
        }

        this.$input.datepicker(
            {
                weekStart: parseInt(task.language.week_start, 10),
                format: format,
                daysMin: task.language.days_min.slice(1, -1).split(','),
                months: task.language.months.slice(1, -1).split(','),
                monthsShort: task.language.months_short.slice(1, -1).split(','),
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
            this.hide_error();
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
                return;
            }
        }
        if (this.table && this.table.edit_mode) {
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
            this.errorValue = undefined;
            this.error = undefined;
            this.hide_error();
        } else {
            task.alert_error(this.error, {replace: false});
            this.show_error();
        }
    }

    show_error() {}

    hide_error() {}

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
        this.$input.data('db_table_input_data', this);
        this.$input.addClass('db-table-input');
    }

    add_to_dom(field, tabIndex, container) {
        this.$input = $('<input type="text" class="form-control">');
        if (field.lookup_data_type === consts.BOOLEAN) {
            input = $('<input class="form-check-input" type="checkbox" value="">');
        }
        let align = this.field.lookup_data_type === consts.BOOLEAN ? 'center' : consts.align_value[this.field.alignment];
        this.$input.css("text-align", align);
        this.$form = this.$input.closest('.jam-form');
    }

    init_buttons() {
    }
}


class DBInput extends DBAbstractInput {
    constructor(field, index, container, options, label) {
        super(field);
        if (this.field.owner && this.field.owner.edit_form &&
            this.field.owner.edit_form.hasClass("modal")) {
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
        this.$input.data('db_input_data', this);
        this.$input.addClass('db-input');
    }

    show_error() {
        this.hide_error();
        this.$input.addClass('is-invalid')
        this.$input.parent()
            .append('<div class="invalid-feedback">' + this.error + '</div></div>')
    }

    hide_error() {
        this.$input.removeClass('is-invalid')
        this.$input.parent().find('div.invalid-feedback').remove();
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
                menu: '<ul class="dropdown-menu typeahead"></ul>',
                item: '<li><a class="dropdown-item" href="#"></a></li>',
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

        items.first().find('a').addClass('active')
        this.$menu.html(items)
        return this
    }

    next(event) {
        var active = this.$menu.find('a.active').parent(),
            next = active.next()

        if (!next.length) {
            next = $(this.$menu.find('li')[0])
        }
        active.find('a').removeClass('active')
        next.find('a').addClass('active')
    }

    prev(event) {
        var active = this.$menu.find('a.active').parent(),
            prev = active.prev()

        if (!prev.length) {
            prev = this.$menu.find('li').last()
        }

        active.find('a').removeClass('active')
        prev.find('a').addClass('active')
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
        this.$menu.find('a.active').removeClass('active')
        $(e.currentTarget).find('a').addClass('active')
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
        var $li = this.$menu.find('a.active').parent();
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
        var $li = this.$menu.find('a.active').parent(),
            id_value = $li.data('id-value');
        this.lookup_item.locate(this.lookup_item._primary_key, id_value);
        this.lookup_item.set_lookup_field_value();
        return this.hide();
    }

    enter_pressed() {
        this.field.select_value();
    }
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


export {DBInput, DBTableInput, highlight}
