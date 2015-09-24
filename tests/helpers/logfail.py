# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2015 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Logging handling for the tests."""

import logging

import pytest

try:
    import pytest_catchlog as catchlog_mod
except ImportError:
    # When using pytest for pyflakes/pep8/..., the plugin won't be available
    # but conftest.py will still be loaded.
    #
    # However, LogFailHandler.emit will never be used in that case, so we just
    # ignore the ImportError.
    pass


class LogFailHandler(logging.Handler):

    """A logging handler which makes tests fail on unexpected messages."""

    def __init__(self, level=logging.NOTSET, min_level=logging.WARNING):
        self._min_level = min_level
        super().__init__(level)

    def emit(self, record):
        logger = logging.getLogger(record.name)
        root_logger = logging.getLogger()

        caplog_handler = None

        for h in root_logger.handlers:
            if isinstance(h, catchlog_mod.RecordingHandler):
                caplog_handler = h
                break

        if (caplog_handler is not None and
                caplog_handler.level == record.levelno):
            # caplog.at_level(...) was used with the level of this message, i.e.
            # it was expected.
            return
        if record.levelno < self._min_level:
            return
        pytest.fail("Got logging message on logger {} with level {}: "
                    "{}!".format(record.name, record.levelname,
                                 record.getMessage()))


@pytest.yield_fixture(scope='session', autouse=True)
def fail_on_logging():
    handler = LogFailHandler()
    logging.getLogger().addHandler(handler)
    yield
    logging.getLogger().removeHandler(handler)
    handler.close()


@pytest.yield_fixture(autouse=True)
def caplog_bug_workaround(request):
    """WORKAROUND for pytest-capturelog bug.

    https://bitbucket.org/memedough/pytest-capturelog/issues/7/

    This would lead to LogFailHandler failing after skipped tests as there are
    multiple CaptureLogHandlers.
    """
    yield
    if catchlog_mod is None:
        return

    root_logger = logging.getLogger()
    caplog_handlers = [h for h in root_logger.handlers
                       if isinstance(h, catchlog_mod.RecordingHandler)]

    for h in caplog_handlers:
        root_logger.removeHandler(h)
        h.close()
