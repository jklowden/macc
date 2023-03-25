#! /usr/bin/python3
from __future__ import print_function

import sys, os, getopt, re, copy 
from pycparser import c_parser, c_generator, c_ast, parse_file

class meta_struct_elem:
    def __init__(self, cname, ctype, csize):
        self.cname = cname
        self.ctype = ctype
        self.csize = csize
    
class meta_struct:
    def __init__(self, node):
        if not isinstance(node, c_ast.Struct):
            print("logic error: not a Struct", file=sys.stderr);
            return
        self.name = node.name
        self.elems = []
        for (_, decl) in node.children():
            csize = 0
            if isinstance(decl.type, c_ast.ArrayDecl):
                cname = decl.type.type.declname
                ctype = decl.type.type.type.names[0]
                csize = int(decl.type.dim.value)
            if isinstance(decl.type, c_ast.TypeDecl):
                cname = decl.type.declname
                ctype = decl.type.type.names[0]
            elem = meta_struct_elem( cname, 
                                     ctype,
                                     csize )
            self.elems.append(elem)

# A visitor to collect struct definitions. 
class StructVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.parsed_structs = {}

    def visit_Struct(self, node):
        if node.decls:
            meta = meta_struct(node)
            self.parsed_structs[node.name] = meta
        super().generic_visit(node)

# A visitor to to apply macros.
class ApplyMacros(c_ast.NodeVisitor):
    def __init__(self, parsed_structs, macros):
        self.parsed_structs = parsed_structs
        self.macros = macros

    def apply_macro(self, node, function):
        name = node.type.declname
        params = node.children()[0][1].params
        args = [ p.name for p in params ]
        tgt_type = node.args.params[1].type.type.type.name
        struct = self.parsed_structs[ tgt_type ]
        return function(struct, *args)

    def visit_Decl(self, node):
        if node.name in self.macros.keys():
            node.type = self.apply_macro(node.type, self.macros[node.name])
            print("matched macro to FuncDecl %s" % (node.name), file=sys.stderr)

def parse(astfile, macros, input):
    parser = c_parser.CParser()
    ast = parser.parse(input)

    # Collect stucture definitions. 
    v = StructVisitor()
    v.visit(ast)

    # Apply macros
    v = ApplyMacros(v.parsed_structs, macros)
    v.visit(ast)


    # Brutally remove all top-level typedefs
    a = []
    for node in ast.ext:
        if not isinstance(node, c_ast.Typedef):
            a.append(node)
    ast.ext = a

    if astfile:
        with open(astfile, 'w') as f:
            ast.show(buf=f, attrnames=True, nodenames=False)
    
    print(c_generator.CGenerator().visit(ast))

def process(astfile, macros, srcfile):
    with open(srcfile, 'r') as f:
        parse(astfile, macros, f.read())
    

__doc__ = """
syntax: 
"""

from importlib import import_module

def main( argv=None ):
    if argv is None:
        argv = sys.argv
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:hm:", ["help"])
    except getopt.error as msg:
        print(msg)
        print("for help use --help")
        sys.exit(2)

    # process options
    astfile = None
    macros = {}
    
    for opt, arg in opts:
        if opt == '-a':
            astfile = arg
        if opt in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        if opt == '-m':
            m = import_module(arg)
            for name, mac in m.macros.items():
                macros[name] = mac

    # process arguments
    if not args:
        args = ('/dev/stdin',)

    for ifile, arg in enumerate(args):
        process(astfile, macros, arg)

if __name__ == "__main__":
    sys.exit(main())
