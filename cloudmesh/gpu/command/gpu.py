import json

from cloudmesh.shell.command import command
from cloudmesh.shell.command import PluginCommand
from cloudmesh.gpu.gpu import Gpu
from pprint import pprint
from cloudmesh.common.debug import VERBOSE
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
                gpu --json [--pretty] [-o FILE]
                gpu --xml [-o FILE]
                gpu --yaml [-o FILE]
                gpu processes
                gpu system
                gpu status
                gpu info
                gpu [-o FILE]



          This command does some useful things.

          Arguments:
              FILE   a file name

          Options:
              -o      specify a file to place the output in

        """

        map_parameters(arguments,
                       "json",
                       "xml",
                       "yaml",
                       "pretty")

        gpu = Gpu()

        if arguments.info:
            result = "LLLL"

        elif arguments.xml:
            result = gpu.smi(output="xml")

        elif arguments.json and arguments.pertty:
            result = gpu.smi(output="json")

        elif arguments.json:
            result = gpu.smi(output="json")

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

        else:
            result = gpu.smi()

        if arguments["-o"]:
            raise NotImplementedError
        else:
            if arguments.pretty:
                result = json.dumps(result, indent=2)
            print(result)

        return ""
