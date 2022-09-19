"""
Sessions
========

Add session support to a WSGI application. For full client-side session
storage see :mod:`secure_cookie.cookie`.


Session Store
-------------

To have the most control over the session, use a session store directly
in your application dispatch. :meth:`SessionStore.new` creates a new
:class:`Session` with a unique id, and :meth:`SessionStore.get` gets an
existing session by that id. Store the id as a cookie.

.. code-block:: python

    from secure_cookie.session import FilesystemSessionStore
    from werkzeug.wrappers import Request, Response

    session_store = FilesystemSessionStore()

    @Request.application
    def application(request):
        sid = request.cookies.get("session_id")

        if sid is None:
            request.session = session_store.new()
        else:
            request.session = session_store.get(sid)

        response = Response(do_stuff(request))

        if request.session.should_save:
            session_store.save(request.session)
            response.set_cookie("session_id", request.session.sid)

        return response


Cleanup
-------

This module does not implement a way to check if a session is expired.
That should be done by a scheduled job independent of the running
application, and is storage-specific. For example, to prune unused
filesystem sessions one could check the modified time of the files. If
sessions are stored in the database, the ``new()`` method could add an
expiration timestamp.


Middleware
----------

For simple applications, :class:`SessionMiddleware` is provided. This
makes the current session available in the WSGI environment as the
``secure_cookie.session`` key. This is convenient, but not as flexible
as using the store directly.

.. code-block:: python

    from secure_cookie.session import FilesystemSessionStore
    from secure_cookie.session import SessionMiddleware

    session_store = FilesystemSessionStore()
    app = SessionMiddleware(app, session_store)


API
---

.. autoclass:: Session
    :members:

.. autoclass:: SessionStore
    :members:

.. autoclass:: FilesystemSessionStore
    :members:

.. autoclass:: SessionMiddleware
    :members:
"""
import os
import pathlib
import pickle
import re
import tempfile
from hashlib import sha1
from random import random
from time import time

from werkzeug.datastructures import CallbackDict
from werkzeug.http import dump_cookie
from werkzeug.http import parse_cookie
from werkzeug.wsgi import ClosingIterator

_sha1_re = re.compile(r"^[a-f0-9]{40}$")


def _urandom():
    if hasattr(os, "urandom"):
        return os.urandom(30)
    return str(random()).encode("ascii")


def generate_key(salt=None):
    if salt is None:
        salt = repr(salt).encode("ascii")
    return sha1(b"".join([salt, str(time()).encode("ascii"), _urandom()])).hexdigest()


class ModificationTrackingDict(CallbackDict):
    __slots__ = ("modified",)

    def __init__(self, *args, **kwargs):
        def on_update(self):
            self.modified = True

        self.modified = False
        super(ModificationTrackingDict, self).__init__(on_update=on_update)
        dict.update(self, *args, **kwargs)

    def copy(self):
        """Create a flat copy of the dict."""
        missing = object()
        result = object.__new__(self.__class__)
        for name in self.__slots__:
            val = getattr(self, name, missing)
            if val is not missing:
                setattr(result, name, val)
        return result

    def __copy__(self):
        return self.copy()


class Session(ModificationTrackingDict):
    """Subclass of a dict that keeps track of direct object changes.
    Changes in mutable structures are not tracked, for those you have to
    set ``modified`` to ``True`` by hand.
    """

    __slots__ = ModificationTrackingDict.__slots__ + ("sid", "new")

    def __init__(self, data, sid, new=False):
        super(Session, self).__init__(data)
        self.sid = sid
        self.new = new

    def __repr__(self):
        return "<{} {}{}>".format(
            self.__class__.__name__,
            dict.__repr__(self),
            "*" if self.should_save else "",
        )

    @property
    def should_save(self):
        """True if the session should be saved."""
        return self.modified


class SessionStore(object):
    """Base class for all session stores.

    :param session_class: The session class to use.
    """

    def __init__(self, session_class=Session):
        self.session_class = session_class

    def is_valid_key(self, key):
        """Check if a key has the correct format."""
        return _sha1_re.match(key) is not None

    def generate_key(self, salt=None):
        """Simple function that generates a new session key."""
        return generate_key(salt)

    def new(self):
        """Generate a new session."""
        return self.session_class({}, self.generate_key(), True)

    def save(self, session):
        """Save a session."""

    def save_if_modified(self, session):
        """Save if a session class wants an update."""
        if session.should_save:
            self.save(session)

    def delete(self, session):
        """Delete a session."""

    def get(self, sid):
        """Get a session for this sid or a new session object. This
        method has to check if the session key is valid and create a new
        session if that wasn't the case.
        """
        return self.session_class({}, sid, True)


# Used for temporary files by the filesystem session store.
_fs_transaction_suffix = ".__session"


