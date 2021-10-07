# sardana-jupyter
Sardana integration into the Jupyter ecosystem

## Installation

You can install the necessary dependencies using conda. 
Prior to that, edit the `environment.yml` file to point to your
local taurus and sardana clones.

```
conda env create -f environment.yml
```

**IMPORTANT**: sardana requires features available in the reszelaz/jupyter-ms branch

## Start the Jupyter notebook

Currently the jupyter extension only instantiate the MacroServer part.
You will need to start your Pool instance as Tango device server and modify the following
configuration variables:

- INSTANCE_NAME - name of your jupyter macroserver instance e.g. "test", "dummy", etc.
- MACRO_PATH = - path(s) to your macros e.g. ["<path-to-sardana-clone>/src/sardana/macroserver/macros/examples"]
- RECORDER_PATH = path(s) to your recorders e.g. ["<path-to-sardana-clone>/src/sardana/macroserver/recorders/examples"]
- POOL_NAMES = pool(s) you would like to connect to e.g. ["Pool_test_1"]

```
conda activate sardana-jupyter
jupyter notebook --config=ipython_config.py example_macros.ipynb
```
