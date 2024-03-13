import consts from "./consts.js";
import {DBTableInput} from "./input.js";
import {highlight} from "./input.js";

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

        if (this.master_table) {
            this.$element.addClass('freezed');
        }
        else {
            let observer = new ResizeObserver(entries => {
                entries.forEach(entry => {
                    self.resize();
                });
            });
            observer.observe(this.$container.get(0));
        }
        this.$element.bind('destroyed', function() {

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
            striped: false,
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
            exact_height: true,
            show_hints: true,
            hint_fields: undefined,
            auto_page_scroll: true
        };

        this.options = $.extend(true, {}, default_options, this.item.table_options);
        this.options = $.extend({}, this.options, options);
        this.options.height = task.px_size(this.options.height);
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
        if (this.column_resizing || this.$container.width() === 0 ||
            (this.cur_width === this.$container.width() &&
            this.cur_height === this.$container.height())) {
                return;
        }
        let self = this;
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
                this.item.warning(task.language.selection_limit_exceeded.replace('%s', this.options.selection_limit))
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
            this.$element.find('input.multi-select-checkbox').prop('checked', selected);
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
                let dict = {};
                if (value) {
                    for (i = 0; i < self.item.selections.length; i++) {
                        dict[self.item.selections[i]] = true;
                    }
                    copy.each(function(c) {
                        if (!dict[c._primary_key_field.value]) {
                            self.item.selections.add(c._primary_key_field.value);
                        }
                    });
                }
                else {
                    copy.each(function(c) {
                        dict[c._primary_key_field.value] = true;
                    });
                    let selections = []
                    for (i = 0; i < self.item.selections.length; i++) {
                        let sel = self.item.selections[i];
                        if (!dict[sel]) {
                            selections.push(sel);
                        }
                    }
                    self.item.selections = selections;
                }
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
            if (self.selected_field && !self.editing && (code === 37 || code === 39)) {
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
            '<table class="outer-table table table-condensed table-bordered caption-top" style="width: 100%;">' +
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
            this.$table.addClass("striped");
        }

        let clicked_touchstart;

        this.$table.on('touchstart mousedown dblclick', 'td', function(e) {
            if (e.type === 'touchstart') {
                clicked_touchstart = true;
                return;
            }
            let syncronize = false;
            if (!clicked_touchstart) {
                syncronize = true;
            }
            let td = $(this);
            if (this.nodeName !== 'TD') {
                td = $(this).closest('td');
            }
            if (!(self.editing && td.find('input').length)) {
                e.preventDefault();
                self.clicked(e, td);
                if (syncronize) {
                    self.syncronize();
                    if (self.datasource.length > self.row_count) {
                        self.datasource.length = self.row_count;
                        self.$table.find('tr:last-child').remove();
                    }
                }
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

        let is_touchstart_event;
        this.$outer_table.on('touchstart mouseenter', 'th', function(e) {
            if (e.type === "touchstart") {
                is_touchstart_event = true;
                return;
            }
            if (e.type === "mouseenter") {
                if (is_touchstart_event) {
                    is_touchstart_event = false;
                    return;
                }
            }
            let $th = $(this),
                field_name = $th.data('field_name'),
                field = self.item.field_by_name(field_name);
            if (self.item.view_options.enable_search &&
                !$th.find('input').length && field &&
                self.item._can_search_on_field(field)) {

                $th.css('position', 'relative');
                let $btn = $(
                    '<button type="button" class="btn btn-secondary title-search-btn">' +
                        '<i class="bi bi-search"></i>' +
                    '</button>'
                );
                $th.append($btn);
                $btn.on('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    let $active_input = $th.parent().find('th input#title-search-input');
                    if ($active_input.length && $active_input.val()) {
                        let $form = $active_input.parent(),
                            active_field_name = $form.parent().data('field_name');
                        $active_input.val('');
                        self.hide_search_inputs();
                        self.item.search(active_field_name, '', 'contains_all', true, function() {
                            let $th = self.$outer_table.find('thead th.' + field_name)
                            $th.css('position', 'relative');
                            self.create_search_input_form(field, $th, $btn)
                        });
                    }
                    else {
                        self.create_search_input_form(field, $th, $btn)
                    }
                });
            }
        });

        this.$outer_table.on('mouseleave', 'th', function(e) {
            $(this).find('.title-search-btn').remove();
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

        this.$element.on('click', 'input.multi-select-checkbox', function(e) {
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

            self.column_resizing = true;
            try {
                change_field_width($th, delta);
                self.update_ellipse_btn(self.$table);
            }
            finally {
                setTimeout(
                    function() {
                        self.column_resizing = false
                    }, 100);
            }

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
                        'height': self.$outer_table.find('thead').innerHeight() +
                            self.$overlay_div.innerHeight() + self.$outer_table.find('tfoot').innerHeight(),
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
                self.item._open_params.__order = self._sorted_fields;
                if (!self.item._paginate) {
                    self.item._sort(self._sorted_fields);
                } else {
                    if (self.options.sort_add_primary) {
                        field = self.item[self.item._primary_key]
                        desc = self._sorted_fields[self._sorted_fields.length - 1][1]
                        self._sorted_fields.push([field.field_name, desc]);
                    }
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

    init_search_inputs() {
        let self = this;
        this.fields.forEach(function(field) {
            if (self.item._can_search_on_field(field)) {
                self.create_search_input_form(field);
            }
        });
        this.$table.on('focus.search', function() {
            self.hide_search_inputs();
        });
    }

    hide_search_inputs($exclude_form) {
        let self = this,
            forms = this.$outer_table.find('thead th .title-search-input-form');
        forms.each(function() {
            let $form = $(this);
            if (!$exclude_form || $exclude_form.get(0) !== $form.get(0)) {
                self.hide_search_input_form($form);
            }
        });
    }

    hide_search_input_form($form) {
        let $input = $form.find('input');
        if ($form.is(":visible") && !$input.val().trim().length) {
            $form.hide();
            $form.parent().find('*').show();
            $form.remove();
        }
    }

    create_search_input_form(field, $th, $btn) {
        let self = this;
        if (!$th) {
            $th = this.$outer_table.find('thead th.' + field.field_name)
            $th.css('position', 'relative');
        }
        if ($btn) {
            $btn.remove();
        }
        $th.find('div *').hide();
        let $search_input_form = $(
            '<form class="title-search-input-form">' +
                '<label for="title-search-input" class="form-label title-search-input-label"></label>' +
                '<input class="form-control" id="title-search-input">' +
            '</form>'
        );
        $th.append($search_input_form);
        let $label = $th.find('label').text(field.field_caption),
            $input = $th.find('input');
        this.item._init_column_title_search(field, $input);
        $input.blur(function() {
            self.hide_search_input_form($search_input_form);
        });
        if ($btn) {
            $input.focus();
        }
        else {
            $input.focus(function() {
                self.hide_search_inputs($search_input_form);
            });
        }
        $input.keyup(function(e) {
            var code = e.which;
            if (code === 27) {
                e.preventDefault();
                e.stopPropagation();
                if (!self.item.paginate && self.item.master) {
                    self.hide_search_input_form($search_input_form);
                }
                else {
                    if (!$input.val().trim().length) {
                        self.hide_search_input_form($search_input_form);
                    }
                }
            }
            else if (code === 40) {
                self.$table.focus();
            }
        });
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
        $element.find('th div').css('margin', 0);
        $td = $table.find('tr:first td');
        this.text_height = $td.find('div').height();
        let $tr = $table.find('tr:nth-child(2)');
        row_height = $tr.outerHeight(true);
        margin = $table.innerHeight() - row_height * 10;
        if (margin < 0) {
            margin = 0;
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
            this.$overlay_div.height(this.row_height * this.options.row_count + this.row_margin);
            if (this.options.expand_selected_row) {
                this.$overlay_div.height(this.row_height * (this.options.row_count - 1) + this.selected_row_height + this.row_margin);
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
        let overlay_div_height = this.$overlay_div.innerHeight();
        if (this.options.expand_selected_row) {
            overlay_div_height = this.$overlay_div.height() - this.selected_row_height;
        }
        this.row_count = Math.floor(overlay_div_height / this.row_height);
        if (this.options.expand_selected_row) {
            this.row_count += 1;
        }
        if (this.row_count <= 0) {
            this.row_count = 1;
        }
        this.calc_overlay_div_height();
        return this.row_count;
    }

    calc_overlay_div_height() {
        //~ this.options.exact_height = false;
        if (this.options.exact_height) {
            let height = this.row_height * this.row_count;
            if (this.options.expand_selected_row) {
                height = this.row_height * (this.row_count - 1) + this.selected_row_height;
            }
            this.$overlay_div.height(height + this.row_margin);
        }
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
                    '<div class="btn-toolbar my-1 d-flex justify-content-center" role="toolbar" aria-label="Toolbar with button groups">' +
                        '<div class="btn-group me-1" >' +
                            '<button type="button" class="pg-btn-first btn btn-outline-secondary"><i class="bi bi-skip-backward-fill"></i></button>' +
                            '<button type="button" class="pg-btn-prior btn btn-outline-secondary"><i class="bi bi-caret-left-fill"></i></button>' +
                        '</div>' +
                        '<div class="input-group me-1">' +
                            '<div class="pg-page input-group-text">' + task.language.page + '</div>' +
                            '<input type="text" class="form-control pagination-input text-center" style="width: 100px;">' +
                            '<div class="input-group-text"><span>' + task.language.of + '</span><span class="page-count ms-1"></span></div>' +
                        '</div>' +
                        '<div class="page-count-text m-2"  style="min-width: 80px;">' +
                            '<span class="page-number"></span>' + '/ ' +
                            '<span class="page-count"></span>' +
                        '</div>' +
                        '<div class="btn-group">' +
                            '<button type="button"class="pg-btn-next btn btn-outline-secondary"><i class="bi bi-caret-right-fill"></i></button>' +
                            '<button type="button" class="pg-btn-last btn btn-outline-secondary"><i class="bi bi-skip-forward-fill"></i></button>' +
                        '</div>' +
                    '</div>'
                );

                if (task.media === 2) {
                    $pagination.find('.input-group *').hide();
                }
                else {
                    $pagination.find('.page-count-text').hide();
                }
                this.$fistPageBtn = $pagination.find('button.pg-btn-first');
                this.$fistPageBtn.on("click", function(e) {
                    self.first_page(true);
                    e.preventDefault();
                });
                this.$fistPageBtn.addClass("disabled");

                this.$priorPageBtn = $pagination.find('button.pg-btn-prior');
                this.$priorPageBtn.on("click", function(e) {
                    self.prior_page(true);
                    e.preventDefault();
                });
                this.$priorPageBtn.addClass("disabled");

                this.$nextPageBtn = $pagination.find('button.pg-btn-next');
                this.$nextPageBtn.on("click", function(e) {
                    self.next_page(true);
                    e.preventDefault();
                });

                this.$lastPageBtn = $pagination.find('button.pg-btn-last');
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
                    '<div class="text-right" style="line-height: normal; padding-top: 0.5rem">' +
                        '<span class="small-pager">' +
                            '<span>' + task.language.page + ' </span>' +
                            '<span class="page-number"></span>' +
                            '<span>' + task.language.of + ' </span>' +
                            '<span class="page-count"></span>' +
                        '</span>' +
                    '</div>'
                )
            }
            if ($pagination) {
                this.$page_count = $pagination.find('.page-count');
                this.$page_number = $pagination.find('.page-number');
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
                this.$page_count.text('');
                if (pagerWidth) {
                    $pagination.find('#pager').width(pagerWidth);
                }
            }
        }
        else {
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
                $td = this.editor.$input.parent();
                field = this.editor.field;
                $td.find('*').show();
                this.editor.$input.remove();
                this.editor.removed = true;
                this.editor = undefined;
                $td.find('*').show();
            } finally {
                this.editing = false;
            }
            this.focus();
        }
    }

    close_editor() {
        if (this.editor) {
            let self = this,
                old_data = this.editor.old_data;
            if (!this.item.is_changing()) {
                this.item.edit();
            }
            this.flush_editor();
            this.hide_editor();
            if (this.item.is_changing()) {
                this.item.post();
            }
            this.item.apply(function(error) {
                if (error) {
                    self.selected_field.data = old_data
                    self.update_field(self.selected_field)
                    self.item.alert_error(error);
                }
                if (self.item.master) {
                    self.item.master.edit();
                }
                self.show_selection();
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
            let field = this.selected_field;
            this.edit_mode = true;
            this.editor = new DBTableInput(this, field);
            this.editor.old_data = field.data;
            this.editor.window_width = $(window).width();
            this.editor.$input.addClass('inline-editor')

            $td = $row.find('td.' + field.field_name);
            $td.find('*').hide();
            $td.css('position', 'relative')
            $td.append(this.editor.$input);
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
                    order_fields[field.field_name] = '<span>&darr;</span>';
                } else {
                    order_fields[field.field_name] = '<span>&uarr;</span>';
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
                input = $('<input class="multi-select-checkbox" type="checkbox" ' + checked + ' tabindex="-1">');
                div.append(input);
                cell = $('<th class="multi-select-checkbox"></th>').append(div);
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
                        '<li><a class="dropdown-item select-all" tabindex="-1" href="#">' + task.language.select_all + '</a></li>' +
                        '<li"><a class="dropdown-item unselect-all" tabindex="-1" href="#">' + task.language.unselect_all + '</a></li>'
                }
                shown_title = task.language.show_selected
                if (self.item._show_selected) {
                    shown_title = task.language.show_all
                }
                select_menu +=
                    '<li><a class="dropdown-item show-selected" tabindex="-1" href="#">' + shown_title + '</a></li>';
                bl = $(
                        '<div class="btn-group select-block" style="position: relative">' +
                            '<button type="button" class="btn mselect-btn" tabindex="-1">' +
                                '<input class="multi-select-checkbox" type="checkbox" tabindex="-1"' + checked + '>' +
                            '</button>' +
                            '<button class="btn btn-outline-secondary select-menu-btn dropdown-toggle" type="button" data-bs-toggle="dropdown" >' +
                            '</button>' +
                            '<ul class="dropdown-menu">' +
                                select_menu +
                            '</ul>' +
                        '</div>'
                );
                input = bl.find('.mselect-block')
                bl.find(".select-all").click(function(e) {
                    e.preventDefault();
                    self.selections_set_all_selected_ex(true);
                    self.$table.focus();
                });
                bl.find(".unselect-all").click(function(e) {
                    e.preventDefault();
                    self.selections_set_all_selected_ex(false);
                    self.$table.focus();
                });
                bl.find(".show-selected").click(function(e) {
                    e.preventDefault();
                    self.item._show_selected = !self.item._show_selected;
                    self.item._reopen(0, {__show_selected_changed: true}, function() {
                        self.selections_update_selected();
                        self.$table.focus();
                    });
                });
                cell = $('<th class="multi-select"></th>').append(div);
                heading.append(cell);
                //~ cell.css('padding-top', 0);
                //~ input.css('top', sel_count.outerHeight() + sel_count.position().top + 4);
                //~ input.css('left', (cell.outerWidth() - input.width()) / 2 + 1);
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
            cell = $('<th class="' + field.field_name + '" data-field_name="' + field.field_name + '" style="vertical-align: middle"></th>').append(div);
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
        return parseInt(this.cell_widths[field_name], 10);
    }

    set_сell_width(field_name, value) {
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
                this.syncronize(true);
                break;
            case consts.UPDATE_CONTROLS:
                this.syncronize(true);
                this.build(true);
                break;
            case consts.UPDATE_CLOSE:
                this.$table.empty();
                break;
            case consts.UPDATE_APPLIED:
                if (this.options.update_summary_after_apply) {
                    this.update_totals();
                }
                break;
            case consts.UPDATE_SUMMARY:
                this.update_summary();
                break;
            case consts.UPDATE_REFRESH:
                this.update_totals();
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
                    value = task.round(value, task.locale.FRAC_DIGITS);//.toFixed(task.locale.FRAC_DIGITS);
                }
                new_text = this.item.on_field_get_summary.call(this.item, field, value);
            }
            if (!new_text) {
                new_text = text;
            }
            this.$foot.find('div.' + field_name).html(new_text);
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
            count_field = copy._primary_key;
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
                        else {
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
            this.selected_row.removeClass("row-selected table-focused");
            if (this.selected_field) {
                this.selected_row.find('td.' + this.selected_field.field_name)
                    .removeClass("field-selected")
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
        if (!this.is_showing_selection) {
            this.is_showing_selection = true;
            try {
                this.selected_row.addClass('row-selected');
                if (this.table_focused()) {
                    this.selected_row.addClass('table-focused');
                }
                if (this.selected_row) {
                    if (this.can_edit() && this.selected_field) {
                        this.selected_row.find('td.' + this.selected_field.field_name)
                            .addClass("field-selected");
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
            divs = this.selected_row.find('tr, div')
            divs.css('height', this.options.row_line_count * textHeight);
            this.update_ellipse_btn(this.selected_row);
        }
        this.selected_row = $row;
        this.show_selection();
        if (this.options.row_line_count && this.options.expand_selected_row) {
            divs = this.selected_row.find('tr, div')
            divs.css('height', '');
            divs.css('height', this.options.expand_selected_row * textHeight);
            this.update_ellipse_btn(this.selected_row);
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
            this.$table.css({'top': this.$overlay_div.scrollTop() + 'px'});
        }
        else {
            this.scroll_table(e);
            if (this.item.paginate) {
                this.$table.css({'top': this.$overlay_div.scrollTop() + 'px'});
            }
            else {
                this.$table.css({'top': (this.$overlay_div.scrollTop() - this.scroll_delta) + 'px'});
                //~ clearTimeout(this.scrolling);
                //~ this.scrolling = setTimeout(function () {
                    //~ let rec_no = self.record_by_row(self.$table.find('tr').eq(0))
                    //~ if (rec_no !== undefined) {
                        //~ self.item.rec_no = rec_no;
                    //~ }
                //~ }, 100);
            }
        }
    }

    scroll_datasource(page_rec) {
        this.datasource = [];
        this.fill_datasource(page_rec, 1);
    }

    scroll_table(e) {
        var self = this,
            scroll_top = this.$overlay_div.scrollTop(),
            page_rec = scroll_top / this.row_height;
        page_rec = Math.floor(page_rec);
        this.scroll_delta = (scroll_top / this.row_height - page_rec) * this.row_height;
        //~ if (scroll_top > this.prev_scroll_top) {
            //~ page_rec = Math.ceil(page_rec);
        //~ }
        //~ else {
            //~ page_rec = Math.floor(page_rec);
        //~ }
        this.prev_scroll_top = this.$overlay_div.scrollTop();
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
        if (this.$page_number) {
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
                this.$page_count.text('1');
                if (this.page_count) {
                    this.$page_count.text(this.page_count);
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
            this.update_ellipse_btn(row);
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
        this.syncronize_tables();
    }

    syncronize_tables() {
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
                this.update_ellipse_btn(row);
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
        this.syncronize_tables();
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
            this.syncronize_tables();
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
            this.syncronize_tables();
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
            this.syncronize_tables();
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
            this.syncronize_tables();
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

    new_column(columnName, align, text, index, field_type) {
        var cell_width = this.get_cell_width(columnName),
            classStr = 'class="' + columnName + ' ' + field_type,
            dataStr = 'data-field_name="' + columnName + '"',
            tdStyleStr = 'style="text-align:' + align + ';overflow: hidden',
            divStyleStr = 'style="overflow: hidden !important';
        if (this.text_height) {
            if (this.options.row_line_count) {
                divStyleStr += '; height: ' + this.options.row_line_count * this.text_height + 'px; width: auto';
            }
        }
        classStr += '""';
        tdStyleStr += '""';
        divStyleStr += '"';
        return '<td ' + classStr + ' ' + dataStr + ' ' + tdStyleStr + '>' +
            '<div ' + classStr + ' ' + divStyleStr + '>' + text +
            '</div>' +
            '</td>';
    }

    new_row() {
        var i,
            len,
            rowStr,
            checked = '';
        len = this.fields.length;
        rowStr = '';
        if (this.options.multiselect) {
            if (this.selections_get_selected()) {
                checked = 'checked';
            }
            rowStr += this.new_column('multi-select',
                'center', '<input class="multi-select" type="checkbox" ' + checked +
                ' tabindex="-1" style="margin: 0">', -1, '');
        }
        for (i = 0; i < len; i++) {
            let field = this.fields[i],
                text = this.get_field_html(field),
                align = field.data_type === consts.BOOLEAN ? 'center' : consts.align_value[field.alignment],
                field_type = consts.field_type_names[field.lookup_data_type] + '-displayed';
            rowStr += this.new_column(field.field_name, align, text, i, field_type);
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
            $row = this.$outer_table.find("tr:first-child");
            this.set_saved_width($row)
            if (this.fields.length && this.$table.is(':visible')) {
                let $tr = this.$table.find('tr:first')
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
            header_col_group = '<colgroup>',
            body_col_group = '<colgroup>',
            len = this.fields.length,
            count = len - 1,
            field,
            width,
            cell_width;
        this.remove_saved_width();
        if (this.options.multiselect) {
            header_col_group += '<col style="width: 52px">'
            body_col_group += '<col style="width: 52px">'
        }
        if (all_cols || this.master_table) {
            count = len;
        }
        for (i = 0; i < count; i++) {
            field = this.fields[i];
            width = this.get_cell_width(field.field_name);
            cell_width = width;
            if (i === 0) {
                let column_row = this.$outer_table.find("tr:first-child"),
                    column_offset = column_row.offset(),
                    cell_row = this.$table.find('tr:first'),
                    cell_offset = cell_row.offset()
                if (column_offset && cell_offset) {
                    cell_width = this.cell_widths[field.field_name]
                    cell_width = width - (Math.round(cell_offset.left + cell_width) -
                        Math.round(column_offset.left + cell_width))
                    cell_width = width - (cell_offset.left + cell_width -
                        (column_offset.left + cell_width))
                }

            }
            header_col_group += '<col style="width: ' + width + 'px">';
            body_col_group += '<col style="width: ' + cell_width + 'px">';
        }
        header_col_group += '</colgroup>';
        body_col_group += '</colgroup>';
        this.$outer_table.prepend(header_col_group)
        this.$table.prepend(body_col_group);
    }

    fill_datasource(start_rec, add_rec) {
        var self = this,
            counter = 0,
            clone = this.item.clone(true);
        if (!this.datasource.length || this.item.paginate) {
            this.datasource = [];
            if (start_rec === undefined) {
                start_rec = 0;
            }
            if (add_rec == undefined) {
                add_rec = 0
            }
            clone.rec_no = start_rec;
            while (!clone.eof()) {
                self.datasource.push([clone.rec_no, null]);
                clone.next();
                counter += 1;
                if (counter >= self.row_count + add_rec) {
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
            search_form = this.$outer_table.find('thead th > form.title-search-input-form'),
            search_field_name,
            search_input_focused,
            self = this;
        is_focused = this.is_focused();
        if (search_form.length === 1) {
            search_field_name = search_form.parent().data('field_name');
            search_input_focused = search_form.find('input').is(":focus");
            search_form.hide();
            search_form.detach();
        }
        else {
            search_form = undefined;
            this.hide_search_inputs();
        }
        if (this.options.editable && this.edit_mode && this.editor) {
            if (!is_focused) {
                is_focused = this.editor.$input.is(':focus');
            }
            editable_val = this.editor.$input.value;
            this.hide_editor();
        }

        if (!this.item.paginate) {
            if (this.options.row_count !== this.row_count) {
                this.calc_overlay_div_height();
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
        if (search_form && search_form.length) {
            let $th = this.$outer_table.find('thead th.' + search_field_name);
            if ($th.length) {
                $th.find('*').hide();
                $th.css('position', 'relative');
                $th.append(search_form);
                search_form.show();
                if (search_input_focused) {
                    search_form.find('input').focus();
                }
            }
        }
        this.prev_scroll_top = this.$overlay_div.scrollTop();
        this.update_ellipse_btn(this.$table);
        this.cur_width = this.$container.width()
        this.cur_height = this.$container.height()
    }

    update_ellipse_btn($parent) {
        let self = this;
        $parent.find('td > div').each(function() {
            let $td = $(this).parent(),
                $btn = $td.find('.hint-btn');
            $btn.eq(0).tooltip('hide');
            $btn.remove();
            if (Math.abs(this.offsetHeight - this.scrollHeight) > 1 ||
                Math.abs(this.offsetWidth - this.scrollWidth) > 1) {
                $td.css('position', 'relative');
                let $btn = $(
                    '<button type="button" class="btn btn-secondary hint-btn">' +
                        '<i class="bi bi-three-dots"></i>' +
                    '</button>'
                );
                $td.append($btn);
                let placement = 'right',
                    table_width = self.$table.width(),
                    container = self.$table;
                if (self.master_table) {
                    table_width = self.master_table.$table.width();
                    container = self.master_table;
                }
                if (table_width - ($(this).offset().left + $(this).width()) < 200) {
                    placement = 'left';
                }
                $btn.tooltip({container: container.get(0), placement: placement, title: $(this).text(), trigger: 'hover'});
                $btn.on('mousedown dblclick click', function(e) {
                    e.stopPropagation();
                });
            }
        });
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
            this.$table.get(0).focus();
        }
    }
}

export default DBTable
