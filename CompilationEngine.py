from Shared import TOKEN_TYPE


class CompilationEngine:
    def __init__(self, tokenizer, vm_writer, symbol_table):
        self.tokenizer = tokenizer
        self.symbol_table = symbol_table
        self.vm_writer = vm_writer
        self.level = 0
        self.class_name = None
        self.subroutine_name = None
        self.label_counter = 0

    def compile_keyword(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.KEYWORD:
            raise ValueError("Parse Error: Expected Keyword Token")
        value = self.tokenizer.key_word()
        self.tokenizer.advance()
        return value

    def compile_identifier(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.IDENTIFIER:
            raise ValueError("Parse Error: Expected Identifier Token")
        value = self.tokenizer.identifier()
        self.tokenizer.advance()
        return value

    def compile_symbol(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.SYMBOL:
            raise ValueError("Parse Error: Expected Symbol Token")
        value = self.tokenizer.symbol()
        self.tokenizer.advance()
        return value

    def compile_string_constant(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.STRING_CONST:
            raise ValueError("Parse Error: Expected String Constant Token")
        value = self.tokenizer.string_const()
        self.tokenizer.advance()
        return value

    def compile_integer_constant(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.INT_CONST:
            raise ValueError("Parse Error: Expected Integer Constant Token")
        value = self.tokenizer.int_const()
        self.tokenizer.advance()
        return value

    # Maps to grammar rule: 'class' className '{' classVarDec * subroutineDec * '}'
    def compile_class(self):
        self.compile_keyword()  # 'class'
        self.class_name = self.compile_identifier()  # 'className
        self.compile_symbol()  # '{'

        # classVarDec*
        while self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['static', 'field']:
            self.compile_class_var_dec()

        # subroutineDec*
        while self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['constructor', 'function', 'method']:
            self.compile_subroutine_dec()

        self.compile_symbol()  # '}'

    # Maps to grammar rule: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody

    def compile_subroutine_dec(self):
        # ('constructor' | 'function' | 'method')
        subroutine_type = self.compile_keyword()
        self.symbol_table.start_subroutine()

        # ('void' | type)
        if self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD:
            self.compile_keyword()
        else:
            self.compile_identifier()

        # subroutineName
        self.subroutine_name = self.compile_identifier()

        self.vm_writer.write_comment(f"COMPILING {self.subroutine_name}")

        # '('
        self.compile_symbol()

        # parameterList
        if subroutine_type == "method":
            self.symbol_table.define("this", self.class_name, "arg")
        self.compile_parameter_list()

        # ')'
        self.compile_symbol()

        # subroutineBody
        self.compile_subroutine_body(subroutine_type)

        self.subroutine_name = None
        self.vm_writer.write_empty_line()

    # Maps to to the grammer rule 'int' | 'char' | 'boolean' | className

    def compile_type(self):
        if self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['int', 'char', 'boolean']:
            return self.compile_keyword()
        else:
            return self.compile_identifier()

    # Maps to grammar rule: ('static' | 'field) type varName (',' varName)* ';'
    def compile_class_var_dec(self):
        kind = self.compile_keyword()  # ('static | 'field')
        # type
        type = self.compile_type()
        # varName
        name = self.compile_identifier()
        self.symbol_table.define(name, type, kind)

        # (',' varName)*
        while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in [',']:
            # ','
            self.compile_symbol()
            # varName
            name = self.compile_identifier()
            self.symbol_table.define(name, type, kind)
        # ";"
        self.compile_symbol()

    # Maps to grammar rule: ( (type varName) (',' type varName)* )?
    def compile_parameter_list(self):
        if (self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['int', 'char', 'boolean']) or self.tokenizer.token_type() == TOKEN_TYPE.IDENTIFIER:
            # type
            type = self.compile_type()
            # varName
            name = self.compile_identifier()
            self.symbol_table.define(name, type, 'arg')

            # (',' type varName)*
            while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in [',']:
                # ','
                self.compile_symbol()
                # type
                type = self.compile_type()
                # varName
                name = self.compile_identifier()
                self.symbol_table.define(name, type, 'arg')

    # Maps to grammar rule: '{' varDec* statements '}'
    def compile_subroutine_body(self, subroutine_type):
        # '{'
        self.compile_symbol()

        # varDec*
        while self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() == 'var':
            self.compile_var_dec()

        self.vm_writer.write_function(
            f"{self.class_name}.{self.subroutine_name}", self.symbol_table.var_count('var'))

        if subroutine_type == "constructor":
            no_of_fields = self.symbol_table.var_count('field')
            self.vm_writer.write_push("constant", no_of_fields)
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)
        elif subroutine_type == "method":
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)

        # statements
        self.compile_statements()

        # '}'
        self.compile_symbol()

    # Maps to the grammar rule: 'var' type varName (',' varName)* ';'
    def compile_var_dec(self):
        kind = self.compile_keyword()  # 'var'
        # type
        type = self.compile_type()
        # varName
        name = self.compile_identifier()
        self.symbol_table.define(name, type, kind)

        # (',' varName)*
        while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in [',']:
            # ','
            self.compile_symbol()
            # varName
            name = self.compile_identifier()
            self.symbol_table.define(name, type, kind)
        # ";"
        self.compile_symbol()

    # Maps to the grammar rule: statement*
    def compile_statements(self):
        while self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ["let", "if", "while", "do", "return"]:
            if self.tokenizer.key_word() == "let":
                self.compile_let_statement()
            if self.tokenizer.key_word() == "if":
                self.compile_if_statement()
            if self.tokenizer.key_word() == "while":
                self.compile_while_statement()
            if self.tokenizer.key_word() == "do":
                self.compile_do_statement()
            if self.tokenizer.key_word() == "return":
                self.compile_return_statement()

    # maps to grammar rule 'let' varName ('[' expression ']')? '=' expression';'
    def compile_let_statement(self):
        # 'let'
        self.compile_keyword()
        # varName
        varName = self.compile_identifier()

        # ('[' expression ']')?
        if self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == '[':
            # '['
            self.compile_symbol()
            # expression
            self.compile_expression()
            # ']'
            self.compile_symbol()

        # ' ='
        self.compile_symbol()

        # expression
        self.compile_expression()

        self.vm_writer.write_pop(self.symbol_table.virtual_segment_of(
            varName), self.symbol_table.index_of(varName))

        # ';'
        self.compile_symbol()

    # maps to the grammar rule 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?

    def compile_if_statement(self):
        label_num = self.label_counter
        self.label_counter += 1
        false_label = f"IF_FALSE{label_num}"
        end_label = f"IF_END{label_num}"

        # 'if'
        self.compile_keyword()

        # '('
        self.compile_symbol()

        # expression
        self.compile_expression()
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if_goto(false_label)

        # ')'
        self.compile_symbol()

        # '{'
        self.compile_symbol()

        # statements
        self.compile_statements()
        self.vm_writer.write_goto(end_label)

        # '}'
        self.compile_symbol()

        self.vm_writer.write_label(false_label)
        if self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['else']:
            # else
            self.compile_keyword()
            # '{'
            self.compile_symbol()
            # statements
            self.compile_statements()
            # '}'
            self.compile_symbol()
        self.vm_writer.write_label(end_label)

    # maps to the grammar rule 'while' '(' expression ')' '{' statements '}'
    def compile_while_statement(self):
        label_num = self.label_counter
        self.label_counter += 1
        start_label = f"WHILE_START{label_num}"
        end_label = f"WHILE_END{label_num}"

        # 'while'
        self.compile_keyword()

        # '('
        self.compile_symbol()

        # expression
        self.vm_writer.write_label(start_label)
        self.compile_expression()
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if_goto(end_label)
        # ')'
        self.compile_symbol()

        # "{"
        self.compile_symbol()

        # statements
        self.compile_statements()
        self.vm_writer.write_goto(start_label)

        # "}"
        self.compile_symbol()
        self.vm_writer.write_label(end_label)

    # maps to the grammar rule: 'do' subroutineCall ';'

    def compile_do_statement(self):
        # 'do'
        self.compile_keyword()

        # subroutineCall
        self.compile_term()
        self.vm_writer.write_pop("temp", 0)

        # ';'
        self.compile_symbol()

    # maps to the grammar rule: 'return' expression? ';'
    def compile_return_statement(self):
        # 'return'
        self.compile_keyword()

        # expression?
        if not (self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ';'):
            self.compile_expression()
        else:
            # vm methods always need to push something on top of the stack
            self.vm_writer.write_push("constant", 0)

        self.vm_writer.write_return()
        # ';'
        self.compile_symbol()

    # maps to the grammar statement: term (op term)*
    def compile_expression(self):
        self.compile_term()

        while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
            # op
            operator = self.compile_symbol()
            # term
            self.compile_term()

            if operator == "+":
                self.vm_writer.write_arithmetic("add")
            elif operator == "-":
                self.vm_writer.write_arithmetic("sub")
            elif operator == "*":
                self.vm_writer.write_call("Math.multiply", 2)
            elif operator == "/":
                self.vm_writer.write_call("Math.divide", 2)
            elif operator == "&":
                self.vm_writer.write_arithmetic("and")
            elif operator == "|":
                self.vm_writer.write_arithmetic("or")
            elif operator == "<":
                self.vm_writer.write_arithmetic("lt")
            elif operator == ">":
                self.vm_writer.write_arithmetic("gt")
            elif operator == "=":
                self.vm_writer.write_arithmetic("eq")

    def compile_term(self):
        if self.tokenizer.token_type() == TOKEN_TYPE.INT_CONST:
            value = self.compile_integer_constant()
            self.vm_writer.write_push("constant", value)
        elif self.tokenizer.token_type() == TOKEN_TYPE.STRING_CONST:
            value = self.compile_string_constant()
            length = len(value)
            self.vm_writer.write_push("constant", length)
            self.vm_writer.write_call("String.new", 1)
            for char in value:
                self.vm_writer.write_push('temp', 0)
                self.vm_writer.write_push('constant', ord(char))
                self.vm_writer.write_call('String.appendChar', 2)
                self.vm_writer.write_pop('temp', 0)

        elif self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ["true", "false", "null", "this"]:
            value = self.compile_keyword()
            if value == "true":
                self.vm_writer.write_push("constant", 1)
                self.vm_writer.write_arithmetic("neg")
            if value == "false":
                self.vm_writer.write_push("constant", 0)
            if value == "null":
                self.vm_writer.write_push("constant", 0)
            if value == "this":
                self.vm_writer.write_push("pointer", 0)

        elif self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in ["~", "-"]:
            value = self.compile_symbol()
            self.compile_term()
            if value == "~":
                self.vm_writer.write_arithmetic("not")
            else:
                self.vm_writer.write_arithmetic("neg")

        elif self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == "(":
            self.compile_symbol()
            self.compile_expression()
            self.compile_symbol()

        else:  # TOKEN_TYPE.IDENTIFIER
            identifier = self.compile_identifier()
            # className or varname
            if self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ".":
                self.compile_symbol()
                subroutine_name = self.compile_identifier()
                self.compile_symbol()
                if self.symbol_table.get(identifier):
                    # method call
                    self.vm_writer.write_push(self.symbol_table.virtual_segment_of(
                        identifier), self.symbol_table.index_of(identifier))
                    nArgs = self.compile_expression_list()
                    class_name = self.symbol_table.type_of(identifier)
                    self.vm_writer.write_call(
                        f"{class_name}.{subroutine_name}", nArgs + 1)
                else:
                    nArgs = self.compile_expression_list()
                    self.vm_writer.write_call(
                        f"{identifier}.{subroutine_name}", nArgs)
                self.compile_symbol()

            # Array access, like array[index]
            elif self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == "[":
                self.compile_symbol()
                self.compile_expression()
                self.compile_symbol()

            # Calls methods of the current object
            elif self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == "(":
                self.compile_symbol()
                subroutine_name = identifier
                self.vm_writer.write_push("pointer", 0)
                nArgs = self.compile_expression_list()
                self.vm_writer.write_call(
                    f"{self.class_name}.{subroutine_name}", nArgs + 1)

                self.compile_symbol()
            # varName
            else:
                self.vm_writer.write_push(self.symbol_table.virtual_segment_of(
                    identifier), self.symbol_table.index_of(identifier))

    def compile_expression_list(self):
        nArgs = 0
        if not (self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ")"):
            self.compile_expression()
            nArgs += 1
            while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ",":
                self.compile_symbol()
                self.compile_expression()
                nArgs += 1
        return nArgs
