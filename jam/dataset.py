import os
import datetime
import traceback

from werkzeug.utils import cached_property

from .common import consts, error_message
from .common  import to_str

FIELD_DEF = FIELD_ID, FIELD_NAME, FIELD_CAPTION, FIELD_DATA_TYPE, FIELD_SIZE, REQUIRED, LOOKUP_ITEM, \
    LOOKUP_FIELD, LOOKUP_FIELD1, LOOKUP_FIELD2, FIELD_VISIBLE, \
    FIELD_READ_ONLY, FIELD_DEFAULT, FIELD_DEFAULT_VALUE, MASTER_FIELD, FIELD_ALIGNMENT, \
    FIELD_LOOKUP_VALUES, FIELD_MULTI_SELECT, FIELD_MULTI_SELECT_ALL, \
    FIELD_ENABLE_TYPEAHEAD, FIELD_HELP, FIELD_PLACEHOLDER, FIELD_INTERFACE, \
    FIELD_IMAGE, FIELD_FILE, DB_FIELD_NAME, FIELD_CALC = range(27)

FILTER_DEF = FILTER_OBJ_NAME, FILTER_NAME, FILTER_FIELD_NAME, FILTER_TYPE, \
    FILTER_MULTI_SELECT, FILTER_DATA_TYPE, FILTER_VISIBLE, FILTER_HELP, \
    FILTER_PLACEHOLDER, FILTER_ID = range(10)

class DatasetException(Exception):
    pass

class DatasetEmpty(Exception):
    pass

class DatasetInvalidState(Exception):
    pass

class FieldInvalidValue(Exception):
    pass

class FieldInvalidLength(Exception):
    pass

class FieldValueRequired(Exception):
    pass

class FieldValidateError(Exception):
    pass

