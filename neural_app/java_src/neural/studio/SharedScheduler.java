package neural.studio;
import java.util.*;
import java.util.concurrent.*;
/** Original scheduled callbacks retain their state and timing, sharing one owner. */
public class SharedScheduler extends AbstractExecutorService implements ScheduledExecutorService {
 private boolean stopped=false;private final String owner=Bridge.scope.get();
 static class Task implements ScheduledFuture<Object>{
  final Runnable run;final String owner;final long interval;volatile long next;volatile boolean cancelled=false,running=false,completed=false;
  Task(Runnable r,String o,long delay,long period){run=r;owner=o;interval=period;next=System.currentTimeMillis()+delay;}
  public long getDelay(TimeUnit unit){return unit.convert(next-System.currentTimeMillis(),TimeUnit.MILLISECONDS);}
  public int compareTo(Delayed other){return Long.compare(getDelay(TimeUnit.MILLISECONDS),other.getDelay(TimeUnit.MILLISECONDS));}
  public boolean cancel(boolean interrupt){cancelled=true;return true;}public boolean isCancelled(){return cancelled;}public boolean isDone(){return cancelled||completed;}
  public Object get(){return null;}public Object get(long timeout,TimeUnit unit){return null;}
 }
 public static ScheduledExecutorService newScheduledThreadPool(int n){return new SharedScheduler();}
 public static ScheduledExecutorService newScheduledThreadPool(int n,ThreadFactory f){return new SharedScheduler();}
 public static ScheduledExecutorService newSingleThreadScheduledExecutor(){return new SharedScheduler();}
 public static ScheduledExecutorService newSingleThreadScheduledExecutor(ThreadFactory f){return new SharedScheduler();}
 public ScheduledFuture<?> schedule(Runnable r,long delay,TimeUnit unit){Task t=new Task(r,owner,unit.toMillis(delay),0);Bridge.tasks.add(t);return t;}
 public <V> ScheduledFuture<V> schedule(Callable<V> c,long d,TimeUnit u){throw new UnsupportedOperationException("Callable schedules require an explicit operation");}
 public ScheduledFuture<?> scheduleAtFixedRate(Runnable r,long d,long p,TimeUnit u){Task t=new Task(r,owner,u.toMillis(d),Math.max(20,u.toMillis(p)));Bridge.tasks.add(t);return t;}
 public ScheduledFuture<?> scheduleWithFixedDelay(Runnable r,long d,long p,TimeUnit u){return scheduleAtFixedRate(r,d,p,u);}
 public void execute(Runnable r){if(!stopped)SharedSwingWorker.workers.execute(()->{Bridge.scope.set(owner);r.run();});}public void shutdown(){stopped=true;Bridge.tasks.removeIf(t->{if(t.owner.equals(owner)){t.cancel(true);return true;}return false;});}
 public List<Runnable> shutdownNow(){shutdown();return List.of();}public boolean isShutdown(){return stopped;}public boolean isTerminated(){return stopped;}
 public boolean awaitTermination(long timeout,TimeUnit unit){return true;}
}
