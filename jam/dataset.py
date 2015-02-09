# -*- coding: utf-8 -*-

import datetime
import traceback
import common

FIELD_INFO = FIELD_ID, FIELD_NAME, NAME, FIELD_DATA_TYPE, REQUIRED, ITEM, MASTER_FIELD, lookup_field, \
    FIELD_VISIBLE, FIELD_VIEW_INDEX, FIELD_EDIT_VISIBLE, FIELD_EDIT_INDEX, FIELD_READ_ONLY, FIELD_EXPAND, FIELD_WORD_WRAP, \
    FIELD_SIZE, FIELD_DEFAULT, FIELD_CALCULATED, FIELD_EDITABLE, FIELD_ALIGNMENT, FIELD_VALUES_LIST = range(21)

class DatasetException(Exception):
    pass

class AbortException(Exception):
    pass

class DBField(object):
    def __init__(self):
        self.ID = None
        self.required = None
        self.field_size = None
        self.is_default = None
        self.data_type = None
        self.required = None
        self.master_field = None
        self.lookup_field = None
        self.view_index = None
        self.edit_visible = None
        self.edit_index = None
        self.calculated = None
        self.editable = None
        self._read_only = None
        self._visible = None
        self._expand = None
        self._word_wrap = None
        self.wrap_width = 0
        self._alignment = 0
        self.value_list = None
        self.bind_index = None
        self.lookup_index = None
        self.filter = None
        self.owner = None
        self.new_value = None

    def copy(self, owner):
        result = self.__class__(owner, self.get_info())
        return result

    def get_info(self):
        result = [None for i in range(len(FIELD_INFO))]
        result[FIELD_ID] = self.ID
        result[FIELD_NAME] = self.field_name
        result[NAME] = self.field_caption
        result[FIELD_DATA_TYPE] = self.data_type
        result[REQUIRED] = self.required
        if self.lookup_item:
            if type(self.lookup_item) == int:
                result[ITEM] = self.lookup_item
            else:
                result[ITEM] = self.lookup_item.ID
        result[MASTER_FIELD] = None
        if self.master_field:
            if type(self.master_field) == int:
                result[MASTER_FIELD] = self.master_field
            else:
                result[MASTER_FIELD] = self.master_field.ID
        result[lookup_field] = self.lookup_field
        result[FIELD_READ_ONLY] = self._read_only
        result[FIELD_VISIBLE] = self.view_visible
        result[FIELD_VIEW_INDEX] = self.view_index
        result[FIELD_EDIT_VISIBLE] = self.edit_visible
        result[FIELD_EDIT_INDEX] = self.edit_index
        result[FIELD_EXPAND] = self.expand
        result[FIELD_WORD_WRAP] = self.word_wrap
        result[FIELD_SIZE] = self.field_size
        result[FIELD_DEFAULT] = self.is_default
        result[FIELD_CALCULATED] = self.calculated
        result[FIELD_EDITABLE] = self.editable
        result[FIELD_ALIGNMENT] = self.alignment
        result[FIELD_VALUES_LIST] = self.value_list
        return result

    def set_info(self, info):
        self.ID = info[FIELD_ID]
        self.field_name = info[FIELD_NAME]
        self.field_caption = info[NAME]
        self.data_type = info[FIELD_DATA_TYPE]
        self.required = info[REQUIRED]
        self.lookup_item = info[ITEM]
        self.master_field = info[MASTER_FIELD]
        self.lookup_field = info[lookup_field]
        self.read_only = info[FIELD_READ_ONLY]
        self.view_visible = info[FIELD_VISIBLE]
        self.view_index = info[FIELD_VIEW_INDEX]
        self.edit_visible = info[FIELD_EDIT_VISIBLE]
        self.edit_index = info[FIELD_EDIT_INDEX]
        self.expand = info[FIELD_EXPAND]
        self.word_wrap = info[FIELD_WORD_WRAP]
        self.field_size = info[FIELD_SIZE]
        self.is_default = info[FIELD_DEFAULT]
        self.calculated = info[FIELD_CALCULATED]
        self.editable = info[FIELD_EDITABLE]
        self.alignment = info[FIELD_ALIGNMENT]
        self.value_list = info[FIELD_VALUES_LIST]
        self.field_type = common.FIELD_TYPE_NAMES[self.data_type]

    def get_row(self):
        if self.owner._records:
            return self.owner._records[self.owner.rec_no]

    def get_data(self):
        row = self.get_row()
        if row and (self.bind_index >= 0):
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
            result = self.get_raw_value()
            if not result is None:
                if self.data_type == common.INTEGER:
                    result = str(result)
                elif self.data_type == common.FLOAT:
                    result = common.float_to_str(result)
                elif self.data_type == common.CURRENCY:
                    result = common.float_to_str(result)
                elif self.data_type == common.DATE:
                    result = common.date_to_str(result)
                elif self.data_type == common.DATETIME:
                    result = common.datetime_to_str(result)
                elif self.data_type == common.TEXT:
                    result = unicode(result)
                elif self.data_type == common.BOOLEAN:
                    if self.value:
                        if self.owner:
                            result = self.owner.task.lang['yes']
                        else:
                            result = u'True'
                    else:
                        if self.owner:
                            result = self.owner.task.lang['no']
                        else:
                            result = u'False'
                else:
                    result = str(result)
            else:
                result = ''
        except Exception, e:
            print traceback.format_exc()
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
                        if len(value) and value[0] in [u'T', u't']:
                            self.set_value(True)
                        else:
                            self.set_value(False)
                else:
                    self.set_value(value)
            except Exception, e:
                print traceback.format_exc()
                self.do_on_error(self.type_error() % (value), e)

    text = property (get_text, set_text)

    def convert_date_time(self, value):
        if value.find('.'):
            value = value.split('.')[0]
        if value.find('T'):
            value = value.replace('T', ' ')
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

    def convert_date(self, value):
        if value.find(' '):
            value = value.split(' ')[0]
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()

    def get_raw_value(self):
        value = self.get_data()
        try:
            if not value is None:
                if self.data_type in (common.TEXT, ):
                    if not isinstance(value, unicode):
                        value = value.decode('utf-8')
                if self.data_type == common.DATE:
                    if isinstance(value, unicode):
                        value = self.convert_date(value)
                    return value
                elif self.data_type == common.DATETIME:
                    if isinstance(value, unicode):
                        value = self.convert_date_time(value)
                    return value
                elif self.data_type == common.BOOLEAN:
                    if value:
                        return True
                    else:
                        return False
                else:
                    return value
        except Exception, e:
            print traceback.format_exc()
            self.do_on_error(self.type_error() % (''), e)

    raw_value = property (get_raw_value)

    def get_value(self):
        value = self.get_raw_value()
        if value == None:
            if self.data_type == common.BOOLEAN:
                value = False
            elif self.data_type in (common.FLOAT, common.INTEGER, common.CURRENCY):
                value = 0
            elif self.data_type == common.TEXT:
                return ''
        return value

    def do_on_change_lookup_field(self, lookup_value=None, slave_field_values=None):
        if self.lookup_item:
            if self.master_field:
                self.master_field.do_on_change_lookup_field(None)
            else:
                self.set_lookup_value(lookup_value)
                if self.owner:
                    for field in self.owner.fields:
                        if self == field.master_field:
                            if slave_field_values and slave_field_values.get(field.field_name):
                                field.set_lookup_data(slave_field_values[field.field_name])
                            else:
                                field.set_lookup_text(None)
                            field.update_controls();

    def do_before_changed(self, new_value, new_lookup_value):
        if self.owner:
            if not self.owner.item_state in (common.STATE_INSERT, common.STATE_EDIT):
                raise DatasetException, u'%s is not in edit or insert mode' % self.owner.item_name
            if self.owner.on_before_field_changed:
                return self.owner.on_before_field_changed(self, new_value, new_lookup_value)

    def set_value(self, value, lookup_value=None, slave_field_values=None, lookup_item=None):
        if ((self.field_name == 'id' and self.value) or self.field_name == 'deleted') and self.owner and not self.filter and (self.value != value):
            raise DatasetException, u'%s: can not change value of the system field - %s' % (self.owner.item_name, self.field_name)
        self.new_value = None
        if not value is None:
            self.new_value = value
            if self.data_type == common.BOOLEAN:
                self.new_value = bool(value)
            elif self.data_type in (common.FLOAT, common.CURRENCY):
                self.new_value = float(value)
            elif self.data_type == common.INTEGER:
                if not (self.filter and self.filter.filter_type == common.FILTER_IN):
                    self.new_value = int(value)
        if self.raw_value != self.new_value:
            if self.do_before_changed(self.new_value, lookup_value) != False:
                try:
                    self.set_data(self.new_value)
                except Exception, e:
                    print traceback.format_exc()
                    self.do_on_error(self.type_error() % (value), e)
                finally:
                    self.new_value = None
                self.do_on_change_lookup_field(lookup_value, slave_field_values)
                self.set_modified(True)
                self.do_after_changed(lookup_item)

    value = property (get_value, set_value)

    def set_modified(self, value):
        if not self.calculated:
            if self.owner:
                self.owner.modified = value

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
            self.update_controls()

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
                            result = common.date_to_str(result)
                        elif data_type == common.DATETIME:
                            result = common.datetime_to_str(result)
                        elif data_type == common.FLOAT:
                            result = common.float_to_str(result)
                        elif data_type == common.CURRENCY:
                            result = common.currency_to_str(result)
            result = unicode(result)
        except Exception, e:
            print traceback.format_exc()
        return result

    def set_lookup_text(self, text):
        if self.lookup_item:
            data_type = self.get_lookup_data_type()
            if text and data_type:
                if data_type == common.DATE:
                    text = common.str_to_date(text)
                elif data_type == common.DATETIME:
                    text = common.str_to_datetime(text)
                elif data_type == common.FLOAT:
                    text = common.str_to_float(text)
                elif data_type == common.CURRENCY:
                    text = str_to_currency(text)
            self.set_lookup_data(text)
            self.update_controls()
        else:
            self.set_text(text)

    lookup_text = property (get_lookup_text, set_lookup_text)

    def get_display_text(self):
        result = ''
        if self.filter and self.filter.filter_type == common.FILTER_IN and self.filter.field.lookup_item and self.filter.value:
            result = self.filter.owner.task.lang['items_selected'] % len(self.filter.value)
        elif self.lookup_item:
            result = self.lookup_text
        elif self.value_list and self.value:
            try:
                result = self.value_list[self.value - 1]
            except:
                pass
        else:
            if self.data_type == common.CURRENCY:
                if not self.raw_value is None:
                    result = common.currency_to_str(self.value)
            else:
                result = self.text
        if self.owner and not self.filter:
            if self.owner.on_get_field_text:
                res = self.owner.on_get_field_text(self)
                if not res is None:
                    result = res
        return result

    display_text = property(get_display_text)

    def set_read_only(self, value):
        self._read_only = value
        self.update_controls()

    def get_read_only(self):
        result = self._read_only
        if self.owner and self.owner.parent_read_only and self.owner.read_only:
            result = self.owner.read_only
        return result

    read_only = property (get_read_only, set_read_only)

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

    def do_after_changed(self, lookup_item):
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
                print u'%s %s - %s: %s' % (self.owner.item_name,
                    self.owner.task.lang['error'].lower(), self.field_name, mess)
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
        if self.field_name in ('id', 'owner_id', 'owner_rec_id', 'deleted'):
            return True

