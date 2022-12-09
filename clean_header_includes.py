from pathlib import Path
import re
from typing import List


set_detection_libs = set()
set_xstream_libs = set()
list_detection_libs = []
list_xstream_libs = []


def get_files(parent_directory: Path):
    """Get files and directories in the Path"""
    files = []
    sub_directories = []
    for path_object in parent_directory.iterdir():
        if path_object.is_file():
            files.append(path_object)
        if path_object.is_dir():
            sub_directories.append(path_object)

    return files, sub_directories


def glob_file_by_pattern(parent_directory: Path, pattern="*"):
    files = []
    for path_object in parent_directory.rglob(pattern):
            files.append(path_object)
    return files


def get_includes(source_file: Path):
    print(source_file)
    pattern = r"#include \"(.*)/(.*)\"\n"
    matches = re.findall(pattern, source_file.read_text(), flags=re.IGNORECASE)
    print(matches)
    print("\n")


def get_headers():
    pass


def do_replace_includes(source_file: Path):
    print(source_file)

    global list_detection_libs, list_xstream_libs
    global set_detection_libs, set_xstream_libs

    allowed_libs = []
    allowed_libs += list_detection_libs
    allowed_libs += list_xstream_libs

    pattern = r"#include \"(.*)/(.*)\"\n"

    def clean_include(match_obj):
        replaced_string = None
        if match_obj.group() is not None:
            lib_name = match_obj.group(1)
            header = match_obj.group(2)
            if lib_name in allowed_libs:
                replaced_string = '#include "' + header + '"\n'
                if lib_name in list_detection_libs:
                    set_detection_libs.add(lib_name)
                elif lib_name in list_xstream_libs:
                    set_xstream_libs.add(lib_name)
                else:
                    raise Exception(f"{lib_name} is neither a detection lib nor a xstream lib")
            else:
                # Do not replace
                replaced_string = match_obj.group(0)
        return replaced_string

    new_source_file = re.sub(pattern, clean_include, source_file.read_text())
    source_file.write_text(new_source_file)
    print("\n")


def process_header_includes(main_lib: Path):
    global list_detection_libs, list_xstream_libs
    h_files = glob_file_by_pattern(main_lib / "src", "*.h")
    cpp_files = glob_file_by_pattern(main_lib / "src", "*.cpp")
    files = []
    files += h_files
    files += cpp_files
    # print(*files, sep="\n")
    for file in files:
        get_includes(file)
        do_replace_includes(file)


if __name__ == "__main__":
    root = Path("/home/akadar/Git/elio2")
    detection_libs = root / "detection" / "libs"
    xstream_libs = root / "xstream" / "libs"
    main_lib = detection_libs / "WorldTrackerApplications"
    main_target = main_lib / "CMakeLists.txt"

    _, detection_sub_directories = get_files(detection_libs)
    list_detection_libs = [full_path.name for full_path in detection_sub_directories]
    _, xstream_sub_directories = get_files(xstream_libs)
    list_xstream_libs = [full_path.name for full_path in xstream_sub_directories]

    print(list_detection_libs, sep="\n")
    print(list_xstream_libs, sep="\n")

    # files, sub_directories = get_files(main_lib / "src")
    # print(*files, sep="\n")

    process_header_includes(main_lib)

    # get_includes(Path("/home/akadar/Git/elio2/detection/libs/WTZoneCounting/src/WTZoneCounting.cpp"))
    # do_replace_includes(Path("/home/akadar/Git/elio2/detection/libs/WTZoneCounting/src/WTZoneCounting.cpp"))

    print("detection libs:")
    for item in set_detection_libs:
        print(f'traf_lib_include("detection" "{item}")')

    print("xstream libs:")
    for item in set_xstream_libs:
        print(f'traf_lib_include("xstream" "{item}")')


