import sys
from enum import IntEnum
from IPython.core.interactiveshell import InteractiveShell
from IPython.display import display
from dash.dependencies import Input, Output
from taurus.core.util.log import Logger
from sardana.macroserver.msmetamacro import MacroClass, MacroFunction
from sardana.macroserver.macroserver import MacroServer
from sardana.spock.ipython_01_00.genutils import expose_magic
from sardana.taurus.core.tango.sardana.macro import MacroInfo
from sardana.taurus.core.tango.sardana.sardana import Door, PlotType
from jupyter_dash import JupyterDash
from plotly import express
import ipywidgets as widgets
import yaml
import logging
import os
import dash_core_components as dcc
import dash_html_components as html
import uuid

Logger.disableLogOutput()
root_logger = logging.getLogger()
root_logger.handlers.clear()


def getElementNamesWithInterface(elements, searching_interface):
    """
    Find all the elements that include an specific interface

    Implementation of
    https://sardana-controls.org/_modules/sardana/taurus/core/tango/sardana/macroserver.html#BaseMacroServer.getElementNamesWithInterface
    """
    found = []
    for element in elements:
        if searching_interface in element["interfaces"]:
            found.append(element["name"])
    return found


class Configuration:
    """
    JupySar Configuration object
    """

    conf: dict
    ms_full_name: str
    door_full_name: str

    # Used for tango
    ms_tango_name: str
    door_tango_name: str

    def __init__(self, conf: dict):
        self.conf = conf

    def from_env_var():
        """
        Create a new configuration by reading from the YAML file specified
        in the SARDANA_JUPYTER_CONF environment variable
        """
        path = os.getenv("SARDANA_JUPYTER_CONF")
        if path is not None:
            file_ = open(path)
            file_content = file_.read()
            conf = yaml.load(file_content, Loader=yaml.FullLoader)
        else:
            conf = {"name": "dummy"}
        self = Configuration(conf)
        self.load_names()
        return self

    def load_names(self):
        """
        Setup the needed MacroServer and Door names
        """
        self.ms_full_name = "{}_ms".format(self.conf["name"])
        self.door_full_name = "{}_door".format(self.conf["name"])

    def get_property(self, prop: str, dft: object = None):
        """
        Easily get a propery from the configuration dictionary
        """
        return self.conf.get(prop, dft)


class ShowscanState(IntEnum):

    Plot = 1
    LastPlotPending = 2
    Done = 3


