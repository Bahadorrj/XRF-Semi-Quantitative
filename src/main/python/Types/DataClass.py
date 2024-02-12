from dataclasses import dataclass, field


@dataclass(order=True)
class Data:
    labels: list[str] = field(default_factory=list, init=False)
    values: list[str] = field(default_factory=list, init=False)

    def getAttribute(self, attribute: str):
        index = self.labels.index(attribute)
        return self.values[index]

    def getName(self):
        return self.getAttribute("name")
