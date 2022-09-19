import consts from "./consts.js";
import Field from "./field.js";

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

export default Param
