# max-duration

A minimal test input with a max_duration constraint and a speed_factor. Uses
the same 1-vehicle, 3-stop geometry and duration matrix as both-matrices. The
max_duration=400 limit (applied after speed_factor=1.1 scaling) makes serving
all 3 stops infeasible (effective cost 409 > 400), forcing stop-3 to be
unplanned. The 2-stop route (start → stop-1 → stop-2 → end) has an effective
cost of 187, well within the limit and with >145% margin over the next-best
2-stop alternative.
