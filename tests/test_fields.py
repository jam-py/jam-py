import datetime
import pytest

class TestFields:

    lookup_params = [
        ('lookup3_text_field', 'text_field'),
        ('lookup3_integer_field', 'integer_field'),
        ('lookup3_date_field', 'date_field'),
        ('lookup3_datetime_field', 'datetime_field'),
        ('lookup3_currency_field', 'currency_field'),
        ('lookup3_boolean_field', 'boolean_field'),
        ('lookup3_keys_field', 'keys_field'),
        ('lookup3_image_field', 'image_field'),
        ('lookup3_file_field', 'file_field'),
        ('lookup3_lookup_list_field', 'lookup_list_field')
    ]

    def test_fields_item(self, task, fields_item):
        item = task.item.copy()
        item.open()
        assert item.rec_count == 1

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
    def test_none_field(self, task, fields_item, field_name, data, value, text, display_text):
        item = task.item.copy()
        item.open()
        field = item.field_by_name(field_name)

        assert field.data == data
        assert field.value == value
        assert field.text == text
        assert field.lookup_data == None
        assert field.lookup_value == field.value
        assert field.lookup_text == field.text
        assert field.display_text == display_text

    date = datetime.datetime.strptime('2019-10-30', '%Y-%m-%d').date()
    date_string = '10/30/2019'
    date_time = datetime.datetime.strptime('2019-10-30 10:10:20', '%Y-%m-%d %H:%M:%S')
    datetime_string = '10/30/2019 10:10:20'
    @pytest.mark.parametrize(('field_name, val, data, value, text, lookup_value, lookup_text, display_text'),
        [
#            field_name,                      val,                 data,       value,            text,  lookup_value,     lookup_text,    display_text

            ('text_field',                  'abc',                'abc',       'abc',           'abc',         'abc',           'abc',           'abc'),
            ('text_field',                    123,                '123',       '123',           '123',         '123',           '123',           '123'),
            ('integer_field',                 123,                  123,         123,           '123',           123,           '123',           '123'),
            ('integer_field',                -123,                 -123,        -123,          '-123',          -123,          '-123',          '-123'),
            ('float_field',               123.123,              123.123,     123.123,       '123.123',       123.123,       '123.123',       '123.123'),
            ('currency_field',            123.123,               123.12,      123.12,        '123.12',        123.12,        '123.12',       '$123.12'),
            ('currency_field',              1.555,                 1.56,        1.56,          '1.56',          1.56,          '1.56',         '$1.56'),
            ('currency_field',             -1.005,                -1.01,       -1.01,         '-1.01',         -1.01,         '-1.01',        '-$1.01'),
            ('currency_field',        1000000.001,           1000000.00,  1000000.00,     '1000000.0',    1000000.00,     '1000000.0', '$1 000 000.00'),
            ('date_field',                   date,                 date,        date,     date_string,          date,     date_string,     date_string),
            ('datetime_field',          date_time,            date_time,   date_time, datetime_string,     date_time, datetime_string, datetime_string),
            ('boolean_field',               False,                    0,       False,         'FALSE',         False,         'FALSE',         'FALSE'),
            ('boolean_field',                True,                    1,        True,          'TRUE',          True,          'TRUE',          'TRUE'),
            ('keys_field',              [1, 2, 3],               '1;2;3',   [1, 2, 3],   'selected: 3',      [1, 2, 3],  'selected: 3',   'selected: 3'),
            ('image_field',             'img.jpg',             'img.jpg',   'img.jpg',       'img.jpg',     'img.jpg',       'img.jpg',       'img.jpg'),
            ('file_field',              'img.jpg',             'img.jpg',   'img.jpg',       'img.jpg',     'img.jpg',       'img.jpg',       'img.jpg'),
            ('file_field',  'img_1.jpg?img 1.jpg', 'img_1.jpg?img 1.jpg', 'img_1.jpg',     'img_1.jpg',    'img_1.jpg',     'img_1.jpg',    'img 1.jpg'),
            ('lookup_list_field',               1,                     1,           1,             '1',              1,             '1',        'item1'),
        ]
    )
    def test_field(self, task, fields_item, val, field_name, data, value, text, lookup_value, lookup_text, display_text):
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
        assert field.lookup_value == lookup_value
        assert field.lookup_text == lookup_text
        assert field.display_text == display_text

        item.apply()
        item.open()

        assert field.data == data
        assert field.value == value
        assert field.text == text
        assert field.lookup_data == None
        assert field.lookup_value == lookup_value
        assert field.lookup_text == lookup_text
        assert field.display_text == display_text

    def test_lookup_list_field(self, task, fields_item):
        pass

    @pytest.mark.parametrize(('lookup2_field_name, lookup3_field_name'), lookup_params)
    def test_lookup2_lookup_field(self, task, fields_item, lookup2_field_name, lookup3_field_name):
        lookup2 = task.lookup2.copy()
        lookup2.open()
        field2 = lookup2.field_by_name(lookup2_field_name)
        lookup3 = task.lookup3.copy()
        lookup3.open()
        field3 = lookup3.field_by_name(lookup3_field_name)

        assert field2.value == lookup3.id.value
        assert field2.text == lookup3.id.text
        assert field2.lookup_value == field3.value
        assert field2.lookup_text == field3.text
        assert field2.display_text == field3.display_text

    @pytest.mark.parametrize(('lookup2_field_name, lookup3_field_name'), lookup_params)
    def test_lookup2_lookup_field_not_expanded(self, task, fields_item, lookup2_field_name, lookup3_field_name):
        lookup2 = task.lookup2.copy()
        lookup2.open(expanded = False)
        field2 = lookup2.field_by_name(lookup2_field_name)
        lookup3 = task.lookup3.copy()
        lookup3.open()

        assert field2.value == lookup3.id.value
        assert field2.text == lookup3.id.text
        assert field2.lookup_value == lookup3.id.value
        assert field2.lookup_text == lookup3.id.text
        assert field2.display_text == lookup3.id.text

    @pytest.mark.parametrize(('item_field_name, lookup3_field_name'), lookup_params)
    def test_item_lookup_field(self, task, fields_item, item_field_name, lookup3_field_name):
        item = task.item.copy()
        item.open()
        field = item.field_by_name(item_field_name)
        lookup3 = task.lookup3.copy()
        lookup3.open()
        lookup3.last()
        field3 = lookup3.field_by_name(lookup3_field_name)

        assert field.value == lookup3.id.value
        assert field.text == lookup3.id.text
        assert field.lookup_value == field3.value
        assert field.lookup_text == field3.text
        assert field.display_text == field3.display_text
