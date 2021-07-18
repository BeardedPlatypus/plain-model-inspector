from enum import Enum
from lark import Lark, Transformer
from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Interpreter
from pydantic import BaseModel
from typing import Collection, Sequence, Tuple, Any, List, Optional


polyfile_grammar = r"""// Grammar defined for polyfiles:
// Common imports
%import common.INT          -> INT
%import common.SIGNED_FLOAT -> FLOAT
%import common.CNAME        -> CNAME

// Whitespace related rules
WS.-5: (" "|/\t/)+
_WS: WS
CR: /\r/
LF: /\n/
END_OF_LINE: WS? CR? LF
_END_OF_LINE: END_OF_LINE
EMPTY_LINES: END_OF_LINE+

// Description header
COMMENT: /\*.*/
?comment_line: COMMENT _END_OF_LINE
description_header: ( comment_line | EMPTY_LINES )+

// Metadata
NAME.-2: CNAME (WS CNAME)*
name_line.-2: WS? NAME _END_OF_LINE

dimensions_valid: INT _WS INT
dimensions_missing_column: INT
dimensions_exceeding_columns: dimensions_valid (_WS INT)+

dimensions_line: WS? ( dimensions_valid | dimensions_missing_column | dimensions_exceeding_columns ) _END_OF_LINE

metadata: name_line EMPTY_LINES? dimensions_line EMPTY_LINES?

// Points
point.2: _WS? FLOAT _WS FLOAT (_WS FLOAT)* _WS?
point_invalid.2: _WS? FLOAT _WS?

// Note we currently always expect an _END_OF_LINE symbol
// This may or may not be part of the input text, and should
// thus always be appended if it does not exist.
?point_line.2: (point | point_invalid) _END_OF_LINE
points.2: (point_line EMPTY_LINES?)+

// Blocks
poly_block.-1: description_header? metadata points

INVALID_BLOCK.-2: (/.+/ END_OF_LINE?)+
invalid_block.-2: name_line? INVALID_BLOCK

// Whole file
poly_file: EMPTY_LINES? (poly_block | invalid_block )+
"""

class ParseErrorLevel(Enum):
    """ParseErrorLevel defines the possible error levels of ParsingReportItems.
    """
    FATAL = 0
    ERROR = 1
    WARNING = 2
    INFO = 3


class ParseMsg(BaseModel):
    level: ParseErrorLevel
    line: Tuple[int, int]
    column: Tuple[int, int]
    reason: str


class DescriptionHeader(BaseModel):
    content: str


class CommentLine(BaseModel):
    content: str


class Metadata(BaseModel):
    name: str
    n_rows: int
    n_columns: int


class Point(BaseModel):
    x: float
    y: float
    z: Optional[float]
    data: Sequence[float]


# TODO: make sure this is an actual object
class PolyObject(BaseModel):
    description: Optional[DescriptionHeader]
    metadata: Metadata
    points: List[Point]


class TokenData(BaseModel):
    token: Token
    data: Any


def _message_from_tokens(tokens: Sequence[Token], 
                         level: ParseErrorLevel, 
                         reason: str) -> ParseMsg:
    return ParseMsg(level=level,           
                    line=(tokens[0].line,           # type: ignore
                          tokens[-1].end_line),     # type: ignore
                    column=(tokens[0].column,       # type: ignore
                            tokens[-1].end_column), # type: ignore
                    reason=reason)