class DBField(object):
    def __init__(self, owner, field_def):
        self.owner = owner
        self.field_def = field_def
        self.field_kind = consts.ITEM_FIELD
        self.ID = field_def[FIELD_ID]
        self.field_name = field_def[FIELD_NAME]
        self.field_caption = field_def[FIELD_CAPTION]
        self.data_type = field_def[FIELD_DATA_TYPE]
        self.required = field_def[REQUIRED]
        self.lookup_item = field_def[LOOKUP_ITEM]
        self.master_field = field_def[MASTER_FIELD]
        self.lookup_field = field_def[LOOKUP_FIELD]
        self.lookup_db_field = None
        self.lookup_item1 = None
        self.lookup_field1 = field_def[LOOKUP_FIELD1]
        self.lookup_db_field1 = None
        self.lookup_item2 = None
        self.lookup_field2 = field_def[LOOKUP_FIELD2]
        self.lookup_db_field2 = None
        self.read_only = field_def[FIELD_READ_ONLY]
        self.view_visible = field_def[FIELD_VISIBLE]
        self.field_size = field_def[FIELD_SIZE]
        self.default = field_def[FIELD_DEFAULT]
        self.default_value = field_def[FIELD_DEFAULT_VALUE]
        self.alignment = field_def[FIELD_ALIGNMENT]
        self.lookup_values = field_def[FIELD_LOOKUP_VALUES]
        self.multi_select = field_def[FIELD_MULTI_SELECT]
        self.multi_select_all = field_def[FIELD_MULTI_SELECT_ALL]
        self.enable_typeahead = field_def[FIELD_ENABLE_TYPEAHEAD]
        self.field_help = field_def[FIELD_HELP]
        self.field_placeholder = field_def[FIELD_PLACEHOLDER]
        self.field_mask = field_def[FIELD_INTERFACE]
        self.field_image = field_def[FIELD_IMAGE]
        self.field_file = field_def[FIELD_FILE]
        self.db_field_name = field_def[DB_FIELD_NAME]
        self.field_type = consts.FIELD_TYPE_NAMES[self.data_type]
        self.filter = None
        self.calculated = field_def[FIELD_CALC]
        self.on_field_get_text_called = None
        # ~ self.bind_index = None

    def __setattr__(self, name, value):
        if name != 'owner' and self.owner and self.owner.task_locked():
            raise Exception(consts.language('server_tree_immutable') + \
                ' Item: "%s", Field: "%s", Attribute: "%s"' % (self.owner.item_name, self.field_name, name))
        super(DBField, self).__setattr__(name, value)

    @property
    def row(self):
        if self.owner._dataset:
            return self.owner._dataset[self.owner.rec_no]
        else:
            raise DatasetEmpty(consts.language('value_in_empty_dataset') % self.owner.item_name)

    @property
    def data(self):
        if self.row and self.bind_index >= 0:
            result = self.row[self.bind_index]
            if self.data_type == consts.DATE:
                if isinstance(result, str):
                    result = consts.convert_date(result)
            elif self.data_type == consts.DATETIME:
                if isinstance(result, str):
                    result = consts.convert_date_time(result)
            return result

    @property
    def restrictions(self):
        result = False, False
        if self.field_kind == consts.ITEM_FIELD:
            if self.owner.user_info:
                result = self.owner.field_def_restrictions(self.field_def, self.owner.user_info['role_id'])
        return result

    @data.setter
    def data(self, value):
        if self.row and (self.bind_index >= 0):
            self.row[self.bind_index] = value

    @property
    def lookup_data(self):
        if self.lookup_index:
            if self.row and (self.lookup_index >= 0):
                result = self.row[self.lookup_index]
                if self.data_type == consts.DATETIME and result:
                    if isinstance(result, str):
                        result = result.replace('T', ' ')
                return result

    @lookup_data.setter
    def lookup_data(self, value):
        if self.lookup_index:
            if self.row and (self.lookup_index >= 0):
                self.row[self.lookup_index] = value

    def _value_to_text(self, data, value, data_type):
        result = ''
        if data is None:
            if data_type == consts.BOOLEAN:
                result = consts.language('false')
        else:
            result = value
            if data_type == consts.INTEGER:
                result = str(result)
            elif data_type == consts.FLOAT:
                result = self.float_to_str(result)
            elif data_type == consts.CURRENCY:
                result = self.float_to_str(result)
            elif data_type == consts.DATE:
                result = self.date_to_str(result)
            elif data_type == consts.DATETIME:
                result = self.datetime_to_str(result)
            elif data_type == consts.BOOLEAN:
                if value:
                    result = consts.language('true')
                else:
                    result = consts.language('false')
            elif data_type == consts.KEYS:
                if len(result):
                    result = consts.language('items_selected') % len(result)
            elif data_type == consts.FILE:
                result = self.get_secure_file_name(result)
            else:
                result = str(result)
        return result

    @property
    def text(self):
        return self._value_to_text(self.data, self.value, self.data_type)

    @text.setter
    def text(self, value):
        if value != self.text:
            if self.data_type == consts.TEXT:
                self.value = str(value)
            elif self.data_type == consts.INTEGER:
                self.value =  int(value)
            if self.data_type == consts.FLOAT:
                self.value = consts.str_to_float(value)
            elif self.data_type == consts.CURRENCY:
                self.value = consts.str_to_cur(value)
            elif self.data_type == consts.DATE:
                self.value = consts.str_to_date(value)
            elif self.data_type == consts.DATETIME:
                self.value = consts.str_to_datetime(value)
            elif self.data_type == consts.BOOLEAN:
                if value.upper() in [consts.language('yes').upper(), consts.language('true').upper()]:
                    self.value = True
                else:
                    self.value = False
            elif self.data_type == consts.KEYS:
                pass
            else:
                self.value = value

    @property
    def raw_value(self): # depricated
        return self.data

    @property
    def value(self):
        return self.get_value()

    def get_value(self, data=None):
        if data is None:
            result = self.data
        else:
            result = data
        if result is None:
            if self.field_kind == consts.ITEM_FIELD:
                if self.data_type in (consts.FLOAT, consts.INTEGER, consts.CURRENCY):
                    result = 0
                elif self.data_type == consts.BOOLEAN:
                    result = False
                elif self.data_type in [consts.TEXT, consts.LONGTEXT]:
                    result = ''
                elif self.data_type == consts.KEYS:
                    result = []
        else:
            if self.data_type == consts.TEXT:
                if not isinstance(result, str):
                    result = to_str(result, 'utf-8')
            elif self.data_type in (consts.FLOAT, consts.CURRENCY):
                result = float(result)
            elif self.data_type == consts.DATE:
                result = consts.convert_date(result)
            elif self.data_type == consts.DATETIME:
                result = consts.convert_date_time(result)
            elif self.data_type == consts.BOOLEAN:
                result = bool(result)
            elif self.data_type == consts.KEYS:
                result = self.data_to_keys(result)
            elif self.data_type == consts.FILE:
                result = self.get_secure_file_name(result)
        return result

    @value.setter
    def value(self, value):
        self.set_value(value)

    def _change_lookup_field(self, lookup_value=None):
        if self.lookup_item:
            if self.owner:
                master_field = self
                if self.master_field:
                    master_field = self.master_field
                master_field.lookup_value = None
                for field in self.owner.fields:
                    if field.master_field == master_field:
                        field.lookup_value = None
            if lookup_value:
                self.lookup_value = lookup_value

    def _do_before_changed(self):
        if self.owner and not self.owner.is_changing():
            raise DatasetInvalidState(consts.language('not_edit_insert_state') % self.owner.item_name)

    def _check_system_field_value(self, value):
        if self.field_kind == consts.ITEM_FIELD:
            if self.field_name == self.owner._primary_key and self.value and self.value != value:
                raise DatasetException(consts.language('no_primary_field_changing') % self.owner.item_name)
            if self.field_name == self.owner._deleted_flag and self.value != value:
                raise DatasetException(consts.language('no_deleted_field_changing') % self.owner.item_name)
            if self.calculated:
                raise DatasetException('Calculated field can not be changed')

    def set_value(self, value, lookup_value=None):
        self._check_system_field_value(value)
        if self.field_kind == consts.ITEM_FIELD and not self.owner.is_changing():
            self.owner.edit()
        self.new_value = None
        if not value is None:
            self.new_value = value
            try:
                if self.data_type == consts.TEXT:
                    self.new_value = to_str(value, 'utf-8')
                elif self.data_type == consts.FLOAT:
                    self.new_value = float(value)
                elif self.data_type == consts.CURRENCY:
                    self.new_value = consts.round(value, consts.FRAC_DIGITS)
                elif self.data_type == consts.INTEGER:
                    self.new_value = int(value)
                elif self.data_type == consts.BOOLEAN:
                    if bool(value):
                        self.new_value = 1
                    else:
                        self.new_value = 0
                elif self.data_type == consts.KEYS:
                    self.new_value = ';'.join([str(v) for v in value])
            except TypeError as e:
                raise FieldInvalidValue(self.type_error(value))
            except ValueError as e:
                raise FieldInvalidValue(self.type_error(value))
        if self.data != self.new_value:
            self._do_before_changed()
            self.data = self.new_value
            self._change_lookup_field(lookup_value)
            self._set_modified(True)

    def type_error(self, value):
        if self.data_type == consts.INTEGER:
            mess = consts.language('invalid_int')
        elif self.data_type == consts.FLOAT:
            mess = consts.language('invalid_float')
        elif self.data_type == consts.CURRENCY:
            mess = consts.language('invalid_cur')
        elif (self.data_type == consts.DATE) or (self.data_type == consts.DATE):
            mess = consts.language('invalid_date')
        elif self.data_type == consts.BOOLEAN:
            mess = consts.language('invalid_bool')
        else:
            mess = consts.language('invalid_value')
        try:
            val = to_str(value)
            mess = mess % val
        except:
            mess = mess.replace('%s', '')
        return mess

    @property
    def cur_data(self):
        if self.owner._is_delta:
            if self.row and self.bind_index >= 0:
                result = None
                self.owner.init_history()
                cur_row = self.owner.change_log.record_info.cur_record
                if cur_row:
                    result = cur_row[self.bind_index]
                return result
        else:
            raise Exception('Only delta can have cur value property.')

    @property
    def old_value(self):
        return self.get_value(self.cur_data)

    @property
    def cur_value(self):
        return self.get_value(self.cur_data)

    def _set_modified(self, value):
        if self.owner:
            self.owner._set_modified(value)

    @property
    def _lookup_field(self):
        if self.lookup_item:
            if self.lookup_field2:
                return self.lookup_item2._field_by_name(self.lookup_field2)
            elif self.lookup_field1:
                return self.lookup_item1._field_by_name(self.lookup_field1)
            else:
                return self.lookup_item._field_by_name(self.lookup_field)

    @property
    def lookup_data_type(self):
        if self.lookup_item:
            return self._lookup_field.data_type
        else:
            return self.data_type

    def _get_value_in_list(self, value):
        result = '';
        if isinstance(value, str):
            return value
        try:
            for val, str_val in self.lookup_values:
                if val == value:
                    result = str_val
        except:
            pass
        return result

    def get_secure_file_name(self, data):
        result = data
        if result is None:
            result = ''
        else:
            sep_pos = data.find('?')
            if sep_pos != -1:
                result = result[0:sep_pos]
        return result

    def get_file_name(self, data):
        result = data
        if result is None:
            result = ''
        else:
            sep_pos = data.find('?')
            if sep_pos != -1:
                result = result[sep_pos+1:]
        return result

    def data_to_keys(self, data):
        try:
            return [int(val) for val in data.split(';')]
        except:
            return []

    @property
    def lookup_value(self):
        result = None
        if self.data_type == consts.KEYS:
            result = self.value
        elif self.lookup_item and (self.field_kind != consts.ITEM_FIELD or self.owner.expanded):
            lookup_field = self._lookup_field
            data_type = lookup_field.data_type
            result = self.lookup_data
            if data_type == consts.DATE:
                if isinstance(result, text_type):
                    result = consts.convert_date(result)
            elif data_type == consts.DATETIME:
                if isinstance(result, text_type):
                    result = consts.convert_date_time(result)
            elif data_type == consts.BOOLEAN:
                result = bool(result)
            elif data_type == consts.KEYS:
                result = self.data_to_keys(result)
            elif data_type == consts.FILE:
                result = self.get_secure_file_name(result)
        else:
            result = self.value
        return result

    @lookup_value.setter
    def lookup_value(self, value):
        if self.lookup_item:
            self.lookup_data = value

    @property
    def lookup_text(self):
        if self.data_type == consts.KEYS:
            return self.text
        elif self.lookup_item and (self.field_kind != consts.ITEM_FIELD or self.owner.expanded):
            return self._value_to_text(self.lookup_data, self.lookup_value, self.lookup_data_type)
        else:
            return self.text

    @property
    def display_text(self):
        if self.lookup_item and (self.field_kind != consts.ITEM_FIELD or self.owner.expanded):
            lookup_field = self._lookup_field
            data_type = lookup_field.data_type
            if lookup_field.lookup_values:
                result = lookup_field._get_value_in_list(self.lookup_data)
            elif data_type == consts.CURRENCY:
                result = self.cur_to_str(self.lookup_data)
            elif data_type == consts.FILE:
                result = self.get_file_name(self.lookup_data)
            else:
                result = self.lookup_text
        else:
            if self.data_type == consts.CURRENCY:
                result = self.cur_to_str(self.data)
            elif self.data_type == consts.FILE:
                result = self.get_file_name(self.data)
            elif self.lookup_values:
                result = self._get_value_in_list(self.data)
            else:
                result = self.lookup_text
        if self.owner and not self.filter:
            if self.owner.on_field_get_text:
                if not self.on_field_get_text_called:
                    self.on_field_get_text_called = True
                    try:
                        res = self.owner.on_field_get_text(self)
                        if not res is None:
                            result = res
                    finally:
                        self.on_field_get_text_called = False
        return result

    @property
    def file_path(self):
        if self.data_type in (consts.FILE, consts.IMAGE):
            if self.value:
                dir_path = to_str(self.owner.task.work_dir, 'utf-8')
                return os.path.join(dir_path, 'static', 'files', self.value)
            else:
                return ''

    def get_default_value(self):
        result = None
        if self.default_value:
            try:
                if self.data_type == consts.INTEGER:
                    result = int(self.default_value)
                elif self.data_type == consts.FLOAT:
                    result = float(self.default_value)
                elif self.data_type == consts.CURRENCY:
                    result = consts.round(self.default_value, consts.FRAC_DIGITS)
                elif self.data_type == consts.DATE:
                    if self.default_value == 'current date':
                        result = datetime.date.today()
                elif self.data_type == consts.DATETIME:
                    if self.default_value == 'current datetime':
                        result = datetime.datetime.now()
                elif self.data_type == consts.BOOLEAN:
                    if self.default_value == 'true':
                        result = 1
                    elif self.default_value == 'false':
                        result = 0
                elif self.data_type in [consts.TEXT, consts.LONGTEXT, \
                    consts.IMAGE, consts.FILE, consts.KEYS]:
                    result = self.default_value
            except Exception as e:
                self.owner.log.exception(error_message(e))
        return result

    def assign_default_value(self):
        self.data = self.get_default_value()

    def check_type(self):
        if (self.data_type == consts.TEXT) and (self.field_size != 0) and \
            (len(self.text) > self.field_size):
            raise FieldInvalidLength('%s: %s' % (self.field_caption, consts.language('invalid_length') % self.field_size))
        return True

    def check_reqired(self):
        if self.required and self.data is None:
            raise FieldValueRequired('%s: %s' % (self.field_caption, consts.language('value_required')))
        return True

    def check_valid(self):
        if self.check_reqired():
            self.check_type()
        return True

    def system_field(self):
        if self.field_name and self.field_name in (self.owner._primary_key,  \
            self.owner._deleted_flag, self.owner._master_id, self.owner._master_rec_id, self.owner._master_field):
            return True

    def float_to_str(self, value):
        return consts.float_to_str(value)

    def cur_to_str(self, value):
        return consts.cur_to_str(value)

    def date_to_str(self, value):
        return consts.date_to_str(value)

    def datetime_to_str(self, value):
        return consts.datetime_to_str(value)

    def str_to_date(self, value):
        return consts.str_to_date(value)

    def str_to_datetime(self, value):
        return consts.str_to_datetime(value)

    def str_to_float(self, value):
        return consts.str_to_float(value)

    def str_to_cur(self, value):
        return consts.str_to_cur(value)

