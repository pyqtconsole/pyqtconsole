import pytest
from pyqtconsole.text import columnize


def _strip(text):
    """Normalize expected strings to allow more readable definition."""
    return text.lstrip('\n').rstrip(' ')


def test_columnize_basic():
    assert columnize([]) == '<empty>\n'
    assert columnize(["a", '2', "c"], 10, ', ') == 'a, 2, c\n'
    assert columnize(["oneitem"]) == 'oneitem\n'
    assert columnize(("one", "two", "three")) == 'one  two  three\n'
    assert columnize(list(range(4))) == '0  1  2  3\n'


def test_columnize_array():
    assert columnize(list(range(12)), opts={
        'displaywidth': 6, 'arrange_array': True}) == _strip("""
[ 0,
  1,
  2,
  3,
  4,
  5,
  6,
  7,
  8,
  9,
 10,
 11]

        """)
    assert columnize(list(range(12)), opts={
        'displaywidth': 10, 'arrange_array': True}) == _strip("""
[ 0,  1,
  2,  3,
  4,  5,
  6,  7,
  8,  9,
 10, 11]

        """)


def test_columnize_horizontal_vs_vertical():
    dat4 = list('0123')
    # use displaywidth 4
    assert columnize(dat4, opts={
        'displaywidth': 4, 'arrange_vertical': False}) == _strip("""
0  1
2  3
    """)
    assert columnize(dat4, opts={
        'displaywidth': 4, 'arrange_vertical': True}) == _strip("""
0  2
1  3
    """)

    # use displaywidth 7:
    assert columnize(dat4, opts={
        'displaywidth': 7, 'arrange_vertical': False}) == _strip("""
0  1  2
3
    """)
    # FIXME: this looks like a bug to me:
    assert columnize(dat4, opts={
        'displaywidth': 7, 'arrange_vertical': True}) == _strip("""
0  2
1  3
    """)

    # longer dataset:
    dat100 = [str(i) for i in range(100)]
    assert columnize(dat100, opts={
        'displaywidth': 80, 'arrange_vertical': False}) == _strip("""
 0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19
20  21  22  23  24  25  26  27  28  29  30  31  32  33  34  35  36  37  38  39
40  41  42  43  44  45  46  47  48  49  50  51  52  53  54  55  56  57  58  59
60  61  62  63  64  65  66  67  68  69  70  71  72  73  74  75  76  77  78  79
80  81  82  83  84  85  86  87  88  89  90  91  92  93  94  95  96  97  98  99
    """)
    assert columnize(dat100, opts={
        'displaywidth': 80, 'arrange_vertical': True}) == _strip("""
0  5  10  15  20  25  30  35  40  45  50  55  60  65  70  75  80  85  90  95
1  6  11  16  21  26  31  36  41  46  51  56  61  66  71  76  81  86  91  96
2  7  12  17  22  27  32  37  42  47  52  57  62  67  72  77  82  87  92  97
3  8  13  18  23  28  33  38  43  48  53  58  63  68  73  78  83  88  93  98
4  9  14  19  24  29  34  39  44  49  54  59  64  69  74  79  84  89  94  99
    """)


def test_columnize_count27():
    data = (
        "one",          "two",          "three",
        "for",          "five",         "six",
        "seven",        "eight",        "nine",
        "ten",          "eleven",       "twelve",
        "thirteen",     "fourteen",     "fifteen",
        "sixteen",      "seventeen",    "eightteen",
        "nineteen",     "twenty",       "twentyone",
        "twentytwo",    "twentythree",  "twentyfour",
        "twentyfive",   "twentysix",    "twentyseven",
    )
    # We use 'inline strings' to make sure the trailing space is obvious to
    # the reader and won't get lost due to automatic removal in some editors:
    assert columnize(data) == (
        'one    five   nine    thirteen  seventeen  twentyone    twentyfive \n'
        'two    six    ten     fourteen  eightteen  twentytwo    twentysix  \n'
        'three  seven  eleven  fifteen   nineteen   twentythree  twentyseven\n'
        'for    eight  twelve  sixteen   twenty     twentyfour \n')
    assert columnize(data, arrange_vertical=False) == (
        'one         two        three        for        five         six       \n'
        'seven       eight      nine         ten        eleven       twelve    \n'
        'thirteen    fourteen   fifteen      sixteen    seventeen    eightteen \n'
        'nineteen    twenty     twentyone    twentytwo  twentythree  twentyfour\n'
        'twentyfive  twentysix  twentyseven\n')


def test_columnize_count55():
    data = [str(i) for i in range(55)]
    assert columnize(data, opts={
        'displaywidth': 39, 'arrange_array': True}) == _strip("""
[ 0,  1,  2,  3,  4,  5,  6,  7,  8,
  9, 10, 11, 12, 13, 14, 15, 16, 17,
 18, 19, 20, 21, 22, 23, 24, 25, 26,
 27, 28, 29, 30, 31, 32, 33, 34, 35,
 36, 37, 38, 39, 40, 41, 42, 43, 44,
 45, 46, 47, 48, 49, 50, 51, 52, 53,
 54]

        """)

    assert columnize(
        data, displaywidth=39, ljust=False,
        colsep=', ', lineprefix='    ') == _strip("""
    0,  7, 14, 21, 28, 35, 42, 49
    1,  8, 15, 22, 29, 36, 43, 50
    2,  9, 16, 23, 30, 37, 44, 51
    3, 10, 17, 24, 31, 38, 45, 52
    4, 11, 18, 25, 32, 39, 46, 53
    5, 12, 19, 26, 33, 40, 47, 54
    6, 13, 20, 27, 34, 41, 48
        """)

    assert columnize(
        data, displaywidth=39, ljust=False,
        arrange_vertical=False, colsep=', ') == _strip("""
 0,  1,  2,  3,  4,  5,  6,  7,  8,  9
10, 11, 12, 13, 14, 15, 16, 17, 18, 19
20, 21, 22, 23, 24, 25, 26, 27, 28, 29
30, 31, 32, 33, 34, 35, 36, 37, 38, 39
40, 41, 42, 43, 44, 45, 46, 47, 48, 49
50, 51, 52, 53, 54
        """)

    assert columnize(
        data, displaywidth=39, ljust=False,
        arrange_vertical=False, colsep=', ', lineprefix='    ') == _strip("""
     0,  1,  2,  3,  4,  5,  6,  7
     8,  9, 10, 11, 12, 13, 14, 15
    16, 17, 18, 19, 20, 21, 22, 23
    24, 25, 26, 27, 28, 29, 30, 31
    32, 33, 34, 35, 36, 37, 38, 39
    40, 41, 42, 43, 44, 45, 46, 47
    48, 49, 50, 51, 52, 53, 54
        """)


def test_columnize_raises_typeerror():
    with pytest.raises(TypeError):
        columnize(5)
