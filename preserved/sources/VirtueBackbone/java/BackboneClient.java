import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.UUID;

/** Java 17+ client for the VB01 binary envelope. No external dependencies. */
public final class BackboneClient implements AutoCloseable {
    private static final int MAGIC = 0x56423031;
    private static final int MAX = 262144;
    private final Socket socket;
    private final DataInputStream in;
    private final DataOutputStream out;

    public BackboneClient(int port, Path tokenFile, String service, String topicsJson) throws IOException {
        socket = new Socket();
        socket.connect(new InetSocketAddress("127.0.0.1", port), 5000);
        socket.setSoTimeout(10000);
        in = new DataInputStream(socket.getInputStream());
        out = new DataOutputStream(socket.getOutputStream());
        try {
            sendJson("{\"op\":\"hello\",\"token\":" + quote(Files.readString(tokenFile).trim())
                    + ",\"service\":" + quote(service) + ",\"topics\":" + topicsJson + "}");
            String welcome = receiveJson();
            if (!welcome.contains("\"op\":\"welcome\"")) throw new IOException("Handshake rejected: " + welcome);
        } catch (IOException | RuntimeException e) { socket.close(); throw e; }
    }

    public synchronized void sendJson(String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        if (bytes.length == 0 || bytes.length > MAX) throw new IOException("Frame size is invalid");
        out.writeInt(MAGIC);
        out.writeInt(bytes.length);
        out.write(bytes);
        out.flush();
    }

    /** Only one reader may call this at a time. Handles fragmented TCP frames. */
    public String receiveJson() throws IOException {
        if (in.readInt() != MAGIC) throw new IOException("Invalid VB01 magic");
        int size = in.readInt();
        if (size <= 0 || size > MAX) throw new IOException("Invalid frame length");
        byte[] bytes = new byte[size];
        in.readFully(bytes);
        return new String(bytes, StandardCharsets.UTF_8);
    }

    /** Returns a correlation id; the single reader must process the matching reply. */
    public String publish(String topic, String dataJson) throws IOException {
        String id = UUID.randomUUID().toString();
        sendJson("{\"op\":\"publish\",\"request_id\":" + quote(id) + ",\"topic\":" + quote(topic)
                + ",\"data\":" + dataJson + "}");
        return id;
    }

    public static String quote(String value) {
        StringBuilder s = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c == '"' || c == '\\') s.append('\\').append(c);
            else if (c < 32) s.append(String.format("\\u%04x", (int)c));
            else s.append(c);
        }
        return s.append('"').toString();
    }

    @Override public void close() throws IOException { socket.close(); }

    /** Demo participant: publishes Java status and receives shared pulses and text-map changes. */
    public static void main(String[] args) throws Exception {
        System.setOut(new PrintStream(System.out, true, StandardCharsets.UTF_8));
        if (args.length < 2) {
            System.err.println("Usage: java -jar backbone-client.jar PORT TOKEN_FILE [PULSES]");
            System.exit(2);
        }
        int count = args.length > 2 ? Integer.parseInt(args[2]) : 40;
        try (BackboneClient bus = new BackboneClient(Integer.parseInt(args[0]), Path.of(args[1]),
                "java-worker-" + ProcessHandle.current().pid(), "[\"pulse\",\"user.exchange\",\"knowledge.updated\",\"workflow.result\"]")) {
            bus.publish("user.exchange", "{\"language\":\"Java\",\"message\":\"Java participant connected\"}");
            bus.publish("workflow.request", "{\"action\":\"map-summary\",\"task_id\":\"java-map-" + ProcessHandle.current().pid() + "\"}");
            int pulses = 0;
            while (pulses < count) {
                String message = bus.receiveJson();
                System.out.println(message);
                if (message.contains("\"topic\":\"pulse\"")) pulses++;
            }
        }
    }
}
