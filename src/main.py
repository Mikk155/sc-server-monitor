import os;
import time;
import json;
import shlex;
import psutil;
import jsonschema;
import subprocess;
import socket;

global gpWorkingDirectory;
gpWorkingDirectory: str = os.path.dirname( os.path.abspath( __file__ ) );
global gpGameDirectory;
gpGameDirectory: str = os.path.dirname( os.path.dirname( gpWorkingDirectory ) );
global gpConfig;
gpConfig: dict = {};

def GetSchema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Sven Co-op Server Monitor Config",
        "type": "object",
        "unevaluatedProperties": False,
        "required":
        [
            "timeout",
            "max_retries",
            "check_interval",
            "servers"
        ],
        "properties":
        {
            "$schema":
            {
                "type": "string"
            },
            "timeout":
            {
                "type": "number",
                "description": "Timeout (In seconds) to wait for a response on a specific server.",
                "minimum": 1.0
            },
            "max_retries":
            {
                "type": "integer",
                "description": "How many consecutive fails on program responses before shuting down it?",
                "minimum": 2
            },
            "check_interval":
            {
                "type": "integer",
                "description": "How much seconds to wait before checking for apps",
                "minimum": 2
            },
            "servers":
            {
                "type": "array",
                "items":
                {
                    "type": "object",
                    "unevaluatedProperties": False,
                    "required":
                    [
                        "app",
                        "port",
                        "map"
                    ],
                    "properties":
                    {
                        "app":
                        {
                            "type": "string",
                            "description": "Executable name at the location of \"../../\" from the current python script.",
                            "default": "svends.exe"
                        },
                        "port":
                        {
                            "type": "integer",
                            "description": "UDP Port for this server",
                            "minimum": 1024,
                            "maximum": 65535
                        },
                        "map":
                        {
                            "type": "string",
                            "description": "Map name to launch the server"
                        },
                        "args":
                        {
                            "type": "array",
                            "items":
                            {
                                "type": "string"
                            },
                            "description": "Additional arguments (Using +argname requires to be split into two different strings!)"
                        }
                    }
                }
            }
        }
    };

def PopSchema() -> None:
    """Write schema for user-configuration"""
    schema: dict = GetSchema();
    shouldRewrite: bool = True;
    global gpWorkingDirectory;
    schemaPath: str = os.path.join( gpWorkingDirectory, "schema.json" );
    if( os.path.exists( schemaPath ) ):
        with open( schemaPath, 'r' ) as fStream:
            try:
                curSchema = json.load( fStream );
                if curSchema == schema:
                    shouldRewrite = False;
            except:
                pass;

    if shouldRewrite is True:
        with open( schemaPath, 'w') as fStream:
            fStream.write( json.dumps( GetSchema(), indent=4 ) );
            print( "Writted schema.json for user-validations" );

def RetrieveConfig( forceLoad: bool = False ) -> bool:
    """
        Load config.json at the working directory if it changed since last time.
        forceLoad: If true it loads the config either way.
        Returns whatever the config has been propertly parsed.
    """

    global gpConfig;
    global gpWorkingDirectory;
    configFile: str = os.path.join( gpWorkingDirectory, "config.json" );

    if not os.path.exists( configFile ):
        print( f"ERROR! could not find config.json at {configFile}" );
        if forceLoad is True:
            exit(1);

    if forceLoad is False:
        with open( configFile, 'r' ) as fStream:
            try:
                curConfig = json.load( fStream );
                if curConfig == gpConfig:
                    return False;
            except:
                return False;

    with open( configFile , 'r' ) as fStream:

        jsonObject: dict = json.load( fStream );

        try:
            jsonschema.validate( instance=jsonObject, schema=GetSchema() );

            if forceLoad is False:
                print( "Updated json configuration." );

            gpConfig = jsonObject;

            return True;

        except jsonschema.ValidationError as e:
            print( f"ERROR! invalid config.json {e.json_path} {e.message}" );

            if forceLoad is True:
                exit(1);

            return False;

    return False;

