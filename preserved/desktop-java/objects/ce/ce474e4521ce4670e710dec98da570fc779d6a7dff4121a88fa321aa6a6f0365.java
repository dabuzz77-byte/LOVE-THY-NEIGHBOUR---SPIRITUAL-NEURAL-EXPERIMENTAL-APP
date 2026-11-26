    // ==========================================
    // RENDER SUBSYSTEM: TWO-DIMENSIONAL GRAPHICAL FRAMEWORK
    // ==========================================
    class TacticalResonanceCanvas extends JPanel {
        
        public TacticalResonanceCanvas() {
            setBackground(new Color(18, 15, 12));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int width = getWidth();
            int height = getHeight();

            drawGeometricGridParchment(g2d, width, height);
            drawSchumannWaveform(g2d, width, height);
            drawSubcomponentNodes(g2d, width);
        }

        private void drawGeometricGridParchment(Graphics2D g2d, int w, int h) {
            g2d.setColor(new Color(139, 115, 85, 30));
            for (int i = 0; i < w; i += 60) g2d.drawLine(i, 0, i, h);
            for (int j = 0; j < h; j += 60) g2d.drawLine(0, j, w, j);
            
            // Concentric Constellation Framing (Grounding flow)
            g2d.setColor(new Color(212, 175, 55, 20));
            g2d.drawOval(w / 4, h / 6, w / 2, h / 2);
        }

        private void drawSchumannWaveform(Graphics2D g2d, int w, int h) {
            g2d.setColor(new Color(218, 165, 32, 180));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("// SCHUMANN CARRIER WAVE HARMONIC SPECTRUM (7.83 HZ BALANCED BASE)", 40, 45);
            
            double[] amplitudes = waveCore.getHarmonicAmplitudes();
            int elementStep = Math.max(4, (w / 3) / amplitudes.length);
            
            for (int i = 0; i < Math.min(amplitudes.length, 64); i++) {
                int computedBarHeight = (int) (amplitudes[i] * 380);
                
                // Translucent glow layers
                g2d.setColor(new Color(184, 115, 51, 130)); // Copper sheen
                g2d.fillRect(40 + (i * (elementStep + 4)), 280 - computedBarHeight, elementStep, computedBarHeight);
                g2d.setColor(new Color(255, 215, 0, 210)); // Gold crest line
                g2d.fillRect(40 + (i * (elementStep + 4)), 280 - computedBarHeight, elementStep, 2);
            }
        }

        private void drawSubcomponentNodes(Graphics2D g2d, int w) {
            g2d.setColor(new Color(244, 164, 96));
            g2d.setFont(new Font("Monospaced", Font.BOLD, 12));
            g2d.drawString("// AETHERIC RIFLE INTEGRATED MECHANISMS (LOCK CONFIGURATION)", w - 480, 45);
            
            List<AetherNode> trackingNodes = cognitionLoop.getHardwareNodes();
            long currentTime = System.currentTimeMillis();
            
            for (int i = 0; i < trackingNodes.size(); i++) {
                AetherNode currentNode = trackingNodes.get(i);
                int dynamicX = w - 320 + (int)(Math.cos(i * 0.8 + currentTime * 0.0022) * 55);
                int dynamicY = 100 + (i * 52);
                
                if (i > 0) {
                    int priorX = w - 320 + (int)(Math.cos((i - 1) * 0.8 + currentTime * 0.0022) * 55);
                    int priorY = 100 + ((i - 1) * 52);
                    g2d.setColor(new Color(212, 175, 55, 80));
                    g2d.setStroke(new BasicStroke(1.2f));
                    g2d.drawLine(dynamicX, dynamicY, priorX, priorY);
                }

                // Node Emission Aura Glow
                g2d.setColor(new Color(205, 133, 63, 50));
                g2d.fillOval(dynamicX - 12, dynamicY - 12, 24, 24);
                
                g2d.setColor(new Color(218, 165, 32, 240));
                g2d.fillOval(dynamicX - 5, dynamicY - 5, 10, 10);
                
                g2d.setColor(new Color(245, 222, 179, 210));
                g2d.setFont(new Font("SansSerif", Font.PLAIN, 11));
                g2d.drawString(currentNode.subcomponentName + " -> " + String.format("%.2f%% Lock", currentNode.resonanceLock * 100), dynamicX + 20, dynamicY + 4);
            }
        }
    }
