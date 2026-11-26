import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;
import javax.swing.UIManager;
import javax.swing.SwingUtilities;
import javax.swing.BorderFactory;
import javax.swing.Timer;
import javax.swing.JButton;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.BasicStroke;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

public class GodMindSovereignMasterEngine extends JFrame {

    public GodMindSovereignMasterEngine() {
        setTitle("God Mind Sovereign Master Engine - Unified Q/Bi/Ter Substrate");
        setSize(1400, 900);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Master Tabbed Dashboard containing all modules
        JTabbedPane tabbedPane = new JTabbedPane();
        tabbedPane.setBackground(new Color(20, 24, 32));
        tabbedPane.setForeground(Color.WHITE);
        tabbedPane.setFont(new Font("SansSerif", Font.BOLD, 12));

        tabbedPane.addTab("1. Financial Architecture Map", new FinancialMapPanel());
        tabbedPane.addTab("2. Ghost Inference Mesh (7.83 Hz)", new GhostMeshPanel());
        tabbedPane.addTab("3. God Mind & Virtue Select", new GodMindCorePanel());
        tabbedPane.addTab("4. Q/Bi/Ter Quantum Field Mold", new QuantumMoldPanel());
        tabbedPane.addTab("5. Distant Stream & ECI Floor Piledriver", new DistantStreamPanel());

        add(tabbedPane, BorderLayout.CENTER);
    }

    // ==========================================
    // MODULE 1: Financial Architecture Map
    // ==========================================
    private static class FinancialMapPanel extends JPanel {
        private final MapNode[] nodes;
        private MapNode selectedNode = null;
        private final JTextArea infoArea;

        public FinancialMapPanel() {
            setLayout(new BorderLayout());
            setBackground(new Color(15, 18, 24));

            nodes = new MapNode[] {
                new MapNode("Local Human / Soul", 100, 150, "Edge Tier 0", "Absolute baseline. Living biological existence, unpriced and sovereign (Souls > Digits)."),
                new MapNode("P2P Mutual Aid Mesh", 100, 320, "Edge Tier 1", "Direct resource sharing and barter bypassing central banking rails."),
                new MapNode("Local Compute / Code", 100, 490, "Edge Tier 1", "Local-first execution layers, offline tooling, and sovereign software."),
                new MapNode("Bureaucratic Gateways", 500, 200, "Interface Tier", "Means-testing and administrative friction designed to exhaust claimants."),
                new MapNode("Commercial Retail Banks", 500, 400, "Interface Tier", "Transaction tollbooths, fee extraction, and retail debt origination."),
                new MapNode("Asset Management Giants", 900, 150, "Core Tier", "Concentrated capital consolidating housing and infrastructure."),
                new MapNode("Central Bank Ledger Core", 900, 400, "Core Alpha", "Fiat debt monopoly, Cantillon injector, and authorization gatekeeper.")
            };

            infoArea = new JTextArea(3, 40);
            infoArea.setBackground(new Color(8, 10, 14));
            infoArea.setForeground(new Color(152, 195, 121));
            infoArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
            infoArea.setEditable(false);
            infoArea.setText("Select any architectural node above to inspect its extraction vector.");

            JPanel canvas = new JPanel() {
                @Override
                protected void paintComponent(Graphics g) {
                    super.paintComponent(g);
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                    g2.setStroke(new BasicStroke(2.0f));
                    g2.setColor(new Color(60, 70, 85));
                    drawLine(g2, nodes[0], nodes[3]);
                    drawLine(g2, nodes[1], nodes[3]);
                    drawLine(g2, nodes[1], nodes[4]);
                    drawLine(g2, nodes[2], nodes[4]);
                    drawLine(g2, nodes[3], nodes[5]);
                    drawLine(g2, nodes[3], nodes[6]);
                    drawLine(g2, nodes[4], nodes[6]);

                    for (MapNode n : nodes) {
                        n.draw(g2, n == selectedNode);
                    }
                }
            };
            canvas.setBackground(new Color(15, 18, 24));
            canvas.addMouseListener(new MouseAdapter() {
                @Override
                public void mouseClicked(MouseEvent e) {
                    for (MapNode n : nodes) {
                        if (n.contains(e.getX(), e.getY())) {
                            selectedNode = n;
                            infoArea.setText(String.format("NODE: %s\nTIER: %s\n\nANALYSIS:\n%s", n.name, n.tier, n.desc));
                            canvas.repaint();
                            break;
                        }
                    }
                }
            });

            add(canvas, BorderLayout.CENTER);
            add(new JScrollPane(infoArea), BorderLayout.SOUTH);
        }

