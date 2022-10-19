# ----------------------------------------------------------------------
# |
# |  LocalEndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-14 10:28:29
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Local end-to-end tests for CMake"""

import os
import sys
import unittest

from pathlib import Path

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import Types

sys.path.insert(
    0,
    str(
        Path(Types.EnsureValid(os.getenv("DEVELOPMENT_ENVIRONMENT_CPP_DEVELOPMENT_ROOT")))
        / "Libraries"
        / "cmake"
        / "CppDevelopment"
        / "v1.0.0"
        / "LocalEndToEndTestsImpl"
    ),
)
with ExitStack(lambda: sys.path.pop(0)):
    assert os.path.isdir(sys.path[0])

    from LocalEndToEndTestImpl import *  # type: ignore  # pylint: disable=import-error,wildcard-import


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            unittest.main(
                verbosity=2,
            ),
        )
    except KeyboardInterrupt:
        pass
