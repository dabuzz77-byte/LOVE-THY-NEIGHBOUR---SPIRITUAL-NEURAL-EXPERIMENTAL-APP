"""Small auditable script writer. Templates are written, never implicitly executed."""
import re
FORMATS={
 'python':('.py','python'), 'javascript':('.js','javascript'), 'powershell':('.ps1','powershell'),
 'batch':('.bat','bat'),'bash':('.sh','bash'),'java':('.java','java'),'csharp':('.cs','csharp'),'html':('.html','html'),'sql':('.sql','sql')}
ALIASES={'py':'python','js':'javascript','ps1':'powershell','bat':'batch','sh':'bash','cs':'csharp'}
def generate(language,concept,filename,a=7,b=3):
 language=ALIASES.get(language.lower(),language.lower());concept=concept.lower()
 if language not in FORMATS:raise ValueError('Formats: '+', '.join(FORMATS))
 ext,alias=FORMATS[language]
 if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*'+re.escape(ext),filename):raise ValueError('Use a simple filename with '+ext)
 if type(a) is not int or type(b) is not int or max(abs(a),abs(b))>100000:raise ValueError('Use bounded integer inputs')
 extras={
 'word_count':"import collections, sys\ntext = sys.stdin.read()\ncounts = collections.Counter(text.lower().split())\nfor word, count in counts.most_common():\n    print(word, count)\n",
 'json_validate':"import json, sys\nvalue = json.load(sys.stdin)\nprint(json.dumps(value, indent=2, ensure_ascii=False))\n",
 'csv_summary':"import csv, sys\nreader = csv.reader(sys.stdin)\nheader = next(reader, [])\nrows = 0\nfor row in reader:\n    rows += 1\nprint({'columns': header, 'rows': rows})\n",
 'directory_report':"from pathlib import Path\nfor item in sorted(Path('.').iterdir()):\n    if item.is_file():\n        print(item.name, item.stat().st_size)\n",
 'line_filter':"import sys\nneedle = sys.argv[1] if len(sys.argv) > 1 else ''\nfor line in sys.stdin:\n    if needle in line:\n        print(line, end='')\n"}
 if concept in extras:
  javascript={
   'word_count':"const fs = await import('node:fs');\nconst words = fs.readFileSync(0, 'utf8').toLowerCase().split(/\\s+/u).filter(Boolean);\nconst counts = new Map();\nfor (const word of words) counts.set(word, (counts.get(word) || 0) + 1);\nfor (const [word, count] of [...counts].sort((a, b) => b[1] - a[1])) console.log(word, count);\n",
   'json_validate':"const fs = await import('node:fs');\nconst value = JSON.parse(fs.readFileSync(0, 'utf8'));\nconsole.log(JSON.stringify(value, null, 2));\n",
   'line_filter':"const fs = await import('node:fs');\nconst needle = process.argv[2] ?? '';\nconst lines = fs.readFileSync(0, 'utf8').match(/[^\\n]*\\n|[^\\n]+$/g) || [];\nfor (const line of lines) if (line.includes(needle)) process.stdout.write(line);\n"}
  if language=='python':source=extras[concept]
  elif language=='javascript' and concept in javascript:source='(async () => {\n'+javascript[concept]+'})().catch(error => { console.error(error.message); process.exitCode = 1; });\n'
  else:raise ValueError('This workflow is available in Python; JavaScript also supports word_count, json_validate and line_filter')
  return {'language':language,'alias':alias,'filename':filename,'source':source,'expected':None,'concept':concept,'basis':'explicit native workflow template; source checked separately','program_executed':False}
 if concept not in ('sum','product','difference'):raise ValueError('Concepts: sum, product, difference; Python also word_count, json_validate, csv_summary, directory_report, line_filter; JavaScript also word_count, json_validate, line_filter')
 op={'sum':'+','product':'*','difference':'-'}[concept];answer={'sum':a+b,'product':a*b,'difference':a-b}[concept]
 name=filename[:-len(ext)]
 programs={
 'python':f'a = {a}\nb = {b}\nanswer = a {op} b\nprint(answer)\n',
 'javascript':f'const a = {a}, b = {b};\nconst answer = a {op} b;\nconsole.log(answer);\n',
 'powershell':f'$a = {a}\n$b = {b}\n$answer = $a {op} $b\nWrite-Output $answer\n',
 'batch':f'@echo off\nset /a "a={a}"\nset /a "b={b}"\nset /a "answer=a{op}b"\necho %answer%\n',
 'bash':f'#!/usr/bin/env bash\na={a}\nb={b}\nanswer=$((a {op} b))\nprintf \'%s\\n\' "$answer"\n',
 'java':f'public class {name} {{ public static void main(String[] args) {{ int a={a}, b={b}; System.out.println(a {op} b); }} }}\n',
 'csharp':f'public static class {name} {{ public static void Main() {{ int a={a}, b={b}; System.Console.WriteLine(a {op} b); }} }}\n',
 'html':f'<!doctype html><meta charset="utf-8"><title>{concept}</title><p>{a} {op} {b} = {answer}</p>\n',
 'sql':f'SELECT {a} {op} {b} AS answer;\n'}
 return {'language':language,'alias':alias,'filename':filename,'source':programs[language],'expected':answer,'concept':concept,'basis':'explicit native template; not unrestricted natural-language program synthesis','program_executed':False}
