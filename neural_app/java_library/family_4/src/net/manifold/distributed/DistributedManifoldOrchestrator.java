package net.manifold.distributed;
import neural.studio.*;


import net.manifold.core.InferenceQuantum;
import net.manifold.engine.InferenceNetworkBroadcaster;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;

/** Local routing compatibility API. No remote destination is configured or contacted. */
public final class DistributedManifoldOrchestrator {
    private final InferenceNetworkBroadcaster engine;
    public DistributedManifoldOrchestrator(InferenceNetworkBroadcaster engine) {
        this.engine = Objects.requireNonNull(engine);
    }
    public CompletableFuture<Void> routeParallelQuantum(InferenceQuantum quantum) {
        return engine.submit(quantum).thenApply(result -> null);
    }
}
