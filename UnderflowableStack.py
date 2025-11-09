class UnderflowableStack:
    """A simulated stack which tolerates underflow, to detect when arguments
    are popped."""
    def __init__(this):
        this.stack = []
        this.nextvarin = 0

    def push(this,x:str):
        """Pushes the given item onto the stack."""
        this.stack.append(x)

    def pop(this) -> str:
        """Takes an item from the stack, if there is one. If there is not,
        creates an anonymous variable to represent a parameter popped from
        the deeper stack, returns that."""
        if len(this.stack) > 0:
            return this.stack.pop()
        else:
            this.nextvarin += 1
            return "x" + str(this.nextvarin - 1)

    def peek(this) -> str:
        """Returns the top of the stack without removing it."""
        return this.stack[-1]

    def depth(this) -> int:
        """Returns the depth of the stack."""
        return len(this.stack)

    def dyadic(this,op:str):
        """Performs a dyadic operator on the top elements of the stack."""
        b = this.pop()
        a = this.pop()
        this.push("(" + a + " " + op + " " + b + ")")

    def cidayd(this,op:str):
        """Performs a dyadic operator with arguments reversed on the top
        elements of the stack."""
        b = this.pop()
        a = this.pop()
        this.push("(" + b + " " + op + " " + a + ")")

    def prefix(this,op:str):
        """Performs a prefix operator on the top element of the stack."""
        a = this.pop()
        this.push("("+op+a+")")

    def postfix(this,op:str):
        """Performs a postfix operator on the top element of the stack."""
        a = this.pop()
        this.push("("+a+op+")")

    def function(this,f:str,arity=1,rev=False):
        """Performs a function call on the top element(s) of the stack."""
        args = []
        for arg in range(arity):
            args.append(this.pop())
        if rev:
            args = args[::-1]
        this.push(f+"("+",".join(args)+")")
