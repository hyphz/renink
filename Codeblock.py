from typing import Iterable


class Codeblock:
    """A block of Python/Ren'py code for output."""

    def __init__(self):
        self.code = []
        self.indent_level = 0

    def add(self, *args:Iterable[str]):
        """Add the code as a single statement to the block."""
        ins = "".join(args)
        ins = ("\t" * self.indent_level) + ins
        self.code.append(ins)

    def start_block(self):
        """Start an indented block."""
        self.indent_level += 1

    def end_block(self):
        """End an indented block."""
        self.indent_level -= 1

    def retro_indent(self):
        """Retroactively indent all code in this block."""
        self.code = ["\t" + x for x in self.code]

    def wrap(self, *args:Iterable[str]):
        """Place the given code at the top of the block, with everything else indented beneath it."""
        ins = "".join(args)
        ins = ("\t" * self.indent_level) + ins
        self.retro_indent()
        self.code.insert(0, ins)

    def prepend(self, *args:Iterable[str]):
        """Place the given code at the top of the block."""
        ins = "".join(args)
        ins = ("\t" * self.indent_level) + ins
        self.code.insert(0, ins)

    def dump(self):
        """Output the block."""
        for line in self.code:
            print(line)

    def concat(self, rest):
        self.code = self.code + rest.code
