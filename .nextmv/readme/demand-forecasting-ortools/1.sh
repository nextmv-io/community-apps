nextmv app create -a demand-forecasting -n "Demand Forecasting" -d "Forecasts demands for shift planning."
nextmv app push -a demand-forecasting
nextmv app run -a demand-forecasting -i input.json -w
