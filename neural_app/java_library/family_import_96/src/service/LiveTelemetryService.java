package service;
import neural.studio.*;





import javafx.concurrent.ScheduledService;

import javafx.concurrent.Task;

import javafx.util.Duration;

import model.MetricSnapshot;

import java.util.Random;



public class LiveTelemetryService extends ScheduledService<MetricSnapshot> {

    private final Random random = new Random();

    private long baseThroughput = 42000L;

    private int stepCounter = 0;



    public LiveTelemetryService() {

        // Set update loop matching the harmonic resonance ratio (approx every ~127ms for 7.83Hz)

        setPeriod(Duration.millis(127)); 

    }



    @Override

    protected Task<MetricSnapshot> createTask() {

        return new Task<>() {

            @Override

            protected MetricSnapshot call() throws Exception {

                stepCounter++;

                

                // Simulate non-linear data variations

                double latency = 12.0 + (random.nextGaussian() * 1.5);

                double memoryBlocks = 64.0 + (Math.sin(stepCounter * 0.1) * 12.0) + random.nextInt(5);

                baseThroughput += random.nextInt(15);

                double frequency = 7.83 + (random.nextGaussian() * 0.02);

                

                // 1-0-0-1 toggle pattern matching parity sync sequence

                int[] paritySequence = {1, 0, 0, 1};

                int activeParity = paritySequence[stepCounter % 4];



                return new MetricSnapshot(latency, memoryBlocks, baseThroughput, frequency, activeParity);

            }

        };

    }

}

