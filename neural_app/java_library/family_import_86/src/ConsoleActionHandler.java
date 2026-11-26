import neural.studio.*;
import javax.swing.*;

/**
 * MODULE 6b: GRAPHICAL WORKER LINK TRANSCEIVER — STACK-OVERFLOW FIXED
 * Dispatches heavy HTTP post calls asynchronously with pure value reads to prevent loops.
 */
public class ConsoleActionHandler {

    public static void dispatchInferenceJob(
            JTextField promptInput,
            JPasswordField cloudKeyField,
            JComboBox<String> routeSelector,
            JButton runButton,
            JTextArea logsArea,
            LocalOllamaBridge localBridge,
            GoogleCloudBridge cloudBridge,
            CentralPortRouter routerBus) {

        // Extract the absolute text strings immediately to decouple from UI events
        final String promptText = promptInput.getText().trim();
        final String securedKey = new String(cloudKeyField.getPassword()).trim();
        final int activeSelection = routeSelector.getSelectedIndex();

        if (promptText.isEmpty()) return;

        // Visual update on the main thread pool
        logsArea.append("[USER REQUEST]: " + promptText + "\n");
        promptInput.setText("");
        runButton.setEnabled(false);

        // Ping the visual graph canvas port without touching UI event registers
        pingRouterPortBus(routerBus);

        // Process network requests on a clean background worker thread
        SharedSwingWorker<String, Void> networkTask = new SharedSwingWorker<>() {
            @Override
            protected String doInBackground() throws Exception {
                if (activeSelection == 0) {
                    return localBridge.executeLocalInference("llama3", promptText);
                } else if (activeSelection == 1) {
                    return localBridge.executeLocalInference("flux", promptText);
                } else {
                    if (securedKey.isEmpty()) {
                        return "[CRITICAL ERROR]: Target aborted. Google AI Studio key token is missing.";
                    }
                    return cloudBridge.executeCloudContentGeneration(securedKey, promptText);
                }
            }

            @Override
            protected void done() {
                try {
                    String engineOutput = get();
                    logsArea.append("[BRIDGE INSTANCE RECONCILIATION RESULT]:\n" + engineOutput + "\n\n");
                } catch (Exception fatalEx) {
                    logsArea.append("[ROUTER HUB TASK EXCEPTION CRITICAL]: " + fatalEx.getMessage() + "\n\n");
                } finally {
                    runButton.setEnabled(true);
                    logsArea.setCaretPosition(logsArea.getDocument().getLength());
                }
            }
        };
        networkTask.execute();
    }

    private static void pingRouterPortBus(CentralPortRouter routerBus) {
        int targetLoopbackPort = routerBus.getActiveLocalPort();
        if (targetLoopbackPort == -1) return;
        try (java.net.Socket transportSocket = new java.net.Socket("127.0.0.1", targetLoopbackPort);
             java.io.OutputStream outgoingStream = transportSocket.getOutputStream()) {
            outgoingStream.write("PULSE\n".getBytes("UTF-8"));
            outgoingStream.flush();
        } catch (Exception ignored) {}
    }
}
