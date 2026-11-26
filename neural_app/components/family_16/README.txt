UNIFIED NEURAL ENGINE

Start the app:
    python unified_graphical_engine.py

Requirements: Python 3.9 or newer with Tkinter (included with the normal Windows
Python installation). No pip packages, downloads, accounts or internet needed.

The app starts training automatically. Cyan and pink signals show actual neuron
activations and learned connection weights. Moving dots illustrate signal flow.

CONTROLS
- Pause / Resume: stop or continue training. Space also toggles; Esc pauses.
- Step: pause and process one training batch of 24 examples.
- Learning task: XOR, Circle or Wave. Changing it resets the network.
- Hidden layers: choose Compact, Balanced or Wide. This resets the network.
- Learning rate: controls the size of weight updates.
- Training speed: sets batches per animation frame.
- Click a neuron to see its activation, bias and incoming connection count.
- Click or drag the decision map, or use the X/Y sliders, to probe an input.
- Follow live samples: automatically moves the probe while training.
- Reset network: restores initial weights and clears the learning curve.
- Save / Open session: stores weights, biases, optimizer momentum, update count,
  dataset and learning rate in JSON. Loading starts paused with a fresh chart.
- Ctrl+S saves; Ctrl+O opens. Scroll the control panel on smaller screens.

READING THE DISPLAY
Training loss is binary cross entropy on 224 training examples. Validation
accuracy is measured on a separate set of 96 examples. The decision map colours
show predicted class probabilities; sample dots show their true class labels.
This is a local educational neural network trained on synthetic examples.

OPTIONAL COMMANDS
    python unified_graphical_engine.py --console
    python unified_graphical_engine.py --self-test
    python unified_graphical_engine.py --smoke-test

REPAIRS AND VALIDATION
Fixed the original unterminated print string. The original text matrix remains
available through --console, with dimension validation and protected borders.
Six deterministic core tests pass, including gradient checking, learning on all
three datasets, save/reload continuation and rejection of invalid parameters.
Desktop interaction checks cover pause, step, probe, neuron selection, session
save/load, invalid-file recovery, dataset/topology changes and resizing.