FILTER_INFO = FILTER_OBJ_NAME, FILTER_NAME, FILTER_FIELD_NAME, \
    FILTER_TYPE, FILTER_DATA_TYPE, FILTER_VISIBLE = range(6)

class DBFilter(object):

    def get_info(self):
        result = [None for i in range(len(FILTER_INFO))]
        result[FILTER_OBJ_NAME] = self.filter_name
        result[FILTER_NAME] = self.filter_caption
        result[FILTER_FIELD_NAME] = self.field_name
        result[FILTER_TYPE] = self.filter_type
        result[FILTER_DATA_TYPE] = self.data_type
        result[FILTER_VISIBLE] = self.visible
        return result

    def set_info(self, info):
        self.filter_name = info[FILTER_OBJ_NAME]
        self.filter_caption = info[FILTER_NAME]
        self.field_name = info[FILTER_FIELD_NAME]
        self.filter_type = info[FILTER_TYPE]
        self.data_type = info[FILTER_DATA_TYPE]
        self.visible = info[FILTER_VISIBLE]

    def set_value(self, value):
        self.field.value = value

    def get_value(self):
        return self.field.raw_value

    value = property (get_value, set_value)


class DBList(list):
    def __init__(self, owner):
        self.owner = owner
        self.obj_by_name = None
        self.attr_err_mess = '%s DBList attribute error: %s'
        self.list_err_mess = '%s: list is empty'

    def __getattr__(self, name):
        if len(self) > 0:
            obj = self.obj_by_name(name)
            if obj:
                setattr(self, name, obj)
                return obj
            else:
                raise AttributeError(self.attr_err_mess % (self.owner.item_name, name))
        else:
            raise RuntimeError(self.list_err_mess % self.owner.item_name)


