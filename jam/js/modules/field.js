import consts from "./consts.js";

class Field {
    constructor(owner, info) {
        this.owner = owner;
        this.set_info(info);
        this.controls = [];
        this.bind_index = null;
        this.lookup_index = null;
        this.field_type = consts.field_type_names[this.data_type];
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
            len = consts.field_attr.length,
            result = [];
        for (i = 0; i < len; i++) {
            result.push(this[consts.field_attr[i]]);
        }
        return result;
    }

    set_info(info) {
        if (info) {
            var i,
                len = consts.field_attr.length;
            for (i = 0; i < len; i++) {
                this[consts.field_attr[i]] = info[i];
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
            var mess = task.language.value_in_empty_dataset.replace('%s', this.owner.item_name);
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
        return consts.field_type_names[this.lookup_data_type];
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
                result = task.language.false;
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
                        result = task.language.true;
                    } else {
                        result = task.language.false;
                    }
                    break;
                case consts.KEYS:
                    if (result.length) {
                        result = task.language.items_selected.replace('%s', result.length);
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
                    if (value.toUpperCase() === task.language.yes.toUpperCase() ||
                        value.toUpperCase() === task.language.true.toUpperCase()) {
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
                throw new Error(task.language.not_edit_insert_state.replace('%s', this.owner.item_name));
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
        else if (this.report) {
            if (this.report.on_param_changed) {
                this.owner.on_param_changed.call(this.owner, this, lookup_item);
            }
        }
    }

    _check_system_field_value(value) {
        if (this._owner_is_item()) {
            if (this.field_name === this.owner._primary_key && this.value && this.value !== value) {
                throw new Error(task.language.no_primary_field_changing.replace('%s', this.owner.item_name));
            }
            if (this.field_name === this.owner._deleted_flag && this.value !== value) {
                throw new Error(task.language.no_deleted_field_changing.replace('%s', this.owner.item_name));
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
                        value = task.round(value, task.locale.FRAC_DIGITS);
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
            if (edit_image) {
                width = (field_image.edit_width + '').trim();
                height = (field_image.edit_height + '').trim();
                if (!width && !height) {
                    width = '100%'
                }
            }
            else {
                width = (field_image.view_width + '').trim();
                height = (field_image.view_height + '').trim();
                if (!width && !height) {
                    height = '100%'
                }
            }
            if (!width) {
                width = 'auto';
            }
            else {
                if (/^\d+$/.test(width)) {
                    width += 'px';
                }
            }
            if (!height) {
                height = 'auto';
            }
            else {
                if (/^\d+$/.test(height)) {
                    height += 'px';
                }
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
                    result = task.language.items_selected.replace('%s', len);
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
        if (this.default_value) {
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
            return this.field_caption + ': ' + task.language.value_required;
        }
        if (this.data_type === consts.TEXT && this.field_size !== 0 && this.text.length > this.field_size) {
            return this.field_caption + ': ' + task.language.invalid_length.replace('%s', this.field_size);
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
            format = task.locale.D_FMT;
        }
        else if (this.data_type === consts.DATETIME) {
            format = task.locale.D_T_FMT;
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

    valid_char_code(code) {
        var ch = String.fromCharCode(code),
            isDigit = code >= 48 && code <= 57,
            decPoint = ch === '.' || ch === task.locale.DECIMAL_POINT || ch === task.locale.MON_DECIMAL_POINT,
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


export default Field
