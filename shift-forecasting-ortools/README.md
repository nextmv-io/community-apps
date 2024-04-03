# Shift Forecasting

This app forecasts demands to be used for shift planning.

## Usage

Locally:

```bash
python3 main.py -input input.json -output output.json -duration 30
```

Remotely:

```bash
nextmv app create -a shift-forecasting -n "Shift Forecasting" -d "Forecasts demands for shift planning."
nextmv app push -a shift-forecasting
nextmv app run -a shift-forecasting -i input.json -w
```