class DBFilters(list):
    pass

class DBTables(DBList):
    def __init__(self, owner):
        DBList.__init__(self, owner)
        self.obj_by_name = owner.detail_by_name
        self.attr_err_mess = '%s details list attribute error: %s'
        self.list_err_mess = '%s: details list is empty'


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
            return self.item.master.change_log.log_changes();
        else:
            return self.item.log_changes;

    def find_record_log(self):
        result = None
        if self.log_changes():
            if self.item.master:
                record_log = self.item.master.change_log.find_record_log()
                if record_log:
                    details = record_log['details']
                    detail = details.get(str(self.item.ID))
                    if not detail:
                        detail = {
                            'logs': {},
                            'records': self.item._records,
                            'fields': [field.field_name for field in self.item.fields if not field.master_field],
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
                        'unmodified_record': None,
                        'record': self.cur_record(),
                        'details': {}
                    }
                    self.logs[change_id] = result
                return result

    def get_detail_log(self, detail_ID):
        if self.log_changes():
            result = None
            record_log = self.find_record_log()
            details = record_log['details']
            if details:
                result = details.get(detail_ID)
            if result is None and self.item.is_delta:
                result = {'records': [], 'fields': [], 'expanded': False}
            return result

    def remove_record_log(self):
        change_id = self.item.rec_change_id
        if change_id:
            self.find_record_log()
            del self.logs[self.item.rec_change_id]
            self.item.rec_change_id = None
            self.item.record_status = common.RECORD_UNCHANGED

    def cur_record(self):
        return self.item._records[self.item.rec_no]

    def record_modified(self, record_log):
        modified = False
        old_rec = record_log['unmodified_record']
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
                if self.item.record_status == common.RECORD_UNCHANGED:
                    record_log['unmodified_record'] = self.copy_record(self.cur_record(), False)
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
                raise Exception, u'%s: change log invalid records state' % self.item.item_name
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
                        'unmodified_record': record_log['unmodified_record'],
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
            new_records.append([int(key), record])
            details = {}
            self.logs[key] = {
                'unmodified_record': record_log['unmodified_record'],
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
                        'unmodified_record': record_log['unmodified_record'],
                        'record': record,
                        'details': details
                    }
            else:
                if detail_item._records:
                    records = self.copy_records(detail_item._records)
            if records or logs:
                dest[detail_id] = {'logs': logs, 'records': records, 'fields': fields, 'expanded': expanded}

    def store_record_log(self):
        if not self.log_changes():
            result = {}
            result['record'] = self.copy_record(self.cur_record())
            details = {}
            for detail in self.item.details:
                if detail._records:
                    details[str(detail.ID)] = list(detail._records)
            result['details'] = details
        else:
            record_log = self.find_record_log()
            details = {}
            self.store_details(record_log['details'], details)
            result = {}
            result['unmodified_record'] = record_log['unmodified_record']
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
                detail._records = log['details'][str(detail.ID)]
        else:
            record_log = self.find_record_log()
            restore_record()
            record_log['unmodified_record'] = log['unmodified_record']
            record_log['record'] = self.cur_record()
            record_log['details'] = log['details']
            for detail in self.item.details:
                detail_log = log['details'].get(str(detail.ID))
                if detail_log:
                    detail._records = detail_log['records']
            if self.item.record_status == common.RECORD_UNCHANGED:
                self.remove_record_log()


    def prepare(self):