class FilterField(DBField):
    def __init__(self, fltr, field, owner):
        DBField.__init__(self, owner, field.field_def)
        self.field_kind = consts.FILTER_FIELD
        self.filter = fltr
        self.lookup_item = None
        self._value = None
        self._lookup_value = None

    def _do_before_changed(self):
        pass

    @property
    def data(self):
        return self._value

    @data.setter
    def data(self, value):
        self._value = value

    def get_lookup_data(self):
        return self._lookup_value

    def set_lookup_data(self, value):
        self._lookup_value = value

    def check_reqired(self, value):
        return True

    def _set_modified(self, value):
        pass

    def _set_record_status(self, value):
        pass

class DBFilter(object):
    def __init__(self, owner, filter_def):
        self.owner = owner
        self.filter_def = filter_def
        self.filter_name = filter_def[FILTER_OBJ_NAME]
        self.filter_caption = filter_def[FILTER_NAME]
        self.field_name = filter_def[FILTER_FIELD_NAME]
        self.filter_type = filter_def[FILTER_TYPE]
        self.data_type = filter_def[FILTER_DATA_TYPE]
        self.multi_select_all = filter_def[FILTER_MULTI_SELECT]
        self.visible = filter_def[FILTER_VISIBLE]
        self.filter_help = filter_def[FILTER_HELP]
        if type(self.field_name) == int:
            self.field_name = owner._field_by_ID(self.field_name).field_name
        field = self.owner._field_by_name(self.field_name)
        if self.field_name:
            self.field = FilterField(self, field, self.owner)
            setattr(self, self.field_name, self.field)
            if self.filter_type in (consts.FILTER_IN, consts.FILTER_NOT_IN):
                self.field.multi_select = True;
            if self.filter_type == consts.FILTER_RANGE:
                self.field1 = FilterField(self, field, self.owner)

    def __setattr__(self, name, value):
        if name != 'owner' and self.owner and self.owner.task_locked():
            raise Exception(consts.language('server_tree_immutable') + \
                ' Item: "%s", Filter: "%s", attribute: "%s"' % (self.owner.item_name, self.filter_name, name))
        super(DBFilter, self).__setattr__(name, value)

    @property
    def value(self):
        return self.field.data

    @value.setter
    def value(self, value):
        if not isinstance(value, FilterField):
            if self.filter_type == consts.FILTER_RANGE:
                if value is None:
                    self.field.value = None;
                    self.field1.value = None;
                else:
                    self.field.value = value[0];
                    self.field1.value = value[1];
            else:
                self.field.value = value

class DBList(list):
    pass


class RecInfo(object):
    def __init__(self, item):
        self.item = item;
        self.record_status = consts.RECORD_UNCHANGED;
        self.log_index = None;
        self.details = {};
        self.cur_record = None

    def add_detail(self, detail_change_log):
        self.details[detail_change_log.item.ID] = detail_change_log;

    def get_changes(self, updates=None):
        result = {};
        for ID, detail in self.details.items():
            detail_changes = {}
            detail.get_changes(detail_changes, updates)
            result[ID] = detail_changes;
        return result;

    def set_changes(self, details):
        for ID, detail in details.items():
            item = self.item.item_by_ID(int(ID))
            change_log = ChangeLog(item, True)
            self.details[int(ID)] = change_log
            change_log.set_changes(details[ID])

    def update(self, details):
        self.log_index = None;
        for ID, detail in details.items():
            self.details[ID].update(detail)

    def copy(self):
        result = RecInfo(self.item);
        result.record_status  = self.record_status
        result.log_index = self.log_index
        result.details = {}
        for ID, detail in self.details.items():
            result.details[ID] = self.details[ID].copy()
        return result;

    def restore(self):
        for ID, detail in self.details.items():
            self.details[ID].restore()

    def print_log(self, indent):
        indent += '    '
        for ID, detail in self.details.items():
            self.details[ID].print_log(indent)

