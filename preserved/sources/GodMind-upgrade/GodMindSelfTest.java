import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.net.*;
import java.net.http.*;
import java.time.Duration;
import java.util.*;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import com.sun.net.httpserver.HttpServer;

/** Run with java -Djava.awt.headless=true -cp build GodMindSelfTest. */
public final class GodMindSelfTest {
    static int checks;
    static void check(boolean condition,String message) { checks++; if (!condition) throw new AssertionError(message); }
    static void edt(Runnable task) throws Exception { SwingUtilities.invokeAndWait(task); }
    static final AtomicReference<GodMindInteractiveVisualizer.Dashboard> ui = new AtomicReference<>();
    static void modelTests() {
        GodMindInteractiveVisualizer.Model a = new GodMindInteractiveVisualizer.Model(64);
        GodMindInteractiveVisualizer.Model b = new GodMindInteractiveVisualizer.Model(64);
        check(Arrays.equals(a.activation,b.activation),"Deterministic initialization");
        Set<String> pairs = new HashSet<>();
        for (GodMindInteractiveVisualizer.Edge e : a.edges) { check(e.from != e.to,"No self links"); check(pairs.add(e.from+":"+e.to),"No duplicate links"); }
        a.autoInput = b.autoInput = false; a.pulse(7);
        for (int i = 0; i < 120; i++) { a.step(1.0/60); b.step(1.0/60); }
        int affected = 0; for (int i = 0; i < a.count; i++) if (i != 7 && Math.abs(a.activation[i]-b.activation[i])>0.00001) affected++;
        check(affected > 5,"Injected signals must propagate to connected nodes");
        for (int n : new int[]{24,64,128}) for (double coupling : new double[]{0.2,1.1,2}) {
            a.reset(n); a.coupling = coupling; a.autoInput = true;
            for (int j = 0; j < 3600; j++) a.step(1.0/60);
            for (double v : a.activation) check(Double.isFinite(v) && v>=0 && v<=1,"Stable finite activations");
            check(a.time > 59.9 && a.steps == 3600,"Accurate fixed-step clock");
        }
        a.coupling = 1.3; a.autoInput = false; a.reset(48);
        check(a.coupling == 1.3 && !a.autoInput && a.steps == 0,"Reset preserves controls and clears time");
        check(a.csv().split("\\R").length == 49,"CSV has a header and one row per node");
        check(a.json(true).contains("\"running\":true"),"Live JSON state");
        check(GodMindInteractiveVisualizer.validateEndpoint("https://example.com").getHost().equals("example.com"),"Valid HTTPS endpoint");
        for (String invalid : new String[]{"file:///tmp/a","example.com","ftp://example.com","http://user:maintainer@example.invalid",""}) {
            try { GodMindInteractiveVisualizer.validateEndpoint(invalid); throw new AssertionError("Invalid URI accepted: "+invalid); } catch (IllegalArgumentException expected) { checks++; }
        }
        System.out.println("PASS: propagation, stability, clock, resets, exports and URL validation");
    }
    static void uiTests() throws Exception {
        edt(() -> {
            GodMindInteractiveVisualizer.theme();
            GodMindInteractiveVisualizer.Dashboard d = new GodMindInteractiveVisualizer.Dashboard(); ui.set(d);
            d.setSize(1420,1000); GodMindInteractiveVisualizer.layoutTree(d);
            d.lastFrame = System.nanoTime(); d.fpsStart = d.lastFrame; d.togglePause(); long before = d.model.steps;
            d.onFrame(); check(before == d.model.steps && !d.running,"Pause freezes simulation");
            d.selected = 4; d.pulse(); check(d.model.stimulus[4]>3,"Pulse selected node");
            d.reset(); check(d.selected == -1 && d.trace.size == 0,"Reset clears selection and history");
            for (String name : new String[]{"Sphere","Orbit","Helix"}) {
                d.field.layout = name;
                for (Dimension size : new Dimension[]{new Dimension(1420,1000),new Dimension(1050,740)}) {
                    d.setSize(size); GodMindInteractiveVisualizer.layoutTree(d);
                    BufferedImage image = new BufferedImage(size.width,size.height,BufferedImage.TYPE_INT_RGB);
                    Graphics2D g = image.createGraphics(); d.printAll(g); g.dispose();
                    check(d.field.px.length == d.model.count,"Every node projected in "+name);
                    for (double x : d.field.px) check(Double.isFinite(x),"Finite responsive projection");
                }
            }
            d.field.project(); int x = (int)d.field.px[10], y = (int)d.field.py[10];
            d.field.dispatchEvent(new MouseEvent(d.field,MouseEvent.MOUSE_PRESSED,0,0,x,y,1,false));
            d.field.dispatchEvent(new MouseEvent(d.field,MouseEvent.MOUSE_RELEASED,0,0,x,y,1,false));
            check(d.selected >= 0,"Click selects a visible node");
            d.togglePause(); check(d.running,"Resume enables simulation");
            d.endpoint.setText("invalid"); d.checkConnection(); check(!d.checking,"Invalid URL leaves check button usable");
        });
        System.out.println("PASS: pause, resume, pulse, selection, responsive rendering, all three layouts");
    }
    static HttpResponse<String> get(HttpClient client,String url) throws Exception {
        return client.send(HttpRequest.newBuilder(URI.create(url)).timeout(Duration.ofSeconds(4)).build(),HttpResponse.BodyHandlers.ofString());
    }
    static void awaitCheck() throws Exception {
        for (int i=0;i<120;i++) { AtomicReference<Boolean> busy = new AtomicReference<>(); edt(() -> busy.set(ui.get().checking)); if (!busy.get()) return; Thread.sleep(50); }
        throw new AssertionError("Connection check did not finish");
    }
    static void networkTests() throws Exception {
        HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build();
        GodMindInteractiveVisualizer.Telemetry telemetry = new GodMindInteractiveVisualizer.Telemetry();
        int port;
        try {
            telemetry.state = new GodMindInteractiveVisualizer.Model(24).json(true); port = telemetry.start(0);
            String url = "http://127.0.0.1:"+port;
            check(get(client,url+"/health").statusCode()==200,"Health route");
            check(get(client,url+"/api/state").body().contains("\"nodeCount\":24"),"Actual model telemetry");
            check(get(client,url+"/health/extra").statusCode()==404,"Exact path validation");
            HttpResponse<String> rejected = client.send(HttpRequest.newBuilder(URI.create(url+"/api/state")).POST(HttpRequest.BodyPublishers.noBody()).build(),HttpResponse.BodyHandlers.ofString());
            check(rejected.statusCode()==405,"API cannot mutate engine");
        } finally { telemetry.close(); }
        HttpServer endpoint = HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
        endpoint.createContext("/ok",exchange -> { exchange.sendResponseHeaders(204,-1); exchange.close(); });
        endpoint.createContext("/fail",exchange -> { exchange.sendResponseHeaders(503,-1); exchange.close(); });
        endpoint.start();
        String base = "http://127.0.0.1:"+endpoint.getAddress().getPort();
        try {
            edt(() -> { ui.get().endpoint.setText(base+"/ok"); ui.get().checkConnection(); }); awaitCheck();
            edt(() -> check(ui.get().netBadge.getText().equals("NET / ONLINE"),"Successful real HTTP check reported online"));
            edt(() -> { ui.get().endpoint.setText(base+"/fail"); ui.get().checkConnection(); }); awaitCheck();
            edt(() -> check(ui.get().netBadge.getText().equals("NET / CHECK FAILED"),"HTTP failure honestly reported"));
        } finally { endpoint.stop(0); }
        edt(() -> { ui.get().endpoint.setText(base+"/ok"); ui.get().checkConnection(); }); awaitCheck();
        edt(() -> { check(ui.get().netBadge.getText().equals("NET / CHECK FAILED"),"Connection refusal honestly reported"); check(ui.get().checkNet.isEnabled(),"Retry available after connection failure"); });
        edt(() -> { ui.get().setTelemetry(true); check(ui.get().telemetry.server != null,"Start local feed from control"); ui.get().setTelemetry(false); check(ui.get().telemetry.server == null,"Stop local feed from control"); });
        System.out.println("PASS: actual HTTP requests, JSON feed, endpoint success/failure/refusal, telemetry controls");
    }
    public static void main(String[] args) throws Exception {
        try {
            modelTests(); uiTests();
            if (args.length == 0 || !args[0].equals("--offline")) networkTests();
        } finally { if (ui.get()!=null) edt(() -> ui.get().close()); }
        System.out.println("ALL CHECKS PASSED ("+checks+")");
    }
}
