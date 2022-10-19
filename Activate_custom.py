# ----------------------------------------------------------------------
# |
# |  Activate_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-05 18:09:44
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

from pathlib import Path
from typing import List, Optional

from Common_Foundation import PathEx                                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell import Commands                                # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Streams.DoneManager import DoneManager               # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Configuration                               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import Constants                                   # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import DataTypes                                   # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.ActivateActivity import ActivateActivity           # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate import DynamicPluginArchitecture  # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
def GetCustomActions(                                                       # pylint: disable=too-many-arguments
    dm: DoneManager,                                                        # pylint: disable=unused-argument
    repositories: List[DataTypes.ConfiguredRepoDataWithPath],               # pylint: disable=unused-argument
    generated_dir: Path,                                                    # pylint: disable=unused-argument
    configuration: Optional[str],                                           # pylint: disable=unused-argument
    version_specs: Configuration.VersionSpecs,                              # pylint: disable=unused-argument
    force: bool,                                                            # pylint: disable=unused-argument
    is_mixin_repo: bool,                                                    # pylint: disable=unused-argument
) -> List[Commands.Command]:
    """Returns a list of actions that should be invoked as part of the activation process."""

    # Calculate the paths
    this_root = Path(__file__).parent
    assert this_root.is_dir(), this_root

    # Create the commands
    commands: List[Commands.Command] = []

    assert configuration

    if CurrentShell.family_name == "Windows":
        if "msvc" in configuration:
            commands += [
                Commands.Set("DEVELOPMENT_ENVIRONMENT_CPP_COMPILER_NAME", "clang-cl"),
                Commands.Set("CC", "clang-cl"),
                Commands.Set("CXX", "clang-cl"),
            ]

        else:
            commands += [
                Commands.Set("DEVELOPMENT_ENVIRONMENT_CPP_COMPILER_NAME", "clang"),
            ]

    # Process the scripts
    scripts_dir = this_root / Constants.SCRIPTS_SUBDIR
    assert scripts_dir.is_dir(), scripts_dir

    with dm.VerboseNested(
        "\nActivating dynamic plugins from '{}'...".format(this_root),
        suffix="\n" if dm.is_debug else "",
    ) as nested_dm:
        for env_name, subdir, name_suffixes in [
            ("DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS", os.path.join("TesterPlugins", "TestExecutors"), ["TestExecutor"]),
        ]:
            commands += DynamicPluginArchitecture.CreateRegistrationCommands(
                nested_dm,
                env_name,
                scripts_dir / subdir,
                lambda fullpath: (
                    fullpath.suffix == ".py"
                    and any(fullpath.stem.endswith(name_suffix) for name_suffix in name_suffixes)
                ),
            )

    commands.append(
        Commands.Augment(
            "DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS",
            [
                # <configuration name>-<plugin type>-<value>[-pri=<priority>]
                "cmake-coverage_executor-Clang",
            ],
        ),
    )

    return commands


# ----------------------------------------------------------------------
def GetCustomActionsEpilogue(                                               # pylint: disable=too-many-arguments
    dm: DoneManager,                                                        # pylint: disable=unused-argument
    repositories: List[DataTypes.ConfiguredRepoDataWithPath],               # pylint: disable=unused-argument
    generated_dir: Path,                                                    # pylint: disable=unused-argument
    configuration: Optional[str],                                           # pylint: disable=unused-argument
    version_specs: Configuration.VersionSpecs,                              # pylint: disable=unused-argument
    force: bool,                                                            # pylint: disable=unused-argument
    is_mixin_repo: bool,                                                    # pylint: disable=unused-argument
) -> List[Commands.Command]:
    """\
    Returns a list of actions that should be invoked as part of the activation process. Note
    that this is called after `GetCustomActions` has been called for each repository in the dependency
    list.

    ********************************************************************************************
    Note that it is very rare to have the need to implement this method. In most cases, it is
    safe to delete the entire method. However, keeping the default implementation (that
    essentially does nothing) is not a problem.
    ********************************************************************************************
    """

    return []
