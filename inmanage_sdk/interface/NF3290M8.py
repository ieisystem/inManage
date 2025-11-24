# -*- coding:utf-8 -*-

from inmanage_sdk.interface.CommonM8 import CommonM8
from inmanage_sdk.util import RedfishTemplate

class NF3290M8(CommonM8):

    #任务列表
    task_dict = {
        "BMC": "BMC",
        "BMCRollback": "RollBack",
        "BMC_PFR": "bmc",
        "BIOS": None,
        "MB": "MB_CPLD",
        "SCM_CPLD": "SCM_CPLD",
        # "BP_CPLD": "BP0_CPLD",
        "FAN_CPLD": "FAN0_CPLD",
        "MP_CPLD": "MP_CPLD",
    }

    # 触发升级
    def _execute_update(self, client, args):
        url_result = self.get_url_info("execute_update")
        pre_dict = {
            0: False,
            1: True
        }
        data = {}
        if args.type == "BMC":
            data['FlashItem'] = "OpenBMC_ENC"
        else:
            data['FlashItem'] = args.type
        if "PFR" in args.type:
            data['PFRType'] = True
            if "pfrimage" in args and args.pfrimage == "active":
                data['PFRRegion'] = "Active"
            else:
                data['PFRRegion'] = "Recovery"
            data['PFRUpdateDynamic'] = pre_dict.get(1 - args.pre_conf)
        else:
            data['PreserveConf'] = pre_dict.get(args.pre_conf)

        data = {"Oem": {"Public": data}}
        postBody = {}
        postBody['json'] = data
        postBody['url'] = url_result.get('url')
        res = RedfishTemplate.post_for_object(client, postBody)
        if res.State:
            return True, None
        else:
            return False, str(res.Message)
