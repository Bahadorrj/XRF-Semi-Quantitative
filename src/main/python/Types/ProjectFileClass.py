from dataclasses import dataclass, field
from pathlib import Path
from python.Types.FileClass import File
from python.Logic.FileExtension import FileHandler

@dataclass
class ProjectFile:
    path: str
    name: str = field(init=False)
    files: list[File] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.name = Path(self.path).stem
        self.files = FileHandler.readFiles(self.path)
