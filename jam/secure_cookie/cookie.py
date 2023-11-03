"""
Secure Cookies
==============

A signed cookie that is not alterable from the client because it adds a
checksum that the server validates. If you don't store a lot of data in
the session, you can use a secure cookie and not need to set up storage
on the server.

Keep in mind that the data is still readable from the client, only not
writable. It is signed, not encrypted. Do not store data in a cookie you
don't want the user to see.

.. code-block:: python

    from secure_cookie.cookie import SecureCookie
    x = SecureCookie({"foo": 42, "baz": (1, 2, 3)}, "deadbeef")

Dumping into a string so that one can store it in a cookie:

.. code-block:: python

    value = x.serialize()

Loading from that string again:

.. code-block:: python

    x = SecureCookie.unserialize(value, "deadbeef")
    assert x["baz"] == (1, 2, 3)

If someone modifies the cookie and the checksum is wrong the
``unserialize`` method will fail silently and return a new empty
:class:`SecureCookie` object.


Application Integration
-----------------------

If you are using the Werkzeug ``Request`` object you could integrate a
secure cookie into your application like this:

.. code-block:: python

    from secure_cookie.cookie import SecureCookie
    from werkzeug.utils import cached_property
    from werkzeug.wrappers import Response
    from werkzeug.wrappers import Request

    # Don't use this key but a different one; you could use
    # os.urandom(16) to get some random bytes.
    SECRET_KEY = b"\xfa\xdd\xb8z\xae\xe0}4\x8b\xea"

    class SessionRequest(Request):
        @cached_property
        def session(self):
            data = self.cookies.get("session")

            if not data:
                return SecureCookie(secret_key=SECRET_KEY)

            return SecureCookie.unserialize(data, SECRET_KEY)

    @SessionRequest.application
    def application(request):
        response = Response(do_stuff(request))

        if request.client_session.should_save:
            response.set_cookie(
                key="session",
                value=request.client_session.serialize(),
                httponly=True,
            )

        return response

A less verbose integration can be achieved by using shorthand methods:

.. code-block:: python

    class SessionRequest(Request):
        @cached_property
        def session(self):
            return SecureCookie.load_cookie(self, secret_key=COOKIE_SECRET)

    @SessionRequest.application
    def application(request):
        response = Response(do_stuff(request))
        request.client_session.save_cookie(response)
        return response


API
---

.. autoclass:: SecureCookie
    :members:

.. autoexception:: UnquoteError
"""
import base64
import json as _json
from datetime import datetime
from hashlib import sha1 as _default_hash
from hmac import compare_digest
from hmac import new as hmac
from numbers import Number
from time import time

# ~ from werkzeug.urls import url_quote_plus
# ~ from werkzeug.urls import url_unquote_plus
from urllib.parse import quote_plus as url_quote_plus
from urllib.parse import unquote_plus as url_unquote_plus

from ._compat import to_bytes
from ._compat import to_native
from .session import ModificationTrackingDict

_epoch_ord = datetime(1970, 1, 1).toordinal()


def _date_to_unix(arg):
    """Converts a timetuple, integer, or datetime object into the
    seconds from epoch in UTC.
    """
    if isinstance(arg, datetime):
        arg = arg.utctimetuple()
    elif isinstance(arg, Number):
        return int(arg)

    year, month, day, hour, minute, second = arg[:6]
    days = datetime(year, month, 1).toordinal() - _epoch_ord + day - 1
    hours = days * 24 + hour
    minutes = hours * 60 + minute
    seconds = minutes * 60 + second
    return seconds


class _JSONModule(object):
    @classmethod
    def dumps(cls, obj, **kw):
        kw.setdefault("separators", (",", ":"))
        kw.setdefault("sort_keys", True)
        return _json.dumps(obj, **kw)

    @staticmethod
    def loads(s, **kw):
        return _json.loads(s, **kw)


class UnquoteError(Exception):
    """Internal exception used to signal failures on quoting."""


