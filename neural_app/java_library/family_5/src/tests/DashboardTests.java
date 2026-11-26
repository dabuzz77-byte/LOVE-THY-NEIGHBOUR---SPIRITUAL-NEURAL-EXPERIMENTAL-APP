import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.nio.file.Path;
import java.time.Duration;
import java.util.*;
import java.util.List;

public final class DashboardTests {
    private static int checks;
    private static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception{
        try(LocalTestServer server=new LocalTestServer();GridEngine engine=new GridEngine()){
            ResonanceDashboard[] view=new ResonanceDashboard[1];
            List<Endpoint> endpoints=List.of(server.endpoint("Local · healthy","/sync"),server.endpoint("Local · delayed","/delayed"),
                    server.endpoint("Local · rejection","/reject"),server.endpoint("Local · created","/created"),
                    server.endpoint("Local · no content","/no-content"),server.endpoint("Local · redirect","/redirect"));
            try{
                SwingUtilities.invokeAndWait(()->{
                    view[0]=new ResonanceDashboard(engine);List<Component> controls=controls(view[0]);
                    check(!button(controls,"Send once").isEnabled(),"No dispatch without endpoints");
                    view[0].setEndpoints(endpoints);check(button(controls,"Send once").isEnabled(),"Configured endpoints enable sending");
                    button(controls,"Request composer").doClick();
                    JTextField signature=controls.stream().filter(c->c instanceof JTextField f&&f.getText().equals("local-operator")).map(c->(JTextField)c).findFirst().orElseThrow();
                    signature.setText("test \"operator\"");
                    check(controls.stream().filter(JTextArea.class::isInstance).map(JTextArea.class::cast).anyMatch(a->a.getText().contains("test \\\"operator\\\"")),"Composer previews escaped JSON");
                    button(controls,"Activity").doClick();button(controls,"Send once").doClick();
                    check(!button(controls,"+ Add").isEnabled(),"Endpoint edits disabled during dispatch");
                    check(button(controls,"Cancel").isEnabled(),"Cancellation enabled while active");
                });
                check(engine.awaitIdle(Duration.ofSeconds(10)),"UI-triggered HTTP batch completes");
                SwingUtilities.invokeAndWait(()->{
                    view[0].accept(engine.snapshot());List<Component> controls=controls(view[0]);
                    check(engine.snapshot().succeeded()==4&&engine.snapshot().completed()==6,"UI displays actual mixed HTTP results");
                    check(button(controls,"+ Add").isEnabled(),"Controls recover after completion");
                    check(controls.stream().filter(JTable.class::isInstance).map(JTable.class::cast).anyMatch(t->t.getRowCount()>=12),"Activity table populated from real events");
                    if(args.length>0){try{render(view[0],1460,980,Path.of(args[0]));if(args.length>1)render(view[0],1150,790,Path.of(args[1]));if(args.length>2){button(controls,"Request composer").doClick();render(view[0],1460,980,Path.of(args[2]));button(controls,"Activity").doClick();}}catch(Exception e){throw new RuntimeException(e);}}
                    button(controls,"Start loop").doClick();check(button(controls,"Stop loop").isEnabled(),"Repeat mode can be stopped");
                    button(controls,"Cancel").doClick();check(!engine.snapshot().active(),"Cancel stops the batch and repeat loop");
                    button(controls,"Clear history").doClick();check(engine.snapshot().events().isEmpty(),"Clear history action works");
                });
            }finally{if(view[0]!=null)SwingUtilities.invokeAndWait(view[0]::close);}
        }
        System.out.println("PASS: "+checks+" dashboard interaction checks using real localhost responses");
    }
    private static JButton button(List<Component> controls,String name){return controls.stream().filter(c->c instanceof JButton b&&name.equals(b.getText())).map(c->(JButton)c).findFirst().orElseThrow();}
    private static List<Component> controls(Container c){List<Component> out=new ArrayList<>();for(Component child:c.getComponents()){out.add(child);if(child instanceof Container nested)out.addAll(controls(nested));}return out;}
    private static void layout(Container c){c.doLayout();for(Component child:c.getComponents())if(child instanceof Container nested)layout(nested);}
    private static void render(JPanel panel,int width,int height,Path path)throws Exception{panel.setSize(width,height);layout(panel);BufferedImage image=new BufferedImage(width,height,BufferedImage.TYPE_INT_RGB);Graphics2D g=image.createGraphics();panel.printAll(g);g.dispose();ImageIO.write(image,"png",path.toFile());}
}
