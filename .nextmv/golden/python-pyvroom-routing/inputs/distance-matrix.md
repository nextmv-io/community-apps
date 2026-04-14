# distance-matrix

A minimal test input with an explicit distance matrix. Uses the same 1-vehicle,
3-stop geometry as no-matrix (stop-3 is an east detour off the main north-south
path), producing a single uniquely optimal route (start → stop-1 → stop-3 →
stop-2 → end) with a ~26% cost margin over the next-best alternative. This
differs from the no-matrix route order because the distance matrix encodes
asymmetric road costs rather than straight-line Haversine distances.
