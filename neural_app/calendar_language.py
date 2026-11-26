"""Calendar transformations from explicit reference dates; no answer-option repair."""
import calendar,datetime,re

MONTHS={name.lower():i for i,name in enumerate(calendar.month_name) if name};MONTHS.update({name.lower():i for i,name in enumerate(calendar.month_abbr) if name})
WORDS={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
DATE=r'(?:\d{1,2}/\d{1,2}/\d{4}|[A-Za-z]+ \d{1,2},? \d{4})'
def parse_date(text):
 match=re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})',text)
 if match:return datetime.date(int(match[3]),int(match[1]),int(match[2]))
 match=re.fullmatch(r'([A-Za-z]+) (\d{1,2}),? (\d{4})',text)
 if not match or match[1].lower() not in MONTHS:raise ValueError('Supply a complete date with a known month')
 return datetime.date(int(match[3]),MONTHS[match[1].lower()],int(match[2]))
def shift(date,amount,unit):
 if unit in ('day','week'):return date+datetime.timedelta(days=amount*(7 if unit=='week' else 1))
 months=date.year*12+date.month-1+amount*(12 if unit=='year' else 1);year,month=divmod(months,12)
 try:return datetime.date(year,month+1,date.day)
 except ValueError:raise ValueError('The calendar shift has no matching day; clarify the end-of-month convention') from None
def offset(text):
 text=text.lower();simple={'today':(0,'day'),'yesterday':(-1,'day'),'tomorrow':(1,'day'),'one day after tomorrow':(2,'day'),'one day before yesterday':(-2,'day')}
 if text in simple:return simple[text]
 match=re.fullmatch(r'(\d+|'+ '|'.join(WORDS)+r') (day|week|month|year)s? (ago(?: from today)?|from today|later(?: from today)?)',text)
 if not match:return None
 amount=WORDS.get(match[1],int(match[1]) if match[1].isdigit() else 0)
 if amount>10000:raise ValueError('Calendar offset exceeds the bounded range')
 return (-amount if match[3].startswith('ago') else amount,match[2])
def solve(text,parse_options,make_result):
 parsed=parse_options(text)
 if not parsed:return None
 body,choices=parsed;question=re.search(r'What is the date (.+?) in MM/DD/YYYY\?',body)
 if not question:return None
 movement=offset(question[1])
 if movement is None:return None
 evidence=[];candidates=[]
 direct=re.findall(r'\bToday(?: is|,)\s*('+DATE+r')(?=[,.\s])',body,re.I)
 if direct:
  candidates=[parse_date(d) for d in direct];evidence+=direct
 else:
  correct=re.search(r'\b([A-Za-z]+) is correct\.',body)
  if correct:
   claims=re.findall(re.escape(correct[1])+r' thinks today is ('+DATE+r')',body);candidates=[parse_date(d) for d in claims];evidence+=claims
 for phrase,delta in [('Yesterday',1),('Tomorrow',-1),('One week ago from today',7),('One week from today',-7)]:
  for anchor in re.findall(r'\b'+phrase+r' (?:was|is|will be) ('+DATE+r')',body,re.I):candidates.append(shift(parse_date(anchor),delta,'day'));evidence.append(phrase+' '+anchor)
 if not candidates:
  # A dated event plus an explicit elapsed duration identifies today's date.
  dates=re.findall(DATE,body);elapsed=re.search(r'(\d+) (day|week|month|year)s? (?:have|has) passed since then',body,re.I)
  anniversary=re.search(r'(\d+)-year anniversary today',body,re.I)
  if len(dates)==1 and elapsed:
   candidates=[shift(parse_date(dates[0]),int(elapsed[1]),elapsed[2].lower())];evidence=[dates[0],elapsed[0]]
  elif len(dates)==1 and anniversary:
   candidates=[shift(parse_date(dates[0]),int(anniversary[1]),'year')];evidence=[dates[0],anniversary[0]]
 if not candidates:
  rule=re.search(r'(\w+) is on the (first|second|third|fourth|fifth|last) (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) of ([A-Za-z]+)',body)
  if rule:
   year=re.search(r'Today is (?:the )?(?:US )?'+re.escape(rule[1])+r' of (\d{4})',body)
   if year and rule[4].lower() in MONTHS:
    y,m=int(year[1]),MONTHS[rule[4].lower()];weekday=list(calendar.day_name).index(rule[3]);first=datetime.date(y,m,1)
    if rule[2]=='last':
     last=datetime.date(y,m,calendar.monthrange(y,m)[1]);resolved=last-datetime.timedelta(days=(last.weekday()-weekday)%7)
    else:resolved=first+datetime.timedelta(days=(weekday-first.weekday())%7+7*(['first','second','third','fourth','fifth'].index(rule[2])))
    if resolved.month!=m:raise ValueError('The requested ordinal weekday does not occur in that month')
    candidates=[resolved];evidence=[rule[0],year[0]]
 if not candidates:
  coming=re.search(r'\b(\d{4}) is coming in (\d+) hours\.',body)
  if coming and int(coming[2])<=8760:
   candidates=[(datetime.datetime(int(coming[1]),1,1)-datetime.timedelta(hours=int(coming[2]))).date()];evidence=[coming[0]]
 if not candidates:return None
 if len(set(candidates))!=1:return {'status':'conflicting-reference-dates','answer':'The explicit calendar anchors imply different dates for today. Resolve that conflict first.','reasoning_family':'calendar','evidence':{'candidate_dates':[d.isoformat() for d in candidates],'source_anchors':evidence},'model_calls':0}
 today=candidates[0];answer=shift(today,*movement);formatted=f'{answer.month:02d}/{answer.day:02d}/{answer.year:04d}';selected=[letter for letter,value in choices if value==formatted]
 facts={'reference_evidence':evidence,'resolved_today':today.isoformat(),'offset':{'amount':movement[0],'unit':movement[1]},'calculated_date':formatted}
 if len(selected)!=1:return {'status':'no-matching-option','answer':'The supplied facts give '+formatted+', which does not match exactly one option. Check the dates and answer choices.','reasoning_family':'calendar','evidence':facts,'model_calls':0}
 return make_result('calendar','('+selected[0]+')',facts,'Calendar arithmetic from explicit dates and elapsed durations; answer options never determine a missing year or repair inconsistent facts.')
