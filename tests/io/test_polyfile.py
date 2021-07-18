from lark import Lark
from plain_model_inspector.io.polyfile import PolyFileInterpreter, PolyFileLiteralTransformer, polyfile_grammar


def test_description_header_is_tokenized_correctly():
    description_header1 = r"""* some value           
* another value      
    
        
* last value

"""
    
    parser = Lark(polyfile_grammar, 
                  start='description_header',
                  parser='lalr')
    result = parser.parse(description_header1)

    assert result is not None
    assert len(result.children) == 5
    assert result.children[0].type == 'COMMENT' # type: ignore
    assert result.children[1].type == 'COMMENT' # type: ignore
    assert result.children[2].type == 'EMPTY_LINES'  # type: ignore
    assert result.children[3].type == 'COMMENT' # type: ignore
    assert result.children[4].type == 'EMPTY_LINES'  # type: ignore


def test_name_is_tokenized_correctly():
    name = "some name with spaces\n"

    parser = Lark(polyfile_grammar, 
                  start='name_line',
                  parser='lalr')
    result = parser.parse(name)

    assert result is not None
    assert result.type == "NAME" # type: ignore
    assert result == "some name with spaces"


def test_valid_dimensions_are_tokenized_correctly():
    name = "5    23\n"

    parser = Lark(polyfile_grammar, 
                  start='dimensions_line',
                  parser='lalr')
    result = parser.parse(name)

    assert result is not None
    assert result.data == "dimensions_line" # type: ignore
    assert len(result.children) == 1        # type: ignore

    assert result.children[0].data == "dimensions_valid" # type: ignore
    assert len(result.children[0].children) == 2         # type: ignore
    assert result.children[0].children[0] == "5"         # type: ignore
    assert result.children[0].children[1] == "23"        # type: ignore


def test_valid_dimensions_with_whitespace_are_tokenized_correctly():
    name = "      5    23\n"

    parser = Lark(polyfile_grammar, 
                  start='dimensions_line',
                  parser='lalr')
    result = parser.parse(name)

    assert result is not None
    assert result.data == "dimensions_line" # type: ignore
    assert len(result.children) == 2        # type: ignore
    
    assert result.children[0].type == "WS" # type: ignore

    assert result.children[1].data == "dimensions_valid" # type: ignore
    assert len(result.children[1].children) == 2         # type: ignore
    assert result.children[1].children[0] == "5"         # type: ignore
    assert result.children[1].children[1] == "23"        # type: ignore


def test_invalid_dimensions_with_too_few_columns_are_tokenized_correctly():
    name = "5\n"

    parser = Lark(polyfile_grammar, 
                  start='dimensions_line',
                  parser='lalr')
    result = parser.parse(name)

    assert result is not None
    assert result.data == "dimensions_line" # type: ignore
    assert len(result.children) == 1        # type: ignore

    assert result.children[0].data == "dimensions_missing_column" # type: ignore
    assert len(result.children[0].children) == 1                  # type: ignore
    assert result.children[0].children[0] == "5"                  # type: ignore


def test_invalid_dimensions_with_too_many_columns_are_tokenized_correctly():
    name = "5 12 18\n"

    parser = Lark(polyfile_grammar, 
                  start='dimensions_line',
                  parser='lalr')
    result = parser.parse(name)

    assert result is not None
    assert result.data == "dimensions_line" # type: ignore
    assert len(result.children) == 1        # type: ignore

    assert result.children[0].data == "dimensions_exceeding_columns" # type: ignore
    assert len(result.children[0].children) == 2                     # type: ignore
    assert result.children[0].children[0].data == "dimensions_valid" # type: ignore
    assert result.children[0].children[0].children[0] == "5"         # type: ignore
    assert result.children[0].children[0].children[1] == "12"        # type: ignore
    assert result.children[0].children[1] == "18"                    # type: ignore


def test_metadata_is_tokenized_correctly():
    metadata = """this is a name  
5    23
"""

    parser = Lark(polyfile_grammar, 
                  start='metadata',
                  parser='lalr')
    result = parser.parse(metadata)

    assert result is not None
    assert len(result.children) == 2
    assert result.data == "metadata"                     # type: ignore

    assert result.children[0].data == "name_line"        # type: ignore
    assert len(result.children[0].children) == 1         # type: ignore
    assert result.children[0].children[0].type == "NAME" # type: ignore

    assert len(result.children[1].children) == 1                     # type: ignore
    assert result.children[1].children[0].data == "dimensions_valid" # type: ignore
    assert len(result.children[1].children[0].children) == 2         # type: ignore
    assert result.children[1].children[0].children[0] == "5"         # type: ignore
    assert result.children[1].children[0].children[1] == "23"        # type: ignore


