import pytest
from jam.common import consts

class TestConsts(object):

    float_param_names = 'decimal_point, value, string'
    float_param_values = [
            ('.', 123.123456, '123.123456'),
            (',', 123.123456, '123,123456'),
        ]

    cur_param_names = """
        mon_decimal_point,
        mon_thousands_sep,
        currency_symbol,
        frac_digits,
        p_cs_precedes,
        n_cs_precedes,
        p_sep_by_space,
        n_sep_by_space,
        positive_sign,
        negative_sign,
        p_sign_posn,
        n_sign_posn,
        value,
        string
    """
    cur_param_values = [
        ('.', '', '$',   '2', True, True, False, False, '', '-', 1, 1, 123456.12, '$123456.12'),
        ('.', '', '',    '2', True, True, False, False, '', '-', 1, 1, 123456.12, '123456.12'),
        ('.', '', 'RSD', '2', True, True, False, False, '', '-', 1, 1, 123456.12, 'RSD123456.12'),
        (',', '', '$',   '2', True, True, False, False, '', '-', 1, 1, 123456.12, '$123456,12'),
        ('.', ',', '$',  '2', True, True, False, False, '', '-', 1, 1, 123456.12, '$123,456.12'),
        ('.', ',', '$',  '2', True, True, False, False, '', '-', 1, 1, 123456789.12, '$123,456,789.12'),
        ('.', ',', '$',  '4', True, True, False, False, '', '-', 1, 1, 123456789.1234, '$123,456,789.1234'),

        ('.', ',', '$',  '2', True, True, True, False, '+', '-', 1, 1, 123456.12, '+$ 123,456.12'),
        ('.', ',', '$',  '2', True, True, False, True, '+', '-', 1, 1, -123456.12, '-$ 123,456.12'),

        ('.', ',', '$',  '2', False, True, False, False, '+', '-', 1, 1, 123456.12, '+123,456.12$'),
        ('.', ',', '$',  '2', True, False, False, False, '+', '-', 1, 1, -123456.12, '-123,456.12$'),

        ('.', ',', '$',  '2', False, True, True, False, '+', '-', 1, 1, 123456.12, '+123,456.12 $'),
        ('.', ',', '$',  '2', True, False, False, True, '+', '-', 1, 1, -123456.12, '-123,456.12 $'),

        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 0, 1, 123456.12, '+($123,456.12)'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 1, 1, 123456.12, '+$123,456.12'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 2, 1, 123456.12, '$123,456.12+'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 3, 1, 123456.12, '$+123,456.12'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 4, 1, 123456.12, '$123,456.12+'),

        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 1, 0, -123456.12, '-($123,456.12)'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 1, 1, -123456.12, '-$123,456.12'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 1, 2, -123456.12, '$123,456.12-'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 1, 3, -123456.12, '$-123,456.12'),
        ('.', ',', '$',  '2', True, True, False, False, '+', '-', 1, 4, -123456.12, '$123,456.12-'),
    ]

    @classmethod
    def teardown_class(cls):
        consts.read_language()

    @pytest.mark.parametrize(('point'), [(',',), ('.',)])
    def test_locale(self, point):
        consts.locale['DECIMAL_POINT'] = point
        assert consts.DECIMAL_POINT == point

    @pytest.mark.parametrize(float_param_names, float_param_values)
    def test_float_to_str(self, decimal_point, value, string):
        consts.DECIMAL_POINT = decimal_point
        assert consts.float_to_str(value) == string

    @pytest.mark.parametrize(float_param_names, float_param_values)
    def test_str_to_float(self, decimal_point, value, string):
        consts.DECIMAL_POINT = decimal_point
        assert consts.str_to_float(string) == value

    @pytest.mark.parametrize(cur_param_names, cur_param_values)
    def test_cur_to_string(
        self,
        mon_decimal_point,
        mon_thousands_sep,
        currency_symbol,
        frac_digits,
        p_cs_precedes,
        n_cs_precedes,
        p_sep_by_space,
        n_sep_by_space,
        positive_sign,
        negative_sign,
        p_sign_posn,
        n_sign_posn,
        value,
        string
    ):
        consts.MON_DECIMAL_POINT = mon_decimal_point
        consts.MON_THOUSANDS_SEP = mon_thousands_sep
        consts.CURRENCY_SYMBOL = currency_symbol
        consts.FRAC_DIGITS = frac_digits
        consts.P_CS_PRECEDES = p_cs_precedes
        consts.N_CS_PRECEDES = n_cs_precedes
        consts.P_SEP_BY_SPACE = p_sep_by_space
        consts.N_SEP_BY_SPACE = n_sep_by_space
        consts.POSITIVE_SIGN = positive_sign
        consts.NEGATIVE_SIGN = negative_sign
        consts.P_SIGN_POSN = p_sign_posn
        consts.N_SIGN_POSN = n_sign_posn

        assert consts.cur_to_str(value) == string

    @pytest.mark.parametrize(cur_param_names, cur_param_values)
    def test_str_to_cur(
        self,
        mon_decimal_point,
        mon_thousands_sep,
        currency_symbol,
        frac_digits,
        p_cs_precedes,
        n_cs_precedes,
        p_sep_by_space,
        n_sep_by_space,
        positive_sign,
        negative_sign,
        p_sign_posn,
        n_sign_posn,
        value,
        string
    ):
        consts.MON_DECIMAL_POINT = mon_decimal_point
        consts.MON_THOUSANDS_SEP = mon_thousands_sep
        consts.CURRENCY_SYMBOL = currency_symbol
        consts.FRAC_DIGITS = frac_digits
        consts.P_CS_PRECEDES = p_cs_precedes
        consts.N_CS_PRECEDES = n_cs_precedes
        consts.P_SEP_BY_SPACE = p_sep_by_space
        consts.N_SEP_BY_SPACE = n_sep_by_space
        consts.POSITIVE_SIGN = positive_sign
        consts.NEGATIVE_SIGN = negative_sign
        consts.P_SIGN_POSN = p_sign_posn
        consts.N_SIGN_POSN = n_sign_posn

        assert consts.str_to_cur(string) == value

    @pytest.mark.parametrize(('decimal_digits, value, result'),
        [
            (2, 1.555, 1.56),
            (2, 1.005, 1.01)
        ]
    )
    def test_round(self, decimal_digits, value, result):
        assert consts.round(value, decimal_digits) == result