def ServerCanResponse( port: int ) -> bool:
    """
        Send a A2S_INFO ping to server to check it's not on a loop
    """

    A2S_INFO = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00';
    client = socket.socket( socket.AF_INET, socket.SOCK_DGRAM );
    global gpConfig;
    client.settimeout( gpConfig[ "timeout" ] );

    try:
        client.sendto( A2S_INFO, ( "127.0.0.1", port ) );
        data, _ = client.recvfrom( 4096 );
        return ( len( data ) > 0 );
    except ( socket.timeout, ConnectionResetError ):
        return False;
    finally:
        client.close();
    return False;

def ServerShutdown( proc ) -> None:
    """
        Shut down proccess
    """
    if proc and psutil.pid_exists( proc.pid ):
        try:
            process = psutil.Process( proc.pid )
            for child in process.children( recursive=True ):
                child.kill();
            process.kill();
            process.wait( timeout=2 );
        except ( psutil.NoSuchProcess, psutil.TimeoutExpired ):
            pass;

def ServerStart( server_obj: dict ) -> subprocess.Popen[bytes]:
    """
        Launch server using the given config
    """

    appName: str = server_obj[ "app" ];
    global gpGameDirectory;
    appPath: str = os.path.join( gpGameDirectory, appName );

    port: int = server_obj[ "port" ];
    startMap: str = server_obj[ "map" ];

    commandArguments: list[str] = [ appPath, "-port", str( port ), "+map", startMap ];
    additionalArguments: list[str] = server_obj.get( "args", [] );

    for arg in additionalArguments:
        cleanArgument: str = arg.replace( '"', '' )
        commandArguments.extend( shlex.split( cleanArgument ) );
    
    # Título personalizado enfocado exclusivamente en el puerto -TODO
    titulo_ventana = f"Port {port}"
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.lpTitle = titulo_ventana

    return subprocess.Popen(
        commandArguments, 
        cwd=gpGameDirectory,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        startupinfo=startup_info
    );

gpServersData: list[dict] = [];

def ParseServersConfig( config: list[dict] ) -> None:

    for i, o in enumerate( config ):

        if i >= len(gpServersData):
            gpServersData.append({});

        curConfig: dict = gpServersData[i];
        curConfig[ "config" ] = o;
        curConfig[ "port" ] = o[ "port" ];
        curConfig[ "fails" ] = curConfig.get( "fails", 0 );
        curConfig[ "proc" ] = curConfig.get( "proc", None );

        # -TODO Is this necesary? Isn't curConfig a reference?
        gpServersData[i] = curConfig;

def main() -> None:

    global gpGameDirectory;
    print( "==================================================" );
    print( " Sven Co-op Server Monitor Active" );
    print( f" Game Directory (CWD): {gpGameDirectory}" );
    print( "==================================================" );

    PopSchema();
    RetrieveConfig( True );
    global gpConfig;
    ParseServersConfig( gpConfig[ "servers" ] );

    try:

        while True:

            for config in gpServersData:

                port: int = config[ "port" ];
                proc: subprocess.Popen[bytes] = config[ "proc" ];

                if proc is None or proc.poll() is not None:

                    if proc is not None:
                        print( f"[CRASH] Server on port {port} closed unexpectedly. Restarting..." );

                    else:
                        print( f"[START] Launching server on port {port}..." );

                    config[ "proc" ] = ServerStart( config[ "config" ] );
                    config[ "fails" ] = 0;

                    continue;

                if ServerCanResponse( port ):

                    config[ "fails" ] = 0

                else:

                    fails: int = config[ "fails" ] + 1;
                    config[ "fails" ] = fails;

                    maxRetries: int = gpConfig[ "max_retries" ];

                    print( f"[WARN] Server on port {port} is not responding ({fails}/{maxRetries})" );

                    if fails >= maxRetries:
                        print( f"[FREEZE] Port {port} hung up due to script loop. Forcing termination..." );
                        ServerShutdown( proc );
                        config[ "proc" ] = ServerStart( config[ "config" ] );
                        config[ "fails" ] = 0

            if RetrieveConfig():
                ParseServersConfig( gpConfig[ "servers" ] );

            time.sleep( gpConfig[ "check_interval" ] );

    except KeyboardInterrupt:

        print( "\nStopping monitor. Terminating all active game servers..." );

        for s in gpServersData:
            ServerShutdown( s[ "proc" ] );

if __name__ == "__main__":
    main();
