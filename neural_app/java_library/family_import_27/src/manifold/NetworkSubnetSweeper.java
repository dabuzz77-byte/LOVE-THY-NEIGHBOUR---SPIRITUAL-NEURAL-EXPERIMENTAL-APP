package manifold;
import neural.studio.*;





import javax.swing.SwingUtilities;

import java.net.InetAddress;

import java.net.Socket;

import java.util.ArrayList;

import java.util.List;



public class NetworkSubnetSweeper {

    private final LiveGhostManifoldEngine engine;



    public NetworkSubnetSweeper(LiveGhostManifoldEngine engine) {

        this.engine = engine;

    }



    public void triggerAsynchronousLANScan() {

        Thread scanThread = new Thread(() -> {

            SwingUtilities.invokeLater(() -> engine.txtTerminal.append("[SCAN] Running parallel ICMP/Ping probe across local network spectrum...\n"));

            List<Thread> scanThreads = new ArrayList<>();



            for (int i = 1; i <= 254; i++) {

                final int hostIndex = i;

                Thread probe = new Thread(() -> {

                    try {

                        String targetIp = engine.localSubnetPrefix + hostIndex;

                        InetAddress address = InetAddress.getByName(targetIp);

                        

                        if (address.isReachable(1200)) {

                            LiveDeviceNode node = new LiveDeviceNode(targetIp, "ACTIVE_NODE");

                            probeHardwarePorts(node);

                            engine.activeDiscoveredDevices.add(node);

                            

                            SwingUtilities.invokeLater(() -> engine.txtTerminal.append(String.format("[DISCOVERED] Node online: %s | Active Sockets: %s\n", targetIp, node.detectedRole)));

                        }

                    } catch (Exception ignored) {}

                    

                    engine.incrementSweepProgress();

                });

                scanThreads.add(probe);

                probe.start();

            }



            for (Thread t : scanThreads) {

                try { t.join(); } catch (InterruptedException ignored) {}

            }

            SwingUtilities.invokeLater(() -> engine.txtTerminal.append("[COMPLETE] LAN hardware topology exploration cycle completed.\n"));

        });

        scanThread.setDaemon(true);

        scanThread.start();

    }



    private void probeHardwarePorts(LiveDeviceNode node) {

        int[] portsToTest = {22, 80, 443, 11434};

        for (int port : portsToTest) {

            try (Socket s = new Socket()) {

                s.connect(new java.net.InetSocketAddress(node.ip, port), 200);

                if (port == 11434) node.detectedRole = "AI_INFERENCE_ENGINE";

                else if (port == 22) node.detectedRole = "SECURE_SHELL_HOST";

                else node.detectedRole = "HTTP_SERVER_NODE";

                return;

            } catch (Exception ignored) {}

        }

    }

}