#        self.find_record_log();
        self.records = [];
        self.logs = {};
        self.fields = [field.field_name for field in self.item.fields if not field.master_field]
        self.expanded = self.item.expanded

    def update(self, updates):
        if updates:
            changes = updates['changes']
            for change in changes:
                log_id = change['log_id']
                rec_id = change['rec_id']
                details = change['details']
                record_log = self.logs[log_id]
                record = record_log['record']
                record_details = record_log['details']
                for detail in details:
                    ID = detail['ID']
                    detail_item = self.item.detail_by_ID(int(ID))
                    item_detail = record_details.get(str(ID))
                    if item_detail:
                        detail_item.change_log.logs = item_detail['logs']
                        detail_item.change_log.update(detail)
                if rec_id and not record[self.item.id.bind_index]:
                    record[self.item.id.bind_index] = rec_id
                info = self.item.get_rec_info(record=record)
                info[common.REC_STATUS] = common.RECORD_UNCHANGED
                info[common.REC_CHANGE_ID] = common.RECORD_UNCHANGED
                del self.logs[log_id]


class AbstractDataSet(object):
    def __init__(self):
        self.ID = 0
        self._fields = []
        self.fields = []
        self.filters = DBFilters()#[]
        self.details = DBTables(self)
        self.controls = []
        self.change_log = ChangeLog(self)
        self._log_changes = True
        self._records = None
        self._eof = False
        self._bof = False
        self._cur_row = None
        self._old_row = 0
        self._old_status = None
        self._buffer = None
        self._modified = None
        self._state = common.STATE_NONE
        self._read_only = False
        self._active = False
        self._where_list = []
        self._order_by_list = []
        self.on_state_changed = None
        self.on_filter_changed = None
        self._filter_row = None
        self._record_lookup_index = -1
        self._record_info_index = -1
        self._filtered = False
        self.expanded = True
        self.limit = 100
        self._open_params = {}
        self.auto_loading = False
        self.loaded_count = 0
        self.is_loaded = False
        self.post_local = False
        self._disabled_count = 0
        self.open_params = {}
        self.is_delta = False
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
        self.on_filter_applied = None
        self.on_before_field_changed = None
        self.on_filter_value_changed = None
        self.on_field_validate = None
        self.on_get_field_text = None

    def __getitem__(self, key):
        if key == 0:
            self.first()
        else:
            self.next()
        if self.eof():
            raise IndexError
        return self

    def copy(self, filters=True, details=True, handlers=True):
        result = self.__class__(self.owner, self.item_name, self.item_caption, self.visible)
        result.ID = self.ID
        result.item_name = self.item_name
        result.expanded = self.expanded
        result.limit = self.limit

        for field in self._fields:
            copy_field = field.copy(result)
            copy_field.lookup_item = field.lookup_item
            result._fields.append(copy_field)
        for field in result._fields:
            if field.master_field:
                field.master_field = result.get_master_field(result._fields, field.master_field)
        result.fields = list(result._fields)
        for field in result.fields:
            if not hasattr(result, field.field_name):
                setattr(result, field.field_name, field)
        if filters:
            for fltr in self.filters:
                result.filters.append(fltr.copy(result))
            result._filter_row = []
            if len(result.filters) > 0:
                for i, fltr in enumerate(result.filters):
                    setattr(result.filters, fltr.filter_name, fltr)
                    result._filter_row.append(None)
                    fltr.field.bind_index = i
                for fltr in result.filters:
                    if fltr.field.lookup_item:
                        result._filter_row.append(None)
                        fltr.field.lookup_index = len(result._filter_row) - 1
        result._events = self._events
        if handlers:
            for func_name, func in result._events:
                setattr(result, func_name, func)
        return result

    def clone(self, keep_filtered=True):
        result = self.__class__(self.owner, self.item_name, self.item_caption, self.visible)
        result.ID = self.ID
        result.item_name = self.item_name
        for field in self._fields:
            copy_field = field.copy(result)
            copy_field.lookup_item = field.lookup_item
            result._fields.append(copy_field)
        for field in result._fields:
            if field.master_field:
                field.master_field = result.get_master_field(result._fields, field.master_field)
        for field in self.fields:
            new_field = result._field_by_name(field.field_name)
            result.fields.append(new_field)
            if not hasattr(result, new_field.field_name):
                setattr(result, new_field.field_name, new_field)
        result.bind_fields()
        result._records = self._records
        if keep_filtered:
            result.on_filter_record = self.on_filter_record
            result.filtered = self.filtered
        result._active = True
        result.first()
        return result

    def get_records(self):
        result = []
        if self.active:
            for r in self._records:
                result.append(r[0:self._record_info_index])
        return result

    def set_records(self, value):
        self._records = value

    records = property (get_records, set_records)

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

    def get_log_changes(self):
        return self._log_changes

    def set_log_changes(self, value):
        self._log_changes = value

    log_changes = property (get_log_changes, set_log_changes)

    def set_modified(self, value):
        self._modified = value

    def get_modified(self):
        return self._modified

    modified = property (get_modified, set_modified)

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

    def get_active(self):
        return self._active

    active = property (get_active)

    def set_read_only(self, value):
        self._read_only = value
        #~ if not self.parent_read_only:
            #~ for field in self.fields:
                #~ field.read_only = value
        for field in self.fields:
            field.update_controls()

    def get_read_only(self):
        return self._read_only

    read_only = property (get_read_only, set_read_only)

    def get_filtered(self):
        return self._filtered

    def set_filtered(self, value):
        if value:
            if not self.on_filter_record:
                value = False
        if self._filtered != value:
            self._filtered = value
            self.first()
            self.update_controls(common.UPDATE_OPEN)

    filtered = property (get_filtered, set_filtered)

    def set_state(self, value):
        if self._state != value:
            self._state = value
            if self.on_state_changed:
                self.on_state_changed(self)

    def get_state(self):
        return self._state

    item_state = property (get_state, set_state)

    def do_after_scroll(self):
        self.update_controls(common.UPDATE_SCROLLED)
        if self.on_after_scroll:
            self.on_after_scroll(self)

    def do_before_scroll(self):
        if not self._cur_row is None:
            if self.item_state in (common.STATE_INSERT, common.STATE_EDIT):
                self.post()
            if self.on_before_scroll:
                return self.on_before_scroll(self)

    def skip(self, value):
        if self.record_count() == 0:
            self.do_before_scroll()
            self._eof = True
            self._bof = True
            self.do_after_scroll()
        else:
            old_row = self._cur_row
            eof = False
            bof = False
            new_row = value
            if new_row < 0:
                new_row = 0
                bof = True
            if new_row >= len(self._records):
                new_row = len(self._records) - 1
                eof = True
            self._eof = eof
            self._bof = bof
            if old_row != new_row:
                if self.do_before_scroll() != False:
                    self._cur_row = new_row
                    self.do_after_scroll()
            elif (eof or bof) and self.is_new() and self.record_count() == 1:
                self.do_before_scroll()
                self.do_after_scroll()

    def set_rec_no(self, value):
        if self._active:
            if self.filter_active():
                self.search_record(value, 0)
            else:
                self.skip(value)

    def get_rec_no(self):
        if self._active:
            return self._cur_row

    rec_no = property (get_rec_no, set_rec_no)

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
            self.rec_no = len(self._records)

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

    def search_record(self, start, direction = 1):

        def update_position():
            if self.record_count() != 0:
                self._eof = False
                self._bof = False
                if self._cur_row < 0:
                    self._cur_row = 0
                    self._bof = True
                if self._cur_row >= len(self._records):
                    self._cur_row = len(self._records) - 1
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
            self._cur_row = start + direction
            update_position()
            if direction == 0:
                if self.valid_record():
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
        self.search_record(len(self._records), -1)

    def find_next(self):
        self.search_record(self.rec_no, 1)

    def find_prior(self):
        self.search_record(self.rec_no, -1)

    def record_count(self):
        if self._records:
            return len(self._records)
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
                record = self._records[rec_no];
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

    def set_record_status(self, value):
        info = self.get_rec_info()
        if info and self.log_changes:
            info[common.REC_STATUS] = value

    record_status = property (get_records_status, set_record_status)

    def get_rec_change_id(self):
        info = self.get_rec_info()
        if info:
            return info[common.REC_CHANGE_ID]

    def set_rec_change_id(self, value):
        info = self.get_rec_info()
        if info:
            info[common.REC_CHANGE_ID] = value

    rec_change_id = property (get_rec_change_id, set_rec_change_id)

    def rec_controls_info(self):
        info = self.get_rec_info()
        if info:
            return info[common.REC_CONTROLS_INFO]

    def bind_fields(self, expanded=True):
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
        for field_arg in field_dict.keys():
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
                result.append((field_name, filter_type, value))
        return result

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

    def do_before_open(self, expanded, fields, where, order_by, open_empty, params):
        result = None
        params['__expanded'] = expanded
        params['__fields'] = []
        params['__filters'] = []
        filters = []

        if self.on_before_open:
             result = self.on_before_open(self, params)
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
                    raise Exception, '%s - do_before_open method error: there is no field with field_name: %s' % (self.item_name, field_name)
            params['__fields'] = fields
        else:
            self.fields = list(self._fields)
        for field in self.fields:
            if not hasattr(self, field.field_name):
                setattr(self, field.field_name, field)
        if result != False and not open_empty:
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
                filters.append([field_name, common.FILTER_SEARCH, text])
            params['__filters'] = filters
            if order_by:
                params['__order'] = get_order_by_list(order_by)
            elif self._order_by_list:
                params['__order'] = list(self._order_by_list)
            self._order_by_list = []
            self._where_list = []
            self._open_params = params
        return result

    def do_after_open(self):
        if self.on_after_open:
            self.on_after_open(self)

    def open(self, expanded, fields, where, order_by, open_empty, params, offset):
        if not params:
            params = {}
        self.loaded_count = 0
        if not offset is None:
            self.loaded_count = offset
        if self.do_before_open(expanded, fields, where, order_by, open_empty, params) != False:
            self.change_log.prepare()
            self.bind_fields(expanded)
            self._records = []
            if not open_empty:
                self.load_next(params)
            self._active = True
            self._cur_row = None
            self.item_state = common.STATE_BROWSE
            self.first()
            self.do_after_open()
            self.update_controls(common.UPDATE_OPEN)
            if self.on_filter_applied:
                self.on_filter_applied(self)


    def load_next(self, params=None):
        if not params:
            params = self._open_params
        if self.auto_loading:
            params['__loaded'] = self.loaded_count
            params['__limit'] = self.limit
        else:
            params['__loaded'] = 0
            params['__limit'] = 0
        rows, error_mes = self.do_internal_open(params)
        if error_mes:
#            self.warning(error_mes)
            raise RuntimeError(error_mes)
        else:
            for row in rows:
                self._records.append(list(row))
            result = len(rows)
            if self.limit and self.auto_loading and result:
                self.loaded_count += self.limit
                self.is_loaded = False
            if result < self.limit:
                self.is_loaded = True
            return result

    def close(self):
        self._active = False
        self._cur_row = None
        self._records = None
        self.close_details()

    def close_details(self):
        for detail in self.details:
            detail.close()

    def new_record(self):
        result = [None for field in self.fields if not field.master_field]
        if self.expanded:
            result += [None for field in self.fields if field.lookup_item]
#        result.append([None, {}, None])
        return result

    def do_before_append(self):
        if self.on_before_append:
            return self.on_before_append(self)

    def do_after_append(self):
        if self.on_after_append:
            self.on_after_append(self)

    def append(self):
        if not self.active:
            raise DatasetException(u"Can't insert record in %s: %s is not active" % (self.item_name, self.item_name))
        if self.item_state != common.STATE_BROWSE:
            raise DatasetException(u"Can't insert record in %s: %s is not in browse state" % (self.item_name, self.item_name))
        if self.do_before_append() != False:
            if self.do_before_scroll() != False:
                self._old_row = self.rec_no
                self.item_state = common.STATE_INSERT
                self._records.append(self.new_record())
                self._cur_row = len(self._records) - 1
                self._modified = False
                self.record_status = common.RECORD_INSERTED
                self.update_controls(common.UPDATE_APPEND)
                self.do_after_scroll()
                self.do_after_append()

    def insert(self):
        if not self.active:
            raise DatasetException(u"Can't insert record in %s: %s is not active" % (self.item_name, self.item_name))
        if self.item_state != common.STATE_BROWSE:
            raise DatasetException(u"Can't insert record in %s: %s is not in browse state" % (self.item_name, self.item_name))
        if self.do_before_append() != False:
            if self.do_before_scroll() != False:
                self._old_row = self.rec_no
                self.item_state = common.STATE_INSERT
                self._records.insert(0, self.new_record())
                self._cur_row = 0
                self._modified = False
                self.record_status = common.RECORD_INSERTED
                self.update_controls(common.UPDATE_INSERT)
                self.do_after_scroll()
                self.do_after_append()

    def copy_rec(self):
        if not self.active:
            raise DatasetException(u"Can't copy record in %s: %s is not active" % (self.item_name, self.item_name))
        if self.item_state != common.STATE_BROWSE:
            raise DatasetException(u"Can't copy record in %s: %s is not in browse state" % (self.item_name, self.item_name))
        if self.record_count() == 0:
            raise DatasetException(u"Can't copy record in %s: %s' record list is empty" % (self.item_name, self.item_name))
        if self.record_count() > 0:
            if self.do_before_append() != False:
                if self.do_before_scroll() != False:
                    self._old_row = self.rec_no
                    self.item_state = common.STATE_INSERT
                    self._buffer = list(self._records[self.rec_no])
                    self._records.append(self.new_record())
                    self._cur_row = len(self._records) - 1
                    for i, it in enumerate(self._records[self.rec_no]):
                        if i < self._record_info_index:
                            self._records[self.rec_no][i] = self._buffer[i]
                    self._records[self.rec_no][self.field_by_name('id').bind_index] = None
                    self._buffer = None
                    self._modified = False
                    self.record_status = common.RECORD_INSERTED
                    self.update_controls(common.UPDATE_APPEND)
                    self.do_after_scroll()
                    self.do_after_append()

    def rec_inserted(self):
        return self.record_status == common.RECORD_INSERTED

    def rec_deleted(self):
        return self.record_status == common.RECORD_DELETED

    def rec_modified(self):
        return self.record_status in (common.RECORD_MODIFIED, common.RECORD_DETAILS_MODIFIED)

    def is_changing(self):
        return (self.item_state == common.STATE_INSERT) or (self.item_state == common.STATE_EDIT)

    def is_new(self):
        return self.item_state == common.STATE_INSERT

    def is_editing(self):
        return self.item_state == common.STATE_EDIT

    def is_deleting(self):
        return self.item_state == common.STATE_DELETE

    def do_before_edit(self):
        if self.on_before_edit:
            return self.on_before_edit(self)

    def do_after_edit(self):
        if self.on_after_edit:
            self.on_after_edit(self)

    def edit(self):
        if not self.active:
            raise DatasetException(u"Can't edit record in %s: %s is not active" % (self.item_name, self.item_name))
        if self.item_state != common.STATE_BROWSE:
            raise DatasetException(u"Can't edit record in %s: %s is not in browse state" % (self.item_name, self.item_name))
        if self.record_count() == 0:
            raise DatasetException(u"Can't edit record in %s: %s' record list is empty" % (self.item_name, self.item_name))
        if self.do_before_edit() != False:
            self.change_log.log_change()
            self._buffer = self.change_log.store_record_log()
            self.item_state = common.STATE_EDIT
            self._old_row = self.rec_no
            self._old_status = self.record_status
            self._modified = False
            self.do_after_edit()

    def do_before_delete(self):
        if self.on_before_delete:
            return self.on_before_delete(self)

    def do_after_delete(self):
        if self.on_after_delete:
            self.on_after_delete(self)

    def delete(self):
        self.item_state = common.STATE_DELETE
        try:
            if self.record_count() > 0:
                if self.do_before_delete() != False:
                    if self.do_before_scroll() != False:
                        self.update_controls(common.UPDATE_DELETE)
                        self.change_log.log_change()
                        if self.master:
                            self.master.modified = True
                        self._records.remove(self._records[self.rec_no])
                        self.rec_no = self.rec_no
                        self.do_after_scroll()
                        self.item_state = common.STATE_BROWSE
                        self.do_after_delete()
        finally:
            self.item_state = common.STATE_BROWSE

    def do_before_cancel(self):
        if self.on_before_cancel:
            return self.on_before_cancel(self)

    def do_after_cancel(self):
        if self.on_after_cancel:
            self.on_after_cancel(self)

    def cancel(self):
        if self.do_before_cancel() != False:
            if self.item_state == common.STATE_EDIT:
                self.change_log.restore_record_log(self._buffer)
                self.update_controls(common.UPDATE_CANCEL)
                for detail in self.details:
                    detail.update_controls(common.UPDATE_OPEN)
            elif self.item_state == common.STATE_INSERT:
                self.change_log.remove_record_log()
                self.update_controls(common.UPDATE_DELETE)
                del self._records[self.rec_no]
            else:
                raise Exception, '%s cancel error: invalid item state' % self.item_name
            prev_state = self.item_state
            self.item_state = common.STATE_BROWSE
            if prev_state in [common.STATE_INSERT]:
                self.do_before_scroll()
            self._cur_row = self._old_row
            if prev_state in [common.STATE_EDIT]:
                self.record_status = self._old_status
            self.modified = False
            if prev_state in [common.STATE_INSERT]:
                self.do_after_scroll()
            self.do_after_cancel()

    def do_before_post(self):
        if self.on_before_post:
            return self.on_before_post(self)

    def do_after_post(self):
        if self.on_after_post:
            self.on_after_post(self)

    def post(self):
        result = False
        if not self.is_changing():
            raise DatasetException, u'%s: dataset is not in edit or insert mode' % self.item_name
        if self.modified:
            if self.check_record_valid():
                if self.do_before_post() != False:
                    for detail in self.details:
                        if detail.is_changing():
                            if not detail.post():
                                return result
                    self.change_log.log_change()
                    self.modified = False
                    if self.master:
                        self.master.modified = True
                    self.item_state = common.STATE_BROWSE
                    if not self.valid_record():
                        self.update_controls(common.UPDATE_DELETE)
                        self.search_record(self.rec_no, 0)
                    self.do_after_post()
                    result = True
        else:
            self.cancel()
            result = True
        return result

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
                return true
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
        for filter_name in filters.keys():
            try:
                filter = self.filter_by_name(filter_name)
                filter.value = filters[filter_name]
            except Exception, e:
                raise RuntimeError('%s: set_filters method arument error %s=%s: %s' % (self.item_name, filter_name, filters[filter_name], e))

    #~ def set_fields(self, **fields):
        #~ for field_name in fields.keys():
            #~ try:
                #~ field = self.field_by_name(field_name)
                #~ value = fields[field_name]
                #~ field.value = value
            #~ except Exception, e:
                #~ raise RuntimeError('%s: set_fields method arument error %s: %s' % (self.item_name, field_name, e))
#~
    #~ def add(self, **fields):
        #~ self.append()
        #~ self.set_fields(fields)
        #~ self.post()
#~
    #~ def change(self, **fields):
        #~ self.edit()
        #~ self.set_fields(fields)
        #~ self.post()

    def find_default_field(self):
        for field in self.fields:
            if field.is_default:
                return field

    default_field = property (find_default_field)

    def round(self, value, dec):
        return round(value, dec)

    def abort(self):
        raise AbortException

class MasterDataSet(AbstractDataSet):
    def __init__(self):
        AbstractDataSet.__init__(self)
        self.details_active = False

    def copy(self, filters=True, details=True, handlers=True):
        result = super(MasterDataSet, self).copy(filters, details, handlers)
        if details:
            for detail in self.details:
                copy_table = detail.copy(filters, details, handlers)
                copy_table.owner = result
                copy_table.master = result
                copy_table.expanded = detail.expanded
                result.details.append(copy_table)
                result.items.append(copy_table)
        return result

    def do_apply(self, params):
        pass

    def apply(self, params=None):
        result = None
        if self.on_before_apply:
            result = self.on_before_apply(self)
        if result != False:
            result = self.do_apply(params)
            if self.on_after_apply:
                self.on_after_apply(self)
        return result

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
        result.expanded = False
        result.is_delta = True
        for detail in result.details:
            detail.expanded = False
            detail.is_delta = True
        result.details_active = True
        result.change_log.set_changes(changes)
        result._records = result.change_log.records
        result.bind_fields(result.change_log.expanded)
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

    def do_after_scroll(self):
        super(MasterDataSet, self).do_after_scroll()
        if self.details_active:
            self.open_details()
        else:
            self.close_details()

    def set_read_only(self, value):
        super(MasterDataSet, self).set_read_only(value)
        for detail in self.details:
            detail.set_read_only(value)


