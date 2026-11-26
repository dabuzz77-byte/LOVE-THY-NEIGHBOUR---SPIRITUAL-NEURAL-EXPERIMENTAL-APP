/* Java 11+ bidirectional client; no external libraries. A callback receives
   the JSON batch, including IDs, topics, payloads and routes. Use your app's
   JSON library to interpret events and pass the route when publishing replies. */
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.regex.*;

public final class HydrogenMeshClient implements AutoCloseable {
    private final String url, token, name;
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build();
    private volatile boolean running = true;
    private final Thread worker;
    private volatile String status = "Connecting";
    public static String quote(String text) {
        StringBuilder b=new StringBuilder("\"");
        for(char c:text.toCharArray()) {
            if(c=='"'||c=='\\') b.append('\\').append(c);
            else if(c<32) b.append(String.format("\\u%04x",(int)c));
            else b.append(c);
        }
        return b.append('"').toString();
    }
    private String request(String path, String body) throws Exception {
        HttpRequest.Builder b=HttpRequest.newBuilder(URI.create(url+path)).timeout(Duration.ofSeconds(5))
            .header("Authorization","Bearer "+token).header("Content-Type","application/json");
        if(body==null)b.GET();else b.POST(HttpRequest.BodyPublishers.ofString(body));
        HttpResponse<String> response=http.send(b.build(),HttpResponse.BodyHandlers.ofString());
        if(response.statusCode()!=200)throw new java.io.IOException("Bus HTTP "+response.statusCode()+": "+response.body());
        return response.body();
    }
    public String publish(String topic, String dataJson, String target, String routeJson) throws Exception {
        String body="{\"id\":"+quote(UUID.randomUUID().toString())+",\"source\":"+quote(name)+
            ",\"topic\":"+quote(topic)+",\"target\":"+quote(target)+",\"route\":"+routeJson+",\"data\":"+dataJson+"}";
        return request("/publish",body);
    }
    public String publish(String topic, String dataJson) throws Exception {
        return publish(topic,dataJson,"*","["+quote(name)+"]");
    }
    public HydrogenMeshClient(String url,String token,String name,Consumer<String> onEvents) {
        if(!url.matches("http://127\\.0\\.0\\.1:[0-9]+"))throw new IllegalArgumentException("Loopback URL required");
        this.url=url;this.token=token;this.name=name;
        worker=new Thread(()->{
            long after=0;boolean initialized=false;
            while(running) {
                try {
                    if(!initialized) {
                        Matcher latest=Pattern.compile("\\\"messages\\\"\\s*:\\s*(\\d+)").matcher(request("/status",null));
                        if(!latest.find())throw new java.io.IOException("Invalid status");
                        after=Long.parseLong(latest.group(1));initialized=true;
                        publish("client.attached","{\"language\":\"Java\"}");
                    }
                    String batch=request("/inbox?after="+after+"&client="+URLEncoder.encode(name,StandardCharsets.UTF_8),null);
                    Matcher cursor=Pattern.compile("^\\{\\s*\\\"cursor\\\"\\s*:\\s*(\\d+)").matcher(batch);
                    if(!cursor.find())throw new java.io.IOException("Invalid inbox");
                    long next=Long.parseLong(cursor.group(1));
                    if(!batch.matches("(?s).*\\\"events\\\"\\s*:\\s*\\[\\s*\\]\\s*}\\s*"))onEvents.accept(batch);
                    after=next;status="Connected";
                } catch(Exception e) {status=e.toString();}
                try{Thread.sleep(250);}catch(InterruptedException e){break;}
            }
        },"Hydrogen Mesh");
        worker.setDaemon(true);worker.start();
    }
    public String status(){return status;}
    public void close(){running=false;worker.interrupt();}
    public static void main(String[] args) throws Exception {
        if(args.length<2){System.out.println("Usage: java HydrogenMeshClient.java URL TOKEN");return;}
        try(HydrogenMeshClient bus=new HydrogenMeshClient(args[0],args[1],"java-example",System.out::println)) {
            for(int i=0;i<12;i++){bus.publish("java.heartbeat","{\"tick\":"+i+"}");Thread.sleep(1000);}
        }
    }
}
