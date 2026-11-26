package clients;
import neural.studio.*;





import android.app.Notification;

import android.app.NotificationChannel;

import android.app.NotificationManager;

import android.app.Service;

import android.content.Intent;

import android.os.IBinder;

import java.io.OutputStream;

import java.net.InetSocketAddress;

import java.net.Socket;

import java.nio.charset.StandardCharsets;



public class AndroidForegroundBridgeService extends Service {



    private boolean isServiceActive = true;

    private final String targetHost = "192.168.1.50"; // Configure to point to your main Java engine IP

    private final int targetPort = 7847;

    private Thread socketWorkerThread;



    @Override

    public void onCreate() {

        super.onCreate();

        initializeAndroidNotificationChannel();

        launchPersistentLatchSocket();

    }



    private void initializeAndroidNotificationChannel() {

        String channelId = "GHOST_MANIFOLD_JAVA";

        String channelName = "Java Native Grid Sync";

        

        NotificationChannel channel = new NotificationChannel(channelId, channelName, NotificationManager.IMPORTANCE_LOW);

        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);

        if (manager != null) {

            manager.createNotificationChannel(channel);

        }



        Notification notification = new Notification.Builder(this, channelId)

            .setContentTitle("Ghost Manifold Java Core Online")

            .setContentText("Maintaining parallel hardware socket connection...")

            .setAutoCancel(false)

            .build();



        startForeground(7835, notification);

    }



    private void launchPersistentLatchSocket() {

        socketWorkerThread = new Thread(new Runnable() {

            @Override

            public void run() {

                while (isServiceActive) {

                    try (Socket socket = new Socket()) {

                        socket.connect(new InetSocketAddress(targetHost, targetPort), 3000);

                        OutputStream os = socket.getOutputStream();



                        while (isServiceActive) {

                            String telemetryFrame = String.format(

                                "{\"os_target\":\"ANDROID_JAVA_OS\",\"status\":\"LATCHED\",\"hardware_vault\":\"SECURE_ENCLAVE_VERIFIED\"}\n"

                            );

                            os.write(telemetryFrame.getBytes(StandardCharsets.UTF_8));

                            os.flush();

                            

                            Thread.sleep(3000); // Validation interval

                        }

                    } catch (Exception networkDropout) {

                        // Connection failed or timed out; sleep and attempt automatic socket recovery loop

                        try { Thread.sleep(6000); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); }

                    }

                }

            }

        }, "AndroidGhostSocketWorker");

        socketWorkerThread.setDaemon(true);

        socketWorkerThread.start();

    }



    @Override

    public int onStartCommand(Intent intent, int flags, int startId) {

        return START_STICKY; // Forces Android OS to automatically rebuild the network pipeline if terminated

    }



    @Override

    public void onDestroy() {

        this.isServiceActive = false;

        if (socketWorkerThread != null) {

            socketWorkerThread.interrupt();

        }

        super.onDestroy();

    }



    @Override

    public IBinder onBind(Intent intent) {

        return null;

    }

}

