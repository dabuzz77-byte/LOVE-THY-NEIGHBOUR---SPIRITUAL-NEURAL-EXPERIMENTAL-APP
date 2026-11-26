package neural.studio;
import javax.swing.*;import java.awt.*;import java.io.*;
/** Export/import paths are supplied through the unified app, without native dialogs. */
public class SectionFileChooser extends JFileChooser {
 public SectionFileChooser(){super();}public SectionFileChooser(String p){super(p);}public SectionFileChooser(File p){super(p);}
 public int showSaveDialog(Component p){if(Bridge.filePath==null){Bridge.messages.add("Choose an export path in the shared section controls.");return CANCEL_OPTION;}setSelectedFile(new File(Bridge.filePath));return APPROVE_OPTION;}
 public int showOpenDialog(Component p){if(Bridge.filePath==null){Bridge.messages.add("Choose an import path in the shared section controls.");return CANCEL_OPTION;}setSelectedFile(new File(Bridge.filePath));return APPROVE_OPTION;}
}
