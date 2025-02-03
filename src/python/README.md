# Python!

This directory collects everything you need to run, and hack on, a
Pythonized version of OpenTTD.

## Rationale

Python is a lot more fun to write than Squirrel.

Also, we spent some effort to keep typing to a minimum without sacrififing
expressiveness and clarity.

## Implementation details

The low-level Python interface is auto-generated.

Above that, there are Python modules that roughly correspond to the
existing Squirrel categories ("sign", "road"). We use objects that wrap
every ID from OpenTTD; many of them currently behave like integers at the
moment, but you shouldn't depend on that.

The Python mainloop is written using "anyio". Individual AIs or game
scripts may or may not run in a subthread. The `openttd._main._async`
contextvar is used to distinguish between modes so that the same calls work
in both; just liberally sprinkle "async" and "await" on your code.

##

# Contributions

… are more than welcome.


## Development

Main development happens on top of the current mainline release.

JRGPP support doesn't yet exist but is planned.

The Python system must not change the core game logic, and it really
shouldn't change anything that would cause incompatibilities with network
games.

Changes to the core game's code should be kept to a minimum and be
submitted to upstream if possible. The intent is to be able to port the
Python part to any more-or-less-recent stock (or JRGPP) OpenTTD release.


## TODO list

### Immediate

Find and fix bugs.

Add more data types.

Add more tests and regression checks.

Start and configure the Python subsystem via OpenTTD dialogs.
(After figuring out how to do that non-intrusively.)

Support configuration via savegames.


### Future

Where do we get OpenTTD Python modules from - Bananas? PyPI?

Add an internal channel for game script and AIs to message each other.

Figure out what to do about installation on Mac and/or Windows.

Add one of the remote Python debuggers.


### Possibilities

Add a queue for fine-grained observables (vehicle arrives at / wants to
depart from station, vehicle breaks down, payment …) that allow an AI to do
its own schedule management, train redirection to depots, or a game script
to control prices directly, etc.

Add a JSON API server that can interacts with the game and/or game script
and/or the AI(s).


# Authors

Matthias Urlichs <matthias@urlichs.de>

