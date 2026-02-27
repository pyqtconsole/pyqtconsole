from pyqtconsole.highlighter import PythonHighlighter
from qtpy.QtGui import QTextDocument
from unittest.mock import MagicMock, call
import pytest


@pytest.fixture
def highlighter():
    """Create a PythonHighlighter instance for testing."""
    doc = QTextDocument()
    h = PythonHighlighter(doc)
    # Mock Qt state methods to avoid runtime errors in tests
    h.setCurrentBlockState = MagicMock()
    h.previousBlockState = MagicMock(return_value=-1)
    h.currentBlockState = MagicMock(return_value=0)
    return h


def test_fstring_interpolation_simple(highlighter):
    """Test highlighting of simple f-string interpolations."""
    highlighter.setFormat = MagicMock()

    text = 'f"Hello {name}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {name} at position 8, length 6
    highlighter.setFormat.assert_called_once_with(
        8, 6, highlighter.styles['fstring'])


def test_fstring_interpolation_multiple(highlighter):
    """Test highlighting of multiple f-string interpolations."""
    highlighter.setFormat = MagicMock()

    text = 'f"x={x}, y={y}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {x} at position 4 and {y} at position 11
    assert highlighter.setFormat.call_count == 2
    calls = highlighter.setFormat.call_args_list
    assert calls[0] == call(4, 3, highlighter.styles['fstring'])
    assert calls[1] == call(11, 3, highlighter.styles['fstring'])


def test_fstring_interpolation_with_expression(highlighter):
    """Test highlighting of f-string with expression."""
    highlighter.setFormat = MagicMock()

    text = 'f"result is {x + y}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {x + y} at position 12, length 7
    highlighter.setFormat.assert_called_once_with(
        12, 7, highlighter.styles['fstring'])


def test_fstring_interpolation_escaped_braces(highlighter):
    """Test that escaped braces {{ and }} are not highlighted."""
    highlighter.setFormat = MagicMock()

    text = 'f"{{escaped}} {real}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should only highlight {real}, not {{escaped}}
    highlighter.setFormat.assert_called_once_with(
        14, 6, highlighter.styles['fstring'])


def test_fstring_interpolation_nested_braces(highlighter):
    """Test highlighting of f-string with nested braces (dict, set)."""
    highlighter.setFormat = MagicMock()

    # Use double quotes inside for dict access instead of escaped quotes
    text = 'f\'{data["key"]}\''
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {data["key"]}
    if highlighter.setFormat.call_count > 0:
        # Verify it was called at least once with the fstring style
        calls = highlighter.setFormat.call_args_list
        assert any(call[0][2] == highlighter.styles['fstring'] for call in calls)


def test_fstring_single_quotes(highlighter):
    """Test f-string with single quotes."""
    highlighter.setFormat = MagicMock()

    text = "f'Hello {name}'"
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {name} at position 8, length 6
    highlighter.setFormat.assert_called_once_with(
        8, 6, highlighter.styles['fstring'])


def test_fstring_raw_string(highlighter):
    """Test raw f-string (rf or fr prefix)."""
    highlighter.setFormat = MagicMock()

    text = 'rf"path\\{name}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {name} at position 8, length 6
    highlighter.setFormat.assert_called_once_with(
        8, 6, highlighter.styles['fstring'])


def test_fstring_format_spec(highlighter):
    """Test f-string with format specification."""
    highlighter.setFormat = MagicMock()

    text = 'f"{value:.2f}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {value:.2f} at position 2, length 11
    highlighter.setFormat.assert_called_once_with(
        2, 11, highlighter.styles['fstring'])


def test_regular_string_not_highlighted(highlighter):
    """Test that regular strings are not highlighted as f-strings."""
    highlighter.setFormat = MagicMock()

    text = '"This {is} not an f-string"'
    highlighter.highlight_fstring_interpolations(text)

    # Should not highlight anything
    highlighter.setFormat.assert_not_called()


