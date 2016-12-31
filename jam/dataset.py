import datetime
import traceback

import jam.common as common

FIELD_DEF = FIELD_ID, FIELD_NAME, NAME, FIELD_DATA_TYPE, REQUIRED, LOOKUP_ITEM, MASTER_FIELD, LOOKUP_FIELD, LOOKUP_FIELD1, \
    LOOKUP_FIELD2, FIELD_VISIBLE, FIELD_VIEW_INDEX, FIELD_EDIT_VISIBLE, FIELD_EDIT_INDEX, FIELD_READ_ONLY, FIELD_EXPAND, \
    FIELD_WORD_WRAP, FIELD_SIZE, FIELD_DEFAULT_VALUE, FIELD_DEFAULT, FIELD_CALCULATED, FIELD_EDITABLE, FIELD_ALIGNMENT, \
    FIELD_LOOKUP_VALUES, FIELD_MULTI_SELECT, FIELD_MULTI_SELECT_ALL, FIELD_ENABLE_TYPEAHEAD, FIELD_HELP, FIELD_PLACEHOLDER = range(29)

FILTER_DEF = FILTER_OBJ_NAME, FILTER_NAME, FILTER_FIELD_NAME, FILTER_TYPE, FILTER_MULTI_SELECT, FILTER_DATA_TYPE, \
    FILTER_VISIBLE, FILTER_HELP, FILTER_PLACEHOLDER = range(9)

class DatasetException(Exception):
    pass

