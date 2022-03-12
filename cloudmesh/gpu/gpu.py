import collections
import sys
import time

import xmltodict
from cloudmesh.common.Shell import Shell
#from cloudmesh.common.Printer import Printer
import pprint
import os
import yaml
from signal import signal, SIGINT
from cloudmesh.common.dotdict import dotdict
from datetime import date

from datetime import datetime



class Gpu:

    def __init__(self):

        self.running = True
        try:
            self._smi = dict(self.smi(output="json"))['nvidia_smi_log']['gpu']
            if not isinstance(self._smi, list):
                self._smi = [self._smi]
        except KeyError:
            raise RuntimeError("nvidia-smi not installed.")


    def exit_handler(self, signal_received, frame):
        """
        Kube manager has a build in Benchmark framework. In case you
        press CTRL-C, this handler asures that the benchmarks will be printed.

        :param signal_received:
        :type signal_received:
        :param frame:
        :type frame:
        :return:
        :rtype:
        """
        # Handle any cleanup here
        print('SIGINT or CTRL-C detected. Exiting gracefully')
        self.running = False

    @property
    def count(self):
        try:
            number = int(Shell.run("nvidia-smi --list-gpus | wc -l").strip())
        except:
            number = 0
        return number

    def vendor(self):
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
        result = None
        try:
            # We want to call this each time, as we want the current processes
            result = dict(self.smi(self, output="json"))["nvidia_smi_log"]["gpu"]
            if isinstance(result, list):
                result = [x['processes']['process_info'] for x in result]
            else:
                result = result["processes"]["process_info"]
        except KeyError:
            pass
        return result

    def system(self):
        result = self._smi
        for gpu_instance in range(len(self._smi)):
            for attribute in [
                    '@id',
                    #'product_name',
                    #'product_brand',
                    #'product_architecture',
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
                    #'vbios_version',
                    'multigpu_board',
                    'board_id',
                    'gpu_part_number',
                    'gpu_module_id',
                    #'inforom_version',
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
                    #'fan_speed',
                    'performance_state',
                    'clocks_throttle_reasons',
                    'fb_memory_usage',
                    'bar1_memory_usage',
                    'compute_mode',
                    #'utilization',
                    'encoder_stats',
                    'fbc_stats',
                    'ecc_mode',
                    'ecc_errors',
                    'retired_pages',
                    'remapped_rows',
                    #'temperature',
                    #'supported_gpu_target_temp',
                    #'power_readings',
                    #'clocks',
                    'applications_clocks',
                    'default_applications_clocks',
                    'max_clocks',
                    'max_customer_boost_clocks',
                    'clock_policy',
                    #'voltage',
                    'supported_clocks',
                    'processes'
                    ]:
                try:
                    del result[gpu_instance][attribute]
                except KeyError:
                    pass
        return result

    def smi(self, output=None):
        # None = text
        # json
        # yaml
        try:
            if output is None:
                result = Shell.run("nvidia-smi").replace("\r", "")
            else:
                r = Shell.run("nvidia-smi -q -x")
                if output == "xml":
                    result = r
                elif output == "json":
                    result = xmltodict.parse(r)
                elif output == "yaml":
                    result = yaml.dump(xmltodict.parse(r))
        except:
            result = None
        return result

    def watch(self, logfile=None, delay=1):

        try:
            delay=int(delay)
        except Exception as e:
            delay = 1

        signal(SIGINT, self.exit_handler)

        stream = sys.stdout
        if logfile is None:
            stream = sys.stdout
        else:
            stream = open(logfile, "w")

        print("# ####################################################################################")
        print ("# time, gpu_util %, memory_util %, encoder_util %, decoder_util %, gpu_temp C, power_draw W")

        while self.running:
            try:
                today = date.today()
                now = datetime.now().time()  # time object
                data = self.smi(output="json")

                utilization = dotdict(data["nvidia_smi_log"]["gpu"]["utilization"])
                temperature = dotdict(data["nvidia_smi_log"]["gpu"]["temperature"])
                power = dotdict(data["nvidia_smi_log"]["gpu"]["power_readings"])

                #
                # have alternative format without spaces
                #
                result = \
                    f"{today} {now}, " \
                    f"{utilization.gpu_util[:-2]: >3}, " \
                    f"{utilization.memory_util[:-2]: >3}, " \
                    f"{utilization.encoder_util[:-2]: >3}, " \
                    f"{utilization.decoder_util[:-2]: >3}, " \
                    f"{temperature.gpu_temp[:-2]: >5}, " \
                    f"{power.power_draw[:-2]: >8}"

                print (result, file=stream)

            except Exception as e:
                print (e)

    def __str__(self):
        return pprint.pformat(self._smi, indent=2)
