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

## Game commands

API requests that query OpenTTD won't delay for long (we hope; they do take
the game lock) and are executed directly.

When you use an API request that does send a command, the Python bindings
capture its parameters and return them to Python. A low-level wrapper
packs them into a message and sends them to the game thread for execution,
returning an Awaitable in async mode.

This low-level API isn't suitable for high-level scripting because (a) the
API doesn't tell us which calls may result in a command, and even those
that do might not if the parameters are wrong; (b), the result isn't
wrapped in a Python object; (c), when a call does not succeed, the Pythonic
way is to raise an exception instead of requiring a lot of "if not API():
fail()" tests.

Thus we wrap all API calls that might trigger a command in an `openttd._util.with_`
statement which takes care of these details.


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


### Testing

The Python scripting comes with a test script that can run automated
checks.

After building the openttd binary, run `env TTDPYTHONPATH=/src/openttd/src/python/ ./openttd -v null:ticks=0 -s null -m null -c ./openttd.cfg -g ../../src/python/tests/pytest.scn -Q -Y "openttd._test all"` (adjust for your sources' location).

Remove the `all` to get a list of available tests.

Remove the video driver ("-v null:…") to watch the test run. ;-)


### Debugging

The standard OpenTTD debug levels include a setting for Python. Please
don't go overboard adding new debug statements, as they do incur some
runtime cost.

You can add `breakpoint()` statements. Be aware that Python runs in
separate threads; two concurrent breaks in different threads can happen and
*will* mess up your debug session.

You can call API functions from the debugger in sync mode.


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