class DBField(object):
    def __init__(self, owner, field_def):
        self.owner = owner
        self.field_def = field_def
        self.field_kind = common.ITEM_FIELD
        self.ID = field_def[FIELD_ID]
        self.field_name = field_def[FIELD_NAME]
        self.field_caption = field_def[NAME]
        self.data_type = field_def[FIELD_DATA_TYPE]
        self.required = field_def[REQUIRED]
        self.lookup_item = field_def[LOOKUP_ITEM]
        self.master_field = field_def[MASTER_FIELD]
        self.lookup_field = field_def[LOOKUP_FIELD]
        self.lookup_item1 = None
        self.lookup_field1 = field_def[LOOKUP_FIELD1]
        self.lookup_item2 = None
        self.lookup_field2 = field_def[LOOKUP_FIELD2]
        self.read_only = field_def[FIELD_READ_ONLY]
        self.view_visible = field_def[FIELD_VISIBLE]
        self.view_index = field_def[FIELD_VIEW_INDEX]
        self.edit_visible = field_def[FIELD_EDIT_VISIBLE]
        self.edit_index = field_def[FIELD_EDIT_INDEX]
        self.expand = field_def[FIELD_EXPAND]
        self.word_wrap = field_def[FIELD_WORD_WRAP]
        self.field_size = field_def[FIELD_SIZE]
        self.default_value = field_def[FIELD_DEFAULT_VALUE]
        self.is_default = field_def[FIELD_DEFAULT]
        self.calculated = field_def[FIELD_CALCULATED]
        self.editable = field_def[FIELD_EDITABLE]
        self.alignment = field_def[FIELD_ALIGNMENT]
        self.lookup_values = field_def[FIELD_LOOKUP_VALUES]
        self.multi_select = field_def[FIELD_MULTI_SELECT]
        self.multi_select_all = field_def[FIELD_MULTI_SELECT_ALL]
        self.enable_typeahead = field_def[FIELD_ENABLE_TYPEAHEAD]
        self.field_help = field_def[FIELD_HELP]
        self.field_placeholder = field_def[FIELD_PLACEHOLDER]

        self.field_type = common.FIELD_TYPE_NAMES[self.data_type]
        self.filter = None
        self.on_field_get_text_called = None

    def get_row(self):
        if self.owner._dataset:
            return self.owner._dataset[self.owner.rec_no]
        else:
            traceback.print_exc()
            raise Exception(self.owner.task.lang['value_in_empty_dataset'] % self.owner.item_name)

    def get_data(self):
        row = self.get_row()
        if row and self.bind_index >= 0:
            return row[self.bind_index]

    def set_data(self, value):
        row = self.get_row()
        if row and (self.bind_index >= 0):
            row[self.bind_index] = value

    def get_lookup_data(self):
        if self.lookup_index:
            row = self.get_row()
            if row and (self.lookup_index >= 0):
                return row[self.lookup_index]

    def set_lookup_data(self, value):
        if self.lookup_index:
            row = self.get_row()
            if row and (self.lookup_index >= 0):
                row[self.lookup_index] = value

    def update_controls(self):
        pass

    def get_text(self):
        result = ''
        try:
            result = self.get_value()
            if not result is None:
                if self.data_type == common.INTEGER:
                    result = str(result)
                elif self.data_type == common.FLOAT:
                    result = self.float_to_str(result)
                elif self.data_type == common.CURRENCY:
                    result = self.cur_to_str(result)
                elif self.data_type == common.DATE:
                    result = self.date_to_str(result)
                elif self.data_type == common.DATETIME:
                    result = self.datetime_to_str(result)
                elif self.data_type == common.TEXT:
                    result = unicode(result)
                elif self.data_type == common.BOOLEAN:
                    if self.value:
                        if self.owner:
                            result = self.owner.task.lang['yes']
                        else:
                            result = 'True'
                    else:
                        if self.owner:
                            result = self.owner.task.lang['no']
                        else:
                            result = 'False'
                else:
                    result = str(result)
            else:
                result = ''
        except Exception as e:
            traceback.print_exc()
            self.do_on_error(self.type_error() % (''), e)
        return result

    def set_text(self, value):
        if value != self.text:
            try:
                if self.data_type == common.TEXT:
                    self.set_value(unicode(value))
                elif self.data_type == common.INTEGER:
                    self.set_value(int(value))
                if self.data_type == common.FLOAT:
                    self.set_value(common.str_to_float(value))
                elif self.data_type == common.CURRENCY:
                    self.set_value(common.str_to_float(value))
                elif self.data_type == common.DATE:
                    self.set_value(common.str_to_date(value))
                elif self.data_type == common.DATETIME:
                    self.set_value(common.str_to_datetime(value))
                elif self.data_type == common.BOOLEAN:
                    if self.owner:
                        if len(value) and value.upper().split() == self.owner.task.lang['yes'].upper().split():
                            self.set_value(True)
                        else:
                            self.set_value(False)
                    else:
                        if len(value) and value[0] in ['T', 't']:
                            self.set_value(True)
                        else:
                            self.set_value(False)
                else:
                    self.set_value(value)
            except Exception as e:
                traceback.print_exc()
                self.do_on_error(self.type_error() % (value), e)

    text = property (get_text, set_text)

    def convert_date_time(self, value):
        if value.find('.'):
            value = value.split('.')[0]
        if value.find('T'):
            value = value.replace('T', ' ')
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

    def convert_date(self, value):
        try:
            if value.find(' '):
                value = value.split(' ')[0]
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except:
            return self.convert_date_time(value).date()


    def get_raw_value(self):
        try:
            value = self.get_data()
            if self.data_type == common.DATE:
                if type(value) in [str, unicode]:
                    value = self.convert_date(value)
            elif self.data_type == common.DATETIME:
                if type(value) in [str, unicode]:
                    value = self.convert_date_time(value)
            return value
        except Exception as e:
            traceback.print_exc()
            self.do_on_error(self.type_error() % (''), e)

    raw_value = property (get_raw_value)

    def get_value(self):
        value = self.get_raw_value()
        try:
            if value == None:
                if self.field_kind == common.ITEM_FIELD:
                    if self.data_type in (common.FLOAT, common.INTEGER, common.CURRENCY):
                        value = 0
                    elif self.data_type == common.BOOLEAN:
                        value = False
                    elif self.data_type == common.TEXT:
                        value = ''
            else:
                if self.data_type in (common.TEXT, ):
                    if not isinstance(value, unicode):
                        value = value.decode('utf-8')
                elif self.data_type == common.BOOLEAN:
                    if value:
                        value = True
                    else:
                        value = False
            return value
        except Exception as e:
            traceback.print_exc()
            self.do_on_error(self.type_error() % (''), e)

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
        if self.owner:
            if not self.owner.item_state in (common.STATE_INSERT, common.STATE_EDIT):
                raise DatasetException(self.owner.task.lang['not_edit_insert_state'] % self.owner.item_name)
            if self.owner.on_before_field_changed:
                self.owner.on_before_field_changed(self)

    def _check_system_field_value(self, value):
        if self.field_kind == common.ITEM_FIELD:
            if self.field_name == self.owner._primary_key and self.value and self.value != value:
                raise DatasetException(self.owner.task.lang['no_primary_field_changing'] % self.owner.item_name)
            if self.field_name == self.owner._deleted_flag and self.value != value:
                raise DatasetException(self.owner.task.lang['no_deleted_field_changing'] % self.owner.item_name)

    def set_value(self, value, lookup_value=None, lookup_item=None):
        self._check_system_field_value(value)
        self.new_value = None
        if not value is None:
            self.new_value = value
            if not self.multi_select:
                if self.data_type == common.BOOLEAN:
                    if bool(value):
                        self.new_value = 1
                    else:
                        self.new_value = 0
                elif self.data_type in (common.FLOAT, common.CURRENCY):
                    self.new_value = float(value)
                elif self.data_type == common.INTEGER:
                    self.new_value = int(value)
        if self.raw_value != self.new_value:
            self._do_before_changed()
            try:
                self.set_data(self.new_value)
            except Exception as e:
                traceback.print_exc()
                self.do_on_error(self.type_error() % (value), e)
            finally:
                self.new_value = None
            self._change_lookup_field(lookup_value)
            self._set_modified(True)
            self._do_after_changed(lookup_item)

    value = property (get_value, set_value)

    def _set_modified(self, value):
        if not self.calculated:
            if self.owner:
                self.owner._set_modified(value)

    def get_lookup_data_type(self):
        if self.lookup_item:
            return self.lookup_item._field_by_name(self.lookup_field).data_type;

    def get_lookup_value(self):
        value = None
        if self.lookup_item:
            if self.value:
                value = self.get_lookup_data()
                data_type = self.get_lookup_data_type()
                if data_type == common.DATE:
                    if isinstance(value, unicode):
                        value = self.convert_date(value)
                elif data_type == common.DATETIME:
                    if isinstance(value, unicode):
                        value = self.convert_date_time(value)
                elif self.data_type == common.BOOLEAN:
                    value = bool(value)
        return value

    def set_lookup_value(self, value):
        if self.lookup_item:
            self.set_lookup_data(value)

    lookup_value = property (get_lookup_value, set_lookup_value)

    def get_lookup_text(self):
        result = ''
        try:
            if self.lookup_item:
                if self.value:
                    result = self.get_lookup_value()
                if result is None:
                    result = ''
                else:
                    data_type = self.get_lookup_data_type()
                    if data_type:
                        if data_type == common.DATE:
                            result = self.date_to_str(result)
                        elif data_type == common.DATETIME:
                            result = self.datetime_to_str(result)
                        elif data_type == common.FLOAT:
                            result = self.float_to_str(result)
                        elif data_type == common.CURRENCY:
                            result = self.cur_to_str(result)
            result = unicode(result)
        except Exception as e:
            traceback.print_exc()
        return result

    lookup_text = property (get_lookup_text)

    def get_display_text(self):

        def get_value_in_list():
            result = '';
            for val, str_val in self.lookup_values:
                if val == self.value:
                    result = str_val
            return result

        result = ''
        if self.filter and self.filter.filter_type == common.FILTER_IN and self.filter.field.lookup_item and self.filter.value:
            result = self.filter.owner.task.lang['items_selected'] % len(self.filter.value)
        elif self.lookup_item:
            result = self.lookup_text
        elif self.lookup_values and self.value:
            try:
                result = get_value_in_list()
            except:
                pass
        else:
            if self.data_type == common.CURRENCY:
                if not self.raw_value is None:
                    result = common.currency_to_str(self.value)
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

    display_text = property(get_display_text)

    def _set_read_only(self, value):
        self._read_only = value
        self.update_controls()

    def _get_read_only(self):
        result = self._read_only
        if self.owner and self.owner.parent_read_only and self.owner.read_only:
            result = self.owner.read_only
        return result

    read_only = property (_get_read_only, _set_read_only)

    def set_visible(self, value):
        self._visible = value
        self.update_controls()

    def get_visible(self):
        return self._visible
    view_visible = property (get_visible, set_visible)

    def set_alignment(self, value):
        self._alignment = value
        self.update_controls()

    def get_alignment(self):
        return self._alignment
    alignment = property (get_alignment, set_alignment)

    def xalign(self):
        return (self.alignment - 1) * 0.5

    def set_expand(self, value):
        self._expand = value
        self.update_controls()

    def get_expand(self):
        return self._expand
    expand = property (get_expand, set_expand)

    def set_word_wrap(self, value):
        self._word_wrap = value
        self.update_controls()

    def get_word_wrap(self):
        return self._word_wrap
    word_wrap = property (get_word_wrap, set_word_wrap)

    def check_type(self):
        self.get_value()
        if (self.data_type == common.TEXT) and (self.field_size != 0) and \
            (len(self.text) > self.field_size):
            print(self.text, len(self.text), type(self.text))
            self.do_on_error(self.owner.task.lang['invalid_length'] % self.field_size)
        return True

    def check_reqired(self):
        if not self.required:
            return True
        elif self.get_raw_value() != None:
            return True
        else:
            self.do_on_error(self.owner.task.lang['value_required'])

    def check_valid(self):
        if self.check_reqired():
            if self.check_type():
                if self.owner:
                    if self.owner.on_field_validate:
                        e = self.owner.on_field_validate(self)
                        if e:
                            self.do_on_error(e)
                return True

    def _do_after_changed(self, lookup_item):
        if self.owner:
            if self.owner.on_field_changed:
                self.owner.on_field_changed(self, lookup_item)
        self.update_controls()

    def do_on_error(self, err_mess, err=None):
        mess = None
        if err_mess and not err:
            mess = err_mess
        elif isinstance(err, ValueError) and err_mess:
            mess = err_mess
        elif err:
            mess = str(err)
        if mess:
            if self.owner:
                print('%s %s - %s: %s' % (self.owner.item_name,
                    self.owner.task.lang['error'].lower(), self.field_name, mess))
        raise TypeError(mess)

    def type_error(self):
        if self.data_type == common.INTEGER:
            return self.owner.task.lang['invalid_int']
        elif self.data_type == common.FLOAT:
            return self.owner.task.lang['invalid_float']
        elif self.data_type == common.CURRENCY:
            return self.owner.task.lang['invalid_cur']
        elif (self.data_type == common.DATE) or (self.data_type == common.DATE):
            return self.owner.task.lang['invalid_date']
        elif self.data_type == common.BOOLEAN:
            return self.owner.task.lang['invalid_bool']
        else:
            return self.owner.task.lang['invalid_value']

    def system_field(self):
        if self.field_name and self.field_name in (self.owner._primary_key,  \
            self.owner._deleted_flag, self.owner._master_id, self.owner._master_rec_id):
            return True

    def float_to_str(self, value):
        return common.float_to_str(value)

    def cur_to_str(self, value):
        return common.cur_to_str(value)

    def date_to_str(self, value):
        return common.date_to_str(value)

    def datetime_to_str(self, value):
        return common.datetime_to_str(value)

    def str_to_date(self, value):
        return common.str_to_date(value)

    def str_to_datetime(self, value):
        return common.str_to_datetime(value)

    def str_to_float(self, value):
        return common.str_to_float(value)

    def str_to_cur(self, value):
        return common.str_to_currency(value)

