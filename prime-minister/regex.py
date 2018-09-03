"""Regular expressions for tokenizing documents."""
import re

# regex for detecting TOC opening header "תוכן העניינים"
# allowing for some missing redundant characters and padding spaces
TOC_HEADER_RE = re.compile(r'^\s*תוכן [ה]?עני[י]?נים\s*$')

# we identify the end of the TOC and beginning of actual content of the
# report by looking at the first TOC title and searching
# for when it appears again for the second time.
#
# This can either be the beginning of the summary chapter,
# or if the summary doesn't exist in the report - the first chapter.
TOC_BORDER_IDENTIFIER_FIRST_CHAPTER_RE = re.compile(r'^\s*פרק\s+ראשון(\s*|\s+.*)$')
TOC_BORDER_IDENTIFIER_SUMMARY_RE = re.compile(r'^\s*(?:תקציר\s+.*|תקצירים\s*)$')

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
TOC_CHAPTER_NUMBER_WITH_TITLE_RE = re.compile(r'^\s*(פרק\s+\w+)\s+-\s+(.+)$')

# regex for detecting a special TOC chapter number with title
# that does NOT have an office name in the following line
#
# used for catching speciall chapter discussin cross-office subjects (מטלות רוחב)
TOC_CHAPTER_NUMBER_WITH_TITLE_CROSS_OFFICE_RE = re.compile(r'^\s*(פרק\s+\w+)\s+-\s+(מטלות רוחב(?:$|\s+.+))$')

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
TOC_CHAPTER_ITEM_RE_ONE_LINE = re.compile(r'^\s*(?:\d+\.\s+)??(.+?)\s*(?:\d+)$')
TOC_CHAPTER_ITEM_RE_MULTI_LINE_START = re.compile(r'^\s*(?:\d+\.\s+)??(.+?)(?<!\d)\s*$')
TOC_CHAPTER_ITEM_RE_MULTI_LINE_END = TOC_CHAPTER_ITEM_RE_ONE_LINE

# regex for joining TOC items which are split across multiple lines.
# should be used with re.sub() for removing newlines
# and truncating extra spaces.
TOC_ITEM_JOIN_RE = re.compile(r'\n\s*')

# regex for detecting chapter numbers, outside of TOC
CHAPTER_NUMBER_RE = TOC_CHAPTER_NUMBER_RE

# regex searching for office names being discussed in a chapter.
CHAPTER_TOPIC_DISCUSSED_OFFICES_RE = re.compile(r'^\s*(הגוף המבוקר|הגופים המבוקרים|המשרדים המבוקרים)(?: )?:\s(.+)$')

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

DEFECT_REPLY_HEADER_RE = re.compile(r'^\s*תגוב(?:ה|ת)(?:\s+כללית|)?\s*$')
