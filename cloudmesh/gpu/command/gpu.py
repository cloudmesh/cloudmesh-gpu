import json

from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.gpu.gpu import Gpu
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.shell.command import map_parameters


class GpuCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_gpu(self, args, arguments):
        """
        ::

          Usage:
                gpu watch [--gpu=GPU] [--delay=SECONDS] [--logfile=LOGFILE] [--count=COUNT] [--dense]
                gpu --json [--gpu=GPU] [--pretty] [FILE]
                gpu --xml
                gpu --yaml
                gpu processes [--gpu=GPU] [--format=FORMAT] [--detail]
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
              --detail            short process names [default: False]
              --format=FORMAT     table, json, yaml [default: table]
              --gpu=GPUS
        """

        map_parameters(arguments,
                       "json",
                       "xml",
                       "yaml",
                       "pretty",
                       "delay",
                       "logfile",
                       "table",
                       "detail",
                       "output"
                       )
        arguments.format = arguments["--format"]
        arguments.gpu = Parameter.expand(arguments["--gpu"])

        # VERBOSE(arguments)

        def _select(d, what):
            try:
                selected = []
                data = dict(gpu.smi(output="json"))["nvidia_smi_log"]['gpu']
                selection = [int(i) for i in what]
                # selected = [data[i] for i in selection]
                # this way we can pass numbers which do not exist
                selected = []
                for i in selection:
                    try:
                        selected.append(data[i])
                    except:
                        pass
                d["nvidia_smi_log"]['gpu'] = selected
            except Exception as e:
                print(e)
            return d

        try:
            gpu = Gpu()

            if arguments.watch:

                gpu.watch(logfile=arguments.logfile,
                          delay=arguments.delay,
                          repeated=int(arguments["--count"]),
                          dense=arguments["--dense"],
                          gpu=arguments.gpu)

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
                result = _select(result, arguments.gpu)

            elif arguments.json:
                filename = arguments.FILE
                result = gpu.smi(output="json", filename=filename)
                result = _select(result, arguments.gpu)

            elif arguments.yaml:
                result = gpu.smi(output="yaml")

            elif arguments.processes:

                arguments.pretty = True
                result = gpu.processes()
                d = []
                counter = 0
                for i in result.keys():
                    if str(i) in arguments.gpu:
                        for p in result[i]:
                            counter = counter + 1
                            p["gpu"] = i
                            p["job"] = counter
                            p = dict(p)
                            if not arguments.detail:
                                p["process_name"] = p["process_name"].split()[0].strip()
                                try:
                                    p["process_name"] = p["process_name"].split("/")[-1]
                                except:
                                    pass
                            d.append(p)
                    print(Printer.write(d,
                                        output=arguments.format,
                                        order=["job", "gpu", "pid", "type", "used_memory", "compute_instance_id",
                                               "gpu_instance_id", "process_name"]))
                return ""

            elif arguments.system:
                arguments.pretty = True
                result = gpu.system()
                # result  = _select(result, arguments.gpu)

            elif arguments.status:
                arguments.pretty = True
                result = gpu.status()
                # result  = _select(result, arguments.gpu)

            elif arguments.count:
                arguments.pretty = True
                result = gpu.count

            else:
                result = gpu.smi()
                # result  = _select(result, arguments.gpu)

            try:
                if arguments.pretty:
                    # result = _select(result, arguments.gpu)
                    result = json.dumps(result, indent=2)
            except:
                result = None
        except:
            result = None

        print(result)

        return ""
