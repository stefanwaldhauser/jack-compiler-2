
'''
When compiling Jack code, the compiler can easily determine which symbol table to check:

First check the subroutine table for local variables
If not found, check the class table for fields/static variables

'''


class SymbolTable:
    def __init__(self):
        # name -> (type, kind, #)
        self.class_scope = {}
        self.class_counts = {
            'static': 0,
            'field': 0
        }

        # name -> (type, kind, #)
        self.subroutine_scope = {}
        self.subroutine_counts = {
            'arg': 0,
            'var': 0
        }

    def start_subroutine(self):
        self.subroutine_scope = {}
        self.subroutine_counts = {
            'arg': 0,
            'var': 0
        }

    def define(self, name, type, kind):
        # class scope
        if kind in ['static', 'field']:
            self.class_scope[name] = (type, kind, self.class_counts[kind])
            self.class_counts[kind] += 1
        else:  # subroutine scope
            self.subroutine_scope[name] = (
                type, kind, self.subroutine_counts[kind])
            self.subroutine_counts[kind] += 1

    def var_count(self, kind):
        # class scope
        if kind in ['static', 'field']:
            return self.class_counts[kind]
        else:  # subroutine scope
            return self.subroutine_scope[kind]

    def get(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]
        if name in self.class_scope:
            return self.class_scope[name]
        return None

    def kind_of(self, name):
        symbol = self.get(name)
        return symbol[1] if symbol else None

    def type_of(self, name):
        symbol = self.get(name)
        return symbol[0] if symbol else None

    def index_of(self, name):
        symbol = self.get(name)
        return symbol[2] if symbol else None
