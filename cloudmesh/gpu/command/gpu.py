import json

from cloudmesh.shell.command import command
from cloudmesh.shell.command import PluginCommand
from cloudmesh.gpu.gpu import Gpu
from pprint import pprint
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.console import Console
from cloudmesh.common.Shell import Shell
from cloudmesh.shell.command import map_parameters
import xmltodict
import yaml


class GpuCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_gpu(self, args, arguments):
        """
        ::

          Usage:
                gpu watch [--delay=SECONDS] [--logfile=LOGFILE] [--count=COUNT] [--dense]
                gpu --json [--pretty] [FILE]
                gpu --xml
                gpu --yaml
                gpu processes
                gpu system
                gpu status
                gpu count
                gpu kill
                gpu

          This command returns some information about NVIDIA GPUs if your 
          system has them.

          Options:
              --json              returns the information in json
              --xml               returns the information in xml
              --yaml              returns the information in xml
              --logfile=LOGFILE   the logfile
              --count=COUNT       how many times the watch is run [default: -1]
              --dense             do not print any spaces [default: False]
        """

        VERBOSE(arguments)

        map_parameters(arguments,
                       "json",
                       "xml",
                       "yaml",
                       "pretty",
                       "delay",
                       "logfile"
                       )

        try:
            gpu = Gpu()


            if arguments.watch:

                gpu.watch(logfile=arguments.logfile,
                          delay=arguments.delay,
                          repeated=int(arguments["--count"]),
                          dense=arguments["--dense"])

                return ""

            elif arguments.kill:

                r = Shell.run('ps -ax | fgrep "cms gpu watch"').splitlines()
                for entry in r:
                    if "python" in entry:
                        pid = entry.strip().split()[0]
                        Shell.kill_pid(pid)

                return ""

            elif arguments.xml:
                try:
                    result = gpu.smi(output="xml")
                except:
                    Console.error("nvidia-smi must be installed on the system")
                    return ""

            elif arguments.json and arguments.pertty:
                filename = arguments.FILE
                result = gpu.smi(output="json", filename=filename)

            elif arguments.json:
                filename = arguments.FILE
                result = gpu.smi(output="json", filename=filename)

            elif arguments.yaml:
                result = gpu.smi(output="yaml")

            elif arguments.processes:
                arguments.pretty = True
                result = gpu.processes()

            elif arguments.system:
                arguments.pretty = True
                result = gpu.system()

            elif arguments.status:
                arguments.pretty = True
                result = gpu.status()

            elif arguments.count:
                arguments.pretty = True
                result = gpu.count

            else:
                result = gpu.smi()

            try:
                if arguments.pretty:
                    result = json.dumps(result, indent=2)
            except:
                result = None
        except:
            result = None
        print(result)

        return ""
