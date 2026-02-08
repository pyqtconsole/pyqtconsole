from qtpy.QtGui import (QColor, QTextCharFormat, QFont, QSyntaxHighlighter)

import keyword
import re


def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue', 'bold'),
    'operator': format('red'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('brown'),
    'inprompt': format('darkBlue', 'bold'),
    'outprompt': format('darkRed', 'bold'),
    'fstring': format('darkCyan', 'bold'),
    'escape': format('darkorange', 'bold'),
    'magic': format('darkCyan', 'bold'),
}


class PromptHighlighter(object):

    def __init__(self, formats=None):
        self.styles = styles = dict(STYLES, **(formats or {}))
        self.rules = [
            # Match the prompt incase of a console
            (re.compile(r'IN[^\:]*'), 0, styles['inprompt']),
            (re.compile(r'OUT[^\:]*'), 0, styles['outprompt']),
            # Numeric literals
            (re.compile(r'\b[+-]?[0-9]+\b'), 0, styles['numbers']),
        ]

    def highlight(self, text):
        for expression, nth, format in self.rules:
            for m in expression.finditer(text):
                yield (m.start(nth), m.end(nth) - m.start(nth), format)


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = keyword.kwlist

    def __init__(self, document, formats=None):
        QSyntaxHighlighter.__init__(self, document)

        self.styles = styles = dict(STYLES, **(formats or {}))

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (re.compile("'''"), 1, styles['string2'])
        self.tri_double = (re.compile('"""'), 2, styles['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, styles['keyword'])
                  for w in PythonHighlighter.keywords]

        # All other rules
        rules += [
            # 'self'
            # (r'\bself\b', 0, STYLES['self']),

            # Magic commands (must come before comments)
            (r'%\w+', 0, styles['magic']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, styles['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, styles['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, styles['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, styles['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, styles['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0,
             styles['numbers']),
        ]

        # Build a regex object for each pattern
        self.rules = [(re.compile(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def _to_utf16_offset(self, text, position):
        """Convert Python string position to UTF-16 offset for Qt.
        
        Qt uses UTF-16 encoding internally, where some characters (like emoji)
        take 2 code units. This converts Python string indices to UTF-16 positions.
        """
        return len(text[:position].encode('utf-16-le')) // 2

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Find all positions inside strings
        string_positions = {
            pos
            for expression, nth, fmt in self.rules
            if fmt == self.styles['string']
            for m in expression.finditer(text)
            for pos in range(m.start(nth), m.end(nth))
        }
        
        # Apply formatting, skipping non-string rules inside strings
        for expression, nth, format in self.rules:
            for m in expression.finditer(text):
                # Skip non-string formatting if it's inside a string
                if format != self.styles['string'] and m.start(nth) in string_positions:
                    continue
                start_pos = self._to_utf16_offset(text, m.start(nth))
                end_pos = self._to_utf16_offset(text, m.end(nth))
                self.setFormat(start_pos, end_pos - start_pos, format)

        # Highlight f-string interpolations
        self.highlight_fstring_interpolations(text)
        
        # Highlight escape sequences in strings
        self.highlight_escape_sequences(text)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``re.Pattern`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            m = delimiter.search(text)
            if m:
                start = m.start()
                # Move past this match
                add = m.end() - m.start()
            else:
                start = -1
                add = -1

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            m = delimiter.search(text, start + add)
            # Ending delimiter on this line?
            if m and (m.start() >= add):
                # length = end - start + add + m.end() - m.start()
                length = add + m.end() - start
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting - convert to UTF-16 positions
            start_utf16 = self._to_utf16_offset(text, start)
            end_utf16 = self._to_utf16_offset(text, start + length)
            self.setFormat(start_utf16, end_utf16 - start_utf16, style)
            # Look for the next match
            m = delimiter.search(text, start + length)
            if m:
                start = m.start()
            else:
                break

        # Return True if still inside a multi-line string, False otherwise
        return self.currentBlockState() == in_state

    def highlight_fstring_interpolations(self, text):
        """Highlight f-string interpolations (the {} parts).
        """
        fstring_pattern = re.compile(r"[fF][rR]?(['\"])([^'\"\\]*(\\.[^'\"\\]*)*?)\1")
        
        for m in fstring_pattern.finditer(text):
            string_content = m.group(2)
            content_start = m.start(2)
            
            i = 0
            while i < len(string_content):
                if string_content[i] == '{':
                    # Skip escaped braces {{
                    if i + 1 < len(string_content) and string_content[i + 1] == '{':
                        i += 2
                        continue
                    
                    # Find matching closing brace
                    brace_count = 1
                    j = i + 1
                    while j < len(string_content) and brace_count > 0:
                        if string_content[j:j+2] == '}}':
                            j += 2  # Skip escaped }}
                        elif string_content[j] == '{':
                            brace_count += 1
                            j += 1
                        elif string_content[j] == '}':
                            brace_count -= 1
                            j += 1
                        else:
                            j += 1
                    
                    if brace_count == 0:
                        self.setFormat(content_start + i, j - i, self.styles['fstring'])
                        i = j
                    else:
                        i += 1
                else:
                    i += 1

    def highlight_escape_sequences(self, text):
        """Highlight escape sequences in strings.
        """
        string_pattern = re.compile(r"(['\"])([^'\"\\]*(\\.[^'\"\\]*)*?)\1")
        escape_pattern = re.compile(
            r'\\(?:[\\\'\"\'abfnrtv0]|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|'
            r'U[0-9a-fA-F]{8}|N\{[^}]+\}|[0-7]{1,3})'
        )
        
        for m in string_pattern.finditer(text):
            content_start = m.start(2)
            for esc in escape_pattern.finditer(m.group(2)):
                self.setFormat(content_start + esc.start(), len(esc.group()), self.styles['escape'])
