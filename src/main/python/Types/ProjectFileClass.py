from dataclasses import dataclass, field

from python.Types.FileClass import File


@dataclass
class ProjectFile:
    name: str
    files: list[File] = field(default_factory=list, init=False)
