"""
Gpu Class Module

This module defines the `Gpu` class, providing functionality to probe, monitor, and analyze GPU information
using nvidia-smi. It includes methods for probing GPU details, reading event logs, analyzing energy data,
generating graphs, and continuous monitoring of GPU status.

Attributes:
    N/A

Methods:
    - probe(): Probe GPU information and display relevant details.
    - fix_date_format(df, col): Fix date format in the given DataFrame column.
    - read_eventlog(filename): Read GPU event log from the specified file.
    - read_energy(filename=None): Read GPU energy data from the specified file.
    - export_figure(plt, x='Time/s', y='Energy/W', filename="energy"): Export a matplotlib figure to a file.
    - graph(file, output, plot_type, histogram_frequency): Generate and display a graph based on GPU event log data.
    - exit_handler(signal_received, frame): Handle the exit when SIGINT or CTRL-C is detected.
    - count(): Get the count of available GPUs.
    - vendor(): Get GPU vendor information.
    - processes(): Get information about GPU processes.
    - system(): Get general information about the GPU system.
    - status(): Get detailed status information about the GPU.
    - smi(output=None, filename=None): Run nvidia-smi command and parse the output.
    - watch(logfile=None, delay=1.0, repeated=None, dense=False, gpu=None): Continuously monitor GPU status and log the information.
    - __str__(): Return a string representation of the Gpu object.

Usage:
    from gpu_module import Gpu

    # Create a Gpu instance
    gpu_instance = Gpu()

    # Probe GPU information
    gpu_instance.probe()

    # Monitor GPU status continuously
    gpu_instance.watch()

"""

import os
# from cloudmesh.common.Printer import Printer
import pprint
import sys
from datetime import date
from datetime import datetime
from signal import signal, SIGINT

import matplotlib.pyplot as plt
import xmltodict
import yaml

from cloudmesh.common.Shell import Shell
from cloudmesh.common.dotdict import dotdict
from cloudmesh.common.util import readfile
from cloudmesh.common.util import banner

from tabulate import tabulate
from cloudmesh.common.util import csv_to_list

