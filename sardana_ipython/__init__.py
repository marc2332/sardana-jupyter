import ipywidgets as widgets
from IPython.display import display

from sardana.macroserver.macroserver import MacroServer
from sardana.spock.ipython_01_00.genutils import expose_magic
from sardana.spock.spockms import split_macro_parameters

import os
import yaml
import logging

ms = None
door = None
progress = None
output = None
logger = logging.getLogger()


def on_elements_changed(value):
    elements = value["new"]
    for elem_name, elem_info in elements.items():
        if "MacroCode" in elem_info["interfaces"]:
            def macro_fn(parameter_s='', name=elem_name, *args, **kwargs):
                global progress
                progress = widgets.FloatProgress(description='Progress:',
                                                 bar_style='info',
                                                 orientation='horizontal')
                display(progress)
                try:
                    name_and_params = [name] + parameter_s.split()
                    return door.run_macro(name_and_params)
                except KeyboardInterrupt:
                    door.macro_executor.stop()
                # macro = door.get_running_macro()
                # return macro.getResult()
            expose_magic(elem_name, macro_fn)


def ms_cb(source, type_, value):
    if type_.name == "ElementsChanged":
        on_elements_changed(value)


def on_macro_status(value):
    macro_status = value[0]
    min, max = macro_status["range"]
    step = macro_status["step"]
    progress.min = min
    progress.max = max
    progress.value = step


def on_record_data(value):
    fmt, data = value
    if data["type"] != "data_desc":
        return
    macro = door.get_running_macro()
    data_desc = data["data"]
    global output
    output = widgets.Output()
    display(output)


def door_cb(source, type_, value):
    if type_.name == "macrostatus":
        on_macro_status(value)
    elif type_.name == "recorddata":
        on_record_data(value)


def load_conf_from_file():
    """
    Retrieve the configuration 
    """
    path = os.getenv("SARDANA_JUPYTER_CONF")
    file = open(path)
    file_content = file.read()
    conf = yaml.load(file_content, Loader=yaml.FullLoader)
    print(conf)
    return conf


def load_ipython_extension(ipython):
    """
    Extension initialization
    """

    conf = load_conf_from_file()

    ms_full_name = ms_name = "{}_ms".format(conf['name'])
    door_full_name = door_name = "{}_door".format(conf['name'])

    global ms
    ms = MacroServer(ms_full_name, ms_name)
    ms.setLogLevel(logging.DEBUG)
    ms.add_listener(ms_cb)
    ms.set_macro_path([conf['macroPath']])
    ms.set_recorder_path([conf['recordersPath']])
    ms.set_pool_names(conf['poolNames'])
    ms.set_environment_db("/tmp/{}-jupyter-ms.properties".format(conf['name']))
    global door
    door = ms.create_door(full_name=door_full_name, name=door_name)
    door.add_listener(door_cb)
    logger.info("Launched Sardana Extension")


def unload_ipython_extension(ipython):
    pass
