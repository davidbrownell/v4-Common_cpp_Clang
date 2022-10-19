# ----------------------------------------------------------------------
# |
# |  Setup_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-05 18:09:33
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
# pylint: disable=missing-module-docstring

import os
import uuid

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from semantic_version import Version as SemVer          # pylint: disable=unused-import

from Common_Foundation.ContextlibEx import ExitStack                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import PathEx                                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell import Commands                                # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Streams.DoneManager import DoneManager               # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import SubprocessEx                                  # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import Types                                         # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Configuration                               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import Constants                                   # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.DownloadNSISInstaller import DownloadNSISInstaller     # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.DownloadZipInstaller import DownloadZipInstaller       # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.Installer import Installer                             # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.LocalSevenZipInstaller import LocalSevenZipInstaller   # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
def GetConfigurations() -> Union[
    Configuration.Configuration,
    Dict[
        str,                                # configuration name
        Configuration.Configuration,
    ],
]:
    """Return configuration information for the repository"""

    if CurrentShell.family_name == "Windows":
        architectures = ["x64", ] # TODO: "x86"
    else:
        architectures = [CurrentShell.current_architecture, ]

    configurations: Dict[str, Configuration.Configuration] = {}

    for llvm_version in [
        "15.0.2",
    ]:
        for architecture in architectures:
            if CurrentShell.family_name == "Windows":
                configurations["{}-mingw-{}".format(llvm_version, architecture)] = Configuration.Configuration(
                    "Uses Clang and LLVM 'v{}' (with mingw) targeting '{}'.".format(
                        llvm_version,
                        architecture,
                    ),
                    [
                        Configuration.Dependency(
                            uuid.UUID("6b2e7017-3364-4722-941f-199ade541e41"),
                            "Common_LLVM",
                            "{}-mingw-{}".format(llvm_version, architecture),
                            "https://github.com/davidbrownell/v4-Common_LLVM.git",
                        ),
                        Configuration.Dependency(
                            uuid.UUID("d0ea9e4a-341b-409f-8bce-d1ea0efc202e"),
                            "Common_cpp_Development",
                            architecture,
                            "https://github.com/davidbrownell/v4-Common_cpp_Development.git",
                        ),
                    ],
                )

                for msvc_version in [
                    "17.4",
                ]:
                    configurations["{}-msvc-{}-{}".format(llvm_version, msvc_version, architecture)] = Configuration.Configuration(
                        "Uses Clang and LLVM 'v{}' (with Microsoft Visual Studio 'v{}') targeting '{}'.".format(
                            llvm_version,
                            msvc_version,
                            architecture,
                        ),
                        [
                            Configuration.Dependency(
                                uuid.UUID("6b2e7017-3364-4722-941f-199ade541e41"),
                                "Common_LLVM",
                                "{}-msvc-{}-{}".format(llvm_version, msvc_version, architecture),
                                "https://github.com/davidbrownell/v4-Common_LLVM.git",
                            ),
                            Configuration.Dependency(
                                uuid.UUID("d0ea9e4a-341b-409f-8bce-d1ea0efc202e"),
                                "Common_cpp_Development",
                                architecture,
                                "https://github.com/davidbrownell/v4-Common_cpp_Development.git",
                            ),
                        ],
                    )

            else:
                configurations["{}-{}".format(llvm_version, architecture)] = Configuration.Configuration(
                    "Uses Clang and and LLVM 'v{}' (without any external dependencies) targeting '{}'.".format(llvm_version, architecture),
                    [
                        Configuration.Dependency(
                            uuid.UUID("6b2e7017-3364-4722-941f-199ade541e41"),
                            "Common_LLVM",
                            "{}-{}".format(llvm_version, architecture),
                            "https://github.com/davidbrownell/v4-Common_LLVM.git",
                        ),
                        Configuration.Dependency(
                            uuid.UUID("d0ea9e4a-341b-409f-8bce-d1ea0efc202e"),
                            "Common_cpp_Development",
                            architecture,
                            "https://github.com/davidbrownell/v4-Common_cpp_Development.git",
                        ),
                    ],
                )

    return configurations


# ----------------------------------------------------------------------
def GetCustomActions(
    dm: DoneManager,                                    # pylint: disable=unused-argument
    explicit_configurations: Optional[List[str]],       # pylint: disable=unused-argument
    force: bool,                                        # pylint: disable=unused-argument
) -> List[Commands.Command]:
    """Return custom actions invoked as part of the setup process for this repository"""

    commands: List[Commands.Command] = []

    root_dir = Path(__file__).parent
    assert root_dir.is_dir(), root_dir

    # Create a link to the foundation's .pylintrc file
    foundation_root_file = Path(Types.EnsureValid(os.getenv(Constants.DE_FOUNDATION_ROOT_NAME))) / ".pylintrc"
    assert foundation_root_file.is_file(), foundation_root_file

    commands.append(
        Commands.SymbolicLink(
            root_dir / foundation_root_file.name,
            foundation_root_file,
            remove_existing=True,
            relative_path=True,
        ),
    )

    return commands
