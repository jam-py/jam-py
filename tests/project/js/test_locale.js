var assert = chai.assert;

describe('Locale', function() {
    var locale;
    const float_params = [
            {decimal_point: '.', value: 123.123456, string: '123.123456'},
            {decimal_point: ',', value: 123.123456, string: '123,123456'}
        ];
        cur_param_names = [
            'MON_DECIMAL_POINT',
            'MON_THOUSANDS_SEP',
            'CURRENCY_SYMBOL',
            'FRAC_DIGITS',
            'P_CS_PRECEDES',
            'N_CS_PRECEDES',
            'P_SEP_BY_SPACE',
            'N_SEP_BY_SPACE',
            'POSITIVE_SIGN',
            'NEGATIVE_SIGN',
            'P_SIGN_POSN',
            'N_SIGN_POSN'
        ],
        cur_params = [
            [cur_param_names, ['.', '', '$',   '2', true, true, false, false, '', '-', 1, 1, 123456.12, '$123456.12']],
            [cur_param_names, ['.', '', '',    '2', true, true, false, false, '', '-', 1, 1, 123456.12, '123456.12']],
            [cur_param_names, ['.', '', 'RSD', '2', true, true, false, false, '', '-', 1, 1, 123456.12, 'RSD123456.12']],
            [cur_param_names, [',', '', '$',   '2', true, true, false, false, '', '-', 1, 1, 123456.12, '$123456,12']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '', '-', 1, 1, 123456.12, '$123,456.12']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '', '-', 1, 1, 123456789.12, '$123,456,789.12']],
            [cur_param_names, ['.', ',', '$',  '4', true, true, false, false, '', '-', 1, 1, 123456789.1234, '$123,456,789.1234']],

            [cur_param_names, ['.', ',', '$',  '2', true, true, true, false, '+', '-', 1, 1, 123456.12, '+$ 123,456.12']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, true, '+', '-', 1, 1, -123456.12, '-$ 123,456.12']],

            [cur_param_names, ['.', ',', '$',  '2', false, true, false, false, '+', '-', 1, 1, 123456.12, '+123,456.12$']],
            [cur_param_names, ['.', ',', '$',  '2', true, false, false, false, '+', '-', 1, 1, -123456.12, '-123,456.12$']],

            [cur_param_names, ['.', ',', '$',  '2', false, true, true, false, '+', '-', 1, 1, 123456.12, '+123,456.12 $']],
            [cur_param_names, ['.', ',', '$',  '2', true, false, false, true, '+', '-', 1, 1, -123456.12, '-123,456.12 $']],

            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 0, 1, 123456.12, '+($123,456.12)']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 1, 1, 123456.12, '+$123,456.12']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 2, 1, 123456.12, '$123,456.12+']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 3, 1, 123456.12, '$+123,456.12']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 4, 1, 123456.12, '$123,456.12+']],

            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 1, 0, -123456.12, '-($123,456.12)']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 1, 1, -123456.12, '-$123,456.12']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 1, 2, -123456.12, '$123,456.12-']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 1, 3, -123456.12, '$-123,456.12']],
            [cur_param_names, ['.', ',', '$',  '2', true, true, false, false, '+', '-', 1, 4, -123456.12, '$123,456.12-']]
        ];

    before(function() {
        locale = JSON.parse(JSON.stringify(task.locale));
    });

    after(function() {
        task.locale = JSON.parse(JSON.stringify(locale));
    });

    describe('float_to_str', function () {
        float_params.forEach(function(param) {
            it('decimal point ' + param.decimal_point + ' ' + param.value + ' ' + 'should be ' + param.string, function() {
                    task.locale.DECIMAL_POINT = param.decimal_point
                    assert.equal(task.float_to_str(param.value), param.string);
            });
        })
    });

    describe('str_to_float', function () {
        float_params.forEach(function(param) {
            it('decimal point ' + param.decimal_point + ' ' + param.string + ' ' + 'should be ' + param.value, function() {
                    task.locale.DECIMAL_POINT = param.decimal_point
                    assert.equal(task.str_to_float(param.string), param.value);
            });
        })
    });


    describe('cur_to_str', function () {
        cur_params.forEach(function(param) {
            var param_names = param[0],
                param_values = param[1],
                value = param_values[param_names.length],
                string = param_values[param_names.length + 1];
            it('cur_to_str ' + value + ' should be ' + string, function() {
                for (var i = 0; i < param_names.length; i++) {
                    task.locale[param_names[i]] = param_values[i]
                }
                assert.equal(task.cur_to_str(value), string);
            });
        })
    });

    describe('str_to_cur', function () {
        cur_params.forEach(function(param) {
            var param_names = param[0],
                param_values = param[1],
                value = param_values[param_names.length],
                string = param_values[param_names.length + 1];
            it('cur_to_str ' + string + ' should be ' + value, function() {
                for (var i = 0; i < param_names.length; i++) {
                    task.locale[param_names[i]] = param_values[i]
                }
                assert.equal(task.str_to_cur(string), value);
            });
        })
    });

});
