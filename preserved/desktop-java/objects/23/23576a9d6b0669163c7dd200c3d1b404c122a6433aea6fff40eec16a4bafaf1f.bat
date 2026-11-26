@echo off

java -XX:+UseG1GC -Xms2g -Xmx4g net.manifold.ui.ManifoldGridVisualizer --deployment=hybrid-mesh
