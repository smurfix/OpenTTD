# OpenTTD and Python

This version of OpenTTD contains experimental Python bindings.


## Rationale

Yes, we already have a script language. However, Squirrel has a bunch of limitations.

* It's single-tasked. Doing more than one thing at the time is difficult,
  sometimes impossible.

* There's no way for a game engine and AIs to exchange data.
  Posting signs somewhere and encoding messages in their text doesn't
  really count, sorry.

* There is no support for running an AI on a network client. Also, you
  can't run more than one AI per company.

* The Squirrel version in OpenTTD is quite old and cannot be updated.

* Debugging Python scripts is a lot easier: using a separate thread allows
  the game engine to continue running.

* Finally, Python code is more expressive and readable than Squirrel.
  We want to make scripting and extending OpenTTD more approachable.


## So how does it work?

When OpenTTD starts, it forks a thread that runs an embedded Python interpreter.

The interpreter uses the same back-end interface as game/AI scripts (it's
auto-generated), though the high-level view looks somewhat different.

Actual commands (like "build a station") are queued up and handled at the
next game tick, at the same time the traditional scripts run. Thus, despite
running in a separate thread, Python code doesn't have an unfair speed
advantage. It also cannot cause de-syncs.


### Inter-Script Multitasking

Within Python we use the "anyio" package for cooperative, structured
multitasking. ("Structured" means that you can't just fire off a subtask and
not wait for it, for much the same reasons modern languages no longer have
a "goto" statement.)

Simple scripts run in a subthread (they *must* check periodically whether
they need to stop). If things get more complicated (your AI wants to
schedule a backgroud task, a game script wants to do several things in
parallel) writing an async scheduler is not difficult; "anyio" is
well-documented.


# Building

Install at least version 3.30 of CMake.
(Patches to bring this back down gladly accepted.)

Install Python, including its development package.

Run `git submodule update --init --recursive`.

Run `cmake` as usual. The line `-- Found: Python 3.12.8 with nanobind`
should be printed right at the top.

Everything else is unchanged.

# Usage

There is a rudimentary "Python Scripts" window (accessible under "Help").

The console gained a new "py" command. Use "py" and "py help" for details.

There are example scripts in "src/python/openttd/\_test/".

Use "PYTHONPATH=src/python pydoc openttd" (or "openttd/tile" or …) for
details.


## Supporting objects

Our supporting objects and classes are not available automagically. You
need to import them.  The easiest way is "from openttd._ import *".


### Tiles

* Tile(x,y)

  A Tile encodes a map location, with x/y coordinates.

  You can add/subtract an `(x,y)` tuple to get to another tile, or subtract
  two tiles to get their `(x,y)` distances.

  `tile\_a % tile\_b` returns the direction from A to B, thus `tile_c =
  tile_a + (tile_a % tile_b)` gets you one step closer to B. The direction
  does include diagonals and takes the diagonal direction first; if you
  don't want that, use `tile_a.step_to(tile_b)` for fine(r) control.

  Tiles have a rich set of fairly-obviously-named attributes and methods;
  for example, `is_station` is a flag whether there's a station on the
  tile, while `station` returns the actual station (or raises an exception
  if there isn't one).

* Dir

  The type for directions. It has the compass directions as attributes.

* DirJump

  A direction plus the distance to travel. A DirJump has a `jump` attribute
  that defaults to True (but not when you subtract two tiles), which helps
  with path construction.

* Turn

  A change of direction.

* TilePath(T,D)

  A TilePath encodes a location and remembers plus where you came from.

  This is obviously important for neighbor discovery: a train track that
  arrives from South is very different from one that arrives from
  NorthWest.

  Comparing a Tile to a TileDir ignores the direction.

  Steps in a TilePath have a "jump" attribute that's true when the step in
  question is a tunnel or bridge, for subsequent path construction.

  TODO: Diagonal TilePath elements (for rails) need an attribute on which
  side of the tile they currently are.

You can do basic "obvious" math: A tile plus a direction is another tile. A
Tile plus a DirStep starts a TilePath (which you can also construct
manually) which you can prolong with follow-up additions of Dir, DirStep,
or Turn elements. The difference of two tiles is a tuple, not a direction;
you can use `A % B` to create a single step from A to B.


### more to come


# Contributions

… are more than welcome.


## Development

Main development happens on top of the current main OpenTTD release.

Changes to the core game's code should be kept to an absolute minimum and
be submitted to upstream if possible. The intent is to be able to port the
Python part to any more-or-less-recent stock OpenTTD release.

This Python scripting does not affect the core game logic and does not
change its network protocol. Python- and non-Python games are 100%
interoperable. Our goal is not to change that.


## Internals

See `src/python.README.md`.


## TODO list

See `src/python.README.md`.


### Possibilities

Add a queue for fine-grained observables (vehicle arrives at / wants to
depart from station, vehicle breaks down, payment …) that allow an AI to do
its own schedule management, train redirection to depots, or a game script
to control prices directly, etc.

Use exceptions for in-script assertion errors (e.g. out-of-bounds tiles or
nonexistent vehicles).

Add a JSON API server that can interacts with the game and/or game script
and/or the AI(s).

… and last but not least, write fun new AIs and game scripts.


# Authors

Matthias Urlichs <matthias@urlichs.de>