class Gpu:
    """
      The `Gpu` class provides functionality to probe, monitor, and analyze GPU information using nvidia-smi.

      Attributes:
          sep (str): Separator for date and time. Default is "T".
          running (bool): Flag indicating whether GPU monitoring is active.
          _smi (list): List containing GPU information from nvidia-smi.

      Methods:
          - probe(): Probe GPU information and display relevant details.
          - fix_date_format(df, col): Fix date format in the given DataFrame column.
          - read_eventlog(filename): Read GPU event log from the specified file.
          - read_energy(filename=None): Read GPU energy data from the specified file.
          - export_figure(plt, x='Time/s', y='Energy/W', filename="energy"): Export a matplotlib figure to a file.
          - graph(file, output, plot_type, histogram_frequency): Generate and display a graph based on GPU event log data.
          - exit_handler(signal_received, frame): Handle the exit when SIGINT or CTRL-C is detected.
          - count(): Get the count of available GPUs.
          - vendor(): Get GPU vendor information.
          - processes(): Get information about GPU processes.
          - system(): Get general information about the GPU system.
          - status(): Get detailed status information about the GPU.
          - smi(output=None, filename=None): Run nvidia-smi command and parse the output.
          - watch(logfile=None, delay=1.0, repeated=None, dense=False, gpu=None): Continuously monitor GPU status and log the information.
          - __str__(): Return a string representation of the Gpu object.
      """

    def __init__(self, sep="T"):
        """
        Initialize the Gpu class.

        Args:
            sep (str): Separator for date and time. Default is "T".
        """
        self.sep =sep
        self.running = True
        try:
            self._smi = dict(self.smi(output="json"))['nvidia_smi_log']['gpu']
            if not isinstance(self._smi, list):
                self._smi = [self._smi]
        except KeyError:
            raise RuntimeError("nvidia-smi not installed.")
        self.gpus = 0

    def probe(self):
        """
        Probe GPU information and display relevant details.

        Returns:
            str: Empty string.
        """
        banner("Cloudmesh GPU Probe", c="=")

        for label, command in [
             ("nvidia-smi", "nvidia-smi"),
        ]:
            try:
                banner(label)
                r = Shell.run(command)
                print (r)
            except:
                pass

        for label, command in [
            ("OS Info", "cat /etc/*release"),
        ]:
            try:
                banner(label)
                r = Shell.run(command)
                r = r.replace("=", ",")
                data = csv_to_list(r)
                print(tabulate(data, tablefmt='fancy_grid'))
            except:
                pass

        for label, command in [
            ("drivers list", "xxx ubuntu-drivers list")
        ]:
            try:
                banner(label)
                r = Shell.run(command)
                r = r.replace("kernel modules provided by", "")\
                    .replace("(","")\
                    .replace(")", "")\
                    .replace(" ", "")
                data = csv_to_list(r)
                print(tabulate(data,tablefmt='fancy_grid'))
            except:
                pass

        for label, command in [
             ("Nvidia Drivers","apt search nvidia-driver"),
        ]:
            try:
                banner(label)
                lines = Shell.run(command)\
                    .replace("\n  ", ";").splitlines()
                lines = [line.replace(" ", ";", 3) for line in lines]
                lines = "\n".join(lines).replace("\n\n", "\n")
                lines =  "\n".join(Shell.find_lines_from(lines, "nvidia"))

                data = csv_to_list(lines, sep=";")
                print(tabulate(data,tablefmt='fancy_grid'))
            except:
                pass



        return ""


    def fix_date_format(self, df, col):
        """
        Fix date format in the given DataFrame column.

        Args:
            df (pandas.DataFrame): DataFrame containing the data.
            col (str): Column name with date values.

        Returns:
            pandas.DataFrame: DataFrame with fixed date format.
        """
        import pandas as pd
        # if We have T in it, we do not need to fix
        for i, row in df.iterrows():
            value = df.loc[i, col]
            if "T" not in value:
                new_date = df.loc[i, col].replace(":", " ", 1)
                df.loc[i, col] = new_date
        df[col] = pd.to_datetime(df[col])
        return df

    def read_eventlog(self, filename):
        """
        Read GPU event log from the specified file.

        Args:
            filename (str): Path to the event log file.

        Returns:
            tuple: Header and data from the event log.
        """

        import csv
        data = []
        header = None
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            data = list(reader)

        header = data[1]
        header[0] = "time"
        data = data[2:]
        return header, data


    def read_energy(self, filename=None):
        """
        Read GPU energy data from the specified file.

        Args:
            filename (str): Path to the energy data file.

        Returns:
            pandas.DataFrame: DataFrame containing the energy data.
        """
        import pandas as pd
        import io

        location = Shell.map_filename(filename).path
        # 1: means removing hashes
        content = readfile(location).splitlines()[1:]
        # removing #
        content[0] = content[0][2:]
        # print(content[0:10])
        content = "\n".join(content)
        content = content.replace(', ', ',')
        df = pd.read_csv(io.StringIO(content), sep=',')

        df = self.fix_date_format(df, "time")
        df[["time"]] = df[["time"]].astype('datetime64[ns]')
        return df



    def export_figure(self, plt, x='Time/s', y='Energy/W',
                      filename="energy"):
        """
        Export a matplotlib figure to a file.

        Args:
            plt (matplotlib.pyplot): Matplotlib pyplot instance.
            x (str): X-axis label. Default is 'Time/s'.
            y (str): Y-axis label. Default is 'Energy/W'.
            filename (str): Base filename for the exported figure.

        Returns:
            None
        """
        plt.xlabel(x)
        plt.ylabel(y)
        png = filename + ".png"
        pdf = filename + ".pdf"
        print ("Writing", png)
        plt.savefig(png, bbox_inches='tight', dpi=600)
        print ("Writing", pdf)
        plt.savefig(pdf, bbox_inches='tight')


    def graph(self, file, output, plot_type, histogram_frequency):
        """
        Generate and display a graph based on GPU event log data.

        Args:
            file (str): Path to the GPU event log file.
            output (str): Output file format (e.g., 'pdf', 'png').
            plot_type (str): Type of plot ('line' or 'histogram').
            histogram_frequency (str): Frequency for histogram ('percent' or 'count').

        Returns:
            str: Information about the written output file.
        """
        import seaborn as sns
        import matplotlib.pyplot as plt
        from datetime import datetime
        import pandas as pd

        header, data = self.read_eventlog(file)
        time = []
        value = []
        for entry in data:
            t = entry[0]
            t = datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%f')

            time.append(t)
            value.append(entry[7])
        x_label = "Time in s"
        y_label = "Power Draw in W"

        df = pd.DataFrame(
            {
                "time": time,
                "energy": value
            }
        )
        df['elapsed'] = df['time'] - pd.to_datetime(df['time'].values[0])

        df['elapsed_seconds'] = df.apply(
            lambda row: row.elapsed / pd.Timedelta(seconds=1), axis=1)
        df['energy'] = df.apply(lambda row: float(row.energy), axis=1)

        if plot_type == 'histogram':

            if histogram_frequency == 'percent':

                import numpy as np

                df["energy"].plot.hist(weights = np.ones_like(df.index) / len(df.index))
                plt.grid(True)

            else:
                df.hist(column='energy')
            plt.title('')
            x_label = 'Power Draw in W'
            y_label = 'Frequency'
        else:
            ax = sns.lineplot(x=f"elapsed_seconds", y="energy", data=df)

        plt.xlabel(x_label)
        plt.ylabel(y_label)

        # taking out extension from file
        # first we determine if there is extension.
        if '.' in output:
            extension = str(os.path.splitext(output)[1])
            name_of_output = output
        # if there is none then we decide that the output is the extension.
        else:
            extension = '.' + output
            file = str(os.path.splitext(file)[0])
            name_of_output = file + extension

        # png = file + ".png"
        # pdf = file + ".pdf"


        if extension.lower() in [".jpg", ".png"]:
            # written_output = output
            plt.savefig(name_of_output, bbox_inches='tight', dpi=600)
        else:
            # written_output = 'pdf'
            plt.savefig(name_of_output, bbox_inches='tight')

        return f'Written to {name_of_output}'


    def exit_handler(self, signal_received, frame):
        """
        Handle the exit when SIGINT or CTRL-C is detected.

        Args:
            signal_received: The received signal.
            frame: The frame.

        Returns:
            None
        """
        # Handle any cleanup here
        print('SIGINT or CTRL-C detected. Exiting gracefully')
        self.running = False

    @property
    def count(self):
        """
        Get the count of available GPUs.

        Returns:
            int: Count of available GPUs.
        """
        if self.gpus == 0:
            try:
                self.gpus = int(Shell.run("nvidia-smi --list-gpus | wc -l").strip())
            except:
                self.gpus = 0
        return self.gpus

    def vendor(self):
        """
        Get GPU vendor information.

        Returns:
            str or list: GPU vendor information.
        """
        if os.name != "nt":
            try:
                r = Shell.run("lspci -vnn | grep VGA -A 12 | fgrep Subsystem:").strip()
                result = r.split("Subsystem:")[1].strip()
            except:
                result = None
        else:
            try:
                r = Shell.run("wmic path win32_VideoController get AdapterCompatibility").strip()
                result = [x.strip() for x in r.split("\r\r\n")[1:]]
            except Exception:
                results = None
        return result

    def processes(self):
        """
        Get information about GPU processes.

        Returns:
            dict: GPU process information.
        """
        result = {}
        try:
            # We want to call this each time, as we want the current processes
            data = dict(self.smi(output="json"))["nvidia_smi_log"]['gpu']
            for i in range(self.count):
                information = data[i]["processes"]["process_info"]
                result[i] = information
        except Exception as e:
            print(e)
        return result

    def system(self):
        """
         Get general information about the GPU system.

         Returns:
             dict: General GPU system information.
         """
        result = self._smi
        for gpu_instance in range(len(self._smi)):
            for attribute in [
                '@id',
                # 'product_name',
                # 'product_brand',
                # 'product_architecture',
                'display_mode',
                'display_active',
                'persistence_mode',
                'mig_mode',
                'mig_devices',
                'accounting_mode',
                'accounting_mode_buffer_size',
                'driver_model',
                'serial',
                'uuid',
                'minor_number',
                # 'vbios_version',
                'multigpu_board',
                'board_id',
                'gpu_part_number',
                'gpu_module_id',
                # 'inforom_version',
                'gpu_operation_mode',
                'gsp_firmware_version',
                'gpu_virtualization_mode',
                'ibmnpu',
                'pci',
                'fan_speed',
                'performance_state',
                'clocks_throttle_reasons',
                'fb_memory_usage',
                'bar1_memory_usage',
                'compute_mode',
                'utilization',
                'encoder_stats',
                'fbc_stats',
                'ecc_mode',
                'ecc_errors',
                'retired_pages',
                'remapped_rows',
                'temperature',
                'supported_gpu_target_temp',
                'power_readings',
                'clocks',
                'applications_clocks',
                'default_applications_clocks',
                'max_clocks',
                'max_customer_boost_clocks',
                'clock_policy',
                'voltage',
                'supported_clocks',
                'processes'
            ]:
                try:
                    del result[gpu_instance][attribute]
                    result[gpu_instance]["vendor"] = self.vendor()
                except KeyError:
                    pass
        return result

    def status(self):
        """
        Get detailed status information about the GPU.

        Returns:
            dict: Detailed GPU status information.
        """
        result = self._smi
        for gpu_instance in range(len(self._smi)):
            for attribute in [
                '@id',
                'product_name',
                'product_brand',
                'product_architecture',
                'display_mode',
                'display_active',
                'persistence_mode',
                'mig_mode',
                'mig_devices',
                'accounting_mode',
                'accounting_mode_buffer_size',
                'driver_model',
                'serial',
                'uuid',
                'minor_number',
                'vbios_version',
                'multigpu_board',
                'board_id',
                'gpu_part_number',
                'gpu_module_id',
                'inforom_version',
                'gpu_operation_mode',
                'gsp_firmware_version',
                'gpu_virtualization_mode',
                'ibmnpu',
                'pci',
                # 'fan_speed',
                'performance_state',
                'clocks_throttle_reasons',
                'fb_memory_usage',
                'bar1_memory_usage',
                'compute_mode',
                # 'utilization',
                'encoder_stats',
                'fbc_stats',
                'ecc_mode',
                'ecc_errors',
                'retired_pages',
                'remapped_rows',
                # 'temperature',
                # 'supported_gpu_target_temp',
                # 'power_readings',
                # 'clocks',
                'applications_clocks',
                'default_applications_clocks',
                'max_clocks',
                'max_customer_boost_clocks',
                'clock_policy',
                # 'voltage',
                'supported_clocks',
                'processes'
            ]:
                try:
                    del result[gpu_instance][attribute]
                except KeyError:
                    pass
        return result

    def smi(self, output=None, filename=None):
        """
         Run nvidia-smi command and parse the output.

         Args:
             output (str): Output format ('text', 'json', 'yaml').
             filename (str): Path to a file containing nvidia-smi output.

         Returns:
             dict or str: Parsed nvidia-smi output.
         """
        # None = text
        # json
        # yaml
        try:
            if filename is None and output is None:
                result = Shell.run("nvidia-smi").replace("\r", "")
                return result

            if filename is not None:
                r = readfile(filename)
            else:
                r = Shell.run("nvidia-smi -q -x")
            if output == "xml":
                result = r
            elif output == "json":
                result = xmltodict.parse(r)

                if int(result["nvidia_smi_log"]["attached_gpus"]) == 1:
                    data = result["nvidia_smi_log"]["gpu"]
                    result["nvidia_smi_log"]["gpu"] = [data]

            elif output == "yaml":
                result = yaml.dump(xmltodict.parse(r))
        except Exception as e:
            print(e)
            result = None
        return result

    def watch(self, logfile=None, delay=1.0, repeated=None, dense=False, gpu=None):
        """
         Continuously monitor GPU status and log the information.

         Args:
             logfile (str): Path to the log file.
             delay (float): Delay between each monitoring iteration.
             repeated (int): Number of repetitions (-1 for continuous monitoring).
             dense (bool): Whether to log data in dense format.
             gpu (list): List of GPU indices to monitor.

         Returns:
             None
         """

        if repeated is None:
            repeated = -1
        else:
            repeated = int(repeated)

        try:
            delay = float(delay)
        except Exception as e:
            delay = 1.0

        signal(SIGINT, self.exit_handler)

        stream = sys.stdout
        if logfile is None:
            stream = sys.stdout
        else:
            stream = open(logfile, "w")

        print("# ####################################################################################")
        print("# time, ", end="")
        for i in range(self.count):
            print(
                f"{i} id, "
                f"{i} gpu_util %, "
                f"{i} memory_util %, "
                f"{i} encoder_util %, "
                f"{i} decoder_util %, "
                f"{i} gpu_temp C, "
                f"{i} power_draw W",
                end="")
        print()

        counter = repeated

        if gpu is not None:
            selected = [int(i) for i in gpu]
        else:
            selected = list(range(self.count))
        while self.running:
            try:
                if counter > 0:
                    counter = counter - 1
                    self.running = self.running and counter > 0
                today = date.today()
                now = datetime.now().time()  # time object
                data = self.smi(output="json")

                result = [f"{today}{self.sep}{now}"]

                for gpu in range(self.count):
                    if gpu in selected:
                        utilization = dotdict(data["nvidia_smi_log"]["gpu"][gpu]["utilization"])
                        temperature = dotdict(data["nvidia_smi_log"]["gpu"][gpu]["temperature"])
                        power = dotdict(data["nvidia_smi_log"]["gpu"][gpu]["power_readings"])
                        line = \
                            f"{gpu:>3}, " \
                            f"{utilization.gpu_util[:-2]: >3}, " \
                            f"{utilization.memory_util[:-2]: >3}, " \
                            f"{utilization.encoder_util[:-2]: >3}, " \
                            f"{utilization.decoder_util[:-2]: >3}, " \
                            f"{temperature.gpu_temp[:-2]: >5}, " \
                            f"{power.power_draw[:-2]: >8}"
                        result.append(line)

                result = ", ".join(result)
                if dense:
                    result = result.replace(" ", "")
                print(result, file=stream)

            except Exception as e:
                print(e)

    def __str__(self):
        """
        Return a string representation of the Gpu object.

        Returns:
            str: String representation of the Gpu object.
        """

        return pprint.pformat(self._smi, indent=2)
