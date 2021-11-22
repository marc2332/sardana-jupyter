# sardana-jupyter
Sardana integration into the Jupyter ecosystem.

This is still a WIP. For a list of missing features/ideas see TODO.md.

## Docker demo
Create the image:
```shell
docker build --label jupysar-demo --tag jupysar-demo -f ./docker/Dockerfile .
```

Run the container:
```shell
sudo docker run -dp 8888:8888 --name jupysar-demo jupysar-demo
```

Wait some seconds, open  [localhost:8888](http://localhost:8888) and select the `Sardana Kernel` Notebook.

## Manual installation

You can install the necessary dependencies using conda. 
Prior to that, edit the `environment.yml` file to point to your
local taurus and sardana clones.

```shell
conda env create -f environment.yml

conda activate sardana-jupyter

./scripts/setup.bash
```

**IMPORTANT**: sardana requires features available in the reszelaz/jupyter-ms branch

## Start the Jupyter Lab

Currently the jupyter extension only instantiate the MacroServer part.
You will need to start your Pool instance as Tango device server and configure the following
configuration variables in your `sardana-jupyter.yml`:

```shell
cp ./examples/sardana-jupyter.yml $HOME/sardana-jupyter.yml
export SARDANA_JUPYTER_CONF=$HOME/sardana-jupyter.yml
```

- name - name of your jupyter macroserver instance e.g. "test", "dummy", etc.
- poolNames = pool(s) you would like to connect to e.g. ["Pool_test_1"]
- macroPath = - path(s) to your macros e.g. ["<path-to-sardana-clone>/src/sardana/macroserver/macros/examples"]
- recordersPath = path(s) to your recorders e.g. ["<path-to-sardana-clone>/src/sardana/macroserver/recorders/examples"]

```shell
jupyter lab examples/example_macros.ipynb
```

And then select the `Sardana Kernel` Notebook.
