package neural.studio;
import java.awt.*;
/** Dialog messages are returned to the app UI; they never create a separate window. */
public class SectionDialogs {
 public static void showMessageDialog(Component c,Object text){Bridge.messages.add(String.valueOf(text));}
 public static void showMessageDialog(Component c,Object text,String title,int kind){Bridge.messages.add(title+": "+text);}
 public static void showMessageDialog(Component c,Object text,String title,int kind,javax.swing.Icon icon){showMessageDialog(c,text,title,kind);}
 public static int showConfirmDialog(Component c,Object text,String title,int options){Bridge.messages.add(title+": "+text);return Bridge.confirmValue;}
 public static int showConfirmDialog(Component c,Object text,String title,int options,int kind){return showConfirmDialog(c,text,title,options);}
 public static String showInputDialog(Component c,Object text){Bridge.messages.add(String.valueOf(text));return Bridge.inputValue;}
 public static String showInputDialog(Component c,Object text,Object value){return showInputDialog(c,text);}
 public static Object showInputDialog(Component c,Object text,String title,int kind,javax.swing.Icon icon,Object[] choices,Object value){return showInputDialog(c,text);}
}
