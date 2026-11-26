package neural.studio;
import javax.swing.*;import javax.swing.text.JTextComponent;
import java.awt.*;import java.awt.event.*;import java.awt.image.BufferedImage;
import java.io.*;import java.lang.reflect.*;import java.net.*;import java.nio.file.*;import java.util.*;import java.util.List;import java.util.concurrent.*;
import javax.imageio.ImageIO;

/** Shared library boundary: native DOM controls and individual graphics, no windows. */
public final class Bridge {
 public static final ThreadLocal<String> scope=ThreadLocal.withInitial(()->"");
 public static final List<SharedTimer> timers=new CopyOnWriteArrayList<>();
 public static final List<SharedScheduler.Task> tasks=new CopyOnWriteArrayList<>();
 public static final List<String> messages=new CopyOnWriteArrayList<>();
 public static String filePath=null,inputValue=null;
 public static int confirmValue=javax.swing.JOptionPane.CANCEL_OPTION;
 public static Broker broker=null;
 public static String dispatch(String section,String payload){return broker==null?"{\"status\":\"awaiting shared runtime\"}":broker.apply(section,payload);}
 private static final Set<String> paused=ConcurrentHashMap.newKeySet();
 public static void setPaused(String id,boolean value){if(value)paused.add(id);else paused.remove(id);}
 private static final Map<String,Object> roots=new LinkedHashMap<>();
 private static final Map<String,IdentityHashMap<Component,String>> ids=new HashMap<>();
 private static final Map<String,Map<String,Component>> components=new HashMap<>();
 private static final Map<String,ClassLoader> loaders=new HashMap<>();
 private static final Map<String,String> failures=new ConcurrentHashMap<>();
 public static volatile String clipboardText=null;
 public static void copyText(String text){clipboardText=text;}
 public static void browse(URI uri){messages.add("Connection URL: "+uri);}
 public static void register(String family,String directory)throws Exception{
  loaders.put(family,new URLClassLoader(new URL[]{Paths.get(directory).toUri().toURL()},Bridge.class.getClassLoader()));
 }
 private static Object construct(Class<?> type,int depth)throws Exception{
  if(depth>4)throw new IllegalArgumentException("Supply an explicit constructor for "+type.getName());
  Constructor<?>[] cs=type.getDeclaredConstructors();Arrays.sort(cs,Comparator.comparingInt(Constructor::getParameterCount));Exception last=null;
  for(Constructor<?> c:cs){try{c.setAccessible(true);Class<?>[] types=c.getParameterTypes();Object[] args=new Object[types.length];
   for(int i=0;i<types.length;i++){
    Class<?> t=types[i];args[i]=t==boolean.class?false:t==int.class?64:t==long.class?64L:t==double.class?.5:t==String.class?"Neural App":t.isInterface()?null:construct(t,depth+1);
   }
   return c.newInstance(args);
  }catch(Exception e){last=e;}}
  throw last==null?new IllegalArgumentException("No constructor"):last;
 }
 public static String open(String id,String family,String className)throws Exception{
  scope.set(id);messages.clear();
  if(!roots.containsKey(id)){
   Object root=construct(Class.forName(className,true,loaders.get(family)),0);
   roots.put(id,root);ids.put(id,new IdentityHashMap<>());components.put(id,new LinkedHashMap<>());
   if(root instanceof Component c){c.setSize(1320,900);layout(c);}
  }
  return describe(id);
 }
 private static void layout(Component c){if(c instanceof Container p){p.doLayout();for(Component child:p.getComponents())layout(child);}}
 public static String describe(String id)throws Exception{
  Object root=roots.get(id);if(root==null)throw new IllegalArgumentException("Section is not loaded");
  Map<String,Object> result=new LinkedHashMap<>();result.put("id",id);result.put("windows",Window.getWindows().length);
  if(root instanceof Component c){layout(c);result.put("ui",walk(id,c,0));}else if(root.getClass().getSimpleName().equals("SubstrateNetworkBus")){result.put("ui",Map.of("type","group","children",List.of(Map.of("id","method:audit","type","button","text","Refresh substrate metrics","enabled",true))));}else{result.put("ui",Map.of("type","engine","class",root.getClass().getName()));}
  if(clipboardText!=null)result.put("clipboard",clipboardText);result.put("messages",new ArrayList<>(messages));result.put("failure",failures.get(id));result.put("engine_fields",fields(root,0,new IdentityHashMap<>()));
  return json(result);
 }
 private static String componentId(String id,Component c){
  IdentityHashMap<Component,String> map=ids.get(id);String key=map.get(c);
  if(key==null){key="c"+map.size();map.put(c,key);components.get(id).put(key,c);}return key;
 }
 private static boolean customPaint(Component c){
  if(!(c instanceof JPanel)||c.getClass().getName().startsWith("javax."))return false;
  try{c.getClass().getDeclaredMethod("paintComponent",Graphics.class);return true;}catch(Exception e){return false;}
 }
 private static Dimension drawingSize(Component c){
  Dimension p=c.getPreferredSize();
  return new Dimension(c.getWidth()>16?c.getWidth():p.width>16?p.width:850,c.getHeight()>16?c.getHeight():p.height>16?p.height:600);
 }
 private static Object walk(String id,Component c,int depth){
  if(depth>28)return null;Map<String,Object> m=new LinkedHashMap<>();m.put("id",componentId(id,c));m.put("enabled",c.isEnabled());
  String name=c.getName();if(name!=null)m.put("name",name);
  if(c instanceof AbstractButton b){m.put("type",b instanceof JCheckBox||b instanceof JRadioButton||b instanceof JToggleButton?"toggle":"button");m.put("text",b.getText());m.put("selected",b.isSelected());}
  else if(c instanceof JLabel b){m.put("type","label");m.put("text",b.getText());}
  else if(c instanceof JTextComponent b){m.put("type",b.isEditable()?(b instanceof JTextField?"input":"textarea"):"output");m.put("password",b instanceof JPasswordField);m.put("value",b.getText());}
  else if(c instanceof JComboBox<?> b){m.put("type","select");List<String> items=new ArrayList<>();for(int i=0;i<b.getItemCount();i++)items.add(String.valueOf(b.getItemAt(i)));m.put("items",items);m.put("selected",b.getSelectedIndex());m.put("editable",b.isEditable());m.put("value",String.valueOf(b.getSelectedItem()));}
  else if(c instanceof JSpinner b){m.put("type","number");m.put("value",b.getValue());if(b.getModel() instanceof SpinnerNumberModel n){m.put("min",n.getMinimum());m.put("max",n.getMaximum());m.put("step",n.getStepSize());}}
  else if(c instanceof JSlider b){m.put("type","range");m.put("value",b.getValue());m.put("min",b.getMinimum());m.put("max",b.getMaximum());}
  else if(c instanceof JProgressBar b){m.put("type","progress");m.put("value",b.getValue());m.put("max",b.getMaximum());m.put("text",b.getString());}
  else if(c instanceof JTable b){m.put("type","table");List<String> columns=new ArrayList<>();List<Object> rows=new ArrayList<>();for(int i=0;i<b.getColumnCount();i++)columns.add(b.getColumnName(i));for(int r=0;r<Math.min(500,b.getRowCount());r++){List<String> row=new ArrayList<>();for(int i=0;i<b.getColumnCount();i++)row.add(String.valueOf(b.getValueAt(r,i)));rows.add(row);}m.put("columns",columns);m.put("rows",rows);m.put("selected",b.getSelectedRow());}
  else if(c instanceof JList<?> b){m.put("type","list");List<String> items=new ArrayList<>();for(int i=0;i<Math.min(500,b.getModel().getSize());i++)items.add(String.valueOf(b.getModel().getElementAt(i)));m.put("items",items);m.put("selected",b.getSelectedIndex());}
  else if(c instanceof JTabbedPane b){m.put("type","tabs");List<Object> tabs=new ArrayList<>();for(int i=0;i<b.getTabCount();i++)tabs.add(Map.of("title",b.getTitleAt(i),"body",walk(id,b.getComponentAt(i),depth+1)));m.put("tabs",tabs);m.put("selected",b.getSelectedIndex());}
  else if(customPaint(c)){Dimension d=drawingSize(c);m.put("type","graphic");m.put("class",c.getClass().getSimpleName());m.put("width",d.width);m.put("height",d.height);}
  else if(c instanceof Container b){m.put("type","group");String title="";if(c instanceof JComponent j&&j.getBorder() instanceof javax.swing.border.TitledBorder t)title=t.getTitle();m.put("title",title);List<Object> children=new ArrayList<>();for(Component child:b.getComponents()){if(child instanceof JScrollBar||child instanceof JSeparator)continue;Object item=walk(id,child,depth+1);if(item!=null)children.add(item);}m.put("children",children);}
  else m.put("type","empty");
  if(c instanceof JComponent j&&j.getToolTipText()!=null)m.put("hint",j.getToolTipText());return m;
 }
 public static String action(String id,String component,String action,String value,String path)throws Exception{
    scope.set(id);messages.clear();clipboardText=null;filePath=path==null||path.isBlank()?null:path;
    if(component.equals("method:audit")&&roots.get(id).getClass().getSimpleName().equals("SubstrateNetworkBus")){Method m=roots.get(id).getClass().getDeclaredMethod("executeSubstrateDiscoveryAudit");m.setAccessible(true);m.invoke(roots.get(id));return describe(id);}
    Component c=components.get(id).get(component);if(c==null)throw new IllegalArgumentException("Control no longer exists");
  if(!c.isEnabled())throw new IllegalArgumentException("Control is disabled");
  if(action.equals("click")&&c instanceof AbstractButton b)b.doClick(0);
  else if(action.equals("set")){
   if(c instanceof JTextComponent b)b.setText(value);
   else if(c instanceof JComboBox<?> b)b.setSelectedIndex(Integer.parseInt(value));
   else if(c instanceof JSlider b)b.setValue(Integer.parseInt(value));
   else if(c instanceof JSpinner b){Object old=b.getValue();b.setValue(old instanceof Integer?Integer.valueOf(value):Double.valueOf(value));}
   else if(c instanceof JTabbedPane b)b.setSelectedIndex(Integer.parseInt(value));
   else if(c instanceof JTable b)b.setRowSelectionInterval(Integer.parseInt(value),Integer.parseInt(value));
   else if(c instanceof JList<?> b)b.setSelectedIndex(Integer.parseInt(value));
   else throw new IllegalArgumentException("Control is not editable");
  }else if(action.equals("set_text")&&c instanceof JComboBox<?> b&&b.isEditable()){b.setSelectedItem(value);
  }else if(action.equals("key")){
   KeyStroke stroke=KeyStroke.getKeyStroke(value);if(stroke==null)throw new IllegalArgumentException("Unknown key");boolean handled=false;
   for(Component parent=c;parent!=null&&!handled;parent=parent.getParent())if(parent instanceof JComponent jc)for(int condition:new int[]{JComponent.WHEN_FOCUSED,JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT,JComponent.WHEN_IN_FOCUSED_WINDOW}){Object key=jc.getInputMap(condition).get(stroke);Action callback=key==null?null:jc.getActionMap().get(key);if(callback!=null&&callback.isEnabled()){callback.actionPerformed(new ActionEvent(c,ActionEvent.ACTION_PERFORMED,String.valueOf(key)));handled=true;break;}}
   if(!handled){KeyEvent event=new KeyEvent(c,KeyEvent.KEY_PRESSED,System.currentTimeMillis(),stroke.getModifiers(),stroke.getKeyCode(),KeyEvent.CHAR_UNDEFINED);for(KeyListener listener:c.getKeyListeners())listener.keyPressed(event);}
  }else if(action.equals("double")){int row=Integer.parseInt(value);if(c instanceof JTable b){b.setRowSelectionInterval(row,row);Rectangle r=b.getCellRect(row,0,true);b.dispatchEvent(new MouseEvent(b,MouseEvent.MOUSE_CLICKED,System.currentTimeMillis(),0,r.x+2,r.y+2,2,false,MouseEvent.BUTTON1));}else if(c instanceof JList<?> b){b.setSelectedIndex(row);Rectangle r=b.getCellBounds(row,row);b.dispatchEvent(new MouseEvent(b,MouseEvent.MOUSE_CLICKED,System.currentTimeMillis(),0,r.x+2,r.y+2,2,false,MouseEvent.BUTTON1));}}else if(action.equals("enter")&&c instanceof JTextField b)b.postActionEvent();
  else if(action.equals("pointer")||action.equals("drag")||action.equals("wheel")){String[] p=value.split(",");int x=Integer.parseInt(p[0]),y=Integer.parseInt(p[1]);long now=System.currentTimeMillis();
   if(action.equals("wheel"))c.dispatchEvent(new MouseWheelEvent(c,MouseEvent.MOUSE_WHEEL,now,0,x,y,0,false,MouseWheelEvent.WHEEL_UNIT_SCROLL,1,Integer.parseInt(p[2])));
   else {c.dispatchEvent(new MouseEvent(c,MouseEvent.MOUSE_PRESSED,now,MouseEvent.BUTTON1_DOWN_MASK,x,y,1,false,MouseEvent.BUTTON1));if(action.equals("drag")){x=Integer.parseInt(p[2]);y=Integer.parseInt(p[3]);c.dispatchEvent(new MouseEvent(c,MouseEvent.MOUSE_DRAGGED,now,MouseEvent.BUTTON1_DOWN_MASK,x,y,0,false,MouseEvent.NOBUTTON));}c.dispatchEvent(new MouseEvent(c,MouseEvent.MOUSE_RELEASED,now,0,x,y,1,false,MouseEvent.BUTTON1));if(action.equals("pointer"))c.dispatchEvent(new MouseEvent(c,MouseEvent.MOUSE_CLICKED,now,0,x,y,1,false,MouseEvent.BUTTON1));}}
  else throw new IllegalArgumentException("Unsupported control operation");
  tick(id);return describe(id);
 }
 public static void tickAll(){for(String id:new ArrayList<>(roots.keySet()))tick(id);}
 public static void tick(String id){if(paused.contains(id))return;scope.set(id);long now=System.currentTimeMillis();
  for(SharedTimer t:timers){try{t.tick(id,now);}catch(Throwable e){failures.put(id,e.toString());}}
  for(SharedScheduler.Task t:tasks){if(!t.cancelled&&!t.completed&&!t.running&&t.owner.equals(id)&&now>=t.next){t.running=true;t.next=now+Math.max(20,t.interval);try{SharedSwingWorker.workers.execute(()->{scope.set(id);try{t.run.run();}catch(Throwable error){failures.put(id,error.toString());}finally{t.running=false;if(t.interval==0)t.completed=true;}});}catch(RejectedExecutionException busy){t.running=false;t.next=now+200;}}}
 }
 public static String graphicSvg(String id,String key)throws Exception{
  scope.set(id);Component c=components.get(id).get(key);
  if(c==null||!customPaint(c))throw new IllegalArgumentException("Drawing is unavailable");
  tick(id);
  Dimension previous=c.getSize(),d=drawingSize(c);c.setSize(d);
  org.jfree.svg.SVGGraphics2D g=new org.jfree.svg.SVGGraphics2D(d.width,d.height);
  try{Method paint=c.getClass().getDeclaredMethod("paintComponent",Graphics.class);paint.setAccessible(true);paint.invoke(c,g);return g.getSVGElement();}
  finally{g.dispose();c.setSize(previous);}
 }
 public static byte[] graphic(String id,String key,int width,int height)throws Exception{
  scope.set(id);Component c=components.get(id).get(key);if(c==null||!customPaint(c))throw new IllegalArgumentException("Graphic no longer exists");
  tick(id);
   // Paint in the section's native layout coordinates; scale the image, never the model.
   int nativeWidth=Math.max(1,c.getWidth()),nativeHeight=Math.max(1,c.getHeight());
   double scale=Math.min(1.0,Math.min(1600.0/nativeWidth,900.0/nativeHeight));
   int outputWidth=Math.max(1,(int)Math.round(nativeWidth*scale)),outputHeight=Math.max(1,(int)Math.round(nativeHeight*scale));
  BufferedImage image=new BufferedImage(outputWidth,outputHeight,BufferedImage.TYPE_INT_RGB);Graphics2D g=image.createGraphics();g.setColor(new Color(8,14,23));g.fillRect(0,0,image.getWidth(),image.getHeight());g.scale(scale,scale);
  Method paint=c.getClass().getDeclaredMethod("paintComponent",Graphics.class);paint.setAccessible(true);paint.invoke(c,g);g.dispose();ByteArrayOutputStream out=new ByteArrayOutputStream();ImageIO.write(image,"png",out);return out.toByteArray();
 }
 private static Object fields(Object value,int depth,IdentityHashMap<Object,Boolean> seen){
  if(value==null||value instanceof String||value instanceof Number||value instanceof Boolean)return value;
  if(value instanceof java.util.concurrent.atomic.AtomicReference<?> r)return fields(r.get(),depth+1,seen);
  if(value instanceof Enum<?>)return value.toString();if(depth>3||seen.put(value,true)!=null)return null;
  Class<?> type=value.getClass();if((value instanceof Component&&type.getName().startsWith("javax."))||value instanceof Thread||value instanceof ExecutorService||type.getName().startsWith("java.awt"))return null;
  if(type.isArray()){List<Object> result=new ArrayList<>();for(int i=0;i<Math.min(160,Array.getLength(value));i++)result.add(fields(Array.get(value,i),depth+1,seen));return result;}
  if(value instanceof Collection<?> c){List<Object> result=new ArrayList<>();int i=0;for(Object v:c){if(i++>=100)break;result.add(fields(v,depth+1,seen));}return result;}
  if(type.getName().startsWith("java."))return String.valueOf(value);
  Map<String,Object> out=new LinkedHashMap<>();for(Field f:type.getDeclaredFields())try{if(Modifier.isStatic(f.getModifiers())||f.getName().startsWith("this$")||f.getName().matches("(?i).*password|.*secret|.*token|.*key"))continue;f.setAccessible(true);Object v=fields(f.get(value),depth+1,seen);if(v!=null)out.put(f.getName(),v);}catch(Exception e){}return out;
 }
 public static String json(Object o){if(o==null)return "null";if(o instanceof Double d&&!Double.isFinite(d)||o instanceof Float f&&!Float.isFinite(f))return "null";if(o instanceof Boolean||o instanceof Number)return o.toString();if(o instanceof Map<?,?> m){List<String> a=new ArrayList<>();m.forEach((k,v)->a.add(json(String.valueOf(k))+":"+json(v)));return "{"+String.join(",",a)+"}";}if(o instanceof Collection<?> c){List<String>a=new ArrayList<>();for(Object v:c)a.add(json(v));return "["+String.join(",",a)+"]";}return "\""+o.toString().replace("\\","\\\\").replace("\"","\\\"").replace("\r","\\r").replace("\n","\\n").replace("\t","\\t")+"\"";}
 public static int coupleRuntime(String id,double signal,double magnitude)throws Exception{
  Object root=roots.get(id);if(!(root instanceof Component c))return 0;
  return coupleComponent(c,Math.max(-1,Math.min(1,signal)),Math.max(0,Math.min(1,magnitude)));
 }
 private static int coupleComponent(Component c,double signal,double magnitude)throws Exception{
  int count=0;
  // Explicitly supported drawing callback; no financial or external-system state is altered.
  if(c.getClass().getName().equals("WaveVisualizerPanel")){
   c.getClass().getMethod("updateGraphicsState",double.class,double.class).invoke(c,signal,magnitude*100);count++;
  }
  if(c instanceof Container p)for(Component child:p.getComponents())count+=coupleComponent(child,signal,magnitude);
  return count;
 }
 public static String stats(){return json(Map.of("sections",roots.size(),"shared_timers",timers.size(),"shared_tasks",tasks.size(),"native_windows",Window.getWindows().length));}
 public static void close(){for(String id:roots.keySet()){scope.set(id);Object root=roots.get(id);try{if(root instanceof AutoCloseable c)c.close();else {try{root.getClass().getMethod("close").invoke(root);}catch(NoSuchMethodException ignored){}}}catch(Exception e){}}timers.forEach(SharedTimer::stop);tasks.clear();SharedSwingWorker.workers.shutdownNow();}
}
