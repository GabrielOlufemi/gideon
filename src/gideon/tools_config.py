from gideon.tools.read_file import read_file, READ_FILE_SCHEMA
from gideon.tools.list_directories import list_directories, LIST_DIRECTORIES_SCHEMA
from gideon.tools.write_file import write_file, WRITE_FILE_SCHEMA
from gideon.tools.run_bash import run_bash, RUN_BASH_SCHEMA
from gideon.tools.edit_file import edit_file, EDIT_FILE_SCHEMA
from gideon.tools.grep_search import grep_search, GREP_SEARCH_SCHEMA
from gideon.tools.read_file_range import read_file_range, READ_FILE_RANGE_SCHEMA
from gideon.tools.move_file import move_file, MOVE_FILE_SCHEMA
from gideon.tools.find_files import find_files, FIND_FILES_SCHEMA

from gideon.config import load_config

TOOLS = [
    READ_FILE_SCHEMA, 
    WRITE_FILE_SCHEMA, 
    LIST_DIRECTORIES_SCHEMA,
    RUN_BASH_SCHEMA, 
    EDIT_FILE_SCHEMA,
    GREP_SEARCH_SCHEMA,
    READ_FILE_RANGE_SCHEMA,
    MOVE_FILE_SCHEMA,
    FIND_FILES_SCHEMA,
]

DESTRUCTIVE_TOOLS = ["write_file", "run_bash", "edit_file", "move_file"]


def get_model() -> str:
    return load_config()["model"]