from bisect import bisect_right

from ipython_pygments_lexers import IPythonLexer as PythonLexer
from pygments import lex
from pygments.styles import get_style_by_name
from pygments.token import Token
from qtpy.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextBlockUserData,
    QTextCharFormat,
)


class NoHighlightData(QTextBlockUserData):
    """User data to mark blocks that should not be syntax highlighted."""

    pass


class ErrorHighlightData(QTextBlockUserData):
    """User data to mark blocks that contain errors."""

    pass


def _find_token_style(style, token_type):
    """Walk up token hierarchy to find a style string.

    Args:
        style: Pygments style object
        token_type: Token type to find style for

    Returns:
        Style string if found, None otherwise
    """
    current = token_type
    while current:
        style_string = style.styles.get(current)
        if style_string:
            return style_string
        current = getattr(current, "parent", None)
    return None


def format(color, style=""):
    """Return a QTextCharFormat with the given attributes."""
    _format = QTextCharFormat()
    if color is not None:
        _color = QColor(color)
        _format.setForeground(_color)
    if "bold" in style:
        _format.setFontWeight(QFont.Bold)
    if "italic" in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    "keyword": format("blue", "bold"),
    "operator": format("red"),
    "brace": format("darkGray"),
    "defclass": format("black", "bold"),
    "string": format("magenta"),
    "string2": format("darkMagenta"),
    "comment": format("darkGreen", "italic"),
    "self": format("black", "italic"),
    "numbers": format("brown"),
    "inprompt": format("darkBlue", "bold"),
    "outprompt": format("darkRed", "bold"),
    "fstring": format("darkCyan", "bold"),
    "escape": format("darkorange", "bold"),
    "error": format("red", "bold"),
}


def pygments_style_to_format(style_dict):
    """Convert a Pygments style dictionary entry to QTextCharFormat.

    Pygments style format: "#rrggbb bg:#rrggbb bold italic underline"
    """
    if not style_dict:
        return None

    _format = QTextCharFormat()

    # Parse the style string
    parts = str(style_dict).split()
    for part in parts:
        if part.startswith("#"):
            # Foreground color
            _format.setForeground(QColor(part))
        elif part.startswith("bg:#"):
            # Background color
            _format.setBackground(QColor(part[3:]))
        elif part == "bold":
            _format.setFontWeight(QFont.Bold)
        elif part == "italic":
            _format.setFontItalic(True)
        elif part == "underline":
            _format.setFontUnderline(True)

    return _format


def build_token_style_map(style_name, token_map):
    """Build a style map from Pygments theme for specific tokens.

    Args:
        style_name: Name of Pygments style (e.g., 'monokai')
        token_map: Dict mapping style keys to Token types

    Returns:
        Dict mapping style keys to QTextCharFormat objects
    """
    style = get_style_by_name(style_name)
    styles = {}

    for key, token_type in token_map.items():
        style_string = _find_token_style(style, token_type)
        if style_string:
            fmt = pygments_style_to_format(style_string)
            styles[key] = fmt if fmt else STYLES[key]
        else:
            styles[key] = STYLES[key]

    return styles


