import ipywidgets as widgets
from IPython.display import display

from sardana.macroserver.macroserver import MacroServer
from sardana.spock.ipython_01_00.genutils import expose_magic
from sardana.spock.spockms import split_macro_parameters

INSTANCE_NAME = "dummy"
MACRO_PATH = ["/homelocal/zreszela/workspace/sardana/src/sardana/macroserver/macros/examples"]
RECORDER_PATH = ["/homelocal/zreszela/workspace/sardana/src/sardana/macroserver/recorders/examples"]
POOL_NAMES = ["Pool_zreszela_1"]


ms = None
door = None
progress = None
output = None

def on_elements_changed(value):
    elements = value["new"]
    for elem_name, elem_info in elements.items():
        if "MacroCode" in elem_info["interfaces"]:
            def macro_fn(parameter_s='', name=elem_name, *args, **kwargs):

                params_def = ms.get_macro(name).get_parameter()
                parameters = split_macro_parameters(parameter_s, params_def)
                par_str_lst = [name]
                par_str_lst.extend(parameters)
                global progress
                progress = widgets.FloatProgress(description='Progress:',
                                                 bar_style='info',
                                                 orientation='horizontal')
                display(progress)
                try:
                    return door.run_macro(par_str_lst)
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
    progress.value=step


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


def load_ipython_extension(ipython):
    # The `ipython` argument is the currently active `InteractiveShell`
    # instance, which can be used in any way. This allows you to register
    # new magics or aliases, for example.
    ms_full_name = ms_name = "{}_ms".format(INSTANCE_NAME)
    door_full_name = door_name = "{}_door".format(INSTANCE_NAME)
    global ms
    ms = MacroServer(ms_full_name, ms_name)
    ms.add_listener(ms_cb)
    ms.set_macro_path(MACRO_PATH)
    ms.set_recorder_path(RECORDER_PATH)
    ms.set_pool_names(POOL_NAMES)
    ms.set_environment_db("/tmp/{}-jupyter-ms.properties".format(INSTANCE_NAME))
    global door
    door = ms.create_door(full_name=door_full_name, name=door_name)
    door.add_listener(door_cb)


def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass

