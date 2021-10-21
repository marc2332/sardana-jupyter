# sardana-jupyter
Sardana integration into the Jupyter ecosystem.

This is still a WIP. For a list of missing features/ideas see TODO.md.

## Installation

You can install the necessary dependencies using conda. 
Prior to that, edit the `environment.yml` file to point to your
local taurus and sardana clones.

```
conda env create -f environment.yml

conda activate sardana-jupyter

./scripts/setup.bash
```

**IMPORTANT**: sardana requires features available in the reszelaz/jupyter-ms branch

## Start the Jupyter notebook

Currently the jupyter extension only instantiate the MacroServer part.
You will need to start your Pool instance as Tango device server and configure the following
configuration variables in your `sardana-jupyter.yml`:

```
cp ./examples/sardana-jupyter.yml $HOME/sardana-jupyter.yml
export SARDANA_JUPYTER_CONF = $HOME/sardana-jupyter.yml
```

- name - name of your jupyter macroserver instance e.g. "test", "dummy", etc.
- poolNames = pool(s) you would like to connect to e.g. ["Pool_test_1"]
- macroPath = - path(s) to your macros e.g. ["<path-to-sardana-clone>/src/sardana/macroserver/macros/examples"]
- recordersPath = path(s) to your recorders e.g. ["<path-to-sardana-clone>/src/sardana/macroserver/recorders/examples"]

```
jupyter notebook examples/example_macros.ipynb  --NotebookApp.kernel_manager_class=notebook.services.kernels.kernelmanager.AsyncMappingKernelManager

```

And then select the Sardana Kernel.
