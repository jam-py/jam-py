import consts from "./consts.js";
import AbsrtactItem from "./abstr_item.js";
import Param from "./param.js";
import {DBInput} from "./input.js";

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
				let err = this.params[i].check_valid();
				if (err) {
					this.warning(err);
					return false;
				}
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

        form = $(
            '<form class="input-form" autocomplete="off">' +
                '<div class="container">' +
                    '<div class="row">' +
                    '</div>' +
                '</div>' +
            '</form>'
            ).appendTo(container);
        if (options.in_well) {
            form.addClass('well');
        }
        if (options.autocomplete) {
            form.attr("autocomplete", "on")
        }
        else {
            form.attr("autocomplete", "off")
        }
        let row = form.find('div.row')
        form.append(row)
        len = params.length;
        for (col = 0; col < options.col_count; col++) {
            cols.push($("<div></div>")
            .addClass("col-md-" + 12 / options.col_count)
            .appendTo(row));
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

export default Report
