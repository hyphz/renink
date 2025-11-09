class UnderflowableStack:
    """A simulated stack which tolerates underflow, to detect when arguments
    are popped."""
    def __init__(self):
        self.stack = []
        self.nextvarin = 0

    def push(self, x:str):
        """Pushes the given item onto the stack."""
        self.stack.append(x)

    def pop(self) -> str:
        """Takes an item from the stack, if there is one. If there is not,
        creates an anonymous variable to represent a parameter popped from
        the deeper stack, returns that."""
        if len(self.stack) > 0:
            return self.stack.pop()
        else:
            self.nextvarin += 1
            return "x" + str(self.nextvarin - 1)

    def peek(self) -> str:
        """Returns the top of the stack without removing it."""
        return self.stack[-1]

    def depth(self) -> int:
        """Returns the depth of the stack."""
        return len(self.stack)

    def dyadic(self, op:str):
        """Performs a dyadic operator on the top elements of the stack."""
        b = self.pop()
        a = self.pop()
        self.push("(" + a + " " + op + " " + b + ")")

    def cidayd(self, op:str):
        """Performs a dyadic operator with arguments reversed on the top
        elements of the stack."""
        b = self.pop()
        a = self.pop()
        self.push("(" + b + " " + op + " " + a + ")")

    def prefix(self, op:str):
        """Performs a prefix operator on the top element of the stack."""
        a = self.pop()
        self.push("(" + op + a + ")")

    def postfix(self, op:str):
        """Performs a postfix operator on the top element of the stack."""
        a = self.pop()
        self.push("(" + a + op + ")")

    def function(self, f:str, arity=1, rev=False):
        """Performs a function call on the top element(s) of the stack."""
        args = []
        for arg in range(arity):
            args.append(self.pop())
        if rev:
            args = args[::-1]
        self.push(f + "(" + ",".join(args) + ")")