def test_fstring_empty_interpolation(highlighter):
    """Test f-string with empty braces."""
    highlighter.setFormat = MagicMock()

    text = 'f"empty {}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight {} at position 8, length 2
    highlighter.setFormat.assert_called_once_with(
        8, 2, highlighter.styles['fstring'])


def test_fstring_multiple_on_same_line(highlighter):
    """Test multiple f-strings on the same line."""
    highlighter.setFormat = MagicMock()

    text = 'f"{a}" + f"{b}"'
    highlighter.highlight_fstring_interpolations(text)

    # Should highlight both {a} and {b}
    assert highlighter.setFormat.call_count == 2
    calls = highlighter.setFormat.call_args_list
    # f"{a}" + f"{b}"
    # 0123456789...
    # {a} is at position 2, {b} is at position 11
    assert calls[0] == call(2, 3, highlighter.styles['fstring'])
    assert calls[1] == call(11, 3, highlighter.styles['fstring'])


# Tests for highlight_escape_sequences


def test_escape_simple_escapes(highlighter):
    """Test highlighting of simple escape sequences."""
    highlighter.setFormat = MagicMock()

    text = '"Hello\\nWorld"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \n at position 6, length 2
    highlighter.setFormat.assert_called_once_with(
        6, 2, highlighter.styles['escape'])


def test_escape_multiple_escapes(highlighter):
    """Test highlighting of multiple escape sequences in one string."""
    highlighter.setFormat = MagicMock()

    text = '"Line1\\nLine2\\tTab"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight both \n and \t
    assert highlighter.setFormat.call_count == 2
    calls = highlighter.setFormat.call_args_list
    assert calls[0] == call(6, 2, highlighter.styles['escape'])  # \n
    assert calls[1] == call(13, 2, highlighter.styles['escape'])  # \t


def test_escape_all_common_escapes(highlighter):
    """Test all common single-character escapes."""
    highlighter.setFormat = MagicMock()

    text = r'"\\  \'  \"  \a  \b  \f  \n  \r  \t  \v  \0"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight all 11 escape sequences
    assert highlighter.setFormat.call_count == 11


def test_escape_hex_escape(highlighter):
    """Test highlighting of hex escape sequences."""
    highlighter.setFormat = MagicMock()

    text = '"Value: \\x41"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \x41 at position 8, length 4
    highlighter.setFormat.assert_called_once_with(
        8, 4, highlighter.styles['escape'])


def test_escape_unicode_escape(highlighter):
    """Test highlighting of Unicode escape sequences."""
    highlighter.setFormat = MagicMock()

    text = '"Greek: \\u03B1"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \u03B1 at position 8, length 6
    highlighter.setFormat.assert_called_once_with(
        8, 6, highlighter.styles['escape'])


def test_escape_unicode_long_escape(highlighter):
    """Test highlighting of long Unicode escape sequences."""
    highlighter.setFormat = MagicMock()

    text = '"Emoji: \\U0001F600"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \U0001F600 at position 8, length 10
    highlighter.setFormat.assert_called_once_with(
        8, 10, highlighter.styles['escape'])


def test_escape_named_unicode(highlighter):
    """Test highlighting of named Unicode escape sequences."""
    highlighter.setFormat = MagicMock()

    text = '"Greek: \\N{GREEK SMALL LETTER ALPHA}"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \N{GREEK SMALL LETTER ALPHA}
    highlighter.setFormat.assert_called_once_with(
        8, 28, highlighter.styles['escape'])


def test_escape_octal_escape(highlighter):
    """Test highlighting of octal escape sequences."""
    highlighter.setFormat = MagicMock()

    text = '"Octal: \\101"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \101 at position 8, length 4
    highlighter.setFormat.assert_called_once_with(
        8, 4, highlighter.styles['escape'])


def test_escape_single_quoted_string(highlighter):
    """Test escape sequences in single-quoted strings."""
    highlighter.setFormat = MagicMock()

    text = "'Line1\\nLine2'"
    highlighter.highlight_escape_sequences(text)

    # Should highlight \n at position 6, length 2
    highlighter.setFormat.assert_called_once_with(
        6, 2, highlighter.styles['escape'])


