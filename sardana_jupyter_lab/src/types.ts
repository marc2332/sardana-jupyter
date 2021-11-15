export interface TracesAxes {
  y: number[][];
}

export type TracesGroup = Array<string>;

export type ValidTraces = { [key: string]: string };

export interface PlotConfig {
  validTraces: ValidTraces;
  xAxe: number;
  traces: TracesGroup;
}
