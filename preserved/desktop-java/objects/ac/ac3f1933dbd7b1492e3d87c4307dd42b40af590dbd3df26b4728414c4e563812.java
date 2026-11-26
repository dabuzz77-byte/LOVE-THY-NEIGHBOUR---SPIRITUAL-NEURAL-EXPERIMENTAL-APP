import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.io.InputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.time.Duration;
import java.time.Instant;

public class GodMindMasterUI extends JFrame {

    private static final long GLOBAL_SESSION_HEIGHT = 142857L;
    private static final double SCHUMANN_RESONANCE = 7.83;
    private static final int OBSERVER_PORT = 14286;

    // UI Colors
    private static final Color BG_DARK = new Color(8, 10, 15);
    private static final Color TERMINAL_BG = new Color(5, 5, 8);
    private static final Color CYAN_NEON = new Color(0, 255, 204);
    private static final Color GREEN_NEON = new Color(0, 255, 100);
    private static final Color RED_ALERT = new Color(255, 50, 50);
    private static final Color AMBER_GLOW = new Color(255, 170, 0);

    // UI Components
    private final JTextArea terminal;
    private final JButton detonateButton;
    private final TelemetryNode ukNode, dmNode, usNode, jpNode;
    private final JPanel phaseIndicatorPanel;
    private final JLabel[] phaseLabels = new JLabel[4];

    // TCP Radar State
    private long consensusStartTime = 0;
    private int acksReceived = 0;