class ChangeLog(object):
    def __init__(self, item, copy=None):
        self.item = item
        self.expanded = item.expanded
        self.logs = []
        self.dataset = item._dataset
        self.fields = []
        self.db_record = None
        for field in self.item.fields:
            self.fields.append(field.field_name)
        if self.item.master and not copy:
            self.item.master.change_log.record_info.add_detail(self)

    def detail_change_log(self, detail):
        return self.record_info.details.get(detail.ID)

    @property
    def cur_record(self):
        return self.item._dataset[self.item.rec_no]

    @cur_record.setter
    def cur_record(self, value):
        self.item._dataset[self.item.rec_no] = value

    @property
    def record_info(self):
        return self.get_record_info()

    def get_record_info(self, record=None):
        if not record:
            record = self.cur_record
        if len(record) < self.item._record_info_index + 1:
            record.append(RecInfo(self.item))
        return record[self.item._record_info_index]

    @property
    def record_status(self):
        return self.record_info.record_status

    @record_status.setter
    def record_status(self, value):
        if self.record_info.log_index == None:
            if value != consts.RECORD_UNCHANGED:
                self.logs.append(self.cur_record)
                self.record_info.log_index = len(self.logs) - 1
        else:
            if value == consts.RECORD_UNCHANGED:
                self.logs[self.record_info.log_index] = None
                self.cur_record[self.item._record_info_index] = RecInfo(self.item)
            else:
                self.logs[self.record_info.log_index] = self.cur_record;
        self.record_info.record_status = value

    @property
    def empty(self):
        for log in self.logs:
            if log:
                return False
        return True

    def detail_modified(self):
        if self.record_status == consts.RECORD_UNCHANGED:
            self.record_status = consts.RECORD_DETAILS_MODIFIED
        if self.item.master:
            self.item.master.change_log.detail_modified()

    def log_change(self):
        state = self.item.item_state
        if self.item.log_changes:
            if state == consts.STATE_INSERT:
                self.record_status = consts.RECORD_INSERTED
            elif state == consts.STATE_EDIT:
                if self.record_status == consts.RECORD_UNCHANGED:
                    self.record_status = consts.RECORD_MODIFIED
                elif self.record_status == consts.RECORD_DETAILS_MODIFIED:
                    self.record_status = consts.RECORD_MODIFIED
            elif state == consts.STATE_DELETE:
                if self.record_status == consts.RECORD_INSERTED:
                    self.record_status = consts.RECORD_UNCHANGED
                else:
                    self.record_status = consts.RECORD_DELETED
            else:
                raise Exception('Item %s: change log invalid records state' % self.item.item_name)
            if self.item.master:
                self.item.master.change_log.detail_modified()

    def copy_record(self, record):
        return record[:self.item._record_info_index]

    def get_changes(self, result, updates=None):
        logs = []
        counter = 0
        if not updates:
            result['fields'] = self.fields
            result['expanded'] = self.expanded
        result['logs'] = logs
        for record in self.logs:
            if record:
                record_info = self.get_record_info(record)
                if record_info.record_status != consts.RECORD_UNCHANGED:
                    new_record = self.copy_record(record)
                    log_index = record_info.log_index
                    if updates:
                        log_index = record_info.index
                    logs.append({
                        'record_status': record_info.record_status,
                        'log_index': log_index,
                        'record': new_record,
                        'details': record_info.get_changes(updates)
                    })
                    counter += 1
        return counter

    def set_changes(self, changes):
        self.fields = changes['fields']
        self.expanded = changes['expanded']
        self.logs = []
        self.dataset = []
        logs = changes['logs']
        for log in logs:
            record = log['record']
            record_info = RecInfo(self.item)
            record.append(record_info)
            record_info.record_status = log['record_status']
            record_info.index = log['log_index']
            self.dataset.append(record)
            self.logs.append(record)
            record_info.log_index = len(self.dataset) - 1
            record_info.set_changes(log['details'])

    def prepare_updates(self):
        result = {}
        self.get_changes(result, updates=True)
        return result

    def update(self, updates):
        if updates:
            for log in updates['logs']:
                log_index = log['log_index']
                record = log['record']
                details = log['details']
                log_record = self.logs[log_index]
                rec_info = self.get_record_info(log_record)
                if rec_info.record_status != consts.RECORD_DELETED:
                    rec = record[:self.item._record_lookup_index]
                    log_record[:self.item._record_lookup_index] = rec
                rec_info.record_status = consts.RECORD_UNCHANGED
                rec_info.update(details)
            self.logs = []

    def copy(self):
        result = ChangeLog(self.item, True)
        result.logs = []
        result.fields = list(self.fields)
        result.dataset = []
        result.rec_no = None
        if self.dataset:
            result.rec_no = self.item.rec_no
            for record in self.dataset:
                rec_info_copy = self.get_record_info(record).copy()
                rec_copy = list(record)
                rec_copy[self.item._record_info_index] = rec_info_copy
                if rec_info_copy.log_index != None:
                    result.logs.append(rec_copy)
                    rec_info_copy.log_index = len(result.logs) - 1
                result.dataset.append(rec_copy)
        return result

    def restore(self):
        self.item._dataset = self.dataset
        if not self.rec_no is None:
            self.item.rec_no = self.rec_no
        if self.dataset:
            self.record_info.restore()

    def store_record(self):
        self.record_info
        result = list(self.cur_record)
        result[self.item._record_info_index] = self.record_info.copy()
        return result

    def restore_record(self, data):
        self.record_status = consts.RECORD_UNCHANGED
        self.cur_record = data
        self.rec_no = None
        self.restore()
        self.record_status = self.record_status

    def print_log(self, indent=None):
        if indent is None:
            indent = ''
        for log in self.logs:
            rec_info = self.get_record_info(log)
            rec_info.print_log(indent)

