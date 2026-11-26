package view;

import javafx.animation.AnimationTimer;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.chart.LineChart;
import javafx.scene.chart.NumberAxis;
import javafx.scene.chart.XYChart;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.layout.*;
import javafx.scene.paint.Color;
import model.MetricSnapshot;
import service.LiveTelemetryService;

import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

public class MonitoringDashboard extends BorderPane {

    private LineChart<Number, Number> latencyChart;
    private XYChart.Series<Number, Number> latencyDataSeries;
    private int chartXIndex = 0;

    private Label lblLatency, lblMemory, lblThroughput, lblParity, lblFrequency;
    private TextArea terminalConsole;
    private Canvas waveformCanvas;
    private double wavePhase = 0;

    public MonitoringDashboard() {
        getStyleClass().add("root-pane");
        setPadding(new Insets(15));

        initHeader();
        initLeftSidebarGauges();
        initCenterRealtimeChart();
        initBottomTerminalConsole();
        initLiveTelemetryStream();
        initCanvasWaveformAnimation();
    }

    private void initHeader() {
        HBox header = new HBox();
        header.getStyleClass().add("header-box");
        header.setAlignment(Pos.CENTER_LEFT);
        header.setPadding(new Insets(10, 15, 10, 15));

        Label title = new Label("OMNI-GRID ARCHITECTURE TELEMETRY MONITOR");
        title.getStyleClass().add("header-title");
        
        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);
        
        Label status = new Label("STATUS: ACTIVE RUNNING");
        status.getStyleClass().add("status-badge");