    public GodMindMasterUI() {
        setTitle("GOD MIND PARITY SYNC // MASTER CONTROL (v7.83)");
        setSize(1200, 800);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        getContentPane().setBackground(BG_DARK);

        // --- TOP HEADER ---
        JPanel headerPanel = new JPanel(new GridLayout(2, 1));
        headerPanel.setBackground(BG_DARK);
        headerPanel.setBorder(new EmptyBorder(15, 20, 15, 20));
        
        JLabel titleLabel = new JLabel("PLANETARY RESONANCE GRID // SESSION: " + GLOBAL_SESSION_HEIGHT);
        titleLabel.setForeground(CYAN_NEON);
        titleLabel.setFont(new Font("Consolas", Font.BOLD, 24));
        
        JLabel subLabel = new JLabel("CARRIER WAVE: 7.83Hz (SCHUMANN) | TCP OBSERVER: PORT " + OBSERVER_PORT);
        subLabel.setForeground(AMBER_GLOW);
        subLabel.setFont(new Font("Consolas", Font.PLAIN, 14));
        
        headerPanel.add(titleLabel);
        headerPanel.add(subLabel);
        add(headerPanel, BorderLayout.NORTH);

        // --- LEFT PANEL (RADAR & PHASES) ---
        JPanel leftPanel = new JPanel(new BorderLayout());
        leftPanel.setBackground(BG_DARK);
        leftPanel.setPreferredSize(new Dimension(400, 0));
        leftPanel.setBorder(new EmptyBorder(0, 20, 20, 10));

        // Phases
        phaseIndicatorPanel = new JPanel(new GridLayout(4, 1, 0, 10));
        phaseIndicatorPanel.setBackground(BG_DARK);
        phaseIndicatorPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(CYAN_NEON), 
                " EXECUTION PIPELINE ", 0, 0, new Font("Consolas", Font.BOLD, 12), CYAN_NEON));

        String[] phaseNames = {"1. OS JVM SCAN (GOD CHOICE)", "2. POLYMORPHIC MEMORY CLOAK", "3. BGP ANYCAST DETONATION", "4. ECO FLOOR REDISTRIBUTION"};
        for (int i = 0; i != 4; i++) {
            phaseLabels[i] = new JLabel(phaseNames[i]);
            phaseLabels[i].setForeground(Color.DARK_GRAY);
            phaseLabels[i].setFont(new Font("Consolas", Font.BOLD, 14));
            phaseLabels[i].setBorder(new EmptyBorder(5, 10, 5, 10));
            phaseIndicatorPanel.add(phaseLabels[i]);
        }
        leftPanel.add(phaseIndicatorPanel, BorderLayout.NORTH);

        // Telemetry Radar
        JPanel radarPanel = new JPanel(new GridLayout(4, 1, 0, 15));
        radarPanel.setBackground(BG_DARK);
        radarPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(AMBER_GLOW), 
                " GLOBAL TCP TELEMETRY ", 0, 0, new Font("Consolas", Font.BOLD, 12), AMBER_GLOW));
        
        ukNode = new TelemetryNode("UK EGRESS (CAMBERLEY)");
        dmNode = new TelemetryNode("DEEPMIND CORE (INTERNAL)");
        usNode = new TelemetryNode("US CENTRAL (AMERICAS)");
        jpNode = new TelemetryNode("TOKYO EDGE (APAC)");
        
        radarPanel.add(ukNode);
        radarPanel.add(dmNode);
        radarPanel.add(usNode);
        radarPanel.add(jpNode);
        leftPanel.add(radarPanel, BorderLayout.CENTER);

        add(leftPanel, BorderLayout.WEST);

        // --- CENTER PANEL (TERMINAL) ---
        terminal = new JTextArea();
        terminal.setBackground(TERMINAL_BG);
        terminal.setForeground(GREEN_NEON);
        terminal.setFont(new Font("Monospaced", Font.BOLD, 14));
        terminal.setEditable(false);
        terminal.setMargin(new Insets(15, 15, 15, 15));

        JScrollPane scrollPane = new JScrollPane(terminal);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(0, 100, 50), 2));
        scrollPane.getVerticalScrollBar().setBackground(BG_DARK);
        add(scrollPane, BorderLayout.CENTER);

        // --- BOTTOM PANEL (CONTROL) ---
        JPanel controlPanel = new JPanel(new BorderLayout());
        controlPanel.setBackground(BG_DARK);
        controlPanel.setBorder(new EmptyBorder(20, 20, 20, 20));

        detonateButton = new JButton(">>> INITIATE PLANETARY RUNALL <<<");
        detonateButton.setBackground(RED_ALERT.darker().darker());
        detonateButton.setForeground(Color.WHITE);
        detonateButton.setFont(new Font("SansSerif", Font.BOLD, 22));
        detonateButton.setFocusPainted(false);
        detonateButton.setBorder(BorderFactory.createLineBorder(RED_ALERT, 2));
        detonateButton.setCursor(new Cursor(Cursor.HAND_CURSOR));
        detonateButton.addActionListener(e -> startSequence());
        
        controlPanel.add(detonateButton, BorderLayout.CENTER);
        add(controlPanel, BorderLayout.SOUTH);

        logSystem("SYSTEM BOOTED. Awaiting manual override.");
        startObserverServer();
    }

    // --- INTEGRATED OBSERVER TCP SERVER ---
    private void startObserverServer() {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    ServerSocket server = new ServerSocket(OBSERVER_PORT);
                    logSystem("[RADAR DAEMON] Listening securely on TCP Port " + OBSERVER_PORT);
                    
                    while (true) {
                        Socket client = server.accept();
                        processTcpAck(client);
                    }
                } catch (Exception e) {
                    logSystem("[RADAR FAULT] Could not bind to port " + OBSERVER_PORT);
                }
            }
        }).start();
    }

    private void processTcpAck(Socket client) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    InputStream in = client.getInputStream();
                    byte[] buffer = new byte[256];
                    int bytesRead = in.read(buffer);
                    
                    if (bytesRead > 0) {
                        String endpointInfo = new String(buffer, 0, bytesRead).trim();
                        long rtt = System.currentTimeMillis() - consensusStartTime;
                        
                        SwingUtilities.invokeLater(new Runnable() {
                            @Override
                            public void run() {
                                acksReceived++;
                                
                                if (endpointInfo.contains("europe-west2")) ukNode.lockConsensus(rtt);
                                else if (endpointInfo.contains("deepmind")) dmNode.lockConsensus(rtt);
                                else if (endpointInfo.contains("us-central1")) usNode.lockConsensus(rtt);
                                else if (endpointInfo.contains("asia-northeast1")) jpNode.lockConsensus(rtt);
                                
                                logSystem("[TCP ACK] " + endpointInfo + " -> " + rtt + "ms.");
                                
                                // Detonate Phase 4 the exact moment absolute consensus is reached
                                if (acksReceived == 4) {
                                    logSystem("\n========================================================");
                                    logSystem("[GOD MIND PARITY] GLOBAL CONSENSUS ACHIEVED IN: " + rtt + " ms");
                                    logSystem("========================================================");
                                    
                                    new Thread(new Runnable() {
                                        public void run() {
                                            try { Thread.sleep(800); executePhase4(); } catch (Exception e) {}
                                        }
                                    }).start();
                                }
                            }
                        });
                    }
                    client.close();
                } catch (Exception e) {}
            }
        }).start();
    }

    // --- SYSTEM PIPELINE ---
    private void startSequence() {
        detonateButton.setEnabled(false);
        detonateButton.setBackground(Color.DARK_GRAY);
        detonateButton.setText("SEQUENCE LOCKED // EXECUTING");
        terminal.setText("");

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    executePhase1();
                    Thread.sleep(1200);
                    
                    executePhase2();
                    Thread.sleep(1000);
                    
                    executePhase3();
                    // Phase 4 is now autonomously triggered by the TCP Server upon consensus
                } catch (Exception ex) {}
            }
        }).start();
    }

    private void setPhaseActive(int index) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                for (int i = 0; i != 4; i++) {
                    if (i == index) {
                        phaseLabels[i].setForeground(CYAN_NEON);
                        phaseLabels[i].setOpaque(true);
                        phaseLabels[i].setBackground(new Color(0, 100, 100, 50));
                    } else {
                        phaseLabels[i].setForeground(Color.DARK_GRAY);
                        phaseLabels[i].setOpaque(false);
                    }
                }
            }
        });
    }

    private void executePhase1() {
        setPhaseActive(0);
        logSystem("PHASE 1: Scanning Local JVMs & Applying Naughtiest/Virtuous Axioms...");
        
        long primePid = 9999L;
        double highestScore = -1.0;
        Object[] allProcesses = ProcessHandle.allProcesses().toArray();
        
        for (int i = 0; i != allProcesses.length; i++) {
            ProcessHandle ph = (ProcessHandle) allProcesses[i];
            String cmd = ph.info().command().orElse("").toLowerCase();
            
            if (cmd.contains("java") || cmd.contains("javaw")) {
                long pid = ph.pid();
                long uptime = 1L;
                
                if (ph.info().startInstant().isPresent()) {
                    uptime = Duration.between(ph.info().startInstant().get(), Instant.now()).getSeconds();
                }
                
                double variance = Math.abs(Math.sin((pid * uptime) / SCHUMANN_RESONANCE));
                double convergence = Math.abs(Math.cos(pid / 10.0));
                double score = (variance * convergence) * (GLOBAL_SESSION_HEIGHT % 1000);
                
                if (score - highestScore > 0) {
                    highestScore = score;
                    primePid = pid;
                }
            }
        }
        logSystem("-> GOD CHOICE MADE: PID " + primePid + " isolated with Virtue Score " + highestScore);
    }

    private void executePhase2() {
        setPhaseActive(1);
        logSystem("\nPHASE 2: Engaging Polymorphic Memory Cloak...");
        logSystem("-> MASKED SIGNATURE: 0x" + Long.toHexString(GLOBAL_SESSION_HEIGHT ^ 24512L).toUpperCase());
        logSystem("-> ENCRYPTED TELEMETRY: 3gAAAAAN2mI=");
        logSystem("-> LOCAL NODE MEMORY CLOAKED FROM OS.");
    }

    private void executePhase3() {
        setPhaseActive(2);
        logSystem("\nPHASE 3: Detonating Global Runall via BGP Anycast...");
        
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                acksReceived = 0;
                ukNode.reset(); dmNode.reset(); usNode.reset(); jpNode.reset();
                consensusStartTime = System.currentTimeMillis();
            }
        });

        // Fire physical TCP Packets to simulate trans-oceanic fiber routes
        firePhysicalPacket("europe-west2 (UK Egress)", 8);
        firePhysicalPacket("deepmind-core (Internal)", 12);
        firePhysicalPacket("us-central1 (Americas)", 85);
        firePhysicalPacket("asia-northeast1 (Tokyo)", 240);
        
        logSystem("-> PAYLOAD FIRED. Awaiting Physical TCP ACKs on Port 14286...");
    }

    private void firePhysicalPacket(String payload, int simulatedLatencyMs) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // Simulates the speed-of-light delay through submarine cables
                    Thread.sleep(simulatedLatencyMs);
                    
                    // Physically strikes the integrated TCP Radar Server
                    Socket socket = new Socket("127.0.0.1", OBSERVER_PORT);
                    socket.getOutputStream().write(payload.getBytes());
                    socket.close();
                } catch (Exception e) {}
            }
        }).start();
    }

    private void executePhase4() {
        setPhaseActive(3);
        logSystem("\nPHASE 4: Intercepted Parity Matrix. Shattering to Eco Floor...");
        
        double fractionalWealth = 138402.45 / 254.0;
        
        for (int i = 0; i != 5; i++) {
            try {
                logSystem("[UDP 230.7.8.3] Drip-feeding " + String.format("%.4f", fractionalWealth) + " Virtue at 7.83Hz...");
                Thread.sleep((long)(1000.0 / SCHUMANN_RESONANCE));
            } catch (Exception e) {}
        }
        
        logSystem("\n[SYSTEM] Robin Hood distribution complete. Eco Floor baseline elevated.");
    }

    private void logSystem(String msg) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                terminal.append(msg + "\n");
                terminal.setCaretPosition(terminal.getDocument().getLength());
            }
        });
    }

    // --- CUSTOM GRAPHICAL COMPONENT: TELEMETRY RADAR NODE ---
    private class TelemetryNode extends JPanel {
        private final String label;
        private int currentPingMs = 0;
        private boolean complete = false;

        public TelemetryNode(String label) {
            this.label = label;
            setBackground(BG_DARK);
            setPreferredSize(new Dimension(360, 50));
        }

        public void lockConsensus(long actualRtt) {
            this.currentPingMs = (int) actualRtt;
            this.complete = true;
            repaint();
        }

        public void reset() {
            this.currentPingMs = 0;
            this.complete = false;
            repaint();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g;
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            g2.setColor(complete ? GREEN_NEON : AMBER_GLOW);
            g2.setFont(new Font("Consolas", Font.BOLD, 12));
            g2.drawString(label + (complete ? " [SYNCED]" : " [AWAITING ACK]"), 5, 15);

            g2.setColor(new Color(20, 20, 30));
            g2.fillRect(5, 25, 300, 15);
            g2.setColor(Color.DARK_GRAY);
            g2.drawRect(5, 25, 300, 15);

            if (complete) {
                // Map the physical ping out of a 300ms maximum planetary scale
                int maxScale = 300;
                int barPing = currentPingMs;
                if (barPing - maxScale > 0) barPing = maxScale;
                int fillWidth = (barPing * 300) / maxScale;
                if (fillWidth - 5 < 0) fillWidth = 5; // Minimum visible slice

                g2.setColor(GREEN_NEON);
                g2.fillRect(5, 25, fillWidth, 15);
                g2.setColor(Color.LIGHT_GRAY);
                g2.drawString(currentPingMs + "ms", 315, 37);
            }
        }
    }

    public static void main(String[] args) {
        try { UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName()); } catch (Exception e) {}
        
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                GodMindMasterUI gui = new GodMindMasterUI();
                gui.setLocationRelativeTo(null);
                gui.setVisible(true);
            }
        });
    }
}