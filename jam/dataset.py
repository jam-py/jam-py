import datetime
import traceback

from werkzeug._compat import iteritems, iterkeys, text_type, string_types, to_unicode
from werkzeug.utils import cached_property

from .common import consts, error_message

FIELD_DEF = FIELD_ID, FIELD_NAME, FIELD_CAPTION, FIELD_DATA_TYPE, FIELD_SIZE, REQUIRED, LOOKUP_ITEM, \
    LOOKUP_FIELD, LOOKUP_FIELD1, LOOKUP_FIELD2, FIELD_VISIBLE, \
    FIELD_READ_ONLY, FIELD_DEFAULT, FIELD_DEFAULT_VALUE, MASTER_FIELD, FIELD_ALIGNMENT, \
    FIELD_LOOKUP_VALUES, FIELD_MULTI_SELECT, FIELD_MULTI_SELECT_ALL, \
    FIELD_ENABLE_TYPEAHEAD, FIELD_HELP, FIELD_PLACEHOLDER, FIELD_MASK, \
    FIELD_IMAGE, FIELD_FILE, DB_FIELD_NAME = range(26)

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
        self.field_mask = field_def[FIELD_MASK]
        self.field_image = field_def[FIELD_IMAGE]
        self.db_field_name = field_def[DB_FIELD_NAME]
        self.field_type = consts.FIELD_TYPE_NAMES[self.data_type]
        self.filter = None
        self.on_field_get_text_called = None

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
                if type(result) in string_types:
                    result = consts.convert_date(result)
            elif self.data_type == consts.DATETIME:
                if type(result) in string_types:
                    result = consts.convert_date_time(result)
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
                    if type(result) in string_types:
                        result = result.replace('T', ' ')
                return result

    @lookup_data.setter
    def lookup_data(self, value):
        if self.lookup_index:
            if self.row and (self.lookup_index >= 0):
                self.row[self.lookup_index] = value

    @property
    def text(self):
        result = self.value
        if not result is None:
            if self.data_type == consts.INTEGER:
                result = str(result)
            elif self.data_type == consts.FLOAT:
                result = self.float_to_str(result)
            elif self.data_type == consts.CURRENCY:
                result = self.float_to_str(result)
            elif self.data_type == consts.DATE:
                result = self.date_to_str(result)
            elif self.data_type == consts.DATETIME:
                result = self.datetime_to_str(result)
            elif self.data_type == consts.TEXT:
                result = text_type(result)
            elif self.data_type == consts.KEYS:
                if len(result):
                    result = consts.language('items_selected') % len(result)
            else:
                result = text_type(result)
        else:
            result = ''
        if self.data_type == consts.BOOLEAN:
            if self.value:
                result = consts.language('true')
            else:
                result = consts.language('false')
        return result

    @text.setter
    def text(self, value):
        if value != self.text:
            if self.data_type == consts.TEXT:
                self.value = text_type(value)
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
                if value.upper() == consts.language('yes').upper():
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
        result = self.data
        if result is None:
            if self.field_kind == consts.ITEM_FIELD:
                if self.data_type in (consts.FLOAT, consts.INTEGER, consts.CURRENCY):
                    result = 0
                elif self.data_type == consts.BOOLEAN:
                    result = False
                elif self.data_type in [consts.TEXT, consts.LONGTEXT]:
                    result = ''
                elif self.data_type == consts.KEYS:
                    result = [];
        else:
            if self.data_type == consts.TEXT:
                if not isinstance(result, text_type):
                    result = to_unicode(result, 'utf-8')
            elif self.data_type in (consts.FLOAT, consts.CURRENCY):
                result = float(result)
            elif self.data_type == consts.DATE:
                result = consts.convert_date(result)
            elif self.data_type == consts.DATETIME:
                result = consts.convert_date_time(result)
            elif self.data_type == consts.BOOLEAN:
                if result:
                    result = True
                else:
                    result = False
            elif self.data_type == consts.KEYS:
                if self.lookup_data:
                    result = self.lookup_data
                else:
                    if isinstance(result, text_type):
                        result = result.split(';')
                    else:
                        result = [int(val) for val in result.split(';')]
                    self.lookup_data = result
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

    def set_value(self, value, lookup_value=None):
        self._check_system_field_value(value)
        self.new_value = None
        if not value is None:
            self.new_value = value
            try:
                if self.data_type == consts.BOOLEAN:
                    if bool(value):
                        self.new_value = 1
                    else:
                        self.new_value = 0
                elif self.data_type == consts.FLOAT:
                    self.new_value = float(value)
                elif self.data_type == consts.CURRENCY:
                    self.new_value = consts.round(value, consts.FRAC_DIGITS)
                elif self.data_type == consts.INTEGER:
                    self.new_value = int(value)
                elif self.data_type == consts.KEYS:
                    self.new_value = ';'.join([str(v) for v in value])
                    lookup_value = value
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
            val = to_unicode(value)
            mess = mess % val
        except:
            mess = mess.replace('%s', '')
        return mess

    @property
    def old_value(self):
        if self.owner._is_delta:
            if self.row and self.bind_index >= 0:
                try:
                    rec_info = self.row[len(self.row) - 1]
                    old_row = rec_info[consts.REC_OLD_REC]
                    if old_row:
                        result = old_row[self.bind_index]
                    elif self.owner.rec_deleted():
                        result = self.value
                    return result
                except:
                    pass
        else:
            raise Exception('Only delta can have old value property.')

    def _set_modified(self, value):
        if self.owner:
            self.owner._set_modified(value)

    @property
    def lookup_data_type(self):
        if self.lookup_item:
            return self.lookup_item._field_by_name(self.lookup_field).data_type;

    def _get_value_in_list(self, value=None):
        result = '';
        if value is None:
            value = self.value
        for val, str_val in self.lookup_values:
            if val == value:
                result = str_val
        return result

    @property
    def lookup_value(self):
        value = None
        if self.lookup_values and self.value:
            try:
                value = self._get_value_in_list()
            except:
                pass
        elif self.lookup_item:
            if self.value:
                value = self.lookup_data
                data_type = self.lookup_data_type
                if data_type == consts.DATE:
                    if isinstance(value, text_type):
                        value = self.convert_date(value)
                elif data_type == consts.DATETIME:
                    if isinstance(value, text_type):
                        value = self.convert_date_time(value)
                elif self.data_type == consts.BOOLEAN:
                    value = bool(value)
        return value

    @lookup_value.setter
    def lookup_value(self, value):
        if self.lookup_item:
            self.lookup_data = value

    @property
    def lookup_text(self):
        result = ''
        try:
            if self.lookup_values and self.value:
                result = self.lookup_value
            elif self.lookup_item:
                if self.value:
                    result = self.lookup_value
                if result is None:
                    result = ''
                else:
                    data_type = self.lookup_data_type
                    if data_type:
                        if data_type == consts.DATE:
                            result = self.date_to_str(result)
                        elif data_type == consts.DATETIME:
                            result = self.datetime_to_str(result)
                        elif data_type == consts.FLOAT:
                            result = self.float_to_str(result)
                        elif data_type == consts.CURRENCY:
                            result = self.cur_to_str(result)
            result = text_type(result)
        except Exception as e:
            traceback.print_exc()
        return result

    @property
    def display_text(self):
        result = ''
        if self.filter and self.filter.filter_type == consts.FILTER_IN \
            and self.filter.field.lookup_item and self.filter.value:
            result = consts.language('items_selected') % len(self.filter.value)
        elif self.lookup_item:
            result = self.lookup_text
        elif self.lookup_values:
            result = self.lookup_text
        else:
            if self.data_type == consts.CURRENCY:
                if not self.data is None:
                    result = self.cur_to_str(self.value)
            else:
                result = self.text
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

    def assign_default_value(self):
        if self.default_value:
            try:
                if self.data_type == consts.INTEGER:
                    self.value = int(self.default_value)
                elif self.data_type in [consts.FLOAT, consts.CURRENCY]:
                    self.value = float(self.default_value)
                elif self.data_type == consts.DATE:
                    if self.default_value == 'current date':
                        self.value = datetime.date.today()
                elif self.data_type == consts.DATETIME:
                    if self.default_value == 'current datetime':
                        self.value = datetime.datetime.now()
                elif self.data_type == consts.BOOLEAN:
                    if self.default_value == 'true':
                        self.value = True
                    elif self.default_value == 'false':
                        self.value = False
                elif self.data_type in [consts.TEXT, consts.LONGTEXT]:
                    self.value = self.default_value
            except Exception as e:
                self.log.exception(error_message(e))

    def check_type(self):
        if (self.data_type == consts.TEXT) and (self.field_size != 0) and \
            (len(self.text) > self.field_size):
            raise FieldInvalidLength(consts.language('invalid_length') % self.field_size)
        return True

    def check_reqired(self):
        if self.required and self.data is None:
            raise FieldValueRequired('%s "%s" - %s' % (consts.language['field'], self.field_name, consts.language['value_required']))
        return True

    def check_valid(self):
        if self.check_reqired():
            self.check_type()
        return True

    def system_field(self):
        if self.field_name and self.field_name in (self.owner._primary_key,  \
            self.owner._deleted_flag, self.owner._master_id, self.owner._master_rec_id):
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