class AbstractDataSet(object):
    def __init__(self):
        self.ID = 0
        self.field_defs = []
        self._fields = []
        self.fields = []
        self.filter_defs = []
        self.filters = DBList()
        self.details = DBList()
        self.master = None
        self.master_applies = None
        self.change_log = None
        self.expanded = True
        self._log_changes = True
        self._dataset = []
        self._primary_key = None
        self._deleted_flag = None
        self._record_version = None
        self.master_field = None
        self._lookup_refs = {}
        self._master_field = None
        self._master_field_db_field_name = None
        self._master_id = None
        self._master_rec_id = None
        self._primary_key_db_field_name = None
        self._deleted_flag_db_field_name = None
        self._record_version_db_field_name = None
        self._master_id_db_field_name = None
        self._master_rec_id_db_field_name = None
        self.__eof = False
        self.__bof = False
        self.__cur_row = None
        self.__old_row = 0
        self._buffer = None
        self._modified = None
        self._state = consts.STATE_INACTIVE
        self._read_only = False
        self._active = False
        self._copy_of = None
        self._virtual_table = False
        self._where_list = []
        self._order_by_list = []
        self._select_field_list = []
        self.on_state_changed = None
        self.on_filter_changed = None
        self._record_lookup_index = -1
        self._record_info_index = -1
        self.expanded = True
        self._open_params = {}
        self._disabled_count = 0
        self._is_delta = False
        self.soft_delete = None
        self.keep_history = False
        self.edit_lock = False
        self.select_all = False
        self.on_field_get_text = None
        self._apply_connection = None

    def __getitem__(self, key):
        if key == 0:
            self.first()
        else:
            self.next()
        if self.eof():
            raise IndexError
        return self

    def add_field_def(self, field_id, field_name, field_caption, data_type, size=0, required=False,
            lookup_item=None, lookup_field=None, visible=True, read_only=False, default=None, default_value=None,
            master_field=None, alignment=None, lookup_values=None, enable_typeahead=False, field_help=None,
            field_placeholder=None, lookup_field1=None, lookup_field2=None, db_field_name=None, field_mask=None,
            image_edit_width=None, image_edit_height=None, image_view_width=None, image_view_height=None,
            image_placeholder=None, image_camera=None, file_download_btn=None, file_open_btn=None, file_accept=None,
            calc_item=None, calc_lookup_field=None, calc_field=None, calc_op=None, textarea=None, do_not_sanitize=None
            ):
        if not db_field_name:
            db_field_name = field_name.upper()
        field_def = [None for i in range(len(FIELD_DEF) + 10)]
        field_def[FIELD_ID] = field_id
        field_def[FIELD_NAME] = field_name
        field_def[FIELD_CAPTION] = field_caption
        field_def[FIELD_DATA_TYPE] = data_type
        field_def[REQUIRED] = required
        field_def[LOOKUP_ITEM] = lookup_item
        field_def[MASTER_FIELD] = master_field
        field_def[LOOKUP_FIELD] = lookup_field
        field_def[LOOKUP_FIELD1] = lookup_field1
        field_def[LOOKUP_FIELD2] = lookup_field2
        field_def[FIELD_READ_ONLY] = read_only
        field_def[FIELD_VISIBLE] = visible
        field_def[FIELD_SIZE] = size
        field_def[FIELD_DEFAULT] = default
        field_def[FIELD_DEFAULT_VALUE] = default_value
        field_def[FIELD_ALIGNMENT] = alignment
        field_def[FIELD_LOOKUP_VALUES] = lookup_values
        field_def[FIELD_ENABLE_TYPEAHEAD] = enable_typeahead
        field_def[FIELD_HELP] = field_help
        field_def[FIELD_PLACEHOLDER] = field_placeholder
        field_def[FIELD_INTERFACE] = {'field_mask': field_mask,
            'textarea': textarea, 'do_not_sanitize': do_not_sanitize}
        if data_type == consts.IMAGE:
            field_def[FIELD_IMAGE] = {'edit_width': image_edit_width,
                'edit_height': image_edit_height, 'view_width': image_view_width,
                'view_height': image_view_height, 'placeholder': image_placeholder,
                'camera': image_camera}
        if data_type == consts.FILE:
            field_def[FIELD_FILE] = {'download_btn': file_download_btn, 'open_btn': file_open_btn, 'accept': file_accept}
        if calc_item:
            field_def[FIELD_CALC] = {'calc_item': calc_item, 'calc_lookup_field': calc_lookup_field,
                'calc_field': calc_field, 'calc_op': calc_op}
        field_def[DB_FIELD_NAME] = db_field_name
        self.field_defs.append(field_def)
        return field_def

    def field_def_restrictions(self, field_def, role_id):
        prohibited = False
        read_only = False
        if not consts.SAFE_MODE or not role_id or not self.task.ID:
            return prohibited, read_only
        restrictions = self.task.app.get_role_field_restrictions(role_id)
        for index in [FIELD_ID, MASTER_FIELD, LOOKUP_FIELD, LOOKUP_FIELD1, LOOKUP_FIELD2]:
            ID = field_def[index]
            if ID:
                r = restrictions.get(ID)
                if r:
                    if index == FIELD_ID:
                        read_only = r['read_only']
                    prohibited = r['prohibited']
                    if prohibited:
                        break
        return prohibited, read_only

    def get_field_defs(self, role_id):
        result = []
        for field_def in self.field_defs:
            prohibited, read_only = self.field_def_restrictions(field_def, role_id)
            if not prohibited:
                fd = field_def[:]
                if read_only:
                    fd[FIELD_READ_ONLY] = True
                fd[DB_FIELD_NAME] = ''
                fd[FIELD_CALC] = bool(fd[FIELD_CALC])
                result.append(fd)
        return result

    def get_filter_defs(self, role_id):
        result = []
        for filter_def in self.filter_defs:
            prohibited = self.check_field_restricted(filter_def[FILTER_FIELD_NAME], 'prohibited', role_id)
            if not prohibited:
                result.append(filter_def)
        return result

    def add_filter_def(self, filter_name, filter_caption, field_name, filter_type,
            multi_select_all, data_type, visible, filter_help, filter_placeholder, filter_ID):
        filter_def = [None for i in range(len(FILTER_DEF))]
        filter_def[FILTER_OBJ_NAME] = filter_name
        filter_def[FILTER_NAME] = filter_caption
        filter_def[FILTER_FIELD_NAME] = field_name
        filter_def[FILTER_TYPE] = filter_type
        filter_def[FILTER_MULTI_SELECT] = multi_select_all
        filter_def[FILTER_DATA_TYPE] = data_type
        filter_def[FILTER_VISIBLE] = visible
        filter_def[FILTER_HELP] = filter_help
        filter_def[FILTER_PLACEHOLDER] = filter_placeholder
        filter_def[FILTER_ID] = filter_ID
        self.filter_defs.append(filter_def)
        return filter_def

    @property
    def virtual_table(self):
        return self._virtual_table

    @property
    def dataset(self):
        result = []
        if self.active:
            for r in self._dataset:
                result.append(r[0:self._record_info_index])
        return result

    @dataset.setter
    def dataset(self, value):
        self._dataset = value

    @property
    def lock_active(self):
        if self.active:
            return self.edit_lock and self._record_version_field

    def _copy(self, filters=True, details=True, handlers=True):
        result = self.__class__(self.task, None, self.item_name, self.item_caption)
        result.ID = self.ID
        result.item_name = self.item_name
        result.expanded = self.expanded
        result.field_defs = self.field_defs
        result.filter_defs = self.filter_defs
        result._virtual_table = self._virtual_table
        result.keep_history = self.keep_history
        result.edit_lock = self.edit_lock
        result.select_all = self.select_all
        result.visible = self.visible
        result.master_field = self.master_field
        result.master_applies = self.master_applies
        result._copy_of = self._copy_of

        for field_def in result.field_defs:
            field = DBField(result, field_def)
            result._fields.append(field)
        result.__prepare_fields()

        if filters:
            for filter_def in result.filter_defs:
                fltr = DBFilter(result, filter_def)
                result.filters.append(fltr)
            result.__prepare_filters()

        result._events = self._events
        if handlers:
            for func_name, func in result._events:
                setattr(result, func_name, func)
        return result

    def clone(self):
        result = self.__class__(self.task, None, self.item_name, self.item_caption)
        result.ID = self.ID
        result.item_name = self.item_name
        result.field_defs = self.field_defs
        result.filter_defs = self.filter_defs
        result.visible = self.visible

        for field_def in result.field_defs:
            field = DBField(result, field_def)
            result._fields.append(field)
        result.__prepare_fields()

        for field in result.fields:
            if hasattr(result, field.field_name):
                delattr(result, field.field_name)

        result.fields = [];
        for field in self.fields:
            new_field = result._field_by_name(field.field_name)
            result.fields.append(new_field)
            if not hasattr(result, new_field.field_name):
                setattr(result, new_field.field_name, new_field)
        result._bind_fields()
        result._dataset = self._dataset
        result._active = True
        result.first()
        return result

    def _prepare_dataset(self):
        self.__prepare_fields()
        self.__prepare_filters()

    def _lookup_item_is_master(self, lookup_item):
        for detail in lookup_item.details:
            if detail.prototype.ID == self.ID:
                return True

    def __prepare_fields(self):
        for field in self._fields:
            if field.lookup_item and type(field.lookup_item) == int:
                field.lookup_item = self.task.item_by_ID(field.lookup_item)
                if self.task.ID and \
                    not self.master and not field.master_field and \
                    not self._lookup_item_is_master(field.lookup_item):
                    if self.task.item_by_ID(self.ID) == self:
                        if not field.lookup_item._lookup_refs.get(self):
                            field.lookup_item._lookup_refs[self] = []
                        field.lookup_item._lookup_refs[self].append(field)
            if field.master_field and type(field.master_field) == int:
                field.master_field = self._field_by_ID(field.master_field)
            if field.lookup_field and type(field.lookup_field) == int:
                lookup_field = field.lookup_item._field_by_ID(field.lookup_field)
                field.lookup_field = lookup_field.field_name
                field.lookup_db_field = lookup_field.db_field_name
                if lookup_field.lookup_item and field.lookup_field1:
                    field.lookup_item1 = lookup_field.lookup_item
                    if type(field.lookup_item1) == int:
                        field.lookup_item1 = self.task.item_by_ID(field.lookup_item1)
                    if type(field.lookup_field1) == int:
                        lookup_field1 = field.lookup_item1._field_by_ID(field.lookup_field1)
                        field.lookup_field1 = lookup_field1.field_name
                        field.lookup_db_field1 = lookup_field1.db_field_name
                    if lookup_field1.lookup_item and field.lookup_field2:
                        field.lookup_item2 = lookup_field1.lookup_item
                        if type(field.lookup_item2) == int:
                            field.lookup_item2 = self.task.item_by_ID(field.lookup_item2)
                        if type(field.lookup_field2) == int:
                            lookup_field2 = field.lookup_item2._field_by_ID(field.lookup_field2)
                            field.lookup_field2 = lookup_field2.field_name
                            field.lookup_db_field2 = lookup_field2.db_field_name
            elif field.lookup_values and type(field.lookup_values) == int:
                try:
                    field.lookup_values = self.task.lookup_lists[field.lookup_values]
                except:
                    pass
            elif field.calculated:
                if type(field.calculated['calc_item']) == int:
                    field._calc_item = self.task.item_by_ID(field.calculated['calc_item'])
                    field._calc_on_field = field._calc_item._field_by_ID(field.calculated['calc_lookup_field'])
                    field._calc_field = field._calc_item._field_by_ID(field.calculated['calc_field'])
                    field._calc_op = field.calculated['calc_op']

        self.fields = list(self._fields)
        for field in self.fields:
            if not hasattr(self, field.field_name):
                setattr(self, field.field_name, field)
        self._master_field = self.master_field
        for sys_field_name in ['_primary_key', '_deleted_flag', '_master_id',
            '_master_rec_id', '_record_version', '_master_field']:
            sys_field = getattr(self, sys_field_name)
            if sys_field and type(sys_field) == int:
                field = self.field_by_ID(sys_field)
                if field:
                    setattr(self, sys_field_name, field.field_name)
                    setattr(self, '%s_%s' % (sys_field_name, 'db_field_name'), field.db_field_name)
        self.master_field = self._master_field

    def __prepare_filters(self):
        for fltr in self.filters:
            setattr(self.filters, fltr.filter_name, fltr)
            if fltr.field.lookup_item and type(fltr.field.lookup_item) == int:
                fltr.field.lookup_item = self.task.item_by_ID(fltr.field.lookup_item)

    def field_by_name(self, field_name):
        for field in self.fields:
            if field.field_name == field_name:
                return field

    def _field_by_name(self, field_name):
        for field in self._fields:
            if field.field_name == field_name:
                return field

    def field_by_ID(self, id_value):
        for field in self.fields:
            if field.ID == id_value:
                return field

    def _field_by_ID(self, id_value):
        for field in self._fields:
            if field.ID == id_value:
                return field

    def filter_by_name(self, name):
        for fltr in self.filters:
            if fltr.filter_name == name:
                return fltr

    @property
    def log_changes(self):
        return self._log_changes

    @log_changes.setter
    def log_changes(self, value):
        self._log_changes = value

    def _set_modified(self, value):
        self._modified = value

    def is_modified(self):
        return self._modified

    @property
    def active(self):
        return self._active

    @property
    def item_state(self):
        return self._state

    @item_state.setter
    def item_state(self, value):
        if self._state != value:
            self._state = value
            if self.on_state_changed:
                self.on_state_changed(self)

    def _do_after_scroll(self):
        pass

    def _do_before_scroll(self):
        if self.is_changing():
            self.post()

    def skip(self, value, trigger_events=True):
        if self.record_count() == 0:
            self.__cur_row = None
            if trigger_events:
                self._do_before_scroll()
            self.__eof = True
            self.__bof = True
            if trigger_events:
                self._do_after_scroll()
        else:
            old_row = self.__cur_row
            eof = False
            bof = False
            new_row = value
            if new_row < 0:
                new_row = 0
                bof = True
            if new_row >= len(self._dataset):
                new_row = len(self._dataset) - 1
                eof = True
            self.__eof = eof
            self.__bof = bof
            if old_row != new_row:
                if trigger_events:
                    self._do_before_scroll()
                self.__cur_row = new_row
                if trigger_events:
                    self._do_after_scroll()
        self.__old_row = self.__cur_row


    @property
    def rec_no(self):
        if self._active:
            return self.__cur_row

    @rec_no.setter
    def rec_no(self, value):
        self.skip(value)

    def first(self):
        self.rec_no = 0

    def last(self):
        self.rec_no = len(self._dataset) - 1

    def next(self):
        self.rec_no += 1

    def prior(self):
        self.rec_no -= 1

    def eof(self):
        if self.active:
            return self.__eof
        else:
            return True

    def bof(self):
        if self.active:
            return self.__bof
        else:
            return True

    @property
    def rec_count(self):
        if self._dataset:
            return len(self._dataset)
        else:
            return 0

    def record_count(self):
        return self.rec_count

    def do_internal_open(self):
        pass

    def _bind_fields(self, expanded=True):
        for field in self.fields:
            field.bind_index = None
            field.lookup_index = None
        j = 0
        for field in self.fields:
            if not field.master_field and not field.calculated:
                field.bind_index = j
                j += 1
        for field in self.fields:
            if field.master_field:
                field.bind_index = field.master_field.bind_index
        self._record_lookup_index = j
        if expanded:
            for field in self.fields:
                if field.calculated:
                    field.bind_index = j;
                    j += 1;
            for field in self.fields:
                if field.lookup_item:
                    field.lookup_index = j
                    j += 1
        self._record_info_index = j

    def get_where_list(self, field_dict):
        result = []
        for field_arg in field_dict.keys():
            field_name = field_arg
            value = field_dict[field_name]
            arr = field_name.split('__');
            field_name = arr[0]
            if len(arr) >= 2:
                filter_str = arr[1]
            else:
                filter_str = 'eq';
            filter_type = consts.FILTER_STR.index(filter_str)
            if filter_type != -1:
                filter_type += 1
            else:
                raise RuntimeError('%s: set_where method argument error %s' % (self.item_name, field_arg))
            field = self._field_by_name(field_name)
            if not field:
                if type(value) == list and type(value[0]) == list:
                    array = []
                    for v in value:
                        d = {}
                        d[v[0]] = v[1]
                        array.append(self.get_where_list(d))
                    result.append(array)
                    continue
                raise RuntimeError('%s: set_where method argument error %s: ' % (self.item_name, field_arg))
            value = field_dict[field_arg]
            if not value is None:
                result.append([field_name, filter_type, value])
        return result

    def set_fields(self, lst=None, *fields):
        field_list = []
        if lst:
            if type(lst) in (list, tuple):
                field_list = list(lst)
            else:
                field_list.append(lst)
        field_list = field_list + list(fields)
        self._select_field_list = field_list

    def set_where(self, dic=None, **fields):
        field_dict = {}
        if dic:
            field_dict = dic
        if fields:
            for key, value in fields.items():
                field_dict[key] = value
        self._where_list = self.get_where_list(field_dict)

    def get_order_by_list(self, field_list):
        result = []
        for field in field_list:
            field_name = field
            desc = False
            if field[0] == '-':
                desc = True
                field_name = field[1:]
            try:
                fld = self._field_by_name(field_name)
            except:
                raise RuntimeError('%s: order_by param error - %s' % (self.item_name, field))
            result.append([fld.field_name, desc])
        return result

    def set_order_by(self, lst=None, *fields):
        field_list = []
        if lst:
            if type(lst) in (list, tuple):
                field_list = list(lst)
            else:
                field_list.append(lst)
        field_list = field_list + list(fields)
        self._order_by_list = self.get_order_by_list(field_list)

    def _update_fields(self, fields):
        for field in self.fields:
            if hasattr(self, field.field_name):
                delattr(self, field.field_name)
        if not fields and self._select_field_list:
            fields = self._select_field_list
        if fields:
            self.fields = []
            for field_name in fields:
                field = self._field_by_name(field_name)
                if field:
                    self.fields.append(field)
                else:
                    raise Exception('%s - _do_before_open method error: there is no field with field_name: %s' % (self.item_name, field_name))
        else:
            self.fields = list(self._fields)
        for field in self.fields:
            if not hasattr(self, field.field_name):
                setattr(self, field.field_name, field)
        for sys_field_name in ['_primary_key', '_deleted_flag', '_master_field', '_master_id', '_master_rec_id', '_record_version']:
            sys_field = getattr(self, sys_field_name)
            if sys_field:
                field = self.field_by_name(sys_field)
                setattr(self, sys_field_name + '_field', field)
        result = []
        for field in self.fields:
            result.append(field.field_name)
        return result

    def _do_before_open(self, expanded, fields, where, order_by, open_empty,
        params, offset, limit, funcs, group_by):

        result = None
        params['__expanded'] = expanded
        params['__fields'] = []
        params['__filters'] = []
        filters = []

        fields = self._update_fields(fields)
        self._select_field_list = []
        if fields:
            params['__fields'] = fields
        if not open_empty:
            params['__limit'] = 0
            params['__offset'] = 0
            if limit:
                params['__limit'] = limit
                if offset:
                    params['__offset'] = offset
            if not where is None:
                filters = self.get_where_list(where)
            elif self._where_list:
                filters = list(self._where_list)
            else:
                if self.filters:
                    for fltr in self.filters:
                        if not fltr.value is None:
                            filters.append([fltr.field.field_name, fltr.filter_type, fltr.value])
            if params.get('__search'):
                field_name, text = params['__search']
                filters.append([field_name, consts.FILTER_CONTAINS_ALL, text])
            params['__filters'] = filters
            if not order_by is None:
                params['__order'] = self.get_order_by_list(order_by)
            elif self._order_by_list:
                params['__order'] = list(self._order_by_list)
            if funcs:
                params['__funcs'] = funcs
            if group_by:
                params['__group_by'] = group_by
            self._order_by_list = []
            self._where_list = []
            self._open_params = params

    def open(self, expanded, fields, where, order_by, open_empty, params,
        offset, limit, funcs, group_by, connection):
        if not params:
            params = {}
        self._do_before_open(expanded, fields, where, order_by, open_empty,
            params, offset, limit, funcs, group_by)
        self._bind_fields(expanded)
        self._dataset = []
        if not open_empty:
            self.do_open(params, connection)
        else:
            self.change_log = ChangeLog(self)
        self._active = True
        self.item_state = consts.STATE_BROWSE
        self.first()

    def do_open(self, params, connection):
        if not params:
            params = self._open_params
        rows, error_mes = self.do_internal_open(params, connection)
        if error_mes:
            raise RuntimeError(error_mes)
        else:
            self._dataset = rows
            self.change_log = ChangeLog(self)

    def close(self):
        self._active = False
        self._dataset = []
        self.skip(0)
        self.close_details()

    def close_details(self):
        for detail in self.details:
            detail.close()

    def new_record(self):
        result = [None for field in self.fields if not field.master_field]
        if self.expanded:
            result += [None for field in self.fields if field.lookup_item]
        return result

    def __append(self, index=None):
        if self._is_delta:
            raise DatasetException('You can not add records to delta')
        if not self.active:
            raise DatasetException(consts.language('append_not_active') % self.item_name)
        if self.master_field and not self.owner._primary_key_field.value:
            raise DatasetException('Master primary key field value is not defined.')
        self._do_before_scroll()
        if self.item_state != consts.STATE_BROWSE:
            raise DatasetInvalidState(consts.language('append_not_browse') % self.item_name)
        self.item_state = consts.STATE_INSERT
        if index == 0:
            self._dataset.insert(0, self.new_record())
        else:
            self._dataset.append(self.new_record())
            index = len(self._dataset) - 1
        self.skip(index, False)
        if self.master_field:
            self._master_field_field.data = self.owner._primary_key_field.value;
        for field in self.fields:
            if not field.master_field:
                field.assign_default_value()
        self._modified = False
        self._do_after_scroll()

    def append(self):
        self._edit_masters()
        self._append()

    def _append(self):
        self.__append()

    def insert(self):
        self.__append(0)

    def _edit_masters(self):
        if self.master:
            self.master._edit_masters()
            if not self.master.is_changing():
                self.master._edit()

    def edit(self):
        self._edit_masters()
        self._edit()

    def _edit(self):
        if not self.active:
            raise DatasetException(consts.language('edit_not_active') % self.item_name)
        if self.item_state == consts.STATE_EDIT:
            return
        if self.item_state != consts.STATE_BROWSE:
            raise DatasetInvalidState(consts.language('edit_not_browse') % self.item_name)
        if self.record_count() == 0:
            raise DatasetEmpty(consts.language('edit_no_records') % self.item_name)
        self._buffer = self.change_log.store_record()
        self._modified_buffer = self._store_modified()
        self.item_state = consts.STATE_EDIT

    def delete(self):
        self._edit_masters()
        self._delete()

    def _delete(self):
        if self._is_delta:
            raise 'You can not add records to delta'
        if not self.active:
            raise DatasetException(consts.language('delete_not_active') % self.item_name)
        if self.record_count() == 0:
            raise DatasetEmpty(consts.language('delete_no_records') % self.item_name)
        self._do_before_scroll()
        self.item_state = consts.STATE_DELETE
        self.change_log.log_change()
        if self.master:
            self.master._set_modified(True)
        self._dataset.remove(self._dataset[self.rec_no])
        self.skip(self.rec_no, False)
        self._do_after_scroll()
        self.item_state = consts.STATE_BROWSE

    def cancel(self):
        if self.item_state == consts.STATE_EDIT:
            self.change_log.restore_record(self._buffer)
        elif self.item_state == consts.STATE_INSERT:
            self._do_before_scroll()
            self.change_log.record_status = consts.RECORD_UNCHANGED;
            del self._dataset[self.rec_no]
        else:
            raise Exception(consts.language('cancel_invalid_state') % self.item_name)
        prev_state = self.item_state
        self.skip(self.__old_row, False)
        self.item_state = consts.STATE_BROWSE
        if prev_state == consts.STATE_EDIT:
            self._restore_modified(self._modified_buffer);
        elif prev_state == consts.STATE_INSERT:
            self._modified = False
            self._do_after_scroll()

    def post(self):
        if not self.is_changing():
            raise DatasetInvalidState(consts.language('not_edit_insert_state') % self.item_name)
        self.check_record_valid()
        if self.master and self._master_id:
            self.field_by_name(self._master_id).value = self.master.ID
        for detail in self.details:
            if detail.is_changing():
                detail.post()
        if self.is_modified() or self.is_new():
            self.change_log.log_change()
        self._modified = False
        self.item_state = consts.STATE_BROWSE

    def rec_inserted(self):
        return self.change_log.record_status == consts.RECORD_INSERTED

    def rec_deleted(self):
        return self.change_log.record_status == consts.RECORD_DELETED

    def rec_modified(self):
        return self.change_log.record_status in (consts.RECORD_MODIFIED, consts.RECORD_DETAILS_MODIFIED)

    def is_browsing(self):
        return self.item_state == consts.STATE_BROWSE

    def is_changing(self):
        return (self.item_state == consts.STATE_INSERT) or (self.item_state == consts.STATE_EDIT)

    def is_new(self):
        return self.item_state == consts.STATE_INSERT

    def is_edited(self):
        return self.item_state == consts.STATE_EDIT

    def is_deleting(self):
        return self.item_state == consts.STATE_DELETE

    def check_record_valid(self):
        for field in self.fields:
            field.check_valid()
        return True

    def locate(self, fields, values):
        clone = self.clone()

        def record_found():
            if isinstance(fields, (list, tuple)):
                for i, field in enumerate(fields):
                    if clone.field_by_name(field).value != values[i]:
                        return False
                return True
            else:
                if clone.field_by_name(fields).value == values:
                    return True

        for c in clone:
            if record_found():
                self.rec_no = clone.rec_no
                return True

    def filter_index(self, filter_name):
        filter = self.filter_by_name(filter_name)
        if filter:
            return self.filters.index(filter)

    def get_field_values(self):
        result = []
        for field in self.fields:
            result.append(field.value)
        return result

    def set_field_values(self, values):
        for i, field in enumerate(self.fields):
            field.value = values[i]

    def compare_field_values(self, values):
        result = True
        for i, field in enumerate(self.fields):
            if self.get_field_values() != values:
                result = False
                break
        return result

    def clear_filters(self):
        for filter in self.filters:
            filter.value = None

    def get_filter_values(self):
        result = []
        for filter in self.filters:
            result.append(filter.value)
        return result

    def set_filter_values(self, values):
        for i, filter in enumerate(self.filters):
            filter.value = values[i]

    def search(self, field_name, text):
        searchText = text.strip()
        params = {};
        if len(searchText):
            params['__search'] = [field_name, searchText]
            self.open(params=params)
        else:
            self.open()