class PromptHighlighter:
    def __init__(self, formats=None, pygments_style=None):
        """Highlighter for console prompts.

        Args:
            formats: Custom format dictionary (legacy, overrides pygments_style)
            pygments_style: Name of Pygments style to use (e.g., 'monokai')
        """
        self.styles = dict(STYLES)
        if pygments_style:
            # Use Pygments built-in style
            self.updateStyle(pygments_style)
        elif formats:
            # Legacy: use custom formats
            self.styles.update(formats)

    def updateStyle(self, style_name):
        """Change the Pygments color scheme for prompts.

        Args:
            style_name: Name of Pygments style (e.g., 'monokai', 'vim')
        """
        try:
            token_map = {
                "inprompt": Token.Comment,
                "outprompt": Token.Comment,
            }
            self.styles = build_token_style_map(style_name, token_map)
        except Exception:
            print(f"Error: Pygments style '{style_name}' not found.")
            return

    def highlight(self, text, is_output=False):
        """Apply prompt formatting to entire text.

        Args:
            text: The prompt text to highlight
            is_output: True for output prompts, False for input prompts
        """
        if not text:
            return

        # Use outprompt color for output prompts, inprompt for input prompts
        fmt = self.styles["outprompt"] if is_output else self.styles["inprompt"]

        # Return formatting for entire text
        yield (0, len(text), fmt)


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language using Pygments.

    Args:
        document: The QTextDocument to highlight
        formats: Custom format dictionary (legacy, overrides pygments_style)
        pygments_style: Name of Pygments style to use (e.g., 'monokai',
                       'vim', 'friendly'). Defaults to custom STYLES.
    """

    def __init__(self, document, formats=None, pygments_style=None):
        """Initialize the syntax highlighter.

        :param document: The doc to apply syntax highlighting to
        :type document: QTextDocument
        :param formats: Optional dict mapping style names to QTextCharFormat
                        objects
        :type formats: dict, None
        :param pygments_style: Name of Pygments style to use (e.g., 'monokai',
                       'vim', 'friendly'). Defaults to custom STYLES.
        :type pygments_style: str, None
        """
        QSyntaxHighlighter.__init__(self, document)

        self.lexer = PythonLexer()

        # Build token formats from Pygments style or custom formats
        self.styles = dict(STYLES)
        if pygments_style:
            # Use Pygments built-in style
            self.token_formats = self._build_pygments_token_formats(pygments_style)
        else:
            if formats:
                # Legacy: use custom formats
                self.styles.update(formats)
            self.token_formats = self._build_custom_token_formats()

        # Cache tokenized document by content hash
        self._cached_doc_text = None
        self._line_formats = {}

    def _build_custom_token_formats(self):
        """Build token format map from custom STYLES dictionary."""
        styles = self.styles
        return {
            Token.Keyword: styles["keyword"],
            Token.Keyword.Constant: styles["keyword"],
            Token.Keyword.Declaration: styles["keyword"],
            Token.Keyword.Namespace: styles["keyword"],
            Token.Keyword.Pseudo: styles["keyword"],
            Token.Keyword.Reserved: styles["keyword"],
            Token.Keyword.Type: styles["keyword"],
            Token.Name.Builtin: styles["keyword"],
            Token.Name.Class: styles["defclass"],
            Token.Name.Function: styles["defclass"],
            Token.Name.Decorator: styles["defclass"],
            Token.String: styles["string"],
            Token.String.Double: styles["string"],
            Token.String.Single: styles["string"],
            Token.String.Doc: styles["string2"],
            Token.String.Escape: styles["escape"],
            Token.String.Interpol: styles["fstring"],
            Token.String.Affix: styles["string"],
            Token.Number: styles["numbers"],
            Token.Number.Integer: styles["numbers"],
            Token.Number.Float: styles["numbers"],
            Token.Number.Hex: styles["numbers"],
            Token.Number.Oct: styles["numbers"],
            Token.Number.Bin: styles["numbers"],
            Token.Comment: styles["comment"],
            Token.Comment.Single: styles["comment"],
            Token.Comment.Multiline: styles["comment"],
            Token.Operator: styles["operator"],
            Token.Punctuation: styles["brace"],
            Token.Generic.Error: styles["error"],
        }

    def _build_pygments_token_formats(self, style_name):
        """Build token format map from Pygments style."""
        style = get_style_by_name(style_name)
        token_formats = {}

        # Convert each token type in the style
        # style.styles is a dict: {token_type: style_string}
        for token_type, style_string in style.styles.items():
            fmt = pygments_style_to_format(style_string)
            if fmt:
                token_formats[token_type] = fmt

        return token_formats

    def updateStyle(self, style_name):
        """Change the Pygments color scheme and re-highlight the document.

        Args:
            style_name: Name of Pygments style (e.g., 'monokai', 'vim')
        """
        try:
            self.token_formats = self._build_pygments_token_formats(style_name)
        except Exception:
            print(f"Error: Pygments style '{style_name}' not found.")
            return
        self._cached_doc_text = None  # Clear cache to force retokenization
        self._line_formats = {}
        self.rehighlight()  # Trigger re-highlighting of entire document

    def _to_utf16_offset(self, text, position):
        """Convert Python string position to UTF-16 offset for Qt.

        Qt uses UTF-16 encoding internally, where some characters
        (like emoji) take 2 code units. This converts Python string
        indices to UTF-16 positions.
        """
        return len(text[:position].encode("utf-16-le")) // 2

    def highlightBlock(self, text):
        """Apply syntax highlighting using Pygments."""
        # Skip highlighting if the block is marked with NoHighlightData
        if isinstance(self.currentBlock().userData(), NoHighlightData):
            return
        if isinstance(self.currentBlock().userData(), ErrorHighlightData):
            # If block contains an error, apply error formatting to entire block
            error_fmt = self._get_format_for_token(Token.Generic.Error)
            if error_fmt:
                self.setFormat(0, len(text), error_fmt)
            return

        if not text:
            return

        # Get document text
        doc_text = self.document().toPlainText()

        # Retokenize if document changed
        if doc_text != self._cached_doc_text:
            self._cached_doc_text = doc_text
            self._line_formats = self._tokenize_document(doc_text)

        # Apply formatting for current line
        block_num = self.currentBlock().blockNumber()
        if block_num in self._line_formats:
            for start, length, fmt in self._line_formats[block_num]:
                self.setFormat(start, length, fmt)

    def _tokenize_document(self, text):
        """Tokenize entire document, return formatting by line number.

        This method is necessary because Pygments requires the entire document
        for context-aware syntax highlighting. Qt's QSyntaxHighlighter only
        provides one line at a time via highlightBlock(), but Pygments needs
        full context to properly handle:
        - Multi-line strings (triple-quoted strings)
        - Nested block structures (indentation-based syntax)
        - Context-dependent tokens (keywords vs identifiers)

        We tokenize the entire document once and cache the formatting positions
        by line number. Each line can then be highlighted independently using
        the cached token positions.

        Args:
            text: The complete document text

        Returns:
            dict: Maps line numbers to lists of (start, length, format) tuples
        """
        line_formats = {}
        if not text:
            return line_formats

        lines = text.split("\n")
        line_starts = [0]
        for line in lines[:-1]:
            line_starts.append(line_starts[-1] + len(line) + 1)

        position = 0
        for token_type, token_value in lex(text, self.lexer):
            if not token_value:
                continue

            fmt = self._get_format_for_token(token_type)
            if not fmt:
                position += len(token_value)
                continue

            # Find which line this token starts on using binary search
            start_line = bisect_right(line_starts, position) - 1

            # Handle tokens across multiple lines
            current_line = start_line
            chars_processed = 0

            while chars_processed < len(token_value) and current_line < len(lines):
                line_start_pos = line_starts[current_line]
                line_text = lines[current_line]

                # Position within current line
                token_pos_in_line = max(0, position + chars_processed - line_start_pos)

                # How many chars of token on this line
                remaining = len(token_value) - chars_processed
                chars_on_line = min(remaining, len(line_text) - token_pos_in_line)

                if chars_on_line > 0:
                    utf16_start = self._to_utf16_offset(line_text, token_pos_in_line)
                    utf16_end = self._to_utf16_offset(
                        line_text, token_pos_in_line + chars_on_line
                    )

                    if current_line not in line_formats:
                        line_formats[current_line] = []
                    line_formats[current_line].append(
                        (utf16_start, utf16_end - utf16_start, fmt)
                    )

                    chars_processed += chars_on_line

                # Skip the newline character
                if chars_processed < len(token_value):
                    chars_processed += 1
                    current_line += 1

            position += len(token_value)

        return line_formats

    def _get_format_for_token(self, token_type):
        """Find the most specific format for a token type.

        Walks up the token hierarchy until a format is found.
        """
        current_type = token_type
        while current_type:
            fmt = self.token_formats.get(current_type)
            if fmt:
                return fmt
            current_type = getattr(current_type, "parent", None)
        return None
