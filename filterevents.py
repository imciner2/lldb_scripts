'''
This file contains the functions needed to perform stop filtering in LLDB.
This filtering will only allow the target to stop execution if one of the criteria
(filename matching, module name matching, function name matching) is satisfied.

To use this script, it must first be imported to LLDB using this command:
command script import filterevents.py

Once it is imported, the filters can be added using the AddStopHookFilter function.
This function takes the filters as arguments, and currently performs an OR across
all three.
An example filter to only stop the target if the source file contains "foo" anywhere
in its name or path is:
script filterevents.AddFilterHook( source_file="foo" )

:author Ian McInerney
:license MIT
'''
import argparse
import lldb
import re
import shlex


def AddStopHookFilter( source_file=None, module_file=None, function=None ):
    '''
    Add a stop hook to the current target that filters stop events using the provided criteria.
    If any of the regular expressions match, then the debugger stops. If none match, the debugger
    continues and ignore the event.

    :param source_file: regular expression to match against the source filename/path
    :param module_file: regular expression to match against the compiled executable name
    :param function: regular expression to match against the function name
    '''

    # Create the arguments for the filter function
    filterArgs = ""
    if source_file != None:
        filterArgs = filterArgs + "--source-file " + "\"" + source_file + "\""

    if module_file != None:
        filterArgs = filterArgs + "--module-file " + "\"" + module_file + "\""

    if function != None:
        filterArgs = filterArgs + "--function " + "\"" + function + "\""

    # Add the python script and the hook to the LLDB session
    res = lldb.SBCommandReturnObject()
    lldb.debugger.GetCommandInterpreter().HandleCommand( "target stop-hook add -o \"FilterEventStopHook " + filterArgs + " \" ", res  )


def FilterEventStopHook( debugger, command, result, dict ):
    '''
    Command function that parses the current target information to see if the criteria are met
    to stop the debugger or continue it.

    This function takes several command line arguments to determine the criteria:
    --source-file  - Regular expression to match against the source file name/path
    --module-file  - Regular expression to match against the module file name/path
    --function     - Regular expression to match against the function name
    '''

    parser = argparse.ArgumentParser( "Only stop the debugger when criteria are met" )

    parser.add_argument( '--source-file', dest='srcFile',
                         type=str, default=None,
                         action='store',
                         help='Only show events that occur inside this source file/path' )
    parser.add_argument( '--module-file', dest='modFile',
                         type=str, default=None,
                         action='store',
                         help='Only show events that occur inside this compiled file/path' )
    parser.add_argument( '--function', dest='function',
                         type=str, default=None,
                         action='store',
                         help='Only show events that occur inside this function' )

    argList = shlex.split( command )
    args = parser.parse_args( argList )

    process = lldb.debugger.GetSelectedTarget().process
    
    # Get the frame from the running thread
    frame = None
    for thread in process:
        if thread.GetStopReason() != lldb.eStopReasonNone and thread.GetStopReason() != lldb.eStopReasonInvalid:
            frame = thread.GetFrameAtIndex( 0 )
            break

    # When the target starts the first time, this could happen
    if frame == None:
        return

    # Extract information about the place that triggered the stop
    lineNum     = None
    funcName    = None
    srcFileName = None
    modFileName = None

    mod = frame.GetModule()
    if mod != None:
        modFileSpec = mod.GetFileSpec()
        if modFileSpec != None:
            modFileName = modFileSpec.__get_fullpath__()

    func = frame.GetFunction()
    if func != None:
        funcName = func.GetDisplayName()

    lineEntry = frame.GetLineEntry()
    if lineEntry != None:
        lineNum = lineEntry.GetLine()
    
        srcFileSpec = lineEntry.GetFileSpec();
        if srcFileSpec != None:
            srcFileName = srcFileSpec.__get_fullpath__()

    # Parse the filters
    allowEvent = False
    if args.function != None and funcName != None:
        funcMatch = re.search( args.function, funcName )
        if funcMatch:
            print( "Stopping due to function name match" )
            allowEvent = True;

    if args.modFile != None and modFileName != None:
        modMatch = re.search( args.modFile, modFileName )
        if modMatch:
            print( "Stopping due to module name match" )
            allowEvent = True;

    if args.srcFile != None and srcFileName != None:
        srcMatch = re.search( args.srcFile, srcFileName )
        if srcMatch:
            print( "Stopping due to source file name match" )
            allowEvent = True;
        

    if not allowEvent:
        # The continue command must be called when async is true
        # otherwise it will wait for the command to return
        asyncStatus = lldb.debugger.GetAsync()
        lldb.debugger.SetAsync( True )
        process.Continue()
        lldb.debugger.SetAsync( asyncStatus )



def __lldb_init_module(debugger, *rest):
    # Add the filter command to LLDB
    res = lldb.SBCommandReturnObject()
    lldb.debugger.GetCommandInterpreter().HandleCommand( "command script add -f filterevents.FilterEventStopHook FilterEventStopHook", res )