class MasterDataSet(AbstractDataSet):
    def __init__(self):
        AbstractDataSet.__init__(self)
        self.__details_active = False

    def _copy(self, filters=True, details=True, handlers=True):
        result = super(MasterDataSet, self)._copy(filters, details, handlers)
        if details:
            for detail in self.details:
                copy_table = detail._copy(filters, details, handlers)
                if detail.master:
                    copy_table.master = result
                result.details.append(copy_table)
                result.items.append(copy_table)
                if not hasattr(result, copy_table.item_name):
                    setattr(result, copy_table.item_name, copy_table)
                if not hasattr(result.details, copy_table.item_name):
                    setattr(result.details, copy_table.item_name, copy_table)
                copy_table.owner = result
                copy_table.prototype = detail.prototype

        return result

    def do_apply(self, params, safe, connection):
        pass

    def apply(self, connection=None, params=None, safe=False, caller=None):
        result = None
        if self.master:
            if self.master_applies or self.master:
                return
            item = self
            while item.master:
                if item.is_changing():
                    item.post()
                item = item.master
            master.apply(connection=None, params=None, safe=False, caller=self)
            return
        if not caller:
            caller = self
        if self.is_changing():
            self.post()
        id_str = str(caller.ID)
        self.do_apply({id_str: params}, safe, connection)

    def copy_record_fields(self, source, copy_system_fields=False):
        modified = False
        for f in source.fields:
            if not copy_system_fields and f.system_field():
                continue
            field = self.field_by_name(f.field_name)
            if field and field.data != f.data:
                modified = True
                field.data = f.data
                field.lookup_data = f.lookup_data
        if modified:
            self._modified = True

    def detail_by_ID(self, ID):
        ID = int(ID)
        for detail in self.details:
            if detail.ID == ID:
                return detail

    def detail_by_name(self, name):
        for detail in self.details:
            if detail.item_name == name:
                return detail

    def open_details(self):
        for detail in self.details:
            if not detail.disabled:
                detail.open()

    def init_history(self):
        if self._is_delta:
            cur_row = self.change_log.record_info.cur_record
            if not cur_row and not self.rec_inserted():
                if self.master:
                    copy = self.prototype.copy(handlers=False, details=False, filters=False)
                else:
                    copy = self.copy(handlers=False, details=False, filters=False)
                pk = copy._primary_key
                copy.set_where({pk: self._primary_key_field.value})
                field_names = [f.field_name for f in self.fields]
                copy.open(expanded=False, fields=field_names, connection=self._apply_connection)
                if copy.rec_count:
                    cur_row = []
                    for f in copy.fields:
                        if not f.master_field and not f.calculated:
                            cur_row.append(f.data)
                    self.change_log.record_info.cur_record = cur_row
    def init_delta_details(self, client_changes):
        for detail in self.details:
            detail._is_delta = True
            detail._tree_item = self._tree_item.detail_by_ID(detail.ID)
            detail.__details_active = True
            detail.client_changes = client_changes
            detail.init_delta_details(client_changes)

    def delta(self, changes=None, client_changes=False):
        if not changes:
            changes = {}
            self.change_log.get_changes(changes)
        result = self.copy(filters=False, details=True, handlers=False)
        result.change_log = ChangeLog(result)
        result._lookup_refs = self._lookup_refs
        result.log_changes = False
        result._is_delta = True
        result._tree_item = self
        result.client_changes = client_changes
        result.init_delta_details(client_changes)
        result.__details_active = True
        result.change_log.set_changes(changes)
        result.expanded = result.change_log.expanded
        result._dataset = result.change_log.dataset
        result._update_fields(result.change_log.fields)
        result._bind_fields(result.change_log.expanded)
        result.item_state = consts.STATE_BROWSE
        result._active = True
        result.first()
        return result

    def _do_after_scroll(self):
        if self.__details_active:
            self.open_details()
        else:
            self.close_details()
        super(MasterDataSet, self)._do_after_scroll()

    def _set_read_only(self, value):
        super(MasterDataSet, self)._set_read_only(value)
        for detail in self.details:
            detail._set_read_only(value)