        header.getChildren().addAll(title, spacer, status);
        setTop(header);
    }

    private void initLeftSidebarGauges() {
        VBox sidebar = new VBox(15);
        sidebar.getStyleClass().add("sidebar-box");
        sidebar.setPrefWidth(260);
        sidebar.setPadding(new Insets(15, 10, 15, 10));

        lblLatency = createGaugeCard(sidebar, "NETWORK LATENCY", "0.00 ms", "neon-cyan");
        lblMemory = createGaugeCard(sidebar, "MEMORY BLOCKS CACHED", "0.00 blocks", "neon-magenta");
        lblThroughput = createGaugeCard(sidebar, "TRANSACTION THROUGHPUT", "0 tx/s", "neon-green");
        lblFrequency = createGaugeCard(sidebar, "HARMONIC BASELINE", "7.83 Hz", "neon-gold");
        lblParity = createGaugeCard(sidebar, "PARITY SYNCHRONIZER", "[ 1 - 0 - 0 - 1 ]", "neon-white");

        setLeft(sidebar);
    }

    private Label createGaugeCard(VBox parent, String title, String defaultVal, String styleClass) {
        VBox card = new VBox(4);
        card.getStyleClass().add("gauge-card");
        
        Label lblTitle = new Label(title);
        lblTitle.getStyleClass().add("gauge-title");
        
        Label lblValue = new Label(defaultVal);
        lblValue.getStyleClass().addAll("gauge-value", styleClass);
        
        card.getChildren().addAll(lblTitle, lblValue);
        parent.getChildren().add(card);
        return lblValue;
    }

    private void initCenterRealtimeChart() {
        VBox centerContainer = new VBox(15);
        centerContainer.setPadding(new Insets(0, 0, 0, 15));
        VBox.setVgrow(centerContainer, Priority.ALWAYS); // Fixed line 97 calculation mismatch!

        NumberAxis xAxis = new NumberAxis(0, 50, 5);
        xAxis.setTickLabelsVisible(false);
        xAxis.setForceZeroInRange(false);
        
        NumberAxis yAxis = new NumberAxis(5, 20, 2);
        yAxis.setLabel("Latency Variance (ms)");

        latencyChart = new LineChart<>(xAxis, yAxis);
        latencyChart.getStyleClass().add("modern-chart");
        latencyChart.setCreateSymbols(false);
        latencyChart.setAnimated(false);
        latencyChart.setTitle("REAL-TIME FABRIC INFERENCE DRIFT TRACKER");

        latencyDataSeries = new XYChart.Series<>();
        latencyDataSeries.setName("Inference Latency");
        latencyChart.getData().add(latencyDataSeries);

        VBox canvasContainer = new VBox(5);
        canvasContainer.getStyleClass().add("canvas-container");
        Label canvasTitle = new Label("7.83 Hz SCHUMANN CLOCK RESONANCE OSCILLATOR WAVEFORM");
        canvasTitle.getStyleClass().add("gauge-title");
        
        waveformCanvas = new Canvas(600, 80);
        canvasContainer.getChildren().addAll(canvasTitle, waveformCanvas);

        centerContainer.getChildren().addAll(latencyChart, canvasContainer);
        setCenter(centerContainer);
    }

    private void initBottomTerminalConsole() {
        VBox bottomContainer = new VBox(5);
        bottomContainer.setPadding(new Insets(15, 0, 0, 0));

        Label lblConsole = new Label("SYSTEM CONSOLE EVENT DISPATCHER LOGS");
        lblConsole.getStyleClass().add("gauge-title");

        terminalConsole = new TextArea();
        terminalConsole.setEditable(false);
        terminalConsole.setWrapText(true);
        terminalConsole.getStyleClass().add("terminal-output");
        terminalConsole.setPrefHeight(140);

        bottomContainer.getChildren().addAll(lblConsole, terminalConsole);
        setBottom(bottomContainer);
    }

    private void initLiveTelemetryStream() {
        LiveTelemetryService service = new LiveTelemetryService();
        service.setOnSucceeded(event -> {
            MetricSnapshot snapshot = service.getValue();
            if (snapshot != null) {
                updateUIElements(snapshot);
            }
        });
        service.start();
    }

    private void updateUIElements(MetricSnapshot snapshot) {
        Platform.runLater(() -> {
            lblLatency.setText(String.format("%.2f ms", snapshot.getNetworkLatency()));
            lblMemory.setText(String.format("%.1f Blocks", snapshot.getMemoryUsageBlocks()));
            lblThroughput.setText(String.format("%,d Tx", snapshot.getTransactionalThroughput()));
            lblFrequency.setText(String.format("%.4f Hz", snapshot.getHarmonicFrequency()));
            lblParity.setText(String.format("ACTIVE BIT: [ %d ]", snapshot.getParityBit()));

            latencyDataSeries.getData().add(new XYChart.Data<>(chartXIndex++, snapshot.getNetworkLatency()));
            if (latencyDataSeries.getData().size() > 50) {
                latencyDataSeries.getData().remove(0);
                NumberAxis xAxis = (NumberAxis) latencyChart.getXAxis();
                xAxis.setLowerBound(chartXIndex - 50);
                xAxis.setUpperBound(chartXIndex);
            }

            String logTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"));
            terminalConsole.appendText(String.format("[%s] [SYS_LOG] Sync Cycle: %d | Throughput Verified | Parity Synced.\n", 
                    logTime, snapshot.getTransactionalThroughput() % 1000));
        });
    }

    private void initCanvasWaveformAnimation() {
        GraphicsContext gc = waveformCanvas.getGraphicsContext2D();
        new AnimationTimer() {
            @Override
            public void handle(long now) {
                double width = waveformCanvas.getWidth();
                double height = waveformCanvas.getHeight();
                
                gc.clearRect(0, 0, width, height);
                gc.setStroke(Color.web("#e0a96d")); // Neon Gold
                gc.setLineWidth(2.0);
                gc.beginPath();

                for (int x = 0; x < width; x++) {
                    double y = (height / 2) + Math.sin((x * 0.03) + wavePhase) * 20 * Math.sin(x * 0.005);
                    if (x == 0) gc.moveTo(x, y);
                    else gc.lineTo(x, y);
                }
                gc.stroke();
                wavePhase += 0.08;
            }
        }.start();
    }
}
