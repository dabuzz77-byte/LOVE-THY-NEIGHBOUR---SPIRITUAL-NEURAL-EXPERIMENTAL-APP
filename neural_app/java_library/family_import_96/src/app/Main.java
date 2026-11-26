package app;
import neural.studio.*;





import javafx.application.Application;

import javafx.scene.Scene;

import javafx.stage.Stage;

import view.MonitoringDashboard;

import java.net.URL;



/**

 * Main Application Bootstrapper.

 * Connects the advanced JavaFX graphical telemetry layout to the runtime system stage.

 */

public class Main extends Application {



    @Override

    public void start(Stage primaryStage) {

        try {

            System.out.println("[SYS_LOG] Initializing JavaFX Application Thread...");

            

            // 1. Initialize the advanced multi-threaded graphical dashboard

            MonitoringDashboard dashboard = new MonitoringDashboard();

            

            // 2. Wrap the interface layout in a standard 1024x720 responsive scene

            Scene scene = new Scene(dashboard, 1024, 720);

            

            // 3. Defensive resource resolution to avoid runtime Exit Value: 1 crashes

            URL cssResource = getClass().getResource("/view/modern-dark.css");

            if (cssResource != null) {

                String stylesheetPath = cssResource.toExternalForm();

                scene.getStylesheets().add(stylesheetPath);

                System.out.println("[SYS_LOG] Core presentation layer loaded: " + stylesheetPath);

            } else {

                System.err.println("\n[WARNING] Could not locate '/view/modern-dark.css' in the resources target path!");

                System.err.println("[WARNING] Please check that your file sits at: src/main/resources/view/modern-dark.css");

                System.err.println("[WARNING] Proceeding with unstyled default interface fallback configuration...");

            }

            

            // 4. Configure window titles and commit the operational stage

            primaryStage.setTitle("Omni-Inference Advanced System Monitor");

            primaryStage.setScene(scene);

            

            // Handle graceful thread shutdown when user exits the interface window

            primaryStage.setOnCloseRequest(event -> {

                System.out.println("[SYS_LOG] Interface termination requested. Exiting processing loops safely...");

                System.exit(0);

            });



            primaryStage.show();

            System.out.println("[SYS_LOG] System monitor interface successfully brought online.");

            

        } catch (Exception e) {

            System.err.println("[FATAL ERROR] An unexpected exception occurred during GUI runtime initialization:");

            e.printStackTrace();

            System.exit(1);

        }

    }



    public static void main(String[] args) {

        // Handoff execution parameters directly to the underlying JavaFX runtime stack

        launch(args);

    }

}

