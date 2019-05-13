class Color():
    BLACK = 0
    RED = 1
    GREEN = 2
    BROWN = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7


class Decoration():
    BOLD = 0x01
    ITALIC = 0x02
    UNDERLINED = 0x04


class ColorizedString():
    SEQUENCE = "\033[{:d}m"

    def __init__(self, text, color, background_color):
        self.text = str(text)
        self.color = color
        self.background_color = background_color
    
    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return self.text

    def __str__(self):
        result = []

        if self.color:
            result.append(self.SEQUENCE.format(30 + self.color))

        if self.background_color:
            result.append(self.SEQUENCE.format(40 + self.background_color))

        result.append(str(self.text))

        result.append(self.SEQUENCE.format(0))

        return "".join(result)


class DecoratedString():
    SEQUENCE = "\033[{:d}m"

    def __init__(self, text, decorator):
        self.text = text
        self.decorator = decorator

    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return self.text

    def __str__(self):
        result = []
        result.append(self.SEQUENCE.format(self.decorator))
        result.append(str(self.text))
        result.append(self.SEQUENCE.format(0))

        return "".join(result)


def colorize(text, color=None, background_color=None):
    return ColorizedString(text, color, background_color)


def underline(text):
    return DecoratedString(text, Decoration.UNDERLINED)


def bold(text):
    return DecoratedString(text, Decoration.BOLD)


def italic(text):
    return DecoratedString(text, Decoration.ITALIC)


def colored_bool(value, color_true=Color.GREEN, color_false=Color.RED):
    return colorize(value, color=color_true if value else color_false)


class CliWriter():
    def __init__(self, output_stream):
        self.output_stream = output_stream
        self.enable_colors = True

    def disable_colors(self):
        self.enable_colors = False

    def table(self, *header, column_padding=3, padding_symbol=" "):
        return TableWriter(self, *header, column_padding=column_padding, padding_symbol=padding_symbol)

    def dict(self):
        return DictWriter(self)

    def list(self, items=[]):
        return ListWriter(self, items)

    def write(self, text):
        if isinstance(text, (ColorizedString, DecoratedString)) and not self.enable_colors:
            text = text.text

        self.output_stream.write(str(text))

    def writeline(self, text=""):
        if isinstance(text, (ColorizedString, DecoratedString)) and not self.enable_colors:
            text = text.text

        self.output_stream.write(str(text))
        self.output_stream.write("\n")

    def _write_boxed(self, text, foreground_color=None, background_color=None):
        self.writeline()

        self.writeline(colorize(" " * (len(text) + 4), background_color=background_color))
        self.writeline(colorize("  " + str(text) + "  ", background_color=background_color, color=foreground_color))
        self.writeline(colorize(" " * (len(text) + 4), background_color=background_color))

        self.writeline()

    def headline(self, text):
        self.writeline()
        self.writeline(underline(text))
        self.writeline()

    def alert(self, text):
        self._write_boxed(text, foreground_color=Color.WHITE, background_color=Color.RED)

    def success(self, text):
        self._write_boxed(text, foreground_color=Color.WHITE, background_color=Color.GREEN)


class ListWriter():
    def __init__(self, cli_writer, items=None):
        self.cli_writer = cli_writer
        self.items = items or []

    def add(self, value):
        self.items.append(value)

    def write(self):
        for item in self.items:
            self.cli_writer.write("  \u2022 ")
            self.cli_writer.writeline(item)


class DictWriter():
    def __init__(self, cli_writer):
        self.cli_writer = cli_writer
        self.items = []
        self.key_width = 0

    def add(self, key, value):
        self.items.append((key, value))
        self.key_width = max(self.key_width, len(key))

        return self

    def write(self):
        for key, value in self.items:
            self.cli_writer.write((key + ":").ljust(self.key_width + 3))
            self.cli_writer.writeline(value)


class TableWriter():
    def __init__(self, cli_writer, *header, column_padding=3, padding_symbol=" "):
        self.cli_writer = cli_writer
        self.header = header
        self.rows = []
        self.column_widths = [len(head) for head in header]
        self.column_padding = column_padding
        self.padding_symbol = padding_symbol
    
    def row(self, *colums):
        assert len(colums) == len(self.header)

        self.rows.append(colums)
        self.column_widths = [max(len(colum), current_width) for colum, current_width in zip(colums, self.column_widths)]

        return self

    def _pad_right(self, text, size):
        return self.padding_symbol * (size - len(text))

    def write(self):
        for head, column_width in zip(self.header, self.column_widths):
            self.cli_writer.write(head)
            self.cli_writer.write(self._pad_right(head, column_width + self.column_padding))
        self.cli_writer.writeline()

        for row in self.rows:
            for column, column_width in zip(row, self.column_widths):
                self.cli_writer.write(column)
                self.cli_writer.write(self._pad_right(column, column_width + self.column_padding))
            self.cli_writer.writeline()
