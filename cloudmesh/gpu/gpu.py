import xmltodict
from cloudmesh.common.Shell import Shell
import os
import yaml

class Gpu:

    def __init__(self):
        pass

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
        try:
            result = dict(self.smi(output="json"))
            result = result["nvidia_smi_log"]["gpu"]["processes"]["process_info"]
        except:
            result = None
        return result

    def system(self):
        try:
            result = dict(self.smi(output="json"))
            result = result["nvidia_smi_log"]["gpu"]
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
                del result[attribute]
                result["vendor"] = self.vendor()
        except:
            result = None
        return result

    def status(self):
        try:
            result = dict(self.smi(output="json"))
            result = result["nvidia_smi_log"]["gpu"]
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
                del result[attribute]
        except:
            result = None
        return result

    def smi(self, output=None):
        # None = text
        # json
        # yaml
        try:
            if output == None:
                result = Shell.run("nvidia-smi")
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