class FilterField(DBField):
    def __init__(self, fltr, field, owner):
        DBField.__init__(self, owner, field.field_def)
        self.field_kind = common.FILTER_FIELD
        self.filter = fltr
        self.lookup_item = None
        self._value = None
        self._lookup_value = None


    def _do_before_changed(self):
        pass

    def get_data(self):
        return self._value

    def set_data(self, value):
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
            if self.filter_type in (common.FILTER_IN, common.FILTER_NOT_IN):
                self.field.multi_select = True;
            if self.filter_type == common.FILTER_RANGE:
                self.field1 = FilterField(self, field, self.owner)

    def set_value(self, value):
        if self.filter_type == common.FILTER_RANGE:
            if value is None:
                self.field.value = None;
                self.field1.value = None;
            else:
                self.field.value = value[0];
                self.field1.value = value[1];
        else:
            self.field.value = value

    def get_value(self):
        return self.field.raw_value

    value = property (get_value, set_value)

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
            self.item.record_status = common.RECORD_UNCHANGED

    def cur_record(self):
        return self.item._dataset[self.item.rec_no]

    def record_modified(self, record_log):
        modified = False
        old_rec = record_log['old_record']
        cur_rec = record_log['record']
        for i in xrange(self.item._record_lookup_index):
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
            if self.item.item_state == common.STATE_BROWSE:
                if (self.item.record_status == common.RECORD_UNCHANGED) or \
                    (self.item.record_status == common.RECORD_DETAILS_MODIFIED and record_log['old_record'] is None):
                    record_log['old_record'] = self.copy_record(self.cur_record(), False)
                    return
            elif self.item.item_state == common.STATE_INSERT:
                self.item.record_status = common.RECORD_INSERTED
            elif self.item.item_state == common.STATE_EDIT:
                if self.item.record_status == common.RECORD_UNCHANGED:
                    self.item.record_status = common.RECORD_MODIFIED
                elif self.item.record_status == common.RECORD_DETAILS_MODIFIED:
                    if self.record_modified(record_log):
                        self.item.record_status = common.RECORD_MODIFIED
            elif self.item.item_state == common.STATE_DELETE:
                if self.item.record_status == common.RECORD_INSERTED:
                    self.remove_record_log()
                else:
                    self.item.record_status = common.RECORD_DELETED
            else:
                raise Exception('Item %s: change log invalid records state' % self.item.item_name)
            if self.item.master:
                if self.item.master.record_status == common.RECORD_UNCHANGED:
                    self.item.master.record_status = common.RECORD_DETAILS_MODIFIED

    def get_changes(self, result):
        data = {}
        result['fields'] = self.fields
        result['expanded'] = False
        result['data'] = data
        for key, record_log in self.logs.iteritems():
            record = record_log['record']
            info = self.item.get_rec_info(record=record)
            if info[common.REC_STATUS] != common.RECORD_UNCHANGED:
                old_record = record_log['old_record']
                new_record = self.copy_record(record_log['record'], expanded=False)
                new_details = {}
                for detail_id, detail in record_log['details'].iteritems():
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
        for key, record_log in data.iteritems():
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
            for detail_id, detail in record_log['details'].iteritems():
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
                for key, record_log in cur_logs.iteritems():
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
            if self.item.record_status == common.RECORD_UNCHANGED:
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
                    if rec_id:
                        if not record[self.item._primary_key_field.bind_index]:
                            record[self.item._primary_key_field.bind_index] = rec_id
                    if master_rec_id:
                        if not record[self.item._master_rec_id_field.bind_index]:
                            record[self.item._master_rec_id_field.bind_index] = master_rec_id
                    info = self.item.get_rec_info(record=record)
                    info[common.REC_STATUS] = common.RECORD_UNCHANGED
                    info[common.REC_CHANGE_ID] = common.RECORD_UNCHANGED
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
        self.controls = []
        self.change_log = ChangeLog(self)
        self._log_changes = True
        self._dataset = None
        self._primary_key = None
        self._deleted_flag = None
        self._master_id = None
        self._master_rec_id = None
        self._eof = False
        self._bof = False
        self._cur_row = None
        self._old_row = 0
        self._old_status = None
        self._buffer = None
        self._modified = None
        self._state = common.STATE_INACTIVE
        self._read_only = False
        self._active = False
        self._where_list = []
        self._order_by_list = []
        self._select_field_list = []
        self.on_state_changed = None
        self.on_filter_changed = None
        self._record_lookup_index = -1
        self._record_info_index = -1
        self._filtered = False
        self.expanded = True
        self._open_params = {}
        self._disabled_count = 0
        self._is_delta = False
        self.keep_history = False
        self.parent_read_only = True
        self.on_before_append = None
        self.on_after_append = None
        self.on_before_edit = None
        self.on_after_edit = None
        self.on_before_open = None
        self.on_after_open = None
        self.on_before_post = None
        self.on_after_post = None
        self.on_before_delete = None
        self.on_after_delete = None
        self.on_before_cancel = None
        self.on_after_cancel = None
        self.on_before_apply = None
        self.on_after_apply = None
        self.on_before_scroll = None
        self.on_after_scroll = None
        self.on_filter_record = None
        self.on_field_changed = None
        self.on_filters_applied = None
        self.on_before_field_changed = None
        self.on_filter_value_changed = None
        self.on_field_validate = None
        self.on_field_get_text = None

    def __getitem__(self, key):
        if key == 0:
            self.first()
        else:
            self.next()
        if self.eof():
            raise IndexError
        return self

    def add_field_def(self, field_ID, field_name, field_caption, data_type, required, lookup_item, lookup_field,
            lookup_field1, lookup_field2, view_visible, view_index, edit_visible, edit_index, read_only, expand,
            word_wrap, field_size, default_value, is_default, calculated, editable, master_field, alignment,
            lookup_values, enable_typeahead, field_help, field_placeholder):
        field_def = [None for i in range(len(FIELD_DEF))]
        field_def[FIELD_ID] = field_ID
        field_def[FIELD_NAME] = field_name
        field_def[NAME] = field_caption
        field_def[FIELD_DATA_TYPE] = data_type
        field_def[REQUIRED] = required
        field_def[LOOKUP_ITEM] = lookup_item
        field_def[MASTER_FIELD] = master_field
        field_def[LOOKUP_FIELD] = lookup_field
        field_def[LOOKUP_FIELD1] = lookup_field1
        field_def[LOOKUP_FIELD2] = lookup_field2
        field_def[FIELD_READ_ONLY] = read_only
        field_def[FIELD_VISIBLE] = view_visible
        field_def[FIELD_VIEW_INDEX] = view_index
        field_def[FIELD_EDIT_VISIBLE] = edit_visible
        field_def[FIELD_EDIT_INDEX] = edit_index
        field_def[FIELD_EXPAND] = expand
        field_def[FIELD_WORD_WRAP] = word_wrap
        field_def[FIELD_SIZE] = field_size
        field_def[FIELD_DEFAULT_VALUE] = default_value
        field_def[FIELD_DEFAULT] = is_default
        field_def[FIELD_CALCULATED] = calculated
        field_def[FIELD_EDITABLE] = editable
        field_def[FIELD_ALIGNMENT] = alignment
        field_def[FIELD_LOOKUP_VALUES] = lookup_values
        field_def[FIELD_ENABLE_TYPEAHEAD] = enable_typeahead
        field_def[FIELD_HELP] = field_help
        field_def[FIELD_PLACEHOLDER] = field_placeholder
        self.field_defs.append(field_def)
        return field_def

    def add_filter_def(self, filter_name, filter_caption, field_name, filter_type,
            multi_select_all, data_type, visible, filter_help, filter_placeholder):
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
        self.filter_defs.append(filter_def)
        return filter_def

    def get_dataset(self):
        result = []
        if self.active:
            for r in self._dataset:
                result.append(r[0:self._record_info_index])
        return result

    def set_dataset(self, value):
        self._dataset = value

    dataset = property (get_dataset, set_dataset)

    def _copy(self, filters=True, details=True, handlers=True):
        result = self.__class__(self.owner, self.item_name, self.item_caption, self.visible)
        result.ID = self.ID
        result.item_name = self.item_name
        result.expanded = self.expanded
        result.field_defs = self.field_defs
        result.filter_defs = self.filter_defs
        result.keep_history = self.keep_history

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

    def clone(self, keep_filtered=True):
        result = self.__class__(self.owner, self.item_name, self.item_caption, self.visible)
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
        if keep_filtered:
            result.on_filter_record = self.on_filter_record
            result.filtered = self.filtered
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
                if lookup_field.lookup_item and field.lookup_field1:
                    field.lookup_item1 = lookup_field.lookup_item
                    if type(field.lookup_item1) == int:
                        field.lookup_item1 = self.task.item_by_ID(field.lookup_item1)
                    if type(field.lookup_field1) == int:
                        lookup_field1 = field.lookup_item1._field_by_ID(field.lookup_field1)
                        field.lookup_field1 = lookup_field1.field_name
                    if lookup_field1.lookup_item and field.lookup_field2:
                        field.lookup_item2 = lookup_field1.lookup_item
                        if type(field.lookup_item2) == int:
                            field.lookup_item2 = self.task.item_by_ID(field.lookup_item2)
                        if type(field.lookup_field2) == int:
                            field.lookup_field2 = field.lookup_item2._field_by_ID(field.lookup_field2).field_name
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

    def _get_log_changes(self):
        return self._log_changes

    def _set_log_changes(self, value):
        self._log_changes = value

    log_changes = property (_get_log_changes, _set_log_changes)

    def _set_modified(self, value):
        self._modified = value

    def is_modified(self):
        return self._modified

    def disable_controls(self):
        self._disabled_count -= 1

    def enable_controls(self):
        self._disabled_count += 1
        if self.controls_enabled():
            self.update_controls(common.UPDATE_SCROLLED)

    def controls_enabled(self):
        return self._disabled_count == 0

    def controls_disabled(self):
        return not self.controls_enabled()

    def _get_active(self):
        return self._active

    active = property (_get_active)

    def _set_read_only(self, value):
        self._read_only = value
        for field in self.fields:
            field.update_controls()

    def _get_read_only(self):
        return self._read_only

    read_only = property (_get_read_only, _set_read_only)

    def _get_filtered(self):
        return self._filtered

    def _set_filtered(self, value):
        if value:
            if not self.on_filter_record:
                value = False
        if self._filtered != value:
            self._filtered = value
            self.first()
            self.update_controls(common.UPDATE_OPEN)

    filtered = property (_get_filtered, _set_filtered)

    def _set_item_state(self, value):
        if self._state != value:
            self._state = value
            if self.on_state_changed:
                self.on_state_changed(self)

    def _get_item_state(self):
        return self._state

    item_state = property (_get_item_state, _set_item_state)

    def _do_after_scroll(self):
        self.update_controls(common.UPDATE_SCROLLED)
        if self.on_after_scroll:
            self.on_after_scroll(self)

    def _do_before_scroll(self):
        if not self._cur_row is None:
            if self.item_state in (common.STATE_INSERT, common.STATE_EDIT):
                self.post()
            if self.on_before_scroll:
                self.on_before_scroll(self)

    def skip(self, value):
        if self.record_count() == 0:
            self._do_before_scroll()
            self._eof = True
            self._bof = True
            self._do_after_scroll()
        else:
            old_row = self._cur_row
            eof = False
            bof = False
            new_row = value
            if new_row < 0:
                new_row = 0
                bof = True
            if new_row >= len(self._dataset):
                new_row = len(self._dataset) - 1
                eof = True
            self._eof = eof
            self._bof = bof
            if old_row != new_row:
                self._cur_row = new_row
                self._do_after_scroll()
            elif (eof or bof) and self.is_new() and self.record_count() == 1:
                self._do_before_scroll()
                self._do_after_scroll()

    def _set_rec_no(self, value):
        if self._active:
            if self.filter_active():
                self.search_record(value, 0)
            else:
                self.skip(value)

    def _get_rec_no(self):
        if self._active:
            return self._cur_row

    rec_no = property (_get_rec_no, _set_rec_no)

    def filter_active(self):
        if self.on_filter_record and self.filtered:
            return True

    def first(self):
        if self.filter_active():
            self.find_first()
        else:
            self.rec_no = 0

    def last(self):
        if self.filter_active():
            self.find_last()
        else:
            self.rec_no = len(self._dataset)

    def next(self):
        if self.filter_active():
            self.find_next()
        else:
            self.rec_no += 1

    def prior(self):
        if self.filter_active():
            self.find_prior()
        else:
            self.rec_no -= 1

    def eof(self):
        return self._eof

    def bof(self):
        return self._bof

    def valid_record(self):
        if self.on_filter_record and self.filtered:
            return self.on_filter_record(self)
        else:
            return True

    def search_record(self, start, direction=1):

        def update_position():
            if self.record_count() != 0:
                self._eof = False
                self._bof = False
                if self._cur_row < 0:
                    self._cur_row = 0
                    self._bof = True
                if self._cur_row >= len(self._dataset):
                    self._cur_row = len(self._dataset) - 1
                    self._eof = True

        def check_record():
            if direction == 1:
                return self.eof()
            else:
                return self.bof()

        if self.active:
            if self.record_count() == 0:
                self.skip(start)
                return
            cur_row = self._cur_row
            self._cur_row = start + direction
            update_position()
            if direction == 0:
                if self.valid_record():
                    self._cur_row = cur_row
                    self.skip(start)
                    return
                direction = 1
            while not check_record():
                if self.valid_record():
                    if start != self._cur_row:
                        row = self._cur_row
                        self._cur_row = start
                        self.skip(row)
                        return
                else:
                    self._cur_row = self._cur_row + direction
                    update_position()

    def find_first(self):
        self.search_record(-1, 1)

    def find_last(self):
        self.search_record(len(self._dataset), -1)

    def find_next(self):
        self.search_record(self.rec_no, 1)

    def find_prior(self):
        self.search_record(self.rec_no, -1)

    def record_count(self):
        if self._dataset:
            return len(self._dataset)
        else:
            return 0

    def update_controls(self, state):
        pass

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
            return info[common.REC_STATUS]

    def _set_record_status(self, value):
        info = self.get_rec_info()
        if info and (self.log_changes or self._is_delta):
            info[common.REC_STATUS] = value

    record_status = property (get_records_status, _set_record_status)

    def _get_rec_change_id(self):
        info = self.get_rec_info()
        if info:
            return info[common.REC_CHANGE_ID]

    def _set_rec_change_id(self, value):
        info = self.get_rec_info()
        if info:
            info[common.REC_CHANGE_ID] = value

    rec_change_id = property (_get_rec_change_id, _set_rec_change_id)

    def rec_controls_info(self):
        info = self.get_rec_info()
        if info:
            return info[common.REC_CONTROLS_INFO]

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
        for field_arg in field_dict.iterkeys():
            field_name = field_arg
            pos = field_name.find('__')
            if pos > -1:
                filter_str = field_name[pos+2:]
                field_name = field_name[:pos]
            else:
                filter_str = 'eq'
            filter_type = common.FILTER_STR.index(filter_str)
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

    def set_fields(self, *fields):
        self._select_field_list = [field for field in fields];

    def set_where(self, **fields):
        self._where_list = self.get_where_list(fields)

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
                raise RuntimeError('%s: change_order method arument error - %s' % (self.item_name, field))
            result.append([fld.ID, desc])
        return result

    def set_order_by(self, *fields):
        self._order_by_list = self.get_order_by_list(fields)

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

        if self.on_before_open:
             self.on_before_open(self, params)

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
            if where:
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
                filters.append([field_name, common.FILTER_CONTAINS_ALL, text])
            params['__filters'] = filters
            if order_by:
                params['__order'] = self.get_order_by_list(order_by)
            elif self._order_by_list:
                params['__order'] = list(self._order_by_list)
            elif self._order_by:
                params['__order'] = self._order_by
            if funcs:
                params['__funcs'] = funcs
            if group_by:
                params['__group_by'] = group_by
            self._order_by_list = []
            self._where_list = []
            self._open_params = params

    def _do_after_open(self):
        if self.on_after_open:
            self.on_after_open(self)

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
        self._cur_row = None
        self.item_state = common.STATE_BROWSE
        self.first()
        self._do_after_open()
        self.update_controls(common.UPDATE_OPEN)
        if self.on_filters_applied:
            self.on_filters_applied(self)

    def do_open(self, params=None):
        if not params:
            params = self._open_params
        rows, error_mes = self.do_internal_open(params)
        if error_mes:
            raise RuntimeError(error_mes)
        else:
            self._dataset = rows

    def close(self):
        self._active = False
        self._cur_row = None
        self._dataset = None
        self.close_details()

    def close_details(self):
        for detail in self.details:
            detail.close()

    def new_record(self):
        result = [None for field in self.fields if not field.master_field]
        if self.expanded:
            result += [None for field in self.fields if field.lookup_item]
        return result

    def _do_before_append(self):
        if self.on_before_append:
            self.on_before_append(self)

    def _do_after_append(self):
        for field in self.fields:
            if field.default_value:
                try:
                    field.text = field.default_value
                except:
                    pass
        self._modified = False
        if self.on_after_append:
            self.on_after_append(self)

    def append(self):
        if not self.active:
            raise DatasetException(self.task.lang['append_not_active'] % self.item_name)
        if self.item_state != common.STATE_BROWSE:
            raise DatasetException(self.task.lang['append_not_browse'] % self.item_name)
        self._do_before_append()
        self._do_before_scroll()
        self._old_row = self.rec_no
        self.item_state = common.STATE_INSERT
        self._dataset.append(self.new_record())
        self._cur_row = len(self._dataset) - 1
        self.record_status = common.RECORD_INSERTED
        self.update_controls(common.UPDATE_APPEND)
        self._do_after_scroll()
        self._do_after_append()

    def insert(self):
        if not self.active:
            raise DatasetException(self.task.lang['insert_not_active'] % self.item_name)
        if self.item_state != common.STATE_BROWSE:
            raise DatasetException(self.task.lang['insert_not_browse'] % self.item_name)
        self._do_before_append()
        self._do_before_scroll()
        self._old_row = self.rec_no
        self.item_state = common.STATE_INSERT
        self._dataset.insert(0, self.new_record())
        self._cur_row = 0
        self._modified = False
        self.record_status = common.RECORD_INSERTED
        self.update_controls(common.UPDATE_INSERT)
        self._do_after_scroll()
        self._do_after_append()

    def rec_inserted(self):
        return self.record_status == common.RECORD_INSERTED

    def rec_deleted(self):
        return self.record_status == common.RECORD_DELETED

    def rec_modified(self):
        return self.record_status in (common.RECORD_MODIFIED, common.RECORD_DETAILS_MODIFIED)

    def is_browsing(self):
        return self.item_state == consts.STATE_BROWSE

    def is_changing(self):
        return (self.item_state == common.STATE_INSERT) or (self.item_state == common.STATE_EDIT)

    def is_new(self):
        return self.item_state == common.STATE_INSERT

    def is_edited(self):
        return self.item_state == common.STATE_EDIT

    def is_deleting(self):
        return self.item_state == common.STATE_DELETE

    def _do_before_edit(self):
        if self.on_before_edit:
            self.on_before_edit(self)

    def _do_after_edit(self):
        if self.on_after_edit:
            self.on_after_edit(self)

    def edit(self):
        if not self.active:
            raise DatasetException(self.task.lang['edit_not_active'] % self.item_name)
        if self.item_state != common.STATE_BROWSE:
            raise DatasetException(self.task.lang['edit_not_browse'] % self.item_name)
        if self.record_count() == 0:
            raise DatasetException(self.task.lang['edit_no_records'] % self.item_name)
        self._do_before_edit()
        self.change_log.log_change()
        self._buffer = self.change_log.store_record_log()
        self.item_state = common.STATE_EDIT
        self._old_row = self.rec_no
        self._old_status = self.record_status
        self._modified = False
        self._do_after_edit()

    def _do_before_delete(self):
        if self.on_before_delete:
            self.on_before_delete(self)

    def _do_after_delete(self):
        if self.on_after_delete:
            self.on_after_delete(self)

    def delete(self):
        if not self.active:
            raise DatasetException(self.task.lang['delete_not_active'] % self.item_name)
        if self.record_count() == 0:
            raise DatasetException(self.task.lang['delete_no_records'] % self.item_name)
        self.item_state = common.STATE_DELETE
        try:
            self._do_before_delete()
            self._do_before_scroll()
            self.update_controls(common.UPDATE_DELETE)
            self.change_log.log_change()
            if self.master:
                self.master._set_modified(True)
            self._dataset.remove(self._dataset[self.rec_no])
            self.rec_no = self.rec_no
            self._do_after_scroll()
            self.item_state = common.STATE_BROWSE
            self._do_after_delete()
        finally:
            self.item_state = common.STATE_BROWSE

    def _do_before_cancel(self):
        if self.on_before_cancel:
            self.on_before_cancel(self)

    def _do_after_cancel(self):
        if self.on_after_cancel:
            self.on_after_cancel(self)

    def cancel(self):
        self._do_before_cancel()
        if self.item_state == common.STATE_EDIT:
            self.change_log.restore_record_log(self._buffer)
            self.update_controls(common.UPDATE_CANCEL)
            for detail in self.details:
                detail.update_controls(common.UPDATE_OPEN)
        elif self.item_state == common.STATE_INSERT:
            self.change_log.remove_record_log()
            self.update_controls(common.UPDATE_DELETE)
            del self._dataset[self.rec_no]
        else:
            raise Exception(self.task.lang['cancel_invalid_state'] % self.item_name)
        prev_state = self.item_state
        self.item_state = common.STATE_BROWSE
        if prev_state in [common.STATE_INSERT]:
            self._do_before_scroll()
        self._cur_row = self._old_row
        if prev_state in [common.STATE_EDIT]:
            self.record_status = self._old_status
        self._set_modified(False)
        if prev_state in [common.STATE_INSERT]:
            self._do_after_scroll()
        self._do_after_cancel()

    def _do_before_post(self):
        if self.on_before_post:
            self.on_before_post(self)

    def _do_after_post(self):
        if self.on_after_post:
            self.on_after_post(self)

    def post(self):
        if not self.is_changing():
            raise DatasetException(self.task.lang['not_edit_insert_state'] % self.item_name)
        self.check_record_valid()
        self._do_before_post()
        if self.master:
            self.field_by_name(self._master_id).value = self.master.ID
        for detail in self.details:
            if detail.is_changing():
                detail.post()
        if self.is_modified() or self.is_new():
            self.change_log.log_change()
        elif self.record_status == common.RECORD_UNCHANGED:
            self.change_log.remove_record_log()
        self._modified = False
        self.item_state = common.STATE_BROWSE
        self._do_after_post()
        if not self.valid_record():
            self.update_controls(common.UPDATE_DELETE)
            self.search_record(self.rec_no, 0)

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

    def set_filters(self, **filters):
        self.clear_filters()
        for filter_name in filters.iterkeys():
            try:
                filter = self.filter_by_name(filter_name)
                filter.value = filters[filter_name]
            except Exception as e:
                raise RuntimeError('%s: set_filters method arument error %s=%s: %s' % (self.item_name, filter_name, filters[filter_name], e))

    def get_default_field(self):
        try:
            return self._default_field
        except:
            self._default_field = None
            for field in self.fields:
                if field.is_default:
                    self._default_field = field
                    break
            return self._default_field

    default_field = property (get_default_field)

    def round(self, value, dec):
        return round(value, dec)

