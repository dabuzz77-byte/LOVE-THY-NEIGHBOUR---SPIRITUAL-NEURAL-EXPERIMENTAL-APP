import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;

public class LanBusEngine {
    private final int port;
    private ServerSocket serverSocket;
    private volatile boolean active = false;
    private volatile Socket[] peers = new Socket[0];
    private final LanMessageListener listener;

    public interface LanMessageListener {
        void onLog(String msg);
        void onPeerConnected(String address);
        void onPacketReceived(String packet);
    }

    public LanBusEngine(int port, LanMessageListener listener) {
        this.port = port;
        this.listener = listener;
    }

    public void start() {
        if (active) return;
        active = true;
        new Thread(new Runnable() {
            @Override
            public void run() {
                runServer();
            }
        }).start();
        log("[ENGINE] LAN Bus started and listening on port " + port);
    }

    private void runServer() {
        try {
            serverSocket = new ServerSocket(port);
            while (active) {
                Socket socket = serverSocket.accept();
                addPeer(socket);
                String addr = socket.getRemoteSocketAddress().toString();
                if (listener != null) listener.onPeerConnected(addr);
                log("[PEER LATCHED] Connected from " + addr);
                new Thread(new PeerHandler(socket)).start();
            }
        } catch (IOException e) {
            if (active) log("[SERVER ERROR] " + e.getMessage());
        }
    }

    private synchronized void addPeer(Socket socket) {
        for (Socket s : peers) {
            if (s.equals(socket)) return;
        }
        Socket[] newPeers = new Socket[peers.length + 1];
        System.arraycopy(peers, 0, newPeers, 0, peers.length);
        newPeers[peers.length] = socket;
        peers = newPeers;
    }

    private synchronized void removePeer(Socket socket) {
        int count = 0;
        for (Socket s : peers) {
            if (s.equals(socket)) count++;
        }
        if (count == 0) return;
        Socket[] newPeers = new Socket[peers.length - count];
        int idx = 0;
        for (Socket s : peers) {
            if (!s.equals(socket)) {
                newPeers[idx++] = s;
            }
        }
        peers = newPeers;
    }

    private class PeerHandler implements Runnable {
        private final Socket socket;
        public PeerHandler(Socket socket) { this.socket = socket; }

        @Override
        public void run() {
            try {
                BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), "UTF-8"));
                String line;
                while ((line = reader.readLine()) != null) {
                    log("[INBOUND PACKET] " + line);
                    if (listener != null) listener.onPacketReceived(line);
                }
            } catch (IOException e) {
                log("[PEER DROPPED] Connection lost.");
            } finally {
                removePeer(socket);
            }
        }
    }

    public void broadcast(final String message) {
        log("[BROADCASTING] " + message);
        new Thread(new Runnable() {
            @Override
            public void run() {
                Socket[] currentPeers = peers;
                for (Socket socket : currentPeers) {
                    try {
                        OutputStream out = socket.getOutputStream();
                        out.write((message + "\n").getBytes("UTF-8"));
                        out.flush();
                    } catch (IOException e) {
                        removePeer(socket);
                    }
                }
            }
        }).start();
    }

    public void connectToPeer(final String host, final int targetPort) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    Socket socket = new Socket(host, targetPort);
                    addPeer(socket);
                    log("[OUTBOUND CONNECTION] Connected to " + host + ":" + targetPort);
                    new Thread(new PeerHandler(socket)).start();
                } catch (IOException e) {
                    log("[CONNECTION FAILED] Could not reach " + host + ":" + targetPort);
                }
            }
        }).start();
    }

    public void stop() {
        active = false;
        try {
            if (serverSocket != null) serverSocket.close();
            Socket[] currentPeers = peers;
            for (Socket s : currentPeers) {
                try {
                    s.close();
                } catch (IOException ignored) {}
            }
            peers = new Socket[0];
            log("[ENGINE STOPPED] Bus deactivated.");
        } catch (IOException e) {
            log("[ERROR] " + e.getMessage());
        }
    }

    private void log(String msg) {
        if (listener != null) listener.onLog(msg + "\n");
    }
}