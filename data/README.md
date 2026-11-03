# COMP9414 assignment 1: Term 3 data

Extract `assignment1_data_t3.zip` and place the `data` folder next to
`zID_assignment1.ipynb`.

## Graph files

- `graphs/workshop.json`: the Part A workshop map.
- `graphs/routes.json`: a larger map for Parts B and C.
- `graphs/detour.json`: the workshop map with the ramp-lift connection closed.

Each graph has `nodes`, `edges`, `start`, and `goal`. Edges are undirected.
Coordinates and positive edge costs use the same distance units.

## Planning files

- `planning/service.json`: two units require servicing and testing.
- `planning/ready.json`: the camera starts serviced but still needs testing.
- `planning/offline.json`: the tool reset action is unavailable.

Each planning file has `initial`, `goal`, and `actions`. Each action has a
unique `name`, `preconditions`, `add`, and `delete`. Facts and action names are
strings. All actions are already grounded: use the strings directly without
parsing their arguments. The assignment describes the transition rule.

You can load all files with Python's standard-library `json` module. You do
not need `ai9414` to use these files. `manifest.json` records their provenance.

Use the Term 3 specification with this data pack.
