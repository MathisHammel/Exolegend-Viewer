# Exolegend-Viewer

This is a simple interface created by team h25 (Gaëtan Eleouet, Mathis Hammel, Pierre Testart) for the [Exolegend 2025](https://www.exolegend.com/) competition, to visualize and debug robots in the arena based on gladiator logs.

![Example run of the player](example.mp4)

Everything is written in Python using pygame, and should be straightforward to run:

```bash
pip install pygame
python viz.py
```

The robot needs to log information in a specific format in each loop iteration. No documentation yet , read the source code and example file to understand the format 😇