class MasterDataSet(AbstractDataSet):
    def __init__(self):
        AbstractDataSet.__init__(self)
        self.details_active = False

    def _copy(self, filters=True, details=True, handlers=True):
        result = super(MasterDataSet, self)._copy(filters, details, handlers)
        if details:
            for detail in self.details:
                copy_table = detail._copy(filters, details, handlers)
                copy_table.owner = result
                copy_table.master = result
                copy_table.expanded = detail.expanded
                result.details.append(copy_table)
                result.items.append(copy_table)
                if not hasattr(result, copy_table.item_name):
                    setattr(result, copy_table.item_name, copy_table)
                if not hasattr(result.details, copy_table.item_name):
                    setattr(result.details, copy_table.item_name, copy_table)

        return result

    def do_apply(self, params, safe):
        pass

    def apply(self, params=None, safe=False):
        result = None
        if self.is_changing():
            self.post()
        if self.on_before_apply:
            result = self.on_before_apply(self)
            if result:
                params = result
        self.do_apply(params, safe)
        if self.on_after_apply:
            self.on_after_apply(self)

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
        result.item_state = common.STATE_BROWSE
        result._cur_row = None
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
            if self.master.record_status != common.RECORD_UNCHANGED:
                return self.master.change_log.get_detail_log(str(self.ID))

    def open(self, expanded=None, fields=None, where=None, order_by=None,
        open_empty=False, params=None, offset=None, limit=None, funcs=None,
        group_by=None, safe=False):
        if safe and not self.can_view():
            raise Exception(self.task.lang['cant_view'] % self.item_caption)
        if expanded is None:
            expanded = self.expanded
        else:
            self.expanded = expanded
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
                    self.item_state = common.STATE_BROWSE
                    self.first()
                    self._do_after_open()
                    self.update_controls(common.UPDATE_OPEN)
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

    def open__in(self, ids, expanded=None, fields=None, where=None, order_by=None, open_empty=False, params=None, offset=None, limit=None):

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
        for args, value in locals().iteritems():
            if not args in ['self', 'ids', 'params', 'slice_ids']:
                params[args] = value
        if type(ids) == dict:
            keys = list(ids.iterkeys())
            id_field_name = keys[0]
            ids = ids[id_field_name]
        elif type(ids) == list:
            id_field_name = 'id'
        else:
            raise Exception('Item %s: invalid ids parameter in open__in method' % self.item_name)
        if params['where'] is None:
            params['where'] = {}
        on_after_open = self.on_after_open
        self.on_after_open = None
        on_filters_applied = self.on_filters_applied
        self.on_filters_applied = None
        records = []
        lst = slice_ids(ids)
        for l in lst:
            params['where'][id_field_name + '__in'] = l
            self.open(**params)
            records += self._dataset
        self._dataset = records
        self.first()
        self.on_after_open = on_after_open
        self.on_filters_applied = on_filters_applied
        self._do_after_open()
        self.update_controls(common.UPDATE_OPEN)
        if self.on_filters_applied:
            self.on_filters_applied(self)

    def insert(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(self.task.lang['insert_master_not_changing'] % self.item_name)
        super(MasterDetailDataset, self).insert()

    def append(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(self.task.lang['append_master_not_changing'] % self.item_name)
        super(MasterDetailDataset, self).append()

    def edit(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(self.task.lang['edit_master_not_changing'] % self.item_name)
        super(MasterDetailDataset, self).edit()

    def delete(self):
        if self.master and not self.master.is_changing():
            raise DatasetException(self.task.lang['delete_master_not_changing'] % self.item_name)
        super(MasterDetailDataset, self).delete()

    def _set_modified(self, value):
        self._modified = value
        if self.master and value:
            self.master._set_modified(value)

    def is_modified(self):
        return super(MasterDetailDataset, self).is_modified()

#    modified = property (is_modified, _set_modified)

    def _get_read_only(self):
        if self.master and self.parent_read_only:
            return self.master.read_only
        else:
            return super(MasterDetailDataset, self)._get_read_only()

    def _set_read_only(self, value):
        return super(MasterDetailDataset, self)._set_read_only(value)

    read_only = property (_get_read_only, _set_read_only)

class Dataset(MasterDetailDataset):
    pass
