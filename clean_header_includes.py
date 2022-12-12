import logging
from pathlib import Path
import re
import subprocess
from typing import List, Tuple, Match, AnyStr

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


def get_begin_end_block_indexes(list_matching_line_numbers: List[int]):
    """
    Returns a map of begin-end matching line number pairs.
    Also returns the begin-end corresponding to the largest matching block.
    """
    begin_index = -1
    end_index = -1
    begin_end_line_numbers = {}
    for index, line_num in enumerate(list_matching_line_numbers):

        # For the first line
        if begin_index == -1 and end_index == -1:
            begin_index = index
            end_index = index
            continue

        if line_num == list_matching_line_numbers[end_index] + 1:
            end_index += 1
            continue
        else:
            begin_end_line_numbers[list_matching_line_numbers[begin_index]] =\
                list_matching_line_numbers[end_index]
            begin_index = index
            end_index = index

    begin_end_line_numbers[list_matching_line_numbers[begin_index]] = \
        list_matching_line_numbers[end_index]

    # # Get begin-end corresponding to the largest block
    new_map = {}
    for begin_line, end_line in begin_end_line_numbers.items():
        new_map[begin_line] = end_line - begin_line + 1
    target_index = max(new_map, key=new_map.get)

    begin_line_number = target_index
    end_line_number = begin_end_line_numbers[target_index]
    return begin_end_line_numbers, begin_line_number, end_line_number


def get_matching_lines(path_file: Path, pattern: str):
    # Read all the lines in the file
    lines: List[AnyStr] = []
    with open(path_file, 'r') as fp:
        lines = fp.readlines()

    # Find lines matching a certain pattern
    matching_lines: List[int] = []
    for index, line in enumerate(lines):
        matches = re.findall(pattern, line)
        if matches:
            matching_lines.append(index)

    return lines, matching_lines


def sort_block_of_lines_matching_pattern(path_file: Path, pattern: str):
    lines, matching_lines = get_matching_lines(path_file, pattern)

    begin_end_line_numbers, _, _ = get_begin_end_block_indexes(matching_lines)

    for begin_line, end_line in begin_end_line_numbers.items():
        lines_to_sort = lines[begin_line:end_line+1]
        lines[begin_line:end_line+1] = sorted(set(lines_to_sort), reverse=True)

    with open(path_file, 'w') as fp:
        contents = "".join(lines)
        fp.write(contents)


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
        logging.info(f"Detection libs count = {len(cls.list_names_detection_libs)}")
        logging.info(f", ".join(cls.list_names_detection_libs))

    @classmethod
    def get_list_names_xstream_libs(cls):
        _, sub_directories = get_files(cls.path_xstream_libs)
        cls.list_names_xstream_libs = [full_path.name for full_path in sub_directories]
        logging.info(f"Xstream libs count = {len(cls.list_names_xstream_libs)}")
        logging.info(f", ".join(cls.list_names_xstream_libs))

    def __init__(self, lib_name: str):
        self.set_detection_libs_to_include = set()
        self.set_xstream_libs_to_include = set()
        self.set_libs_not_included = set()
        self.path_main_binary_dir: Path = Lib.path_binary_dir / lib_name
        self.path_main_lib: Path = Lib.path_detection_libs / lib_name
        self.path_main_cmakelists: Path = self.path_main_lib / "CMakeLists.txt"

    def _pre_process(self):
        args = "/usr/bin/cmake --build /home/akadar/Git/elio2/qtcreator-build/WTZoneCounting/Desktop/Release --target clean"
        completed_process = subprocess.run(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if completed_process.returncode != 0:
            logging.critical(f"Failed target clean {self.path_main_lib.name}")
            logging.error(completed_process.stdout)
        else:
            logging.critical(f"Passed target clean {self.path_main_lib.name}")

    def _post_process(self):
        args = "/usr/bin/cmake --build /home/akadar/Git/elio2/qtcreator-build/WTZoneCounting/Desktop/Release --target all -j 1"
        # completed_process = subprocess.run(args, shell=True, capture_output=True, text=True)
        completed_process = subprocess.run(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if completed_process.returncode != 0:
            logging.critical(f"Failed target all {self.path_main_lib.name}")
            logging.error(completed_process.stdout)
        else:
            logging.critical(f"Passed target all {self.path_main_lib.name}")

    def process(self):
        self._pre_process()
        self._process_header_includes()
        self._include_libs_in_cmakelists("detection", self.set_detection_libs_to_include)
        self._include_libs_in_cmakelists("xstream", self.set_xstream_libs_to_include)
        self._post_process()

    def _include_libs_in_cmakelists(self, lib_type, set_to_include):

        # Find lines matching pattern
        pattern = r"traf_lib_include\(\"" + lib_type + r"\" \"(.*)\"\)"
        lines, matching_lines = get_matching_lines(self.path_main_cmakelists, pattern)

        _, begin_line_number, end_line_number = get_begin_end_block_indexes(matching_lines)

        print(begin_line_number, end_line_number)

        # Prepare new includes
        new_includes = lines[begin_line_number:end_line_number+1]
        for item in set_to_include:
            new_includes.append(f'traf_lib_include("{lib_type}" "{item}")\n')

        new_includes = sorted(set(new_includes), reverse=True)

        # Remove includes
        lines = lines[0:begin_line_number] + lines[end_line_number+1:]

        # Add lines
        for item in new_includes:
            lines.insert(begin_line_number, item)

        with open(self.path_main_cmakelists, 'w') as fp:
            contents = "".join(lines)
            fp.write(contents)


    def _process_header_includes(self):
        private_h_files = glob_file_by_pattern(self.path_main_lib / "src", "*.h")
        cpp_files = glob_file_by_pattern(self.path_main_lib / "src", "*.cpp")
        all_files = []
        all_files.extend(private_h_files)
        all_files.extend(cpp_files)
        for file in all_files:
            self._do_replace_includes(file)

    def _do_replace_includes(self, path_source_file: Path):
        logging.debug(path_source_file)

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
        logging.debug(f"Number of matches found = {number_of_subs_made}\n")
        if not dry_run and new_text != original_text:
            path_source_file.write_text(new_text)


def main():
    Lib.get_list_names_detection_libs()
    Lib.get_list_names_xstream_libs()

    lib = Lib("WTZoneCounting")
    lib.process()

    logging.info("detection libs:")
    for item in lib.set_detection_libs_to_include:
        logging.info(f'traf_lib_include("detection" "{item}")')

    logging.info("xstream libs:")
    for item in lib.set_xstream_libs_to_include:
        logging.info(f'traf_lib_include("xstream" "{item}")')

    logging.info("Unknown libs:")
    for item in lib.set_libs_not_included:
        logging.info(f'traf_lib_include("unknown" "{item}")')


if __name__ == "__main__":
    logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
    main()
