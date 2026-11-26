import neural.studio.*;
import java.util.*;
/** JSON codec for the local bus. */
final class FluxJson {
 static String write(Object v) {
  if(v==null)return "null";
  if(v instanceof Number || v instanceof Boolean)return v.toString();
  if(v instanceof Map<?,?> m){StringJoiner j=new StringJoiner(",","{","}");m.forEach((k,x)->j.add(write(k.toString())+":"+write(x)));return j.toString();}
  if(v instanceof Iterable<?> a){StringJoiner j=new StringJoiner(",","[","]");a.forEach(x->j.add(write(x)));return j.toString();}
  StringBuilder b=new StringBuilder("\"");
  for(char c:v.toString().toCharArray())switch(c){case '"'->b.append("\\\"");case '\\'->b.append("\\\\");case '\n'->b.append("\\n");case '\r'->b.append("\\r");case '\t'->b.append("\\t");default->{if(c<32)b.append(String.format("\\u%04x",(int)c));else b.append(c);}}
  return b.append('"').toString();
 }
 @SuppressWarnings("unchecked") static Map<String,Object> object(Object o){return o instanceof Map<?,?>?(Map<String,Object>)o:Map.of();}
 static Object read(String s){Parser p=new Parser(s);Object o=p.value(0);p.space();if(p.i!=s.length())throw new IllegalArgumentException("Trailing JSON");return o;}
 private static class Parser {
  final String s;int i;Parser(String s){this.s=s;}
  void space(){while(i<s.length()&&Character.isWhitespace(s.charAt(i)))i++;}
  char take(){if(i>=s.length())throw new IllegalArgumentException("Incomplete JSON");return s.charAt(i++);}
  Object value(int d){
   if(d>32)throw new IllegalArgumentException("JSON too deep");space();char c=take();
   if(c=='"')return string();
   if(c=='{'){Map<String,Object> m=new LinkedHashMap<>();space();if(i<s.length()&&s.charAt(i)=='}'){i++;return m;}
    while(true){space();if(take()!='"')throw new IllegalArgumentException("Key required");String k=string();space();if(take()!=':')throw new IllegalArgumentException("Colon required");m.put(k,value(d+1));space();char n=take();if(n=='}')return m;if(n!=',')throw new IllegalArgumentException("Comma required");}}
   if(c=='['){List<Object>a=new ArrayList<>();space();if(i<s.length()&&s.charAt(i)==']'){i++;return a;}
    while(true){a.add(value(d+1));space();char n=take();if(n==']')return a;if(n!=',')throw new IllegalArgumentException("Comma required");}}
   int start=i-1;while(i<s.length()&&",]} \r\n\t".indexOf(s.charAt(i))<0)i++;String t=s.substring(start,i);
   return switch(t){case "true"->true;case "false"->false;case "null"->null;default->{if(!t.matches("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?"))throw new IllegalArgumentException("Invalid JSON");double n=Double.parseDouble(t);if(!Double.isFinite(n))throw new IllegalArgumentException("Nonfinite JSON");yield n;}};
  }
  String string(){StringBuilder b=new StringBuilder();while(true){char c=take();if(c=='"')return b.toString();if(c<32)throw new IllegalArgumentException("Control character");if(c!='\\'){b.append(c);continue;}char e=take();b.append(switch(e){case '"','\\','/'->e;case 'b'->'\b';case 'f'->'\f';case 'n'->'\n';case 'r'->'\r';case 't'->'\t';case 'u'->{String h=""+take()+take()+take()+take();yield (char)Integer.parseInt(h,16);}default->throw new IllegalArgumentException("Bad escape");});}}
 }
}