class ChangeLog(object):
    def __init__(self, item):
        self.item = item
        self._change_id = 0
        self.records = []
        self.logs = {}
        self.fields = []
        self.expanded = True

    def get_change_id(self):
        self._change_id += 1
        return str(self._change_id)

    def log_changes(self):
        if self.item.master:
            return self.item.master.change_log.log_changes()
        else:
            return self.item.log_changes;

    def find_record_log(self):
        result = None
        if self.item.master:
            record_log = self.item.master.change_log.find_record_log()
            if record_log:
                details = record_log['details']
                detail = details.get(str(self.item.ID))
                if not detail:
                    detail = {
                        'logs': {},
                        'records': self.item._dataset,
                        'fields': [field.field_name for field in self.item.fields],
                        'expanded': self.item.expanded
                    }
                    details[str(self.item.ID)] = detail
                self.logs = detail['logs']
                self.records = detail['records']
                self.fields = detail['fields']
                self.expanded = detail['expanded']
        if self.item.record_count():
            change_id = self.item.rec_change_id
            if not change_id:
                change_id = self.get_change_id()
                self.item.rec_change_id = change_id;
            result = self.logs.get(change_id)
            if not result:
                result = {
                    'old_record': None,
                    'record': self.cur_record(),
                    'details': {}
                }
                self.logs[change_id] = result
            return result

    def get_detail_log(self, detail_ID):
        result = None
        record_log = self.find_record_log()
        details = record_log['details']
        if details:
            result = details.get(detail_ID)
        if result is None and self.item._is_delta:
            result = {'records': [], 'fields': [], 'expanded': False, 'logs': {}}
        return result

    def remove_record_log(self):
        change_id = self.item.rec_change_id
        if change_id:
            self.find_record_log()
            del self.logs[self.item.rec_change_id]
            self.item.rec_change_id = None
            self.item.record_status = consts.RECORD_UNCHANGED

    def cur_record(self):
        return self.item._dataset[self.item.rec_no]

    def record_modified(self, record_log):
        modified = False
        old_rec = record_log['old_record']
        cur_rec = record_log['record']
        for i in range(self.item._record_lookup_index):
            if old_rec[i] != cur_rec[i]:
                modified = True
                break
        return modified

    def copy_record(self, record, expanded=True):
        result = None
        if record:
            if expanded:
                result = record[0:self.item._record_info_index]
            else:
                result = record[0:self.item._record_lookup_index]
            info = self.item.get_rec_info(record=record)
            result.append([info[0], {}, info[2]])
        return result

    def log_change(self):
        if self.log_changes():
            record_log = self.find_record_log()
            if self.item.item_state == consts.STATE_BROWSE:
                if (self.item.record_status == consts.RECORD_UNCHANGED) or \
                    (self.item.record_status == consts.RECORD_DETAILS_MODIFIED and record_log['old_record'] is None):
                    record_log['old_record'] = self.copy_record(self.cur_record(), False)
                    return
            elif self.item.item_state == consts.STATE_INSERT:
                self.item.record_status = consts.RECORD_INSERTED
            elif self.item.item_state == consts.STATE_EDIT:
                if self.item.record_status == consts.RECORD_UNCHANGED:
                    self.item.record_status = consts.RECORD_MODIFIED
                elif self.item.record_status == consts.RECORD_DETAILS_MODIFIED:
                    if self.record_modified(record_log):
                        self.item.record_status = consts.RECORD_MODIFIED
            elif self.item.item_state == consts.STATE_DELETE:
                if self.item.record_status == consts.RECORD_INSERTED:
                    self.remove_record_log()
                else:
                    self.item.record_status = consts.RECORD_DELETED
            else:
                raise Exception('Item %s: change log invalid records state' % self.item.item_name)
            if self.item.master:
                if self.item.master.record_status == consts.RECORD_UNCHANGED:
                    self.item.master.record_status = consts.RECORD_DETAILS_MODIFIED

    def get_changes(self, result):
        data = {}
        result['fields'] = self.fields
        result['expanded'] = False
        result['data'] = data
        for key, record_log in iteritems(self.logs):
            record = record_log['record']
            info = self.item.get_rec_info(record=record)
            if info[consts.REC_STATUS] != consts.RECORD_UNCHANGED:
                old_record = record_log['old_record']
                new_record = self.copy_record(record_log['record'], expanded=False)
                new_details = {}
                for detail_id, detail in iteritems(record_log['details']):
                    new_detail = {}
                    detail_item = self.item.item_by_ID(int(detail_id))
                    detail_item.change_log.logs = detail['logs']
                    detail_item.change_log.fields = detail['fields']
                    detail_item.change_log.expanded = detail['expanded']
                    detail_item.change_log.get_changes(new_detail)
                    new_details[detail_id] = new_detail
                data[key] = {
                        'old_record': old_record,
                        'record': new_record,
                        'details': new_details
                    }

    def set_changes(self, changes):
        new_records = []
        self.records = []
        self.logs = {}
        self.fields = changes['fields']
        self.expanded = changes['expanded']
        data = changes['data']
        self._change_id = 0
        for key, record_log in iteritems(data):
            if self._change_id < int(key):
                self._change_id = int(key)
            record = record_log['record']
            record[len(record) - 1].append(record_log['old_record'])
            new_records.append([int(key), record])
            details = {}
            self.logs[key] = {
                'old_record': None,
                'record': record,
                'details': details
            }
            for detail_id, detail in iteritems(record_log['details']):
                detail_item = self.item.item_by_ID(int(detail_id))
                detail_item.change_log.set_changes(detail)
                details[detail_id] = {
                    'logs': detail_item.change_log.logs,
                    'records': detail_item.change_log.records,
                    'fields': detail_item.change_log.fields,
                    'expanded': detail_item.change_log.expanded
                }
        new_records.sort(key=lambda x: x[0])
        self.records = [rec for key, rec in new_records]

    def copy_records(self, records):
        result = []
        for rec in records:
            result.append(list(rec))
        return result

    def store_details(self, source, dest):
        for detail_item in self.item.details:
            detail_id = str(detail_item.ID)
            detail = source.get(detail_id)
            logs = {}
            records = []
            fields = []
            expanded = True
            if detail:
                cur_logs = detail['logs']
                cur_records = detail['records']
                fields = detail['fields']
                expanded = detail['expanded']
                records = self.copy_records(cur_records)
                for key, record_log in iteritems(cur_logs):
                    cur_record = record_log['record']
                    record = detail_item.change_log.copy_record(cur_record)
                    index = None
                    try:
                        index = cur_records.index(cur_record)
                    except:
                        pass
                    if not index is None:
                        records[index] = record
                    details = {}
                    detail_item.change_log.store_details(record_log['details'], details)
                    logs[key] = {
                        'old_record': record_log['old_record'],
                        'record': record,
                        'details': details
                    }
            else:
                if detail_item._dataset:
                    records = self.copy_records(detail_item._dataset)
            if records or logs:
                dest[detail_id] = {'logs': logs, 'records': records, 'fields': fields, 'expanded': expanded}

    def store_record_log(self):
        if not self.log_changes():
            result = {}
            result['record'] = self.copy_record(self.cur_record())
            details = {}
            for detail in self.item.details:
                if not detail.disabled and detail._dataset:
                    details[str(detail.ID)] = list(detail._dataset)
            result['details'] = details
        else:
            record_log = self.find_record_log()
            details = {}
            self.store_details(record_log['details'], details)
            result = {}
            result['old_record'] = record_log['old_record']
            result['record'] = self.copy_record(record_log['record'])
            result['details'] = details
        return result

    def restore_record_log(self, log):

        def restore_record():
            record = log['record']
            cur_record = self.cur_record()
            info_index = self.item._record_info_index
            for i, it in enumerate(cur_record):
                if i < info_index:
                    cur_record[i] = record[i]

        if not self.log_changes():
            restore_record()
            for detail in self.item.details:
                detail._dataset = log['details'][str(detail.ID)]
        else:
            record_log = self.find_record_log()
            restore_record()
            record_log['old_record'] = log['old_record']
            record_log['record'] = self.cur_record()
            record_log['details'] = log['details']
            for detail in self.item.details:
                detail_log = log['details'].get(str(detail.ID))
                if detail_log:
                    detail._dataset = detail_log['records']
            if self.item.record_status == consts.RECORD_UNCHANGED:
                self.remove_record_log()

    def prepare(self):
        if self.item.master:
            log = self.item.master.change_log.get_detail_log(str(self.item.ID))
            if log:
                log['records'] = []
                log['logs'] = {}
                log['fields'] = []
                log['fields'] = [field.field_name for field in self.item.fields if not field.master_field]
                log['expanded'] = self.item.expanded
        else:
            self.records = []
            self.logs = {}
            self.fields = []
            self.fields = [field.field_name for field in self.item.fields if not field.master_field]
            self.expanded = self.item.expanded

    def update(self, updates, master_rec_id=None):
        if updates:
            changes = updates['changes']
            for change in changes:
                log_id = change['log_id']
                rec_id = change['rec_id']
                details = change['details']
                record_log = self.logs.get(log_id)
                if record_log:
                    record = record_log['record']
                    record_details = record_log['details']
                    for detail in details:
                        ID = detail['ID']
                        detail_item = self.item.detail_by_ID(int(ID))
                        item_detail = record_details.get(str(ID))
                        if item_detail:
                            detail_item.change_log.logs = item_detail['logs']
                            detail_item.change_log.update(detail, rec_id)
                    if rec_id and self.item._primary_key:
                        if not record[self.item._primary_key_field.bind_index]:
                            record[self.item._primary_key_field.bind_index] = rec_id
                    if master_rec_id:
                        if not record[self.item._master_rec_id_field.bind_index]:
                            record[self.item._master_rec_id_field.bind_index] = master_rec_id
                    info = self.item.get_rec_info(record=record)
                    info[consts.REC_STATUS] = consts.RECORD_UNCHANGED
                    info[consts.REC_CHANGE_ID] = consts.RECORD_UNCHANGED
                    del self.logs[log_id]


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
        self.change_log = ChangeLog(self)
        self._log_changes = True
        self._dataset = None
        self._primary_key = None
        self._deleted_flag = None
        self._master_id = None
        self._master_rec_id = None
        self._primary_key_db_field_name = None
        self._deleted_flag_db_field_name = None
        self._master_id_db_field_name = None
        self._master_rec_id_db_field_name = None
        self.__eof = False
        self.__bof = False
        self.__cur_row = None
        self.__old_row = 0
        self._old_status = None
        self._buffer = None
        self._modified = None
        self._state = consts.STATE_INACTIVE
        self._read_only = False
        self._active = False
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
        self._keep_history = False
        self.edit_lock = False
        self.select_all = False
        self.on_field_get_text = None

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
            image_placeholder=None, image_camera=None, file_download_btn=None, file_open_btn=None, file_accept=None):
        if not db_field_name:
            db_field_name = field_name.upper()
        field_def = [None for i in range(len(FIELD_DEF))]
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
        field_def[FIELD_MASK] = field_mask
        if data_type == consts.IMAGE:
            field_def[FIELD_IMAGE] = {'edit_width': image_edit_width, 'edit_height': image_edit_height,
                'view_width': image_view_width, 'view_height': image_view_height, 'placeholder': image_placeholder,
                'camera': image_camera}
        if data_type == consts.FILE:
            field_def[FIELD_FILE] = {'download_btn': file_download_btn, 'open_btn': file_open_btn, 'accept': file_accept}
        field_def[DB_FIELD_NAME] = db_field_name
        self.field_defs.append(field_def)
        return field_def

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
    def keep_history(self):
        if self.master:
            return self.prototype._keep_history
        else:
            return self._keep_history

    def _copy(self, filters=True, details=True, handlers=True):
        result = self.__class__(self.task, None, self.item_name, self.item_caption, self.visible)
        result.ID = self.ID
        result.item_name = self.item_name
        result.expanded = self.expanded
        result.field_defs = self.field_defs
        result.filter_defs = self.filter_defs
        result._virtual_table = self._virtual_table
        result._keep_history = self._keep_history
        result.select_all = self.select_all

        for field_def in result.field_defs:
            field = DBField(result, field_def)
            result._fields.append(field)
        result.prepare_fields()

        for filter_def in result.filter_defs:
            fltr = DBFilter(result, filter_def)
            result.filters.append(fltr)
        result.prepare_filters()

        result._events = self._events
        if handlers:
            for func_name, func in result._events:
                setattr(result, func_name, func)
        return result

    def clone(self):
        result = self.__class__(self.task, None, self.item_name, self.item_caption, self.visible)
        result.ID = self.ID
        result.item_name = self.item_name
        result.field_defs = self.field_defs
        result.filter_defs = self.filter_defs

        for field_def in result.field_defs:
            field = DBField(result, field_def)
            result._fields.append(field)
        result.prepare_fields()

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

    def prepare_fields(self):
        for field in self._fields:
            if field.lookup_item and type(field.lookup_item) == int:
                field.lookup_item = self.task.item_by_ID(field.lookup_item)
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
            if field.lookup_values and type(field.lookup_values) == int:
                try:
                    field.lookup_values = self.task.lookup_lists[field.lookup_values]
                except:
                    pass
        self.fields = list(self._fields)
        for field in self.fields:
            if not hasattr(self, field.field_name):
                setattr(self, field.field_name, field)
        for sys_field_name in ['_primary_key', '_deleted_flag', '_master_id', '_master_rec_id']:
            sys_field = getattr(self, sys_field_name)
            if sys_field and type(sys_field) == int:
                field = self.field_by_ID(sys_field)
                if field:
                    setattr(self, sys_field_name, field.field_name)
                    setattr(self, '%s_%s' % (sys_field_name, 'db_field_name'), field.db_field_name)

    def prepare_filters(self):
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
        pass

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

    def find_rec_info(self, rec_no=None, record=None):
        if record is None:
            if rec_no is None:
                rec_no = self.rec_no
            if self.record_count() > 0:
                record = self._dataset[rec_no];
        if record and self._record_info_index > 0:
            if len(record) < self._record_info_index + 1:
                record.append([None, {}, None])
            return record[self._record_info_index]

    def get_rec_info(self, rec_no=None, record=None):
        return self.find_rec_info(rec_no, record)

    def get_records_status(self):
        info = self.get_rec_info()
        if info:
            return info[consts.REC_STATUS]

    def _set_record_status(self, value):
        info = self.get_rec_info()
        if info and (self.log_changes or self._is_delta):
            info[consts.REC_STATUS] = value

    record_status = property (get_records_status, _set_record_status)

    def _get_rec_change_id(self):
        info = self.get_rec_info()
        if info:
            return info[consts.REC_CHANGE_ID]

    def _set_rec_change_id(self, value):
        info = self.get_rec_info()
        if info:
            info[consts.REC_CHANGE_ID] = value

    rec_change_id = property (_get_rec_change_id, _set_rec_change_id)

    def rec_controls_info(self):
        info = self.get_rec_info()
        if info:
            return info[consts.REC_CONTROLS_INFO]

    def _bind_fields(self, expanded=True):
        for field in self.fields:
            field.bind_index = None
            field.lookup_index = None
        j = 0
        for field in self.fields:
            if not field.master_field:
                field.bind_index = j
                j += 1
        for field in self.fields:
            if field.master_field:
                field.bind_index = field.master_field.bind_index
        self._record_lookup_index = j
        if expanded:
            for field in self.fields:
                if field.lookup_item:
                    field.lookup_index = j
                    j += 1
        self._record_info_index = j

    def get_where_list(self, field_dict):
        result = []
        for field_arg in iterkeys(field_dict):
            field_name = field_arg
            pos = field_name.find('__')
            if pos > -1:
                filter_str = field_name[pos+2:]
                field_name = field_name[:pos]
            else:
                filter_str = 'eq'
            filter_type = consts.FILTER_STR.index(filter_str)
            if filter_type != -1:
                filter_type += 1
            else:
                raise RuntimeError('%s: set_where method arument error %s' % (self.item_name, field_arg))
            field = self._field_by_name(field_name)
            if not field:
                raise RuntimeError('%s: set_where method arument error %s: ' % (self.item_name, field_arg))
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
            for key, value in iteritems(fields):
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
        for sys_field_name in ['_primary_key', '_deleted_flag', '_master_id', '_master_rec_id']:
            sys_field = getattr(self, sys_field_name)
            if sys_field:
                field = self.field_by_name(sys_field)
                if field:
                    setattr(self, sys_field_name + '_field', field)

    def _do_before_open(self, expanded, fields, where, order_by, open_empty,
        params, offset, limit, funcs, group_by):

        result = None
        params['__expanded'] = expanded
        params['__fields'] = []
        params['__filters'] = []
        filters = []

        if fields is None and self._select_field_list:
            fields = self._select_field_list
        self._update_fields(fields)
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
        offset, limit, funcs, group_by):
        if not params:
            params = {}
        self._do_before_open(expanded, fields, where, order_by, open_empty,
            params, offset, limit, funcs, group_by)
        self.change_log.prepare()
        self._bind_fields(expanded)
        self._dataset = []
        if not open_empty:
            self.do_open(params)
        self._active = True
        # ~ self.__cur_row = None
        self.item_state = consts.STATE_BROWSE
        self.first()

    def do_open(self, params=None):
        if not params:
            params = self._open_params
        rows, error_mes, info = self.do_internal_open(params)
        if error_mes:
            raise RuntimeError(error_mes)
        else:
            self._dataset = rows

    def close(self):
        self._active = False
        self._dataset = None
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

    def append(self, index=None):
        if not self.active:
            raise DatasetException(consts.language('append_not_active') % self.item_name)
        if self.item_state != consts.STATE_BROWSE:
            raise DatasetInvalidState(consts.language('append_not_browse') % self.item_name)
        self._do_before_scroll()
        self.item_state = consts.STATE_INSERT
        if index == 0:
            self._dataset.insert(0, self.new_record())
            self.skip(0, trigger_events=False)
        else:
            self._dataset.append(self.new_record())
            self.skip(len(self._dataset) - 1)
        self.record_status = consts.RECORD_INSERTED
        for field in self.fields:
            field.assign_default_value()
        self._modified = False
        self._do_after_scroll()

    def insert(self):
        self.append(0)

    def edit(self):
        if not self.active:
            raise DatasetException(consts.language('edit_not_active') % self.item_name)
        if self.item_state == consts.STATE_EDIT:
            return
        if self.item_state != consts.STATE_BROWSE:
            raise DatasetInvalidState(consts.language('edit_not_browse') % self.item_name)
        if self.record_count() == 0:
            raise DatasetEmpty(consts.language('edit_no_records') % self.item_name)
        self.change_log.log_change()
        self._buffer = self.change_log.store_record_log()
        self.item_state = consts.STATE_EDIT
        self._old_status = self.record_status
        self._modified = False

    def delete(self):
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
        self.skip(self.rec_no, trigger_events=False)
        self._do_after_scroll()
        self.item_state = consts.STATE_BROWSE

    def cancel(self):
        if self.item_state == consts.STATE_EDIT:
            self.change_log.restore_record_log(self._buffer)
        elif self.item_state == consts.STATE_INSERT:
            self._do_before_scroll()
            self.change_log.remove_record_log()
            del self._dataset[self.rec_no]
        else:
            raise Exception(consts.language('cancel_invalid_state') % self.item_name)
        prev_state = self.item_state
        self.skip(self.__old_row, trigger_events=False)
        self.item_state = consts.STATE_BROWSE
        self._set_modified(False)
        if prev_state == consts.STATE_EDIT:
            self.record_status = self._old_status
        elif prev_state == consts.STATE_INSERT:
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
        elif self.record_status == consts.RECORD_UNCHANGED:
            self.change_log.remove_record_log()
        self._modified = False
        self.item_state = consts.STATE_BROWSE

    def rec_inserted(self):
        return self.record_status == consts.RECORD_INSERTED

    def rec_deleted(self):
        return self.record_status == consts.RECORD_DELETED

    def rec_modified(self):
        return self.record_status in (consts.RECORD_MODIFIED, consts.RECORD_DETAILS_MODIFIED)

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

    def round(self, value, dec):
        return consts.round(value, dec)

