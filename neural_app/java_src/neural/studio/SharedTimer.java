package neural.studio;
import java.awt.event.*;
/** Swing timer logic is ticked by Neural App's shared scheduler, never its own loop. */
public class SharedTimer extends javax.swing.Timer {
 private boolean enabled=false;private long next=0;private final String owner;
 public SharedTimer(int delay,ActionListener listener){super(delay,listener);owner=Bridge.scope.get();Bridge.timers.add(this);}
 @Override public void start(){enabled=true;next=0;} @Override public void stop(){enabled=false;}
 @Override public boolean isRunning(){return enabled;} @Override public void restart(){stop();start();}
 public void tick(String selected,long now){if(!enabled||!owner.equals(selected)||now<next)return;next=now+Math.max(20,getDelay());for(ActionListener l:getActionListeners())l.actionPerformed(new ActionEvent(this,0,"shared-tick"));if(!isRepeats())enabled=false;}
}