class MasterDetailDataset(MasterDataSet):
    def __init__(self):
        MasterDataSet.__init__(self)
        self.disabled = False

    def open(self, options=None, expanded=None, fields=None, where=None, order_by=None,
        open_empty=False, params=None, offset=None, limit=None, funcs=None,
        group_by=None, safe=False, connection=None):
        if safe and not self.can_view():
            raise Exception(consts.language('cant_view') % self.item_caption)
        if options and type(options) == dict:
            expanded = options.get('expanded')
            fields = options.get('fields')
            where = options.get('where')
            order_by = options.get('order_by')
            open_empty = options.get('open_empty')
            params = options.get('params')
            offset = options.get('offset')
            limit = options.get('limit')
            funcs = options.get('funcs')
        if expanded is None:
            expanded = self.expanded
        else:
            self.expanded = expanded
        group_by
        if not params:
            params = {}
        if self.master:
            if not self.disabled and self.master.record_count() > 0:
                params['__master_id'] = None
                if self.master_field:
                    if self.owner.rec_count and not self.owner.is_new():
                        params['__master_field'] = self.owner.field_by_name(self.owner._primary_key).value
                    else:
                        open_empty = True
                elif self._master_id:
                    params['__master_id'] = self.master.ID
                    params['__master_rec_id'] = self.master.field_by_name(self.master._primary_key).value
                elif self._master_rec_id:
                    params['__master_rec_id'] = self.master.field_by_name(self.master._primary_key).value
                dataset = None
                if self.master.is_new():
                    self.change_log = ChangeLog(self)
                    dataset = []
                else:
                    change_log = self.master.change_log.detail_change_log(self)
                    if change_log and not change_log.empty:
                        self.change_log = change_log
                        dataset = self.change_log.dataset
                        fields = self.change_log.fields
                        expanded = self.change_log.expanded
                    elif self._is_delta:
                        self.change_log = None
                        dataset = []
                if not dataset is None:
                    self._do_before_open(expanded, fields, where, order_by,
                        open_empty, params, offset, limit, funcs, group_by)
                    self._bind_fields(expanded)
                    self._dataset = dataset
                    if self.change_log:
                        self.change_log.dataset = dataset;
                    self._active = True
                    self.item_state = consts.STATE_BROWSE
                    self.first()
                else:
                    return super(MasterDetailDataset, self).open(expanded,
                        fields, where, order_by, open_empty, params, offset,
                        limit, funcs, group_by, connection)
            else:
                return
        else:
            return super(MasterDetailDataset, self).open(expanded,
                fields, where, order_by, open_empty, params, offset, limit,
                funcs, group_by, connection)

    def open__in(self, ids, expanded=None, fields=None, where=None, order_by=None, open_empty=False, params=None, offset=None, limit=None): #depricated

        def slice_ids(ids):
            MAX_IN_LIST = 999
            result = []
            while True:
                result.append(ids[0:MAX_IN_LIST])
                ids = ids[MAX_IN_LIST:]
                if len(ids) == 0:
                    break;
            return result

        params = {}
        for args, value in locals().items():
            if not args in ['self', 'ids', 'params', 'slice_ids']:
                params[args] = value
        if type(ids) == dict:
            keys = list(ids.keys())
            id_field_name = keys[0]
            ids = ids[id_field_name]
        elif type(ids) == list:
            id_field_name = 'id'
        else:
            raise Exception('Item %s: invalid ids parameter in open__in method' % self.item_name)
        if params['where'] is None:
            params['where'] = {}
        records = []
        lst = slice_ids(ids)
        for l in lst:
            params['where'][id_field_name + '__in'] = l
            self.open(**params)
            records += self._dataset
        self._dataset = records
        self.first()

    def _store_modified(self, result=None):
        if result is None:
            result = {}
        result[self.ID] = self._modified
        if self.master:
            self.master._store_modified(result)
        return result

    def _restore_modified(self, value):
        self._modified = value[self.ID]
        if self.master:
            self.master._restore_modified(value);

    def _set_modified(self, value):
        self._modified = value
        if self.master and value:
            self.master._set_modified(value)

    def is_modified(self):
        return super(MasterDetailDataset, self).is_modified()

    def _get_read_only(self):
        if self.master:
            return self.master.read_only
        else:
            return super(MasterDetailDataset, self)._get_read_only()

    def _set_read_only(self, value):
        return super(MasterDetailDataset, self)._set_read_only(value)

    read_only = property (_get_read_only, _set_read_only)


