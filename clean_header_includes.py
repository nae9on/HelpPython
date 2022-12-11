from pathlib import Path
import re
from typing import List, Tuple, Match

debug = True
dry_run = False


def get_files(parent_directory: Path) -> Tuple[List[Path], List[Path]]:
    """Get outermost files and directories in the Path"""
    sub_files: List[Path] = []
    sub_directories: List[Path] = []
    for path_object in parent_directory.iterdir():
        if path_object.is_file():
            sub_files.append(path_object)
        if path_object.is_dir():
            sub_directories.append(path_object)

    return sub_files, sub_directories


def glob_file_by_pattern(parent_directory: Path, pattern="*") -> List[Path]:
    """Pattern match files recursively in the nested directory tree"""
    files: List[Path] = []
    for path_object in parent_directory.rglob(pattern):
        files.append(path_object)
    return files


class Lib:
    path_source_dir = Path("/home/akadar/Git/elio2")
    path_binary_dir = Path("/home/akadar/Git/elio2/qtcreator-build")
    path_detection_libs: Path = path_source_dir / "detection" / "libs"
    path_xstream_libs: Path = path_source_dir / "xstream" / "libs"
    list_names_detection_libs: List[str] = None
    list_names_xstream_libs: List[str] = None

    @classmethod
    def get_list_names_detection_libs(cls):
        _, sub_directories = get_files(cls.path_detection_libs)
        cls.list_names_detection_libs = [full_path.name for full_path in sub_directories]
        print(f"Detection libs count = {len(cls.list_names_detection_libs)}")
        print(cls.list_names_detection_libs, sep="\n")

    @classmethod
    def get_list_names_xstream_libs(cls):
        _, sub_directories = get_files(cls.path_xstream_libs)
        cls.list_names_xstream_libs = [full_path.name for full_path in sub_directories]
        print(f"Xstream libs count = {len(cls.list_names_xstream_libs)}")
        print(cls.list_names_xstream_libs, sep="\n")

    def __init__(self, lib_name: str):
        self.set_detection_libs_to_include = set()
        self.set_xstream_libs_to_include = set()
        self.set_libs_not_included = set()
        self.path_main_binary_dir: Path = Lib.path_binary_dir / lib_name
        self.path_main_lib: Path = Lib.path_detection_libs / lib_name
        self.path_main_cmakelists: Path = self.path_main_lib / "CMakeLists.txt"

        self._pre_process()
        self._post_process()

    def _pre_process(self):
        pass

    def _post_process(self):
        pass

    def process(self):
        self._pre_process()
        self._process_header_includes()
        self._post_process()

    def _process_header_includes(self):
        private_h_files = glob_file_by_pattern(self.path_main_lib / "src", "*.h")
        cpp_files = glob_file_by_pattern(self.path_main_lib / "src", "*.cpp")
        all_files = []
        all_files.extend(private_h_files)
        all_files.extend(cpp_files)
        for file in all_files:
            self._do_replace_includes(file)

    def _do_replace_includes(self, path_source_file: Path):
        print(path_source_file)

        allowed_libs = []
        allowed_libs.extend(Lib.list_names_detection_libs)
        allowed_libs.extend(Lib.list_names_xstream_libs)

        def clean_include(match_obj: Match):
            """
            repl function is called for every non-overlapping occurrence of pattern.
            The function takes a single match object argument, and returns the replacement string.
            """

            replacement_string: str = match_obj.group(0)
            lib_name: str = match_obj.group(1)
            header: str = match_obj.group(2)

            if lib_name in Lib.list_names_detection_libs:
                self.set_detection_libs_to_include.add(lib_name)
            elif lib_name in Lib.list_names_xstream_libs:
                self.set_xstream_libs_to_include.add(lib_name)
            else:
                self.set_libs_not_included.add(lib_name)
                # raise Exception(f"{lib_name} is neither a detection lib nor a xstream lib")

            if lib_name in allowed_libs:
                replacement_string = '#include "' + header + '"\n'

            return replacement_string

        pattern = r"#include \"(.*)/(.*)\"\n"
        # matches = re.findall(pattern, source_file.read_text())
        # print(matches)
        original_text = path_source_file.read_text()
        new_text, number_of_subs_made = re.subn(pattern, clean_include, original_text)
        print(f"Number of matches found = {number_of_subs_made}\n")
        if not dry_run and new_text != original_text:
            path_source_file.write_text(new_text)


if __name__ == "__main__":
    Lib.get_list_names_detection_libs()
    Lib.get_list_names_xstream_libs()

    lib = Lib("WTZoneCounting")
    lib.process()

    print("detection libs:")
    for item in lib.set_detection_libs_to_include:
        print(f'traf_lib_include("detection" "{item}")')

    print("\nxstream libs:")
    for item in lib.set_xstream_libs_to_include:
        print(f'traf_lib_include("xstream" "{item}")')

    print("\nUnknown libs:")
    for item in lib.set_libs_not_included:
        print(f'traf_lib_include("unknown" "{item}")')
