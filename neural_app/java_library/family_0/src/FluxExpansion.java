import neural.studio.*;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.*;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.function.DoubleConsumer;

/** Additive sidebar: the original drawing and SEND/RECEIVE paths remain untouched. */
final class FluxExpansion extends JPanel implements AutoCloseable {
 static final Color BG=new Color(7,12,22),PANEL=new Color(15,24,38),EDGE=new Color(40,65,91),TEXT=new Color(228,239,250),MUTED=new Color(137,160,183),CYAN=new Color(67,220,239),AMBER=new Color(255,183,91);
 final DoubleConsumer perturb;
 final FluxBusLink link;
 final BinaryGrid grid=new BinaryGrid();
 final JTextArea messages=area(),processes=area(),commentary=area();
 final JLabel bus=new JLabel("Bus starting..."),flux=new JLabel("FluxBus v2: connecting..."),observatory=new JLabel("Observatory v4: connecting...");
 final JComboBox<String> targets=new JComboBox<>(new String[]{"all","FluxBus-v2","Observatory-v4"});
 final JComboBox<String> models=new JComboBox<>();
 JSplitPane lowerSplit;
 final JPanel commentPanel=new JPanel(new BorderLayout(4,4));
 final JCheckBox commentToggle=new JCheckBox("Llama commentary");
 final ArrayBlockingQueue<Map<String,Object>> pending=new ArrayBlockingQueue<>(256);
 final neural.studio.SharedTimer drain;
 final Random random=new Random();
 final ArrayDeque<Transfer> transfers=new ArrayDeque<>();
 long frames,simSequence,sendCount,receiveCount,externalCount;
 double currentActivity,currentRandom;
 boolean closed;
 record Transfer(long due,long id,int bits,double energy){}
 FluxExpansion(DoubleConsumer perturb){
  this.perturb=perturb;setLayout(new BorderLayout(7,7));setBackground(PANEL);setPreferredSize(new Dimension(328,650));setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(EDGE),new EmptyBorder(10,10,10,10)));
  JPanel top=new JPanel(new BorderLayout(4,4));top.setOpaque(false);top.add(grid,BorderLayout.NORTH);
  JPanel labels=new JPanel(new GridLayout(0,1,0,4));labels.setOpaque(false);
  for(JLabel label:new JLabel[]{bus,flux,observatory}){label.setForeground(MUTED);label.setFont(new Font(Font.SANS_SERIF,Font.PLAIN,11));labels.add(label);}
  commentToggle.setToolTipText("Local Llama commentary updates about every 20 seconds; off stops requests.");commentToggle.setOpaque(false);commentToggle.setForeground(TEXT);labels.add(commentToggle);top.add(labels,BorderLayout.CENTER);add(top,BorderLayout.NORTH);
  JTabbedPane tabs=new JTabbedPane();JPanel msg=new JPanel(new BorderLayout(4,4));msg.setOpaque(false);msg.add(scroll(messages),BorderLayout.CENTER);
  JPanel compose=new JPanel(new BorderLayout(4,4));compose.setOpaque(false);targets.setEditable(true);targets.setToolTipText("all, FluxBus-v2, Observatory-v4, or a connected process PID");compose.add(targets,BorderLayout.NORTH);
  JTextField input=new JTextField();input.setToolTipText("Send information to the selected connected process or application");JButton send=new JButton("Send");
  JPanel entry=new JPanel(new BorderLayout(4,0));entry.add(input,BorderLayout.CENTER);entry.add(send,BorderLayout.EAST);compose.add(entry,BorderLayout.SOUTH);msg.add(compose,BorderLayout.SOUTH);
  tabs.addTab("Messages",msg);tabs.addTab("Processes",scroll(processes));
  tabs.setMinimumSize(new Dimension(180,96));
  lowerSplit=new JSplitPane(JSplitPane.VERTICAL_SPLIT,tabs,null);lowerSplit.setOpaque(false);lowerSplit.setBorder(null);lowerSplit.setDividerSize(0);lowerSplit.setResizeWeight(.55);add(lowerSplit,BorderLayout.CENTER);
  JPanel modelControls=new JPanel(new BorderLayout(4,0));JButton refresh=new JButton("Refresh");modelControls.add(models,BorderLayout.CENTER);modelControls.add(refresh,BorderLayout.EAST);
  commentPanel.setOpaque(false);commentPanel.add(modelControls,BorderLayout.NORTH);commentPanel.add(scroll(commentary),BorderLayout.CENTER);commentPanel.setPreferredSize(new Dimension(300,195));commentPanel.setMinimumSize(new Dimension(180,90));commentPanel.setVisible(false);
  commentary.setText("Turn on commentary to describe recent stochastic events with a local Llama model.");
  link=new FluxBusLink(e->{if(!pending.offer(e)){pending.poll();pending.offer(e);}},(name,value)->edt(()->{switch(name){case "flux"->flux.setText(value);case "observatory"->observatory.setText(value);case "ledger"->flux.setToolTipText(value);default->bus.setText(value);}}),text->edt(()->{processes.setText(text);processes.setCaretPosition(0);}),list->edt(()->{Object selected=models.getSelectedItem();models.removeAllItems();for(String name:list)models.addItem(name);if(selected!=null&&list.contains(selected.toString()))models.setSelectedItem(selected);configureCommentary();}),text->edt(()->{if(commentToggle.isSelected()){commentary.setText(text);commentary.setCaretPosition(0);}}));
  send.addActionListener(e->{String text=input.getText().trim();if(text.isEmpty())return;String target=String.valueOf(targets.getSelectedItem());if(target.equals("null")||target.isBlank())target="all";
   link.publish("message",Map.of("text",text),target);log("SEND > "+target+": "+text+" (queued; adapter must receive)");input.setText("");});input.addActionListener(e->send.doClick());
  commentToggle.addActionListener(e->{boolean shown=commentToggle.isSelected();commentPanel.setVisible(shown);lowerSplit.setBottomComponent(shown?commentPanel:null);lowerSplit.setDividerSize(shown?5:0);configureCommentary();revalidate();if(shown)SwingUtilities.invokeLater(()->lowerSplit.setDividerLocation(.55));});models.addActionListener(e->configureCommentary());refresh.addActionListener(e->link.workers.execute(link::refreshModels));
  drain=new neural.studio.SharedTimer(100,e->{for(int i=0;i<12;i++){Map<String,Object> event=pending.poll();if(event==null)break;externalCount++;grid.event(event.hashCode(),false,String.valueOf(event.get("source")));perturb.accept(.12);log("RECV < "+event.get("source")+" / "+event.get("topic")+": "+FluxBusLink.shortText(FluxJson.write(event.get("data")),400));}});drain.start();link.start();
 }
 void configureCommentary(){if(link==null)return;Object selected=models.getSelectedItem();link.setCommentary(commentToggle.isSelected(),selected==null?"":selected.toString());if(commentToggle.isSelected()&&selected==null)commentary.setText("No Llama model available. Start Ollama with an installed Llama model, then click Refresh.");}
 static void edt(Runnable r){if(SwingUtilities.isEventDispatchThread())r.run();else SwingUtilities.invokeLater(r);}
 static JTextArea area(){JTextArea a=new JTextArea();a.setEditable(false);a.setLineWrap(true);a.setWrapStyleWord(true);a.setBackground(BG);a.setForeground(TEXT);a.setFont(new Font(Font.MONOSPACED,Font.PLAIN,11));a.setBorder(new EmptyBorder(6,6,6,6));return a;}
 static JScrollPane scroll(JTextArea a){JScrollPane s=new JScrollPane(a);s.setBorder(BorderFactory.createLineBorder(EDGE));s.setPreferredSize(new Dimension(300,140));return s;}
 void log(String text){messages.append(java.time.LocalTime.now().withNano(0)+" "+text+"\n");if(messages.getDocument().getLength()>22000)messages.replaceRange("",0,8000);messages.setCaretPosition(messages.getDocument().getLength());}
 void advance(double activity,double influence,double orbitRotation){
  frames++;currentActivity=activity;currentRandom=influence;
  if(influence>0&&random.nextDouble()<.012+influence*.065){long id=++simSequence;int bits=random.nextInt(256);double energy=Math.min(.7,influence*(.45+random.nextDouble()));
   transfers.addLast(new Transfer(frames+5+random.nextInt(9),id,bits,energy));sendCount++;grid.event(bits,true,"SIM SEND #"+id);perturb.accept(energy);
   link.publish("simulated-send",Map.of("transfer",id,"byte",bits,"energy",energy,"orbit_phase",orbitRotation,"simulation",true),"all");
  }
  while(!transfers.isEmpty()&&transfers.peekFirst().due<=frames){Transfer t=transfers.removeFirst();receiveCount++;grid.event(t.bits^0x5a,false,"SIM RECEIVE #"+t.id);perturb.accept(t.energy*.65);
   link.publish("simulated-receive",Map.of("transfer",t.id,"byte",t.bits,"energy",t.energy,"simulation",true),"all");}
  if(frames%15==0)link.telemetry=Map.of("mixed_activity",activity,"random_influence",influence,"simulated_send",sendCount,"simulated_receive",receiveCount,"actual_bus_received",externalCount);
  grid.fade();
 }
 public void close(){if(closed)return;closed=true;drain.stop();link.close();}
 static final class BinaryGrid extends JPanel {
  final boolean[] bits=new boolean[96];final float[] heat=new float[96];String last="Waiting for stochastic or bus events";boolean sending;
  BinaryGrid(){setPreferredSize(new Dimension(300,191));setBackground(BG);setBorder(BorderFactory.createLineBorder(EDGE));}
  void event(int seed,boolean send,String label){sending=send;last=label;Random r=new Random(seed);for(int i=0;i<5;i++){int at=r.nextInt(bits.length);bits[at]=!bits[at];heat[at]=1;}repaint();}
  void fade(){for(int i=0;i<heat.length;i++)heat[i]*=.97f;repaint();}
  protected void paintComponent(Graphics graphics){super.paintComponent(graphics);Graphics2D g=(Graphics2D)graphics.create();g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,RenderingHints.VALUE_TEXT_ANTIALIAS_ON);g.setFont(new Font(Font.MONOSPACED,Font.BOLD,11));g.setColor(CYAN);g.drawString("BINARY FLUX / 12 x 8",10,19);int cellW=(getWidth()-20)/12;
   for(int row=0;row<8;row++)for(int col=0;col<12;col++){int at=row*12+col,x=10+col*cellW,y=30+row*16;Color accent=sending?CYAN:AMBER;g.setColor(new Color(accent.getRed(),accent.getGreen(),accent.getBlue(),(int)(15+heat[at]*75)));g.fillRect(x,y,cellW-2,14);g.setColor(bits[at]?new Color(110,235,165):new Color(75+(int)(heat[at]*100),100,120));g.drawString(bits[at]?"1":"0",x+cellW/2-3,y+11);}
   g.setColor(MUTED);g.setFont(new Font(Font.SANS_SERIF,Font.PLAIN,10));g.drawString(FluxBusLink.shortText(last,48),10,178);g.dispose();}
 }
}
