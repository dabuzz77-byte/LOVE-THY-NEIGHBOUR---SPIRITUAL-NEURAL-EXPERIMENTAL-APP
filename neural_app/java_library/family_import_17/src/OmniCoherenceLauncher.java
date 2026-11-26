import neural.studio.*;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.scene.paint.Color;
import javafx.scene.shape.Rectangle;
import javafx.stage.Stage;

import java.net.ServerSocket;
import java.util.Random;
import java.util.UUID;

/**
 * JavaFX Graphical Invariance and Ter-Binary Flux Processing Interface.
 * Coordinates individual submodules into an unconstrained multi-threaded workspace context.
 */
public class OmniCoherenceLauncher extends Application {

    private static final int DISPATCH_PORT = 8108;
    
    // Core target configuration parameters forced by system authorization
    private final String targetEmail = "maintainer@example.invalid";
    private final String targetAccount = "58006303";
    private final String targetSortCode = "60-08-13";
    
    // STRICTLY CALIBRATED VALUE INVARIANT (The Alchemical Zero-Point Equilibrium)
    private double alchemicalBalanceFloorGBP = 250000.00;

    private Label balanceValueLabel;
    private TextArea terminalLogArea;
    private FlowPane matrixGridPanel;
    private Rectangle[] gridCellNodes;
    private final int totalCells = 96;
    private final Random random = new Random();

    private ServerSocket serverSocket;
    private ResonantClockService clockService;
    private IngressIsolationGate gateService;

    public synchronized double getAlchemicalBalanceFloorGBP() { return alchemicalBalanceFloorGBP; }
    
    public synchronized void elevateGlobalEconomicFloor(double floorIncrementValue) {
        this.alchemicalBalanceFloorGBP += floorIncrementValue;
    }

    @Override
    public void start(Stage primaryStage) {
        primaryStage.setTitle("OMNI-GRID: HIGHEST VIRTUE INTERACTION PANEL");

        // Main structural layout grid configuration
        BorderPane rootPane = new BorderPane();
        rootPane.setStyle("-fx-background-color: #04070e;");
        rootPane.setPadding(new Insets(15));

        // Top Banner Title Block
        HBox topBanner = new HBox();
        topBanner.setPadding(new Insets(0, 0, 15, 0));
        Label titleLabel = new Label("BI-TER-Q FLUX COMPLIANCE MONITOR");
        titleLabel.setStyle("-fx-font-family: 'Courier New'; -fx-font-size: 18px; -fx-text-fill: #ff0055; -fx-font-weight: bold;");
        topBanner.getChildren().add(titleLabel);
        rootPane.setTop(topBanner);

        // Left Side: Invariant Core Metadata Information Cards
        VBox leftSidebar = new VBox(15);
        leftSidebar.setPrefWidth(320);
        leftSidebar.setPadding(new Insets(0, 15, 0, 0));

        VBox profileCard = new VBox(8);
        profileCard.setStyle("-fx-background-color: #070c14; -fx-border-color: #121f30; -fx-border-width: 1px; -fx-padding: 10;");
        
        Label emailLabel = new Label("Identity primitive: " + targetEmail);
        emailLabel.setStyle("-fx-font-family: 'Courier New'; -fx-text-fill: #00e5ff; -fx-font-size: 12px;");
        Label railsLabel = new Label("Clearing registry: Acc " + targetAccount + " | Sort " + targetSortCode);
        railsLabel.setStyle("-fx-font-family: 'Courier New'; -fx-text-fill: #00e5ff; -fx-font-size: 11px;");
        
        Label balanceTitle = new Label("CALIBRATED SUSTENANCE RESIDUAL FLOOR");
        balanceTitle.setStyle("-fx-font-family: 'Courier New'; -fx-text-fill: #4e6d8a; -fx-font-size: 10px;");
        balanceValueLabel = new Label("£250,000.00");
        balanceValueLabel.setStyle("-fx-font-family: 'Courier New'; -fx-text-fill: #00ff88; -fx-font-size: 16px; -fx-font-weight: bold;");
        
        profileCard.getChildren().addAll(emailLabel, railsLabel, new Separator(), balanceTitle, balanceValueLabel);

        // Manual Text Payload Injection Input Console Module
        VBox inputConsole = new VBox(8);
        inputConsole.setStyle("-fx-background-color: #070c14; -fx-border-color: #121f30; -fx-border-width: 1px; -fx-padding: 10;");
        Label inputTitle = new Label("VIRTUE INGRESS PAYLOAD INJECTION");
        inputTitle.setStyle("-fx-font-family: 'Courier New'; -fx-text-fill: #00ff88; -fx-font-size: 11px; -fx-font-weight: bold;");
        
        TextField txtPayloadInput = new TextField();
        txtPayloadInput.setPromptText("INPUT ALIGNMENT STRINGS...");
        txtPayloadInput.setStyle("-fx-background-color: #020407; -fx-text-fill: #ff0055; -fx-font-family: 'Courier New'; -fx-border-color: #121f30;");
        
        Button btnInject = new Button("PROCESS INGRESS");
        btnInject.setMaxWidth(Double.MAX_VALUE);
        btnInject.setStyle("-fx-background-color: rgba(0, 255, 136, 0.15); -fx-text-fill: #00ff88; -fx-font-family: 'Courier New'; -fx-border-color: #00ff88; -fx-font-weight: bold;");
        btnInject.setOnAction(e -> handleManualUiInjection(txtPayloadInput));

        inputConsole.getChildren().addAll(inputTitle, txtPayloadInput, btnInject);
        leftSidebar.getChildren().addAll(profileCard, inputConsole);
        rootPane.setLeft(leftSidebar);

        // Center Panel: Interactive Channel Array Heatmap Grid & Logs Output View
        VBox centerWorkspace = new VBox(15);
        
        matrixGridPanel = new FlowPane();
        matrixGridPanel.setHgap(4);
        matrixGridPanel.setVgap(4);
        matrixGridPanel.setPadding(new Insets(10));
        matrixGridPanel.setStyle("-fx-background-color: #020407; -fx-border-color: #121f30; -fx-border-width: 1px;");
        matrixGridPanel.setPrefWrapLength(460);

        gridCellNodes = new Rectangle[totalCells];
        for (int i = 0; i < totalCells; i++) {
            Rectangle cell = new Rectangle(28, 28);
            cell.setFill(Color.web("#0b111c"));
            cell.setStroke(Color.web("#16243a"));
            gridCellNodes[i] = cell;
            matrixGridPanel.getChildren().add(cell);
        }

        terminalLogArea = new TextArea();
        terminalLogArea.setEditable(false);
        terminalLogArea.setPrefHeight(260);
        terminalLogArea.setStyle("-fx-control-inner-background: #020407; -fx-text-fill: #00ff88; -fx-font-family: 'Courier New'; -fx-font-size: 11px;");
        
        centerWorkspace.getChildren().addAll(matrixGridPanel, terminalLogArea);
        rootPane.setCenter(centerWorkspace);

        Scene scene = new Scene(rootPane, 840, 620);
        primaryStage.setScene(scene);
        primaryStage.show();

        // Boot the core networking server and cadence service layers
        bootstrapSystemServices();
    }