class Extension:
    """
    Jupysar Extension object
    """

    ipython: InteractiveShell
    ms: MacroServer
    door: Door
    conf: Configuration
    app: JupyterDash
    plotConf = {}

    # Progress bar widget
    progress: widgets.FloatProgress

    def __init__(self, ipython: InteractiveShell, conf: Configuration):
        self.ipython = ipython
        self.conf = conf

        # Create MacroServer
        self.ms = MacroServer(conf.ms_full_name)
        self.ms.add_listener(self.ms_handler)
        self.ms.setLogLevel(logging.INFO)
        self.ms.set_macro_path(conf.get_property("macroPath", []))
        self.ms.set_recorder_path(conf.get_property("recorderPath", []))
        self.ms.set_pool_names(conf.get_property("poolNames", []))
        self.ms.set_environment_db(
            "/tmp/{}-jupyter-ms.properties".format(conf.get_property("name"))
        )

        # Create Door
        self.door = self.ms.create_door(
            full_name=conf.door_full_name, name=conf.door_full_name
        )
        self.door.add_listener(self.door_handler)

        self.prepare_macro_logging()
        self._showscan_state = None

    def prepare_macro_logging(self):
        Logger.addLevelName(15, "OUTPUT")

        def output(loggable, msg, *args, **kw):
            loggable.getLogObj().log(Logger.Output, msg, *args, **kw)

        Logger.output = output

        self.door.getLogObj().setLevel(logging.DEBUG)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(Logger.Output)
        self.door.addLogHandler(handler)

    def ms_handler(self, source, type_, value):
        """
        Handle events from the MacroServer
        """
        if type_.name == "ElementsChanged":
            self.on_elements_changed(value)

    def door_handler(self, source, type_, value):
        """
        Handle events from the Door
        """
        if type_.name == "macrostatus":
            self.on_macro_status(value)
        elif type_.name == "recorddata":
            self.on_record_data(value)

    def auto_complete_macro(self, zmq_shell, event):
        """
        Method called by the IPython autocompleter.
        It will determine values for macro arguments.
        """

        macro_name = event.command.lstrip("%")

        # Calculate parameter index
        param_idx = len(event.line.split()) - 1
        if not event.line.endswith(" "):
            param_idx -= 1

        # Get macro info
        macro = self.ms.get_macros()[macro_name]
        info = MacroInfo(from_json=macro.serialize())

        # Get the parameters info
        possible_params = info.getPossibleParams(param_idx)

        # Return the existing elements for the given parameter type
        if possible_params:
            res = []
            for param in possible_params:
                if param["type"].lower() == "boolean":
                    res.extend(["True", "False"])
                else:
                    res.extend(
                        getElementNamesWithInterface(
                            self.ms.get_elements_info(), param["type"]
                        )
                    )
            return res

    def on_elements_changed(self, value):
        """
        Handle changed elements events on the MacroServer
        """

        elements = value["new"]
        for element in elements:
            elem_name = element.name
            if isinstance(element, (MacroClass, MacroFunction)):
                """
                Register the macros from the MacroServer as magic commands
                in the iPython shell
                """

                def macro_fn(parameter_s="", name=elem_name, *args, **kwargs):
                    self.progress = widgets.FloatProgress(
                        description="Progress:",
                        bar_style="info",
                        orientation="horizontal",
                    )
                    display(self.progress)
                    try:
                        name_and_params = [name] + parameter_s.split()
                        return self.door.run_macro(name_and_params)
                    except KeyboardInterrupt:
                        self.door.macro_executor.stop()

                # logger.info("registered: "+element.name)
                expose_magic(elem_name, macro_fn, self.auto_complete_macro)

    def on_macro_status(self, value):
        """
        Handle the status updates on macros
        """
        macro_status = value[0]
        min, max = macro_status["range"]
        step = macro_status["step"]

        # Update the progress bar widget
        self.progress.min = min
        self.progress.max = max
        self.progress.value = step

    def on_record_data(self, value):
        """
        Handle incoming data from a Recorder
        """
        fmt, data = value

        if data["type"] == "data_desc":
            """
            Run the dash server when the scan is starting
            """

            # Plot data
            self.plot = {"x": [], "y": [], "name": []}

            self._showscan_state = ShowscanState.Plot

            # Plot configuration
            self.plotConf = {
                "graph_id": "live-update-graph-" + str(uuid.uuid4()),
                "figure": None,
                "x_title": "x",
            }

            # Only allow Spectrum plots
            self.allowedTraces = {}
            for trace in data["data"]["column_desc"]:
                ptype = trace.get("plot_type", PlotType.No)
                if ptype == PlotType.No:
                    continue
                if ptype != PlotType.Spectrum:
                    continue
                x_axes = [
                    "point_nb" if axis == "<idx>" else axis
                    for axis in trace.get("plot_axes", ())
                ]
                if len(x_axes) == 0:
                    continue
                if x_axes[0] == "point_nb":
                    continue
                self.allowedTraces[trace["name"]] = trace
                self.plotConf["x_title"] = x_axes[0]

            if len(self.allowedTraces) == 0:
                return

            self.plotConf["figure"] = create_line_figure(
                self.plot, self.plotConf
            )

            # Crate the JupyterDash app
            self.app = JupyterDash(__name__)
            self.app.layout = html.Div(
                [
                    # The graph element
                    dcc.Graph(
                        self.plotConf["graph_id"],
                        figure=self.plotConf["figure"],
                    ),
                    # Interval element that triggers the render loop
                    dcc.Interval(
                        id="interval-loop",
                        interval=500,
                        n_intervals=0,
                    ),
                ]
            )

            @self.app.callback(
                [
                    Output(self.plotConf["graph_id"], "figure"),
                    Output("interval-loop", "disabled"),
                ],
                Input("interval-loop", "n_intervals"),
            )
            def render_graph(n):
                """
                A render loop binded to the interval element and
                ouputs a new figure to the graph element.
                """
                fig = create_line_figure(self.plot, self.plotConf)
                if self._showscan_state == ShowscanState.LastPlotPending:
                    self._showscan_state = ShowscanState.Done
                elif self._showscan_state == ShowscanState.Done:
                    return (fig, True)
                return (fig, False)

            self.app.run_server(mode="inline", inline_exceptions=True)

        if data["type"] == "record_data":
            """
            Update the plot data
            """
            for traceName in self.allowedTraces:
                traceValue = data["data"][traceName]
                traceData = self.allowedTraces[traceName]

                motorName = traceData["plot_axes"][0]
                motorPos = data["data"][motorName]

                self.plot["x"].append(motorPos)
                self.plot["y"].append(traceValue)
                self.plot["name"].append(traceData["label"])

        if data["type"] == "record_end":
            """
            There is no need to manually stop the server because JupyterDash
            already does it when you render a new app.
            """
            if len(self.allowedTraces) == 0:
                return

            self._showscan_state = ShowscanState.LastPlotPending
            # self.app._terminate_server_for_port(8050)


def create_line_figure(data, conf):
    """
    Shortcut to easily create a new Line figure
    """
    fig = express.line(
        data,
        x="x",
        y="y",
        markers=True,
        color="name",
        labels={"x": conf["x_title"], "y": "values", "name": "channels"},
    )

    fig.update_layout(
        clickmode="event+select",
        # Leaving this parameter with always
        # this value prevents dash from re-rendering on each update
        uirevision="empty",
    )

    return fig


def load_ipython_extension(ipython):
    """
    Extension initialization
    """

    # Retrieve the configuration
    conf = Configuration.from_env_var()

    # Run the extension
    Extension(ipython, conf)

    # root_logger.critical('Launched Sardana Extension')


def unload_ipython_extension(ipython):
    pass
