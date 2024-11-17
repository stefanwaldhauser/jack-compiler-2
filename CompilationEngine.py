from Shared import TOKEN_TYPE


class CompilationEngine:
    def __init__(self, tokenizer, file, symbol_table):
        self.tokenizer = tokenizer
        self.symbol_table = symbol_table
        self.file = file
        self.level = 0
        self.class_name = ""

    def write_indent(self):
        for _ in range(self.level):
            self.file.write(" ")

    def write_new_line(self):
        self.file.write("\n")

    def write_inline_tag(self, tag, value, attributes=None):
        self.write_indent()
        if attributes:
            to_write = f"<{tag}"
            for k, v in attributes:
                to_write += f" {k}={v}"
            to_write += f">{value}</{tag}>\n"
            self.file.write(to_write)
        else:
            self.file.write(f"<{tag}>{value}</{tag}>\n")

    def write_open_tag(self, tag):
        self.write_indent()
        self.file.write(f"<{tag}>\n")
        self.level = self.level + 1

    def write_close_tag(self, tag):
        self.level = self.level - 1
        self.write_indent()
        self.file.write(f"</{tag}>\n")

    def compile_keyword(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.KEYWORD:
            raise ValueError("Parse Error: Expected Keyword Token")
        value = self.tokenizer.key_word()
        self.write_inline_tag("keyword", value)
        self.tokenizer.advance()
        return value

    def compile_identifier(self, type=None, kind=None, usage=None):
        if self.tokenizer.token_type() != TOKEN_TYPE.IDENTIFIER:
            raise ValueError("Parse Error: Expected Identifier Token")
        value = self.tokenizer.identifier()

        if usage:
            if usage == "defined":
                self.symbol_table.define(value, type, kind)
            self.write_inline_tag("identifier", value, [
                                  ("usage", usage),
                                  ("type", self.symbol_table.type_of(value)),
                                  ("kind", self.symbol_table.kind_of(value)),
                                  ("index", self.symbol_table.index_of(value))])
        else:
            self.write_inline_tag("identifier", value)

        self.tokenizer.advance()
        return value

    def compile_symbol(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.SYMBOL:
            raise ValueError("Parse Error: Expected Symbol Token")
        value = self.tokenizer.symbol()
        self.write_inline_tag("symbol", value)
        self.tokenizer.advance()

    def compile_string_constant(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.STRING_CONST:
            raise ValueError("Parse Error: Expected String Constant Token")
        value = self.tokenizer.string_const()
        self.write_inline_tag("stringConstant", value)
        self.tokenizer.advance()

    def compile_integer_constant(self):
        if self.tokenizer.token_type() != TOKEN_TYPE.INT_CONST:
            raise ValueError("Parse Error: Expected Integer Constant Token")
        value = self.tokenizer.int_const()
        self.write_inline_tag("integerConstant", value)
        self.tokenizer.advance()

    # Maps to grammar rule: 'class' className '{' classVarDec * subroutineDec * '}'
    def compile_class(self):
        self.write_open_tag("class")
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
        self.write_close_tag("class")

    # Maps to grammar rule: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody

    def compile_subroutine_dec(self):
        self.write_open_tag("subroutineDec")
        # ('constructor' | 'function' | 'method')
        subroutine_type = self.compile_keyword()
        self.symbol_table.start_subroutine()
        
        if subroutine_type == "method":
            self.symbol_table.define("this", self.class_name, "arg")

        # ('void' | type)
        if self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD:
            self.compile_keyword()
        else:
            self.compile_identifier()

        # subroutineName
        self.compile_identifier()

        # '('
        self.compile_symbol()

        # parameterList
        self.compile_parameter_list()

        # ')'
        self.compile_symbol()

        # subroutineBody
        self.compile_subroutine_body()

        self.write_close_tag("subroutineDec")

    # Maps to to the grammer rule 'int' | 'char' | 'boolean' | className
    def compile_type(self):
        if self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['int', 'char', 'boolean']:
            return self.compile_keyword()
        else:
            return self.compile_identifier()

    # Maps to grammar rule: ('static' | 'field) type varName (',' varName)* ';'
    def compile_class_var_dec(self):
        self.write_open_tag("classVarDec")
        kind = self.compile_keyword()  # ('static | 'field')
        # type
        type = self.compile_type()
        # varName
        self.compile_identifier(type, kind, "defined")
        # (',' varName)*
        while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in [',']:
            # ','
            self.compile_symbol()
            # varName
            self.compile_identifier(type, kind, "defined")
        # ";"
        self.compile_symbol()
        self.write_close_tag("classVarDec")

    # Maps to grammar rule: ( (type varName) (',' type varName)* )?
    def compile_parameter_list(self):
        self.write_open_tag("parameterList")
        if (self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['int', 'char', 'boolean']) or self.tokenizer.token_type() == TOKEN_TYPE.IDENTIFIER:
            # type
            type = self.compile_type()
            # varName
            self.compile_identifier(type, 'arg', "defined")
            # (',' type varName)*
            while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in [',']:
                # ','
                self.compile_symbol()
                # type
                type = self.compile_type()
                # varName
                self.compile_identifier(type, 'arg', "defined")
        self.write_close_tag("parameterList")

    # Maps to grammar rule: '{' varDec* statements '}'
    def compile_subroutine_body(self):
        self.write_open_tag("subroutineBody")
        # '{'
        self.compile_symbol()

        # varDec*
        while self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['var']:
            self.compile_var_dec()

        # statements
        self.compile_statements()

        # '}'
        self.compile_symbol()

        self.write_close_tag("subroutineBody")

    # Maps to the grammar rule: 'var' type varName (',' varName)* ';'
    def compile_var_dec(self):
        self.write_open_tag("varDec")
        kind = self.compile_keyword()  # 'var'
        # type
        type = self.compile_type()
        # varName
        self.compile_identifier(type, kind, "defined")
        # (',' varName)*
        while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in [',']:
            # ','
            self.compile_symbol()
            # varName
            self.compile_identifier(type, kind, "defined")
        # ";"
        self.compile_symbol()
        self.write_close_tag("varDec")

    # Maps to the grammar rule: statement*
    def compile_statements(self):
        self.write_open_tag("statements")
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

        self.write_close_tag("statements")

    # maps to grammar rule 'let' varName ('[' expression ']')? '=' expression';'
    def compile_let_statement(self):
        self.write_open_tag("letStatement")
        # 'let'
        self.compile_keyword()
        # varName
        self.compile_identifier(usage="used")

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

        # ';'
        self.compile_symbol()

        self.write_close_tag("letStatement")

    # maps to the grammar rule 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
    def compile_if_statement(self):
        self.write_open_tag("ifStatement")

        # 'if'
        self.compile_keyword()

        # '('
        self.compile_symbol()

        # expression
        self.compile_expression()

        # ')'
        self.compile_symbol()

        # '{'
        self.compile_symbol()

        # statements
        self.compile_statements()

        # '}'
        self.compile_symbol()

        if self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ['else']:
            # else
            self.compile_keyword()
            # '{'
            self.compile_symbol()
            # statements
            self.compile_statements()
            # '}'
            self.compile_symbol()

        self.write_close_tag("ifStatement")

    # maps to the grammar rule 'while' '(' expression ')' '{' statements '}'
    def compile_while_statement(self):
        self.write_open_tag("whileStatement")
        # 'while'
        self.compile_keyword()

        # '('
        self.compile_symbol()

        # expression

        self.compile_expression()

        # ')'
        self.compile_symbol()

        # "{"
        self.compile_symbol()

        # statements
        self.compile_statements()

        # "}"
        self.compile_symbol()

        self.write_close_tag("whileStatement")

    # maps to the grammar rule: 'do' subroutineCall ';'
    def compile_do_statement(self):
        self.write_open_tag("doStatement")
        # 'do'
        self.compile_keyword()

        # subroutineCall
        self.handle_term()

        # ';'
        self.compile_symbol()
        self.write_close_tag("doStatement")

    # maps to the grammar rule: 'return' expression? ';'
    def compile_return_statement(self):
        self.write_open_tag("returnStatement")
        # 'return'
        self.compile_keyword()

        # expression?
        if not (self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ';'):
            self.compile_expression()

        # ';'
        self.compile_symbol()
        self.write_close_tag("returnStatement")

    # maps to the grammar statement: term (op term)*
    def compile_expression(self):
        self.write_open_tag("expression")
        self.compile_term()

        while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in ["+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "="]:
            # op
            self.compile_symbol()
            # term
            self.compile_term()

        self.write_close_tag("expression")

    def compile_term(self):
        self.write_open_tag("term")
        self.handle_term()

        self.write_close_tag("term")

    def handle_term(self):
        if self.tokenizer.token_type() == TOKEN_TYPE.INT_CONST:
            self.compile_integer_constant()
        elif self.tokenizer.token_type() == TOKEN_TYPE.STRING_CONST:
            self.compile_string_constant()
        elif self.tokenizer.token_type() == TOKEN_TYPE.KEYWORD and self.tokenizer.key_word() in ["true", "false", "null", "this"]:
            self.compile_keyword()
        elif self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() in ["~", "-"]:
            self.compile_symbol()
            self.compile_term()
        elif self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == "(":
            self.compile_symbol()
            self.compile_expression()
            self.compile_symbol()
        else:  # TOKEN_TYPE.IDENTIFIER
            self.compile_identifier(usage="used")
            if self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ".":
                self.compile_symbol()
                self.compile_identifier()
                self.compile_symbol()
                self.compile_expression_list()
                self.compile_symbol()

            if self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == "[":
                self.compile_symbol()
                self.compile_expression()
                self.compile_symbol()

            if self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == "(":
                self.compile_symbol()
                self.compile_expression_list()
                self.compile_symbol()

    def compile_expression_list(self):
        self.write_open_tag("expressionList")

        if not (self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ")"):
            self.compile_expression()
            while self.tokenizer.token_type() == TOKEN_TYPE.SYMBOL and self.tokenizer.symbol() == ",":
                self.compile_symbol()
                self.compile_expression()

        self.write_close_tag("expressionList")