def test_point_is_tokenized_correctly():
    point = "   1.0  2.0  3.0 "


    parser = Lark(polyfile_grammar, 
                  start='point',
                  parser='lalr')
    result = parser.parse(point)

    assert result is not None
    assert result.data == "point"
    assert len(result.children) == 3
    assert result.children[0] == "1.0"
    assert result.children[1] == "2.0"
    assert result.children[2] == "3.0"


def test_point_line_is_tokenized_correctly():
    point = "   1.0  2.0  3.0   \n"

    parser = Lark(polyfile_grammar, 
                  start='point_line',
                  parser='lalr')
    result = parser.parse(point)

    assert result is not None
    assert result.data == "point"
    assert len(result.children) == 3
    assert result.children[0] == "1.0"
    assert result.children[1] == "2.0"
    assert result.children[2] == "3.0"


def test_invalid_point_line_is_tokenized_correctly():
    point = "   1.0     \n"

    parser = Lark(polyfile_grammar, 
                  start='point_line',
                  parser='lalr')
    result = parser.parse(point)

    assert result is not None
    assert result.data == "point_invalid"
    assert len(result.children) == 1
    assert result.children[0] == "1.0"


def test_points_is_tokenized_correctly():
    point = """    1.0  2.0  3.0   
    4.0  5.0  6.0    


    7.0  8.0  9.0   
"""

    parser = Lark(polyfile_grammar, 
                  start='points',
                  parser='lalr')
    result = parser.parse(point)

    assert result is not None
    assert result.data == "points"
    assert len(result.children) == 4
    assert result.children[0].data == "point"       # type: ignore
    assert result.children[0].children[0] == "1.0"  # type: ignore
    assert result.children[0].children[1] == "2.0"  # type: ignore
    assert result.children[0].children[2] == "3.0"  # type: ignore
    assert result.children[1].data == "point"       # type: ignore
    assert result.children[1].children[0] == "4.0"  # type: ignore
    assert result.children[1].children[1] == "5.0"  # type: ignore
    assert result.children[1].children[2] == "6.0"  # type: ignore
    assert result.children[2].type == "EMPTY_LINES" # type: ignore
    assert result.children[3].data == "point"       # type: ignore
    assert result.children[3].children[0] == "7.0"  # type: ignore
    assert result.children[3].children[1] == "8.0"  # type: ignore
    assert result.children[3].children[2] == "9.0"  # type: ignore


def test_polyblock_is_tokenized_correctly():
    point = """* Some description header
this is a name  
5    23
    1.0  2.0  3.0   
    4.0  5.0  6.0    


    7.0  8.0  9.0   
"""

    parser = Lark(polyfile_grammar, 
                  start='poly_block',
                  parser='lalr')
    result = parser.parse(point)

    assert result is not None
    assert result.data == "poly_block"
    assert len(result.children) == 3

    # Assert correct description header
    assert result.children[0].data == 'description_header'               # type: ignore
    assert result.children[0].children[0].type == 'COMMENT'              # type: ignore
    assert result.children[0].children[0] == '* Some description header' # type: ignore

    # Assert correct metadata
    assert len(result.children[1].children) == 2               # type: ignore
    assert result.children[1].data == "metadata"               # type: ignore
    assert result.children[1].children[0].data == "name_line"       # type: ignore
    assert result.children[1].children[0].children[0].type == "NAME"       # type: ignore

    assert result.children[1].children[1].data == "dimensions_line" # type: ignore
    assert result.children[1].children[1].children[0].data == "dimensions_valid" # type: ignore
    assert len(result.children[1].children[1].children[0].children) == 2   # type: ignore
    assert result.children[1].children[1].children[0].children[0] == "5"   # type: ignore
    assert result.children[1].children[1].children[0].children[1] == "23"  # type: ignore

    # Assert correct points
    assert result.children[2].data == "points"                  # type: ignore
    assert result.children[2].children[0].data == "point"       # type: ignore
    assert result.children[2].children[0].children[0] == "1.0"  # type: ignore
    assert result.children[2].children[0].children[1] == "2.0"  # type: ignore
    assert result.children[2].children[0].children[2] == "3.0"  # type: ignore
    assert result.children[2].children[1].data == "point"       # type: ignore
    assert result.children[2].children[1].children[0] == "4.0"  # type: ignore
    assert result.children[2].children[1].children[1] == "5.0"  # type: ignore
    assert result.children[2].children[1].children[2] == "6.0"  # type: ignore
    assert result.children[2].children[2].type == "EMPTY_LINES" # type: ignore
    assert result.children[2].children[3].data == "point"       # type: ignore
    assert result.children[2].children[3].children[0] == "7.0"  # type: ignore
    assert result.children[2].children[3].children[1] == "8.0"  # type: ignore
    assert result.children[2].children[3].children[2] == "9.0"  # type: ignore