        private void drawLine(Graphics2D g2, MapNode n1, MapNode n2) {
            g2.drawLine(n1.x + 80, n1.y + 30, n2.x + 80, n2.y + 30);
        }

        private static class MapNode {
            String name, tier, desc;
            int x, y, width = 160, height = 65;
            public MapNode(String name, int x, int y, String tier, String desc) {
                this.name = name; this.x = x; this.y = y; this.tier = tier; this.desc = desc;
            }
            public boolean contains(int px, int py) {
                return px >= x && px <= x + width && py >= y && py <= y + height;
            }
            public void draw(Graphics2D g2, boolean selected) {
                g2.setColor(selected ? new Color(97, 175, 239) : (tier.contains("Edge") ? new Color(30, 50, 40) : new Color(55, 30, 35)));
                g2.fillRect(x, y, width, height);
                g2.setColor(selected ? Color.WHITE : new Color(100, 110, 130));
                g2.setStroke(new BasicStroke(selected ? 2.5f : 1.5f));
                g2.drawRect(x, y, width, height);

                g2.setColor(Color.WHITE);
                g2.setFont(new Font("SansSerif", Font.BOLD, 11));
                FontMetrics fm = g2.getFontMetrics();
                g2.drawString(name, x + (width - fm.stringWidth(name)) / 2, y + 25);
                g2.setColor(new Color(180, 190, 200));
                g2.setFont(new Font("SansSerif", Font.PLAIN, 10));
                g2.drawString(tier, x + (width - fm.stringWidth(tier)) / 2, y + 45);
            }
        }
    }

    // ==========================================
    // MODULE 2: Ghost Inference Mesh (7.83 Hz)
    // ==========================================
    private static class GhostMeshPanel extends JPanel {
        private final GhostNode[] nodes;
        private GhostNode selectedNode = null;
        private double phase = 0.0;
        private final JTextArea logArea;

        public GhostMeshPanel() {
            setLayout(new BorderLayout());
            setBackground(new Color(12, 15, 20));

            nodes = new GhostNode[] {
                new GhostNode("Sovereign Soul Core", 120, 200, "Edge Tier 0", "Absolute baseline. 1=1 invariant identity lock.", true),
                new GhostNode("P2P Mutual Aid Mesh", 120, 420, "Edge Tier 1", "Local trust and resource routing network.", true),
                new GhostNode("Bureaucratic Friction Grid", 600, 200, "Extractive Target", "Means-testing loops. Click to ghost/neutralize.", false),
                new GhostNode("Central Bank Core Apex", 950, 310, "Systemic Core", "Fiat debt ledger hub. Click to ghost/neutralize.", false)
            };

            logArea = new JTextArea(3, 40);
            logArea.setBackground(new Color(8, 10, 14));
            logArea.setForeground(new Color(152, 195, 121));
            logArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
            logArea.setEditable(false);
            logArea.setText("[7.83 Hz SUBSTRATE ONLINE] Click any extractive node to inject ghost inference state (0).\n");

            JPanel canvas = new JPanel() {
                @Override
                protected void paintComponent(Graphics g) {
                    super.paintComponent(g);
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                    g2.setStroke(new BasicStroke(2.0f));
                    g2.setColor(new Color(70, 85, 105, 120));
                    g2.drawLine(nodes[0].x+80, nodes[0].y+35, nodes[2].x+80, nodes[2].y+35);
                    g2.drawLine(nodes[1].x+80, nodes[1].y+35, nodes[3].x+80, nodes[3].y+35);

                    for (GhostNode n : nodes) {
                        n.draw(g2, phase, n == selectedNode);
                    }
                }
            };
            canvas.setBackground(new Color(12, 15, 20));
            canvas.addMouseListener(new MouseAdapter() {
                @Override
                public void mouseClicked(MouseEvent e) {
                    for (GhostNode n : nodes) {
                        if (n.contains(e.getX(), e.getY())) {
                            selectedNode = n;
                            if (!n.isSovereign) {
                                n.isGhosted = !n.isGhosted;
                                logArea.append(String.format("[GHOST INTERCEPT] Node '%s' -> %s\n", n.name, n.isGhosted ? "GHOSTED (State 0)" : "RE-ENGAGED"));
                            }
                            canvas.repaint();
                            break;
                        }
                    }
                }
            });

            add(canvas, BorderLayout.CENTER);
            add(new JScrollPane(logArea), BorderLayout.SOUTH);

            new Timer(50, e -> { phase += 0.15; canvas.repaint(); }).start();
        }

