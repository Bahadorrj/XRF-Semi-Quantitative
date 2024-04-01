from dataclasses import dataclass, field
from pathlib import Path

from python.Logic.FileExtension import FileHandler
from python.Types.FileClass import File


@dataclass
class ProjectFile:
    path: str = field(default="None")
    name: str = field(init=False)
    files: list[File] = field(default_factory=list, init=False)

    def __post_init__(self):
        if self.path.endswith(".xdd"):
            self.name = Path(self.path).stem
            self.files = FileHandler.readFiles(self.path)
