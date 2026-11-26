import neural.studio.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
/** Cooperative client. Use from a worker thread in another Java application. */
public final class AllPrevBusClient {
 private final String base;private final long pid;private final String name;private long cursor;
 public AllPrevBusClient(String name){this(name,"http://127.0.0.1:48763");}
 public AllPrevBusClient(String name,String base){this.name=name;this.base=base;pid=ProcessHandle.current().pid();}
 public Map<String,Object> send(String topic,Object data)throws IOException{return send("all",topic,data);}
 public Map<String,Object> send(String target,String topic,Object data)throws IOException{
  return call("/api/events",Map.of("source",name,"pid",pid,"target",target,"topic",topic,"data",data));
 }
 @SuppressWarnings("unchecked") public List<Map<String,Object>> receive()throws IOException{
  Map<String,Object> result=call("/api/events?pid="+pid+"&after="+cursor,null);
  cursor=((Number)result.get("cursor")).longValue();return (List<Map<String,Object>>)result.get("events");
 }
 private Map<String,Object> call(String path,Object body)throws IOException{
  HttpURLConnection c=(HttpURLConnection)URI.create(base+path).toURL().openConnection();c.setConnectTimeout(1000);c.setReadTimeout(3000);
  try{if(body!=null){c.setDoOutput(true);c.setRequestMethod("POST");c.setRequestProperty("Content-Type","application/json");try(OutputStream out=c.getOutputStream()){out.write(FluxJson.write(body).getBytes(StandardCharsets.UTF_8));}}
   if(c.getResponseCode()>=300)throw new IOException("Bus HTTP "+c.getResponseCode());try(InputStream in=c.getInputStream()){return FluxJson.object(FluxJson.read(new String(in.readNBytes(1048576),StandardCharsets.UTF_8)));}
  }finally{c.disconnect();}
 }
}
