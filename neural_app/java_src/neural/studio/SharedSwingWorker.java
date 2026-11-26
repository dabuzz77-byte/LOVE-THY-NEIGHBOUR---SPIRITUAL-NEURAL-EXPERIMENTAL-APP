package neural.studio;
import java.util.*;import java.util.concurrent.*;import javax.swing.SwingUtilities;
/** Bounded background I/O shared by every migrated section. */
public abstract class SharedSwingWorker<T,V> {
 public static final ThreadPoolExecutor workers=new ThreadPoolExecutor(2,2,30,TimeUnit.SECONDS,new ArrayBlockingQueue<>(16),r->{Thread t=new Thread(r,"neural-section-io");t.setDaemon(true);return t;});
 private FutureTask<T> future;private String owner;
 protected abstract T doInBackground()throws Exception;
 protected void done(){} protected void process(List<V> chunks){}
 public final void execute(){owner=Bridge.scope.get();future=new FutureTask<>(()->{Bridge.scope.set(owner);try{return doInBackground();}finally{SwingUtilities.invokeLater(()->{Bridge.scope.set(owner);done();});}});workers.execute(future);}
 @SafeVarargs protected final void publish(V...chunks){List<V> items=Arrays.asList(chunks);SwingUtilities.invokeLater(()->{Bridge.scope.set(owner);process(items);});}
 public final T get()throws InterruptedException,ExecutionException{return future.get();}
 public final T get(long time,TimeUnit unit)throws InterruptedException,ExecutionException,TimeoutException{return future.get(time,unit);}
 public final boolean cancel(boolean interrupt){return future!=null&&future.cancel(interrupt);}
 public final boolean isCancelled(){return future!=null&&future.isCancelled();}
 public final boolean isDone(){return future!=null&&future.isDone();}
}
