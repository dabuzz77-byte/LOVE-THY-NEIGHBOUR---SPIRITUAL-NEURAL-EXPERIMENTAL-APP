/** A real, bounded Java workload for watching Matrix Bus. Runs for 60 seconds. */
public class Pulse {
    public static void main(String[] args) throws Exception {
        byte[] memory = new byte[32 * 1024 * 1024];
        long end = System.nanoTime() + 60_000_000_000L;
        double value = 0;
        int tick = 0;
        while (System.nanoTime() < end) {
            long duration = (tick / 12) % 2 == 0 ? 150_000_000L : 25_000_000L;
            long start = System.nanoTime();
            while (System.nanoTime() - start < duration) value += Math.sin(value + 0.1);
            memory[(int)(System.nanoTime() & (memory.length - 1))]++;
            System.out.println("Java pulse " + tick + ": " + value);
            Thread.sleep(200);
            tick++;
        }
        System.out.println("Java demo finished.");
    }
}
