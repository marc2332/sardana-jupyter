from typing import List
from IPython.core.interactiveshell import InteractiveShell
from IPython.display import display
from sardana.macroserver.macroserver import MacroServer
from sardana.spock.ipython_01_00.genutils import expose_magic, from_name_to_tango
from ipykernel.comm import Comm
from sardana.taurus.core.tango.sardana.macro import MacroInfo
from sardana.taurus.core.tango.sardana.sardana import Door
from traitlets.config.application import get_config
import ipywidgets as widgets
import yaml
import logging
import os

logger = logging.getLogger()

def getElementNamesWithInterface(elements, searching_interface):
    """
    Find all the elements that include an specific interface 

    Implementation of https://sardana-controls.org/_modules/sardana/taurus/core/tango/sardana/macroserver.html#BaseMacroServer.getElementNamesWithInterface
    """
    found = []
    for element in elements:
        if searching_interface in element['interfaces']:
            found.append(element['name'])
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
        Create a new configuration by reading from the YAML file specified in the SARDANA_JUPYTER_CONF environment variable
        """
        path = os.getenv('SARDANA_JUPYTER_CONF')
        file = open(path)
        file_content = file.read()
        conf = yaml.load(file_content, Loader=yaml.FullLoader)
        self = Configuration(conf)
        self.load_names()
        self.load_into_ipython()
        return self

    def load_names(self):
        """
        Setup the needed MacroServer and Door names
        """
        self.ms_full_name = '{}_ms'.format(self.conf['name'])
        self.door_full_name = '{}_door'.format(self.conf['name'])
        self.ms_tango_name = from_name_to_tango('MacroServer/{}/1'.format(self.ms_full_name))[0]
        self.door_tango_name = from_name_to_tango('Door/{}/1'.format(self.door_full_name))[0]

    def load_into_ipython(self):
        """
        Load the MacroServer and Door names into the ipython config because of some spock utils
        """
        ipython_config = get_config()
        ipython_config.Spock.macro_server_name = self.ms_tango_name
        ipython_config.Spock.door_name = self.door_tango_name

    def get_property(self, prop: str):
        """
        Easily get a propery from the configuration dictionary
        """
        return self.conf[prop]

    

class Extension:
    """
    Jupysar Extension object
    """

    ipython: InteractiveShell
    ms: MacroServer
    door: Door
    conf: Configuration
    comms: List[Comm] = []

    # Progress bar widget
    progress: widgets.FloatProgress

    def __init__(self, ipython: InteractiveShell, conf: Configuration):
        self.ipython = ipython
        self.conf = conf

        # Open a Jupyter Comm
        ipython.kernel.comm_manager.register_target('result', self.on_comm)
        logger.critical("Reopenned")

        # Create MacroServer
        self.ms = MacroServer(conf.ms_full_name, conf.ms_full_name)
        self.ms.add_listener(self.ms_handler)
        self.ms.setLogLevel(logging.CRITICAL)
        self.ms.set_macro_path([conf.get_property('macroPath')])
        self.ms.set_recorder_path([conf.get_property('recordersPath')])
        self.ms.set_pool_names(conf.get_property('poolNames'))
        self.ms.set_environment_db('/tmp/{}-jupyter-ms.properties'.format(conf.get_property('name')))

        # Create Door
        self.door = self.ms.create_door(full_name = conf.door_full_name, name = conf.door_full_name)
        self.door.add_listener(self.door_handler)      

    def send_to_comms(self, data):
        for comm in self.comms:
            comm.send(data)
        
    def on_comm(self, comm, init_msg):
        """
        Handle incomming messages from the Jupyter Comm
        """

        self.comms.append(comm)
        logger.debug("New external connection")

        """
        @comm.on_msg
        def _recv(msg):
            comm.send()
        """

    def ms_handler(self, source, type_, value):
        """
        Handle events from the MacroServer
        """
        if type_.name == 'ElementsChanged':
            self.on_elements_changed(value)

    def door_handler(self, source, type_, value):
        """
        Handle events from the Door
        """
        if type_.name == 'macrostatus':
            self.on_macro_status(value)
        elif type_.name == 'recorddata':
            self.on_record_data(value)

    def auto_complete_macro(self, zmq_shell, event):
        """
        Method called by the IPython autocompleter. It will determine values for macro arguments.
        """

        macro_name = event.command.lstrip('%')

        # Calculate parameter index
        param_idx = len(event.line.split()) - 1
        if not event.line.endswith(' '):
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
                if param['type'].lower() == 'boolean':
                    res.extend(['True', 'False'])
                else:
                    res.extend(getElementNamesWithInterface(self.ms.get_elements_info(), param['type']))
            return res

    def on_elements_changed(self,value):
        """
        Handle changed elements events on the MacroServer
        """

        elements = value['new']
        for elem_name, elem_info in elements.items():
            if 'MacroCode' in elem_info['interfaces']:
                """
                Register the macros from the MacroServer as magic commands in the iPython shell
                """
                def macro_fn(parameter_s='', name=elem_name, *args, **kwargs):
                    self.progress = widgets.FloatProgress(description='Progress:', bar_style='info', orientation='horizontal')
                    display(self.progress)
                    try:
                        name_and_params = [name] + parameter_s.split()
                        return self.door.run_macro(name_and_params)
                    except KeyboardInterrupt:
                        self.door.macro_executor.stop()
                expose_magic(elem_name, macro_fn, self.auto_complete_macro)

    def on_macro_status(self, value):
        """
        Handle the status updates on macros
        """
        macro_status = value[0]
        min, max = macro_status['range']
        step = macro_status['step']
        # Update the progress bar widget
        self.progress.min = min
        self.progress.max = max
        self.progress.value = step


    def on_record_data(self, value):
        """
        Handle incoming data from a Recorder
        """
        fmt, data = value
        # Send the retrieved data from the recorder to the frontend extension through the comm channel
        self.send_to_comms({'data': data})


def load_ipython_extension(ipython):
    """
    Extension initialization
    """

    # Retrieve the configuration 
    conf = Configuration.from_env_var()

    # Run the extension
    Extension(ipython, conf)

    logger.critical('Launched Sardana Extension')

def unload_ipython_extension(ipython):
    pass
