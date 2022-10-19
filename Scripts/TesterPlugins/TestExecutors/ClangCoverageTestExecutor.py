# ----------------------------------------------------------------------
# |
# |  ClangCoverageTestExecutor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-10 15:47:32
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the ClangCoverageTestExecutor object"""

import json
import os

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from Common_Foundation.EnumSource import EnumSource
from Common_Foundation.Streams.DoneManager import DoneManager
from Common_Foundation import SubprocessEx
from Common_Foundation.Types import overridemethod

from Common_FoundationEx.CompilerImpl.CompilerImpl import CompilerImpl
from Common_FoundationEx.TesterPlugins.CodeCoverageValidatorImpl.CodeCoverageFilter import ApplyFilters, CodeCoverageContentFilter, CoverageResult
from Common_FoundationEx.InflectEx import inflect
from Common_FoundationEx import TyperEx

from Common_cpp_Development.CodeCoverageExecutor import CodeCoverageExecutor    # type: ignore  # pylint: disable=import-error
from Common_cpp_Development.TestExecutorImpl import TestExecutorImpl            # type: ignore  # pylint: disable=import-error


# ----------------------------------------------------------------------
class TestExecutor(TestExecutorImpl):
    """Test Executor able to process Clang coverage output"""

    # ----------------------------------------------------------------------
    def __init__(self):
        super(TestExecutor, self).__init__(
            "Clang",
            "Extracts code coverage information from clang binaries.",
            _CodeCoverageExecutor(),
            is_code_coverage_executor=True,
        )

    # ----------------------------------------------------------------------
    @overridemethod
    def GetCustomCommandLineArgs(self) -> TyperEx.TypeDefinitionsType:
        # No custom arguments support
        return {}

    # ----------------------------------------------------------------------
    @overridemethod
    def IsSupportedCompiler(
        self,
        compiler: CompilerImpl,
    ) -> bool:
        return compiler.name == "CMake" or compiler.IsSupported(Path("file.cpp"))

    # ----------------------------------------------------------------------
    @overridemethod
    def IsSupportedTestItem(
        self,
        item: Path,
    ) -> bool:
        # No custom logic here
        return True


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _CodeCoverageExecutor(CodeCoverageExecutor):
    # ----------------------------------------------------------------------
    def __init__(self):
        super(_CodeCoverageExecutor, self).__init__("coverage.ade", "lines")

    # ----------------------------------------------------------------------
    @overridemethod
    def StartCoverage(
        self,
        dm: DoneManager,
        coverage_filename: Path,
    ) -> None:
        found = 0

        if coverage_filename.exists():
            with dm.Nested("Removing previous coverage file..."):
                coverage_filename.unlink()

        with dm.Nested(
            "Removing previous .gcda files...",
            lambda: "{} found".format(inflect.no("file", found)),
        ) as cleanup_dm:
            if coverage_filename.parent.is_dir():
                for root, _, filenames in EnumSource(coverage_filename.parent):
                    for filename in filenames:
                        if os.path.splitext(filename)[1] == ".gcda":
                            fullpath = root / filename

                            with cleanup_dm.VerboseNested("'{}'...".format(fullpath)):
                                fullpath.unlink()
                                found += 1

    # ----------------------------------------------------------------------
    @overridemethod
    def StopCoverage(
        self,
        dm: DoneManager,
        coverage_filename: Path,
    ) -> None:
        gcda_dirs: Set[Path] = set()

        gcda_dirs.add(coverage_filename.parent)

        with dm.Nested(
            "Detecting .gcda dirs...",
            lambda: "{} found".format(inflect.no("directory", len(gcda_dirs))),
        ):
            for root, _, filenames in EnumSource(coverage_filename.parent):
                for filename in filenames:
                    if os.path.splitext(filename)[1] == ".gcda":
                        gcda_dirs.add(root)
                        break

        with dm.Nested("Generating coverage information...") as generate_dm:
            command_line = 'grcov {dirs} --llvm --output-type ade > "{output_file}"'.format(
                dirs=" ".join('"{}"'.format(gcda_dir) for gcda_dir in gcda_dirs),
                output_file=coverage_filename,
            )

            generate_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

            result = SubprocessEx.Run(
                command_line,
                cwd=coverage_filename.parent,
            )

            generate_dm.result = result.returncode

            if generate_dm.result != 0:
                generate_dm.WriteError(result.output)

            with generate_dm.YieldVerboseStream() as stream:
                stream.write(result.output)

    # ----------------------------------------------------------------------
    @overridemethod
    def ExtractCoverageInfo(
        self,
        dm: DoneManager,
        compiler_context: Dict[str, Any],
        coverage_filename: Path,
        binary_filename: Path,
    ) -> Tuple[
        int,                                # Covered
        int,                                # Not Covered
    ]:
        with dm.Nested("Extracting coverage information...") as extract_dm:
            # ----------------------------------------------------------------------
            def CreateItemMatcher(
                glob_value: str,
            ) -> Callable[[str], bool]:
                glob_parts = glob_value.split("::")

                # ----------------------------------------------------------------------
                def Impl(
                    value: str,
                ) -> bool:
                    value_parts = value.split("::")

                    glob_part_index = 0
                    value_part_index = 0

                    while glob_part_index < len(glob_parts) and value_part_index < len(value_parts):
                        glob_part = glob_parts[glob_part_index]
                        value_part = value_parts[value_part_index]

                        if glob_part == "*{1}":
                            value_part_index += 1

                        elif glob_part == "*":
                            if glob_part_index + 1 == len(glob_parts):
                                return True

                            next_glob_part = glob_parts[glob_part_index + 1]

                            while (
                                value_part_index < len(value_parts)
                                and value_parts[value_part_index] != next_glob_part
                            ):
                                value_part_index += 1

                        else:
                            if glob_part != value_part:
                                break

                            value_part_index += 1

                        glob_part_index += 1

                    return glob_part_index == len(glob_parts) and value_part_index == len(value_parts)

                # ----------------------------------------------------------------------

                return Impl

            # ----------------------------------------------------------------------
            def CreateSourceMatcher(
                filter: CodeCoverageContentFilter,
            ) -> Callable[[str], bool]:
                include_funcs = [CreateItemMatcher(item) for item in filter.includes or []]
                exclude_funcs = [CreateItemMatcher(item) for item in filter.excludes or []]

                # ----------------------------------------------------------------------
                def Impl(
                    value: str,
                ) -> bool:
                    if (
                        exclude_funcs
                        and any(exclude_func(value) for exclude_func in exclude_funcs)
                    ):
                        return False

                    if (
                        include_funcs
                        and not any(include_func(value) for include_func in include_funcs)
                    ):
                        return False

                    return True

                # ----------------------------------------------------------------------

                return Impl

            # ----------------------------------------------------------------------
            def ApplyFunc(
                source_filters: Dict[
                    str,                    # source filename glob
                    CodeCoverageContentFilter,
                ],
            ) -> Optional[CoverageResult]:
                # Create the matchers
                should_match_all_file_globs: Set[str] = set()
                source_matchers: Dict[str, Callable[[str], bool]] = {}

                for k, v in source_filters.items():
                    if (
                        len(v.includes or []) == 1
                        and v.includes[0] == "*"
                        and v.excludes is None
                    ):
                        should_match_all_file_globs.add(k)
                        continue

                    source_matchers[k] = CreateSourceMatcher(v)

                # Calculate the results
                file_result: Optional[CoverageResult] = None
                result: Optional[Tuple[int, int]] = None

                with coverage_filename.open() as f:
                    for line in f.readlines():
                        data = json.loads(line)

                        filename = data.get("file", {}).get("name", None)
                        assert filename is not None

                        filename = Path(filename)

                        # Coverage data is organized by file and by method;
                        # determine which one we are looking at here.
                        file_data = data.get("file", {})

                        if "total_covered" in file_data and "total_uncovered" in file_data:
                            if (
                                file_result is None
                                and any(
                                    filename.match(should_match_all_file_glob)
                                    for should_match_all_file_glob in should_match_all_file_globs
                                )
                            ):
                                file_result = CoverageResult(
                                    file_data["total_covered"],
                                    file_data["total_uncovered"],
                                )

                            continue

                        match_funcs: List[Callable[[str], bool]] = []

                        for source_glob, match_func in source_matchers.items():
                            if filename.match(source_glob):
                                match_funcs.append(match_func)

                        method_data = data.get("method", None)
                        assert method_data

                        method_name = method_data.get("name", None)
                        assert method_name is not None

                        if match_funcs and all(match_func(method_name) for match_func in match_funcs):
                            total_covered = method_data.get("total_covered", None)
                            total_uncovered = method_data.get("total_uncovered", None)

                            assert total_covered is not None
                            assert total_uncovered is not None

                            if result is None:
                                result = (0, 0)

                            result = (
                                result[0] + total_covered,
                                result[1] + total_uncovered,
                            )

                if result is not None:
                    return CoverageResult(*result)
                if file_result is not None:
                    return file_result

                return None

            # ----------------------------------------------------------------------

            source_filenames = compiler_context.get("inputs", None)
            if source_filenames is None:
                source_filenames = compiler_context.get("input", None)
                source_filenames = [source_filenames, ] or []

            result = ApplyFilters(binary_filename, source_filenames, ApplyFunc)

            if result is None:
                return 0, 0

            return result.covered, result.uncovered
