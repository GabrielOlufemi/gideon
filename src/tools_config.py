# tool schema imports (basically static stuff)
from tools.read_file import read_file, READ_FILE_SCHEMA
from tools.list_directories import list_directories, LIST_DIRECTORIES_SCHEMA
from tools.write_file import write_file, WRITE_FILE_SCHEMA
from tools.run_bash import run_bash, RUN_BASH_SCHEMA

MODEL = "google/gemini-2.5-flash"

TOOLS = [
    READ_FILE_SCHEMA, 
    WRITE_FILE_SCHEMA, 
    LIST_DIRECTORIES_SCHEMA,
    RUN_BASH_SCHEMA
]

DESTRUCTIVE_TOOLS = ["write_file", "run_bash"]
