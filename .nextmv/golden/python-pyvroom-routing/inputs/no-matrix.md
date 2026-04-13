# no-matrix

A minimal test input with no matrix provided. The app will fall back to using
the Haversine formula to calculate the cost of travel between locations. Uses
1 vehicle with different start and end locations and 3 collinear stops, which
produces a single uniquely optimal route (start → stop-1 → stop-2 → stop-3 →
end) with a ~50% cost margin over the next-best alternative.
