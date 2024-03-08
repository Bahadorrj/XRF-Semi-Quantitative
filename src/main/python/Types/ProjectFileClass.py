from dataclasses import dataclass, field
from src.main.python.Types.FileClass import File
from src.main.python.Logic.FileExtension import FileHandler

@dataclass
class ProjectFile:
    path: str
    files: list[File] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.files = FileHandler.readFiles(self.path)
