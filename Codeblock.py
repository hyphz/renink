class Codeblock:
    """A block of Python/Ren'py code for output."""

    def __init__(this):
        this.code = []
        this.indent_level = 0

    def add(this, *args:list[str]):
        """Add the code as a single statement to the block."""
        ins = "".join(args)
        ins = ("\t"*this.indent_level) + ins
        this.code.append(ins)

    def start_block(this):
        """Start an indented block."""
        this.indent_level += 1

    def end_block(this):
        """End an indented block."""
        this.indent_level -= 1

    def retro_indent(this):
        """Retroactively indent all code in this block."""
        this.code = ["\t"+x for x in this.code]

    def wrap(this, *args:list[str]):
        """Place the given code at the top of the block, with everything else indented beneath it."""
        ins = "".join(args)
        ins = ("\t"*this.indent_level) + ins
        this.retro_indent()
        this.code.insert(0,ins)

    def prepend(this, *args:list[str]):
        """Place the given code at the top of the block."""
        ins = "".join(args)
        ins = ("\t"*this.indent_level) + ins
        this.code.insert(0,ins)

    def dump(this):
        """Output the block."""
        for line in this.code:
            print(line)

    def concat(this,rest):
        this.code = this.code + rest.code
