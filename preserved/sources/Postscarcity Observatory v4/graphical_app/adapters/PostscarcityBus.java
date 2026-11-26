import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.function.Consumer;
import java.util.regex.*;

/** Java 11+ cooperative bus adapter. It follows in-app port changes. */
public final class PostscarcityBus implements AutoCloseable {
    private final Path connection;
    private final DatagramSocket socket;
    private final String name;
    private final Consumer<String> callback;
    private volatile boolean running = true;
    private volatile int port = 0;
    private volatile String token = "";
    private final Thread reader;

    public PostscarcityBus(Path connection, String name, Consumer<String> callback) throws Exception {
        this.connection=connection; this.name=name; this.callback=callback;
        socket=new DatagramSocket(new InetSocketAddress("127.0.0.1",0));
        socket.setSoTimeout(1000);
        reader=new Thread(this::listen,"postscarcity-bus"); reader.setDaemon(true); reader.start();
    }
    private static String quote(String value) {
        StringBuilder out=new StringBuilder("\"");
        for(char c:value.toCharArray()) {
            if(c=='"'||c=='\\') out.append('\\').append(c);
            else if(c<32) out.append(String.format("\\u%04x",(int)c));
            else out.append(c);
        }
        return out.append('"').toString();
    }
    private void send(String fields) throws Exception {
        if(port==0)return;
        String json="{\"token\":"+quote(token)+",\"pid\":"+ProcessHandle.current().pid()+",\"name\":"+quote(name)+","+fields+"}";
        byte[] bytes=json.getBytes(StandardCharsets.UTF_8);
        if(bytes.length>14000)throw new IllegalArgumentException("Bus event exceeds 14 KB");
        socket.send(new DatagramPacket(bytes,bytes.length,InetAddress.getByName("127.0.0.1"),port));
    }
    public void publish(String topic,String text) throws Exception {
        send("\"type\":\"event\",\"topic\":"+quote(topic)+",\"data\":{\"text\":"+quote(text)+"}");
    }
    private void listen() {
        long next=0;
        while(running) {
            try {
                if(System.currentTimeMillis()>=next) {
                    String config=Files.readString(connection);
                    Matcher p=Pattern.compile("\"port\"\\s*:\\s*(\\d+)").matcher(config);
                    Matcher t=Pattern.compile("\"token\"\\s*:\\s*\"([^\"]+)\"").matcher(config);
                    if(p.find()&&t.find()){port=Integer.parseInt(p.group(1));token=t.group(1);send("\"type\":\"subscribe\"");}
                    next=System.currentTimeMillis()+5000;
                }
                byte[] buffer=new byte[65535]; DatagramPacket packet=new DatagramPacket(buffer,buffer.length);
                socket.receive(packet);
                if(packet.getPort()==port&&packet.getAddress().isLoopbackAddress()) callback.accept(new String(buffer,0,packet.getLength(),StandardCharsets.UTF_8));
            } catch(SocketTimeoutException ignored) {
            } catch(Exception ex) { if(running)try{Thread.sleep(200);}catch(InterruptedException ignored){} }
        }
    }
    public void close(){running=false;socket.close();try{reader.join(1500);}catch(InterruptedException ex){Thread.currentThread().interrupt();}}
    public static void main(String[] args)throws Exception{
        Path connection=Paths.get(args.length>0?args[0]:"graphical_app/data/connection.json");
        long seconds=args.length>1?Long.parseLong(args[1]):0;
        try(PostscarcityBus bus=new PostscarcityBus(connection,"Java bus example",event->{if(event.contains("\"type\":\"attached\""))System.out.println("Java connected to postscarcity bus");})){
            long started=System.currentTimeMillis();
            while(seconds==0||System.currentTimeMillis()-started<seconds*1000){bus.publish("java.activity","Java process listening and broadcasting");Thread.sleep(2000);}
        }
    }
}
