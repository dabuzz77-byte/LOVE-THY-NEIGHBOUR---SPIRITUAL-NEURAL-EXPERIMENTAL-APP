package neural.studio;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;

/** A section controller/container. It never creates an AWT Window or native peer. */
public class SectionFrame extends JPanel {
 public static final int EXIT_ON_CLOSE=3, DISPOSE_ON_CLOSE=2, DO_NOTHING_ON_CLOSE=0;
 public static final int MAXIMIZED_BOTH=6, ICONIFIED=1, NORMAL=0;
 private String title=""; private final java.util.List<WindowListener> listeners=new ArrayList<>();
 public SectionFrame(){super(new BorderLayout());}
 public SectionFrame(String title){this();this.title=title;}
 public void setTitle(String s){title=s;} public String getTitle(){return title;}
 public Container getContentPane(){return this;}
 public void setContentPane(Container c){removeAll();setLayout(new BorderLayout());add(c,BorderLayout.CENTER);}
 public void setDefaultCloseOperation(int n){} public int getDefaultCloseOperation(){return DISPOSE_ON_CLOSE;}
 public void setLocationRelativeTo(Component c){} public void setResizable(boolean b){}
 public void setIconImage(Image i){} public void setExtendedState(int n){} public int getExtendedState(){return 0;}
 public int getState(){return 0;} public void setState(int n){}
 public void pack(){Dimension d=getPreferredSize();setSize(Math.max(1100,d.width),Math.max(760,d.height));}
 public void addWindowListener(WindowListener l){listeners.add(l);} public void removeWindowListener(WindowListener l){listeners.remove(l);}
 public WindowListener[] getWindowListeners(){return listeners.toArray(WindowListener[]::new);}
 public void dispose(){setVisible(false);} public void toFront(){} public void setJMenuBar(JMenuBar bar){add(bar,BorderLayout.NORTH);}
 public void setLocationByPlatform(boolean b){} public void setAlwaysOnTop(boolean b){}
 public void setUndecorated(boolean b){} public void setDefaultLookAndFeelDecorated(boolean b){}
 public JRootPane getRootPane(){return new JRootPane();}
}