class FilesystemSessionStore(SessionStore):
    """Simple example session store that saves sessions on the
    filesystem.

    :param path: The path to the folder used for storing the sessions.
        If not provided the default temporary directory is used.
    :param filename_template: A string template used to give the session
        a filename. ``%s`` is replaced with the session id.
    :param session_class: The session class to use.
    :param renew_missing: Set to ``True`` if you want the store to give
        the user a new sid if the session was not yet saved.

    .. versionchanged:: 0.1.0
        ``filename_template`` defaults to ``secure_cookie_%s.session``
        instead of ``werkzeug_%s.sess``.
    """

    def __init__(
        self,
        path=None,
        filename_template="secure_cookie_%s.session",
        session_class=Session,
        renew_missing=False,
        mode=0o644,
    ):
        super(FilesystemSessionStore, self).__init__(session_class=session_class)

        if path:
            try:
                pathlib.Path(path).mkdir(parents=True, exist_ok=True)
            except OSError:
                raise
        else:
            path = tempfile.gettempdir()

        self.path = path

        assert not filename_template.endswith(_fs_transaction_suffix), (
            "filename templates may not end with %s" % _fs_transaction_suffix
        )
        self.filename_template = filename_template
        self.renew_missing = renew_missing
        self.mode = mode

    def get_session_filename(self, sid):
        # Out of the box this should be a strict ASCII subset, but you
        # might reconfigure the session object to have a more arbitrary
        # string.
        return str(pathlib.Path(self.path, self.filename_template % sid))

    def save(self, session):
        fn = self.get_session_filename(session.sid)
        fd, tmp = tempfile.mkstemp(suffix=_fs_transaction_suffix, dir=self.path)
        f = os.fdopen(fd, "wb")

        try:
            pickle.dump(dict(session), f, pickle.HIGHEST_PROTOCOL)
        finally:
            f.close()

        try:
            os.rename(tmp, fn)
            os.chmod(fn, self.mode)
        except (IOError, OSError):  # noqa: B014
            pass

    def delete(self, session):
        fn = self.get_session_filename(session.sid)

        try:
            os.unlink(fn)
        except OSError:
            pass

    def get(self, sid):
        if not self.is_valid_key(sid):
            return self.new()

        try:
            f = open(self.get_session_filename(sid), "rb")
        except IOError:
            if self.renew_missing:
                return self.new()

            data = {}
        else:
            try:
                try:
                    data = pickle.load(f)
                except Exception:
                    data = {}
            finally:
                f.close()

        return self.session_class(data, sid, False)

    def list(self):
        """List all sessions in the store."""
        before, after = self.filename_template.split("%s", 1)
        filename_re = re.compile(
            r"{}(.{{5,}}){}$".format(re.escape(before), re.escape(after))
        )
        result = []
        for filename in os.listdir(self.path):
            # this is a session that is still being saved.
            if filename.endswith(_fs_transaction_suffix):
                continue
            match = filename_re.match(filename)
            if match is not None:
                result.append(match.group(1))
        return result


class SessionMiddleware(object):
    """A middleware that puts the session object of a store into the
    WSGI environ. It automatically sets cookies and restores sessions.

    However a middleware is not the preferred solution because it won't
    be as fast as sessions managed by the application itself and will
    put a key into the WSGI environment only relevant for the
    application which is against the concept of WSGI.

    The cookie parameters are the same as for the :func:`~dump_cookie`
    function just prefixed with ``cookie_``. Additionally ``max_age`` is
    called ``cookie_age`` and not ``cookie_max_age`` because of
    backwards compatibility.

    .. versionchanged:: 0.1.0
        ``environ_key`` defaults to ``secure_cookie.session`` instead of
        ``werkzeug.session``.
    """

    def __init__(
        self,
        app,
        store,
        cookie_name="session_id",
        cookie_age=None,
        cookie_expires=None,
        cookie_path="/",
        cookie_domain=None,
        cookie_secure=None,
        cookie_httponly=False,
        cookie_samesite="Lax",
        environ_key="secure_cookie.session",
    ):
        self.app = app
        self.store = store
        self.cookie_name = cookie_name
        self.cookie_age = cookie_age
        self.cookie_expires = cookie_expires
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.environ_key = environ_key

    def __call__(self, environ, start_response):
        sid = self._get_session_id(environ)

        if sid is None:
            session = self.store.new()
        else:
            session = self.store.get(sid)

        environ[self.environ_key] = session

        def injecting_start_response(status, headers, exc_info=None):
            if session.should_save:
                self.store.save(session)
                headers.append(("Set-Cookie", self._dump_cookie(session)))

            return start_response(status, headers, exc_info)

        return ClosingIterator(
            self.app(environ, injecting_start_response),
            lambda: self.store.save_if_modified(session),
        )

    def _get_session_id(self, environ):
        cookie = parse_cookie(environ.get("HTTP_COOKIE", ""))
        return cookie.get(self.cookie_name, None)

    def _dump_cookie(self, session):
        return dump_cookie(
            key=self.cookie_name,
            value=session.sid,
            max_age=self.cookie_age,
            expires=self.cookie_expires,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )
