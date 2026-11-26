import neural.studio.*;
import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.nio.file.*;
import java.util.Arrays;

/** Dependency-free behavioral checks; run through check.bat. */
public final class EngineChecks {
    static int checks;
    static void check(boolean ok, String message) { checks++; if (!ok) throw new AssertionError(message); }
    static void rejects(Runnable r, String message) {
        boolean rejected = false;
        try { r.run(); } catch (IllegalArgumentException ex) { rejected = true; }
        check(rejected, message);
    }
    public static void main(String[] args) throws Exception {
        LocalInferenceBusEngine.NeuralModel m = LocalInferenceBusEngine.NeuralModel.train(783);
        System.out.printf("Synthetic holdout accuracy: %.2f%%%n", m.validationAccuracy * 100);
        check(m.validationAccuracy > .94, "Model must learn the synthetic activity boundaries");
        double[][] examples = {{.04, .35, .02}, {.9, .4, .05}, {.1, .4, .95}, {.1, .98, .05}};
        for (int i = 0; i < 4; i++) {
            LocalInferenceBusEngine.Prediction p = m.infer(examples[i]);
            check(p.winner == i, "Wrong canonical class " + i);
            check(Math.abs(Arrays.stream(p.output).sum() - 1) < 1e-12, "Probabilities must sum to one");
        }
        rejects(() -> m.infer(Double.NaN, .2, .3), "NaN inference must fail");
        rejects(() -> m.infer(-.1, .2, .3), "Negative inference must fail");
        rejects(() -> m.infer(1.1, .2, .3), "Overflow inference must fail");
        rejects(() -> m.infer(.1, .2), "Missing inference input must fail");
        Path dir = Files.createTempDirectory("inference-bus-check-");
        Path saved = dir.resolve("model.bin");
        try {
            m.save(saved);
            LocalInferenceBusEngine.NeuralModel loaded = LocalInferenceBusEngine.NeuralModel.load(saved);
            check(Arrays.equals(m.infer(examples[1]).output, loaded.infer(examples[1]).output), "Saved model predictions must round-trip exactly");
            Files.write(saved, new byte[]{0, 1, 2});
            boolean rejected = false;
            try { LocalInferenceBusEngine.NeuralModel.load(saved); } catch (java.io.IOException ex) { rejected = true; }
            check(rejected, "Truncated model must fail cleanly");
        } finally { Files.deleteIfExists(saved); Files.deleteIfExists(dir); }
        LocalInferenceBusEngine.Sampler sampler = new LocalInferenceBusEngine.Sampler();
        sampler.acceptCounters(1000, 2000, 1_000_000_000L);
        check(sampler.rx < 0, "First network sample needs a baseline");
        sampler.acceptCounters(5000, 4000, 3_000_000_000L);
        check(sampler.rx == 2000 && sampler.tx == 1000, "Network rates must use elapsed seconds");
        sampler.acceptCounters(2, 3, 4_000_000_000L);
        check(sampler.rx < 0 && sampler.tx < 0, "Counter reset must not create a traffic spike");
        sampler.sampleSystem();
        check(sampler.latest.totalMemory > 0, "System memory sensor must be available"); sampler.close();
        LocalInferenceBusEngine.Telemetry idle = new LocalInferenceBusEngine.Telemetry(.02, .3, .01, 0, 0, 3, 10);
        LocalInferenceBusEngine.Telemetry busy = new LocalInferenceBusEngine.Telemetry(.9, .85, .1, 1048576, 65536, 8, 10);
        double idleMotion = LocalInferenceBusEngine.ActivityMotion.target(idle, m.infer(.02, .3, 0), .75, .3, 0);
        double busyMotion = LocalInferenceBusEngine.ActivityMotion.target(busy, m.infer(.9, .85, 1), .75, .3, 0);
        check(busyMotion > idleMotion + .4, "Real system load must materially change motion");
        check(LocalInferenceBusEngine.ActivityMotion.target(idle, null, 0, .1, 0) < LocalInferenceBusEngine.ActivityMotion.target(idle, null, 0, .9, 0), "Random layer must affect motion");
        check(LocalInferenceBusEngine.ActivityMotion.target(idle, null, 1, .1, 0) == LocalInferenceBusEngine.ActivityMotion.target(idle, null, 1, .9, 0), "100% system blend must exclude random intensity");
        check(LocalInferenceBusEngine.AtomCanvas.density(.5, .2, 0, 0) == .25, "Pure 1s density must be the squared amplitude");
        check(Math.abs(LocalInferenceBusEngine.AtomCanvas.density(.5, .2, 1, 0) - .04) < 1e-12, "Pure 2p density must be the squared amplitude");
        double constructive = LocalInferenceBusEngine.AtomCanvas.density(.5, .2, .5, 0);
        double destructive = LocalInferenceBusEngine.AtomCanvas.density(.5, .2, .5, Math.PI);
        check(constructive > destructive && destructive >= 0, "Superposition must include a nonnegative phase-dependent interference term");
        check(LocalInferenceBusEngine.AtomCanvas.excitedWeight(busyMotion) > LocalInferenceBusEngine.AtomCanvas.excitedWeight(idleMotion), "System activity must change the atom state blend");
        double integral = 0;
        java.util.Random probabilityRandom = new java.util.Random(9);
        for (int i = 0; i < 20000; i++) {
            LocalInferenceBusEngine.HydrogenSample point = new LocalInferenceBusEngine.HydrogenSample(probabilityRandom, (i & 1) == 0);
            integral += LocalInferenceBusEngine.AtomCanvas.density(point.s, point.p, .43, .8) / point.proposal;
        }
        check(Math.abs(integral / 20000 - 1) < .035, "Weighted orbital sampling must preserve normalized probability");
        SwingUtilities.invokeAndWait(() -> {
            LocalInferenceBusEngine.ConsolePanel ui = new LocalInferenceBusEngine.ConsolePanel(false);
            try {
                ui.model = m; ui.sampler.latest = busy; ui.tick();
                check(ui.atomView.isSelected() && ui.atomCanvas.isVisible(), "Hydrogen / silicon must be the default view");
                ui.execute("view neural"); check(ui.neuralView.isSelected() && ui.canvas.isVisible(), "Neural view command must reveal the activation graph");
                ui.execute("view atom"); check(ui.atomView.isSelected() && ui.atomCanvas.isVisible(), "Atom view command must restore the new graphic");
                check(ui.inferences == 1 && ui.prediction != null, "A live sensor sample must trigger neural inference");
                ui.tick(); check(ui.inferences == 1, "Same sensor sample must not count as a new inference");
                double phase = ui.canvas.phase;
                ui.execute("pause"); ui.tick(); check(ui.canvas.phase == phase, "Pause must freeze motion");
                ui.execute("net off"); check(ui.prediction == null && !ui.netActive, "Net off must stop inference");
                ui.execute("net on"); ui.tick(); check(ui.netActive && ui.prediction != null, "Net on must restore inference");
                ui.execute("mix 63"); check(ui.mix == .63, "Command must update mix control");
                ui.execute("mix NaN"); check(ui.mix == .63, "Invalid mix must preserve current value");
                ui.execute("speed Infinity"); check(ui.speed == 1, "Invalid speed must preserve current value");
                ui.execute("speed 2"); check(ui.speed == 2, "Speed command must work");
                ui.execute("infer .9 .4 .05"); check(ui.log.getText().contains("Sample result: COMPUTE"), "Inference command must return model output");
                ui.execute("infer 5 .4 .05"); check(ui.log.getText().contains("Enter a number"), "Bad inference command must show error");
                ui.execute("bogus"); check(ui.log.getText().contains("Unknown command"), "Unknown command must show help hint");
                ui.execute("resume"); check(!ui.paused, "Resume must work");
                ui.command.setText("draft");
                ui.command.getActionMap().get("history-up").actionPerformed(null);
                check(ui.command.getText().equals("resume"), "Up must recall command");
                ui.command.getActionMap().get("history-down").actionPerformed(null);
                check(ui.command.getText().equals("draft"), "Down must restore draft");
                ui.execute("mix 75"); ui.command.setText("");
                ui.sampler.latest = new LocalInferenceBusEngine.Telemetry(-1, .6, .01, -1, -1, 6, 10); ui.tick();
                check(ui.prediction != null && ui.modelStatus.getText().contains("PARTIAL"), "Partial sensors must support explicitly labeled inference");
                ui.sampler.latest = LocalInferenceBusEngine.Telemetry.empty(); ui.tick();
                check(ui.prediction == null, "No sensors must not manufacture an inference");
                ui.sampler.latest = busy; ui.tick();
                if (args.length > 0) {
                    ui.log.setText(""); ui.append("QA preview: synthetic sensor fixture. Live sensors are tested separately.");
                    render(ui, 1228, 817, Paths.get(args[0] + "-large.png"));
                    render(ui, 944, 781, Paths.get(args[0] + "-small.png"));
                    ui.showView("neural"); render(ui, 1228, 817, Paths.get(args[0] + "-neural.png"));
                }
            } finally { ui.close(); }
        });
        System.out.println("PASS: " + checks + " behavioral checks.");
    }
    static void layout(Container c) { c.doLayout(); for (Component child : c.getComponents()) if (child instanceof Container) layout((Container) child); }
    static void render(JComponent c, int w, int h, Path path) {
        c.setSize(w, h); layout(c);
        BufferedImage image = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics(); c.printAll(g); g.dispose();
        try { ImageIO.write(image, "png", path.toFile()); } catch (java.io.IOException ex) { throw new RuntimeException(ex); }
    }
}
