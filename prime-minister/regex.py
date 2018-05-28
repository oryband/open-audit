"""Regular expressions for tokenizing documents."""
import re

# regex for detecting TOC opening header "תוכן העניינים"
# allowing for some missing redundant characters and padding spaces
TOC_START_RE = re.compile(r'^\s*תוכן [ה]?עני[י]?נים\s*$')

# regex for detecting TOC end (not including this line).
# this is the instance of "פרק ראשון"
TOC_END_RE = re.compile(r'^\s*פרק\s+ראשון\s*$')

# regexes for detecting a TOC chapter number in text form
# WITHOUT any following title, for example:
#
# פרק שני
TOC_CHAPTER_NUMBER_RE = re.compile(r'^\s*(פרק\s+\w+)\s*$')

# regexes for detecting a TOC chapter number and a following title and number, for example:
#
# פרק חמישי - מוסדות המדינה, חברות ממשלתיות  <-- THIS
#
# ותאגידים  <-- THIS
#
# הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות
#
# 1.  פעילות הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות...151
#
# NOTE there is a chance for false positives here: if the second line was
# missing, the third line will be counted as part of the title if though it's an office.
#
# the easiest solution for this that i thought of is the following:
# - construct a list of common chapter alternative names e.g. מוסדות המדינה | מוסדות המדינה ותאגידים
#   then tokenize them first (as chapters)
# - fetch all office names from state-comptroller output files,
#   and in addition construct a common office alternative names e.g. משרד הבטחון | משרד הב_י_טחון
#   then tokenize them second (as offices)
TOC_CHAPTER_TITLE_RE = re.compile(r'^\s*(פרק\s+\w+)\s+-\s+(.+)$')

# regex for detecting a TOC chapter office, for example:
# פרק חמישי - מוסדות המדינה, חברות ממשלתיות
#
# ותאגידים
#
# הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות  <--- THIS
#
# 1.  פעילות הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות...151
TOC_CHAPTER_OFFICE_RE = re.compile(r'^\s*(.*)\s*$')

# regex for detecting a TOC item in the form of:
#
# 1.  החברה לאיתור והשבת נכסים של נספי השואה בע"מ ופעולות המדינה לאיתור
#     ולהשבה של נכסי
#         הנספים.....................................................49
#
# NOTE we're ignoring the multiple dots and page number, and taking just the
# text.
TOC_CHAPTER_ITEM_RE_START = re.compile(r'^\s*\d+\.\s+(.+?)(?:\.{3,}\d+)?$')
TOC_CHAPTER_ITEM_RE_CONTINUE = re.compile(r'^\s*(.*)\s*$')
TOC_CHAPTER_ITEM_RE_END = re.compile(r'^\s*(.+?)\.{3,}\d+$')

# regex for joining TOC items which are split across multiple lines.
# should be used with re.sub() for removing newlines
# and truncating extra spaces.
TOC_ITEM_JOIN_RE = re.compile(r'\n\s*')

# regex searching for office names being discussed in a chapter.
CHAPTER_TOPIC_DISCUSSED_OFFICES_RE = re.compile(r'^\s*הגופים המבוקרים:\s(.+)$')

# regex searching for defect number (or numbers) in the beginning of a paragraph.
# for example: '2. bla bla bla' will fetch "2".
DEFECT_NUMBER_RE = re.compile(r'^\s*(\d+)\S*')

DEFECT_HEADER_RE = re.compile(r'^\s*ליקוי\s*$')

# regex for getting entire line without the first word
# (which is a defect number)
DEFECT_DESCRIPTION_RE = re.compile(r'^\s*\S+\s+(.*)')

# similar regex to DEFECT_NUMBER_RE but for defect reply.
# note some replies correspond to multiple defects in a single paragraph,
# and mention a range of defect numbers.
#
# For example: '2-4. bla bla bla' will fetch ["2", "4"]
# and means this reply corresponds to defects #2,#3,#4
DEFECT_REPLY_NUMBER_RE = re.compile(r'^\s*(\d+)(?:-(\d+))?\S*')

DEFECT_REPLY_HEADER_RE = re.compile(r'^\s*תגובה(?:\s+כללית)?\s*$')
