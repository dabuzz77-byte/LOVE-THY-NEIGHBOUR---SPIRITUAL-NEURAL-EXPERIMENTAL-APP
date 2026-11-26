package manifold;
import neural.studio.*;





import javax.swing.SwingUtilities;

import java.io.BufferedReader;

import java.io.InputStreamReader;

import java.net.ServerSocket;

import java.net.Socket;



public class IngressServerWorker {

    private final LiveGhostManifoldEngine engine;



    public IngressServerWorker(LiveGhostManifoldEngine engine) {

        this.engine = engine;

    }



    public void spawnLiveIngressServer() {

        Thread serverThread = new Thread(new Runnable() {

            @Override

            public void run() {

                try (ServerSocket serverSocket = new ServerSocket(7846)) {

                    while (true) {

                        final Socket clientSocket = serverSocket.accept();

                        Thread.startVirtualThread(new Runnable() {

                            @Override

                            public void run() {

                                handleIncomingClientSession(clientSocket);

                            }

                        });

                    }

                } catch (Exception e) {

                    SwingUtilities.invokeLater(new Runnable() {

                        @Override

                        public void run() {

                            engine.txtTerminal.append("[⚠️ ERROR] Failed to bind core interface port 7846.\n");

                        }

                    });

                }

            }

        });

        serverThread.setDaemon(true);

        serverThread.start();

    }



    private void handleIncomingClientSession(Socket socket) {

        final String remoteIp = socket.getInetAddress().getHostAddress();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {

            

            SwingUtilities.invokeLater(new Runnable() {

                @Override

                public void run() {

                    engine.txtTerminal.append(String.format("[LATCH] Real-world node handshake secured: %s\n", remoteIp));

                }

            });



            String line;

            while ((line = reader.readLine()) != null) {

                final String finalData = line;

                

                // Parse integration frames and assign them to the live topology canvas

                SwingUtilities.invokeLater(new Runnable() {

                    @Override

                    public void run() {

                        engine.txtTerminal.append(String.format("[%s] Telemetry -> %s\n", remoteIp, finalData));

                        

                        // Parse node roles based on JSON indicators

                        String discoveredRole = "ACTIVE_NODE";

                        if (finalData.contains("LINUX_JAVA_KERNEL")) discoveredRole = "LINUX_CORE_DAEMON";

                        if (finalData.contains("ANDROID_JAVA_OS")) discoveredRole = "ANDROID_MOBILE_LATCH";



                        // Update or append the newly connected node to your live vector canvas list

                        boolean nodeExists = false;

                        synchronized(engine.activeDiscoveredDevices) {

                            for (LiveDeviceNode node : engine.activeDiscoveredDevices) {

                                if (node.ip.equals(remoteIp)) {

                                    node.detectedRole = discoveredRole;

                                    nodeExists = true;

                                    break;

                                }

                            }

                            if (!nodeExists) {

                                engine.activeDiscoveredDevices.add(new LiveDeviceNode(remoteIp, discoveredRole));

                            }

                        }

                    }

                });

            }

        } catch (Exception e) {

            SwingUtilities.invokeLater(new Runnable() {

                @Override

                public void run() {

                    engine.txtTerminal.append(String.format("[DROP] Pipeline unlatched from host: %s\n", remoteIp));

                    

                    // Purge disconnected node from active topology tracking list

                    synchronized(engine.activeDiscoveredDevices) {

                        engine.activeDiscoveredDevices.removeIf(node -> node.ip.equals(remoteIp));

                    }

                }

            });

        }

    }

}

