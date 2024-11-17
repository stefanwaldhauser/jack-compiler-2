from enum import Enum

jack_symbols = [
    "{", "}", "(", ")", "[", "]", ".", ",", ";", "+",
    "-", "*", "/", "&", "|", "<", ">", "=", "~"
]


class TOKEN_TYPE(Enum):
    KEYWORD = 1
    SYMBOL = 2
    IDENTIFIER = 3
    INT_CONST = 4
    STRING_CONST = 5


class KEYWORD(Enum):
    CLASS = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    INT = 5
    BOOLEAN = 6
    CHAR = 7
    VOID = 8
    VAR = 9
    STATIC = 10
    FIELD = 11
    LET = 12
    DO = 13
    IF = 14
    ELSE = 15
    WHILE = 16
    RETURN = 17
    TRUE = 18
    FALSE = 19
    NULL = 20
    THIS = 21


keyword_str_to_constant = {item.name.lower(): item.name for item in KEYWORD}

token_type_to_xml_tag = {
    TOKEN_TYPE.KEYWORD: "keyword",
    TOKEN_TYPE.SYMBOL: "symbol",
    TOKEN_TYPE.IDENTIFIER: "identifier",
    TOKEN_TYPE.INT_CONST: "integerConstant",
    TOKEN_TYPE.STRING_CONST: "stringConstant"
}
