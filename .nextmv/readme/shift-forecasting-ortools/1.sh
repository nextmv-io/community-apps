nextmv app create -a shift-forecasting -n "Shift Forecasting" -d "Forecasts demands for shift planning."
nextmv app push -a shift-forecasting
nextmv app run -a shift-forecasting -i input.json -w