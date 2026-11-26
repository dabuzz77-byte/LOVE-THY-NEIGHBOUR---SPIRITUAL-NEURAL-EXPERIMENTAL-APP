import java.net.*;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;

public final class GridEngineTests {
    private static int checks;
    private interface Action { void run() throws Exception; }
    private static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    private static void fails(Action action,String message)throws Exception{boolean failed=false;try{action.run();}catch(Exception expected){failed=true;}check(failed,message);}
    private static DispatchPayload payload(){return new DispatchPayload(142857,"test \"signature\"","line 1\nline 2\t\\test ☃");}
    private static GridEngine.Snapshot run(GridEngine engine,List<Endpoint> endpoints,int timeout,int concurrency)throws Exception{
        engine.configure(endpoints);engine.dispatch(payload(),Duration.ofSeconds(timeout),concurrency);
        check(engine.awaitIdle(Duration.ofSeconds(12)),"Batch completes within deadline");return engine.snapshot();
    }
    public static void main(String[] args)throws Exception{
        check(DispatchPayload.quote("a\"\\\n\t\r\u0001").equals("\"a\\\"\\\\\\n\\t\\r\\u0001\""),"JSON control characters escaped");
        check(DispatchPayload.quote("😀").equals("\"\\ud83d\\ude00\""),"Unicode surrogate pairs encoded safely");
        check(payload().json().contains("\"telemetry\""),"Plain telemetry labelled honestly");
        fails(()->new DispatchPayload(-1,"label",""),"Negative session rejected");
        fails(()->new DispatchPayload(1," ",""),"Blank signature rejected");
        fails(()->new DispatchPayload(1,"x","a".repeat(32769)),"Oversized draft rejected");
        fails(()->new DispatchPayload(1,"x","\u0001".repeat(20000)).bytes(),"Encoded size is bounded");
        for(String url:List.of("file:///tmp/x","ftp://example.com/x","https://user:maintainer@example.invalid/x","https://example.com/#x","https:///missing","http://localhost:0/x","http://localhost:99999/x"))fails(()->Endpoint.create("test",url),"Invalid endpoint rejected: "+url);
        fails(()->Endpoint.create("bad\nname","http://localhost"),"Control characters in name rejected");
        check(Endpoint.create("IPv6","http://[::1]:1234/test").uri().getPort()==1234,"IPv6 supported");
        Endpoint endpoint=Endpoint.create("Unicode α","https://example.invalid/api");
        GridConfig config=new GridConfig(List.of(endpoint),6,3,15);
        Path profile=Files.createTempFile("resonance-test-",".properties");
        try{
            config.save(profile);check(GridConfig.load(profile).equals(config),"Configuration round trip preserves UTF-8 and IDs");
            check(!Files.readString(profile).contains("telemetry"),"Draft payload is not persisted in profile");
            Files.writeString(profile,"version=1\ncount=999999\n");fails(()->GridConfig.load(profile),"Untrusted config count bounded");
            Files.writeString(profile,"x".repeat(131073));fails(()->GridConfig.load(profile),"Oversized config rejected");
        }finally{Files.deleteIfExists(profile);}
        fails(()->new GridConfig(List.of(endpoint,endpoint),5,4,10),"Duplicate config endpoints rejected");
        String csv=ResonanceDashboard.csv(List.of(new GridEngine.Event(0,"=evil,\"label\"",GridEngine.State.FAILED,"x")));
        check(csv.contains("\"'=evil,\"\"label\"\"\""),"CSV quoting and formula protection");

        try(LocalTestServer server=new LocalTestServer();GridEngine engine=new GridEngine()){
            fails(()->engine.dispatch(payload(),Duration.ofSeconds(5),4),"Dispatch without endpoints rejected");
            var snapshot=run(engine,server.endpoints(),5,3);
            check(snapshot.completed()==3&&snapshot.succeeded()==2,"Actual 200/202 accepted and 503 rejected");
            check(snapshot.nodes().stream().anyMatch(r->r.state()==GridEngine.State.HTTP_ERROR&&r.code()==503),"Error response never becomes simulated success");
            check(server.requests.get()==3&&server.lastBody.equals(payload().json()),"Real HTTP receiver got exact JSON bytes");
            check(snapshot.payloadBytes()==3L*payload().bytes().length,"Acknowledged request payload bytes counted");
            check(snapshot.nodes().stream().filter(r->r.code()==202).findFirst().orElseThrow().latencyMs()>=550,"Latency measures actual delayed response");
            snapshot=run(engine,List.of(server.endpoint("Created","/created"),server.endpoint("No content","/no-content")),5,2);
            check(snapshot.nodes().stream().allMatch(r->r.state()==GridEngine.State.SUCCESS),"Every 2xx status accepted");
            int before=server.requests.get();snapshot=run(engine,List.of(server.endpoint("Redirect","/redirect")),5,1);
            check(snapshot.nodes().get(0).code()==307&&server.requests.get()==before+1,"POST redirects not followed or duplicated");
            snapshot=run(engine,List.of(server.endpoint("Slow body","/slow-body")),1,1);
            check(snapshot.nodes().get(0).state()==GridEngine.State.TIMED_OUT,"Deadline also bounds response body time");
            check(snapshot.nodes().get(0).latencyMs()<2000,"Body timeout does not wait for the slow server");
            snapshot=run(engine,List.of(server.endpoint("Recovery","/sync")),5,1);
            check(snapshot.nodes().get(0).state()==GridEngine.State.SUCCESS,"Worker recovers after timeout");
            engine.configure(List.of(server.endpoint("Slow header","/timeout")));
            engine.dispatch(payload(),Duration.ofSeconds(1),1);
            fails(()->engine.dispatch(payload(),Duration.ofSeconds(1),1),"Overlapping batch rejected");
            fails(()->engine.configure(List.of()),"Reconfiguration during dispatch rejected");
            fails(engine::clearHistory,"Cannot clear active results");
            check(engine.awaitIdle(Duration.ofSeconds(4)),"Header deadline completes");
            check(engine.snapshot().nodes().get(0).state()==GridEngine.State.TIMED_OUT,"Header timeout explicit");
            engine.configure(List.of(server.endpoint("Cancel running","/timeout"),server.endpoint("Cancel queued","/sync")));
            engine.dispatch(payload(),Duration.ofSeconds(5),1);engine.cancel();
            check(engine.awaitIdle(Duration.ofSeconds(1)),"Cancellation returns promptly");
            check(engine.snapshot().nodes().stream().allMatch(r->r.state()==GridEngine.State.CANCELLED),"Running and queued requests cancelled");
            long cancelledBatch=engine.snapshot().batch();Thread.sleep(80);
            check(engine.snapshot().batch()==cancelledBatch&&engine.snapshot().nodes().stream().noneMatch(r->r.state()==GridEngine.State.SUCCESS),"Late completion cannot overwrite cancellation");
            engine.clearHistory();check(engine.snapshot().events().isEmpty()&&engine.snapshot().completed()==0,"History reset clears metrics");
        }

        try(LocalTestServer server=new LocalTestServer();GridEngine engine=new GridEngine()){
            List<Endpoint> endpoints=new ArrayList<>();for(int i=0;i<6;i++)endpoints.add(server.endpoint("Worker "+i,"/delayed?node="+i));
            run(engine,endpoints,5,2);check(server.peak.get()<=2,"Configured concurrency respected at the receiving server");
            for(int i=0;i<6;i++)endpoints.set(i,server.endpoint("Fast "+i,"/sync?node="+i));
            for(int i=0;i<23;i++)run(engine,endpoints,5,4);
            check(engine.snapshot().history().size()==120,"Chart history bounded under sustained work");
            check(engine.snapshot().events().size()==300,"Event history bounded under sustained work");
            check(engine.snapshot().completed()==144,"Cumulative completion count preserved");
        }
        int closedPort;try(java.net.ServerSocket socket=new java.net.ServerSocket(0,1,InetAddress.getLoopbackAddress())){closedPort=socket.getLocalPort();}
        GridEngine closed=new GridEngine();
        try{
            var result=run(closed,List.of(Endpoint.create("Unavailable","http://127.0.0.1:"+closedPort+"/")),2,1).nodes().get(0);
            check(result.state()==GridEngine.State.FAILED&&result.code()==0,"Connection refusal reported as failure");
        }finally{closed.close();}
        fails(()->closed.configure(List.of()),"Closed engine cannot restart");
        fails(()->closed.dispatch(payload(),Duration.ofSeconds(2),1),"Closed engine cannot dispatch");
        System.out.println("PASS: "+checks+" checks, including real loopback HTTP, deadlines, cancellation, concurrency, and bounded history");
    }
}