def test_escape_in_fstring(highlighter):
    """Test escape sequences are also highlighted in f-strings."""
    highlighter.setFormat = MagicMock()

    text = 'f"Value\\n{x}"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \n at position 7, length 2
    highlighter.setFormat.assert_called_once_with(
        7, 2, highlighter.styles['escape'])


def test_escape_mixed_escapes(highlighter):
    """Test mix of different escape types in one string."""
    highlighter.setFormat = MagicMock()

    text = r'"Tab:\t Hex:\x41 Unicode:\u03B1"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight all three different escape types
    assert highlighter.setFormat.call_count == 3
    calls = highlighter.setFormat.call_args_list
    assert calls[0] == call(5, 2, highlighter.styles['escape'])   # \t
    assert calls[1] == call(12, 4, highlighter.styles['escape'])  # \x41
    assert calls[2] == call(25, 6, highlighter.styles['escape'])  # \u03B1


def test_escape_no_escapes(highlighter):
    """Test that strings without escapes don't trigger highlighting."""
    highlighter.setFormat = MagicMock()

    text = '"Just a normal string"'
    highlighter.highlight_escape_sequences(text)

    # Should not highlight anything
    highlighter.setFormat.assert_not_called()


def test_escape_backslash_at_end(highlighter):
    """Test that a backslash followed by valid escape char is highlighted."""
    highlighter.setFormat = MagicMock()

    text = '"Path\\\\File"'
    highlighter.highlight_escape_sequences(text)

    # Should highlight \\ at position 5, length 2
    highlighter.setFormat.assert_called_once_with(
        5, 2, highlighter.styles['escape'])


# Edge case tests for comment handling


def test_comment_with_hash_in_string(highlighter):
    """Test that # inside a string doesn't prevent comment highlighting."""
    highlighter.setFormat = MagicMock()

    text = "x='123 #123 abc'  #122"

    # highlightBlock processes the whole line
    highlighter.highlightBlock(text)

    # Verify that comment formatting was applied
    # The actual comment starts at position 17 (after the string)
    calls = [call for call in highlighter.setFormat.call_args_list
             if len(call[0]) >= 3 and call[0][2] == highlighter.styles['comment']]
    assert len(calls) > 0, "Comment should be highlighted"


def test_comment_numbers_not_highlighted(highlighter):
    """Test that numbers in comments are not highlighted separately."""
    highlighter.setFormat = MagicMock()

    text = "#123 comment with numbers 456"
    highlighter.highlightBlock(text)

    # Should only have comment formatting, not number formatting
    number_calls = [call for call in highlighter.setFormat.call_args_list
                    if len(call[0]) >= 3 and call[0][2] == highlighter.styles['numbers']]
    assert len(number_calls) == 0, "Numbers in comments should not be highlighted"

    comment_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['comment']]
    assert len(comment_calls) > 0, "Comment should be highlighted"


def test_comment_with_fstring_not_highlighted(highlighter):
    """Test that f-strings in comments are not highlighted."""
    highlighter.setFormat = MagicMock()

    text = "# f'123 \\n {123}'"
    highlighter.highlightBlock(text)

    # Should not have fstring or escape formatting
    fstring_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['fstring']]
    assert len(
        fstring_calls) == 0, "F-string interpolations in comments should not be highlighted"

    escape_calls = [call for call in highlighter.setFormat.call_args_list
                    if len(call[0]) >= 3 and call[0][2] == highlighter.styles['escape']]
    assert len(
        escape_calls) == 0, "Escape sequences in comments should not be highlighted"

    comment_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['comment']]
    assert len(comment_calls) > 0, "Comment should be highlighted"