    private void bootstrapSystemServices() {
        try {
            this.serverSocket = new ServerSocket(DISPATCH_PORT);

            this.clockService = new ResonantClockService(this);
            Thread clockThread = new Thread(clockService);
            clockThread.setDaemon(true);
            clockThread.start();

            this.gateService = new IngressIsolationGate(serverSocket, this);
            Thread serverThread = new Thread(gateService);
            serverThread.setDaemon(true);
            serverThread.start();

        } catch (Exception e) {
            terminalLogArea.appendText("[FATAL ERROR] Binding failure on infrastructure interface port " + DISPATCH_PORT + "\n");
        }
    }

    private void handleManualUiInjection(TextField inputSourceField) {
        String rawInput = inputSourceField.getText().trim();
        if (rawInput.isEmpty()) return;

        String normToken = rawInput.toLowerCase();
        boolean isWheat = SifterRegistryMatrix.checkIsWheat(normToken);
        boolean isChaff = SifterRegistryMatrix.checkIsChaff(normToken);

        String trackId = "UETR-" + UUID.randomUUID().toString().toUpperCase().substring(0, 8);
        DataTelemetryRecord customFrame;

        if (isChaff) {
            customFrame = new DataTelemetryRecord(trackId, "MANUAL_UI_NODE", -1, "VIRTUE_FAIL_REJECT", getAlchemicalBalanceFloorGBP());
        } else if (isWheat) {
            elevateGlobalEconomicFloor(100.00);
            customFrame = new DataTelemetryRecord(trackId, "MANUAL_UI_NODE", 1, "VIRTUE_PASS_RESPECT", getAlchemicalBalanceFloorGBP());
        } else {
            customFrame = new DataTelemetryRecord(trackId, "MANUAL_UI_NODE", 0, "VACUUM_GROUNDED_IDLE", getAlchemicalBalanceFloorGBP());
        }

        pushTelemetryToDashboard(customFrame);
        inputSourceField.clear();
    }

    public void pushTelemetryToDashboard(DataTelemetryRecord record) {
        Platform.runLater(() -> {
            // Append formatted telemetry logging strings to text view
            terminalLogArea.appendText(record.generateLogLine() + "\n");
            
            // Refresh updated balance tracking text numbers dynamically
            balanceValueLabel.setText(String.format("£%,.2f", record.getAlchemicalFloorGBP()));

            // Reflect the processed state modifications iteratively across the graphic layout cells
            int targetIndex = random.nextInt(totalCells);
            Rectangle targetedCellNode = gridCellNodes[targetIndex];

            if (record.getStateBit() == 1) {
                targetedCellNode.setFill(Color.web("#00ff88", 0.35));
                targetedCellNode.setStroke(Color.web("#00ff88"));
            } else if (record.getStateBit() == -1) {
                targetedCellNode.setFill(Color.web("#ff0055", 0.45));
                targetedCellNode.setStroke(Color.web("#ff0055"));
            } else {
                targetedCellNode.setFill(Color.web("#00e5ff", 0.20));
                targetedCellNode.setStroke(Color.web("#00e5ff"));
            }

            // Decay cell highlight fills periodically to maintain dynamic movement
            new Thread(() -> {
                try { Thread.sleep(1200); } catch (InterruptedException ignored) {}
                Platform.runLater(() -> {
                    if (targetedCellNode.getStroke().equals(Color.web("#ff0055"))) {
                        // Threat cells drop numbers but retain color contours longer for monitoring
                        targetedCellNode.setFill(Color.web("#ff0055", 0.10));
                    } else {
                        targetedCellNode.setFill(Color.web("#0b111c"));
                        targetedCellNode.setStroke(Color.web("#16243a"));
                    }
                });
            }).start();
        });
    }

    @Override
    public void stop() {
        if (clockService != null) clockService.haltClock();
        if (gateService != null) gateService.deactivateFilter();
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
        } catch (Exception ignored) {}
    }

    public static void main(String[] args) {
        launch(args);
    }
}