def test_poly_file_is_tokenized_correctly():
    point = """* Some description header
this is a name  
5    23
    1.0  2.0  3.0
    4.0  5.0  6.0


    7.0  8.0  9.0

// should not put comments here

this is a different name  
6    15
    6.0  5.0  2.0   
    3.0  2.0  1.0    


    9.0  8.0  7.0

woo this should be an invalid block
because this should not exist.
"""

    parser = Lark(polyfile_grammar, 
                  start='poly_file',
                  lexer='contextual',
                  parser='lalr')
    result = parser.parse(point)

    assert result is not None
    assert result.data == "poly_file"
    assert len(result.children) == 4

    assert result.children[0].data == "poly_block" # type: ignore
    assert len(result.children[0].children) == 3   # type: ignore

    # Assert correct description header
    assert result.children[0].children[0].data == 'description_header'               # type: ignore
    assert result.children[0].children[0].children[0].type == 'COMMENT'              # type: ignore
    assert result.children[0].children[0].children[0] == '* Some description header' # type: ignore

    # Assert correct metadata
    assert len(result.children[0].children[1].children) == 2               # type: ignore
    assert result.children[0].children[1].data == "metadata"               # type: ignore
    assert result.children[0].children[1].children[0].data == "name_line"  # type: ignore
    assert result.children[0].children[1].children[0].children[0].type == "NAME"       # type: ignore

    assert result.children[0].children[1].children[1].data == "dimensions_line" # type: ignore
    assert result.children[0].children[1].children[1].children[0].data == "dimensions_valid" # type: ignore
    assert len(result.children[0].children[1].children[1].children[0].children) == 2   # type: ignore
    assert result.children[0].children[1].children[1].children[0].children[0] == "5"   # type: ignore
    assert result.children[0].children[1].children[1].children[0].children[1] == "23"  # type: ignore

    # Assert correct points
    assert result.children[0].children[2].data == "points"                  # type: ignore
    assert result.children[0].children[2].children[0].data == "point"       # type: ignore
    assert result.children[0].children[2].children[0].children[0] == "1.0"  # type: ignore
    assert result.children[0].children[2].children[0].children[1] == "2.0"  # type: ignore
    assert result.children[0].children[2].children[0].children[2] == "3.0"  # type: ignore
    assert result.children[0].children[2].children[1].data == "point"       # type: ignore
    assert result.children[0].children[2].children[1].children[0] == "4.0"  # type: ignore
    assert result.children[0].children[2].children[1].children[1] == "5.0"  # type: ignore
    assert result.children[0].children[2].children[1].children[2] == "6.0"  # type: ignore
    assert result.children[0].children[2].children[2].type == "EMPTY_LINES" # type: ignore
    assert result.children[0].children[2].children[3].data == "point"       # type: ignore
    assert result.children[0].children[2].children[3].children[0] == "7.0"  # type: ignore
    assert result.children[0].children[2].children[3].children[1] == "8.0"  # type: ignore
    assert result.children[0].children[2].children[3].children[2] == "9.0"  # type: ignore


def test_poly_file_is_tokenized_correctly2():
    point = """* Some description header
this is a name  
5    23
    1.0  2.0  3.0
    4.0  5.0  6.0


    someName
6    15
    6.0  5.0  2.0   
    3.0  2.0  1.0    


    9.0  8.0  7.0

woo this should be an invalid block
because this should not exist.
"""

    parser = Lark(polyfile_grammar, 
                  start='poly_file',
                  lexer='contextual',
                  parser='lalr')
    result = parser.parse(point)