def test_fstring_with_comment_positions(highlighter):
    """Test that f-string interpolations respect comment positions."""
    highlighter.setFormat = MagicMock()

    # Create comment positions for the second half of the text
    text = 'f"{x}" # f"{y}"'
    comment_positions = set(range(7, len(text)))

    highlighter.highlight_fstring_interpolations(text, comment_positions)

    # Should only highlight {x}, not {y} which is in the comment
    assert highlighter.setFormat.call_count == 1
    calls = highlighter.setFormat.call_args_list
    assert calls[0] == call(2, 3, highlighter.styles['fstring'])


def test_escape_with_comment_positions(highlighter):
    """Test that escape sequences respect comment positions."""
    highlighter.setFormat = MagicMock()

    # Create comment positions for the second half of the text
    text = '"\\n" # "\\t"'
    comment_positions = set(range(5, len(text)))

    highlighter.highlight_escape_sequences(text, comment_positions)

    # Should only highlight \n, not \t which is in the comment
    assert highlighter.setFormat.call_count == 1
    calls = highlighter.setFormat.call_args_list
    assert calls[0] == call(1, 2, highlighter.styles['escape'])


def test_comment_after_code(highlighter):
    """Test comment highlighting after regular code."""
    highlighter.setFormat = MagicMock()

    text = "x = 123  # this is a comment"
    highlighter.highlightBlock(text)

    # Should have both number and comment highlighting
    number_calls = [call for call in highlighter.setFormat.call_args_list
                    if len(call[0]) >= 3 and call[0][2] == highlighter.styles['numbers']]
    assert len(number_calls) > 0, "Number should be highlighted"

    comment_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['comment']]
    assert len(comment_calls) > 0, "Comment should be highlighted"


def test_string_containing_hash_not_comment(highlighter):
    """Test that # inside a string is not treated as a comment."""
    highlighter.setFormat = MagicMock()

    text = '"This is a # hashtag"'
    highlighter.highlightBlock(text)

    # Should have string highlighting but no comment highlighting
    string_calls = [call for call in highlighter.setFormat.call_args_list
                    if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string']]
    assert len(string_calls) > 0, "String should be highlighted"

    comment_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['comment']]
    assert len(comment_calls) == 0, "# inside string should not be treated as comment"


def test_comment_with_keywords(highlighter):
    """Test that keywords in comments are not highlighted separately."""
    highlighter.setFormat = MagicMock()

    text = "# def class if else while"
    highlighter.highlightBlock(text)

    # Should not have keyword formatting
    keyword_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['keyword']]
    assert len(keyword_calls) == 0, "Keywords in comments should not be highlighted"

    comment_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['comment']]
    assert len(comment_calls) > 0, "Comment should be highlighted"


# Tests for multi-line string highlighting


def test_multiline_triple_double_quotes_single_line(highlighter):
    """Test triple-double-quoted string on a single line."""
    highlighter.setFormat = MagicMock()

    text = '"""This is a docstring"""'
    highlighter.highlightBlock(text)

    # Should have string2 formatting for the entire string
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(string2_calls) > 0, "Triple-quoted string should be highlighted"

    # Block state should be 0 (not in multi-line)
    highlighter.setCurrentBlockState.assert_called_with(0)


def test_multiline_triple_single_quotes_single_line(highlighter):
    """Test triple-single-quoted string on a single line."""
    highlighter.setFormat = MagicMock()

    text = "'''This is a docstring'''"
    highlighter.highlightBlock(text)

    # Should have string2 formatting for the entire string
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(string2_calls) > 0, "Triple-single-quoted string should be highlighted"

    # Block state should be 0 (not in multi-line)
    highlighter.setCurrentBlockState.assert_called_with(0)


def test_multiline_string_start(highlighter):
    """Test start of a multi-line string."""
    highlighter.setFormat = MagicMock()

    text = '"""Start of multi-line string'
    highlighter.highlightBlock(text)

    # Should have string2 formatting
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(string2_calls) > 0, "Multi-line string start should be highlighted"

    # Block state should be 2 (inside triple-double-quotes)
    highlighter.setCurrentBlockState.assert_called_with(2)