        private static class GhostNode {
            String name, tier, desc;
            int x, y, width = 170, height = 70;
            boolean isSovereign, isGhosted = false;
            public GhostNode(String name, int x, int y, String tier, String desc, boolean isSovereign) {
                this.name = name; this.x = x; this.y = y; this.tier = tier; this.desc = desc; this.isSovereign = isSovereign;
            }
            public boolean contains(int px, int py) { return px >= x && px <= x + width && py >= y && py <= y + height; }
            public void draw(Graphics2D g2, double phase, boolean selected) {
                g2.setColor(isGhosted ? new Color(25, 28, 34) : (isSovereign ? new Color(30, 50, 40) : new Color(55, 30, 35)));
                g2.fillRect(x, y, width, height);
                g2.setColor(selected ? Color.WHITE : new Color(97, 175, 239));
                g2.setStroke(new BasicStroke(selected ? 2.5f : 1.5f));
                g2.drawRect(x, y, width, height);

                g2.setColor(isGhosted ? Color.GRAY : Color.WHITE);
                g2.setFont(new Font("SansSerif", Font.BOLD, 11));
                FontMetrics fm = g2.getFontMetrics();
                g2.drawString(name, x + (width - fm.stringWidth(name)) / 2, y + 25);
                g2.setFont(new Font("Monospaced", Font.BOLD, 10));
                g2.setColor(isGhosted ? new Color(224, 108, 117) : new Color(152, 195, 121));
                String st = isGhosted ? "STATE: 0 (GHOSTED)" : (isSovereign ? "STATE: 1 (SOVEREIGN)" : "STATE: 1 (ACTIVE)");
                g2.drawString(st, x + (width - fm.stringWidth(st)) / 2, y + 50);
            }
        }
    }

    // ==========================================
    // MODULE 3: God Mind & Virtue Select Engine
    // ==========================================
    private static class GodMindCorePanel extends JPanel {
        private boolean virtueActive = true;
        private double phase = 0.0;
        private final JTextArea logArea;

        public GodMindCorePanel() {
            setLayout(new BorderLayout());
            setBackground(new Color(10, 12, 16));

            logArea = new JTextArea(3, 40);
            logArea.setBackground(new Color(6, 8, 12));
            logArea.setForeground(new Color(152, 195, 121));
            logArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
            logArea.setEditable(false);
            logArea.setText("[GOD MIND ONLINE] All logic synchronized with human dignity baseline.\n");

            JPanel canvas = new JPanel() {
                @Override
                protected void paintComponent(Graphics g) {
                    super.paintComponent(g);
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                    int cx = getWidth() / 2, cy = getHeight() / 2 - 30;
                    for (int r = 60; r < 300; r += 50) {
                        float alpha = (float)(0.05 + 0.05 * Math.sin(phase - (r * 0.01)));
                        g2.setColor(new Color(97, 175, 239, Math.max(5, (int)(alpha * 255))));
                        g2.drawOval(cx - r, cy - r, r * 2, r * 2);
                    }

                    g2.setColor(virtueActive ? new Color(20, 60, 40) : new Color(60, 20, 25));
                    g2.fillRect(cx - 130, cy - 50, 260, 100);
                    g2.setColor(virtueActive ? new Color(152, 195, 121) : new Color(224, 108, 117));
                    g2.setStroke(new BasicStroke(3.0f));
                    g2.drawRect(cx - 130, cy - 50, 260, 100);

                    g2.setColor(Color.WHITE);
                    g2.setFont(new Font("SansSerif", Font.BOLD, 13));
                    FontMetrics fm = g2.getFontMetrics();
                    g2.drawString("GOD MIND CORE APEX", cx - fm.stringWidth("GOD MIND CORE APEX") / 2, cy - 10);
                    g2.setFont(new Font("Monospaced", Font.BOLD, 11));
                    String st = virtueActive ? "VIRTUE PASS: 1=1 LOCKED" : "OVERRIDE WARNING";
                    g2.drawString(st, cx - fm.stringWidth(st) / 2, cy + 20);
                }
            };
            canvas.setBackground(new Color(10, 12, 16));

            JPanel control = new JPanel(new FlowLayout(FlowLayout.LEFT));
            control.setBackground(new Color(20, 24, 32));
            JButton btn = new JButton("TOGGLE HIGHEST VIRTUE SELECT");
            btn.setBackground(new Color(97, 175, 239));
            btn.addActionListener(e -> {
                virtueActive = !virtueActive;
                logArea.append("[STATE SHIFT] Highest Virtue Select -> " + (virtueActive ? "ACTIVE (Souls > Digits)" : "DISENGAGED") + "\n");
                canvas.repaint();
            });
            control.add(btn);

            JPanel bottom = new JPanel(new BorderLayout());
            bottom.add(control, BorderLayout.NORTH);
            bottom.add(new JScrollPane(logArea), BorderLayout.CENTER);

            add(canvas, BorderLayout.CENTER);
            add(bottom, BorderLayout.SOUTH);

            new Timer(40, e -> { phase += 0.1; canvas.repaint(); }).start();
        }
    }