def test_comment_is_parsed_correctly():
    description_header1 = """* some value           
* another value      
    
        
* last value
"""
    parser = Lark(polyfile_grammar, 
                  start='description_header',
                  parser='lalr')
    tokens = parser.parse(description_header1)
    transformed_tokens = PolyFileLiteralTransformer().transform(tokens)    
    (result, msgs) = PolyFileInterpreter().visit(transformed_tokens)

    assert result.content == " some value\n another value\n last value"
    assert len(msgs) == 1
    assert msgs[0].reason == "Unexpected empty lines will be ignored."


def test_metadata_is_parsed_correctly():
    metadata = """this is a name  
5    23
"""

    parser = Lark(polyfile_grammar, 
                  start='metadata',
                  parser='lalr')
    tokens = parser.parse(metadata)
    transformed_tokens = PolyFileLiteralTransformer().transform(tokens)
    (result, msgs) = PolyFileInterpreter().visit(transformed_tokens)

    assert result.name == "this is a name"
    assert result.n_rows == 5
    assert result.n_columns == 23


def test_point_line_is_parsed_correctly():
    point = "   1.0  2.0  3.0  4.0  5.0   \n"

    parser = Lark(polyfile_grammar, 
                  start='point_line',
                  parser='lalr')
    tokens = parser.parse(point)
    transformed_tokens = PolyFileLiteralTransformer().transform(tokens)

    interpreter = PolyFileInterpreter(has_z_value=True)
    interpreter._expected_n_columns = 5
    (result, msgs) = interpreter.visit(transformed_tokens)

    assert result is not None
    assert result.x == 1.0
    assert result.y == 2.0
    assert result.z == 3.0
    assert result.data[0] == 4.0
    assert result.data[1] == 5.0

    assert len(msgs) == 0


def test_invalid_point_line_is_parsed_correctly():
    point = "   1.0     \n"

    parser = Lark(polyfile_grammar, 
                  start='point_line',
                  parser='lalr')
    tokens = parser.parse(point)
    transformed_tokens = PolyFileLiteralTransformer().transform(tokens)
    (result, msgs) = PolyFileInterpreter().visit(transformed_tokens)

    assert result is None
    assert len(msgs) == 1


def test_points_is_parsed_correctly():
    point = """    1.0  2.0  3.0   
    4.0  5.0  6.0    


    7.0  8.0  9.0   
"""

    parser = Lark(polyfile_grammar, 
                  start='points',
                  parser='lalr')
    tokens = parser.parse(point)
    transformed_tokens = PolyFileLiteralTransformer().transform(tokens)
    (result, msgs) = PolyFileInterpreter(True).visit(transformed_tokens)

    assert result is not None
    assert len(result) == 3
    assert len(msgs) == 1

    assert result[0].x == 1.0
    assert result[0].y == 2.0
    assert result[0].z == 3.0
    assert len(result[0].data) == 0

    assert result[1].x == 4.0
    assert result[1].y == 5.0
    assert result[1].z == 6.0
    assert len(result[1].data) == 0

    assert result[2].x == 7.0
    assert result[2].y == 8.0
    assert result[2].z == 9.0
    assert len(result[2].data) == 0


def test_polyblock_is_parsed_correctly():
    block = """* Some description header
this is a name  
3    3
    1.0  2.0  3.0   
    4.0  5.0  6.0    


    7.0  8.0  9.0   
"""

    parser = Lark(polyfile_grammar, 
                  start='poly_block',
                  parser='lalr')
    tokens = parser.parse(block)
    transformed_tokens = PolyFileLiteralTransformer().transform(tokens)
    (result, msgs) = PolyFileInterpreter(True).visit(transformed_tokens)

    assert result is not None
    assert len(msgs) == 1

    assert result.metadata.name == "this is a name"
    assert result.metadata.n_rows == 3
    assert result.metadata.n_columns == 3

    assert result.points[0].x == 1.0
    assert result.points[0].y == 2.0
    assert result.points[0].z == 3.0
    assert len(result.points[0].data) == 0

    assert result.points[1].x == 4.0
    assert result.points[1].y == 5.0
    assert result.points[1].z == 6.0
    assert len(result.points[1].data) == 0

    assert result.points[2].x == 7.0
    assert result.points[2].y == 8.0
    assert result.points[2].z == 9.0
    assert len(result.points[2].data) == 0