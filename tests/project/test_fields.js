var assert = chai.assert;

describe('Fields', function() {
    const date = new Date('2019-10-30T00:00:00'),
        date_string = '10/30/2019',
        date_time = new Date('2019-10-30T10:10:20'),
        datetime_string = '10/30/2019 10:10:20',
        file_full = 'img_1.jpg?img 1.jpg',
        file_secure = 'img_1.jpg',
        file_disp = 'img 1.jpg',
        field_names =
        [
            ('text_field'),
            ('integer_field'),
            ('float_field'),
            ('currency_field')
        ],
        empty_fields_data =
        [
//            field_name,        data,  value,    text, display_text
            ['text_field',       null,     '',      '',      ''],
            ['integer_field',    null,      0,      '',      ''],
            ['float_field',      null,      0,      '',      ''],
            ['currency_field',   null,      0,      '',      ''],
            ['date_field',       null,   null,      '',      ''],
            ['datetime_field',   null,   null,      '',      ''],
            ['boolean_field',    null,  false, 'FALSE', 'FALSE'],
            ['keys_field',       null,     [],      '',      ''],
            ['file_field',       null,   null,      '',      ''],
            ['image_field',      null,   null,      '',      '']
        ],
        fields_data =
        [
//           field_name,                      val,                 data,       value,            text,  lookup_value,     lookup_text,    display_text

            ['text_field',                  'abc',                'abc',       'abc',           'abc',         'abc',           'abc',           'abc'],
            ['text_field',                    123,                '123',       '123',           '123',         '123',           '123',           '123'],
            ['integer_field',                 123,                  123,         123,           '123',           123,           '123',           '123'],
            ['integer_field',                -123,                 -123,        -123,          '-123',          -123,          '-123',          '-123'],
            ['float_field',               123.123,              123.123,     123.123,       '123.123',       123.123,       '123.123',       '123.123'],
            ['currency_field',            123.123,               123.12,      123.12,        '123.12',        123.12,        '123.12',       '$123.12'],
            ['currency_field',              1.555,                 1.56,        1.56,          '1.56',          1.56,          '1.56',         '$1.56'],
            ['currency_field',             -1.005,                -1.01,       -1.01,         '-1.01',         -1.01,         '-1.01',        '-$1.01'],
            ['currency_field',        1000000.001,           1000000.00,  1000000.00,     '1000000.0',    1000000.00,     '1000000.0', '$1 000 000.00'],
            ['date_field',                   date,                 date,        date,     date_string,          date,     date_string,     date_string],
            ['datetime_field',          date_time,            date_time,   date_time, datetime_string,     date_time, datetime_string, datetime_string],
            ['boolean_field',               false,                    0,       false,         'FALSE',         false,         'FALSE',         'FALSE'],
            ['boolean_field',                true,                    1,        true,          'TRUE',          true,          'TRUE',          'TRUE'],
            ['keys_field',              [1, 2, 3],               '1;2;3',   [1, 2, 3],   'selected: 3',      [1, 2, 3],  'selected: 3',   'selected: 3'],
            ['image_field',             'img.jpg',             'img.jpg',   'img.jpg',       'img.jpg',     'img.jpg',       'img.jpg',       'img.jpg'],
            ['file_field',              'img.jpg',             'img.jpg',   'img.jpg',       'img.jpg',     'img.jpg',       'img.jpg',       'img.jpg'],
            ['file_field',  'img_1.jpg?img 1.jpg', 'img_1.jpg?img 1.jpg', 'img_1.jpg',     'img_1.jpg',    'img_1.jpg',     'img_1.jpg',    'img 1.jpg'],
            ['lookup_list_field',               1,                     1,           1,             '1',              1,             '1',        'item1'],

        ],
        lookup_params = [
            ['lookup3_text_field', 'text_field'],
            ['lookup3_integer_field', 'integer_field'],
            ['lookup3_date_field', 'date_field'],
            ['lookup3_datetime_field', 'datetime_field'],
            ['lookup3_currency_field', 'currency_field'],
            ['lookup3_boolean_field', 'boolean_field'],
            ['lookup3_keys_field', 'keys_field'],
            ['lookup3_image_field', 'image_field'],
            ['lookup3_file_field', 'file_field'],
            ['lookup3_lookup_list_field', 'lookup_list_field']
        ];


    before(function() {
        task.server('prepare_field_items');
        let lookup3 = task.lookup3.copy();
        lookup3.open({open_empty: true});
        for (let i = 0; i < 2; i++) {
            let val = i + 1;
            lookup3.append();
            lookup3.text_field.value = 'lookup3_text' + val;
            lookup3.integer_field.value = val;
            lookup3.currency_field.value = 100.001;
            lookup3.date_field.value = date;
            lookup3.datetime_field.value = date_time;
            lookup3.boolean_field.value = Boolean(i);
            lookup3.lookup_list_field.value = val;
            lookup3.keys_field.value = [val, val+1];
            lookup3.image_field.value = 'img' + val + '.jpeg';
            lookup3.file_field.value = 'img_' + val + '.jpg?img ' + val + '.jpg';
            lookup3.post();
        }
        lookup3.apply();
        lookup3.first();

        let lookup2 = task.lookup2.copy();
        lookup2.open({open_empty: true})
        for (let i = 0; i < 2; i++) {
            lookup2.append();
            lookup2.name.value = 'lookup2_text' + (i + 1);
            lookup3.rec_no = i;
            lookup2.lookup3_text_field.value = lookup3.id.value;
            lookup2.post()
        }
        lookup2.apply();
        lookup2.open();

        let lookup1 = task.lookup1.copy();
        lookup1.open({open_empty: true});
        for (let i = 0; i < 2; i++) {
            lookup1.append();
            lookup1.name.value = 'lookup1_name' + (i + 1);
            lookup2.rec_no = i;
            lookup1.lookup_field2.value = lookup2.id.value;
            lookup1.post();
        }
        lookup1.apply();
        lookup1.last(); //!!!!!!!!!!!!!

        let item = task.item.copy();
        item.open();
        item.append();
        item.lookup1_name_field.value = lookup1.id.value;
        item.lookup_list_field.value = 1;
        item.post();
        item.apply();
    });

    describe('test_fields_item', function () {
        it('Testing fields item', function() {
            let item = task.item.copy();
            item.open();
            assert.equal(item.rec_count, 1)
        });
    });

    describe('test_field_by_name', function () {
        field_names.forEach(function(field_name) {
            it('Testing field_by_name for field_name "' + field_name + '"', function() {
                let item = task.item.copy()
                item.open()
                let field = item.field_by_name(field_name);
                assert.equal(field.field_name, field_name);
            });
        })
    });

    describe('test_null_field', function () {
        empty_fields_data.forEach(function(field_data) {
            it('Testing null data for field "' + field_data[0] + '"', function() {
                let item = task.item.copy(),
                    field_name = field_data[0];
                    field = item.field_by_name(field_name);
                item.open()
                assert.equal(field.field_name, field_name);
                assert.equal(field.data, field_data[1]);
                assert.deepEqual(field.value, field_data[2]);
                assert.equal(field.text, field_data[3]);
                assert.equal(field.lookup_data, null);
                assert.deepEqual(field.lookup_value, field.value);
                assert.equal(field.lookup_text, field.text);
                assert.equal(field.display_text, field_data[4]);

            });
        })
    });

    describe('test_field', function () {
        fields_data.forEach(function(field_data) {
            it('Testing field "' + field_data[0] + '"', function() {
                let item = task.item.copy(),
                    field_name = field_data[0],
                    val = field_data[1],
                    data = field_data[2],
                    value = field_data[3],
                    text = field_data[4],
                    lookup_value = field_data[5],
                    lookup_text = field_data[6],
                    display_text = field_data[7],
                    field = item.field_by_name(field_name);
                item.open();
                item.edit();
                field.value = val;
                item.post();

                //~ assert.equal(field.data, data);
                assert.deepEqual(field.value, value);
                assert.equal(field.text, text);
                assert.equal(field.lookup_data, null);
                assert.deepEqual(field.lookup_value, lookup_value);
                assert.equal(field.lookup_text, lookup_text);
                assert.equal(field.display_text, display_text);

                item.apply()
                item.open()

                //~ assert.equal(field.data, data);
                assert.deepEqual(field.value, value);
                assert.equal(field.text, text);
                assert.equal(field.lookup_data, null);
                assert.deepEqual(field.lookup_value, lookup_value);
                assert.equal(field.lookup_text, lookup_text);
                assert.equal(field.display_text, display_text);
            });
        })
    });

    describe('test_lookup2_lookup_field', function () {
        lookup_params.forEach(function(field_data) {
            it('Testing lookup2 lookup field "' + field_data[0] + '"', function() {
                let lookup2 = task.lookup2.copy(),
                    lookup3 = task.lookup3.copy(),
                    field2,
                    field3;
                lookup2.open();
                field2 = lookup2.field_by_name(field_data[0]);
                lookup3.open();
                field3 = lookup3.field_by_name(field_data[1]);

                assert.equal(field2.value, lookup3.id.value);
                assert.equal(field2.text, lookup3.id.text);
                assert.deepEqual(field2.lookup_value, field3.value);
                assert.equal(field2.lookup_text, field3.text);
                assert.equal(field2.display_text, field3.display_text);
            });
        })
    });

    describe('test_lookup2_lookup_field_not_expanded', function () {
        lookup_params.forEach(function(field_data) {
            it('Testing lookup2 not expanded lookup field "' + field_data[0] + '"', function() {
                let lookup2 = task.lookup2.copy(),
                    lookup3 = task.lookup3.copy(),
                    field2,
                    field3;
                lookup2.open({expanded: false});
                field2 = lookup2.field_by_name(field_data[0]);
                lookup3.open();
                field3 = lookup3.field_by_name(field_data[1]);

                assert.equal(field2.value, lookup3.id.value);
                assert.equal(field2.text, lookup3.id.text);
                assert.equal(field2.lookup_value, lookup3.id.value);
                assert.equal(field2.lookup_text, lookup3.id.text);
                assert.equal(field2.display_text, lookup3.id.text);
            });
        })
    });

    describe('test_lookup2_lookup_field', function () {
        lookup_params.forEach(function(field_data) {
            it('Testing item lookup field "' + field_data[0] + '"', function() {
                let item = task.item.copy(),
                    lookup3 = task.lookup3.copy(),
                    field,
                    field3;
                item.open();
                field = item.field_by_name(field_data[0]);
                lookup3.open();
                lookup3.last(); //!!!!!!!!
                field3 = lookup3.field_by_name(field_data[1]);

                assert.equal(field.value, lookup3.id.value);
                assert.equal(field.text, lookup3.id.text);
                assert.deepEqual(field.lookup_value, field3.value);
                assert.equal(field.lookup_text, field3.text);
                assert.equal(field.display_text, field3.display_text);
            });
        })
    });

});