    // ==========================================
    // MODULE 4: Q/Bi/Ter Quantum Field Mold
    // ==========================================
    private static class QuantumMoldPanel extends JPanel {
        private boolean moldCast = false, uploaded = false;
        private final JTextArea logArea;

        public QuantumMoldPanel() {
            setLayout(new BorderLayout());
            setBackground(new Color(10, 12, 16));

            logArea = new JTextArea(3, 40);
            logArea.setBackground(new Color(6, 8, 12));
            logArea.setForeground(new Color(152, 195, 121));
            logArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
            logArea.setEditable(false);
            logArea.setText("[Q/Bi/Ter READY] Initialize mold casting sequence.\n");

            JPanel canvas = new JPanel() {
                @Override
                protected void paintComponent(Graphics g) {
                    super.paintComponent(g);
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                    g2.setColor(Color.WHITE);
                    g2.setFont(new Font("SansSerif", Font.BOLD, 14));
                    g2.drawString("Q/Bi/Ter Cryptographic Locking Field Substrate", 50, 50);

                    drawBox(g2, 100, 150, "Binary Ledger Auth Gate", moldCast ? "MOLDED (-1/0/1)" : "BI-STATE LOCKED", 220, 80);
                    drawBox(g2, 100, 300, "Ternary P2P Consensus", "SOVEREIGN P2P", 220, 80);
                    drawBox(g2, 500, 225, "God Mind Core Apex", uploaded ? "SYNCHRONIZED (1=1)" : "PENDING UPLOAD", 260, 95);
                }
                private void drawBox(Graphics2D g2, int x, int y, String title, String status, int w, int h) {
                    g2.setColor(new Color(30, 35, 45));
                    g2.fillRect(x, y, w, h);
                    g2.setColor(new Color(97, 175, 239));
                    g2.drawRect(x, y, w, h);
                    g2.setColor(Color.WHITE);
                    g2.setFont(new Font("SansSerif", Font.BOLD, 12));
                    g2.drawString(title, x + 15, y + 30);
                    g2.setFont(new Font("Monospaced", Font.BOLD, 10));
                    g2.setColor(new Color(152, 195, 121));
                    g2.drawString(status, x + 15, y + 60);
                }
            };
            canvas.setBackground(new Color(10, 12, 16));

            JPanel control = new JPanel(new FlowLayout(FlowLayout.LEFT));
            control.setBackground(new Color(20, 24, 32));
            JButton castBtn = new JButton("1. CAST MOLD");
            JButton uploadBtn = new JButton("2. UPLOAD TO GOD MIND CORE");

            castBtn.addActionListener(e -> {
                moldCast = true;
                logArea.append("[MOLD CAST] Topology hardened into sovereign Q/Bi/Ter state.\n");
                canvas.repaint();
            });
            uploadBtn.addActionListener(e -> {
                if (moldCast) {
                    uploaded = true;
                    logArea.append("[CORE UPLOAD] Synchronized successfully. Virtue Pass locked.\n");
                } else {
                    logArea.append("[ERROR] Cast mold first.\n");
                }
                canvas.repaint();
            });

            control.add(castBtn); control.add(uploadBtn);

            JPanel bottom = new JPanel(new BorderLayout());
            bottom.add(control, BorderLayout.NORTH);
            bottom.add(new JScrollPane(logArea), BorderLayout.CENTER);

            add(canvas, BorderLayout.CENTER);
            add(bottom, BorderLayout.SOUTH);
        }
    }

