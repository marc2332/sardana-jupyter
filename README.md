# sardana-jupyter
Sardana integration into the Jupyter ecosystem.

This is still a WIP. For a list of missing features/ideas see TODO.md.

**Note**: The old plotting mechanism was made using PlotlyJS, you can see how it worked, [here](https://gitlab.com/sardana-org/sardana-jupyter/-/blob/98bb157b15857790c18edd48ee6be44ab7c967c9/sardana_jupyter_lab/src/index.ts).

## Docker demo
Create the image:
```shell
docker build --label jupysar-demo --tag jupysar-demo -f ./docker/Dockerfile .
```

Run the container:
```shell
sudo docker run -dp 8888:8888 -dp 8050:8050 --name jupysar-demo jupysar-demo
```

- Wait some seconds
- Open  [localhost:8888](http://localhost:8888) 
- Wait for a popup to come up, then select "Build"
- Wait for another popup to come, select "Save and Reload"
- Open the Notebook `/examples/example_macros.ipynib` with Sardana Kernel selected
- Follow the guide

## Manual installation

You can install the necessary dependencies using conda. 

```shell
conda env create -f environment.yml
conda activate sardana-jupyter
./scripts/setup.bash
```

## Start the Jupyter Lab

Currently the Jupyter extension only instantiate the MacroServer part. 
You can still use it on its own but it may be not so interesting...

In order to use the full Sardana system you will need to run your Pool
instance as a Tango device server and point to it in the configuration file
(see the "Configuration" section below).

Then to start the Jupter Lab you just need:

```shell
jupyter lab examples/example_macros.ipynb
```

And then select the `Sardana Kernel` Notebook.

## Configuration

sardana-jupyter can be configured using a YAML file.
The file location must be set using the `SARDANA_JUPYTER_CONF` environment variable.
You can use the example configuration file as a template.

```shell
cp ./examples/sardana-jupyter.yml $HOME/sardana-jupyter.yml
export SARDANA_JUPYTER_CONF=$HOME/sardana-jupyter.yml
```

In the file you can set the following keys:

- `name` - name of your jupyter macroserver instance e.g. `test`, `dummy`, etc.
- `poolNames` - pool(s) you would like to connect to e.g. `Pool_test_1`
- `macroPath` - path(s) to your macros e.g. `<install-dir>/sardana/macroserver/macros/examples`
- `recorderPath` = path(s) to your recorders e.g. `<install-dir>/sardana/macroserver/recorders/examples`
