# Rules for AI Code assistant

## Documentation

Use [Nextmv python SDK][nextmv-py].
Use Nextmv [documentation][nextmv-docs].
Use [Ruff][ruff] for linting rules.

## Visualization

Only use plotly, geoJSON, or chartJS to create visuals.
Make any geoJSON compatible with Leaflet.
Make any geoJSON properties use metadata as shown in [Nextmv documentation][nextmv-docs-custom-viz].
Store visuals in Nextmv Assets.
Add assets to the nextmv.Output.

[nextmv-docs]: https://nextmv.io/docs
[nextmv-py]: https://github.com/nextmv-io/nextmv-py
[nextmv-docs-custom-viz]: https://nextmv.io/docs/using-nextmv/run/custom-visualization
[ruff]: https://docs.astral.sh/ruff/
