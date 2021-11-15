import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICommandPalette, MainAreaWidget } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';
// @ts-ignore
import * as Plotly from 'plotly.js/dist/plotly.min.js';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { PlotConfig, TracesAxes } from './types';
import {
  IComm,
  IKernelConnection
} from '@jupyterlab/services/lib/kernel/kernel';
import { ICommMsgMsg } from '@jupyterlab/services/lib/kernel/messages';

/*
 * Easy-to-use wrapper around Jupyter Comms
 */
class Connection {
  private connection: IComm;

  constructor(
    name: string,
    kernel: IKernelConnection,
    listener: (msg: ICommMsgMsg<'iopub' | 'shell'>) => void
  ) {
    this.connection = kernel.createComm(name);
    this.connection.onMsg = listener;
    this.connection.open();
  }
}

class NotebookExtension {
  // HTML Container
  private container: HTMLElement;

  // Accumulation object for the next plot
  private currentPlot: PlotConfig = {
    validTraces: {},
    xAxe: 0,
    traces: []
  };

  constructor(app: JupyterFrontEnd, panel: NotebookPanel) {
    // Shortcut to get the current token
    const getCurrentKernel = () => panel.sessionContext.session?.kernel;

    // Create a new Jupyter Comm when the kernel is reloaded
    panel.sessionContext.kernelChanged.connect(() => {
      setTimeout(() => {
        const kernel = getCurrentKernel();

        if (kernel != null) {
          new Connection(
            'result',
            kernel,
            this.connectionMessageHandler.bind(this)
          );
        }
      }, 5000);
    });

    // Connect to the Jupyter conn running on kernel
    const kernel = getCurrentKernel();
    if (kernel != null) {
      new Connection(
        'result',
        kernel,
        this.connectionMessageHandler.bind(this)
      );
    }

    // Container
    const content = new Widget();
    content.node.style.height = '100%';
    content.node.style.width = '100%';

    // Jupyter panel
    const widget = new MainAreaWidget({ content });
    widget.id = `${Math.random()}-sardana-demo`;
    widget.title.label = 'Sardana';
    widget.title.closable = true;

    // Plot container
    const container = document.createElement('div');
    content.node.appendChild(container);
    this.container = container;

    // Add the panel (aka Tab) to the main area
    app.shell.add(widget, 'main');

    // Activate the widget
    app.shell.activateById(widget.id);
  }

  /*
   * Handle incomming messages from the comm channel
   */
  public connectionMessageHandler(msg: any) {
    const data = msg.content.data;
    try {
      switch (data.data.type) {
        case 'data_desc':
          data.data.data.column_desc.forEach((trace: any) => {
            if (trace.output === true) {
              this.currentPlot.validTraces[trace.name] = trace.label;
              this.currentPlot.traces.push(trace.label);
            }
            if (trace.is_reference) {
              if (this.currentPlot.xAxe === 0) {
                this.currentPlot.xAxe = trace.max_value;
              }
            }
          });
          this.createPlot();
          break;
        case 'record_data':
          const itemsData = data.data.data;

          const tracesData: TracesAxes = {
            y: []
          };

          Object.keys(itemsData).forEach(traceName => {
            if (this.currentPlot.validTraces[traceName]) {
              const traceValue = itemsData[traceName];
              tracesData.y.push([traceValue]);
            }
          });
          this.extendPlot(tracesData);

          break;
        case 'record_end':
          // FINISHED
          break;
      }
    } catch (e) {
      console.log(e);
    }
  }

  // Update the Plotly plot
  public extendPlot(traces: TracesAxes) {
    Plotly.extendTraces(
      this.container,
      traces,
      traces.y.map((_: any, i: number) => i)
    );
  }

  // Initialize the PlotlyPlot
  public createPlot() {
    const traces = this.currentPlot.traces;

    // Transform the data to plotly
    const data = traces.map((name: string) => {
      return {
        y: [],
        name,
        mode: 'lines+markers',
        type: 'scatter',
        line: {
          shape: 'spline'
        }
      };
    });

    // Plotly layout
    const layout = {
      title: 'Result',
      showlegend: true
    };

    // Plotly configuration
    const config = {
      scrollZoom: true
    };

    // Create the plot graphic
    Plotly.newPlot(this.container, data, layout, config);
  }
}

class Extension implements JupyterFrontEndPlugin<void> {
  public id = 'Jupysar:plugin';
  public autoStart = true;
  public optional = [
    ICommandPalette,
    ISettingRegistry,
    ILayoutRestorer,
    INotebookTracker
  ];

  // Extension init method
  public activate(
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    settingRegistry: ISettingRegistry,
    restorer: ILayoutRestorer,
    notebook: INotebookTracker
  ) {
    console.clear();

    // The extension loads
    console.log('Sardana extension is activated!');

    // When a Notebook is created
    notebook.widgetAdded.connect(async (sender: any, panel: NotebookPanel) => {
      // Wait the notebook to load
      await panel.sessionContext.ready;

      // Create a new Notebook extension for each new Notebook created
      new NotebookExtension(app, panel);
    });
  }
}

export default new Extension();
