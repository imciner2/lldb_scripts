# LLDB scripts
Various scripts to assist with using LLDB for debugging programs.

# Scripts

## filterevents.py

This script provides a function that can be used as a filter in ```target stop-hook``` to ignore events.
This filter operates on the file name, module name and the function name.
If any of them match the regular expression provided, then the debugger will stop at the event.
If none of them match, the debugger will ignore the event and continue one.
This is useful when debugging modules inside a larger program, since you can then ignore any events that occur outside the module of interest.

To use this filter, the script file must be imported into LLDB by running:
```
command script import filterevents.py
```

Once it is imported, a filter can be created by running:
```
script filterevents.AddFilterHook( source_file="foo" )
```
Any of the arguments can be specified as a regular expression, and they are currently OR'd together.
The possible arguments are:
```
source_file=...
module_file=...
function=...
```