class Dataset(MasterDetailDataset):
    pass

class Param(DBField):
    def __init__(self, owner, param_def):
        DBField.__init__(self, owner, param_def)
        self.field_kind = consts.PARAM_FIELD
        if self.data_type == consts.TEXT:
            self.field_size = 1000
        else:
            self.field_size = 0
        self.param_name = self.field_name
        self.param_caption = self.field_caption
        self._value = None
        self._lookup_value = None
        setattr(owner, self.param_name, self)

    def system_field(self):
        return False

    @property
    def data(self):
        return self._value

    @data.setter
    def data(self, value):
        self._value = value

    @property
    def lookup_data(self):
        return self._lookup_value

    @lookup_data.setter
    def lookup_data(self, value):
        self._lookup_value = value

    def _do_before_changed(self):
        pass

    def _change_lookup_field(self, lookup_value=None, slave_field_values=None):
        pass

    def _set_modified(self, value):
        pass

    def copy(self, owner):
        result = Param(owner, self.param_caption, self.field_name, self.data_type,
            self.lookup_item, self.lookup_field, self.required,
            self.edit_visible, self.alignment)
        return result

class ParamReport(object):
    def __init__(self):
        self.param_defs = []
        self.params = []

    def add_param(self, *args):
        param_def = self.add_param_def(*args)
        param = Param(self, param_def)
        self.params.append(param)

    def create_params(self, info):
        for param_def in info:
            self.add_param(*param_def)

    def add_param_def(self, param_caption, param_name, data_type,
            lookup_item, lookup_field, required, visible,
            alignment, multi_select, multi_select_all, enable_typeahead,
            lookup_values, param_help, param_placeholder):
        param_def = [None for i in range(len(FIELD_DEF))]
        param_def[FIELD_NAME] = param_name
        param_def[FIELD_CAPTION] = param_caption
        param_def[FIELD_DATA_TYPE] = data_type
        param_def[REQUIRED] = required
        param_def[LOOKUP_ITEM] = lookup_item
        param_def[LOOKUP_FIELD] = lookup_field
        param_def[FIELD_VISIBLE] = visible
        param_def[FIELD_ALIGNMENT] = alignment
        param_def[FIELD_MULTI_SELECT] = multi_select
        param_def[FIELD_MULTI_SELECT_ALL] = multi_select_all
        param_def[FIELD_ENABLE_TYPEAHEAD] = enable_typeahead
        param_def[FIELD_LOOKUP_VALUES] = lookup_values
        param_def[FIELD_HELP] = param_help
        param_def[FIELD_PLACEHOLDER] = param_placeholder
        self.param_defs.append(param_def)
        return param_def

    def prepare_params(self):
        for param in self.params:
            if param.lookup_item and type(param.lookup_item) == int:
                param.lookup_item = self.task.item_by_ID(param.lookup_item)
            if param.lookup_field and type(param.lookup_field) == int:
                param.lookup_field = param.lookup_item._field_by_ID(param.lookup_field).field_name
            if param.lookup_values and type(param.lookup_values) == int:
                try:
                    param.lookup_values = self.task.lookup_lists[param.lookup_values]
                except:
                    pass
