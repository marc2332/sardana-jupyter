# General

- [x] Configuration parameters loaded from a file
- [ ] Stop the MacroServer execution when the extension unloads (inspired by tango door device's delete_device() method )
- [ ] How to present to the user the macro exception details (equivalent to Spock's `www`)
- [ ] Unit tests + CI
- [x] Integrate flake8 and black via pre-commit and in the CI

# Macro execution

- [x] Macros with string parameters can not be started e.g. senv
- [ ] Show macro result
- [x] Do not log all logger messages e.g. GScan messages during scan execution
- [x] Macro parameters tab completion
- [ ] Interactive macros (macro input)
- [ ] Macros that execute other macros might interfere with the parent macro's progress bar (e.g sar_demo)

# GUI

- [x] Showscan online plotting

# Docker
- [ ] Automatically rebuild JupyterLab (See [this](https://github.com/plotly/jupyter-dash#jupyterlab-support))