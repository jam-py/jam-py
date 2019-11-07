import datetime
import pytest

class TestFields:

    def text_fields_item(self, task, fields_item):
        item = task.item.copy()
        item.open()
        assert item.rec_count == 1
        for field in item.fields:
            assert field.data == None

    @pytest.mark.parametrize(('field_name'),
        [
            ('text_field'),
            ('integer_field'),
            ('float_field'),
            ('currency_field')
        ]
    )
    def test_field_by_name(self, task, fields_item, field_name):
        item = task.item.copy()
        item.open()
        field = item.field_by_name(field_name)
        assert field.field_name == field_name

    @pytest.mark.parametrize(('field_name, data, value, text, display_text'),
        [
#             field_name,        data,  value,    text, display_text

            ('text_field',       None,     '',      '',      ''),
            ('integer_field',    None,      0,      '',      ''),
            ('float_field',      None,      0,      '',      ''),
            ('currency_field',   None,      0,      '',      ''),
            ('date_field',       None,   None,      '',      ''),
            ('datetime_field',   None,   None,      '',      ''),
            ('boolean_field',    None,  False, 'FALSE', 'FALSE'),
            ('keys_field',       None,     [],      '',      ''),
            ('file_field',       None,   None,      '',      ''),
            ('image_field',      None,   None,      '',      ''),
        ]
    )
    def test_none_field(self, task, field_name, data, value, text, display_text):
        item = task.item.copy()
        item.open()
        field = item.field_by_name(field_name)

        assert field.data == data
        assert field.value == value
        assert field.text == text
        assert field.lookup_data == None
        assert field.lookup_value == None
        assert field.lookup_text == ''
        assert field.display_text == display_text

    date = datetime.datetime.strptime('2019-10-30', '%Y-%m-%d').date()
    date_string = '10/30/2019'
    datetime = datetime.datetime.strptime('2019-10-30 10:10:20', '%Y-%m-%d %H:%M:%S')
    datetime_string = '10/30/2019 10:10:20'
    @pytest.mark.parametrize(('field_name, val, data, value, text, display_text'),
        [
#            field_name,               val,        data,      value,            text,    display_text

            ('text_field',           'abc',       'abc',      'abc',           'abc',           'abc'),
            ('text_field',             123,       '123',      '123',           '123',           '123'),
            ('integer_field',          123,         123,        123,           '123',           '123'),
            ('integer_field',         -123,        -123,       -123,          '-123',          '-123'),
            ('float_field',        123.123,     123.123,    123.123,       '123.123',       '123.123'),
            ('currency_field',     123.123,      123.12,     123.12,        '123.12',       '$123.12'),
            ('currency_field',       1.555,        1.56,       1.56,          '1.56',         '$1.56'),
            ('currency_field',      -1.005,       -1.01,      -1.01,         '-1.01',        '-$1.01'),
            ('currency_field', 1000000.001,  1000000.00, 1000000.00,     '1000000.0', '$1 000 000.00'),
            ('date_field',            date,        date,       date,     date_string,     date_string),
            ('datetime_field',    datetime,    datetime,   datetime, datetime_string, datetime_string),
            ('boolean_field',        False,           0,      False,         'FALSE',         'FALSE'),
            ('boolean_field',         True,           1,       True,          'TRUE',          'TRUE'),
        ]
    )
    def test_field(self, task, val, field_name, data, value, text, display_text):
        item = task.item.copy()
        item.open()
        field = item.field_by_name(field_name)

        item.edit()
        field.value = val
        item.post()

        assert field.data == data
        assert field.value == value
        assert field.text == text
        assert field.lookup_data == None
        assert field.lookup_value == None
        assert field.lookup_text == ''
        assert field.display_text == display_text

        item.apply()
        item.open()
        assert field.data == data
        assert field.value == value
        assert field.text == text
        assert field.lookup_data == None
        assert field.lookup_value == None
        assert field.lookup_text == ''
        assert field.display_text == display_text

    def test_lookup_field(self, task):
        date = datetime.datetime.strptime('2019-10-30', '%Y-%m-%d').date()
        date_string = '10/30/2019'

        lookup3 = task.lookup3.copy()
        lookup3.empty()
        lookup3.open(open_empty=True)
        for i in range(2):
            lookup3.append()
            lookup3.name.value = 'lookup3_name' + str(i + 1)
            lookup3.val.value = i + 1;
            lookup3.date_val.value = date
            lookup3.post()
        lookup3.apply()
        lookup3.first()
        assert lookup3.rec_count == 2

        lookup2 = task.lookup2.copy()
        lookup2.empty()
        lookup2.open(open_empty=True)
        for i in range(2):
            lookup2.append()
            lookup2.name.value = 'lookup2_name' + str(i + 1)
            lookup2.val.value = i + 1;
            lookup3.rec_no = i
            lookup2.lookup_field3.value = lookup3.id.value
            lookup2.post()
        lookup2.apply()
        lookup2.first()
        assert lookup2.rec_count == 2

        lookup1 = task.lookup1.copy()
        lookup1.empty()
        lookup1.open(open_empty=True)
        for i in range(2):
            lookup1.append()
            lookup1.name.value = 'lookup1_name' + str(i + 1)
            lookup1.val.value = i + 1
            lookup2.rec_no = i
            lookup1.lookup_field2.value = lookup2.id.value
            lookup1.post()
        lookup1.apply()
        lookup1.first()

        assert lookup2.rec_count == 2
        item = task.item.copy()
        item.open()
        item.edit()
        item.lookup1_field.value = lookup1.id.value
        item.post()
        item.apply()
        item.open()
        assert item.lookup1_field.data == lookup1.id.value
        assert item.lookup1_field.value == lookup1.id.value
        assert item.lookup1_field.text == str(lookup1.id.value)
        assert item.lookup1_field.lookup_value == 'lookup1_name' + str(lookup1.val.value)

        assert item.lookup4_field.data == lookup1.id.value
        assert item.lookup4_field.value == lookup1.id.value
        assert item.lookup4_field.text == str(lookup1.id.value)
        assert item.lookup4_field.lookup_value == date
        assert item.lookup4_field.lookup_text == date_string
        assert item.lookup4_field.display_text == date_string