class MasterDataSet(AbstractDataSet):
    def __init__(self):
        AbstractDataSet.__init__(self)
        self.details_active = False

    def _copy(self, filters=True, details=True, handlers=True):
        result = super(MasterDataSet, self)._copy(filters, details, handlers)
        if details:
            for detail in self.details:
                copy_table = detail._copy(filters, details, handlers)
                copy_table.master = result
                copy_table.expanded = detail.expanded
                result.details.append(copy_table)
                result.items.append(copy_table)
                if not hasattr(result, copy_table.item_name):
                    setattr(result, copy_table.item_name, copy_table)
                if not hasattr(result.details, copy_table.item_name):
                    setattr(result.details, copy_table.item_name, copy_table)
                copy_table.owner = result
                copy_table.prototype = detail.prototype

        return result

    def do_apply(self, params, safe):
        pass

    def apply(self, connection=None, params=None, safe=False):
        result = None
        if self.master or self.virtual_table:
            return
        if self.is_changing():
            self.post()
        self.do_apply(params, safe, connection)

    def detail_by_ID(self, ID):
        ID = int(ID)
        for detail in self.details:
            if detail.ID == ID:
                return detail

    def delta(self, changes=None):
        if not changes:
            changes = {}
            self.change_log.get_changes(changes)
        result = self.copy(filters=False, details=True, handlers=False)
        result.log_changes = False
        result.expanded = False
        result._is_delta = True
        for detail in result.details:
            detail.log_changes = False
            detail.expanded = False
            detail._is_delta = True
        result.details_active = True
        result.change_log.set_changes(changes)
        result._dataset = result.change_log.records
        result._update_fields(result.change_log.fields)
        result._bind_fields(result.change_log.expanded)
        result.item_state = consts.STATE_BROWSE
        result._active = True
        result.first()
        return result

    def detail_by_name(self, name):
        for detail in self.details:
            if detail.item_name == name:
                return detail

    def open_details(self):
        for detail in self.details:
            if not detail.disabled:
                detail.open()

    def _do_after_scroll(self):
        if self.details_active:
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

    def find_change_log(self):
        if self.master:
            if self.master.record_status != consts.RECORD_UNCHANGED:
                return self.master.change_log.get_detail_log(str(self.ID))

    def open(self, options=None, expanded=None, fields=None, where=None, order_by=None,
        open_empty=False, params=None, offset=None, limit=None, funcs=None,
        group_by=None, safe=False):
        if safe and not self.can_view():
            raise Exception(consts.language('cant_view') % self.item_caption)
        if options and type(options) == dict:
            if options.get('expanded'):
                expanded = options['expanded']
            if options.get('fields'):
                fields = options['fields']
            if options.get('where'):
                where = options['where']
            if options.get('order_by'):
                order_by = options['order_by']
            if options.get('open_empty'):
                open_empty = False
            if options.get('params'):
                params = options['params']
            if options.get('offset'):
                offset = options['offset']
            if options.get('limit'):
                limit = options['limit']
            if options.get('funcs'):
                funcs = options['funcs']
        if expanded is None:
            expanded = self.expanded
        else:
            self.expanded = expanded
        if self.virtual_table:
            open_empty = True
        group_by
        if not params:
            params = {}
        if self.master:
            if not self.disabled and self.master.record_count() > 0:
                records = None
                if self.master.is_new():
                    records = []
                else:
                    log = self.find_change_log()
                    if log:
                        records = log['records']
                        fields = log['fields']
                        expanded = log['expanded']
                if not records is None:
                    self._do_before_open(expanded, fields, where, order_by,
                        open_empty, params, offset, limit, funcs, group_by)
                    self._bind_fields(expanded)
                    if self.master.is_new():
                        self.change_log.prepare()
                    self._dataset = records
                    self._active = True
                    self.item_state = consts.STATE_BROWSE
                    self.first()
                else:
                    params['__master_id'] = self.master.ID
                    params['__master_rec_id'] = self.master.field_by_name(self.master._primary_key).value
                    return super(MasterDetailDataset, self).open(expanded,
                        fields, where, order_by, open_empty, params, offset,
                        limit, funcs, group_by)
            else:
                return
        else:
            return super(MasterDetailDataset, self).open(expanded,
                fields, where, order_by, open_empty, params, offset, limit,
                funcs, group_by)

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
        for args, value in iteritems(locals()):
            if not args in ['self', 'ids', 'params', 'slice_ids']:
                params[args] = value
        if type(ids) == dict:
            keys = list(iterkeys(ids))
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

    def insert(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(consts.language('insert_master_not_changing') % self.item_name)
        super(MasterDetailDataset, self).insert()

    def append(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(consts.language('append_master_not_changing') % self.item_name)
        super(MasterDetailDataset, self).append()

    def edit(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(consts.language('edit_master_not_changing') % self.item_name)
        super(MasterDetailDataset, self).edit()

    def delete(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(consts.language('delete_master_not_changing') % self.item_name)
        super(MasterDetailDataset, self).delete()

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