class MasterDetailDataset(MasterDataSet):
    def __init__(self):
        MasterDataSet.__init__(self)
        self.master = None
        self.disabled = False

    def find_change_log(self):
        if self.master:
            if self.master.record_status != common.RECORD_UNCHANGED:
                return self.master.change_log.get_detail_log(str(self.ID))

    def open(self, expanded=None, fields=None, where=None, order_by=None, open_empty=False, params=None, offset=None):
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
                    if self.do_before_open(expanded, fields, where, order_by, open_empty, params) != False:
                        self.bind_fields(expanded)
                        self._records = records
                        self._active = True
                        self.item_state = common.STATE_BROWSE
                        self.first()
                        self.do_after_open()
                        self.update_controls(common.UPDATE_OPEN)
                else:
                    params['__owner_id'] = self.master.ID
                    params['__owner_rec_id'] = self.master.id.value
                    return super(MasterDetailDataset, self).open(expanded, fields, where, order_by, open_empty, params, offset)
            else:
                return
        else:
            return super(MasterDetailDataset, self).open(expanded, fields, where, order_by, open_empty, params, offset)

    def insert(self):
        if self.master and not self.master.is_changing():
            raise DatasetException, u"%s: can't insert record - master item is not in edit or insert mode" % self.owner.item_name
        super(MasterDetailDataset, self).insert()

    def append(self):
        if self.master and not self.master.is_changing():
            raise DatasetException, u"%s: can't append record - master item is not in edit or insert mode" % self.owner.item_name
        super(MasterDetailDataset, self).append()

    def edit(self):
        if self.master and not self.master.is_changing():
            raise DatasetException, u"%s: can't edit record - master item is not in edit or insert mode" % self.owner.item_name
        super(MasterDetailDataset, self).edit()

    def copy_rec(self):
        if self.master and not self.master.is_changing():
            raise DatasetException, u"%s: can't copy record - master item is not in edit or insert mode" % self.owner.item_name
        super(MasterDetailDataset, self).copy_rec()

    def delete(self):
        if self.master and not self.master.is_changing():
            raise DatasetException, u"%s: can't delete record - master item is not in edit or insert mode" % self.owner.item_name
        super(MasterDetailDataset, self).delete()

    def set_modified(self, value):
        self._modified = value
        if self.master and value:
            self.master.modified = value

    def get_modified(self):
        return super(MasterDetailDataset, self).get_modified()

    modified = property (get_modified, set_modified)

    def get_read_only(self):
        if self.master and self.parent_read_only:
            return self.master.read_only
        else:
            return super(MasterDetailDataset, self).get_read_only()

    def set_read_only(self, value):
        return super(MasterDetailDataset, self).set_read_only(value)

    read_only = property (get_read_only, set_read_only)

class Dataset(MasterDetailDataset):
    pass