class PolyFileLiteralTransformer(Transformer):
    """ Transforms the literals of a polyfile to usable objects"""
    def COMMENT(self, token: Token) -> CommentLine:
        # Comments cannot contain errors, as such we directly return the CommentLine
        return CommentLine(content=token[1:].rstrip())

    def EMPTY_LINES(self, token: Token) -> ParseMsg:
        # Empty lines are not permitted by the standard, as such they always return a
        # warning parse message.
        return _message_from_tokens((token,), ParseErrorLevel.WARNING, "Unexpected empty lines will be ignored.")

    def WS(self, token: Token) -> ParseMsg:
        # Non-ignored whitespace is not permitted by the standard, as such it always 
        # returns a warning parse message.
        return _message_from_tokens((token,), ParseErrorLevel.WARNING, "Unexpected empty whitespace will be ignored.")

    def NAME(self, token: Token) -> TokenData: 
        return TokenData(token=token, data=str(token))

    def INT(self, token: Token) -> TokenData:
        return TokenData(token=token, data=int(str(token)))

    def FLOAT(self, token: Token) -> TokenData:
        return TokenData(token=token, data=float(str(token)))


class PolyFileInterpreter(Interpreter):
    """PolyFileInterpreter converts a poly_file tree (given the polyfile_grammar) 
    into the corresponding contents of the polyfile as well as any parse messages.

    Note that the PolyFileInterpreter contains state, and as such a new instance 
    should be created whenever a new object is created. If no new instance is created
    the behaviour is undetermined. Furthermore, we assume that only 'poly_file' trees 
    are fed into this interpreter. Any other trees might lead to undetermined behaviour
    as well.
    """

    def __init__(self, has_z_value: bool=False) -> None:
        super().__init__()
        self._has_z_value = has_z_value
        self._min_n_columns: int = 2 if not has_z_value else 3
        self._expected_n_columns = self._min_n_columns

    @staticmethod
    def _filter_msgs(input: Collection) -> Collection:
        elems = list(x for x in input if not isinstance(x, ParseMsg))
        msgs = list(x for x in input if isinstance(x, ParseMsg))

        return elems, msgs

    def description_header(self, tree: Tree) -> Tuple[DescriptionHeader, Sequence[ParseMsg]]:
        (comments, msgs) = PolyFileInterpreter._filter_msgs(tree.children)

        # Either elements are ParseMsgs or they are CommentLines, due to the grammar
        result: str = "\n".join(elem.content for elem in comments)
        return DescriptionHeader(content=result), msgs

    def metadata(self, tree: Tree) -> Tuple[Metadata, List[ParseMsg]]:
        elems, msgs = PolyFileInterpreter._filter_msgs(tree.children)

        name, name_msgs = self.visit(elems[0])
        ((n_rows, n_columns), dimensions_msgs) = self.visit(elems[1])

        msgs.extend(name_msgs)
        msgs.extend(dimensions_msgs)

        return Metadata(name=name, n_rows=n_rows, n_columns=n_columns), msgs

    def name_line(self, tree: Tree) -> Tuple[str, List[ParseMsg]]:
        elems, msgs = PolyFileInterpreter._filter_msgs(tree.children)
        return elems[0].data, msgs


    def dimensions_line(self, tree: Tree) -> Tuple[Tuple[int, int], List[ParseMsg]]:
        (result, msgs) = self.visit(tree.children[-1]) # type: ignore

        if len(tree.children) > 1:
            # Given the grammar, if more than 1 element exist, it is due
            # to the first element being whitespace.
            msgs.append(_message_from_tokens((tree.children[0].token, ), # type: ignore
                                             ParseErrorLevel.WARNING,
                                             "Whitespace at the beginning of the dimensions is ignored."))

        return result, msgs

    def dimensions_valid(self, tree: Tree) -> Tuple[Tuple[int, int], List[ParseMsg]]:
        # Given the grammar, we know that a valid tree has two children with valid integers.
        msgs: List[ParseMsg] = list()

        # TODO: check if we need validation on the number of points here (lines vs polygons)
        n_rows: int = tree.children[0].data # type: ignore
        n_columns: int = tree.children[1].data # type: ignore

        if n_columns < self._min_n_columns:
            msgs.append(_message_from_tokens((tree.children[1].token, ), # type: ignore
                                             ParseErrorLevel.ERROR, 
                                             "The number of specified columns is smaller than the minimum expected number."))

        return ((n_rows, n_columns), msgs)

    def dimensions_exceeding_columns(self, tree: Tree) -> Tuple[Tuple[int, int], List[ParseMsg]]:
        (result, msgs) = self.visit(tree.children[0]) # type: ignore

        msgs.append(_message_from_tokens((tree.children[1].token, ), # type: ignore
                                         ParseErrorLevel.WARNING, 
                                         "Too many columns specified, the excess columns will be ignored."))

        return (result, msgs)

    def dimensions_missing_column(self, tree: Tree) -> Tuple[Tuple[int, int], List[ParseMsg]]:
        msgs = [ _message_from_tokens((tree.children[0].token,), # type: ignore
                                      ParseErrorLevel.ERROR, 
                                      "Only one dimension is specified, the number of columns will not be validated")
               ]

        n_rows: int = tree.children[0].data # type: ignore

        return ((n_rows, -1), msgs)

    def point(self, tree: Tree) -> Tuple[Optional[Point], List[ParseMsg]]:
        msgs: List[ParseMsg] = list()

        values: List[float] = list(v.data for v in tree.children) # type: ignore
        n_values = len(values)

        if n_values < self._expected_n_columns:
            msgs.append(_message_from_tokens((tree.children[0].token, tree.children[-1].token), # type: ignore
                        ParseErrorLevel.ERROR,
                        "Not as many columns provided as specified, the created point will be missing data."))

        elif n_values > self._expected_n_columns:
            msgs.append(_message_from_tokens((tree.children[0].token, tree.children[-1].token), # type: ignore
                        ParseErrorLevel.ERROR,
                        "Too many columns provided as specified, the created point will contain too much data."))

        z_value = values[2] if self._has_z_value and n_values >= 3 else None
        data = values[self._min_n_columns:]

        return (Point(x=values[0], y=values[1], z=z_value, data=data), msgs)


    def point_invalid(self, tree: Tree) -> Tuple[Optional[Point], List[ParseMsg]]:
        return (None, 
                [ _message_from_tokens((tree.children[0].token, ), # type: ignore
                                       ParseErrorLevel.ERROR,
                                       "No point can be constructed from only a single value, row will be skipped") ])

    def points(self, tree: Tree) -> Tuple[List[Point], List[ParseMsg]]:
        # TODO: add validation for the number of points
        elems, msgs = PolyFileInterpreter._filter_msgs(tree.children)
        points: List[Point] = []

        for e in elems:
            (point, point_msgs) = self.visit(e)

            if point:
                points.append(point)
            if point_msgs:
                msgs.extend(point_msgs)

        return (points, msgs)
        

    def poly_block(self, tree: Tree) -> Tuple[PolyObject, List[ParseMsg]]:
        elems, msgs = PolyFileInterpreter._filter_msgs(tree.children)

        # TODO: set validation values

        components = tuple(self.visit(e) for e in elems)

        # given the grammar, we either have 2 or 3 components, because
        # the description header is optional
        if (len(components) == 3):
            ((description, description_msgs), 
             (metadata, metadata_msgs),
             (points, point_msgs)) = components
        else:
            ((metadata, metadata_msgs),
             (points, point_msgs)) = components
            description= None
            description_msgs = []

        msgs.extend(description_msgs)
        msgs.extend(metadata_msgs)
        msgs.extend(point_msgs)

        return (PolyObject(description=description, 
                           metadata=metadata,
                           points=points),
                msgs)

    def invalid_block(self, tree: Tree):
        # Note: we know that an invalid block only
        # consists of tokens, as such we use this to construct the range
        return _message_from_tokens(tree.children, # type: ignore
                                    ParseErrorLevel.ERROR, 
                                    "Invalid block of data will be ignored.")

    def poly_file(self, tree: Tree):
        """Handle the parsing of a poly file.

        This serves as the entry point of the parsing of whole pol files.

        Args:
            tree (Tree): [description]
        """
        pass