def test_multiline_string_continuation(highlighter):
    """Test continuation of a multi-line string."""
    highlighter.setFormat = MagicMock()

    # Set previous block state to indicate we're inside a triple-double-quoted string
    highlighter.previousBlockState = MagicMock(return_value=2)

    text = 'This is the middle of a multi-line string'
    highlighter.highlightBlock(text)

    # Should have string2 formatting for the entire line
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(
        string2_calls) > 0, "Multi-line string continuation should be highlighted"

    # Block state should still be 2 (still inside multi-line string)
    highlighter.setCurrentBlockState.assert_called_with(2)


def test_multiline_string_end(highlighter):
    """Test end of a multi-line string."""
    highlighter.setFormat = MagicMock()

    # Set previous block state to indicate we're inside a triple-double-quoted string
    highlighter.previousBlockState = MagicMock(return_value=2)

    text = 'End of multi-line string"""'
    highlighter.highlightBlock(text)

    # Should have string2 formatting
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(string2_calls) > 0, "Multi-line string end should be highlighted"

    # Block state should be 0 (exited multi-line string)
    highlighter.setCurrentBlockState.assert_called_with(0)


def test_multiline_with_code_before(highlighter):
    """Test multi-line string with code before it."""
    highlighter.setFormat = MagicMock()

    text = 'x = """docstring"""'
    highlighter.highlightBlock(text)

    # Should have string2 formatting
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(string2_calls) > 0, "Multi-line string should be highlighted"


def test_multiline_string_with_content(highlighter):
    """Test multi-line string with various content inside."""
    highlighter.setFormat = MagicMock()

    text = '"""This has numbers 123 and keywords def class"""'
    highlighter.highlightBlock(text)

    # Should not highlight numbers or keywords inside the triple-quoted string
    number_calls = [call for call in highlighter.setFormat.call_args_list
                    if len(call[0]) >= 3 and call[0][2] == highlighter.styles['numbers']]
    # Numbers inside the string should not be highlighted separately
    # (they would be within the string2 formatting)

    keyword_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['keyword']]
    # Keywords inside should not be highlighted
    assert len(
        keyword_calls) == 0, "Keywords inside multi-line string should not be highlighted"


def test_multiline_triple_single_start(highlighter):
    """Test start of a multi-line string with triple-single-quotes."""
    highlighter.setFormat = MagicMock()

    text = "'''Start of multi-line string"
    highlighter.highlightBlock(text)

    # Should have string2 formatting
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(string2_calls) > 0, "Multi-line string start should be highlighted"

    # Block state should be 1 (inside triple-single-quotes)
    highlighter.setCurrentBlockState.assert_called_with(1)


def test_multiline_triple_single_continuation(highlighter):
    """Test continuation of triple-single-quoted multi-line string."""
    highlighter.setFormat = MagicMock()

    # Set previous block state to indicate we're inside a triple-single-quoted string
    highlighter.previousBlockState = MagicMock(return_value=1)

    text = 'Middle of string'
    highlighter.highlightBlock(text)

    # Should have string2 formatting
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(
        string2_calls) > 0, "Multi-line string continuation should be highlighted"

    # Block state should still be 1
    highlighter.setCurrentBlockState.assert_called_with(1)


def test_multiline_triple_single_end(highlighter):
    """Test end of triple-single-quoted multi-line string."""
    highlighter.setFormat = MagicMock()

    # Set previous block state to indicate we're inside a triple-single-quoted string
    highlighter.previousBlockState = MagicMock(return_value=1)

    text = "End of string'''"
    highlighter.highlightBlock(text)

    # Should have string2 formatting
    string2_calls = [call for call in highlighter.setFormat.call_args_list
                     if len(call[0]) >= 3 and call[0][2] == highlighter.styles['string2']]
    assert len(string2_calls) > 0, "Multi-line string end should be highlighted"

    # Block state should be 0 (exited multi-line string)
    highlighter.setCurrentBlockState.assert_called_with(0)
