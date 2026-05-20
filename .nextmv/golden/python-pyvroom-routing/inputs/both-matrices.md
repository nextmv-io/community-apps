# both-matrices

A minimal test input with both a duration matrix and a distance matrix. Uses
the same 1-vehicle, 3-stop geometry as the other tests. The duration matrix
encodes a fast highway path north (start → stop-1 → stop-2) with stop-3 as a
cheap last-leg detour, yielding a unique optimal route of start → stop-1 →
stop-2 → stop-3 → end (cost 450, >500% margin). This is the opposite order
from the distance-matrix test, demonstrating that the duration matrix takes
precedence when both are provided.