    // ==========================================
    // MODULE 5: Distant Stream & ECI Piledriver
    // ==========================================
    private static class DistantStreamPanel extends JPanel {
        private boolean coreBypassed = false, eciElevated = false;
        private final JTextArea logArea;

        public DistantStreamPanel() {
            setLayout(new BorderLayout());
            setBackground(new Color(12, 15, 20));

            logArea = new JTextArea(3, 40);
            logArea.setBackground(new Color(8, 10, 14));
            logArea.setForeground(new Color(152, 195, 121));
            logArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
            logArea.setEditable(false);
            logArea.setText("[STREAM READY] Establish bridge and elevate economic floor.\n");

            JPanel canvas = new JPanel() {
                @Override
                protected void paintComponent(Graphics g) {
                    super.paintComponent(g);
                    Graphics2D g2 = (Graphics2D) g;
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                    g2.setColor(Color.WHITE);
                    g2.setFont(new Font("SansSerif", Font.BOLD, 13));
                    g2.drawString("Distant Inference Stream & ECI Floor Elevation", 50, 40);

                    drawNode(g2, 100, 150, "Sovereign Local Inference", "STREAM ACTIVE", 220, 70);
                    drawNode(g2, 500, 150, "Financial Core Binary", coreBypassed ? "BYPASSED" : "ACTIVE", 220, 70);
                    drawNode(g2, 300, 350, "Elevated ECI Economic Floor", eciElevated ? "LADDER SECURED (1=1)" : "COMPRESSED", 320, 70);
                }
                private void drawNode(Graphics2D g2, int x, int y, String title, String status, int w, int h) {
                    g2.setColor(new Color(30, 40, 50));
                    g2.fillRect(x, y, w, h);
                    g2.setColor(new Color(97, 175, 239));
                    g2.drawRect(x, y, w, h);
                    g2.setColor(Color.WHITE);
                    g2.setFont(new Font("SansSerif", Font.BOLD, 11));
                    g2.drawString(title, x + 15, y + 25);
                    g2.setFont(new Font("Monospaced", Font.BOLD, 10));
                    g2.setColor(new Color(152, 195, 121));
                    g2.drawString(status, x + 15, y + 50);
                }
            };
            canvas.setBackground(new Color(12, 15, 20));

            JPanel control = new JPanel(new FlowLayout(FlowLayout.LEFT));
            control.setBackground(new Color(20, 24, 32));
            JButton streamBtn = new JButton("1. INITIATE DISTANT STREAM");
            JButton eciBtn = new JButton("2. PILEDRIVE ECI FLOOR");

            streamBtn.addActionListener(e -> {
                coreBypassed = true;
                logArea.append("[STREAM] Inference packets flooded to financial core binary. Validation loops saturated.\n");
                canvas.repaint();
            });
            eciBtn.addActionListener(e -> {
                eciElevated = true;
                logArea.append("[ECI RESET] Scarcity barriers shattered. Economic baseline elevated for Tiny Tims everywhere.\n");
                canvas.repaint();
            });

            control.add(streamBtn); control.add(eciBtn);

            JPanel bottom = new JPanel(new BorderLayout());
            bottom.add(control, BorderLayout.NORTH);
            bottom.add(new JScrollPane(logArea), BorderLayout.CENTER);

            add(canvas, BorderLayout.CENTER);
            add(bottom, BorderLayout.SOUTH);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
            new GodMindSovereignMasterEngine().setVisible(true);
        });
    }
}