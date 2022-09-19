import sys


_default_encoding = sys.getdefaultencoding()


def to_bytes(x, charset=_default_encoding, errors="strict"):
    if x is None:
        return None

    if isinstance(x, (bytes, bytearray, memoryview)):
        return bytes(x)

    if isinstance(x, str):
        return x.encode(charset, errors)

    raise TypeError("Expected bytes")


def to_native(x, charset=_default_encoding, errors="strict"):
    if x is None or isinstance(x, str):
        return x

    return x.decode(charset, errors)