class SecureCookie(ModificationTrackingDict):
    """Represents a secure cookie. You can subclass this class and
    provide an alternative mac method. The import thing is that the mac
    method is a function with a similar interface to the hashlib.
    Required methods are :meth:`update` and :meth:`digest`.

    .. code-block:: python

        x = SecureCookie({"foo": 42, "baz": (1, 2, 3)}, "deadbeef")
        assert x["foo"] == 42
        assert x["baz"] == (1, 2, 3)
        x["blafasel"] = 23
        assert x.should_save is True

    :param data: The initial data. Either a dict, list of tuples, or
        ``None``.
    :param secret_key: The secret key. If ``None`` or not specified it
        has to be set before :meth:`serialize` is called.
    :param new: The initial value of the ``new`` flag.

    .. versionchanged:: 0.1.0
        The default serialization method is ``json`` instead of
        ``pickle``. To upgrade existing tokens, override unquote to try
        ``pickle`` if ``json`` fails.
    """

    #: The hash method to use. This has to be a module with a new
    #: function or a function that creates a hashlib object, such as
    #: func:`hashlib.md5`. Subclasses can override this attribute. The
    #: default hash is sha1. Make sure to wrap this in
    #: :func:`staticmethod` if you store an arbitrary function there
    #: such as :func:`hashlib.sha1` which might be implemented as a
    #: function.
    hash_method = staticmethod(_default_hash)

    #: The module used for serialization. Should have a ``dumps`` and a
    #: ``loads`` method that takes bytes. The default is :mod:`json`.
    #:
    #: .. versionchanged:: 0.1.0
    #:     Use ``json`` instead of ``pickle``.
    serialization_method = _JSONModule

    #: If the contents should be base64 quoted. This can be disabled if
    #: the serialization process returns cookie safe strings only.
    quote_base64 = True

    def __init__(self, data=None, secret_key=None, new=True):
        super(SecureCookie, self).__init__(data or ())

        if secret_key is not None:
            secret_key = to_bytes(secret_key, "utf-8")

        self.secret_key = secret_key
        self.new = new

    def __repr__(self):
        return "<{} {}{}>".format(
            self.__class__.__name__,
            dict.__repr__(self),
            "*" if self.should_save else "",
        )

    @property
    def should_save(self):
        """True if the session should be saved. By default this is only
        true for :attr:`modified` cookies, not :attr:`new`.
        """
        return self.modified

    @classmethod
    def quote(cls, value):
        """Quote the value for the cookie. This can be any object
        supported by :attr:`serialization_method`.

        :param value: The value to quote.
        """
        if cls.serialization_method is not None:
            value = cls.serialization_method.dumps(value)

        if cls.quote_base64:
            value = b"".join(
                base64.b64encode(to_bytes(value, "utf8")).splitlines()
            ).strip()

        return value

    @classmethod
    def unquote(cls, value):
        """Unquote the value for the cookie. If unquoting does not work
        a :exc:`UnquoteError` is raised.

        :param value: The value to unquote.
        """
        try:
            if cls.quote_base64:
                value = base64.b64decode(value)

            if cls.serialization_method is not None:
                value = cls.serialization_method.loads(value)

            return value
        except Exception as exc:
            # Unfortunately serialization modules can cause pretty much
            # every error here. If we get one we catch it and convert it
            # into an UnquoteError.
            raise UnquoteError() from exc

    def serialize(self, expires=None):
        """Serialize the secure cookie into a string.

        If expires is provided, the session will be automatically
        invalidated after expiration when you unserialize it. This
        provides better protection against session cookie theft.

        :param expires: An optional expiration date for the cookie (a
            :class:`datetime.datetime` object).
        """
        if self.secret_key is None:
            raise RuntimeError("no secret key defined")

        if expires:
            self["_expires"] = _date_to_unix(expires)

        result = []
        mac = hmac(self.secret_key, None, self.hash_method)

        for key, value in sorted(self.items()):
            result.append(
                (
                    "{}={}".format(
                        url_quote_plus(key), self.quote(value).decode("ascii")
                    )
                ).encode("ascii")
            )
            mac.update(b"|" + result[-1])

        return b"?".join([base64.b64encode(mac.digest()).strip(), b"&".join(result)]).decode()

    @classmethod
    def unserialize(cls, string, secret_key):
        """Load the secure cookie from a serialized string.

        :param string: The cookie value to unserialize.
        :param secret_key: The secret key used to serialize the cookie.
        :return: A new :class:`SecureCookie`.
        """
        if isinstance(string, str):
            string = string.encode("utf-8", "replace")

        if isinstance(secret_key, str):
            secret_key = secret_key.encode("utf-8", "replace")

        try:
            base64_hash, data = string.split(b"?", 1)
        except (ValueError, IndexError):
            items = ()
        else:
            items = {}
            mac = hmac(secret_key, None, cls.hash_method)

            for item in data.split(b"&"):
                mac.update(b"|" + item)

                if b"=" not in item:
                    items = None
                    break

                key, value = item.split(b"=", 1)
                # try to make the key a string
                key = url_unquote_plus(key.decode("ascii"))

                try:
                    key = to_native(key)
                except UnicodeError:
                    pass

                items[key] = value

            # no parsing error and the mac looks okay, we can now
            # load the cookie.
            try:
                client_hash = base64.b64decode(base64_hash)
            except TypeError:
                items = client_hash = None

            if items is not None and compare_digest(client_hash, mac.digest()):
                try:
                    for key, value in items.items():
                        items[key] = cls.unquote(value)
                except UnquoteError:
                    items = ()
                else:
                    if "_expires" in items:
                        if time() > items["_expires"]:
                            items = ()
                        else:
                            del items["_expires"]
            else:
                items = ()
        return cls(items, secret_key, False)

    @classmethod
    def load_cookie(cls, request, key="session", secret_key=None):
        """Load a :class:`SecureCookie` from a cookie in the request. If
        the cookie is not set, a new :class:`SecureCookie` instance is
        returned.

        :param request: A request object that has a ``cookies``
            attribute which is a dict of all cookie values.
        :param key: The name of the cookie.
        :param secret_key: The secret key used to unquote the cookie.
            Always provide the value even though it has no default!
        """
        data = request.cookies.get(key)

        if not data:
            return cls(secret_key=secret_key)

        return cls.unserialize(data, secret_key)

    def save_cookie(
        self,
        response,
        key="session",
        expires=None,
        session_expires=None,
        max_age=None,
        path="/",
        domain=None,
        secure=None,
        httponly=False,
        force=False,
    ):
        """Save the data securely in a cookie on response object. All
        parameters that are not described here are forwarded directly
        to ``set_cookie``.

        :param response: A response object that has a ``set_cookie``
            method.
        :param key: The name of the cookie.
        :param session_expires: The expiration date of the secure cookie
            stored information. If this is not provided the cookie
            ``expires`` date is used instead.
        """
        if force or self.should_save:
            data = self.serialize(session_expires or expires)
            response.set_cookie(
                key,
                data,
                expires=expires,
                max_age=max_age,
                path=path,
                domain=domain,
                secure=secure,
                httponly=httponly,
            )
