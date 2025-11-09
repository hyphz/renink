
import json
from enum import Enum
from Codeblock import Codeblock
from UnderflowableStack import UnderflowableStack


class InkMode(Enum):
    """Current Ink runtime evaluation mode."""
    CONTENT_MODE = 0
    LOGICAL_EVALUATION_MODE = 1
    STRING_EVALUATION_MODE = 2
    

class LabelMarker:
    """Used in flattening JSON files to handle nested lists."""
    def __init__(self, l):
        self.label = l


class Compiler:
    """Instance of the compiler.

    ink_globals           List of all Ink global variables
       (do we need this? global seems to be default in Renpy?)
    ink_functions         List of Ink defined functions/tunnels and arities
    string_evaluation_no  Number of the buffer used for string evaluation mode
    raw_listdefs          The listDefs member of the file
    ike_value_ordinals    Unique enum values for each Ink list member
    iked_value_ordinals   As above but decorated with the list type


    """

    def __init__(self):
        self.ink_globals = []
        self.ink_functions = dict()
        self.string_evaluation_no = 0
        
    def compile_list_defs(self, listdefs):
        """Goes through the listDefs entry at the root. 'lists' in Ink are actually
        sets of named enums."""
        self.raw_listdefs = listdefs
        self.ike_ordinal = 0
        # Assign a unique ordinal to each enum value of any type, because
        # in Ink they can be blended
        self.ike_value_ordinals = dict()
        self.iked_value_ordinals = dict()
        for (l,d) in listdefs.items():
            self.ink_globals.append(l)
            for value in (d.keys()):
                self.ike_value_ordinals[value] = self.ike_ordinal
                self.iked_value_ordinals[l + "." + value] = self.ike_ordinal
                self.ike_ordinal += 1


    def label_flatten(self, ic):
        """Occasionally a list container will have a sub-list inside it.
        There's no listed semantics for this, so I assume it just runs
        straight on, but potentially has #f and #n members."""
        out = []
        anon_inner_index = 0

        for item in ic:
            anon_inner_index += 1
            if isinstance(item, list):
                sublist = self.label_flatten(item)[:-1]
                if (item[-1]) is not None:
                    if (item[-1].get("#n")) is not None:
                        out.append(LabelMarker(item[-1].get("#n")))
                    else:
                        out.append(LabelMarker(str(anon_inner_index)))
                    # TODO also need to handle flags
                    out += sublist
            else:
                out.append(item)
            
        return out
        
    def compile_list(self, ic, c_name):
        stack = UnderflowableStack()
        code = Codeblock()
        active_globals = []
        active_locals = []
        c = self.label_flatten(ic)
        trivial_sem_length = None
        trivial_sem_string = None

        mode = InkMode.CONTENT_MODE
        for item in c:
            trivial_in_sem= False
            #print(item)
            #code.add("# "+str(item))
            if isinstance(item, list):
                print("LABEL_FLATTEN DIDN'T WORK")
                #print("Nested list..")
                #print(item)
                #(nstack,ncode) = this.doList(item,c_name+"_"+str(nested_list_no))
                #code.concat(ncode)
                #ncode.dump()
                #nested_list_no += 1

            elif isinstance(item, LabelMarker):
                code.add("label "+c_name+"__"+item.label+":")
                
            elif isinstance(item, str):
                
                # Literal string
                if item[0] == "^":
                    # If in output mode, treat as a say
                    if mode == InkMode.CONTENT_MODE:
                        code.add("say \"",item[1:],"\"")
                    elif mode == InkMode.LOGICAL_EVALUATION_MODE:
                        # Otherwise, push on the stack, removing the ^, and in
                        # quotes for Python
                        stack.push("\"item[1:]\"")
                    else:
                        assert mode == InkMode.STRING_EVALUATION_MODE
                        trivial_in_sem = True
                        if trivial_sem_length is not None:
                            trivial_sem_string += item[1:]
                        code.add("_seml" + str(self.string_evaluation_no) + ".append(\"", item[1:], "\")")

                # Number (encoded as a string by JSON)
                elif item.isdigit():
                    # If in output mode, treat as a say
                    if mode == InkMode.CONTENT_MODE:
                        code.add("say \"",item,"\"")
                    elif mode == InkMode.LOGICAL_EVALUATION_MODE:
                        # Otherwise, push on the stack
                        stack.push(str(item))
                    else:
                        assert mode == InkMode.STRING_EVALUATION_MODE
                        trivial_in_sem = True
                        if trivial_sem_length is not None:
                            trivial_sem_string += str(item[1:])
                        code.add("_seml" + str(self.string_evaluation_no) + ".append(\"", item[1:], "\")")

                # No-op        
                elif item == "\n":
                    pass
                
                # Start evaluation mode  
                elif item == "ev":
                    mode = InkMode.LOGICAL_EVALUATION_MODE

                # End evaluation mode
                elif item == "/ev":
                    mode = InkMode.CONTENT_MODE

                # Output in evulation mode    
                elif item == "out":
                    # If in stringbuilder mode, append to string
                    if mode == InkMode.STRING_EVALUATION_MODE:
                        code.add("_seml" + str(self.string_evaluation_no) + ".append(" + str(stack.pop()) + ")")
                    else:
                        # In evaluation mode, output from stack
                        code.add("say",stack.pop())

                # Pop and trash                    
                elif item == "pop":
                    stack.pop()

                # Return from function    
                elif item == "~ret":
                    code.add("return ",stack.pop())

                # Return from tunnel
                elif item == "->->":
                    code.add("return ",stack.pop())

                # Duplicate stack
                elif item == "du":
                    stack.push(stack.peek())

                # Enter string mode
                elif item == "str":
                    mode = InkMode.STRING_EVALUATION_MODE
                    code.add("_seml" + str(self.string_evaluation_no) + " = []")
                    trivial_sem_length = 0
                    trivial_sem_string = ""
                    trivial_in_sem = True

                # End stringbuilder mode
                elif item == "/str":
                    mode = InkMode.LOGICAL_EVALUATION_MODE
                    if trivial_sem_length is None:
                        stack.push("\"\".join(_seml" + str(self.string_evaluation_no) + ")")
                        self.string_evaluation_no += 1
                    else:
                        code.code = code.code[::-trivial_sem_length]
                        code.add("# "+str(trivial_sem_length)+" trivial sem lines compressed")
                        stack.push("\""+trivial_sem_string+"\"")
                        trivial_sem_length = None
                        
                        

                # Non-op
                elif item == "nop":
                    pass
                    
                elif item == "choiceCnt":
                    stack.push("choiceCnt")
                    #print("Push choice count")
                elif item == "turn":
                    stack.push("turnCnt")
                    #print("Push turn count")
                elif item == "turns":
                    stack.push("turnsSince("+stack.pop()+")")
                    #print("Push turns since visited")
                elif item == "visit":
                    stack.push("visits")
                    #print("Push visits this container")
                elif item == "seq":
                    print("Pop elements, push shuffle")
                elif item == "thread":
                    print("Thread")
                elif item == "done":
                    print("End thread")
                elif item == "end":
                    print("End story")
                elif item == "\n":
                    print("Newline")
                elif item == "+":
                    stack.function("inkl_plus",2,True)
                elif item == "-":
                    stack.function("inkl_minus",2,True)
                elif item == "rnd":
                    stack.function("inkl_rand",2,True)
                elif item == "srnd":
                    stack.function("inkl_seed",1,True)
                elif item == "listInt":
                    stack.function("inkl_listInt",2,True)
                elif item == "range":
                    stack.function("inkl_range",3,True)
                elif item == "lrnd":
                    stack.function("random.choice",1,True)
                elif item in ["*","/","%","==",">","<",">=","<=","!="]:
                    stack.dyadic(item)                
                elif item == "?":
                    stack.function("inkl_contains",2,True)
                elif item == "L^":
                    stack.function("inkl_intersect",2,True)
                elif item == "_":
                    stack.prefix("-")
                elif item == "!":
                    stack.prefix("not ")
                elif item == "&&":
                    stack.dyadic("and")
                elif item == "||":
                    stack.dyadic("or")
                elif item == "MIN":
                    stack.function("min",2,True)
                elif item == "MAX":
                    stack.function("max",2,True)
                elif item == "POW":
                    stack.function("math.pow",2,True)
                elif item == "LIST_MIN":
                    stack.postfix("[0]")
                elif item == "void":
                    stack.push("None")
                elif item == "!?":
                    stack.function("not inkl_contains",2,True)
                elif item == "LIST_ALL":
                    pass  # Don't need this in Python
                else:
                    print("Unknown string",item)
                
            elif isinstance(item, dict):
                if "->" in item:
                    if ("c" in item) and (item["c"]):
                        code.add("if " + stack.pop() + ":")
                        code.start_block()
                    if ("var" in item) and (item["var"]):
                        code.add("jump expression ",item["->"])
                    else:
                        code.add("jump ",item["->"])
                    if ("c" in item) and (item["c"]):
                        code.end_block()

                        
                elif ("f()" in item) or ("->t->" in item):
                    if "f()" in item:
                        funcname = item["f()"]
                    else:
                        funcname = item["->t->"]
                    if funcname not in self.ink_functions:
                        print("Call to unknown function",funcname)
                    else:
                        arity = self.ink_functions[funcname]
                        code.add("call ",funcname,"(",(",".join([stack.pop() for _ in range(arity)]))+")")
                                            
                elif "x()" in item:
                    print("External function call:",item["x()"])

                elif "list" in item:
                    if "origins" in item:
                        stack.push("# List with origins " + str(item["origins"]))
                    else:
                        rset = [str(self.iked_value_ordinals[x]) for x in item["list"].keys()]
                        stack.push("["+",".join(rset)+"]")
                    
                elif "VAR=" in item:
                    varname = item["VAR="]
                    code.add(varname,"=",stack.pop())   # Global?
                    if varname not in self.ink_globals:
                        self.ink_globals.append(varname)
                    if varname not in active_globals:
                        active_globals.append(varname)
                        code.prepend("global ",varname)
                elif "temp=" in item:
                    code.add(item["temp="],"=",stack.pop())
                    active_locals.append(item["temp="])
                elif "VAR?" in item:
                    varname = item["VAR?"]
                    if varname in active_locals:
                        varexp = varname
                    elif varname in self.ike_value_ordinals:
                        varexp = str(self.ike_value_ordinals[varname])
                    else:
                        if varname not in active_globals:
                            active_globals.append(varname)
                            code.prepend("global ",varname)
                        varexp = varname
                
                    if mode == InkMode.CONTENT_MODE:
                        code.add("say " + varexp)
                    elif mode == InkMode.LOGICAL_EVALUATION_MODE:
                        stack.push(varexp)
                    else:
                        assert mode == InkMode.STRING_EVALUATION_MODE
                        code.add("_seml.append("+varexp+")")
                        
                elif "CNT?" in item:
                    print("Get reference count of:",item["CNT?"])
                elif "*" in item:
                    flags = item["flg"]
                    if flags & 1:
                        code.add("if ",stack.pop(),":")
                        code.start_block()
                    start = stack.pop() if (flags & 2) else "None"
                    content = stack.pop() if (flags & 4) else "None"
                    code.add("inkl_choicepoint("+start+","+content+","+item["*"]+")")
                    
                    if flags & 1:
                        code.end_block()
                    
                elif "^var" in item:
                    stack.push(item["^var"])
                    #print("Pointer to:",item["^var"])
                elif "^->" in item:
                    print("Scene pointer to:",item["^->"])
                else:
                    print("Probably packed content dict!")
                    print(item)
                    for k in item.keys():
                        self.compile_container(item[k], c_name)
            elif isinstance(item, int):
                if mode == 0:
                    code.add("say \"",str(item),"\"")
                else:
                    # Otherwise, push on the stack
                    stack.push(str(item))
            else:
                print("Unknown type item",item)

            if trivial_sem_length is not None:
                if trivial_in_sem:
                    trivial_sem_length += 1
                else:
                    trivial_sem_length = None
                
                
        return stack,code


    def compile_container(self, c, path):

        real_name = path
         
        # Sometimes in a subcontainer dict, a "container" is just one
        # value. Convert it to a list for ease of parsing.
        if not isinstance(c, list):
            c = [c]
        else:
            # The last member of a list container is meant to be either
            # None, or a dict of subcontainers.
            endm = c.pop()  
            if isinstance(endm, dict):
                if "#n" in endm:
                    real_name = path + "__" + endm["#n"]
                    del endm["#n"]
                if "#f" in endm:
                    flags = endm["#f"]
                    del endm["#f"]
                for subContainer in endm.keys():
                    self.compile_container(endm[subContainer], real_name + "_" + subContainer)
            elif endm is not None:
                print("?? SPEC: Bad container end sentinel",endm)

        # Just to confuse everyone, occasionally a sublist will show up
        # in the code list of a container. This sublist can have a
        # #n and #f, and can also have subcontainers. Get the
        # subcontainers done now.
        anon_inner_index = 0

        for lc in c:
            anon_inner_index += 1
            if isinstance(lc, list):
                lcend = lc[-1]
                inner_name = real_name + "__" + str(anon_inner_index)
                if isinstance(lcend, dict):
                    if "#n" in lcend:
                        inner_name = real_name + "_" + lcend["#n"]
                    for subContainer in lcend.keys():
                        if (subContainer != "#f") and (subContainer != "#n"):
                            self.compile_container(lcend[subContainer], inner_name + "_" + subContainer)

        (stack,code) = self.compile_list(c, real_name)
        # Things were left on stack, probably returns
        
#        if (stack.depth() > 0):
#            leftovers = ",".join(stack.stack[::-1])
#            code.add("return ("+leftovers+")")

        varins = ["x"+str(varin) for varin in range(stack.nextvarin)]

        code.wrap("label " + real_name + "(" + ",".join(varins) + "):")
        code.dump()
        self.ink_functions[real_name] = stack.nextvarin
        

    def compile(self, j):
        if "listDefs" in j:
            self.compile_list_defs(j["listDefs"])
        self.compile_container(j["root"], "")
        
    
        
            
            

with open("test/scene.json") as f:
   j = json.load(f)


print("Ink version: ",j["inkVersion"])

Compiler().compile(j)

