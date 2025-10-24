# -*- coding:utf-8 -*-

import collections
import sys
import re
import json
import html
import os
import time
from inmanage_sdk.interface import utoolUtil
from inmanage_sdk.interface.ResEntity import (
    ResultBean,
    SMTPBean,
    SmtpDestBean,
    DNSBean,
    NetworkBondBean,
    HBABean,
    HBAPost,
    SessionBean,
    NICController,
    NicPort,
    NICBean,
    NicAllBean,
    UpTimeBean,
    NetBean,
    IPv4Bean,
    IPv6Bean,
    FruBean,
    vlanBean
)
from inmanage_sdk.interface.Base import (Base, ascii2hex, hexReverse)
from inmanage_sdk.util import RedfishTemplate, RegularCheckUtil
from inmanage_sdk.command import RestFunc, IpmiFunc


class CommonM8(Base):

    def get_url_info(self, key, name="CommonM8"):
        import yaml
        import os
        url_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "command",
                                "RedfishUrl.yml")
        url_file = open(url_path)
        content = yaml.load(url_file, Loader=yaml.FullLoader)
        url_file.close()
        sub_content = content.get(name, {})
        if sub_content.get(key.lower(), None):
            return sub_content.get(key.lower())
        else:
            return {}

    def getsmtp(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            item = result.Message
            status_dict = {1: "Enabled", 0: "Disabled", "Enable": "Enabled", "Disable": "Disabled"}
            smtpbean = SMTPBean()
            SmtpCfg = item.get('SmtpCfg')
            # if SnmpTrapCfg['TrapVersion'] == 0:
            if SmtpCfg['SmtpEnable'] == 0:
                smtpbean.SmtpEnable('Disabled')
            else:
                smtpbean.SmtpEnable('Enabled')
                smtpbean.ServerAddr(SmtpCfg.get('ServerAddr', None))
                smtpbean.SmtpPort(SmtpCfg.get('SmtpPort', 0))
                smtpbean.SmtpSecurePort(SmtpCfg.get('SmtpSecurePort', 0))
                smtpbean.EnableSTARTTLS(status_dict[SmtpCfg.get('EnableSTARTTLS', 0)])
                smtpbean.EnableSSLTLS(status_dict[SmtpCfg.get('EnableSSLTLS', 0)])
                smtpbean.SMTPAUTH(status_dict[SmtpCfg.get('SMTPAUTH', 0)])
                smtpbean.UserName(SmtpCfg.get('UserName', None))
                smtpbean.PassWord(SmtpCfg.get('PassWord', None))
                smtpbean.SenderAddr(SmtpCfg.get('SenderAddr', None))
                smtpbean.Subject(SmtpCfg.get('Subject', None))
                smtpbean.HostName(status_dict[SmtpCfg.get('HostName', 0)])
                smtpbean.SerialNumber(status_dict[SmtpCfg.get('SerialNumber', 0)])
                smtpbean.AssetTag(status_dict[SmtpCfg.get('AssetTag', 0)])
                smtpbean.EventLevel(SmtpCfg.get('EventLevel', None))
            SmtpDestCfg = item.get('SmtpDestCfg')
            SmtpDestList = []
            for std in SmtpDestCfg:
                stdnew = SmtpDestBean()
                stdnew.Id(std["Id"] + 1)
                stdnew.Enable(status_dict.get(std["Enabled"], std["Enabled"]))
                stdnew.EmailAddress(std.get('EmailAddress', None))
                stdnew.Description(std.get('Description', None))
                SmtpDestList.append(stdnew.dict)
            smtpbean.Destination(SmtpDestList)
            res.Message([smtpbean.dict])
            res.State("Success")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def setsmtpcom(self, client, args):
        res = ResultBean()

        def patch_func(data, responses):
            get_data = responses.json()
            current_smtp_cfg = get_data.get("SmtpCfg", {})
            set_smtp_cfg = data.get("SmtpCfg")
            if set_smtp_cfg:
                for key in set_smtp_cfg.keys():
                    current_smtp_cfg[key] = set_smtp_cfg.get(key)

            if current_smtp_cfg.get("SmtpEnable") and current_smtp_cfg.get("SMTPAUTH"):
                if not current_smtp_cfg.get("PassWord"):
                    return ResultBean.fail('please input SMTP server Password(-PW).')
            if current_smtp_cfg.get("SmtpEnable") is False:
                current_smtp_cfg = {"SmtpEnable" : False}

            patch_body = {"SmtpCfg": current_smtp_cfg}

            if data.get("SmtpDestCfg"):
                set_smtp_dest = data.get("SmtpDestCfg")[0]
                current_smtp_dest = get_data.get("SmtpDestCfg", [])
                for cdest in current_smtp_dest:
                    if cdest.get("Id") == set_smtp_dest.get("Id") - 1:
                        if set_smtp_dest.get("Enabled") is not None:
                            cdest["Enabled"] = set_smtp_dest['Enabled']
                        if set_smtp_dest.get("EmailAddress"):
                            cdest["EmailAddress"] = set_smtp_dest['EmailAddress']
                        if set_smtp_dest.get("Description"):
                            cdest["Description"] = set_smtp_dest['Description']
                        break
                if cdest.get("Enabled"):
                    if not cdest.get("EmailAddress"):
                        return ResultBean.fail('please input SMTP server Password(-PW).')

                patch_body['SmtpDestCfg'] = [cdest]

            return ResultBean.success(patch_body)

        bool_dict = {
            'enable': True,
            'disable': False
        }
        fulldata = {}
        data = {}
        if args.status:
            data['SmtpEnable'] = bool_dict[args.status]
        if args.serverIP:
            data['ServerAddr'] = args.serverIP
        if args.serverPort is not None:
            if args.serverPort < 1 or args.serverPort > 65535:
                return ResultBean.fail('the length of serverPort should between 1 and 65535.')
            data['SmtpPort'] = args.serverPort
        if args.serverSecurePort is not None:
            if args.serverSecurePort < 1 or args.serverSecurePort > 65535:
                return ResultBean.fail('the length of serverSecurePort should between 1 and 65535.')
            data['SmtpSecurePort'] = args.serverSecurePort
        if args.email:
            data['SenderAddr'] = args.email
        if args.serverAuthentication:
            data['SMTPAUTH'] = bool_dict[args.serverAuthentication]
        if args.serverUsername:
            data['UserName'] = args.serverUsername
        if args.serverPassword:
            data['PassWord'] = args.serverPassword
        if args.SSLTLSEnable:
            data['EnableSSLTLS'] = bool_dict[args.SSLTLSEnable]
        if args.STARTTLSEnable:
            data['EnableSTARTTLS'] = bool_dict[args.STARTTLSEnable]
        if args.subject:
            data['Subject'] = args.subject
        if args.hostName:
            data['HostName'] = bool_dict[args.hostName]
        if args.serialNumber:
            data['SerialNumber'] = bool_dict[args.serialNumber]
        if args.assetTag:
            data['AssetTag'] = bool_dict[args.assetTag]
        if args.eventLevel:
            if args.eventLevel == "info":
                args.eventLevel = "Info"
            elif args.eventLevel == "critical":
                args.eventLevel = "Critical"
            else:
                args.eventLevel = "Warning"
            data['EventLevel'] = args.eventLevel
        if data:
            fulldata["SmtpCfg"] = data

        # if args.destinationid:
        #     dest = {}
        #     dest['Id'] = args.destinationid
        #     if args.enabled:
        #         dest['Enabled'] = bool_dict[args.enabled]
        #     if args.address:
        #         dest['EmailAddress'] = args.address
        #     if args.description is not None:
        #         if len(args.description) > 111:
        #             return ResultBean.fail('the length of serverPort should between 1 and 65535.')
        #         dest['Description'] = args.description
        #     fulldata["SmtpDestCfg"] = [dest]
        # if not fulldata:
        #     res.State('Failure')
        #     res.Message("Nothing to set.")
        #     return res

        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        patchbody = {}
        patchbody["url"] = url_result.get('url')
        patchbody["func"] = patch_func
        patchbody["json"] = fulldata
        result = RedfishTemplate.patch_for_object(client, patchbody)
        if result.State:
            res.State('Success')
            res.Message(" ")
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def setsmtpdest(self, client, args):

        def patch_func(data, responses):
            get_data = responses.json()
            current_smtp_dests = get_data.get("SmtpDestCfg", [])
            for current_smtp_dest in current_smtp_dests:
                if current_smtp_dest.get("Id") == data.get("Id") - 1:
                    if data.get("Enabled") is not None:
                        current_smtp_dest["Enabled"] = data['Enabled']
                    if data.get("EmailAddress"):
                        current_smtp_dest["EmailAddress"] = data['EmailAddress']
                    if data.get("Description"):
                        current_smtp_dest["Description"] = data['Description']
                    if current_smtp_dest["Enabled"] is False:
                        current_smtp_dest = {"Id": data.get("Id") - 1 ,"Enabled": False}
                        current_smtp_dests = [current_smtp_dest]
            # DestIndex 为SmtpDestCfg的下标，现在list只有一个 所以就是0
            # ami
            # patch_body = {"SmtpDestCfg": current_smtp_dests, "DestIndex": data.get("Id") - 1, "SmtpCfg":{'SenderAddr': 'admin@inspur.com', "EventLevel": "Info"}}
            patch_body = {"SmtpDestCfg": current_smtp_dests, "DestIndex": data.get("Id") - 1}
            return ResultBean.success(patch_body)

        bool_dict = {
            'enable': True,
            'disable': False
        }
        data = {}
        if args.destinationid:
            data['Id'] = args.destinationid
        if args.enabled:
            data['Enabled'] = bool_dict[args.enabled]
        if args.address:
            data['EmailAddress'] = args.address
        if args.description is not None:
            if len(args.description) > 111:
                return ResultBean.fail('the length of serverPort should between 1 and 65535.')
            data['Description'] = args.description

        # url_result = self.get_url_info(sys._getframe().f_code.co_name)
        url_result = self.get_url_info("setsmtpcom")
        patchbody = {}
        patchbody["url"] = url_result.get('url')
        patchbody["func"] = patch_func
        patchbody["json"] = data
        result = RedfishTemplate.patch_for_object(client, patchbody)
        res = ResultBean()
        if result.State:
            res.State('Success')
            res.Message(" ")
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getuser(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data = []
            for item in info:
                single_data = collections.OrderedDict()
                single_data['UserID'] = item.get('Id', "N/A")
                single_data['UserName'] = item.get('UserName', "N/A")
                single_data['UserAccess'] = "enable" if item.get('Enabled', False) else "disable"
                single_data['UserGroup'] = item.get('RoleId', 'N/A')
                data.append(single_data)
            res.State("Success")
            res.Message(data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def adduser(self, client, args):
        res = ResultBean()
        if len(args.upass) < 8 or len(args.upass) > 20:
            res.State("Failure")
            res.Message('password length should between 8 and 20')
            return res
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message
            support_id = []
            exist_name = []
            accounts_list = info.get("Oem", {}).get("Public", {}).get("Accounts", [])
            if len(accounts_list) == 0:
                res.State("Failure")
                res.Message("get user info failed.")
                return res
            for account in accounts_list:
                name = account.get('UserName')
                if name is not None and name != "":
                    exist_name.append(name)
                else:
                    support_id.append(account.get('UserId'))
            if len(support_id) == 0:
                res.State("Failure")
                res.Message("no space to add users.")
                return res
            if args.uid and args.uid not in support_id:
                res.State("Failure")
                res.Message("please choose -ID from " + str(support_id))
                return res
            if args.uname in exist_name:
                res.State("Failure")
                res.Message(args.uname + " has been exist.")
                return res
            user_group = ["ipmi", "redfish", "snmp", "ssh", "web"]
            if args.priv is not None:
                if "kvm" in args.priv:
                    user_group.append('kvm')
                if "vmm" in args.priv:
                    user_group.append('vm')
                if "sol" in args.priv:
                    user_group.append('sol')
            set_data = {
                "UserName": args.uname,
                "Password": args.upass,
                "RoleId": args.roleid,
                "UserGroups": user_group,
                "Oem": {"Public": {}}
            }
            if args.uid:
                set_data['Id'] = args.uid
            else:
                set_data['Id'] = support_id[0]
            set_data.get("Oem").get("Public")["EncryptFlag"] = False
            set_data.get("Oem").get("Public")['CurrentPassword'] = args.passcode
            postBody = {}
            postBody['url'] = url_result.get('url')
            postBody['json'] = set_data
            set_result = RedfishTemplate.post_for_object(client, postBody)
            if set_result.State:
                res.State("Success")
                res.Message("")
            else:
                res.State("Failure")
                res.Message(set_result.Message)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def setuser(self, client, args):
        res = ResultBean()
        if args.uname is None and args.uid is None:
            res.State("Failure")
            res.Message("enter at lease one of -N and -ID.")
            return res
        if args.uid is not None:
            if int(args.uid) < 1 or int(args.uid) > 16:
                res.State("Failure")
                res.Message("user id out of range, please input -ID between 1 and 16.")
                return res
        if args.upass is None and args.uname is None and args.roleid is None and args.access is None:
            res.State("Failure")
            res.Message("please input a command at least.")
            return res

        url_get = self.get_url_info("getuser")
        get_result = RedfishTemplate.get_for_object_single(client, url_get.get('url'))
        if get_result.State:
            get_data = get_result.Message
            accounts = get_data.get("Oem", {}).get("Public", {}).get("Accounts", [])
            uid = None
            uname = None
            uaccess = None
            if isinstance(accounts, list) and len(accounts) > 0:
                for account in accounts:
                    if args.uname is not None and account.get('UserName', '') == args.uname and "UserId" in account:
                        if args.uid is not None and account.get('UserId') != args.uid:
                            res.Message('user ' + str(args.uname) + ' not match user id ' + str(args.uid))
                            res.State('Failure')
                            return res
                        uid = account.get('UserId')
                        uname = args.uname
                        uaccess = account.get('Enabled')
                        break
                    elif args.uid is not None and account.get('UserId', -1) == args.uid and "UserName" in account:
                        if args.uname is not None and account.get('UserName') != args.uname:
                            res.Message('user ' + str(args.uname) + ' not match user id ' + str(args.uid))
                            res.State('Failure')
                            return res
                        uid = args.uid
                        uname = account.get('UserName')
                        uaccess = account.get('Enabled')
                        break
                if uid is None:
                    res.Message(str(args.uname) + ' not exist.')
                    res.State('Failure')
                    return res
                if uname is None:
                    res.Message('user id ' + str(args.uid) + ' not exist.')
                    res.State('Failure')
                    return res
                if args.newname:
                    uname = args.newname
                data = {
                    "UserName": uname,
                    "Oem": {"Public": {}}
                }
                if args.upass:
                    data['Password'] = args.upass
                else:
                    data['Password'] = None
                if args.access:
                    if args.access == "enable":
                        data['Enabled'] = True
                    else:
                        data['Enabled'] = False
                else:
                    if uaccess == "Enable":
                        data['Enabled'] = True
                    else:
                        data['Enabled'] = False
                if args.roleid:
                    data['RoleId'] = args.roleid

                if args.priv is not None:
                    user_group = ["ipmi", "redfish", "snmp", "ssh", "web"]
                    if "kvm" in args.priv:
                        user_group.append('kvm')
                    if "vmm" in args.priv:
                        user_group.append('vm')
                    if "sol" in args.priv:
                        user_group.append('sol')
                    data["UserGroups"] = user_group
                data.get("Oem").get("Public")["EncryptFlag"] = False
                data.get("Oem").get("Public")['CurrentPassword'] = args.passcode
                url_set = self.get_url_info("setuser")
                patchBody = {}
                patchBody['url'] = str(url_set.get('url')) + str(uid)
                patchBody['json'] = data
                result = RedfishTemplate.patch_for_object(client, patchBody)
                if result.State:
                    res.State("Success")
                    res.Message('')
                else:
                    res.State("Failure")
                    res.Message(result.Message)
            else:
                res.State("Failure")
                res.Message("can not get user accounts")
        else:
            res.State("Failure")
            res.Message(get_result.Message)
        return res

    def deluser(self, client, args):
        res = ResultBean()
        if args.uname is None and args.uid is None:
            res.State("Failure")
            res.Message("enter at lease one of -N and -ID.")
            return res
        if args.uid is not None:
            if int(args.uid) < 1 or int(args.uid) > 16:
                res.State("Failure")
                res.Message("user id out of range, please input -ID between 1 and 16.")
                return res
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message
            accounts_list = info.get("Oem", {}).get("Public", {}).get("Accounts", [])
            if len(accounts_list) == 0:
                res.State("Failure")
                res.Message("get user info failed.")
                return res
            uid = None
            for account in accounts_list:
                if args.uid is not None and args.uname is None:
                    if account.get("UserId", -1) == args.uid:
                        if account.get("UserName", "") is not None:
                            uid = args.uid
                            break
                        else:
                            res.State("Failure")
                            res.Message('user ' + str(args.uid) + ' not exist.')
                            return res
                if args.uid is None and args.uname is not None:
                    if account.get("UserName", "") == args.uname and "UserId" in account:
                        uid = account.get("UserId")
                        break
                else:  # -ID 和 -N均不为空的情况
                    if account.get("UserId", -1) == args.uid:
                        if account.get("UserName", "") == args.uname:
                            uid = args.uid
                            break
                        else:
                            res.State("Failure")
                            res.Message('user ' + str(args.uname) + ' not match user id ' + str(args.uid))
                            return res
            if uid is None:
                res.State("Failure")
                res.Message(str(args.uname) + ' not exist.')
                return res
            delete_url = url_result.get('url') + "/" + str(uid)
            del_result = RedfishTemplate.delete_for_object(client, delete_url)
            if del_result.State:
                res.State("Success")
                res.Message('')
            else:
                res.State("Failure")
                res.Message(del_result.Message)
            return res
        else:
            res.State("Failure")
            res.Message("get user info failed, " + str(result.Message))
        return res

    def edituser(self, client, args):
        result = ResultBean()
        if args.__contains__('uid'):
            if args.state == 'absent':
                result = self.deluser(client, args)
            elif args.state == 'present':
                res = self.getuser(client, args)
                if res.State == "Success" and res.Message is not None:
                    duplication_flag = False
                    data = res.Message
                    for userdata in data:
                        if args.uid is None:
                            if userdata['UserName'] == args.uname:
                                duplication_flag = True
                        else:
                            if str(userdata['UserID']) == str(args.uid):
                                duplication_flag = True
                                args.newname = args.uname
                                args.uname = None
                else:
                    result.State("Failure")
                    result.Message(["get user information error"])
                    return result
                # 有重名
                if duplication_flag:
                    result = self.setuser(client, args)
                else:
                    result = self.adduser(client, args)
        else:
            if args.state == 'absent':
                result = self.deluser(client, args)
            elif args.state == 'present':
                res = self.getuser(client, args)
                if res.State == "Success" and res.Message is not None:
                    duplication_flag = False
                    data = res.Message
                    for userdata in data:
                        if userdata['UserName'] == args.uname:
                            duplication_flag = True
                            args.newname = None
                else:
                    result.State("Failure")
                    result.Message(["get user information error"])
                    return result
                # 有重名
                if duplication_flag:
                    result = self.setuser(client, args)
                else:
                    result = self.adduser(client, args)
        return result

    def getsnmptrap(self, client, args):
        url_result = self.get_url_info("gettrap")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        device_dict = {255: "ALL", 4: "FAN", 5: "INTRUSION", 7: "CPU", 8: "PSU", 11: "ADDIN CARD", 12: "MEMORY",
                       13: "DISK", 15: "SYS FW PROGRESS", 16: "EVENT LOG", 17: "WATCHDOG1", 18: "SYSTEM EVENT",
                       20: "BUTTON", 21: "MAINBORARD", 23: "PCIE", 24: "BMC", 25: "PCH", 27: "CABLE", 29: "SYS RESTART",
                       30: " BOOT ERROR", 31: "BIOS BOOT", 32: "OS STATUS", 34: "ACPI STATUS", 35: "IPMI WATCHDOG",
                       39: "LAN", 40: "SUB SYSTEM", 201: "BIOS OPTIONS", 208: "GPU", 209: "RAID", 210: "FW UPDATE",
                       211: "SYSTEM", 212: "SYSTEM HOT", 213: "SNMP TEST"}
        res = ResultBean()
        if result.State:
            data = collections.OrderedDict()
            trap = result.Message.get('SnmpTrapNotification', {})
            snmpVer = trap.get('TrapVersion', 'Disabled')
            if snmpVer == "Disable":
                data['Enable'] = "Disabled"
            else:
                version_dict = {"V1": "V1", "V2": "V2", "V3": "V3", "V2C": "V2"}
                data['Enable'] = "Enabled"
                data['TrapVersion'] = version_dict.get(trap.get('TrapVersion', 'N/A'), trap.get('TrapVersion', 'N/A'))
                data['EventSeverity'] = trap.get('EventLevelLimit', 'N/A')
                data['HostId'] = trap.get('HostID', 'N/A')
                if data.get('TrapVersion') == "V3":
                    data['UserName'] = trap.get('UserName', 'N/A')
                    data['DeviceType'] = device_dict.get(trap.get('DeviceType', 'N/A'), trap.get('DeviceType', 'N/A'))
                    data['EngineID'] = trap.get('EngineID', 'N/A')
                    data['AUTHProtocol'] = trap.get('AuthProtocol', 'N/A')
                    # data['AuthPasswd'] = '-'
                    data['PRIVProtocol'] = trap.get('PrivProtocol', 'N/A')
                    # data['PrivPasswd'] = '-'
                # else:
                #     data['Community'] = '-'
                trap_server = trap.get('TrapServer', [])
                server_info = []
                if isinstance(trap_server, list) and len(trap_server) > 0:
                    for item in trap_server:
                        single_server = collections.OrderedDict()
                        if item.get('Destination') is not None and item.get('Destination', "") != "":
                            single_server['No.'] = str(int(item.get("Id")) + 1)
                            single_server["Status"] = "Enabled" if item.get("Enabled") else "Disabled"
                            single_server["Address"] = item.get("Destination")
                            single_server["Port"] = item.get("Port")
                            server_info.append(single_server)
                data['TrapServer'] = server_info
            res.State("Success")
            res.Message(data)
        else:
            res = result
        return res

    def setsnmptrap(self, client, args):

        def patch_func(data, responses):
            get_data = responses.json()
            trapinfo = get_data.get("SnmpTrapNotification", {})
            current_version = trapinfo.get("TrapVersion")
            if data.get("TrapVersion"):
                future_version = data.get("TrapVersion")
            else:
                future_version = current_version
                if future_version == "V2C":
                    future_version = "V2"
            if future_version == "V1" or future_version == "V2":
                if not (current_version == "V1" or current_version == "V2" or current_version == "V2C"):
                    if not data.get("Community"):
                        return ResultBean.fail('please input community for v1/v2c.')
                    data["TrapVersion"] = future_version
            elif future_version == "V3":
                if current_version != future_version:
                    # 从非V3 改为V3
                    # UserName EngineID 必须输入
                    # AuthProtocol如果不是NONE 则必须输入AuthPassword，且此时
                    #    PrivProtocol如果不是NONE PrivPassword
                    # AuthProtocol如果是NONE 或者没输入 啥事没有
                    if not data.get("UserName"):
                        return ResultBean.fail('please input username for v3.')
                    # EngineID可以为空了
                    # if not data.get("EngineID"):
                    #     return ResultBean.fail('please input engineId for v3.')
                    # AuthProtocol如果没输入则自动补全为NONE
                    if not data.get("AuthProtocol"):
                        data["AuthProtocol"] = "NONE"
                        data["PrivProtocol"] = "NONE"
                    else:
                        # AuthProtocol如果输入则判断是否为NONE 是-PrivProtocol也补为NONE
                        if data.get("AuthProtocol") == "NONE":
                            data["PrivProtocol"] = "NONE"
                        else:
                            # AuthProtocol不为NONE 则首先判断AuthPassword是否输入
                            if not data.get("AuthPassword"):
                                return ResultBean.fail('please input authentication password.')
                            if len(data.get("AuthPassword")) < 8 or len(data.get("AuthPassword")) > 16:
                                return ResultBean.fail('the length of authentication password should between 8 and 16.')
                            # 判断是否输入PrivProtocol 否-补全为NONE
                            if not data.get("PrivProtocol"):
                                data["PrivProtocol"] = "NONE"
                            else:
                                # 输入PrivProtocol 判断是否为NONE 否-判断PrivPassword是否输入
                                if data.get("PrivProtocol") != 'NONE':
                                    if not data.get("PrivPassword"):
                                        return ResultBean.fail('please input encryption password.')
                                    if len(data.get("PrivPassword")) < 8 or len(data.get("PrivPassword")) > 16:
                                        return ResultBean.fail(
                                            'the length of encryption password should between 8 and 16.')
                    data["TrapVersion"] = future_version
                else:
                    # 原本就是V3
                    # UserName EngineID 可以不输
                    # 新的AuthProtocol如果不是NONE 则必须输入AuthPassword，且此时
                    #    新的PrivProtocol如果不是NONE PrivPassword
                    # AuthProtocol如果是NONE 或者没输入 啥事没有
                    authflag = False
                    if data.get("AuthProtocol") == "SHA" or data.get("AuthProtocol") == "MD5" \
                            or data.get("AuthProtocol") == "SHA256" or data.get("AuthProtocol") == "SHA384" \
                            or data.get("AuthProtocol") == "SHA512":
                        authflag = True
                    elif data.get("AuthProtocol") == "NONE":
                        pass
                    else:
                        if trapinfo.get("AuthProtocol") == "SHA" or trapinfo.get("AuthProtocol") == "MD5" \
                                or trapinfo.get("AuthProtocol") == "SHA256" or trapinfo.get("AuthProtocol") == "SHA384" \
                                or trapinfo.get("AuthProtocol") == "SHA512":
                            authflag = True
                    if authflag:
                        if not data.get("AuthPassword") and data.get("AuthProtocol"):
                            return ResultBean.fail('please input authentication password.')
                        privflag = False
                        if data.get("AuthProtocol") == "AES" or data.get("AuthProtocol") == "DES" \
                            or data.get("AuthProtocol") == "AES256":
                            privflag = True
                        elif data.get("AuthProtocol") == "NONE":
                            pass
                        else:
                            if trapinfo.get("PrivProtocol") == "AES" or trapinfo.get("PrivProtocol") == "DES" \
                                    or trapinfo.get("AuthProtocol") == "AES256":
                                privflag = True
                        if privflag:
                            if not data.get("PrivPassword") and data.get("PrivProtocol"):
                                return ResultBean.fail('please input encryption password.')
            else:
                # disabled
                pass
            patch_body = {"SnmpTrapNotification": data}
            return ResultBean.success(patch_body)

        data = {}
        # 前期的处理 可以直接判断的情况
        if args.version == 1 or args.version == 2:
            if args.version == 1:
                data["TrapVersion"] = "V1"
            else:
                data["TrapVersion"] = "V2C"
            if not args.community:
                return ResultBean.fail('please input community.')
        elif args.version == 3:
            data["TrapVersion"] = "V3"
            # 如果此时有加密 则需要输入密码
            if args.authProtocol and args.authProtocol != 'NONE':
                if not args.authPassword:
                    return ResultBean.fail('please input authentication password.')
                if len(args.authPassword) < 8 or len(args.authPassword) > 16:
                    return ResultBean.fail('the length of authentication password should between 8 and 16.')
                if args.privProtocol and args.privProtocol != 'NONE':
                    if args.privProtocol == "AES128":
                        return ResultBean.fail('The privacy field does not support AES128.')
                    if not args.privPassword:
                        return ResultBean.fail('please input encryption password.')
                    if len(args.privPassword) < 8 or len(args.privPassword) > 16:
                        return ResultBean.fail('the length of encryption password should between 8 and 16.')
        elif args.version == 0:
            data["TrapVersion"] = "Disable"

        event_dict = {
            'all':'Info',
            'warning': 'Warning',
            'critical': 'Critical'
        }
        # disabled时可以单独设置
        if args.eventSeverity:
            data["EventLevelLimit"] = event_dict.get(args.eventSeverity, 'Info')
        # disabled时可以单独设置
        if args.hostid:
            data["HostID"] = args.hostid
        if args.version == 1 or args.version == 2:
            # V1V2
            if args.community:
                data["Community"] = args.community
        elif args.version == 3:
            # V3
            if args.v3username:
                data["UserName"] = args.v3username
                if len(args.v3username) > 16:
                    return ResultBean.fail('the length of username should between 1 and 16.')
            if args.engineId:
                data["EngineID"] = args.engineId
                if len(args.engineId) % 2 != 0 or not re.fullmatch('^[0-9a-f]{10,48}$', args.engineId, re.I):
                    return ResultBean.fail('the engine id should be an even-length hex sequences of 10 to 48.')
            if args.authProtocol:
                data["AuthProtocol"] = args.authProtocol
            if args.authPassword:
                data["AuthPassword"] = args.authPassword
                if len(data.get("AuthPassword")) < 8 or len(data.get("AuthPassword")) > 16:
                    return ResultBean.fail('the length of authentication password should between 8 and 16.')
            if args.privProtocol:
                data["PrivProtocol"] = args.privProtocol
            if args.privPassword:
                data["PrivPassword"] = args.privPassword
                if len(args.privPassword) < 8 or len(args.privPassword) > 16:
                    return ResultBean.fail('the length of encryption password should between 8 and 16.')

        url_result = self.get_url_info("settrap")
        patchBody = {}
        patchBody['url'] = str(url_result.get('url'))
        patchBody['func'] = patch_func
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        res = ResultBean()
        if result.State:
            res.State('Success')
            res.Message('Set snmp trap successfully.')
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getalertpolicy(self, client, args):
        url_result = self.get_url_info("gettrap")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            aps = []
            trap = result.Message.get('SnmpTrapNotification', {})
            trapServers = trap.get('TrapServer', [])
            for trapServer in trapServers:
                ap = collections.OrderedDict()
                ap["No."] = str(int(trapServer.get("Id")) + 1)
                ap["Status"] = "Enabled" if trapServer.get("Enabled") else "Disabled"
                ap["Address"] = trapServer.get("Destination")
                ap["Port"] = trapServer.get("Port")
                aps.append(ap)
            res.State("Success")
            res.Message({"Destination": aps})
        else:
            res = result
        return res

    def setalertpolicy(self, client, args):
        args.destinationid = args.id
        args.test = False
        if 'status' in args:
            args.enabled = args.status
        else:
            args.enabled = None
        if 'trap_port' in args:
            args.trapport = args.trap_port
        else:
            args.trapport = None
        if 'destination' in args:
            args.address = args.destination
        else:
            args.address = None
        alertinfo = self.settrapdest(client, args)
        return alertinfo

    def settrapdest(self, client, args):

        if args.test:
            param = {"Id": args.destinationid}
            url_test = self.get_url_info("testsnmp")
            postBody = {}
            postBody['url'] = str(url_test.get('url'))
            postBody['json'] = param
            testres = RedfishTemplate.post_for_object(client, postBody)
            testtrap = ResultBean()
            if testres.State:
                testtrap.State("Success")
                testtrap.Message("test BMC alert policy settings success")
            else:
                testtrap.State("Failure")
                testtrap.Message("test BMC alert policy settings failed. " + str(testres.Message))
            return testtrap

        def patch_func(data, responses):
            get_data = responses.json()
            dests = get_data.get("SnmpTrapNotification", {}).get("TrapServer", [])
            for dests in dests:
                if dests.get("Id") == data.get("Id") - 1:
                    if data.get("Enabled") is not None:
                        dests["Enabled"] = data['Enabled']
                    if data.get("Destination"):
                        dests["Destination"] = data['Destination']
                    if data.get("Port"):
                        dests["Port"] = data['Port']
                    trapserver = {"TrapServer": [dests]}
                    patch_body = {"SnmpTrapNotification": trapserver}
                    return ResultBean.success(patch_body)

        data = {}
        if args.destinationid:
            data['Id'] = args.destinationid
        if args.enabled:
            if args.enabled.lower() == "enable":
                data['Enabled'] = True
            else:
                data['Enabled'] = False

        if args.address:
            data['Destination'] = args.address
        if args.trapport is not None:
            if args.trapport < 1 or args.trapport > 65535:
                return ResultBean.fail('the length of trap port should between 1 and 65535.')
            data['Port'] = args.trapport
        url_result = self.get_url_info("settrap")
        patchBody = {}
        patchBody['url'] = str(url_result.get('url'))
        patchBody['func'] = patch_func
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        res = ResultBean()
        if result.State:
            res.State('Success')
            res.Message('Set trap destination successfully.')
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getsnmp(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            data = {}
            snmp = result.Message
            data['SnmpV1Enable'] = "Enabled" if snmp.get('SnmpV1Enable') else "Disabled"
            data['SnmpV2Enable'] = "Enabled" if snmp.get('SnmpV2CEnable') else "Disabled"
            data['SnmpV3Enable'] = "Enabled" if snmp.get('SnmpV3Enable') else "Disabled"
            data['AUTHProtocol'] = snmp.get('SnmpV3AuthProtocol', 'N/A')
            data['PrivProtocol'] = snmp.get('SnmpV3PrivProtocol', 'N/A')
            data['AUTHUserName'] = snmp.get('SnmpV3AuthUserName', 'N/A')
            res.State("Success")
            res.Message(data)
        else:
            res = result
        return res

    def setsnmp(self, client, args):
        def patch_func(data, responses):
            trapinfo = responses.json()
            if not data.get("SnmpV1Enable") is None or not data.get("SnmpV2CEnable") is None:
                if data.get("SnmpV1Enable") is None:
                    data["SnmpV1Enable"] = trapinfo.get("SnmpV1Enable")
                if data.get("SnmpV2CEnable") is None:
                    data["SnmpV2CEnable"] = trapinfo.get("SnmpV2CEnable")
                if data.get("SnmpV2CEnable") or data.get("SnmpV1Enable"):
                    if data.get("ReadOnlyCommunity") and data.get("ReadWriteCommunity"):
                        pass
                    else:
                        return ResultBean.fail('Community for v1/v2 is needed.')
            if data.get("SnmpV3Enable") is None:
                data["SnmpV3Enable"] = trapinfo.get("SnmpV3Enable")
            if data["SnmpV3Enable"]:
                if not data.get("SnmpV3AuthUserName"):
                    data["SnmpV3AuthUserName"] = trapinfo.get("SnmpV3AuthUserName")
                    if data["SnmpV3AuthUserName"] is None or data["SnmpV3AuthUserName"] == "":
                        return ResultBean.fail('UserName for v3 is needed.')

            return ResultBean.success(data)

        bool_dict = {
            'enable': True,
            'disable': False
        }
        data = {}
        if args.v1status:
            data["SnmpV1Enable"] = bool_dict[args.v1status]
        if args.v2status:
            data["SnmpV2CEnable"] = bool_dict[args.v2status]
        if args.v3status:
            data["SnmpV3Enable"] = bool_dict[args.v3status]
        if args.readCommunity:
            data["ReadOnlyCommunity"] = args.readCommunity
            if len(args.readCommunity) > 16 or len(args.readCommunity) < 1:
                return ResultBean.fail('the length of readonly community name should between 1 and 16.')
        if args.readWriteCommunity:
            data["ReadWriteCommunity"] = args.readWriteCommunity
            if len(args.readWriteCommunity) > 16 or len(args.readWriteCommunity) < 1:
                return ResultBean.fail('the length of readwrite community name should between 1 and 16.')
        # 不能相同
        if args.readCommunity and args.readWriteCommunity:
            if args.readCommunity == args.readWriteCommunity:
                return ResultBean.fail('readonly community name and readwrite community name can not be the same.')
        if args.authProtocol:
            data["SnmpV3AuthProtocol"] = args.authProtocol
        if args.authPassword:
            data["SnmpV3AuthPassword"] = args.authPassword
            if len(args.authPassword) < 8 or len(args.authPassword) > 23:
                return ResultBean.fail('the length of authentication password should between 8 and 23.')
        if args.v3username:
            data["SnmpV3AuthUserName"] = args.v3username
            if len(args.v3username) < 2 or len(args.v3username) > 16:
                return ResultBean.fail('the length of authentication username should between 2 and 16.')
        if args.privProtocol:
            data["SnmpV3PrivProtocol"] = args.privProtocol
        if args.privPassword:
            data["SnmpV3PrivPassword"] = args.privPassword
            if len(args.privPassword) < 8 or len(args.privPassword) > 23:
                return ResultBean.fail('the length of encryption password should between 8 and 23.')

        url_result = self.get_url_info("setsnmp")
        patchBody = {}
        patchBody['url'] = str(url_result.get('url'))
        patchBody['func'] = patch_func
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        res = ResultBean()
        if result.State:
            res.State('Success')
            res.Message('Set snmp successfully.')
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getnetwork(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        # 获取网口类型
        result_type = RedfishTemplate.get_for_object(client, [url_result.get('url')])
        interface_type = {}
        if result_type.State and result_type.Message.get(url_result.get('url')).State:
            interface_type = {member.get('@odata.id'): member.get('type') for member in
                              result_type.Message.get(url_result.get('url')).Message.get('Members', [])}
            # 获取网口具体信息
            result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
            if result.State:
                networks = result.Message
                data = []
                channel_dict = {
                    "shared": "8",  # eth1
                    "dedicated": "1",  # eth0
                    "bond": "1"  # eth0
                }
                for network in networks:
                    single_data = collections.OrderedDict()
                    single_data['InterfaceName'] = network.get('Id', 'N/A')
                    single_data['ChannelNum'] = channel_dict.get(interface_type.get(network.get('@odata.id', 'N/A'), 'N/A'), "N/A")
                    single_data['LanChannel'] = interface_type.get(network.get('@odata.id', 'N/A'), 'N/A')
                    single_data['MACAddress'] = network.get('PermanentMACAddress', 'N/A')
                    ipv4_dhcp = network.get('IPv4Addresses', [])[0].get('AddressOrigin', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'
                    if ipv4_dhcp is not None and ipv4_dhcp != "N/A":
                        ipv4_dhcp = str(ipv4_dhcp).lower()
                    single_data['Ipv4DhcpEnable'] = ipv4_dhcp
                    single_data['Ipv4Address'] = network.get('IPv4Addresses', [])[0].get('Address', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'
                    single_data['Ipv4Subnet'] = network.get('IPv4Addresses', [])[0].get('SubnetMask', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'
                    single_data['Ipv4Gateway'] = network.get('IPv4Addresses', [])[0].get('Gateway', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'

                    ipv6_dhcp = network.get('DHCPv6', {}).get('OperatingMode', 'N/A') if network.get('DHCPv6', {}) else 'N/A'
                    if ipv6_dhcp is not None and ipv6_dhcp != "N/A":
                        if "stateful" in str(ipv6_dhcp).lower():
                            ipv6_dhcp = "dhcp"
                            single_data['Ipv6DhcpEnable'] = ipv6_dhcp
                            dhcpAddress = network.get('IPv6Addresses', [])
                            count = 1
                            self.buildIPv6(count, dhcpAddress, single_data)
                            gateways = network.get('Oem', {}).get("Public", {}).get('IPv6DefaultGateways', [])
                            count = 1
                            for gateway in gateways:
                                single_data['Ipv6Gateway' + str(count)] = gateway.get('Address', 'N/A') if gateway.get('Address', 'N/A') else 'N/A'
                                count += 1
                        elif "disabled" in str(ipv6_dhcp).lower():
                            ipv6_dhcp = "static"
                            single_data['Ipv6DhcpEnable'] = ipv6_dhcp
                            dhcpAddress = network.get('IPv6Addresses', [])
                            count = 1
                            count = self.buildIPv6(count, dhcpAddress, single_data)
                            staticAddress = network.get('IPv6StaticAddresses', [])
                            self.buildIPv6(count, staticAddress, single_data)
                            gateways = network.get('IPv6StaticDefaultGateways', [])
                            count = 1
                            for gateway in gateways:
                                single_data['Ipv6Gateway' + str(count)] = gateway.get('Address', 'N/A') if gateway.get('Address', 'N/A') else 'N/A'
                                count += 1

                    single_data['VlanEnable'] = "enable" if network.get('VLAN', {}).get('VLANEnable', 'N/A') is True else "disable"
                    single_data['VlanId'] = network.get('VLAN', {}).get('VLANId', 'N/A')
                    data.append(single_data)
                res.State('Success')
                res.Message(data)
            else:
                res = result
        elif not result_type.State:
            res.Message(result_type.Message)
        elif not result_type.Message.get(url_result.get('url')).State:
            res.Message(result_type.Message.get(url_result.get('url')).Message)
        return res

    def buildIPv6(self, count, dhcpAddress, single_data):
        for addresss in dhcpAddress:
            single_data['Ipv6Address' + str(count)] = addresss.get('Address', 'N/A') if addresss else 'N/A'
            single_data['Ipv6Prefix' + str(count)] = addresss.get('PrefixLength', 'N/A') if addresss else 'N/A'
            single_data['Ipv6Origin' + str(count)] = addresss.get('AddressOrigin', 'N/A') if addresss else 'N/A'
            count += 1
        return count

    def setnet(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message(["Not Support"])
        return res

    def setipv4(self, client, args):
        ipinfo = ResultBean()
        interface_dict = {
            "shared": "eth1",
            "dedicated": "eth0",
            "bond0": "bond1"
        }
        url_result = self.get_url_info('getnetwork')
        result_type = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        interface_type = {}
        if result_type.State:
            interface_type = {str(member.get('@odata.id')).split("/")[-1]: member.get('@odata.id') for member in
                              result_type.Message.get('Members', [])}
            inter = interface_dict.get(args.interface_name, args.interface_name)
            if inter in interface_type.keys():
                result = RedfishTemplate.get_for_object_single(client, str(interface_type.get(inter)))
                if result.State:
                    enable_status = result.Message.get('Oem', {}).get('Public', {}).get('EnableStatus', None)
                    if not enable_status:
                        ipinfo.State("Failure")
                        ipinfo.Message(["get network enable status error "])
                        return ipinfo
                else:
                    ipinfo.State("Failure")
                    ipinfo.Message(["get " + args.interface_name + " error "])
                    return ipinfo
                if args.ipv4_status == 'disable':
                    if enable_status == 'ipv4':
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv6 is disable, ipv4 cannot be disable."])
                        return ipinfo
                    enable_status = 'ipv6'
                else:
                    if enable_status == 'ipv4':
                        enable_status = 'ipv4'
                    else:
                        enable_status = 'both'
                if enable_status == 'ipv6':
                    if args.ipv4_address is not None or args.ipv4_subnet is not None or args.ipv4_gateway is not None\
                            or args.ipv4_dhcp_enable is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv4 is disabled, please enable it first."])
                        return ipinfo
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                else:
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                    # 启用 ipv4 默认先启用 网络 lan_enable 固定为1
                    # IPV4 SETTING
                    if args.ipv4_dhcp_enable == "dhcp":
                        if args.ipv4_address is not None or args.ipv4_subnet is not None or args.ipv4_gateway is not None:
                            ipinfo.State("Failure")
                            ipinfo.Message(["'ip', 'subnet','gateway' is not active in DHCP mode."])
                            return ipinfo
                        data["IPv4Addresses"] = [{"AddressOrigin": "DHCP"}]
                    else:
                        static_info = {"AddressOrigin": "Static"}
                        if args.ipv4_address is not None:
                            if RegularCheckUtil.checkIP(args.ipv4_address):
                                ipv4_address = args.ipv4_address
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv4 IP address."])
                                return ipinfo
                            static_info["Address"] = ipv4_address
                        if args.ipv4_subnet is not None:
                            if RegularCheckUtil.checkSubnetMask(args.ipv4_subnet):
                                ipv4_subnet = args.ipv4_subnet
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv4 subnet mask."])
                                return ipinfo
                            static_info["SubnetMask"] = ipv4_subnet
                        if args.ipv4_gateway is not None:
                            if RegularCheckUtil.checkIP(args.ipv4_gateway):
                                ipv4_gateway = args.ipv4_gateway
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv4 default gateway."])
                                return ipinfo
                            static_info["Gateway"] = ipv4_gateway
                        data["IPv4Addresses"] = [static_info]
                patchBody = {}
                patchBody['url'] = str(interface_type.get(inter))
                patchBody['json'] = data
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    ipinfo.State('Success')
                    ipinfo.Message('')
                else:
                    ipinfo.State('Failure')
                    ipinfo.Message(str(set_result.Message))
                return ipinfo
            else:
                ipinfo.State("Failure")
                ipinfo.Message(["get " + args.interface_name + " error "])
                return ipinfo
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get " + args.interface_name + " error "])
            return ipinfo


    def setipv6(self, client, args):
        ipinfo = ResultBean()
        if not args.ipv6_status:
            ipinfo.State("Failure")
            ipinfo.Message(["The ipv6_status settings is not supported."])
            return ipinfo
        interface_dict = {
            "shared": "eth1",
            "dedicated": "eth0",
            "bond0": "bond1"
        }
        url_result = self.get_url_info('getnetwork')
        result_type = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        interface_type = {}
        if result_type.State:
            interface_type = {str(member.get('@odata.id')).split("/")[-1]: member.get('@odata.id') for member in
                              result_type.Message.get('Members', [])}
            inter = interface_dict.get(args.interface_name, args.interface_name)
            if inter in interface_type.keys():
                result = RedfishTemplate.get_for_object_single(client, str(interface_type.get(inter)))
                if result.State:
                    enable_status = result.Message.get('Oem', {}).get('Public', {}).get('EnableStatus', None)
                    if not enable_status:
                        ipinfo.State("Failure")
                        ipinfo.Message(["get network enable status error "])
                        return ipinfo
                else:
                    ipinfo.State("Failure")
                    ipinfo.Message(["get " + args.interface_name + " error "])
                    return ipinfo
                if args.ipv6_status == 'disable':
                    if enable_status == 'ipv6':
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv4 is disable, ipv6 cannot be disable."])
                        return ipinfo
                    enable_status = 'ipv4'
                else:
                    if enable_status == 'ipv6':
                        enable_status = 'ipv6'
                    else:
                        enable_status = 'both'
                if enable_status == 'ipv4':
                    if args.ipv6_address is not None or args.ipv6_index is not None or args.ipv6_gateway is not None\
                            or args.ipv6_prefix is not None or args.ipv6_dhcp_enable is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv6 is disabled, please enable it first."])
                        return ipinfo
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                else:
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                    # 启用 ipv6 默认先启用 网络 lan_enable 固定为1
                    # IPV6 SETTING
                    if args.ipv6_dhcp_enable == "dhcp":
                        if args.ipv6_address is not None or args.ipv6_index is not None or args.ipv6_gateway is not None\
                                or args.ipv6_prefix is not None:
                            ipinfo.State("Failure")
                            ipinfo.Message(
                                ["'ip', 'index','Subnet prefix length','gateway' is not active in DHCP mode."])
                            return ipinfo
                        data["IPv6Addresses"] = [{"AddressOrigin": "DHCPv6"}]
                    else:
                        static_info = {"AddressOrigin": "Static"}
                        data["IPv6Addresses"] = [static_info]
                        if args.ipv6_address is not None:
                            if RegularCheckUtil.checkIPv6(args.ipv6_address):
                                ipv6_address = args.ipv6_address
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 IP address."])
                                return ipinfo
                            static_info["Address"] = ipv6_address
                        if args.ipv6_gateway is not None:
                            if RegularCheckUtil.checkIPv6(args.ipv6_gateway):
                                ipv6_gateway = args.ipv6_gateway
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 default gateway."])
                                return ipinfo
                            gateway = {"Address": ipv6_gateway}
                            data["IPv6StaticDefaultGateways"] = [gateway]
                        if args.ipv6_index is not None:
                            if RegularCheckUtil.checkIndex(args.ipv6_index):
                                ipv6_index = args.ipv6_index
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 index(0-15)."])
                                return ipinfo
                        if args.ipv6_prefix is not None:
                            if RegularCheckUtil.checkPrefix(args.ipv6_prefix):
                                ipv6_prefix = args.ipv6_prefix
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 Subnet prefix length(0-128)."])
                                return ipinfo
                            static_info["PrefixLength"] = ipv6_prefix
                patchBody = {}
                patchBody['url'] = str(interface_type.get(inter))
                patchBody['json'] = data
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    ipinfo.State('Success')
                    ipinfo.Message('')
                else:
                    ipinfo.State('Failure')
                    ipinfo.Message(str(set_result.Message))
                return ipinfo
            else:
                ipinfo.State("Failure")
                ipinfo.Message(["get " + args.interface_name + " error "])
                return ipinfo
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get " + args.interface_name + " error "])
            return ipinfo

    def setvlan(self, client, args):
        ipinfo = ResultBean()
        interface_dict = {
            "shared": "eth1",
            "dedicated": "eth0"
        }
        url_result = self.get_url_info('getnetwork')
        result_type = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        interface_type = {}
        if result_type.State:
            interface_type = {str(member.get('@odata.id')).split("/")[-1]: member.get('@odata.id') for member in
                              result_type.Message.get('Members', [])}
            inter = interface_dict.get(args.interface_name, args.interface_name)
            if inter in interface_type.keys():
                if args.vlan_status == "disable":
                    if args.vlan_id is not None or args.vlan_priority is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["vlan is disabled, please enable it first."])
                        return ipinfo
                    vlan = {"VLANEnable": False}
                else:
                    vlan = {"VLANEnable": True}
                    if args.vlan_id is not None:
                        if args.vlan_id < 1 or args.vlan_id > 4094:
                            ipinfo.State("Failure")
                            ipinfo.Message(["vlan id should be 1-4094."])
                            return ipinfo
                        vlan["VLANId"] = args.vlan_id
                patchBody = {}
                patchBody['url'] = str(interface_type.get(inter))
                patchBody['json'] = {"VLAN": vlan}
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    ipinfo.State('Success')
                    ipinfo.Message('')
                else:
                    ipinfo.State('Failure')
                    ipinfo.Message(str(set_result.Message))
                return ipinfo
            else:
                ipinfo.State("Failure")
                ipinfo.Message(["get " + args.interface_name + " error "])
                return ipinfo
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get " + args.interface_name + " error "])
            return ipinfo

    def getad(self, client, args):
        res = ResultBean()
        url_service = self.get_url_info("getuserrule")
        result = RedfishTemplate.get_for_object_single(client, url_service.get('url'))
        if result.State:
            info = result.Message.get("ActiveDirectory", {})
            if info != {}:
                res_data = collections.OrderedDict()
                res_data['ActiveDirectoryAuthentication'] = "enable" if info.get('ServiceEnabled', False) else "disable"

                res_data['SecretName'] = info.get("Authentication", {}).get("Username", "N/A")
                res_data['UserDomainName'] = result.Message.get("Oem").get("Public").get("ActiveDirectory").get("UserDomainName")
                res_data['SSLEnable'] = "enable" if result.Message.get("Oem").get("Public").get("ActiveDirectory").get("SSLEnable") else "disable"
                ServiceAddresses = info.get("ServiceAddresses")
                if isinstance(ServiceAddresses, list) and len(ServiceAddresses) > 0:
                    head = "ldap://"
                    if result.Message.get("Oem").get("Public").get("ActiveDirectory").get("SSLEnable"):
                        head = "ldaps://"
                    if len(ServiceAddresses) == 1:
                        res_data['DomainControllerServerAddress1'] = str(ServiceAddresses[0]).replace(head, "").split(":")[0]
                        res_data['DomainControllerServerAddress2'] = "N/A"
                        res_data['DomainControllerServerAddress3'] = "N/A"
                    elif len(ServiceAddresses) == 2:
                        res_data['DomainControllerServerAddress1'] = str(ServiceAddresses[0]).replace(head, "").split(":")[0]
                        res_data['DomainControllerServerAddress2'] = str(ServiceAddresses[1]).replace(head, "").split(":")[0]
                        res_data['DomainControllerServerAddress3'] = "N/A"
                    elif len(ServiceAddresses) == 3:
                        res_data['DomainControllerServerAddress1'] = str(ServiceAddresses[0]).replace(head, "").split(":")[0]
                        res_data['DomainControllerServerAddress2'] = str(ServiceAddresses[1]).replace(head, "").split(":")[0]
                        res_data['DomainControllerServerAddress3'] = str(ServiceAddresses[2]).replace(head, "").split(":")[0]
                else:
                    res_data['DomainControllerServerAddress1'] = "N/A"
                    res_data['DomainControllerServerAddress2'] = "N/A"
                    res_data['DomainControllerServerAddress3'] = "N/A"
                res.State("Success")
                res.Message(res_data)
            else:
                res.State("Failure")
                res.Message("cannot find LDAP info.")
        else:
            res.State("Failure")
            res.Message("get ldap info failed, " + str(result.Message))
        return res

    def setad(self, client, args):

        def patch_info(raw_data, get_res):
            patch_res = ResultBean()
            try:
                # get的结果不管，因为直接patch会报错
                data = get_res.json()
                data_ldap = data.get("ActiveDirectory")
                data_auth = data.get("Oem")
                ldapaddr = data_ldap.get('ServiceAddresses')[0]
                if ldapaddr != "":
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    ipport = ip_port[1]
                    iphead = ldapaddr.split("//")[0]+"//"
                    ipaddr1 = ip_port[0]
                else:
                    iphead = "ldaps://"
                    ipport = "636"
                    ipaddr1 = ""
                # isRsa 判断
                if RestFunc.encrypt_type_flag == 1:
                    data_auth.get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
                    data_auth.get("Public")["EncryptFlag"] = True
                else:
                    data_auth.get("Public")["EncryptFlag"] = False
                    data_auth.get("Public")['CurrentPassword'] = args.passcode
                if args.enable is not None:
                    if args.enable == "enable":
                        data_ldap["ServiceEnabled"] = True
                    else:
                        data_ldap_new = {}
                        data_ldap_new["ServiceEnabled"] = False
                        data_new = {}
                        data_new["ActiveDirectory"] = data_ldap_new
                        data_auth.pop("OpenBMC")
                        data_auth.get("Public").pop("LDAP")
                        data_auth.get("Public").pop("PasswordRule")
                        data_auth.get("Public").get("ActiveDirectory").pop("Timeout")
                        if "@odata.id" in data_auth.get("Public").keys():
                            data_auth.get("Public").pop("@odata.id")
                        if "@odata.type" in data_auth.get("Public").keys():
                            data_auth.get("Public").pop("@odata.type")
                        data_new["Oem"] = data_auth
                        return patch_res.success(data_new)

                if args.code:
                    if len(args.code) < 6 or len(args.code) > 127:
                        return patch_res.fail("password is a string of 6 to 127 characters")
                    elif " " in str(args.code):
                        return patch_res.fail("spaces are not allowed in argument -PWD")
                    else:
                        if RestFunc.encrypt_type_flag == 1:
                            data_ldap.get("Authentication")['Password'] = RestFunc.encrypt_rsa(args.code, client.type)
                        else:
                            data_ldap.get("Authentication")['Password'] = args.code
                else:
                    return patch_res.fail("argument -PWD is required")
                if args.ssl_enable is not None:
                    if args.ssl_enable == "enable":
                        iphead = "ldaps://"
                        data_auth.get("Public").get("ActiveDirectory")['SSLEnable'] = True
                    else:
                        iphead = "ldap://"
                        data_auth.get("Public").get("ActiveDirectory")['SSLEnable'] = False
                if args.domain:
                    if len(args.domain) < 4 or len(args.domain) > 127:
                        return patch_res.fail("domain is a string of 4 to 127 alpha-numeric characters")
                    elif not args.domain[0].isalpha():
                        return patch_res.fail("-DOMAIN must start with an alphabetical character")
                    else:
                        data_auth.get("Public").get("ActiveDirectory")['UserDomainName'] = args.domain

                if args.addr1:
                    if RegularCheckUtil.checkIP(args.addr1) or RegularCheckUtil.checkIPv6(args.addr1):
                        ipaddr1 = args.addr1
                        data_ldap['ServiceAddresses'][0] = iphead + ipaddr1 + ":" + ipport
                    else:
                        return patch_res.fail("Invalid Server addr1. Please input an IPv4 or IPv6 address")

                if args.addr2:
                    if RegularCheckUtil.checkIP(args.addr2) or RegularCheckUtil.checkIPv6(args.addr2):
                        ipaddr2 = args.addr2
                        # 如果要设置addr2 则需要更新或者新加
                        if len(data_ldap['ServiceAddresses']) >= 2:
                            data_ldap['ServiceAddresses'][1] = iphead + ipaddr2 + ":" + ipport
                        elif len(data_ldap['ServiceAddresses']) == 1:
                            data_ldap['ServiceAddresses'].append(iphead + ipaddr2 + ":" + ipport)
                    else:
                        return patch_res.fail("Invalid Server addr2. Please input an IPv4 or IPv6 address")
                if args.addr3:
                    if RegularCheckUtil.checkIP(args.addr3) or RegularCheckUtil.checkIPv6(args.addr3):
                        ipaddr3 = args.addr3
                        # 如果要设置addr3 则需要更新或者新加
                        if len(data_ldap['ServiceAddresses']) >= 3:
                            data_ldap['ServiceAddresses'][2] = iphead + ipaddr3 + ":" + ipport
                        else:
                            data_ldap['ServiceAddresses'].append(iphead + ipaddr3 + ":" + ipport)
                    else:
                        return patch_res.fail("Invalid Server addr3. Please input an IPv4 or IPv6 address")

                if len(data_ldap['ServiceAddresses']) == 1:
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldap://", iphead)
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldaps://", iphead)
                if len(data_ldap['ServiceAddresses']) == 2:
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldap://", iphead)
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldap://", iphead)
                if len(data_ldap['ServiceAddresses']) == 3:
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldap://", iphead)
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldap://", iphead)
                    data_ldap['ServiceAddresses'][2] = data_ldap['ServiceAddresses'][2].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][2] = data_ldap['ServiceAddresses'][2].replace("ldap://", iphead)
                if args.name:
                    if len(args.name) < 6 or len(args.name) > 283:
                        return patch_res.fail("name is a string of 6 to 283 alpha-numeric characters")
                    elif not str(args.name).startswith('cn=') and not str(args.name).startswith('uid='):
                        return patch_res.fail("name must start with 'cn=' or 'uid='")
                    else:
                        data_ldap.get("Authentication")['Username'] = args.name
                data_ldap.get("Authentication").pop("AuthenticationType")
                data_ldap.pop("RemoteRoleMapping")
                data_ldap.pop("LDAPService")
                data_auth.pop("OpenBMC")
                data_auth.get("Public").pop("LDAP")
                data_auth.get("Public").pop("PasswordRule")
                data_auth.get("Public").get("ActiveDirectory").pop("Timeout")
                if "@odata.id" in data_auth.get("Public").keys():
                    data_auth.get("Public").pop("@odata.id")
                if "@odata.type" in data_auth.get("Public").keys():
                    data_auth.get("Public").pop("@odata.type")
                data_new = {}
                data_new["ActiveDirectory"] = data_ldap
                data_new["Oem"] = data_auth
                return patch_res.success(data_new)
            except Exception as e:
                return patch_res.fail(str(e))

        res = ResultBean()
        if args.enable is None and args.ssl_enable is None and args.addr1 is None and args.name is None and \
                args.domain is None and args.code is None and args.addr2 is None and args.addr3 is None:
            res.State("Failure")
            res.Message("please input one parameter at least.")
            return res
        url_get = self.get_url_info("getuserrule")
        url_get_res = RedfishTemplate.get_for_object_single(client, url_get.get('url'))
        if url_get_res.State:
            data = url_get_res.Message.get("ActiveDirectory")
            if data['ServiceEnabled'] == False and args.enable is None:
                res.State("Failure")
                res.Message("please enable ad status first.")
                return res
            if data['ServiceEnabled'] == False and args.enable is not None and args.enable == "disable":
                res.State("Success")
                res.Message("")
                return res
            url_info_set = self.get_url_info("setuserrule")
            patchBody = {}
            patchBody['url'] = url_info_set.get("url")
            patchBody['func'] = patch_info
            set_info_res = RedfishTemplate.patch_for_object(client, patchBody)
            if set_info_res.State:
                res.State("Success")
                res.Message("")
            else:
                res.State("Failure")
                res.Message(set_info_res.Message)

        else:
            res.State("Failure")
            res.Message(url_get_res.Message)
        return res

    def getadgroup(self, client, args):
        url_status = self.get_url_info("getuserrule")
        res = ResultBean()
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State is False:
            res.State("Failure")
            res.Message(status_result.Message)
            return res
        info = status_result.Message.get("ActiveDirectory").get("RemoteRoleMapping")
        data_sum = []
        for item in info:
            itemdict = item.get("Oem").get("Public")
            single_data = collections.OrderedDict()
            single_data['GroupID'] = itemdict.get('id', "N/A")
            single_data['GroupName'] = item.get('RemoteGroup', "N/A")
            single_data['GroupSearchBase'] = itemdict.get('Domain', "N/A")
            single_data['GroupPrivilege'] = item.get('LocalRole', "N/A")
            single_data['KVMAccess'] = "enable" if itemdict.get('KVMS', False) else "disable"
            single_data['VMediaAccess'] = "enable" if itemdict.get('Vmedia',False) else "disable"
            single_data['SSHAccess'] = "enable" if itemdict.get('SSH',False) else "disable"
            single_data['WEBAccess'] = "enable" if itemdict.get('WEB',False) else "disable"

            data_sum.append(single_data)
        res.State("Success")
        res.Message(data_sum)

        return res

    def addadgroup(self, client, args):
        def checkGroupName(name):
            # 角色组名称是一个64字母数字组成的字串。
            # 允许特殊字符如连字符和下划线。
            dn = '^[\da-zA-Z\-_]{1,64}$'
            if re.search(dn, name, re.I):
                return True
            return False

        def checkDoamin(s):
            # 域名名称是一个5-127字母数字组成的字串。
            # 开头字符必须是字母。
            # 允许特殊字符如点(.)，逗号(,)，连字符(-)，下划线(_)，等于号(=)。
            # 范例: cn=manager,ou=login, dc=domain,dc=com
            dn = '^[a-zA-Z][a-zA-Z\-_\.\,\=]{5,127}$'
            if re.search(dn, s, re.I):
                return True
            return False

        url_status = self.get_url_info("getuserrule")
        res = ResultBean()
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State:
            status = status_result.Message.get("ActiveDirectory").get("ServiceEnabled")
            if status is False:
                res.State("Failure")
                res.Message("ad status is disable.")
                return res
        else:
            res.State("Failure")
            res.Message(status_result.Message)
            return res

        info = status_result.Message.get("ActiveDirectory").get("RemoteRoleMapping")
        set_data = {}
        id = -1
        for i in range(0, len(info)):
            # 重名
            item = info[i]
            if item.get("RemoteGroup") == args.name:
                res.State("Failure")
                res.Message('group ' + args.name + ' already exists, please use setADgroup method')
                return res
        for i in range(0,len(info)):
            item = info[i]
            # if args.id is not None:
            #     if str(item.get("Oem").get("Public").get("id")) == args.id:
            #         set_data = item
            #         id = i
            #         break
            #
            # else:
            # 找到空余ID可添加
            if item.get("RemoteGroup") == "":
                set_data = item
                id = i
                break
        if set_data == {} or id == -1:
            res.State("Failure")
            res.Message("cannot get group id")
            return res
        if checkDoamin(args.domain):
            set_data.get("Oem").get("Public")['Domain'] = args.domain
        else:
            res.State("Failure")
            res.Message(
                'Domain Name is a string of 5 to 127 alpha-numeric characters.It must start with an alphabetical character.Special Symbols like dot(.), comma(,), hyphen(-), underscore(_), equal-to(=) are allowed.Example: cn=manager,ou=login,dc=domain,dc=com')
            return res

        if checkGroupName(args.name):
            set_data['RemoteGroup'] = args.name
        else:
            res.State("Failure")
            res.Message(
                'Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.')
            return res
        set_data['LocalRole'] = args.pri.title()
        set_data.get("Oem").get("Public")['KVMS'] = True if args.kvm=="enable" else False
        set_data.get("Oem").get("Public")['Vmedia'] =  True if args.vm=="enable" else False
        set_data.get("Oem").get("Public")['SSH'] = True
        set_data.get("Oem").get("Public")['WEB'] = True
        if "@odata.id" in set_data.get("Oem").get("Public").keys():
            set_data.get("Oem").get("Public").pop("@odata.id")
        if "@odata.type" in set_data.get("Oem").get("Public").keys():
            set_data.get("Oem").get("Public").pop("@odata.type")


        url_result = self.get_url_info("setuserrule")
        patchBody = {}
        patchBody['url'] = url_result.get("url")

        set_data_list = []
        for i in range(0,len(info)):
            if i == id:
                set_data_list.append(set_data)
            else:
                set_data_list.append({})
        data = {"ActiveDirectory":{"RemoteRoleMapping":set_data_list},"Oem":{"Public":{}}}
        if RestFunc.encrypt_type_flag == 1:
            data.get("Oem").get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
            data.get("Oem").get("Public")["EncryptFlag"] = True
        else:
            data.get("Oem").get("Public")["EncryptFlag"] = False
            data.get("Oem").get("Public")['CurrentPassword'] = args.passcode

        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)

        return res

    def setadgroup(self, client, args):
        def checkGroupName(name):
            # 角色组名称是一个64字母数字组成的字串。
            # 允许特殊字符如连字符和下划线。
            dn = '^[\da-zA-Z\-_]{1,64}$'
            if re.search(dn, name, re.I):
                return True
            return False

        def checkDoamin(s):
            # 域名名称是一个4-127字母数字组成的字串。
            # 开头字符必须是字母。
            # 允许特殊字符如点(.)，逗号(,)，连字符(-)，下划线(_)，等于号(=)。
            # 范例: cn=manager,ou=login, dc=domain,dc=com
            dn = '^[a-zA-Z][a-zA-Z\-_\.\,\=]{5,127}$'
            if re.search(dn, s, re.I):
                return True
            return False

        res = ResultBean()
        if args.name is None and args.domain is None and args.pri is None and args.kvm is None and args.vm is None:
            res.State("Failure")
            res.Message("please input one parameter at least.")
            return res
        url_status = self.get_url_info("getuserrule")
        res = ResultBean()
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State:
            status = status_result.Message.get("ActiveDirectory").get("ServiceEnabled")
            if status is False:
                res.State("Failure")
                res.Message("ad status is disable.")
                return res
        else:
            res.State("Failure")
            res.Message(status_result.Message)
            return res

        info = status_result.Message.get("ActiveDirectory").get("RemoteRoleMapping")
        data = {}
        id = -1
        for i in range(0,len(info)):
            item = info[i]
            if str(item.get("Oem").get("Public").get("id")) == args.id:
                data = item
                id = i
                break
        if data == {} or id == -1:
            res.State("Failure")
            res.Message("cannot get group id")
            return res
        if data.get('RemoteGroup') is None:
            res.State("Failure")
            res.Message("group " + str(args.id) + " not exist, please use addLDAPgroup method")
            return res

        if args.domain is not None:
            if checkDoamin(args.domain):
                data.get("Oem").get("Public")['Domain'] = args.domain
            else:
                res.State("Failure")
                res.Message(
                    'Domain Name is a string of 5 to 127 alpha-numeric characters.It must start with an alphabetical character.Special Symbols like dot(.), comma(,), hyphen(-), underscore(_), equal-to(=) are allowed.Example: cn=manager,ou=login,dc=domain,dc=com')
                return res
        if args.name is not None:
            if checkGroupName(args.name):
                data['RemoteGroup'] = args.name
            else:
                res.State("Failure")
                res.Message(
                    'Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.')
                return res
        if args.pri is not None:
            data['LocalRole'] = args.pri.title()
        if args.kvm is not None:
            data.get("Oem").get("Public")['KVMS'] = True if args.kvm=="enable" else False

        if args.vm is not None:
            data.get("Oem").get("Public")['Vmedia'] = True if args.vm == "enable" else False
        if "@odata.id" in data.get("Oem").get("Public").keys():
            data.get("Oem").get("Public").pop("@odata.id")
        if "@odata.type" in data.get("Oem").get("Public").keys():
            data.get("Oem").get("Public").pop("@odata.type")
        url_result = self.get_url_info("setuserrule")
        patchBody = {}
        patchBody['url'] = url_result.get("url")
        set_data_list = []
        for i in range(0, len(info)):
            if i == id:
                set_data_list.append(data)
            else:
                set_data_list.append({})
        set_data = {"ActiveDirectory": {"RemoteRoleMapping": set_data_list}, "Oem": {"Public": {}}}
        if RestFunc.encrypt_type_flag == 1:
            set_data.get("Oem").get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
            set_data.get("Oem").get("Public")["EncryptFlag"] = True
        else:
            set_data.get("Oem").get("Public")["EncryptFlag"] = False
            set_data.get("Oem").get("Public")['CurrentPassword'] = args.passcode

        patchBody['json'] = set_data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)

        return res

    def deladgroup(self, client, args):
        res = ResultBean()
        if args.name is None and args.domain is None and args.pri is None and args.kvm is None and args.vm is None:
            res.State("Failure")
            res.Message("please input one parameter at least.")
            return res
        url_status = self.get_url_info("getuserrule")
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State:
            status = status_result.Message.get("ActiveDirectory").get("ServiceEnabled")
            if status is False:
                res.State("Failure")
                res.Message("ldap status is disable.")
                return res
        else:
            res.State("Failure")
            res.Message(status_result.Message)
            return res

        info = status_result.Message.get("ActiveDirectory").get("RemoteRoleMapping")
        id = -1
        for i in range(0, len(info)):
            item = info[i]
            if str(item.get("RemoteGroup")) == args.name:
                id = i
                break
        if id == -1:
            res.State("Failure")
            res.Message(str(args.name) + " not exist")
            return res
        url_result = self.get_url_info("setuserrule")
        patchBody = {}
        patchBody['url'] = url_result.get("url")
        set_data_list = []
        for i in range(0, len(info)):
            if i == id:
                set_data_list.append(None)
            else:
                set_data_list.append({})
        set_data = {"ActiveDirectory": {"RemoteRoleMapping": set_data_list}, "Oem": {"Public": {}}}
        if RestFunc.encrypt_type_flag == 1:
            set_data.get("Oem").get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
            set_data.get("Oem").get("Public")["EncryptFlag"] = True
        else:
            set_data.get("Oem").get("Public")["EncryptFlag"] = False
            set_data.get("Oem").get("Public")['CurrentPassword'] = args.passcode

        patchBody['json'] = set_data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)

        return res

    def getldap(self, client, args):
        res = ResultBean()
        url_service = self.get_url_info("getuserrule")
        result = RedfishTemplate.get_for_object_single(client, url_service.get('url'))
        if result.State:
            data = result.Message.get("LDAP")
            res_data = collections.OrderedDict()
            state_dict = {
                True: "enable",
                False: "disable"
            }
            res_data['AuthenState'] = state_dict.get(data.get('ServiceEnabled', False))
            res_data['Encryption'] = result.Message.get("Oem").get("Public").get("LDAP").get('EncryptionType', "N/A")
            res_data['CommonNameType'] = result.Message.get("Oem").get("Public").get("LDAP").get('CommonNameType',
                                                                                                 "N/A")

            if len(data.get('ServiceAddresses')) == 1:
                if data.get('ServiceAddresses')[0] != "":
                    ldapaddr = data.get('ServiceAddresses')[0]
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    res_data['ServerAddress'] = ip_port[0]
                    res_data['Port'] = ip_port[1]
            elif len(data.get('ServiceAddresses')) == 2:
                if data.get('ServiceAddresses')[0] != "":
                    ldapaddr = data.get('ServiceAddresses')[0]
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    res_data['ServerAddress1'] = ip_port[0]
                    res_data['Port'] = ip_port[1]
                if data.get('ServiceAddresses')[1] != "":
                    ldapaddr = data.get('ServiceAddresses')[1]
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    res_data['ServerAddress2'] = ip_port[0]
            elif len(data.get('ServiceAddresses')) == 3:
                if data.get('ServiceAddresses')[0] != "":
                    ldapaddr = data.get('ServiceAddresses')[0]
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    res_data['ServerAddress1'] = ip_port[0]
                    res_data['Port'] = ip_port[1]
                if data.get('ServiceAddresses')[1] != "":
                    ldapaddr = data.get('ServiceAddresses')[1]
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    res_data['ServerAddress2'] = ip_port[0]
                if data.get('ServiceAddresses')[2] != "":
                    ldapaddr = data.get('ServiceAddresses')[2]
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    res_data['ServerAddress2'] = ip_port[0]
            res_data['SearchBase'] = data.get('LDAPService').get("SearchSettings").get("BaseDistinguishedNames")[0]
            res_data['BindDN'] = data.get('Authentication').get("Username", "N/A")
            res_data['LoginAttr'] = data.get('LDAPService').get("SearchSettings").get('UsernameAttribute', "N/A")

            res.State("Success")
            res.Message(res_data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def setldap(self, client, args):

        def patch_info(raw_data, get_res):
            patch_res = ResultBean()
            try:
                # get的结果不管，因为直接patch会报错
                data = get_res.json()
                data_ldap = data.get("LDAP")
                data_auth = data.get("Oem")
                ldapaddr = data_ldap.get('ServiceAddresses')[0]
                if ldapaddr != "":
                    ips = ldapaddr.split("//")[1]
                    ip_port = ips.split(":")
                    ipport = ip_port[1]
                    iphead = ldapaddr.split("//")[0]+"//"
                    ipaddr = ip_port[0]
                else:
                    iphead = "ldap://"
                    ipport = "636"
                    ipaddr = ""
                # isRsa 判断
                if RestFunc.encrypt_type_flag == 1:
                    data_auth.get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
                    data_auth.get("Public")["EncryptFlag"] = True
                else:
                    data_auth.get("Public")["EncryptFlag"] = False
                    data_auth.get("Public")['CurrentPassword'] = args.passcode
                if args.enable is not None:
                    if args.enable == "enable":
                        data_ldap["ServiceEnabled"] = True
                    else:
                        data_ldap_new = {}
                        data_ldap_new["ServiceEnabled"] = False
                        data_new = {}
                        data_new["LDAP"] = data_ldap_new
                        data_auth.pop("OpenBMC")
                        data_auth.get("Public").pop("ActiveDirectory")
                        data_auth.get("Public").pop("PasswordRule")
                        if "@odata.id" in data_auth.get("Public").keys():
                            data_auth.get("Public").pop("@odata.id")
                        if "@odata.type" in data_auth.get("Public").keys():
                            data_auth.get("Public").pop("@odata.type")
                        data_new["Oem"] = data_auth
                        return patch_res.success(data_new)
                if args.code:
                    if len(args.code) < 1 or len(args.code) > 48:
                        return patch_res.fail("password is a string of 1 to 48 characters")
                    elif " " in str(args.code):
                        return patch_res.fail("spaces are not allowed in argument -PWD")
                    else:
                        if RestFunc.encrypt_type_flag == 1:
                            data_ldap.get("Authentication")['Password'] = RestFunc.encrypt_rsa(args.code, client.type)
                        else:
                            data_ldap.get("Authentication")['Password'] = args.code
                else:
                    return patch_res.fail("argument -PWD is required")
                if args.encry:
                    encty_dict = {
                        'no': "None",
                        'SSL': "SSL",
                        'StartTLS': "TLS"
                    }
                    data_auth.get("Public").get("LDAP")['EncryptionType'] = encty_dict.get(args.encry)
                    if args.encry != "no":
                        iphead = "ldaps://"
                    else:
                        iphead = "ldap://"
                if data_auth.get("Public").get("LDAP")['EncryptionType'] != "None":
                    return patch_res.fail("only support encryption type(-E) is none(no).")

                if args.server_port is not None:
                    if args.server_port < 1 or args.server_port > 65535:
                        return patch_res.fail("argument -PORT range in 1-65535")
                    else:
                        ipport = str(args.server_port)

                if args.address:
                    if RegularCheckUtil.checkIP(args.address) or RegularCheckUtil.checkIPv6(args.address):
                        # ldapaddr = iphead + args.address + ipport
                        ipaddr = args.address
                        data_ldap['ServiceAddresses'][0] = iphead + ipaddr + ":" + ipport

                    else:
                        return patch_res.fail("Invalid Server Address. Please input an IPv4 or IPv6 address")

                        # ldapaddr = iphead + ipaddr +":"+args.server_port
                if len(data_ldap['ServiceAddresses']) == 1:
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldap://", iphead)
                    ip_port = data_ldap['ServiceAddresses'][0].split(":")
                    if len(ip_port) == 3:
                        data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace(
                            ":" + ip_port[len(ip_port) - 1], ":" + ipport)
                if len(data_ldap['ServiceAddresses']) == 2:
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldap://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldap://", iphead)
                    ip_port0 = data_ldap['ServiceAddresses'][0].split(":")
                    ip_port = data_ldap['ServiceAddresses'][1].split(":")
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace(
                        ":" + ip_port0[len(ip_port0) - 1], ":" + ipport)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace(
                        ":" + ip_port[len(ip_port) - 1], ":" + ipport)
                if len(data_ldap['ServiceAddresses']) == 3:
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace("ldap://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace("ldap://", iphead)
                    data_ldap['ServiceAddresses'][2] = data_ldap['ServiceAddresses'][2].replace("ldaps://", iphead)
                    data_ldap['ServiceAddresses'][2] = data_ldap['ServiceAddresses'][2].replace("ldap://", iphead)
                    ip_port0 = data_ldap['ServiceAddresses'][0].split(":")
                    ip_port1 = data_ldap['ServiceAddresses'][1].split(":")
                    ip_port2 = data_ldap['ServiceAddresses'][2].split(":")
                    data_ldap['ServiceAddresses'][0] = data_ldap['ServiceAddresses'][0].replace(
                        ":" + ip_port0[len(ip_port0) - 1], ":" + ipport)
                    data_ldap['ServiceAddresses'][1] = data_ldap['ServiceAddresses'][1].replace(
                        ":" + ip_port1[len(ip_port1) - 1], ":" + ipport)
                    data_ldap['ServiceAddresses'][2] = data_ldap['ServiceAddresses'][2].replace(
                        ":" + ip_port2[len(ip_port2) - 1], ":" + ipport)
                if len(data_ldap['ServiceAddresses']) == 0 or (len(data_ldap['ServiceAddresses'])==1 and data_ldap['ServiceAddresses'][0] == "" ):
                    return patch_res.fail("please input -ADDR.")
                if args.dn:
                    if len(args.dn) < 6 or len(args.dn) > 283:
                        return patch_res.fail("Bind DN is a string of 6 to 283 alpha-numeric characters")
                    elif not str(args.dn).startswith('cn=') and not str(args.dn).startswith('uid='):
                        return patch_res.fail("Bind DN must start with 'cn=' or 'uid='")
                    else:
                        data_ldap.get("Authentication")['Username'] = args.dn
                if len(data_ldap.get("Authentication")['Username'])==0:
                    return patch_res.fail("please input -DN.")
                if args.base:
                    if len(args.base) < 4 or len(args.base) > 127:
                        return patch_res.fail("Search base is a string of 4 to 127 alpha-numeric characters")
                    elif not args.base[0].isalpha():
                        return patch_res.fail("-BASE must start with an alphabetical character")
                    else:
                        data_ldap.get("LDAPService").get("SearchSettings")['BaseDistinguishedNames'][0] = args.base
                if len(data_ldap.get("LDAPService").get("SearchSettings")['BaseDistinguishedNames'])==0 or (len(data_ldap.get("LDAPService").get("SearchSettings")['BaseDistinguishedNames'])==1 and data_ldap.get("LDAPService").get("SearchSettings")['BaseDistinguishedNames'][0] == "" ):
                    return patch_res.fail("please input -BASE.")
                if args.attr:
                    data_ldap.get("LDAPService").get("SearchSettings")['UsernameAttribute'] = args.attr
                if args.cn:
                    data_auth.get("Public").get("LDAP")['CommonNameType'] = str(args.cn).upper()
                data_ldap.pop("Certificates")
                data_ldap.pop("RemoteRoleMapping")
                data_auth.pop("OpenBMC")
                data_auth.get("Public").pop("ActiveDirectory")
                data_auth.get("Public").pop("PasswordRule")
                if "@odata.id" in data_auth.get("Public").keys():
                    data_auth.get("Public").pop("@odata.id")
                if "@odata.type" in data_auth.get("Public").keys():
                    data_auth.get("Public").pop("@odata.type")
                data_new = {}
                data_new["LDAP"] = data_ldap
                data_new["Oem"] = data_auth
                return patch_res.success(data_new)
            except Exception as e:
                return patch_res.fail(str(e))

        res = ResultBean()
        if args.enable is None and args.encry is None and args.address is None and args.server_port is None and \
                args.dn is None and args.code is None and args.base is None and args.attr is None and args.cn is None:
            res.State("Failure")
            res.Message("please input one parameter at least.")
            return res
        url_get = self.get_url_info("getuserrule")
        url_get_res = RedfishTemplate.get_for_object_single(client, url_get.get('url'))
        if url_get_res.State:
            data = url_get_res.Message.get("LDAP")
            if data['ServiceEnabled'] == False and args.enable is None:
                res.State("Failure")
                res.Message("please enable ldap status first.")
                return res
            if data['ServiceEnabled'] == False and args.enable is not None and args.enable == "disable":
                res.State("Success")
                res.Message("")
                return res
            url_info_set = self.get_url_info("setuserrule")
            patchBody = {}
            patchBody['url'] = url_info_set.get("url")
            patchBody['func'] = patch_info
            set_info_res = RedfishTemplate.patch_for_object(client, patchBody)
            if set_info_res.State:
                res.State("Success")
                res.Message("")
            else:
                res.State("Failure")
                res.Message(set_info_res.Message)
        else:
            res.State("Failure")
            res.Message(url_get_res.Message)
        return res

    def getldapgroup(self, client, args):
        url_status = self.get_url_info("getuserrule")
        res = ResultBean()
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State is False:
            res.State("Failure")
            res.Message(status_result.Message)
            return res
        info = status_result.Message.get("LDAP").get("RemoteRoleMapping")
        data_sum = []
        for item in info:
            itemdict = item.get("Oem").get("Public")
            single_data = collections.OrderedDict()
            single_data['GroupID'] = itemdict.get('id', "N/A")
            single_data['GroupName'] = item.get('RemoteGroup', "N/A")
            single_data['GroupSearchBase'] = itemdict.get('Domain', "N/A")
            single_data['GroupPrivilege'] = item.get('LocalRole', "N/A")
            single_data['KVMAccess'] = "enable" if itemdict.get('KVMS', False) else "disable"
            single_data['VMediaAccess'] = "enable" if itemdict.get('Vmedia',False) else "disable"
            single_data['SSHAccess'] = "enable" if itemdict.get('SSH',False) else "disable"
            single_data['WEBAccess'] = "enable" if itemdict.get('WEB',False) else "disable"
            data_sum.append(single_data)
        res.State("Success")
        res.Message(data_sum)
        return res

    def addldapgroup(self, client, args):
        def checkGroupName(name):
            # 角色组名称是一个64字母数字组成的字串。
            # 允许特殊字符如连字符和下划线。
            dn = '^[\da-zA-Z\-_]{1,64}$'
            if re.search(dn, name, re.I):
                return True
            return False

        def checkDoamin(s):
            # 域名名称是一个5-127字母数字组成的字串。
            # 开头字符必须是字母。
            # 允许特殊字符如点(.)，逗号(,)，连字符(-)，下划线(_)，等于号(=)。
            # 范例: cn=manager,ou=login, dc=domain,dc=com
            dn = '^[a-zA-Z][a-zA-Z\-_\.\,\=]{5,127}$'
            if re.search(dn, s, re.I):
                return True
            return False

        url_status = self.get_url_info("getuserrule")
        res = ResultBean()
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State:
            status = status_result.Message.get("LDAP").get("ServiceEnabled")
            if status is False:
                res.State("Failure")
                res.Message("ldap status is disable.")
                return res
        else:
            res.State("Failure")
            res.Message(status_result.Message)
            return res

        info = status_result.Message.get("LDAP").get("RemoteRoleMapping")
        set_data = {}
        id = -1
        for i in range(0, len(info)):
            # 重名
            item = info[i]
            if item.get("RemoteGroup") == args.name:
                res.State("Failure")
                res.Message('group ' + args.name + ' already exists, please use setLDAPgroup method')
                return res
        for i in range(0,len(info)):
            item = info[i]
            # if args.id is not None:
            #     if str(item.get("Oem").get("Public").get("id")) == args.id:
            #         set_data = item
            #         id = i
            #         break
            #
            # else:
            # 找到空余ID可添加
            if item.get("RemoteGroup") == "":
                set_data = item
                id = i
                break
        if set_data == {} or id == -1:
            res.State("Failure")
            res.Message("cannot get group id")
            return res
        if checkDoamin(args.base):
            set_data.get("Oem").get("Public")['Domain'] = args.base
        else:
            res.State("Failure")
            res.Message(
                'Domain Name is a string of 5 to 127 alpha-numeric characters.It must start with an alphabetical character.Special Symbols like dot(.), comma(,), hyphen(-), underscore(_), equal-to(=) are allowed.Example: cn=manager,ou=login,dc=domain,dc=com')
            return res

        if checkGroupName(args.name):
            set_data['RemoteGroup'] = args.name
        else:
            res.State("Failure")
            res.Message(
                'Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.')
            return res
        set_data['LocalRole'] = args.pri.title()
        set_data.get("Oem").get("Public")['KVMS'] = True if args.kvm=="enable" else False
        set_data.get("Oem").get("Public")['Vmedia'] =  True if args.vm=="enable" else False
        set_data.get("Oem").get("Public")['SSH'] = True
        set_data.get("Oem").get("Public")['WEB'] = True
        if "@odata.id" in set_data.get("Oem").get("Public").keys():
            set_data.get("Oem").get("Public").pop("@odata.id")
        if "@odata.type" in set_data.get("Oem").get("Public").keys():
            set_data.get("Oem").get("Public").pop("@odata.type")

        url_result = self.get_url_info("setuserrule")
        patchBody = {}
        patchBody['url'] = url_result.get("url")

        set_data_list = []
        for i in range(0,len(info)):
            if i == id:
                set_data_list.append(set_data)
            else:
                set_data_list.append({})
        data = {"LDAP":{"RemoteRoleMapping":set_data_list},"Oem":{"Public":{}}}
        if RestFunc.encrypt_type_flag == 1:
            data.get("Oem").get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
            data.get("Oem").get("Public")["EncryptFlag"] = True
        else:
            data.get("Oem").get("Public")["EncryptFlag"] = False
            data.get("Oem").get("Public")['CurrentPassword'] = args.passcode

        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)

        return res

    def setldapgroup(self, client, args):
        def checkGroupName(name):
            # 角色组名称是一个64字母数字组成的字串。
            # 允许特殊字符如连字符和下划线。
            dn = '^[\da-zA-Z\-_]{1,64}$'
            if re.search(dn, name, re.I):
                return True
            return False

        def checkDoamin(s):
            # 域名名称是一个4-127字母数字组成的字串。
            # 开头字符必须是字母。
            # 允许特殊字符如点(.)，逗号(,)，连字符(-)，下划线(_)，等于号(=)。
            # 范例: cn=manager,ou=login, dc=domain,dc=com
            dn = '^[a-zA-Z][a-zA-Z\-_\.\,\=]{5,127}$'
            if re.search(dn, s, re.I):
                return True
            return False

        res = ResultBean()
        if args.name is None and args.base is None and args.pri is None and args.kvm is None and args.vm is None:
            res.State("Failure")
            res.Message("please input one parameter at least.")
            return res
        url_status = self.get_url_info("getuserrule")
        res = ResultBean()
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State:
            status = status_result.Message.get("LDAP").get("ServiceEnabled")
            if status is False:
                res.State("Failure")
                res.Message("ldap status is disable.")
                return res
        else:
            res.State("Failure")
            res.Message(status_result.Message)
            return res

        info = status_result.Message.get("LDAP").get("RemoteRoleMapping")
        data = {}
        id = -1
        for i in range(0,len(info)):
            item = info[i]
            if str(item.get("Oem").get("Public").get("id")) == args.id:
                data = item
                id = i
                break
        if data == {} or id == -1:
            res.State("Failure")
            res.Message("cannot get group id")
            return res
        if data.get('RemoteGroup') is None:
            res.State("Failure")
            res.Message("group " + str(args.id) + " not exist, please use addLDAPgroup method")
            return res

        if args.base is not None:
            if checkDoamin(args.base):
                data.get("Oem").get("Public")['Domain'] = args.base
            else:
                res.State("Failure")
                res.Message(
                    'Domain Name is a string of 5 to 127 alpha-numeric characters.It must start with an alphabetical character.Special Symbols like dot(.), comma(,), hyphen(-), underscore(_), equal-to(=) are allowed.Example: cn=manager,ou=login,dc=domain,dc=com')
                return res
        if args.name is not None:
            if checkGroupName(args.name):
                data['RemoteGroup'] = args.name
            else:
                res.State("Failure")
                res.Message(
                    'Group name is a string of less than 64 alpha-numeric characters, and hyphen and underscore are also allowed.')
                return res
        if args.pri is not None:
            data['LocalRole'] = args.pri.title()
        if args.kvm is not None:
            data.get("Oem").get("Public")['KVMS'] = True if args.kvm=="enable" else False

        if args.vm is not None:
            data.get("Oem").get("Public")['Vmedia'] = True if args.vm == "enable" else False
        if "@odata.id" in data.get("Oem").get("Public").keys():
            data.get("Oem").get("Public").pop("@odata.id")
        if "@odata.type" in data.get("Oem").get("Public").keys():
            data.get("Oem").get("Public").pop("@odata.type")
        url_result = self.get_url_info("setuserrule")
        patchBody = {}
        patchBody['url'] = url_result.get("url")
        set_data_list = []
        for i in range(0, len(info)):
            if i == id:
                set_data_list.append(data)
            else:
                set_data_list.append({})
        set_data = {"LDAP": {"RemoteRoleMapping": set_data_list}, "Oem": {"Public": {}}}
        if RestFunc.encrypt_type_flag == 1:
            set_data.get("Oem").get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
            set_data.get("Oem").get("Public")["EncryptFlag"] = True
        else:
            set_data.get("Oem").get("Public")["EncryptFlag"] = False
            set_data.get("Oem").get("Public")['CurrentPassword'] = args.passcode
        patchBody['json'] = set_data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)

        return res

    def delldapgroup(self, client, args):
        res = ResultBean()
        if args.name is None and args.base is None and args.pri is None and args.kvm is None and args.vm is None:
            res.State("Failure")
            res.Message("please input one parameter at least.")
            return res
        url_status = self.get_url_info("getuserrule")
        status_result = RedfishTemplate.get_for_object_single(client, url_status.get('url'))
        if status_result.State:
            status = status_result.Message.get("LDAP").get("ServiceEnabled")
            if status is False:
                res.State("Failure")
                res.Message("ldap status is disable.")
                return res
        else:
            res.State("Failure")
            res.Message(status_result.Message)
            return res

        info = status_result.Message.get("LDAP").get("RemoteRoleMapping")
        id = -1
        for i in range(0, len(info)):
            item = info[i]
            if str(item.get("RemoteGroup")) == args.name:
                id = i
                break
        if id == -1:
            res.State("Failure")
            res.Message(str(args.name) + " not exist")
            return res
        url_result = self.get_url_info("setuserrule")
        patchBody = {}
        patchBody['url'] = url_result.get("url")
        set_data_list = []
        for i in range(0, len(info)):
            if i == id:
                set_data_list.append(None)
            else:
                set_data_list.append({})
        set_data = {"LDAP": {"RemoteRoleMapping": set_data_list}, "Oem": {"Public": {}}}
        if RestFunc.encrypt_type_flag == 1:
            set_data.get("Oem").get("Public")['CurrentPassword'] = RestFunc.encrypt_rsa(args.passcode, client.type)
            set_data.get("Oem").get("Public")["EncryptFlag"] = True
        else:
            set_data.get("Oem").get("Public")["EncryptFlag"] = False
            set_data.get("Oem").get("Public")['CurrentPassword'] = args.passcode

        patchBody['json'] = set_data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)

        return res

    def editldapgroup(self, client, args):
        result = ResultBean()
        if args.state == 'absent':
            result = self.delldapgroup(client, args)
        elif args.state == 'present':
            name_exist_flag = False
            add_flag = False
            res = self.getldapgroup(client, args)
            if res.State == "Success":
                for item in res.Message:
                    name = item.get('GroupName', "unknown")
                    args.id = str(item.get('GroupID', 0))
                    if name == args.name:
                        name_exist_flag = True
                        break
                    if name == "":
                        add_flag = True
                        break
            else:
                result.State("Failure")
                result.Message(res.Message)
                return result

            if name_exist_flag:
                result = self.setldapgroup(client, args)
            elif add_flag:
                result = self.addldapgroup(client, args)
            else:
                result.State("Failure")
                result.Message(['LDAP role group is full.'])
        return result

    def editadgroup(self, client, args):
        result = ResultBean()
        if args.state == 'absent':
            result = self.deladgroup(client, args)
        elif args.state == 'present':
            name_exist_flag = False
            add_flag = False
            res = self.getadgroup(client, args)
            if res.State == "Success":
                for item in res.Message:
                    name = item.get('GroupName', "unknown")
                    args.id = str(item.get('GroupID', 0))
                    if name == args.name:
                        name_exist_flag = True
                        break
                    if name == "":
                        add_flag = True
                        break
            else:
                result.State("Failure")
                result.Message(res.Message)
                return result

            if name_exist_flag:
                result = self.setadgroup(client, args)
            elif add_flag:
                result = self.addadgroup(client, args)
            else:
                result.State("Failure")
                result.Message(['AD role group is full.'])
        return result

    def getnic(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            nic_info = result.Message
            nicinfo = NicAllBean()
            PCIElist = []
            for item in nic_info:
                PCIEinfo = NICBean()
                adapterinfo = NICController()
                adapterinfo.Id(item.get('Id', "N/A"))
                adapterinfo.Location(item.get('Oem', {}).get("Public", {}).get("DeviceLocator", "N/A"))
                adapterinfo.Manufacturer(item.get('Manufacturer', "N/A"))
                adapterinfo.Model(item.get('Model', "N/A"))
                adapterinfo.PN(item.get('PartNumber', "N/A"))
                adapterinfo.Serialnumber(item.get('SerialNumber', "N/A"))
                adapterinfo.FirmwareVersion(item.get('Oem', {}).get("Public", {}).get("FirmwareVersion", "N/A"))
                adapterinfo.PortCount(item.get('Oem', {}).get("Public", {}).get("PortNumber", "N/A"))
                single_data = collections.OrderedDict()
                single_data['Present'] = 'Present' if 'enable' in str(item.get('Status', {}).get("State", "N/A")).lower() else "Absent"
                single_data['Status'] = item.get('Status', {}).get("Health", "N/A")
                port_url_list = item.get('Controllers', [{}])[0].get("Links", {}).get("NetworkPorts", [])
                port_url = []
                for single_url in port_url_list:
                    if single_url.get("@odata.id") is not None:
                        port_url.append(single_url.get("@odata.id"))
                portlist = []
                if len(port_url) > 0:
                    for i in range(len(port_url)):
                        port_res = RedfishTemplate.get_for_object_single(client, port_url[i])
                        if port_res.State:
                            port_info = port_res.Message
                            portBean = NicPort()
                            portBean.MACAddress(port_info.get("AssociatedNetworkAddresses", ["N/A"])[0])
                            portBean.LinkStatus(port_info.get("LinkStatus", "N/A"))
                            portBean.MediaType(port_info.get('Oem', {}).get('Public', {}).get("PortType", "N/A"))
                            portlist.append(portBean.dict)
                    adapterinfo.Port(portlist)
                controllerList = []
                controllerList.append(adapterinfo.dict)
                PCIEinfo.State(item.get('Status', {}).get("Health", "N/A"))
                PCIEinfo.Controller(controllerList)
                PCIElist.append(PCIEinfo.dict)
            nicinfo.Maximum(len(nic_info))
            nicinfo.NIC(PCIElist)
            res.State("Success")
            res.Message([nicinfo.dict])
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def addLogicalDisk(self, client, args):
        result = ResultBean()
        url_result = self.get_url_info("getstorages")
        raidurl = url_result.get('url') + "/" + str(args.ctrlId)
        raidres = RedfishTemplate.get_for_object_single(client, raidurl)
        raidtype = None
        if raidres.State:
            try:
                raidtype = raidres.Message.get("StorageControllers")[0].get("Oem", {}).get("Public", {}).get("RaidType")
            except:
                raidtype = None

        if not raidtype:
            result.State("Failure")
            result.Message("create virtual drive failed, cannot get raid type")
            return result


        addldurl = url_result.get('url') + "/" + str(args.ctrlId) + "/Volumes"

        raid_dict = {0: "raid0", 1: "raid1", 5: "raid5", 6: "raid6", 10: "raid10"}
        stripsize_dict = {0: "32k", 1: "64k", 2: "128k", 3: "256k", 4: "512k", 5: "1024k"}
        access_dict = {1: "Read Write", 2: "Read Only", 3: "Blocked"}
        read_dict = {1: "Read Ahead", 2: "No Read Ahead"}
        write_dict = {1: "Write Through", 2: "Write Back", 3: "Always Write Back", 4: "Write Back With BBU"}
        io_dict = {1: "Direct IO", 2: "Cached IO"}
        cache_dict = {1: "Unchanged", 2: "Enabled", 3: "Disabled"}
        init_dict = {1: "No Init", 2: "Quick Init", 3: "Full Init"}

        hwdict = {}

        if args.pdlist is not None:
            args.pdlist = args.pdlist.strip().split(',')
            hdlist = []
            for pdid in args.pdlist:
                try:
                    hdlist.append(int(pdid))
                except:
                    hdlist.append(pdid)

            hwdict["Drives"] = hdlist
        if args.vname is not None:
            hwdict["Name"] = args.vname
        if args.StripSize is not None:
            hwdict["StripeSize"] = stripsize_dict.get(args.StripSize)
        if args.rlevel is not None:
            hwdict["RaidLevel"] = "raid" + str(args.rlevel)

        if raidtype == "PMC":
            if args.accelerator:
                hwdict["Accelerator"] = args.accelerator
        else:
            if args.selectSize is not None:
                hwdict["SelectSize"] = args.selectSize
            if args.spandepth is not None:
                hwdict["SpanDepth"] = args.spandepth
            if args.access is not None:
                hwdict["AccessPolicy"] = access_dict.get(args.access)
            if args.r is not None:
                hwdict["ReadPolicy"] = read_dict.get(args.r)
            if args.w is not None:
                hwdict["WritePolicy"] = write_dict.get(args.w)
            if args.io is not None:
                hwdict["CachePolicy"] = cache_dict.get(args.io)
            if args.cache is not None:
                hwdict["IoPolicy"] = io_dict.get(args.cache)
            if args.init is not None:
                hwdict["InitState"] = init_dict.get(args.init)
                hwdict["BackGroundInit"] = True

        postBody = {}
        postBody['url'] = addldurl
        postBody['json'] = hwdict
        addres = RedfishTemplate.post_for_object(client, postBody)

        if addres.State:
            result.State("Success")
            result.Message('create virtual drive successful.')
        else:
            result.State("Failure")
            result.Message("create virtual drive failed, " + str(addres.Message))
        return result

    def getPhysicalDiskInfo(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info("getstorages")
        storageurl = url_result.get('url')

        result = RedfishTemplate.get_for_collection_object_all(client, storageurl)
        if result.State:
            drivedict = {}
            plist = []
            clist = result.Message
            for ctrl in clist:
                if not ctrl.State:
                    continue

                ctrlraw = ctrl.Message
                ctrlId = ctrlraw.get("Id")
                if args.ctrlId is not None and ctrlId != args.ctrlId:
                    continue
                try:
                    raidType = ctrlraw.get("StorageControllers")[0].get("SupportedRAIDTypes")[0]
                except:
                    raidType = None

                drives = ctrlraw.get("Drives")
                for driveurldict in drives:
                    driveurl = driveurldict.get("@odata.id")
                    dresult = RedfishTemplate.get_for_object_single(client, driveurl)
                    if dresult.State:
                        drive = dresult.Message
                    else:
                        continue
                    pdformat = collections.OrderedDict()

                    pdformat["ControllerId"] = ctrlId
                    pdformat["RaidType"] = raidType
                    did = drive.get('Id')
                    if did and "Disk_" in did:
                        did = did.replace("Disk_", "")
                    pdformat["Id"] = did
                    pdformat["Index"] = pdformat["Id"]
                    pdformat["Name"] = drive.get('Name')

                    for key, value in self.showkeydict_phy.items():
                        formatvalue = None
                        if value:
                            if isinstance(value, str):
                                formatvalue = drive.get(value)
                            elif isinstance(value, list):
                                tmpdict = drive.get(value[0])
                                for i in range(1, len(value)):
                                    tmpdict = tmpdict.get(value[i])
                                    formatvalue = tmpdict
                        if formatvalue is not None:
                            pdformat[key] = formatvalue
                    plist.append(pdformat)

            drivedict["physicalDriveNum"] = len(plist)
            drivedict["physicalDrive"] = plist
            res.State('Success')
            res.Message(drivedict)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res


    showkeydict_phy = {
        # "Id": ['Oem', 'Huawei', 'DeviceID'],
        # "Index": ['Oem', 'Huawei', 'DeviceID'],
        # "Name": "Name",
        "DeviceID": None,
        "VenderID": None,
        "Manufacturer": "Manufacturer",
        "VendSpec": None,
        "Model": "Model",
        "EnclosureDdeviceID": None,
        "Sn": "SerialNumber",
        "Temperature": "temperature",
        "SlotNumber": "Slot",
        "ScsiDevType": None,
        "InterfaceType": "Protocol",
    # SPI/PCIe/AHCI/UHCI/SAS/SATA/USB/NVMe/FC/iSCSI/FCoE/NVMeOverFabrics/SMB/NFSv3/NFSv4/HTTP/HTTPS/FTP/SFTP
        "UserDataBlockSize": None,
        "EmulatedBlockSize": None,
        "PathCount": None,
        "IsPathBroken": None,
        "SasAddr": None,
        "SasAddr2": None,
        "ProductID": None,
        "LinkSpeed": "CapableSpeedGbs",
        "MediaErrCount": None,
        "PredFailCount": None,
        # UnconfiguredGood/UnconfigureBad/HotSpareDrive/Offline/Failed/Online/GettingCopied/JBOD/UnconfiguredShieded/HotSpareShielded/ConfiguredShielded/Foreign/Active/Standby/Sleep/DSTInProgress/SMARTOfflineDataCollection/SCTCommand/Rebuilding/Raw/Ready/NotSupported/PredictiveFailure/EraseInProgress
        "FwState": ["Oem", "Public", "FWState"],
        "DisableRemoval": None,
        "DdfType": None,
        "RawSize": "CapacityBytes",
        "Capacity": "CapacityBytes",
        # "NonCoercedSize": None,
        # "CoercedSize": None,
        "PdProgress": None,
        "ProgressRebuild": None,
        "ProgressPatrol": None,
        "ProgressClear": None,
        "ProgressCopyBack": None,
        "ProgressErase": None,
        "ProgressLocate": None,
        "CopeBakePartnerID": None,
        "BadBlockTableFull": None,
        "Security": None,
        "FdeCapable": None,
        "FdeEnabled": None,
        "FwDownloadAllow": None,
        "MediaType": "MediaType",  # HDD/SSD/SMR
        "PowerState": None,  # SpunUp/SpunDown/Transition
        "ConnectedPortNum": None,
        "Certified": None,
        "Props": None,
        "CommissionedSpare": None,
        "EmergencySpare": None,
        "LogicalDisks": None,
        "Status": None,
        "SsdLifeUsed": None,
        "TimeLeft": ["Oem", "Public", "TimeLeft"],
        "ControllerName": ["Oem", "Public", "RaidName"],
        "Location": None,
        "LogicalName": ["Oem", "Public", "VolumeName"],
        "RaidControllerId": None,
        "PatrolRead": None,
        "DeviceSpeed": None,
        "ProductRevisionLevel": None,
        "LastPredFailEventSeqNum": None,
        "OtherErrCount": None,
        "MultiLunDevice": None,
        "Linktype": None,
        "RevisionLevelSATA": None,
        "UsageInfo": None,
        "BlockSize": None,
        "CapableSpeedGbs": "CapableSpeedGbs",
        "NegotiatedSpeedGbs": "NegotiatedSpeedGbs",
        "HotspareState": None,  # None Global Dedicated AutoReplace
        "PowerOnHours": None,
        "BootDevice": None,
        "BootPriority": None,
        "RotationSpeedRPM": None,
        "FwVersion": "Revision",
        "LedStatus": None,  # Off Blinking
        "StatusIndicator": None,
    }

    def setController(self, client, args):
        result = ResultBean()

        raiddict = {}
        if args.raidtype == "PMC":
            url_result = self.get_url_info("setstorages_pmc")
            storageurl = url_result.get('url')
            storageurl = storageurl.replace("{cid}", str(args.ctrlId))
            if args.mode:
                raiddict = {"StorageControllers": [{"Oem": {"Public": {"ControllerMode": args.mode}}}]}
            else:
                result.State("Failure")
                result.Message(['set controller properties failed, -M mode is needed for pmc.'])
                return result
            patchBody = {}
            patchBody['url'] = storageurl
            patchBody['json'] = raiddict
            res = RedfishTemplate.patch_for_object(client, patchBody)
        else:
            url_result = self.get_url_info("setstorages")
            storageurl = url_result.get('url')
            storageurl = storageurl.replace("{cid}", str(args.ctrlId))
            if args.jbod:
                if args.jbod == "enable":
                    raiddict["JBod"] = "Enabled"
                else:
                    raiddict["JBod"] = "Disabled"
            if args.copy:
                if args.copy == "enable":
                    raiddict["CopyBack"] = "Enabled"
                else:
                    raiddict["CopyBack"] = "Disabled"
            if args.smarter:
                if args.smarter == "enable":
                    raiddict["SmartError"] = "Enabled"
                else:
                    raiddict["SmartError"] = "Disabled"

            patchBody = {}
            patchBody['url'] = storageurl
            patchBody['json'] = raiddict
            res = RedfishTemplate.post_for_object(client, patchBody)
        if res.State:
            result.State("Success")
            result.Message(['set controller properties successful.'])
        else:
            result.State("Failure")
            result.Message(['set controller properties failed, ' + str(res.Message)])

        return result

    def createVirtualDrive(self, client, args):
        res = ResultBean()
        ctrl_id_name_dict = {}
        ctrl_id_list = []
        ctrl_type_dict = {
            "LSI": [],
            "PMC": [],
            "MV": []
        }
        # 获取全部ctrl信息需要ctrlid为None
        tmpctrlid = args.ctrlId
        args.ctrlId = None
        raid_result = self.getRaidCtrlInfo(client, args)
        if raid_result.State == "Success":
            ctrls = raid_result.Message
            for ctrl in ctrls:
                if str(ctrl.get("RaidType")).upper() == "PMC":
                    ctrl_type_dict['PMC'].append(ctrl["Name"])
                elif str(ctrl.get("RaidType")).upper() == "LSI":
                    ctrl_type_dict['LSI'].append(ctrl["Name"])
                elif str(ctrl.get("RaidType")).upper() == "MV":
                    ctrl_type_dict['MV'].append(ctrl["Name"])
                if "Index" in ctrl.keys():
                    ctrl_id_name_dict[ctrl["Index"]] = ctrl["Name"]
                    ctrl_id_list.append(str(ctrl["Index"]))
                elif "id" in ctrl.keys():
                    ctrl_id_name_dict[ctrl["id"]] = ctrl["Name"]
                    ctrl_id_list.append(str(ctrl["id"]))
        else:
            res.State("Failure")
            res.Message(["ctrl Information Request Fail!" + raid_result.Message])
            return res
        if ctrl_id_list == []:
            res.State("Failure")
            res.Message(["No raid controller!"])
            return res
        ctrl_list_dict = {}
        pds = {}
        pd_result = self.getPhysicalDiskInfo(client, args)
        if pd_result.State == "Success":
            pds = pd_result.Message.get('physicalDrive')
            for pd in pds:
                if pd['ControllerId'] not in ctrl_list_dict:
                    ctrl_list_dict[pd['ControllerId']] = []
                ctrl_list_dict[pd['ControllerId']].append(pd['Index'])
        else:
            res.State('Failure')
            res.Message('Get physical drive info failed!' + pd_result.Message)
            return res
        if 'Info' in args and args.Info is not None:
            for pd in ctrl_list_dict:
                ctrl_list_dict.get(pd).sort()
            LSI_flag = False
            raidList = []
            for ctrlid in ctrl_id_name_dict:
                raidDict = collections.OrderedDict()
                raidDict['Controller ID'] = ctrlid
                raidDict['Controller Name'] = ctrl_id_name_dict.get(ctrlid)
                if str(ctrl_id_name_dict.get(ctrlid)) in ctrl_type_dict.get('LSI'):
                    raidDict['Controller Type'] = "LSI"
                elif str(ctrl_id_name_dict.get(ctrlid)) in ctrl_type_dict.get('PMC'):
                    raidDict['Controller Type'] = "PMC"
                elif str(ctrl_id_name_dict.get(ctrlid)) in ctrl_type_dict.get('MV'):
                    raidDict['Controller Type'] = "MV"
                pdiskList = []
                for pd in pds:
                    if pd.get("ControllerId") == ctrl_id_name_dict.get(ctrlid):
                        LSI_flag = True
                        pdiskDict = collections.OrderedDict()
                        pdiskDict['Slot Number'] = pd.get("SlotNumber", '')
                        pdiskDict['Drive Name'] = pd.get("Name")
                        if "InterfaceType" in pd:
                            pdiskDict['Interface'] = pd.get("InterfaceType")
                        else:
                            pdiskDict['Interface'] = None
                        if "MediaType" in pd:
                            pdiskDict['Media Type'] = pd.get("MediaType", )
                        if "Capacity" in pd:
                            pdiskDict['Capacity'] = pd.get("Capacity")
                        if "FwState" in pd:
                            pdiskDict['Firmware State'] = pd.get("FwState")
                        else:
                            pdiskDict['Firmware State'] = None
                        pdiskList.append(pdiskDict)
                raidDict['pdisk'] = pdiskList
                raidList.append(raidDict)
                if not LSI_flag:
                    res.State('Failure')
                    res.Message(['Device information Not Available (Device absent or failed to get)!'])
                    return res
            res.State('Success')
            res.Message(raidList)
            return res
        args.ctrlId = tmpctrlid
        if args.ctrlId not in ctrl_list_dict:
            res.State('Failure')
            res.Message("Invalid physical ctrl id, choose from " + ",".join(ctrl_list_dict.keys()))
            return res
        pds = ctrl_list_dict.get(args.ctrlId)
        for pd in args.pdlist.split(","):
            if pd not in pds:
                res.State('Failure')
                res.Message("Invalid physical drive id, choose from " + ",".join(pds))
                return res

        add_result = self.addLogicalDisk(client, args)

        if add_result.State == "Success":
            res.State('Success')
            res.Message("Create virtual disk successfully!")
        else:
            res.State('Failure')
            res.Message('Create virtual disk failed!' + str(add_result.Message))
        return res

    def getraid(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info("getstorages")
        storageurl = url_result.get('url')
        result = RedfishTemplate.get_for_collection_object_all(client, storageurl)
        if result.State:
            clist = []
            rlist = result.Message
            for rl in rlist:
                if rl.State:
                    clist.append(rl.Message)
            res.State('Success')
            res.Message(json.dumps(clist))
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getpdisk(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info("getstorages")
        storageurl = url_result.get('url')
        result = RedfishTemplate.get_for_collection_object_all(client, storageurl)
        if result.State:
            plist = []
            clist = result.Message
            for ctrl in clist:
                if not ctrl.State:
                    continue
                ctrlraw = ctrl.Message
                drives = ctrlraw.get("Drives")
                for driveurldict in drives:
                    driveurl = driveurldict.get("@odata.id")
                    dresult = RedfishTemplate.get_for_object_single(client, driveurl)
                    if dresult.State:
                        drive = dresult.Message
                        plist.append(drive)
                    else:
                        continue
            res.State('Success')
            res.Message(json.dumps(plist))
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getRaidCtrlInfo(self, client, args):
        sfuncs = storageFuncs()
        res = ResultBean()
        url_result = self.get_url_info("getstorages")
        storageurl = url_result.get('url')

        result = RedfishTemplate.get_for_collection_object_all(client, storageurl)
        if result.State:
            ctrls = []
            clist = result.Message
            for ctrl in clist:
                if not ctrl.State:
                    continue
                ctrlformat = collections.OrderedDict()
                ctrlraw = ctrl.Message


                drives = ctrlraw.get("Drives")
                pnum = len(drives)
                lnum = 0
                lurl = ctrlraw.get("Volumes").get("@odata.id")
                lres = RedfishTemplate.get_for_object_single(client, lurl)
                if lres.State and lres.Message.get("Members"):
                    lnum = len(lres.Message.get("Members"))

                #2025年2月28日 为了ham openbmc  提到这里
                ctrlformat["Id"] = ctrlraw.get("Id")
                ctrlformat["Name"] = ctrlraw.get("Name")
                StorageControllers = ctrlraw.get("StorageControllers")[0]
                for key, value in self.showkeydict_ctrl.items():
                    #print(key)
                    if key == "LogicalDevCnt":
                        ctrlformat[key] = lnum
                    elif key == "PhysicalDiskDevCnt":
                        ctrlformat[key] = pnum
                    else:
                        formatvalue = None
                        if value:
                            if isinstance(value, str):
                                formatvalue = StorageControllers.get(value)
                            elif isinstance(value, list):
                                tmpdict = StorageControllers.get(value[0])
                                for i in range(1, len(value)):
                                    if tmpdict is None:
                                        break
                                    tmpdict = tmpdict.get(value[i])
                                    formatvalue = tmpdict
                        if key in self.showvaluedict_ctrl.keys():
                            func = getattr(sfuncs, self.showvaluedict_ctrl.get(key))
                            formatvalue = func(formatvalue)
                        if formatvalue or formatvalue == 0:
                            ctrlformat[key] = formatvalue
                ctrls.append(ctrlformat)

            res.State('Success')
            res.Message(ctrls)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    showkeydict_ctrl = {
        #2025年2月28日 兼容ham openbmc 提到上一层
        # "Id": '@odata.id',
        # "Index": "@odata.id",
        # "Name": "@odata.id",  # PCIE1_RAID
        "RaidType": ['Oem', 'Public', 'RaidType'],
        "Description": 'Description',
        "Model": 'Model',
        "ProductName": 'Model',
        "SerialNumber": "SerialNumber",
        "VendorID": ['Oem', 'Public', 'PCIVendorID'],
        "Vendor": "Manufacturer",
        "DeviceID": ['Oem', 'Public', 'PCIDeviceID'],
        "DeviceName": None,
        "SubVendorId": ['Oem', 'Public', 'PCISubVendorID'],
        "SubDeviceId": ['Oem', 'Public', 'PCISubDeviceID'],
        "ChipRevision": ['Oem', 'Public', 'Chip'],
        "HostPortCount": None,
        "HostInterface": ['Oem', 'Public', 'HostInterface'],#NE3180M8
        "DevicePortCount": None,
        "DeviceInterface": None,
        "fwVersion": "FirmwareVersion",
        "FwVerBuildDate": None,
        "FwVerBuildTime": None,
        "BiosVersion": ['Oem', 'Public', 'BIOSVersion'], #NE3180M8
        # "PackageVersion": ['Oem', 'Huawei', 'ConfigurationVersion'],#NVDATA Version
        "NVDATAVersion": "PackageVersion",
        "TempROC": None,
        "TempCtrl": None,
        "FwCurTime": None,
        "LogicalDevCnt": None,  # 需要计算
        "LogicalDevDegradedCnt": None,
        "LogicalDevOfflineCnt": None,
        "PhysicalDevCnt": None,  # 物理磁盘数+1
        "PhysicalDiskDevCnt": None,  # 物理磁盘数 'Drives@odata.count'
        "PhysicalDiskDevPredFailCnt": None,
        "PhysicalDiskDevFailCnt": None,
        "NVRAMSize": None,
        "MemSize": None,
        "FlashSize": None,
        "DDRECCCount": None,
        "StripMinSize": ['Oem', 'Public', 'StripMinSize'],
        "StripMaxSize": ['Oem', 'Public', 'StripMaxSize'],
        "SupportShieldState": None,
        "SupportJBOD": None,
        "EnableJBOD": ['Oem', 'Public', 'JBOD'], #NE3180M8
        "JBODConfig": ['Oem', 'Public', 'JBODConfig'], #NE3180M8
        "Status": None,
        "SequenceNum": None,
        "PredFailPollInterval": None,
        "InterruptThrottleCount": None,
        "InterruptThrottleTimeUs": None,
        "RebuildRate": None,
        "PatrolReadRate": None,
        "BackgroundInitRate": None,
        "ConsistencyCheckRate": None,
        "ReconstructionRate": None,
        "CacheFlushInterval": None,
        "ClusterMode": None,
        "CoercionMode": None,
        "AlarmEnable": None,
        "AutoRebuild": None,
        "BatteryWarning": None,
        "EccBucketSize": None,
        "EccBucketLeakRate": None,
        "RestoreHSpareOnInsertion": None,
        "ExposeEnclosureDev": None,
        "MaintainPDFailHistory": None,
        "DisHostReqReorder": None,
        "AbortCCOnError": None,
        "LoadBalanceMode": None,
        "SpinDownTime": None,
        "SmartErEnabled": ['Oem', 'Public', 'SmartErr'],
        "SasAddr": ['Oem', 'Public', 'SASAddress'],
        "WebBIOSVersion": None,
        "SpinUpDelay": None,
        "SpinUpDriveCount": None,
        "ControllerBIOS": None,

        "Volt": None,
        "MaxVolt": None,
        "PBSIVersion": None,
        "JunctionTemp": ['Oem', 'Public', 'JunctionTemperature'],
        "LDOptimalCount": ['Oem', 'Public', 'LDOptimalCount'],
        "PDOptimalCount": ['Oem', 'Public', 'PDOptimalCount'],
        "ChargeState": None,
        "AmbientTemp": None,
        "Health": ['Status', 'Health'],
        "HealthRollup": ['Status', 'HealthRollup'],
        "State": ['Status', 'State'],
        "DSTVersion": None,
        "DDRSize(KB)": None,
        "Current": None,
        "Speed": "SpeedGbps",
        "UnconfiguredGoodSpinDown": None,
        #
        "CopyBack": ['Oem', 'Public', 'CopyBack'],  # True
        "SmartCopyBack": None,
        "Ncq": None,
        "HotSpareSpinDown": None,
        "PersonalityMode": None,
        "BbuStatus": ['Oem', 'Public', 'BBUState'],
        "BbuSeverity": None,
        "BbuHealth": None,
        "BbuFaultDetails": None,
        "BbuTemp": None,
        "BbuType": None,
        "BbuVolt": None,
        "WorkMode": None,
        "SupportedRAIDLevels": "SupportedRAIDTypes",
        "MaintainPDFailureHistory": None,
        "BDF": "Bdf",
        "OutOfBandManage": None,
        "TotalCacheSizeMiB": ["CacheSummary", "TotalCacheSizeMiB"],
        "ControllerMode": ['Oem', 'Public', 'ControllerMode'],
        "HardwareRevision": ['Oem', 'Public', 'HardwareRevision'],
        "Memory": ['Oem', 'Public', 'Memory'],
        "MemoryChangeable": ['Oem', 'Public', 'MemoryChangeable'],#NE3180M8
        "MemoryCorrectErrCount": ['Oem', 'Public', 'MemoryCorrectErrCount'],#NE3180M8
        "MemoryUnCorrectErrCount": ['Oem', 'Public', 'MemoryUnCorrectErrCount'],#NE3180M8
        "WWN": ['Oem', 'Public', 'WWN'],
        "SeqNumLastCleanShutdownEvent": ['Oem', 'Public', 'SeqNumLastCleanShutdownEvent'],
        "SeqNumLastClearEvent": ['Oem', 'Public', 'SeqNumLastClearEvent'],
        "SeqNumNewestEvent": ['Oem', 'Public', 'SeqNumNewestEvent'],
        "SeqNumOldestEvent": ['Oem', 'Public', 'SeqNumOldestEvent'],
        "SeqNumThisSessionBootEvent": ['Oem', 'Public', 'SeqNumThisSessionBootEvent'],
        #NE3180M8
        "SupportedControllerProtocols": "SupportedControllerProtocols",
        "SupportedDeviceProtocols": "SupportedDeviceProtocols",
        "PortCount": ['Oem', 'Public', 'PortCount'],
        "Result": ['Oem', 'Public', 'Result'],
        "SSDSmartErr": ['Oem', 'Public', 'SSDSmartErr'],

    }

    showvaluedict_ctrl = {
        "RaidType": "getraidtype",
        "DeviceName": 'getDeviceID',
    }

    def addldisk(self, client, args):
        return self.createVirtualDrive(client, args)

    def getldisk(self, client, args):
        return self.getLogicalDiskInfo(client, args)

    def getLogicalDiskInfo(self, client, args):
        sfuncs = storageFuncs()
        res = ResultBean()
        url_result = self.get_url_info("getstorages")
        storageurl = url_result.get('url')

        result = RedfishTemplate.get_for_collection_object_all(client, storageurl)
        if result.State:
            drivedict = {}
            plist = []
            clist = result.Message
            for ctrl in clist:
                if not ctrl.State:
                    continue

                ctrlraw = ctrl.Message
                ctrlId = ctrlraw.get("Id")
                if args.ctrlId is not None and ctrlId != args.ctrlId:
                    continue
                try:
                    raidType = ctrlraw.get("StorageControllers")[0].get("SupportedRAIDTypes")[0]
                except:
                    raidType = None

                vrul = ctrlraw.get("Volumes", {}).get("@odata.id")
                vresult = RedfishTemplate.get_for_collection_object_all(client, vrul)
                if vresult.State:
                    vlist = vresult.Message
                    for volume in vlist:
                        if not volume.State:
                            continue
                        drive = volume.Message

                        pdformat = collections.OrderedDict()

                        pdformat["ControllerId"] = ctrlId
                        pdformat["RaidType"] = raidType
                        vid = drive.get("Id")
                        if vid and "LogicalDisk" in vid:
                            vid = vid.replace("LogicalDisk", "")
                        pdformat["Id"] = vid

                        for key, value in self.showkeydict_virtual.items():
                            formatvalue = None
                            if value:
                                if isinstance(value, str):
                                    formatvalue = drive.get(value)
                                elif isinstance(value, list):
                                    tmpdict = drive.get(value[0])
                                    for i in range(1, len(value)):
                                        tmpdict = tmpdict.get(value[i])
                                        formatvalue = tmpdict
                            if key in self.showvaluedict_virtual.keys():
                                func = getattr(sfuncs, self.showvaluedict_virtual.get(key))
                                formatvalue = func(formatvalue)
                            if formatvalue is not None:
                                pdformat[key] = formatvalue

                        plist.append(pdformat)



            drivedict["logicalDriveNum"] = len(plist)
            drivedict["logicalDrive"] = plist
            res.State('Success')
            res.Message(drivedict)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    showkeydict_virtual = {
        # "Id": "Id",
        # "Index": "Id",
        # "TargetID": "Id",
        "SN": None,
        "VolumeName": "Name",
        "RaidLevel": "RAIDType",
        "ControllerName": ["Oem", "Public", "ControllerName"],
        # DefaultCachePolicy, DefaultIOPolicy 应该是一套
        "DefaultCachePolicy": None,
        "DefaultWritePolicy": None,
        "DefaultReadPolicy": None,
        "CurrentCachePolicy": ["Oem", "Public", "CurrentCachePolicy"],
        "CurrentWritePolicy": ["Oem", "Public", "CurrentWritePolicy"],
        "CurrentReadPolicy": ["Oem", "Public", "CurrentReadPolicy"],
        "DriveCachePolicy": ["Oem", "Public", "DriveCachePolicy"],
        "AccessPolicy": ["Oem", "Public", "AccessPolicy"],
        "BackgroundInitialization": None,
        "SSCDCaching": None,
        "PrimayRaidLevel": None,
        "RaidLevelQaulifier": None,
        "SecondaryRaidLevel": None,
        "StripSize": ["Oem", "Public", "StripeBlock"],
        "DrivesPerSpan": ["Oem", "Public", "DrivesPerSpan"],
        "SpanNum": ["Oem", "Public", "SpanNum"],
        "InitState": None,
        "State": None,
        "IsConsistent": None,
        "BadBlocksExist": None,
        "IsCachePinned": None,
        "EncryptionType": None,
        "DefaultPowerPolicy": None,
        "CurrentPowerPolicy": None,
        "Capacity": "CapacityBytes",
        "OwnerDevID": None,
        "CCProgress": None,
        "PhysicalDisks": ['Links', 'Drives'],
        "VolumeRaidLevel": None,
        "Status": None,
        "IsSSCD": None,
        "BootEnable": ["Oem", "Public", "BootEnable"],
        "BootPriority": None,
        "LogicalName": None,
        "Location": None,
        "Progress": None,
        "Percentage": None,
        "ElementsNum": None,
        "VendorType": None,
        "AcceleratorType": None,
        "LogicalDriveType": None,
    }

    showvaluedict_virtual = {
        "RaidLevel": "getRaidLevel",
        "Capacity": "kb2gb",
        "PhysicalDisks": "getPds",
    }

    def setLogicalDisk(self, client, args):
        result = ResultBean()
        M8PMCkey = "LogicalDisk"

        if args.option == "DEL":
            url_result = self.get_url_info("getstorages")
            delurl = url_result.get('url') + "/" + str(args.ctrlId) + "/Volumes/" + M8PMCkey + str(args.ldiskId)
            res = RedfishTemplate.delete_for_object(client, delurl)
        elif args.option == "LOC":
            mydict = {}
            url_result = self.get_url_info("locatelogicaldrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{vid}", M8PMCkey + str(args.ldiskId))
            mydict["Action"] = "start"
            if args.duration is not None:
                if args.duration < 0 or args.duration > 255:
                    result.State("Failure")
                    result.Message('Invalid Duration(0-255).')
                    return result
                mydict["Duration"] = args.duration
            else:
                result.State("Failure")
                result.Message('-D is needed when locate virtual drive')
                return result
            patchBody = {}
            patchBody['url'] = setpdurl
            patchBody['json'] = mydict
            res = RedfishTemplate.post_for_object(client, patchBody)
        elif args.option == "STL":
            mydict = {}
            url_result = self.get_url_info("locatelogicaldrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{vid}", M8PMCkey + str(args.ldiskId))
            mydict["Action"] = "stop"
            mydict["Duration"] = 50
            patchBody = {}
            patchBody['url'] = setpdurl
            patchBody['json'] = mydict
            res = RedfishTemplate.post_for_object(client, patchBody)
        elif args.option == "FI":
            mydict = {}
            url_result = self.get_url_info("initlogicaldrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{vid}", M8PMCkey + str(args.ldiskId))
            mydict["InitType"] = "Fast Initialization"
            patchBody = {}
            patchBody['url'] = setpdurl
            patchBody['json'] = mydict
            res = RedfishTemplate.post_for_object(client, patchBody)
        elif args.option == "SFI":
            mydict = {}
            url_result = self.get_url_info("initlogicaldrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{vid}", M8PMCkey + str(args.ldiskId))
            mydict["InitType"] = "Full Initialization"
            patchBody = {}
            patchBody['url'] = setpdurl
            patchBody['json'] = mydict
            res = RedfishTemplate.post_for_object(client, patchBody)
        elif args.option == "SI":
            mydict = {}
            url_result = self.get_url_info("initlogicaldrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{vid}", M8PMCkey + str(args.ldiskId))
            mydict["InitType"] = "Stop Initialization"
            patchBody = {}
            patchBody['url'] = setpdurl
            patchBody['json'] = mydict
            res = RedfishTemplate.post_for_object(client, patchBody)
        if res.State:
            result.State("Success")
            result.Message('operation is successful,please wait a few seconds.')
        else:
            result.State("Failure")
            result.Message('operation is failed, ' + str(res.Message))

        return result

    def setldisk(self, client, args):
        result = ResultBean()
        if not args.Info:
            if args.ctrlId is None or args.ldiskId is None or args.option is None:
                result.State("Failure")
                result.Message(['Controller id, Logical drive id and operation is needed.'])
                return result

        ctrl_vd_dict = {}
        # 获取全部ctrl信息需要ctrlid为None
        tmpctrlid = args.ctrlId
        args.ctrlId = None
        vd_result = self.getLogicalDiskInfo(client, args)
        vds = None
        if vd_result.State == "Success":
            vds = vd_result.Message.get('logicalDrive')
            for vd in vds:
                ctrlid = vd.get("ControllerId")
                vdid = vd.get("Id")
                if ctrl_vd_dict.get(ctrlid):
                    ctrl_vd_dict.get(ctrlid).append(vdid)
                else:
                    ctrl_vd_dict[ctrlid] = [vdid]
        else:
            result.State("Failure")
            result.Message(['get virtual drive info failed!' + vd_result.Message])
            return result

        if args.Info:
            result.State('Success')
            result.Message(ctrl_vd_dict)
            return result

        args.ctrlId = tmpctrlid
        if args.ctrlId not in ctrl_vd_dict:
            result.State("Failure")
            result.Message(['Invalid virtual ctrl id, choose from ' + ','.join(ctrl_vd_dict.keys())])
            return result
        vds = ctrl_vd_dict.get(args.ctrlId)
        if args.ldiskId not in vds:
            result.State("Failure")
            result.Message(['Invalid virtual drive id, choose from ' + ','.join(vds)])
            return result

        ctrl_result = self.setLogicalDisk(client, args)
        if ctrl_result.State == "Success":
            result.State("Success")
            result.Message('Set virtual drive successfully!')
            return result
        elif ctrl_result.State == "Not Support":
            result.State("Failure")
            result.Message(['This server does not support set virtual drive.' ])
            return result
        else:
            result.State("Failure")
            result.Message(['Set virtual drive failed!' + ctrl_result.Message])
            return result

    def getauditlog(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url')+"?$top=1900")
        res = ResultBean()
        if result.State:
            info = result.Message.get("Members", [])
            data_sum = []
            for item in info:
                single_data = collections.OrderedDict()
                single_data['ID'] = item.get('Id', "N/A")
                single_data['TimeStamp'] = item.get('Created', "N/A")
                single_data['HostName'] = item.get('Oem', {}).get('Public', {}).get('HostName', "N/A")
                single_data['Description'] = html.unescape(item.get('Message', "N/A"))
                single_data['Address'] = item.get('Oem', {}).get('Public', {}).get('Address', "N/A")
                single_data['InterfaceName'] = item.get('Oem', {}).get('Public', {}).get('InterfaceName', "N/A")
                single_data['UserName'] = item.get('Oem', {}).get('Public', {}).get('UserName', "N/A")
                data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def setscreen(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        res = ResultBean()
        data = {
            'ScreenShot': {
                'AutoCaptureEnabled': True if args.status == 'enable' else False
            }
        }
        patchBody = {}
        patchBody['url'] = url_result.get('url')
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getscreen(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data = {}
            data['AutoCapture'] = 'enable' if info.get('ScreenShot', {}).get('AutoCaptureEnabled', False) else 'disable'
            res.State('Success')
            res.Message(data)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getbackplane(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data_sum = []
            for item in info:
                single_data = collections.OrderedDict()
                single_data['ID'] = item.get('Id', "N/A")
                single_data['Present'] = "Present" if "enable" in str(item.get('Status', {}).get('State', "N/A")).lower() else "Absent"
                single_data['FwVersion'] = item.get('BackplaneVersion', "N/A")
                single_data['TotalSlotCount'] = item.get('PortCount', "N/A")
                single_data['Temperature'] = item.get('Temperature', "N/A")
                # single_data['Status'] = item.get('Status', {}).get('Health', "N/A")
                data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def backup(self, client, args):
        args.fileurl = args.bak_file
        res = filePath("bmcconfig", args)
        if res.State == "Failure":
            return res
        bmcres = ResultBean()
        param = {}
        url_back = self.get_url_info("bmcbackup")
        postBody = {}
        postBody['url'] = str(url_back.get('url'))
        postBody['json'] = param
        testres = RedfishTemplate.post_for_object(client, postBody)

        if testres.State:
            with open(args.fileurl, 'wb') as f:
                f.write(testres.Message.content)
                f.close()
            bmcres.State("Success")
            bmcres.Message(["bmc config file export success: " + args.fileurl])
        else:
            bmcres.State("Failure")
            bmcres.Message(["cannot prepare for export BMC cfg. " + str(testres.Message)])
        return bmcres

    def restore(self, client, args):
        args.fileurl = args.bak_file
        checkparam_res = ResultBean()
        if not os.path.exists(args.fileurl):
            checkparam_res.State("Failure")
            checkparam_res.Message(["File not exists."])
            return checkparam_res
        if not os.path.isfile(args.fileurl):
            checkparam_res.State("Failure")
            checkparam_res.Message(["The file url is not file."])
            return checkparam_res
        url_result = self.get_url_info("bmcrestore")
        postBody = {}
        postBody['data'] = {}
        postBody['file'] = [('config', open(args.fileurl, 'rb'))]
        postBody['url'] = url_result.get('url')
        res = RedfishTemplate.post_for_object(client, postBody)
        bmcres = ResultBean()
        if res.State:
            bmcres.State("Success")
            bmcres.Message([""])
        else:
            bmcres.State("Failure")
            bmcres.Message([res.Message])
        # logout
        return bmcres

    def exportbioscfg(self, client, args):
        res = filePath("biosconfig", args)
        if res.State == "Failure":
            return res
        url_result = self.get_url_info("exportbiosoption")
        postbody = {}
        postbody["url"] = url_result.get('url')
        result = RedfishTemplate.post_for_object(client, postbody)
        res = ResultBean()
        if result.State:
            with open(args.fileurl, 'w') as f:
                import json
                f.write(json.dumps(result.Message.json(), indent=4))
                # f.write(str(result.Message.json()))
            res.State('Success')
            res.Message('Bios Configuration export to ' + str(args.fileurl))
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def importbioscfg(self, client, args):
        checkparam_res = ResultBean()
        if not os.path.exists(args.fileurl):
            checkparam_res.State("Failure")
            checkparam_res.Message(["File not exists."])
            return checkparam_res
        if not os.path.isfile(args.fileurl):
            checkparam_res.State("Failure")
            checkparam_res.Message(["The file url is not file."])
            return checkparam_res
        url_result = self.get_url_info("importbiosoption")

        with open(args.fileurl, 'rb') as f:
            files = [("config", f.read())]

        postbody = {}
        postbody["url"] = url_result.get('url')
        postbody["file"] = files
        result = RedfishTemplate.post_for_object(client, postbody)
        res = ResultBean()
        if result.State:
            res.State('Success')
            res.Message('Import Bios Configuration successfully')
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getbios(self, client, args):
        args.Attribute = None
        # 获取bios版本 放在args里面
        self._get_bios_version(client, args)
        bios_result = ResultBean()

        url_result = self.get_url_info("getbios")
        server_result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if server_result.State:
            server_bios = server_result.Message.get("Attributes")
            if not server_bios:
                bios_result.State("Failure")
                bios_result.Message(["Cannot get bios info"])
                return bios_result

            # 获取映射信息
            mapper_result = self._get_xml_mapper(args, 'cmd', 'value')
            attr_dict = {}
            if mapper_result[0]:
                attr_dict = mapper_result[1]
            else:
                bios_result.Message([mapper_result[1]])
                bios_result.State('Failure')
                return bios_result

            attr_request = []  # 统一处理-A指定的配置项或所有可获取的配置项
            if args.Attribute:  # 获取指定BIOS
                if args.Attribute.strip().lower().replace(" ", "") not in attr_dict:
                    bios_result.Message(["[{}] is invalid option.".format(args.Attribute)])
                    bios_result.State('Failure')
                    return bios_result
                attr_request.append(args.Attribute.strip().lower().replace(" ", ""))
            else:  # 获取全部BIOS项
                attr_request = list(attr_dict.keys())

            bios = {}
            for attr_lower in attr_request:
                attr = attr_dict[attr_lower]['getter']
                attr_parent = attr_dict[attr_lower]['parent']
                attr_desc = attr_dict[attr_lower]['description']
                attr_desc_nospace = attr_desc.replace(" ", "")
                if attr_parent not in server_bios:

                    # 根据指定的参数确定输出的提示信息
                    if args.Attribute:
                        bios_result.State('Failure')
                        bios_result.Message(["can't get the value of [{}].".format(attr_desc)])
                        return bios_result
                    else:
                        bios[attr_desc_nospace] = None

                else:
                    l1_bios_value = server_bios[attr_parent]
                    if isinstance(l1_bios_value, dict):
                        if attr in l1_bios_value:
                            bios[attr_desc_nospace] = self._transfer_value(l1_bios_value[attr],
                                                                           attr_dict[attr_lower]['setter'],
                                                                           attr_desc)
                        elif attr[:-1] in l1_bios_value:
                            if len(l1_bios_value[attr[:-1]]) > int(attr[-1]):
                                bios[attr_desc_nospace] = self._transfer_value(l1_bios_value[attr[:-1]][int(attr[-1])],
                                                                               attr_dict[attr_lower]['setter'],
                                                                               attr_desc)
                            else:
                                bios[attr_desc_nospace] = None

                        else:

                            # 根据指定的参数确定输出的提示信息
                            if args.Attribute:
                                bios_result.State('Failure')
                                bios_result.Message(
                                    ["can't get value of [{}].".format(attr_desc)])
                                return bios_result
                            else:
                                bios[attr_desc_nospace] = None

                    else:

                        # 根据指定的参数确定输出的提示信息
                        if args.Attribute:
                            bios_result.State('Failure')
                            bios_result.Message(
                                ['not support getting value of [{}].'.format(attr_desc)])
                            return bios_result
                        else:
                            bios[attr_desc_nospace] = None

            bios_result.State('Success')
            bios_result.Message([bios])
        else:
            bios_result.State('Failure')
            bios_result.Message([server_result.Message])
        return bios_result

    def _transfer_value(self, origin_value, value_map, user_key):
        """
        服务器原始bios配置值 -> 符合配置文件约束的配置值
        args:
            origin_value: 服务器原始bios值
            value_map: 机型映射文件{cmd: value}
            user_key: 当前需要转换的description，用来特殊处理BootOption
        returns:
            转换后的值
        """
        if isinstance(origin_value, list):
            if user_key.startswith(('UEFIBootOption', 'LegacyBootOption')):
                index = int(user_key[-1:]) - 1
                return value_map.get(origin_value[index], origin_value[index])
            else:
                return [value_map.get(str(value), str(value)) for value in origin_value]
        elif isinstance(origin_value, dict):
            return {k: value_map.get(str(v), str(v)) for k, v in origin_value}
        else:
            if len(value_map) == 1:
                return origin_value
            else:
                return value_map.get(str(origin_value), None)

    def setbios(self, client, args):
        # 获取bios版本 放在args里面
        self._get_bios_version(client, args)
        res = ResultBean()
        attr_dict = {}
        # 读取映射文件
        mapper_result = self._get_xml_mapper(args, 'value', 'cmd')
        if mapper_result[0]:
            if args.list:  # 打印信息
                help_list = []
                for key, value in mapper_result[1].items():
                    help_list.append(
                        '{:<35}: {}'.format(value['description'].replace(" ", ""), list(value['setter'].keys())))
                res.Message(help_list)
                res.State('Success')
                return res
            else:
                attr_dict = mapper_result[1]
        else:
            res.Message([mapper_result[1]])
            res.State('Failure')
            return res

        # 获取用户输入，统一处理通过-A或通过文件配置的值
        import json
        input_value = {}
        if args.fileurl:
            if not os.path.exists(args.fileurl) or not os.path.isfile(args.fileurl):
                res.Message(['file path error.'])
                res.State('Failure')
                return res
            try:
                with open(args.fileurl) as f:
                    input_value = json.loads(f.read())
            except:
                res.Message(['file format error.'])
                res.State('Failure')
                return res
        if args.attribute:
            input_value[args.attribute.strip()] = args.value.strip()

        # getbios
        url_result = self.get_url_info("getbios")
        server_result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if not server_result.State:
            res.Message(['get bios failed.' + str(server_result.Message)])
            res.State('Failure')
            return res
        # 当前值
        server_bios = server_result.Message.get("Attributes")

        # 获取future
        url_result = self.get_url_info("setbios")
        future_result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if future_result.State:
            future_bios = future_result.Message.get('Attributes')
        else:
            future_bios = None

        # 校验输入并转换，默认映射文件完全正确，不再和服务器键比对
        user_bios = {}  # 最终会提交到redfish接口中的配置字典
        bootdict = {}
        for key, value in input_value.items():
            # 校验键
            if key.lower().replace(" ", "") not in attr_dict:
                res.Message(['not support setting [{}]. Please refer to [-L]'.format(key)])
                res.State('Failure')
                return res
            # 校验值并转换
            item_dict = attr_dict[key.lower().replace(" ", "")]
            attr = item_dict['getter']
            attr_setter = item_dict['setter']
            attr_parent = item_dict['parent']
            # list的3种处理方式 {0:"x", 1:"y"} [x,y,...] x
            if item_dict.get('list') > 0:
                inputlist = []
                if isinstance(value, dict):
                    dict2list = server_bios.get(attr_parent).get(attr)
                    for k, v in value.items():
                        dict2list[k] = str(attr_setter[v])
                    inputlist = dict2list
                elif isinstance(value, list):
                    for valuesingle in value:
                        if attr_setter.get(valuesingle):
                            inputlist.append(str(attr_setter[valuesingle]))
                        elif attr_setter.get(str(valuesingle)):
                            inputlist.append(str(attr_setter[str(valuesingle)]))
                        else:
                            res.Message(['[{}] is invalid value for bios option [{}], and valid values are [{}].'
                                        .format(value, key, ', '.join(list(attr_setter.keys())))])
                            res.State('Failure')
                            return res

                elif isinstance(value, str):
                    if "{" in value:
                        try:
                            valueinjson = json.loads(value)
                            dict2list = server_bios.get(attr_parent).get(attr)
                            for k, v in valueinjson.items():  # 根据目前支持的配置项，值统一处理为str
                                if int(k) >= len(dict2list):
                                    res.Message(
                                        ['incorrect key: "{}", list length is {}. '.format(k, len(dict2list))])
                                    res.State('Failure')
                                    return res

                                dict2list[int(k)] = str(attr_setter[v])
                                inputlist = dict2list
                        except Exception as e:

                            res = ResultBean()
                            res.Message(
                                ['incorrect format for key: [{}], value: [{}]. value format is JSON.'.format(key,
                                                                                                             value)])
                            res.State('Failure')
                            return res
                    elif "[" in value:
                        valueinlist = value[1:-1].split(",")
                        for valuesingle in valueinlist:
                            inputlist.append(str(attr_setter[valuesingle]))
                    else:
                        inputlist = [str(attr_setter[value])] * item_dict.get('list')

                if user_bios.get(attr_parent):
                    user_bios.get(attr_parent)[attr] = inputlist
                else:
                    user_bios[attr_parent] = {attr: inputlist}
            elif attr_parent == "FixedBootPriorities":

                if value not in attr_setter:
                    res.Message(['[{}] is invalid value for bios option [{}], and valid values are [{}].'
                                .format(value, key, ', '.join(list(attr_setter.keys())))])
                    res.State('Failure')
                    return res
                bootdict[attr] = str(attr_setter.get(value, value))
            else:
                if len(attr_setter) == 1:
                    # 类型
                    for valuerange in attr_setter.keys():
                        if "-" in valuerange:
                            min = int(valuerange.split("-")[0])
                            max = int(valuerange.split("-")[1])
                        elif "~" in valuerange:
                            min = int(valuerange.split("~")[0])
                            max = int(valuerange.split("~")[1])
                        else:
                            res.Message([
                                '[{}] is invalid range value for bios option [{}], range should be a~b or a-b.'
                                .format(valuerange, key)])
                            res.State('Failure')
                            return res
                        if int(value) < min or int(value) > max:
                            res.Message(
                                ['[{}] is invalid value for bios option [{}], and valid values are [{}].'
                                 .format(value, key, valuerange)])
                            res.State('Failure')
                            return res

                    if user_bios.get(attr_parent):
                        user_bios.get(attr_parent)[attr] = int(value)
                    else:
                        user_bios[attr_parent] = {attr: int(value)}
                    # user_bios[attr] = int(value)
                else:
                    if item_dict['match'] and value not in attr_setter:
                        res.Message(['[{}] is invalid value for bios option [{}], and valid values are [{}].'
                                    .format(value, key, ', '.join(list(attr_setter.keys())))])
                        res.State('Failure')
                        return res

                    if user_bios.get(attr_parent):
                        user_bios.get(attr_parent)[attr] = str(attr_setter.get(value, value))
                    else:
                        user_bios[attr_parent] = {attr: str(attr_setter.get(value, value))}

                    # user_bios[attr] = str(attr_setter.get(value, value))

        if bootdict:
            # 需要特殊处理boot相关
            uefibootlist = []
            legacybootlist = []
            if future_bios and future_bios.get("FixedBootPriorities"):
                uefibootlist = future_bios.get("FixedBootPriorities").get("UefiPriorities", [])
                legacybootlist = future_bios.get("FixedBootPriorities").get("LegacyPriorities", [])

            if not uefibootlist:
                uefibootlist = server_bios.get("FixedBootPriorities").get("UefiPriorities", [])
            if not legacybootlist:
                legacybootlist = server_bios.get("FixedBootPriorities").get("LegacyPriorities", [])

            for uboot, uvalue in bootdict.items():
                if "UefiPriorities" in uboot and uefibootlist:
                    uid = int(uboot.replace("UefiPriorities", ""))
                    uefibootlist[uid] = uvalue
                if "LegacyPriorities" in uboot and legacybootlist:
                    uid = int(uboot.replace("LegacyPriorities", ""))
                    legacybootlist[uid] = uvalue
            if uefibootlist:
                user_bios["FixedBootPriorities"] = {"UefiPriorities": uefibootlist}
            if legacybootlist:
                if user_bios.get("FixedBootPriorities"):
                    user_bios.get("FixedBootPriorities")["LegacyPriorities"] = legacybootlist
                else:
                    user_bios["FixedBootPriorities"] = {"LegacyPriorities": legacybootlist}

        # 读取映射文件
        flag, bios_info = self._get_xml(args)
        if not flag:
            res.Message([bios_info])
            res.State('Failure')
            return res

        # 检查前置项
        conditionflag, conditionmessage = self.judgeCondition(user_bios, future_bios, server_bios, bios_info)
        if not conditionflag:
            res.State('Failure')
            res.Message([conditionmessage])
            # logout
            return res

        user_bios_f = self.formatBiosPatchBody(user_bios)

        patchBody = {}
        url_result = self.get_url_info("setbios")
        patchBody['url'] = url_result.get('url')
        url_result = self.get_url_info("getbios")
        patchBody['etagurl'] = url_result.get('url')
        patchBody['json'] = user_bios_f
        set_result = RedfishTemplate.patch_for_object(client, patchBody)

        if set_result.State:
            res.Message([''])
            res.State("Success")
        else:
            res.Message([set_result.Message])
            res.State('Failure')
        return res

    # 2023年3月30日 M7 1.35.05 通过redfish配置bios body 必须带Attributes
    def formatBiosPatchBody(self, user_bios):
        return {"Attributes": user_bios}

    def _get_bios_version(self, client, args):
        biosversion = None
        # get

        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        if result.State:
            data = result.Message
            for item in data:
                if item.get("Id") == "Bios":
                    version = item.get('Version', 'N/A')
                    if version is None:
                        version = "N/A"
                    version_index = str(version).find('(')
                    if version_index == -1:
                        biosversion = version
                    else:
                        biosversion = str(version)[:version_index].strip()
                    break

        args.biosversion = biosversion
        return biosversion

    def _get_xml_file(self, args):
        xml_path = os.path.join(IpmiFunc.command_path, "bios") + os.path.sep
        return xml_path + 'M8.xml'


    def _get_xml_mapper(self, args, key, value):
        """
            {
                'descriptionName': {
                    'description': 'descriptionName',
                    'list': 64,
                    'match': True/False,
                    'parent': 'server_bios_parent_key',
                    'getter': 'server_bios_key',
                    'setter': {
                        'cmd': 'value' 或 'value': 'cmd' 根据参数确定
                    }
                }
            }
        """
        try:
            # xml_filepath = sys.path[0] + '/mappers/bios/M7.xml'
            xml_filepath = self._get_xml_file(args)
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_filepath)
            server = tree.getroot()
            map_dict = {}
            for items in server:
                for item in items:
                    map_dict[item.find('name').find('description').text.lower().replace(" ", "")] = {
                        'description': item.find('name').find('description').text,
                        'list': 0 if item.find('list') is None else int(item.find('list').text),
                        'match': True if item.find('match') is None else False if item.find(
                            'match').text == 'False' else True,
                        'parent': None if item.find('parent') is None else item.find('parent').text,
                        'getter': item.find('getter').text,
                        'setter': {
                            setter.find(key).text: setter.find(value).text for setter in item.find('setters')
                        },
                        'conditions': {} if item.find('conditions') is None else {
                            setter.find("key").text: setter.find("value").text for setter in item.find('conditions')
                        },
                    }
            return True, map_dict
        except Exception as e:
            return False, str(e)

    def _get_xml(self, args):
        """
            {
                'getter': {
                    'description': 'descriptionName',
                    'type': 'int/str/list/dict',
                    'match': True/False,
                    'parent': 'server_bios_parent_key',
                    'getter': 'server_bios_key',
                    'setter': {
                        'cmd': 'value'
                    },
                    'condition': {
                        'getter': 'cmd'
                    }
                }
            }
        """
        try:
            # xml_filepath = sys.path[0] + '/mappers/bios/M7.xml'
            xml_filepath = self._get_xml_file(args)
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_filepath)
            server = tree.getroot()
            map_dict = {}
            for items in server:
                for item in items:
                    map_dict[item.find('getter').text] = {
                        'description': item.find('name').find('description').text,
                        'type': 'str' if item.find('type') is None else item.find('type').text,
                        'match': True if item.find('match') is None else False if item.find(
                            'match').text == 'False' else True,
                        'parent': None if item.find('parent') is None else item.find('parent').text,
                        'getter': item.find('getter').text,
                        'setter': {
                            setter.find("cmd").text: setter.find("value").text for setter in item.find('setters')
                        },
                        'conditions': {} if item.find('conditions') is None else {
                            setter.find("key").text: setter.find("value").text for setter in item.find('conditions')
                        },
                    }
            return True, map_dict
        except Exception as e:
            return False, str(e)

    # 判断是否可以设置
    # bios_set={redfishkey,redfishvalue}
    # bios_future={redfishkey,redfishvalue}
    # bios_cur={redfishkey,redfishvalue}
    # bios_all_info={clikey, allinfo}
    def judgeCondition(self, bios_set, bios_future, bios_cur, bios_all_info):
        conditionflag = True
        # getter: {conditiongetter:{}}
        conditionDict = {}
        # getter:  {getter2: value}
        condition_dict = {}
        # getter: description
        bios_dict = {}
        # getter: {cmd: value}
        bios_value_dict = {}
        errordict = {}
        for bioskey, biosvalue in bios_set.items():
            conditions = bios_all_info.get(bioskey, {}).get("conditions", {})
            errorlist = []
            errorinfo = ""
            # 如果和当前值相等 不需要考虑condition
            bioskeyparent = bios_all_info.get(bioskey, {}).get("parent")
            if bioskeyparent:
                if bioskeyparent == "FixedBootPriorities":
                    # 如果是启动项，可能获取方式有区别
                    bioskeylistname = bioskey[0:-1]
                    bioskeylistid = bioskey[-1]
                    if bios_set.get(bioskey) == bios_cur.get(bioskeyparent, {}).get(bioskeylistname, [])[
                        int(bioskeylistid)]:
                        continue
                else:
                    if bios_cur.get(bioskeyparent, {}).get(bioskey) == bios_set.get(bioskey):
                        continue

            for conditionkey, conditionvalue in conditions.items():
                condition_bios_info = bios_all_info.get(conditionkey)
                # condition 的 cli 展示 key
                conditionkeyshow = condition_bios_info.get("description")
                # {bmc value: cli value}
                conditionvaluedict = condition_bios_info.get("setter")
                conditionvalueshow = conditionvaluedict.get(conditionvalue, conditionvalue)
                conditionparent = condition_bios_info.get("parent")
                # 比较当前设置值
                conditonvalue_set = None
                if bios_set.get(conditionkey):
                    conditonvalue_set = bios_set.get(conditionkey)
                elif bios_set.get(conditionparent):
                    conditonvalue_set = bios_set.get(conditionparent).get(conditionkey)
                if conditonvalue_set:
                    if conditionvalue == conditonvalue_set:
                        continue
                    else:
                        errorlist.append(self.formatCondition(conditionkeyshow, conditionvalueshow,
                                                              conditionvaluedict.get(conditonvalue_set), 1))
                        continue
                # 比较即将生效值
                if bios_future:
                    conditonvalue_future = None
                    if bios_future.get(conditionkey):
                        conditonvalue_future = bios_future.get(conditionkey)
                    elif bios_future.get(conditionparent):
                        conditonvalue_future = bios_future.get(conditionparent).get(conditionkey)
                    if conditonvalue_future:
                        if conditionvalue == conditonvalue_future:
                            continue
                        else:
                            errorlist.append(self.formatCondition(conditionkeyshow, conditionvalueshow,
                                                                  conditionvaluedict.get(conditonvalue_future), 2))
                            continue
                # 比较当前值
                conditonvalue_current = None
                if bios_cur.get(conditionkey):
                    conditonvalue_current = bios_cur.get(conditionkey)
                elif bios_cur.get(conditionparent):
                    conditonvalue_current = bios_cur.get(conditionparent).get(conditionkey)
                if conditonvalue_current:
                    if conditionvalue == conditonvalue_current:
                        continue
                    else:
                        errorlist.append(self.formatCondition(conditionkeyshow, conditionvalueshow,
                                                              conditionvaluedict.get(conditonvalue_current), 3))
                        continue
            if errorlist != []:
                errorinfo = ",".join(errorlist)
                errordict[bios_all_info.get(bioskey).get("description")] = errorinfo
        if errordict == {}:
            return True, None
        else:
            return False, errordict

    def setbootimage(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getbootimage(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getsysboot(self, client, args):
        url_result = self.get_url_info("getsysteminfo")
        res = ResultBean()
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message.get('Boot', {})
            data = collections.OrderedDict()
            time_dict = {
                "Disabled": "disabled",
                "Once": "next boot",
                "Continuous": "all future boots"
            }
            option_dict = {
                "None": "none",
                "Pxe": "pxe",
                "Cd": "cd",
                "Hdd": "hard disk",
                "BiosSetup": "BIOS Setup"
            }

            data['Timeliness'] = time_dict.get(info.get("BootSourceOverrideEnabled", "N/A"), info.get("BootSourceOverrideEnabled", "N/A"))
            data['BootOptions'] = option_dict.get(info.get("BootSourceOverrideTarget", "N/A"), info.get("BootSourceOverrideTarget", "N/A"))
            res.State("Success")
            res.Message(data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def setsysboot(self, client, args):
        res = ResultBean()
        if args.effective is None and args.device is None:
            res.State('Failure')
            res.Message('please input one parameter at lease')
            return res
        time_dict = {"Once": "Once", "Continuous": "Continuous"}
        option_dict = {"none": "None", "PXE": "Pxe", "HDD": "Hdd", "BIOSSETUP": "BiosSetup", "CD": "Cd"}
        data = {}
        if args.effective:
            data['BootSourceOverrideEnabled'] = time_dict.get(args.effective, 'Once')
        if args.device:
            data['BootSourceOverrideTarget'] = option_dict.get(args.device)
        data = {
            'Boot': data
        }
        url_result = self.get_url_info("setsysteminfo")
        patchBody = {}
        patchBody['url'] = url_result.get('url')
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getconnectmedia(self, client, args):
        # restful web
        MediaType = {1: 'CD/DVD',
                     2: 'Floppy',
                     4: 'Harddisk'}
        RedirectionStatus = {0: '~',
                             1: 'Started',
                             2: "Connection Denied",
                             3: "Login Failed",
                             4: "MAX Session Reached",
                             5: "Permission Denied",
                             6: "Unknown Error",
                             7: "Media Detach Stage",
                             8: "Maximum User Reached",
                             9: "Unable to Connect",
                             10: "Invalid Image",
                             11: "Mount Error",
                             12: "Unable to Open",
                             13: "Media License Expired",
                             14: "Connection Lost",
                             15: "Mount Cancelled By User",
                             16: "Device Ejected",
                             17: "Session Terminated",
                             100: "Starting..."
                             }
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            remotemedia_list = []
            mounttedImage = info.get("Image")
            if mounttedImage is not None and mounttedImage.strip() != "":
                remote_image = info.get("ImageName")
                general_settings = collections.OrderedDict()
                general_settings["ID"] = "1"
                general_settings["ImageType"] = 'CD/DVD'
                general_settings["ImageIndex"] = "~"
                general_settings["ImageName"] = remote_image
                if info.get("Inserted"):
                    general_settings["RedirectionStatus"] = "Started"
                else:
                    general_settings["RedirectionStatus"] = "~"
                general_settings["SessionIndex"] = "~"
                remotemedia_list.append(general_settings)
            res.State("Success")
            res.Message({"RemoteMedia": remotemedia_list})
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    # 启动停止远程镜像
    def setconnectmedia(self, client, args):

        result = ResultBean()
        if args.opType.lower() == "start":
            url_result = self.get_url_info("insertvm")

            if args.image_name[-4:] != '.iso':
                result.State('Failure')
                result.Message('The file format should be iso.')
                return result
            # 将image拆成 protocol 及  其他。
            if '://' not in args.image_name or '/' not in args.image_name:
                result.State('Failure')
                result.Message(
                    'image(-N) format should be like protocol://[username:password@]IP[:port]/directory/filename. ')
                return result
            try:
                [protocol, data] = args.image_name.split('://')
                # 校验protocol
                if protocol.lower() != 'nfs' and protocol.lower() != 'cifs' and protocol.lower() != 'smb':
                    result.State('Failure')
                    result.Message('media protocol[' + protocol + '] is not supported.')
                    return result
                # 是否包括用户名密码
                if '@' in data:
                    fplist = data.split('@')
                    filepath = fplist[-1]
                    imagefullpath = filepath
                    # 提取用户名密码
                    un_pw = data.split('@' + filepath)[0]
                    if ':' in un_pw:
                        [user, cifspd] = un_pw.split(':')
                        if protocol == "cifs":
                            if user == "" or cifspd == "":
                                result.State('Failure')
                                result.Message('Please input valid username and password')
                                return result

                    else:
                        result.State('Failure')
                        result.Message('Please input username and password')
                        return result
                else:
                    # nfs可以不要用户名密码  cifs/smb需要用户名密码
                    if protocol.lower() == "nfs":
                        imagefullpath = data
                        user = None
                        cifspd = None
                    else:
                        result.State('Failure')
                        result.Message('Please input username and password')
                        return result
            except Exception as e:
                result = ResultBean()
                result.State('Failure')
                result.Message('image(-N) format error.' + str(e))
                return result
            vmdata = {}
            vmdata['Image'] = imagefullpath
            if user and cifspd:
                vmdata['UserName'] = user
                vmdata['Password'] = cifspd
            vmdata['TransferProtocolType'] = protocol.upper()

        else:
            url_result = self.get_url_info("ejectvm")
            vmdata = {}

        postBody = {}
        postBody['json'] = vmdata
        postBody['url'] = url_result.get('url')
        result = RedfishTemplate.post_for_object(client, postBody)
        res = ResultBean()
        if result.State:
            res.State("Success")
            res.Message(result.Message)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getdns(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info("getnetwork")
        # 获取网口类型
        result_type = RedfishTemplate.get_for_object(client, [url_result.get('url')])
        dns_result = DNSBean()
        if result_type.State and result_type.Message.get(url_result.get('url')).State:
            dns_oem = result_type.Message.get(url_result.get('url')).Message.get('Oem').get('Public')
            dns_result.DNSStatus("Enable" if dns_oem.get("DNSEnabled", False) else "Disable")
            dns_result.MDNSStatus("Enable" if dns_oem.get("mDNSEnabled", False) else "Disable")
            interface_type = {member.get('@odata.id'): member.get('type') for member in
                              result_type.Message.get(url_result.get('url')).Message.get('Members', [])}
            # 获取网口具体信息
            result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
            if result.State:
                networks = result.Message
                channel_dict = {
                    "shared": "8",  # eth1
                    "dedicated": "1",  # eth0
                    "bond": "1"
                }
                for network in networks:
                    dns = network.get('Oem').get('Public').get('DNS')
                    dns_result.HostSettings("auto" if dns.get('HostNameAutoConfigedEnable', False) else "manual")
                    dns_result.Hostname(network['HostName'])
                    dns_result.DomainSettings("manual" if dns.get('DomainManual', False) else "auto")
                    dns_result.DomainName(dns['DomainName'])
                    dns_result.DNSSettings("manual" if dns.get('Manual', False) else "auto")
                    nameServers = network.get('NameServers')
                    if nameServers:
                        if len(nameServers) > 0:
                            dns_result.DNSServer1(nameServers[0])
                        if len(nameServers) > 1:
                            dns_result.DNSServer2(nameServers[1])
                        if len(nameServers) > 2:
                            dns_result.DNSServer3(nameServers[2])
                    channelNum = channel_dict.get(interface_type.get(network.get('@odata.id', 'N/A'), 'N/A'), "N/A")
                    if channelNum == "1":
                        dns_result.REGIfg1(network['Id'])
                        dns_result.REGOption1(dns.get('RegistionOption', 'N/A'))
                    elif channelNum == "8":
                        dns_result.REGIfg2(network['Id'])
                        dns_result.REGOption2(dns.get('RegistionOption', 'N/A'))
                res.State('Success')
                res.Message([dns_result.dict])
            else:
                res = result
        elif not result_type.State:
            res.Message(result_type.Message)
        elif not result_type.Message.get(url_result.get('url')).State:
            res.Message(result_type.Message.get(url_result.get('url')).Message)
        return res

    def setdns(self, client, args):
        result = ResultBean()
        args.mdns = None
        url_result = self.get_url_info("getnetwork")
        data = {}
        dns_set = {"Oem": {"Public": data}}
        if args.dns is not None or args.mdns is not None:
            if args.dns is not None:
                data["DNSEnabled"] = True if 'enable' == args.dns else False
            if args.mdns is not None:
                data["mDNSEnabled"] = True if 'enable' == args.mdns else False
            patchBody = {}
            patchBody['url'] = url_result.get('url')
            patchBody['json'] = dns_set
            dns_res = RedfishTemplate.patch_for_object(client, patchBody)
            if not dns_res.State:
                result.State("Failure")
                result.Message([dns_res.Message])
                return result

        registration = {
            'dhcp': 'DHCPClientFQDN',
            'hostname': 'Hostname',
            'nsupdate': 'nsupdate'
        }
        # 获取网口类型
        result_type = RedfishTemplate.get_for_object(client, [url_result.get('url')])
        if result_type.State and result_type.Message.get(url_result.get('url')).State:
            dns_msg = result_type.Message.get(url_result.get('url')).Message
            dns_oem = dns_msg.get('Oem').get('Public')
            members = dns_msg.get('Members')
            for member in members:
                data = {}
                dns_set = {"Oem": {"Public": {"DNS": data}}}
                url = member.get('@odata.id')
                type = member.get('type')
                if args.hostManual:
                    if args.hostManual == 'auto':
                        data['HostNameAutoConfigedEnable'] = True
                    elif args.hostManual == 'manual':
                        data['HostNameAutoConfigedEnable'] = False
                        if args.hostName is not None:
                            dns_set['HostName'] = args.hostName
                if 'shared' == type:
                    if args.registrationMethod2:
                        data['RegistionOption'] = registration.get(args.registrationMethod2)
                else:
                    if args.registrationMethod1:
                        data['RegistionOption'] = registration.get(args.registrationMethod1)
                if args.domainManual:
                    if args.domainManual == 'auto':
                        data['DomainManual'] = False
                        if args.domainName is not None:
                            result.State('Failure')
                            result.Message(['host name(-DN) can not be set when domain settings is auto.'])
                            return result
                    elif args.domainManual == 'manual':
                        data['DomainManual'] = True
                        if 'RegistionOption' not in data.keys() or data['RegistionOption'] == 'hostname':
                            result.State('Failure')
                            result.Message(["The 'registrationMethod' field needs to be set either 'nsupdate' or 'dhcp' simultaneously"])
                            return result
                        if args.domainName is None or args.domainName == "":
                            result.State('Failure')
                            result.Message(['-DN parameter is needed.'])
                            return result
                        else:
                            data['DomainName'] = args.domainName
                if args.dnsManual:
                    if args.dnsManual == 'auto':
                        data['Manual'] = False
                    elif args.dnsManual == 'manual':
                        data['Manual'] = True
                        servers = []
                        if args.dnsServer1 is not None:
                            servers.append(args.dnsServer1)
                        if args.dnsServer2 is not None:
                            servers.append(args.dnsServer2)
                        if args.dnsServer3 is not None:
                            servers.append(args.dnsServer3)
                        dns_set['NameServers'] = servers
                patchBody = {}
                patchBody['url'] = url
                patchBody['json'] = dns_set
                dns_res = RedfishTemplate.patch_for_object(client, patchBody)
                if not dns_res.State:
                    result.State("Failure")
                    result.Message([dns_res.Message])
                    return result
        elif not result_type.State:
            result.Message([result_type.Message])
        elif not result_type.Message.get(url_result.get('url')).State:
            result.Message([result_type.Message.get(url_result.get('url')).Message])
        result.State("Success")
        result.Message(["DNS is reseting, please wait for a few minutes."])
        return result

    def getfan(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            fanpower = result.Message.get("Oem", {}).get("Public", {}).get("CurrentFANPowerWatts", 'N/A')
            data = {}
            fans = result.Message.get('Fans', [])
            data['count'] = len(fans)
            data['power'] = fanpower
            if data['count'] > 0:
                # 所有风扇的状态一致，取第一个风扇的状态
                data['mode'] = result.Message.get('Oem', {}).get('Public', {}).get('FanControlMode', 'N/A')
                data['fans'] = [{'ID': fan.get('MemberId', 'N/A'),
                                 'FanName': fan.get('Name', 'N/A'),
                                 'Present': "Present" if "enable" in str(fan.get('Status', {}).get('State', 'N/A')).lower() else "Absent",
                                 'Status': fan.get('Status', {}).get('Health', 'N/A'),
                                 'SpeedRPM': fan.get('Reading', 'N/A'),
                                 'DutyRatio(%)': fan.get('Oem', {}).get('Public', {}).get('SpeedRatio', 'N/A')} for fan
                                in fans]
            res.State('Success')
            res.Message(data)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def fancontrol(self, client, args):
        def patch_mode_func(data, responses):
            get_data = responses.json()
            fans = get_data.get("Fans", [])
            fannum = len(fans)
            if fannum == 0:
                return ResultBean.fail('cannot get fan info.')
            currentmode = get_data.get("Oem", {}).get("Public", {}).get("FanControlMode", "")
            if str(currentmode).lower() == "manual":
                if data.get("FanControlMode") == "Manual":
                    return ResultBean.fail('NothingToDo')
            else:
                if data.get("FanControlMode") == "Auto":
                    return ResultBean.fail('NothingToDo')
            patch_body = {"Oem": {"Public": data}}
            return ResultBean.success(patch_body)

        def setfanmode(mode):
            url_result = self.get_url_info("getfan")
            patchBody = {}
            patchBody['url'] = str(url_result.get('url'))
            patchBody['json'] = {"FanControlMode": mode}
            patchBody['func'] = patch_mode_func
            result = RedfishTemplate.patch_for_object(client, patchBody)
            res = ResultBean()
            if result.State:
                res.State('Success')
                res.Message('Set fan mode to ' + mode + ' successfully.')
            else:
                if result.Message == "NothingToDo":
                    res.State('Success')
                    res.Message('Fan mode is ' + mode + '. Nothing need to do.')
                else:
                    res.State('Failure')
                    res.Message(result.Message)
            return res

        def patch_fan_func(data, responses):
            get_data = responses.json()
            fans = get_data.get("Fans", [])
            fannum = len(fans)
            if fannum == 0:
                return ResultBean.fail('cannot get fan info.')
            if data.get("MemberId") == 255:
                fans_set_data = []
                for fan in fans:
                    single_data = {
                        "Oem": {
                            "Public": {
                                "SpeedRatio": data.get("SpeedRatio"),
                                "FanIndex": int(fan.get("MemberId"))
                            }
                        }
                    }
                    fans_set_data.append(single_data)
            else:
                # 风扇是否存在
                existflag = False
                for fan in fans:
                    if fan.get("MemberId") == str(data.get("MemberId")):
                        existflag = True
                        break
                if not existflag:
                    return ResultBean.fail('Invalid fan id, choose fan id by getFan.')
                fans_set_data = [
                    {
                        "Oem": {
                            "Public": {
                                "SpeedRatio": data.get("SpeedRatio"),
                                "FanIndex": data.get("MemberId")
                            }
                        }
                    }
                ]
            patch_body = {"Fans": fans_set_data, "Oem": {"Public": {"FanControlMode": "Manual"}}}
            return ResultBean.success(patch_body)

        def setfanspeed(id, speed):
            url_result = self.get_url_info("setfan")
            data = {}
            data["ControlMode"] = "Manual"
            data["MemberId"] = int(id)
            data["SpeedRatio"] = int(speed)
            patchBody = {}
            patchBody['url'] = str(url_result.get('url'))
            patchBody['func'] = patch_fan_func
            patchBody['json'] = data
            result = RedfishTemplate.patch_for_object(client, patchBody)
            res = ResultBean()
            if result.State:
                res.State('Success')
                res.Message('Set fan speed successfully.')
            else:
                res.State('Failure')
                res.Message(result.Message)
            return res

        result = ResultBean()
        if args.fanspeedlevel is None and args.mode is None:
            result.State("Failure")
            result.Message("Please input a command.")
            return result
        if args.fanspeedlevel is not None:
            if args.fanspeedlevel < 20 or args.fanspeedlevel > 100:
                result.State("Failure")
                result.Message("fanspeedlevel in range of 20-100")
                return result

        if args.mode == 'Automatic' or args.mode == "auto":
            return setfanmode('Auto')
        elif args.mode == 'manual' and args.id is None:
            # res = ResultBean()
            res = setfanmode('Manual')
            if res.State != "Success":
                return res
            if args.fanspeedlevel is not None and args.id is None:
                args.id = "255"
                return setfanspeed(str(args.id), args.fanspeedlevel)
            else:
                return res
        else:
            if args.fanspeedlevel is None:
                result.State("Failure")
                result.Message("fanspeedlevel is needed.")
                return result
            if args.id is None:
                args.id = "255"
            return setfanspeed(str(args.id), args.fanspeedlevel)

    def cleareventlog(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        postBody = {}
        postBody['url'] = url_result.get('url')
        result = RedfishTemplate.post_for_object(client, postBody)
        res = ResultBean()
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def collect(self, client, args):
        global time
        def onekey_end(json_data):
            flag = False
            try:
                if "Complete" in json_data.get("TaskState") and int(json_data.get('PercentComplete')) == 100:
                    flag = True
                return flag
            except:
                return False

        checkparam_res = ResultBean()
        if args.fileurl == ".":
            file_name = ""
            file_path = os.path.abspath(".")
            args.fileurl = os.path.join(file_path, file_name)
        elif args.fileurl == "..":
            file_name = ""
            file_path = os.path.abspath("..")
            args.fileurl = os.path.join(file_path, file_name)
        elif re.search("^[C-Zc-z]\:$", args.fileurl, re.I):
            file_name = ""
            file_path = os.path.abspath(args.fileurl + "\\")
            args.fileurl = os.path.join(file_path, file_name)
        else:
            file_name = os.path.basename(args.fileurl)
            file_path = os.path.dirname(args.fileurl)
        # 只输入文件名字，则默认为当前路径
        if file_path == "":
            file_path = os.path.abspath(".")
            args.fileurl = os.path.join(file_path, file_name)

        # 用户输入路径，则默认文件名dump_psn_time.tar.gz
        if file_name == "":
            psn = "UNKNOWN"
            res = self.getfru(client, args)
            if res.State == "Success":
                frulist = res.Message[0].get("FRU", [])
                if frulist != []:
                    psn = frulist[0].get('ProductSerial', 'UNKNOWN')
            else:
                return res
            import time
            struct_time = time.localtime()
            logtime = time.strftime("%Y%m%d-%H%M", struct_time)
            file_name = "dump_" + psn + "_" + logtime + ".tar.gz"
            args.fileurl = os.path.join(file_path, str(file_name))
        else:
            file_name = str(file_name)
            p = '\.tar\.gz$'
            if not re.search(p, file_name, re.I):
                checkparam_res.State("Failure")
                checkparam_res.Message(["Filename should be xxx.tar.gz"])
                return checkparam_res
            file_name = file_name[0:-7] + ".tar.gz"

        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except:
                checkparam_res.State("Failure")
                checkparam_res.Message(["can not create path."])
                return checkparam_res
        else:
            if os.path.exists(args.fileurl):
                name_id = 1
                name_new = file_name[:-7] + "(1).tar.gz"
                file_new = os.path.join(file_path, name_new)
                while os.path.exists(file_new):
                    name_id = name_id + 1
                    name_new = file_name[:-7] + "(" + str(name_id) + ")" + ".tar.gz"
                    file_new = os.path.join(file_path, name_new)
                args.fileurl = file_new

        result = ResultBean()
        url_process = self.get_url_info("get_onekey_process")
        get_status_res = RedfishTemplate.get_for_object_single(client, url_process.get('url'))
        if not get_status_res.State or (get_status_res.State and get_status_res.Message.get("TaskState") != "Running"):
            url_collect = self.get_url_info("onekey_collect")
            postBody = {}
            postBody['url'] = url_collect.get('url')
            collect_res = RedfishTemplate.post_for_object(client, postBody)
            if not collect_res.State:
                result.State("Failure")
                result.Message(collect_res.Message)
                return result
        time.sleep(1)
        get_process_res = RedfishTemplate.get_for_object_cycle(client, url_process.get('url'), 60, onekey_end)
        if get_process_res.State:
            url_download = self.get_url_info("onekey_download")
            postBody = {}
            postBody['url'] = url_download.get('url')
            download_res = RedfishTemplate.post_for_object(client, postBody)
            if download_res.State:
                download_info = download_res.Message
                try:
                    with open(args.fileurl, 'wb') as f:
                        f.write(download_info.content)
                        f.close()
                    result.State("Success")
                    result.Message("log file path is " + str(args.fileurl))
                except:
                    result.State("Failure")
                    result.Message("please check the path: " + str(args.fileurl))
            else:
                result.State("Failure")
                result.Message(download_res.Message)
        else:
            result.State("Failure")
            result.Message(get_process_res.Message)
        # else:
        #     result.State("Failure")
        #     result.Message("get onekey log task failed.")
        return result

    def getgpu(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            gpu_info = result.Message
            data = {}
            data_gpu = []
            for item in gpu_info:
                if item.get('ProcessorType') == "GPU":
                    single_data = collections.OrderedDict()
                    single_data['ID'] = item.get('Id', "N/A")
                    single_data['Name'] = item.get('Name', "N/A")
                    single_data['VendorId'] = item.get('ProcessorId', {}).get('VendorId', "N/A")
                    single_data['DeviceID'] = item.get('Model', "N/A")
                    single_data['SerialNumber'] = item.get('Oem', {}).get('Public', {}).get('SerialNumber', "N/A")
                    single_data['Present'] = "Present" if "enable" in str(item.get('Status', {}).get('State', "N/A")).lower() else "Absent"
                    single_data['Health'] = item.get('Status', {}).get('Health', "N/A")
                    data_gpu.append(single_data)
            data['GPU'] = data_gpu
            res.State("Success")
            res.Message(data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getcpu(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            cpu_info = result.Message
            data = {}
            data['Maximum'] = len(cpu_info)
            data_cpu = []
            for item in cpu_info:
                single_data = collections.OrderedDict()
                if "ProcessorType" in item.keys() and item['ProcessorType'] != "CPU":
                    continue
                single_data['ID'] = item.get('Id', "N/A")
                single_data['Model'] = item.get('Model', "N/A")
                single_data['CPUPresent'] = "Present" if "enable" in str(item.get('Status', {}).get('State', "N/A")).lower() else "Absent"
                single_data['CPUStatus'] = item.get('Status', {}).get('Health', "N/A")
                single_data['ProSpeed(MHZ)'] = item.get('Oem', {}).get('Public', {}).get('CurrentSpeedMHz', "N/A")
                single_data['MaxSpeed(MHZ)'] = item.get('MaxSpeedMHz', "N/A")
                single_data['TotalCores'] = item.get('TotalCores', "N/A")
                single_data['TotalThreads'] = item.get('TotalThreads', "N/A")
                # single_data['L1Cache(KB)'] = item.get('Oem', {}).get('Public', {}).get('L1CacheKiB', "N/A")
                # single_data['L2Cache(KB)'] = item.get('Oem', {}).get('Public', {}).get('L2CacheKiB', "N/A")
                # single_data['L3Cache(KB)'] = item.get('Oem', {}).get('Public', {}).get('L3CacheKiB', "N/A")
                ProcessorMemory = item.get("ProcessorMemory", [])
                if ProcessorMemory is not None and isinstance(ProcessorMemory, list) and len(ProcessorMemory) > 0:
                    for p_item in ProcessorMemory:
                        if p_item.get("MemoryType", "N/A") == "L1Cache":
                            if "CapacityKB" in p_item:
                                single_data['L1Cache(KB)'] = p_item.get("CapacityKB", "N/A")
                            elif "CapacityMiB" in p_item:
                                single_data['L1Cache(KB)'] = p_item.get("CapacityMiB") * 1024
                            else:
                                single_data['L1Cache(KB)'] = "N/A"
                        elif p_item.get("MemoryType", "N/A") == "L2Cache":
                            if "CapacityKB" in p_item:
                                single_data['L2Cache(KB)'] = p_item.get("CapacityKB", "N/A")
                            elif "CapacityMiB" in p_item:
                                single_data['L2Cache(KB)'] = p_item.get("CapacityMiB") * 1024
                            else:
                                single_data['L2Cache(KB)'] = "N/A"
                        elif p_item.get("MemoryType", "N/A") == "L3Cache":
                            if "CapacityKB" in p_item:
                                single_data['L3Cache(KB)'] = p_item.get("CapacityKB", "N/A")
                            elif "CapacityMiB" in p_item:
                                single_data['L3Cache(KB)'] = p_item.get("CapacityMiB") * 1024
                            else:
                                single_data['L3Cache(KB)'] = "N/A"
                else:
                    single_data['L1Cache(KB)'] = "N/A"
                    single_data['L2Cache(KB)'] = "N/A"
                    single_data['L3Cache(KB)'] = "N/A"


                single_data['PPIN'] = item.get('Oem', {}).get('Public', {}).get('SerialNumber', "N/A")
                single_data['MicroCode'] = item.get('ProcessorId', {}).get('MicrocodeInfo', "N/A")
                # single_data['TurboEnableMaxSpeed(MHz)'] = item.get('Oem', {}).get('Public', {}).get(
                #     'TurboEnableMaxSpeedMHz', "N/A")
                # single_data['TurboDisableMaxSpeed(MHz)'] = item.get('Oem', {}).get('Public', {}).get(
                #     'TurboDisableMaxSpeedMHz', "N/A")
                # single_data['VendorId'] = item.get('ProcessorId', {}).get('VendorId', "N/A")
                # single_data['IdentificationRegisters'] = item.get('ProcessorId', {}).get('IdentificationRegisters',
                #                                                                          "N/A")
                # single_data['EffectiveFamily'] = item.get('ProcessorId', {}).get('EffectiveFamily', "N/A")
                # single_data['Step'] = item.get('ProcessorId', {}).get('Step', "N/A")
                single_data['InstructionSet'] = item.get('InstructionSet', "N/A")
                # single_data['ProcessorArchitecture'] = item.get('ProcessorArchitecture', "N/A")
                single_data['Vendor'] = item.get('Manufacturer', "N/A")
                data_cpu.append(single_data)
            data['CPU'] = data_cpu
            res.State("Success")
            res.Message(data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getmemory(self, client, args):
        res = ResultBean()
        data = {}
        url_chassis = self.get_url_info("getchassis")
        result_chassis = RedfishTemplate.get_for_object_single(client, url_chassis.get('url'))
        if result_chassis.State:
            chassisAll = result_chassis.Message
            data["NumberOfSlot"] = chassisAll.get("Oem", {}).get("Public", {}).get("DeviceMaxNum", {}).get("MemoryNum","N/A")

        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        if result.State:
            memories = result.Message
            data['count'] = len(memories)
            if data['count'] > 0:
                data['volume'] = 0
                data['memories'] = []
                for memory in memories:
                    single_mem = collections.OrderedDict()
                    single_mem['MemId'] = memory.get('Id', 'N/A')
                    single_mem['MemPresent'] = "Present" if "enable" in str(
                        memory.get('Status', {}).get('State', 'N/A')).lower() else "Absent"
                    single_mem['MemStatus'] = memory.get('Status', {}).get('Health', 'N/A')
                    single_mem['MemPartNum'] = memory.get('PartNumber', 'N/A')
                    single_mem['MemVendor'] = memory.get('VendorID', 'N/A')
                    single_mem['MemSize(GB)'] = int(int(memory.get('CapacityMiB', 0)) / 1024)
                    single_mem['MemType'] = memory.get('MemoryDeviceType', 'N/A')
                    single_mem['MemRank'] = memory.get('RankCount', 'N/A')
                    single_mem['DataWidthBits'] = memory.get('DataWidthBits', 'N/A')
                    single_mem['CurrentFrequency(MHZ)'] = memory.get('OperatingSpeedMhz', memory.get('CurrentSpeedMhz', 'N/A'))
                    aslist = memory.get('AllowedSpeedsMHz')
                    if aslist and isinstance(aslist, list):
                        single_mem['MaxFrequency(MHZ)'] = aslist[0]
                    else:
                        single_mem['MaxFrequency(MHZ)'] = "N/A"
                    single_mem['MemMediaType'] = memory.get('MemoryType', 'N/A')
                    single_mem['MemSerialNum'] = memory.get('SerialNumber', 'N/A')
                    single_mem['MemBaseModule'] = memory.get('BaseModuleType', 'N/A')
                    single_mem['Voltage(mV)'] = memory.get('Oem', {}).get('Public', {}).get('Voltage', "N/A")
                    data['memories'].append(single_mem)
                    data['volume'] += int(memory.get('CapacityMiB', 0) / 1024)
            res.State("Success")
            res.Message(data)
        else:
            res = result
        return res

    def getbackplane(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data_sum = []
            for item in info:
                single_data = collections.OrderedDict()
                single_data['ID'] = item.get('Id', "N/A")
                single_data['Present'] = "Present" if "enable" in str(item.get('Status', {}).get('State', "N/A")).lower() else "Absent"
                # single_data['Name'] = item.get('Name', "N/A")
                # single_data['Manufacturer'] = item.get('Manufacturer', "N/A")
                # single_data['SerialNumber'] = item.get('SerialNumber', "N/A")
                # single_data['PartNumber'] = item.get('PartNumber', "N/A")
                single_data['FwVersion'] = item.get('BackplaneVersion', "N/A")
                single_data['TotalSlotCount'] = item.get('PortCount', "N/A")
                single_data['Temperature'] = item.get('Temperature', "N/A")
                # single_data['Status'] = item.get('Status', {}).get('Health', "N/A")
                data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getpsu(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message.get('PowerSupplies')
            if info is None:
                res.State("Failure")
                res.Message('cannot get Power Supplies')
                return res
            data_sum = []
            for item in info:
                single_data = collections.OrderedDict()
                single_data['ID'] = item.get('Name', "N/A").replace(" ","")
                single_data['Present'] = "Present" if "enable" in str(item.get('Status', {}).get('State', "N/A")).lower() else "Absent"
                single_data['Status'] = item.get('Status', {}).get('Health', "N/A")
                single_data['Vendor'] = item.get('Manufacturer', "N/A")
                single_data['Model'] = item.get('Model', "N/A")
                single_data['SerialNumber'] = item.get('SerialNumber', "N/A")
                single_data['PartNumber'] = item.get('PartNumber', "N/A")
                single_data['RatedPowerWatts(W)'] = item.get('PowerCapacityWatts', "N/A")
                single_data['FwVersion'] = item.get('FirmwareVersion', "N/A")
                single_data['Temperature'] = item.get("Oem", {}).get("Public", {}).get('EnvironmentTemperature', "N/A")
                single_data['PIN(W)'] = item.get('PowerInputWatts', "N/A")
                single_data['POUT(W)'] = item.get('LastPowerOutputWatts', "N/A")
                single_data['VIN(V)'] = item.get("Oem", {}).get("Public", {}).get('OutputCurrent', "N/A")
                single_data['VOUT(V)'] = item.get("Oem", {}).get("Public", {}).get('OutputVolt', "N/A")
                single_data['IIN(A)'] = item.get("Oem", {}).get("Public", {}).get('InputCurrent', "N/A")
                single_data['IOUT(A)'] = item.get("Oem", {}).get("Public", {}).get('OutputCurrent', "N/A")
                single_data['WorkMode'] = item.get("Oem", {}).get("Public", {}).get('WorkMode', "N/A")
                data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def check_filepath(self, client, args):
        checkparam_res = ResultBean()
        if args.file_url is None:
            file_name = ""
            file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "logs"))
            args.file_url = os.path.join(file_path, file_name)
        elif args.file_url == ".":
            file_name = ""
            file_path = os.path.abspath(".")
            args.file_url = os.path.join(file_path, file_name)
        elif args.file_url == "..":
            file_name = ""
            file_path = os.path.abspath("..")
            args.file_url = os.path.join(file_path, file_name)
        elif re.search("^[C-Zc-z]\:$", args.file_url, re.I):
            file_name = ""
            file_path = os.path.abspath(args.file_url + "\\")
            args.file_url = os.path.join(file_path, file_name)
        else:
            file_name = os.path.basename(args.file_url)
            file_path = os.path.dirname(args.file_url)
        # 只输入文件名字，则默认为当前路径
        if file_path == "":
            file_path = os.path.abspath(".")
            args.file_url = os.path.join(file_path, file_name)
        if file_name == "":
            import time
            struct_time = time.localtime()
            logtime = time.strftime("%Y%m%d-%H%M", struct_time)
            file_name = client.host + "-downtime-" + logtime + ".jpeg"
            args.file_url = os.path.join(file_path, file_name)
        else:
            p = '\.jpeg$'
            if not re.search(p, file_name, re.I):
                checkparam_res.State("Failure")
                checkparam_res.Message("Filename should be xxx.jpeg")
                return checkparam_res

        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except:
                checkparam_res.State("Failure")
                checkparam_res.Message("can not create path.")
                return checkparam_res
        else:
            if os.path.exists(args.file_url):
                name_id = 1
                name_new = file_name[:-5] + "(1).jpeg"
                file_new = os.path.join(file_path, name_new)
                while os.path.exists(file_new):
                    name_id = name_id + 1
                    name_new = file_name[:-5] + "(" + str(name_id) + ")" + ".jpeg"
                    file_new = os.path.join(file_path, name_new)
                args.file_url = file_new

        checkparam_res.State("Success")
        checkparam_res.Message(args.file_url)
        return checkparam_res

    def manualscreenshot(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        if args.option == "capture":
            check_res = self.check_filepath(client, args)
            if check_res.State == "Success":
                args.url = check_res.Message
                postBody = {}
                postBody['url'] = url_result.get('url')[0]
                postBody['json'] = None
                set_result = RedfishTemplate.post_for_object(client, postBody)
                if set_result.State:
                    get_result = RedfishTemplate.get_for_object_single(client, url_result.get('url')[1])
                    if get_result.State:
                        with open(args.url, 'wb') as f:
                            f.write(get_result.Message.content)
                        res.State("Success")
                        res.Message("File path: " + str(args.url))
                    else:
                        res.State("Failure")
                        res.Message(get_result.Message)
                else:
                    res.State("Failure")
                    res.Message(set_result.Message)
            else:
                return check_res
        else:
            del_result = RedfishTemplate.delete_for_object(client, url_result.get('url')[2])
            if del_result.State:
                res.State("Success")
                res.Message("")
            else:
                res.State("Failure")
                res.Message(del_result.Message)
        return res

    def getbmclogsettings(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            logsettings = result.Message
            # data = {'ServiceEnabled': logsettings.get('ServiceEnabled', 'N/A')}
            data = collections.OrderedDict()
            enable_dict = {
                "LocalEnable": "Local",
                "RemoteEnable": "Remote&Local"
            }
            data['Syslog'] = enable_dict.get(logsettings.get('ServiceSyslogEnable', 'N/A'), "N/A")
            data['SyslogTag'] = logsettings.get('ServiceSyslogTag', 'N/A')
            data['SyslogLevel'] = logsettings.get('AlarmSeverity', 'N/A')
            data['SyslogProtocol'] = logsettings.get('TransmissionProtocol', 'N/A')
            servers = logsettings.get('SyslogServers', [])
            data['servers'] = [{'DestIndex': server.get('MemberId', 'N/A'),
                                'Enable': "enable" if "enable" in str(server.get('Enabled', 'N/A')).lower() else "disable",
                                'HostName': server.get('Address', 'N/A'),
                                'SyslogPort': server.get('Port', 'N/A'),
                                'SyslogType': str(server.get('Logtype', 'N/A')).lower()} for
                               server in servers]
            res.State('Success')
            res.Message(data)
        elif not result.State:
            res = result
        elif not result.Message.get(url_result.get('url')[0]).State:
            res = result.Message.get(url_result.get('url')[0])
        return res

    def setbmclogcfg(self, client, args):
        res = ResultBean()
        if args.serverPort is not None:
            if not isinstance(args.serverPort, int) or args.serverPort < 0 or args.serverPort > 65535:
                res.State('Failure')
                res.Message('serverPort should be a positive integer(0-65535)')
                return res

        url_result = self.get_url_info("getbmclogsettings")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            if "Remote" not in str(result.Message.get('ServiceSyslogEnable', "")) and \
                    (args.status is None or args.status != 'enable'):
                res.State('Failure')
                res.Message('remote log setting not enable.')
                return res
            if args.test:
                for server in result.Message.get('SyslogServers', []):
                    if server['MemberId'] == args.serverId:
                        if server['Enabled'] == 'Enable':
                            break
                        else:
                            res.State('Failure')
                            res.Message(str(args.serverId) + ' syslog server not enable.')
                            return res
                # for 正常循环结束会进入else，break退出不会进else
                else:
                    res.State('Failure')
                    res.Message("can not get " + str(args.serverId) + " syslog server settings.")
                    return res
                data = {'MemberId': args.serverId}
                url_result = self.get_url_info("sendbmcsyslogtest")
                postBody = {}
                postBody['url'] = url_result.get('url')
                postBody['json'] = data
                test_result = RedfishTemplate.post_for_object(client, postBody)
                if test_result.State:
                    res.State('Success')
                    res.Message("")
                else:
                    res.State('Failure')
                    res.Message(test_result.Message)
            else:
                data = result.Message
                # 删除设置时不需要传递的key
                if '@odata.id' in data:
                    del data['@odata.id']
                if '@odata.type' in data:
                    del data['@odata.type']
                if 'Actions' in data:
                    del data['Actions']
                if 'Description' in data:
                    del data['Description']
                if 'Id' in data:
                    del data['Id']
                if 'Name' in data:
                    del data['Name']
                if 'ServiceEnabled' in data:
                    del data['ServiceEnabled']  # 'SyslogEnable' 一直是True， 暂不清楚如何设置
                if args.status:
                    data['ServiceSyslogEnable'] = 'RemoteEnable' if args.status == 'enable' else 'LocalEnable'
                if args.level:
                    data['AlarmSeverity'] = args.level
                if args.hosttag:
                    if args.hosttag == "AssertTag":
                        data['ServiceSyslogTag'] = "PartNumber"
                    else:
                        data['ServiceSyslogTag'] = args.hosttag
                if args.protocolType:
                    data['TransmissionProtocol'] = args.protocolType
                if args.serverId is not None:
                    server_info = None
                    for item in data.get('SyslogServers', []):
                        if str(item.get("MemberId", "N/A")) == str(args.serverId):
                            server_info = item
                            break
                    if server_info is None:
                        res.State('Failure')
                        res.Message("can not get syslog server info.")
                        return res
                    if args.serverAddr:
                        server_info['Address'] = args.serverAddr
                    if args.serverPort:
                        server_info['Port'] = args.serverPort
                    if args.logType:
                        type_info = {'idl': 'IDL', 'audit': 'Audit', 'none': 'None', 'both': 'Audit+IDL'}
                        server_info['Logtype'] = type_info.get(args.logType)
                    if args.serverStatus:
                        serverStatus_dict = {
                            "enable": "Enable",
                            "disable": "Disable"
                        }
                        server_info['Enabled'] = serverStatus_dict.get(args.serverStatus)
                    data['SyslogServers'] = [server_info]
                else:
                    del data['SyslogServers']
                url_result = self.get_url_info(sys._getframe().f_code.co_name)
                patchBody = {}
                patchBody['url'] = url_result.get('url')
                patchBody['json'] = data
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    res.State('Success')
                    res.Message("")
                else:
                    res.State('Failure')
                    res.Message(set_result.Message)
        else:
            res.State('Failure')
            res.Message("can not get syslog server settings.")
        return res

    def screenmanual(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info('manualscreenshot')
        if args.type == "capture":
            postBody = {}
            postBody['url'] = url_result.get('url')[0]
            postBody['json'] = None
            set_result = RedfishTemplate.post_for_object(client, postBody)
            if set_result.State:
                res.State("Success")
                res.Message("")
            else:
                res.State("Failure")
                res.Message(set_result.Message)
        else:
            del_result = RedfishTemplate.delete_for_object(client, url_result.get('url')[2])
            if del_result.State:
                res.State("Success")
                res.Message("")
            else:
                res.State("Failure")
                res.Message(del_result.Message)
        return res

    def downscreenmanual(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info('manualscreenshot')
        check_res = self.check_filepath(client, args)
        if check_res.State == "Success":
            args.file_url = check_res.Message
            get_result = RedfishTemplate.get_for_object_single(client, url_result.get('url')[1])
            if get_result.State:
                with open(args.file_url, 'wb') as f:
                    f.write(get_result.Message.content)
                res.State("Success")
                res.Message("File path: " + str(args.file_url))
            else:
                res.State("Failure")
                res.Message(get_result.Message)
        else:
            return check_res
        return res

    def downscreen(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info("downloadautocapture")
        check_res = self.check_auto_filepath(client, args)
        if check_res.State == "Success":
            args.file_url = check_res.Message

            get_result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
            if get_result.State:
                with open(args.file_url, 'wb') as f:
                    f.write(get_result.Message.content)
                res.State("Success")
                res.Message("File path: " + str(args.file_url))
            else:
                res.State("Failure")
                res.Message(get_result.Message)
        else:
            return check_res

        return res


    def check_auto_filepath(self, client, args):
        checkparam_res = ResultBean()
        if args.file_url is None:
            file_name = ""
            file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "logs"))
            args.file_url = os.path.join(file_path, file_name)
        elif args.file_url == ".":
            file_name = ""
            file_path = os.path.abspath(".")
            args.file_url = os.path.join(file_path, file_name)
        elif args.file_url == "..":
            file_name = ""
            file_path = os.path.abspath("..")
            args.file_url = os.path.join(file_path, file_name)
        elif re.search("^[C-Zc-z]\:$", args.file_url, re.I):
            file_name = ""
            file_path = os.path.abspath(args.file_url + "\\")
            args.file_url = os.path.join(file_path, file_name)
        else:
            file_name = os.path.basename(args.file_url)
            file_path = os.path.dirname(args.file_url)
        # 只输入文件名字，则默认为当前路径
        if file_path == "":
            file_path = os.path.abspath(".")
            args.file_url = os.path.join(file_path, file_name)
        if file_name == "":
            import time
            struct_time = time.localtime()
            logtime = time.strftime("%Y%m%d-%H%M", struct_time)
            file_name = client.host + "-downtime-" + logtime + ".tar.gz"
            args.file_url = os.path.join(file_path, file_name)
        else:
            p = '\.jpeg$'
            if not re.search(p, file_name, re.I):
                checkparam_res.State("Failure")
                checkparam_res.Message("Filename should be xxx.jpeg")
                return checkparam_res

        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except:
                checkparam_res.State("Failure")
                checkparam_res.Message("can not create path.")
                return checkparam_res
        else:
            if os.path.exists(args.file_url):
                name_id = 1
                name_new = file_name[:-5] + "(1).jpeg"
                file_new = os.path.join(file_path, name_new)
                while os.path.exists(file_new):
                    name_id = name_id + 1
                    name_new = file_name[:-5] + "(" + str(name_id) + ")" + ".jpeg"
                    file_new = os.path.join(file_path, name_new)
                args.file_url = file_new

        checkparam_res.State("Success")
        checkparam_res.Message(args.file_url)
        return checkparam_res


    def getncsi(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info('getnetwork')
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message.get('Oem', {}).get('Public', {}).get('NCSI')
            if info is not None and isinstance(info, dict):
                data = collections.OrderedDict()
                data['NCSIMode'] = info.get('Mode', 'N/A')
                data['NicName'] = info.get('Interface', 'N/A')
                data['Port'] = info.get('Port', 'N/A')
                data['Nicinfo'] = info.get('Support', [])
                res.State('Success')
                res.Message(data)
            else:
                res.State('Failure')
                res.Message('get NCSI key failed.')
        else:
            res.State('Failure')
            res.Message(str(result.Message))
        return res

    # 设置提示成功，但是未生效，重启BMC再次获取仍不生效
    def setncsi(self, client, args):
        res = ResultBean()
        if args.mode == "auto" and args.channel_number is not None:
            res.State('Failure')
            res.Message('port cannot be set when NCSI mode is auto')
            return res
        if args.channel_number:
            if not isinstance(args.channel_number, int) or args.channel_number < 1:
                res.State('Failure')
                res.Message('portnumber should be a positive integer')
                return res
        url_result = self.get_url_info('getnetwork')
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            if args.mode == "auto":
                mode = "AutoFailover"
            else:
                mode = "Manual"
            info = result.Message.get('Oem', {}).get('Public', {}).get('NCSI')
            if info is not None and isinstance(info, dict):
                support_list = info.get('Support', [])
                support_dict = {}
                for item in support_list:
                    if "Interface" in item and "PortNumber" in item:
                        support_dict[item.get('Interface')] = item.get('PortNumber')
                if args.nic_type:
                    if args.nic_type not in support_dict.keys():
                        res.State("Failure")
                        res.Message("please choose -N from " + str(list(support_dict.keys())))
                        return res
                else:
                    args.nic_type = info.get('Interface', 'N/A')
                if args.channel_number:
                    if args.channel_number and mode == "Manual":
                        if args.channel_number not in [i for i in range(int(support_dict.get(args.nic_type)))]:
                            res.State("Failure")
                            res.Message("please choose -PN/-C from " + str([i for i in range(int(support_dict.get(args.nic_type)))]))
                            return res
                else:
                    args.channel_number = info.get('Port', 'N/A')

                patch_data = {
                    'Mode': mode,
                    'Interface': args.nic_type,
                    'Port': args.channel_number
                }
                patch_data = {
                    "Oem": {
                            "Public": {
                                'NCSI': patch_data
                            }
                    }
                }
                patchBody = {}
                patchBody['url'] = str(url_result.get('url'))
                patchBody['json'] = patch_data
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    res.State('Success')
                    res.Message('')
                else:
                    res.State('Failure')
                    res.Message(str(set_result.Message))
            else:
                res.State('Failure')
                res.Message('get NCSI key failed.')
        else:
            res.State('Failure')
            res.Message(str(result.Message))
        return res

    def getnetwork(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        # 获取网口类型
        result_type = RedfishTemplate.get_for_object(client, [url_result.get('url')])
        interface_type = {}
        if result_type.State and result_type.Message.get(url_result.get('url')).State:
            interface_type = {member.get('@odata.id'): member.get('type') for member in
                              result_type.Message.get(url_result.get('url')).Message.get('Members', [])}
            # 获取网口具体信息
            result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
            if result.State:
                networks = result.Message
                data = []
                channel_dict = {
                    "shared": "8",  # eth1
                    "dedicated": "1",  # eth0
                    "bond": "1"  # eth0
                }
                for network in networks:
                    single_data = collections.OrderedDict()
                    single_data['InterfaceName'] = network.get('Id', 'N/A')
                    single_data['ChannelNum'] = channel_dict.get(interface_type.get(network.get('@odata.id', 'N/A'), 'N/A'), "N/A")
                    single_data['LanChannel'] = interface_type.get(network.get('@odata.id', 'N/A'), 'N/A')
                    single_data['MACAddress'] = network.get('PermanentMACAddress', 'N/A')
                    ipv4_dhcp = network.get('IPv4Addresses', [])[0].get('AddressOrigin', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'
                    if ipv4_dhcp is not None and ipv4_dhcp != "N/A":
                        ipv4_dhcp = str(ipv4_dhcp).lower()
                    single_data['Ipv4DhcpEnable'] = ipv4_dhcp
                    single_data['Ipv4Address'] = network.get('IPv4Addresses', [])[0].get('Address', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'
                    single_data['Ipv4Subnet'] = network.get('IPv4Addresses', [])[0].get('SubnetMask', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'
                    single_data['Ipv4Gateway'] = network.get('IPv4Addresses', [])[0].get('Gateway', 'N/A') if network.get('IPv4Addresses', []) else 'N/A'

                    ipv6_dhcp = network.get('DHCPv6', {}).get('OperatingMode', 'N/A') if network.get('DHCPv6', {}) else 'N/A'
                    if ipv6_dhcp is not None and ipv6_dhcp != "N/A":
                        if "stateful" in str(ipv6_dhcp).lower():
                            ipv6_dhcp = "dhcp"
                            single_data['Ipv6DhcpEnable'] = ipv6_dhcp
                            dhcpAddress = network.get('IPv6Addresses', [])
                            count = 1
                            self.buildIPv6(count, dhcpAddress, single_data)
                            gateways = network.get('Oem', {}).get("Public", {}).get('IPv6DefaultGateways', [])
                            count = 1
                            for gateway in gateways:
                                single_data['Ipv6Gateway' + str(count)] = gateway.get('Address', 'N/A') if gateway.get('Address', 'N/A') else 'N/A'
                                count += 1
                        elif "disabled" in str(ipv6_dhcp).lower():
                            ipv6_dhcp = "static"
                            single_data['Ipv6DhcpEnable'] = ipv6_dhcp
                            dhcpAddress = network.get('IPv6Addresses', [])
                            count = 1
                            count = self.buildIPv6(count, dhcpAddress, single_data)
                            staticAddress = network.get('IPv6StaticAddresses', [])
                            self.buildIPv6(count, staticAddress, single_data)
                            gateways = network.get('IPv6StaticDefaultGateways', [])
                            count = 1
                            for gateway in gateways:
                                single_data['Ipv6Gateway' + str(count)] = gateway.get('Address', 'N/A') if gateway.get('Address', 'N/A') else 'N/A'
                                count += 1

                    single_data['VlanEnable'] = "enable" if network.get('VLAN', {}).get('VLANEnable', 'N/A') is True else "disable"
                    single_data['VlanId'] = network.get('VLAN', {}).get('VLANId', 'N/A')
                    data.append(single_data)
                res.State('Success')
                res.Message(data)
            else:
                res = result
        elif not result_type.State:
            res.Message(result_type.Message)
        elif not result_type.Message.get(url_result.get('url')).State:
            res.Message(result_type.Message.get(url_result.get('url')).Message)
        return res

    def buildIPv6(self, count, dhcpAddress, single_data):
        for addresss in dhcpAddress:
            single_data['Ipv6Address' + str(count)] = addresss.get('Address', 'N/A') if addresss else 'N/A'
            single_data['Ipv6Prefix' + str(count)] = addresss.get('PrefixLength', 'N/A') if addresss else 'N/A'
            single_data['Ipv6Origin' + str(count)] = addresss.get('AddressOrigin', 'N/A') if addresss else 'N/A'
            count += 1
        return count

    def setnetwork(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message(["Not Support"])
        return res

    def setipv4(self, client, args):
        ipinfo = ResultBean()
        interface_dict = {
            "shared": "eth1",
            "dedicated": "eth0",
            "bond0": "bond1"
        }
        url_result = self.get_url_info('getnetwork')
        result_type = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        interface_type = {}
        if result_type.State:
            interface_type = {str(member.get('@odata.id')).split("/")[-1]: member.get('@odata.id') for member in
                              result_type.Message.get('Members', [])}
            inter = interface_dict.get(args.interface_name, args.interface_name)
            if inter in interface_type.keys():
                result = RedfishTemplate.get_for_object_single(client, str(interface_type.get(inter)))
                if result.State:
                    enable_status = result.Message.get('Oem', {}).get('Public', {}).get('EnableStatus', None)
                    if not enable_status:
                        ipinfo.State("Failure")
                        ipinfo.Message(["get network enable status error "])
                        return ipinfo
                else:
                    ipinfo.State("Failure")
                    ipinfo.Message(["get " + args.interface_name + " error "])
                    return ipinfo
                if args.ipv4_status == 'disable':
                    if enable_status == 'ipv4':
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv6 is disable, ipv4 cannot be disable."])
                        return ipinfo
                    enable_status = 'ipv6'
                else:
                    if enable_status == 'ipv4':
                        enable_status = 'ipv4'
                    else:
                        enable_status = 'both'
                if enable_status == 'ipv6':
                    if args.ipv4_address is not None or args.ipv4_subnet is not None or args.ipv4_gateway is not None or args.ipv4_dhcp_enable is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv4 is disabled, please enable it first."])
                        return ipinfo
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                else:
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                    # 启用 ipv4 默认先启用 网络 lan_enable 固定为1
                    # IPV4 SETTING
                    if args.ipv4_dhcp_enable == "dhcp":
                        if args.ipv4_address is not None or args.ipv4_subnet is not None or args.ipv4_gateway is not None:
                            ipinfo.State("Failure")
                            ipinfo.Message(["'ip', 'subnet','gateway' is not active in DHCP mode."])
                            return ipinfo
                        data["IPv4Addresses"] = [{"AddressOrigin": "DHCP"}]
                    else:
                        static_info = {"AddressOrigin": "Static"}
                        if args.ipv4_address is not None:
                            if RegularCheckUtil.checkIP(args.ipv4_address):
                                ipv4_address = args.ipv4_address
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv4 IP address."])
                                return ipinfo
                            static_info["Address"] = ipv4_address
                        if args.ipv4_subnet is not None:
                            if RegularCheckUtil.checkSubnetMask(args.ipv4_subnet):
                                ipv4_subnet = args.ipv4_subnet
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv4 subnet mask."])
                                return ipinfo
                            static_info["SubnetMask"] = ipv4_subnet
                        if args.ipv4_gateway is not None:
                            if RegularCheckUtil.checkIP(args.ipv4_gateway):
                                ipv4_gateway = args.ipv4_gateway
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv4 default gateway."])
                                return ipinfo
                            static_info["Gateway"] = ipv4_gateway
                        data["IPv4Addresses"] = [static_info]
                patchBody = {}
                patchBody['url'] = str(interface_type.get(inter))
                patchBody['json'] = data
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    ipinfo.State('Success')
                    ipinfo.Message('')
                else:
                    ipinfo.State('Failure')
                    ipinfo.Message(str(set_result.Message))
                return ipinfo
            else:
                ipinfo.State("Failure")
                ipinfo.Message(["get " + args.interface_name + " error "])
                return ipinfo
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get " + args.interface_name + " error "])
            return ipinfo


    def setipv6(self, client, args):
        ipinfo = ResultBean()
        interface_dict = {
            "shared": "eth1",
            "dedicated": "eth0",
            "bond0": "bond1"
        }
        url_result = self.get_url_info('getnetwork')
        result_type = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        interface_type = {}
        if result_type.State:
            interface_type = {str(member.get('@odata.id')).split("/")[-1]: member.get('@odata.id') for member in
                              result_type.Message.get('Members', [])}
            inter = interface_dict.get(args.interface_name, args.interface_name)
            if inter in interface_type.keys():
                result = RedfishTemplate.get_for_object_single(client, str(interface_type.get(inter)))
                if result.State:
                    enable_status = result.Message.get('Oem', {}).get('Public', {}).get('EnableStatus', None)
                    if not enable_status:
                        ipinfo.State("Failure")
                        ipinfo.Message(["get network enable status error "])
                        return ipinfo
                else:
                    ipinfo.State("Failure")
                    ipinfo.Message(["get " + args.interface_name + " error "])
                    return ipinfo
                if args.ipv6_status == 'disable':
                    if enable_status == 'ipv6':
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv4 is disable, ipv6 cannot be disable."])
                        return ipinfo
                    enable_status = 'ipv4'
                else:
                    if enable_status == 'ipv6':
                        enable_status = 'ipv6'
                    else:
                        enable_status = 'both'
                if enable_status == 'ipv4':
                    if args.ipv6_address is not None or args.ipv6_index is not None or args.ipv6_gateway is not None or args.ipv6_prefix is not None or args.ipv6_dhcp_enable is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["ipv6 is disabled, please enable it first."])
                        return ipinfo
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                else:
                    data = {"Oem": {"Public": {"EnableStatus": enable_status}}}
                    # 启用 ipv6 默认先启用 网络 lan_enable 固定为1
                    # IPV6 SETTING
                    if args.ipv6_dhcp_enable == "dhcp":
                        if args.ipv6_address is not None or args.ipv6_index is not None or args.ipv6_gateway is not None or args.ipv6_prefix is not None:
                            ipinfo.State("Failure")
                            ipinfo.Message(
                                ["'ip', 'index','Subnet prefix length','gateway' is not active in DHCP mode."])
                            return ipinfo
                        data["IPv6Addresses"] = [{"AddressOrigin": "DHCPv6"}]
                    else:
                        static_info = {"AddressOrigin": "Static"}
                        data["IPv6Addresses"] = [static_info]
                        if args.ipv6_address is not None:
                            if RegularCheckUtil.checkIPv6(args.ipv6_address):
                                ipv6_address = args.ipv6_address
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 IP address."])
                                return ipinfo
                            static_info["Address"] = ipv6_address
                        if args.ipv6_gateway is not None:
                            if RegularCheckUtil.checkIPv6(args.ipv6_gateway):
                                ipv6_gateway = args.ipv6_gateway
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 default gateway."])
                                return ipinfo
                            gateway = {"Address": ipv6_gateway}
                            data["IPv6StaticDefaultGateways"] = [gateway]
                        if args.ipv6_index is not None:
                            if RegularCheckUtil.checkIndex(args.ipv6_index):
                                ipv6_index = args.ipv6_index
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 index(0-15)."])
                                return ipinfo
                        if args.ipv6_prefix is not None:
                            if RegularCheckUtil.checkPrefix(args.ipv6_prefix):
                                ipv6_prefix = args.ipv6_prefix
                            else:
                                ipinfo.State("Failure")
                                ipinfo.Message(["Invalid IPv6 Subnet prefix length(0-128)."])
                                return ipinfo
                            static_info["PrefixLength"] = ipv6_prefix
                patchBody = {}
                patchBody['url'] = str(interface_type.get(inter))
                patchBody['json'] = data
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    ipinfo.State('Success')
                    ipinfo.Message('')
                else:
                    ipinfo.State('Failure')
                    ipinfo.Message(str(set_result.Message))
                return ipinfo
            else:
                ipinfo.State("Failure")
                ipinfo.Message(["get " + args.interface_name + " error "])
                return ipinfo
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get " + args.interface_name + " error "])
            return ipinfo

    def setvlan(self, client, args):
        ipinfo = ResultBean()
        interface_dict = {
            "shared": "eth1",
            "dedicated": "eth0"
        }
        url_result = self.get_url_info('getnetwork')
        result_type = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        interface_type = {}
        if result_type.State:
            interface_type = {str(member.get('@odata.id')).split("/")[-1]: member.get('@odata.id') for member in
                              result_type.Message.get('Members', [])}
            inter = interface_dict.get(args.interface_name, args.interface_name)
            if inter in interface_type.keys():
                if args.vlan_status == "disable":
                    if args.vlan_id is not None or args.vlan_priority is not None:
                        ipinfo.State("Failure")
                        ipinfo.Message(["vlan is disabled, please enable it first."])
                        return ipinfo
                    vlan = {"VLANEnable": False}
                else:
                    vlan = {"VLANEnable": True}
                    if args.vlan_id is not None:
                        if args.vlan_id < 1 or args.vlan_id > 4094:
                            ipinfo.State("Failure")
                            ipinfo.Message(["vlan id should be 1-4094."])
                            return ipinfo
                        vlan["VLANId"] = args.vlan_id
                patchBody = {}
                patchBody['url'] = str(interface_type.get(inter))
                patchBody['json'] = {"VLAN": vlan}
                set_result = RedfishTemplate.patch_for_object(client, patchBody)
                if set_result.State:
                    ipinfo.State('Success')
                    ipinfo.Message('')
                else:
                    ipinfo.State('Failure')
                    ipinfo.Message(str(set_result.Message))
                return ipinfo
            else:
                ipinfo.State("Failure")
                ipinfo.Message(["get " + args.interface_name + " error "])
                return ipinfo
        else:
            ipinfo.State("Failure")
            ipinfo.Message(["get " + args.interface_name + " error "])
            return ipinfo

    def getnetworkbond(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            res.State("Success")
            bond = NetworkBondBean()
            enable_dict = {True: 'enable', False: 'disable'}
            lanDict = {'eth1': 'dedicated', 'eth0': 'shared', 'both': 'both'}
            bond.BondStatus(enable_dict.get(info['BondEnable'], 'unknown'))
            bond.BondMode(info['Mode'])
            bond.BondIfc(lanDict.get(info['PrimaryInterface'], 'unknown'))
            res.Message([bond.dict])
        else:
            res.State("Failure")
            res.Message(['network bond get failed'])
        return res

    def setnetworkbond(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        bonddata = {}
        bondifc = {"dedicated": "eth0", "shared": "eth1"}
        if args.interface:
            bonddata["PrimaryInterface"] = bondifc.get(args.interface, args.interface)
        if args.bond:
            bonddata["BondEnable"] = True if args.bond == 'enable' else False
            bonddata["Mode"] = "active-backup"
        patchBody = {}
        patchBody['url'] = url_result.get('url')
        patchBody['json'] = bonddata
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def gettime(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object(client, url_result.get('url'))
        if result.State:
            data = result.Message
            res_data = collections.OrderedDict()
            mode_dict = {
                "Static": 'auto',
                "DHCP IPv4": 'dhcp4',
                "DHCP IPv6": "dhcp6"
            }
            for key, value in data.items():
                if key == url_result.get('url')[0]:
                    if value.State:
                        zone_data = value.Message
                        res_data['Time'] = zone_data.get('DateTime', 'N/A')
                        res_data['Timezone'] = zone_data.get('DateTimeLocalOffset', 'N/A')
                if key == url_result.get('url')[1]:
                    if value.State:
                        ntp_data = value.Message
                        if ntp_data.get('ServiceEnabled', False) is True:
                            res_data['DateAutoSyn'] = mode_dict.get(ntp_data.get('NtpServerType', 'N/A'),
                                                                   ntp_data.get('NtpServerType', 'N/A'))
                            if res_data['DateAutoSyn'] == "auto":
                                res_data['NTPServer1'] = ntp_data.get('PrimaryNtpServer', 'N/A')
                                res_data['NTPServer2'] = ntp_data.get('SecondaryNtpServer', 'N/A')
                                res_data['NTPServer3'] = ntp_data.get('ThirdNtpServer', 'N/A')
                                res_data['NTPServer4'] = ntp_data.get('FourthNtpServer', 'N/A')
                                res_data['NTPServer5'] = ntp_data.get('FifthNtpServer', 'N/A')
                                res_data['NTPServer6'] = ntp_data.get('SixthNtpServer', 'N/A')
                        else:
                            res_data['DateAutoSyn'] = "manual"
                        res_data['NTPSYNCycle'] = ntp_data.get('PollingInterval', 'N/A')
                        res_data['NTPMAXVariety'] = ntp_data.get('MaxVariety', 'N/A')
            res.State('Success')
            res.Message(res_data)
        else:
            res = result
        return res

    def settime(self, client, args):
        def set_zone(res):
            flag = 1
            try:
                data = {}
                if args.timeZone is not None:
                    zone_flag = RegularCheckUtil.checkRawZone(args.timeZone)
                    if zone_flag == 1:  # 整点
                        if float(args.timeZone) > 0:
                            newzone = '+' + str(int(float(args.timeZone))).zfill(2) + ":00"
                        else:
                            newzone = str(int(float(args.timeZone))).zfill(2) + ":00"
                        data['DateTimeLocalOffset'] = newzone
                        flag = 0
                    elif zone_flag == 2:  # 半点
                        if float(args.timeZone) > 0:
                            newzone = '+' + str(int(float(args.timeZone))).zfill(2) + ":30"
                        else:
                            newzone = str(int(float(args.timeZone))).zfill(2) + ":30"
                        data['DateTimeLocalOffset'] = newzone
                        flag = 0
                    else:   # 不符合
                        data = "please chose timezone from {-12, -11.5, -11, ... ,13, 13.5, 14}"
                        flag = 2
            except Exception as e:
                data = str(e)
                flag = 2
            return flag, data

        def set_time(res):
            flag = 0
            try:
                get_data = res.json()
                if "Description" in get_data:
                    del get_data['Description']
                if "Id" in get_data:
                    del get_data['Id']
                if "Name" in get_data:
                    del get_data['Name']
                if "AutoKey" in get_data:
                    del get_data['AutoKey']
                if "NetworkSuppliedServers" in get_data:
                    del get_data['NetworkSuppliedServers']
                if get_data.get("ServiceEnabled") is False and (args.autoDate is None or args.autoDate != "auto"):
                    if args.NTPServer1 is not None or args.NTPServer2 is not None or args.NTPServer3 is not None or \
                            args.NTPServer4 is not None or args.NTPServer5 is not None or args.NTPServer6 is not None:
                        flag = 2
                        get_data = "please set -A to auto first"
                        return flag, get_data
                if args.NTPServer1 is not None or args.NTPServer2 is not None or args.NTPServer3 is not None or \
                        args.NTPServer4 is not None or args.NTPServer5 is not None or args.NTPServer6 is not None or \
                        args.autoDate is not None or args.NTPSyncCycle is not None or args.NTPMAXvariety is not None:
                    flag = 0
                if args.autoDate:
                    if args.autoDate == "manual":
                        get_data['ServiceEnabled'] = False
                    elif args.autoDate == "auto":
                        if args.NTPServer1 is None and args.NTPServer2 is None and args.NTPServer3 is None and \
                                args.NTPServer4 is None and args.NTPServer5 is None and args.NTPServer6 is None:
                            flag = 2
                            get_data = "please input NTP Server"
                            return flag, get_data
                        get_data['ServiceEnabled'] = True
                        get_data['NtpServerType'] = "Static"
                    elif args.autoDate == "dhcp4":
                        get_data['ServiceEnabled'] = True
                        get_data['NtpServerType'] = "DHCP IPv4"
                    else:
                        get_data['ServiceEnabled'] = True
                        get_data['NtpServerType'] = "DHCP IPv6"
                if args.NTPServer1:
                    get_data['PrimaryNtpServer'] = args.NTPServer1
                if args.NTPServer2:
                    get_data['SecondaryNtpServer'] = args.NTPServer2
                if args.NTPServer3:
                    get_data['ThirdNtpServer'] = args.NTPServer3
                if args.NTPServer4:
                    get_data['FourthNtpServer'] = args.NTPServer4
                if args.NTPServer5:
                    get_data['FifthNtpServer'] = args.NTPServer5
                if args.NTPServer6:
                    get_data['SixthNtpServer'] = args.NTPServer6
                if args.NTPSyncCycle:
                    get_data['PollingInterval'] = args.NTPSyncCycle
                if args.NTPMAXvariety:
                    get_data['MaxVariety'] = args.NTPMAXvariety
            except Exception as e:
                flag = 2
                get_data = str(e)
            return flag, get_data

        res = ResultBean()
        if args.autoDate is None and args.timeZone is None and args.NTPServer1 is None and args.NTPServer2 is None and \
                args.NTPServer3 is None and args.NTPServer4 is None and args.NTPServer5 is None and \
                args.NTPServer6 is None and args.NTPSyncCycle is None and args.NTPMAXvariety is None:
            res.State("Failure")
            res.Message("No setting changed")
            return res
        url_result = self.get_url_info("setntp")
        result = RedfishTemplate.patch_multi_for_object(client, url_result.get('url')[1:], [set_zone, set_time])
        message = ""
        error_flag = False
        if isinstance(result, dict):
            if result.get(url_result.get('url')[1]) and result.get(url_result.get('url')[1]).State is False:
                if type(result.get(url_result.get('url')[1]).Message) is str:
                    message += "set time zone failed, " + str(result.get(url_result.get('url')[1]).Message) + ". "
                else:
                    message += "set time zone failed, " + str(result.get(url_result.get('url')[1]).Message.json()) + ". "
                error_flag = True
            if result.get(url_result.get('url')[2]) and result.get(url_result.get('url')[2]).State is False:
                if type(result.get(url_result.get('url')[2]).Message) is str:
                    message += "set ntp failed, " + str(result.get(url_result.get('url')[2]).Message) + ". "
                else:
                    message += "set ntp failed, " + str(result.get(url_result.get('url')[2]).Message.json()) + ". "
                error_flag = True
            if error_flag:
                res.State("Failure")
                res.Message(message)
            else:
                res.State("Success")
                res.Message([])
        else:
            res = result
        return res

    def setpdisk(self, client, args):
        result = ResultBean()
        mydict = {}
        setpdurl = ""
        M8PMCkey = "Disk_"
        if M8PMCkey in args.deviceId:
            M8PMCkey = ""
        if args.option == "LOC":
            url_result = self.get_url_info("locatephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Action"] = "start"
            if args.duration:
                # if args.duration < 1 or args.duration > 255:
                #     result.State("Failure")
                #     result.Message('Invalid Duration(1-255).')
                #     return result
                mydict["Duration"] = args.duration
            else:
                # result.State("Failure")
                # result.Message('-D is needed when locate virtual drive')
                # return result
                mydict["Duration"] = 0
        elif args.option == "STL":
            url_result = self.get_url_info("locatephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Action"] = "stop"
            mydict["Duration"] = 0
        elif args.option == "ES":
            url_result = self.get_url_info("erasephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Erasure"] = "Stop"
        elif args.option == "EM":
            url_result = self.get_url_info("erasephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Erasure"] = "Simple"
        elif args.option == "EN":
            url_result = self.get_url_info("erasephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Erasure"] = "Normal"
        elif args.option == "ET":
            url_result = self.get_url_info("erasephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Erasure"] = "Through"
        elif args.option == "1PASS":
            url_result = self.get_url_info("erasephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Erasure"] = "1Pass"
        elif args.option == "2PASS":
            url_result = self.get_url_info("erasephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Erasure"] = "2Pass"
        elif args.option == "3PASS":
            url_result = self.get_url_info("erasephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))
            mydict["Erasure"] = "3Pass"
        elif args.option == "HS":
            url_result = self.get_url_info("hotsparephysicadrive")
            setpdurl = url_result.get('url').replace("{cid}", str(args.ctrlId)).replace("{pid}", M8PMCkey + str(args.deviceId))

            if args.action == "remove":
                mydict["HotSpare"] = "Remove"
            elif args.action == "global":
                mydict["HotSpare"] = "Global"
            elif args.action == "dedicate":
                mydict["HotSpare"] = "Dedicated"
            mydict["Volumes"] = []
            if args.logicalDrivers:
                mydict["Volumes"] = ["LogicalDisk" + args.logicalDrivers]

        else:
            result.State("Failure")
            result.Message(['not support'])
            return result

        patchBody = {}
        patchBody['url'] = setpdurl
        patchBody['json'] = mydict
        res = RedfishTemplate.post_for_object(client, patchBody)
        if res.State:
            result.State("Success")
            result.Message('operation is successful,please wait a few seconds.')
        else:
            result.State("Failure")
            result.Message('operation is failed, ' + str(res.Message))

        return result

    def getpowerrestore(self, client, args):
        url_result = self.get_url_info("getsysteminfo")
        res = ResultBean()
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message.get('PowerRestorePolicy',)
            policy_dict = {
                'AlwaysOn': 'Always Power On',
                'AlwaysOff': 'Always Power Off',
                'LastState': 'Restore Last Power State'
            }

            JSON = {}
            JSON['policy'] = policy_dict.get(info, 'UnKnown')
            res.State("Success")
            res.Message([JSON])
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def setpowerrestore(self, client, args):
        res = ResultBean()
        policy_dict = {'on': 'AlwaysOn', 'off': 'AlwaysOff', 'restore': 'LastState'}
        action = policy_dict.get(args.option, None)
        if action is None:
            res.State("Failure")
            res.Message("parameter is invalid")
            return res
        data = {'PowerRestorePolicy': action}
        url_result = self.get_url_info("setsysteminfo")
        patchBody = {}
        patchBody['url'] = url_result.get('url')
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getpowerstatus(self, client, args):
        url_result = self.get_url_info("getsysteminfo")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data_res = {}
            #On Off
            data_res['PowerStatus'] = info.get('PowerState', "unknown")
            res.State("Success")
            res.Message(data_res)
        else:
            res = result
        return res

    def powercontrol(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        status_dict = {
            "on": "On",
            "off": "ForceOff",
            "cycle": "PowerCycle",
            "reset": "ForceRestart",
            "nmi": "Nmi",
            "shutdown": "GracefulShutdown"
        }
        data = {}
        data['ResetType'] = status_dict.get(args.state)
        postBody = {}
        postBody['url'] = url_result.get('url')
        postBody['json'] = data
        result = RedfishTemplate.post_for_object(client, postBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getpsuconfig(self, client, args):
        url_result = self.get_url_info('getpsu')
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message.get("PowerSupplies", [])
            data = []
            for item in info:
                single_data = collections.OrderedDict()
                single_data['ID'] = item.get("MemberId", "N/A")
                single_data['Present'] = "Present" if "enable" in str(item.get('Status', {}).get('State', "N/A")).lower() else "Absent"
                single_data['Mode'] = item.get('Oem', {}).get('Public', {}).get('WorkMode', 'N/A')
                data.append(single_data)
            res.State('Success')
            res.Message(data)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def setpsuconfig(self, client, args):
        url_result = self.get_url_info('getpsu')
        res = ResultBean()
        switch_dict = {
            'active': 'Active',
            'standby': 'Standby',
            'normal': 'Normal'
        }
        data = {
            'PowerSupplies': [{
                "MemberId": str(args.id),
                "Oem": {
                    "Public": {
                        "WorkMode": switch_dict.get(args.switch)
                    }
                }
            }]
        }

        patchBody = {}
        patchBody['url'] = str(url_result.get('url'))
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message('')
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def resetbmc(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        postdata = {"ResetType": "ForceRestart"}
        postBody = {}
        postBody['json'] = postdata
        postBody['url'] = url_result.get('url')
        result = RedfishTemplate.post_for_object(client, postBody)
        res = ResultBean()
        if result.State:
            res.State("Success")
            res.Message(result.Message)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def restorefactorydefaults(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        postdata = {"ResetType": "ForceRestart"}  # 传参与restBMC一样，待确认
        postBody = {}
        postBody['json'] = postdata
        postBody['url'] = url_result.get('url')
        result = RedfishTemplate.post_for_object(client, postBody)
        res = ResultBean()
        if result.State:
            res.State("Success")
            res.Message(result.Message)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getservice(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data = []
            service_name = {
                'HTTPS': 'web',
                'IPMI': 'ipmi',
                'SSH': 'ssh',
                'VirtualMedia': 'virtual-media',
                'KVMIP': 'kvm',
                'RFB': 'vnc'
            }
            count = 1
            for item in service_name.keys():
                single_info = info.get(item, {})
                oem_info = info.get("Oem", {}).get("Public", {}).get(item, {})
                if single_info is not None and single_info != {}:
                    single_data = collections.OrderedDict()
                    single_data['ID'] = str(count)
                    count += 1
                    single_data['ServiceName'] = service_name.get(item)
                    single_data['State'] = 'active' if single_info.get('ProtocolEnabled', False) else 'inactive'
                    single_data['SecurePort'] = single_info.get('Port', 'N/A')
                    single_data['NonSecurePort'] = oem_info.get('NonSecurePort', 'N/A')
                    single_data['TimeOut'] = oem_info.get('Timeout', 'N/A')
                    # 接口文档：安全性考量，get请求不显示超时时间和非安全端口
                    data.append(single_data)
            res.State('Success')
            res.Message(data)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def setservice(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            service_name = {
                'web': 'HTTPS',
                'kvm': 'KVMIP',
                'virtualmedia': 'VirtualMedia',
                'ssh': 'SSH',
                'vnc': "RFB",
                'ipmi': 'IPMI'
            }
            if args.servicename != 'ipmi':
                item = service_name.get(args.servicename)
                single_info = info.get(item, {})
                if 'Certificates' in single_info:
                    del single_info['Certificates']
                oem_info = info.get("Oem", {}).get("Public", {}).get(item, {})
                if 'MaxSession' in oem_info:
                    del oem_info['MaxSession']
                if args.enabled:
                    single_info['ProtocolEnabled'] = True if args.enabled == 'active' else False
                if args.secureport:
                    single_info['Port'] = args.secureport
                if args.nonsecureport and oem_info.get('NonSecurePort', None):
                    oem_info['NonSecurePort'] = args.nonsecureport
                if args.timeout and oem_info.get('Timeout', None):
                    oem_info['Timeout'] = args.timeout
                oem = {"Public": {item: oem_info}}
                data = {item: single_info, "Oem": oem}
            else:
                data = {"IPMI": {"ProtocolEnabled": True if args.enabled == 'active' else False}}

            patchBody = {}
            patchBody['url'] = str(url_result.get('url'))
            patchBody['json'] = data
            result = RedfishTemplate.patch_for_object(client, patchBody)
            if result.State:
                res.State("Success")
                res.Message('')
            else:
                res.State("Failure")
                res.Message(result.Message)
            return res
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def getSystemLockdownMode(self, client, args):
        url_result = self.get_url_info("getsystemlockdownmode")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            status_dict = {
                "Disabled": "close",
                "Enabled": "open"
            }
            mode = result.Message.get("BmcLockMode", "")
            status = status_dict.get(mode, 'Unknown')
            data = {
                "lock_status": status
            }
            res.State('Success')
            res.Message(data)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def setSystemLockdownMode(self, client, args):
        url_result = self.get_url_info("setsystemlockdownmode")
        res = ResultBean()
        status_dict = {
            'close': "Disabled",
            'open': "Enabled"
        }
        data = {
            'BmcLockMode': status_dict.get(args.status)
        }
        patchBody = {}
        patchBody['url'] = str(url_result.get('url'))
        patchBody['json'] = data
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message('')
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getuid(self, client, args):
        url_result = self.get_url_info("getchassis")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            status_dict = {
                "Off": "off",
                "Lit": "on",
                "Blinking": "blink"
            }
            info = result.Message
            data_res = {}
            data_res['UIDLed'] = status_dict.get(info.get('IndicatorLED'), info.get('IndicatorLED', "unknown"))
            res.State("Success")
            res.Message(data_res)
        else:
            res = result
        return res

    def setuid(self, client, args):
        def set_status(raw_data, res):
            patch_res = ResultBean()
            status_dict = {
                "blink": "Blinking",
                "on": "Lit",
                "off": "Off"
            }
            try:
                data = res.json()
                if args.led is not None and "IndicatorLED" in data:
                    data = {}
                    data['IndicatorLED'] = status_dict.get(args.led)
                    return patch_res.success(data)
                else:
                    return patch_res.fail("get uid info failed")
            except Exception as e:
                return patch_res.fail(str(e))

        res = ResultBean()
        url_result = self.get_url_info("setchassis")
        patchBody = {}
        patchBody['url'] = url_result.get('url')
        patchBody['func'] = set_status
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message("")
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def geteventlog(self, client, args):
        url_result = self.get_url_info("getsystemeventlog")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url')+"?$top=3639")
        res = ResultBean()
        if result.State:
            info = result.Message.get("Members", [])
            data_sum = []
            for item in info:
                single_data = collections.OrderedDict()
                single_data['ID'] = item.get('Id', "N/A")
                single_data['TimeStamp'] = item.get('Created', "N/A")
                single_data['Severity'] = item.get('Severity', "N/A")
                single_data['SensorNumber'] = item.get('SensorNumber', "N/A")
                single_data['SensorType'] = item.get('SensorType', item.get("OemSensorType","N/A"))
                single_data['SensorDesc'] = item.get('Message', "N/A")
                data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getfw(self, client, args):
        def sortfw(fwraw):
            fwdict = {
                "ActiveBMC": 0,
                "BackupBMC": 1,
                "BIOS": 2,
                "ME": 2.5,
                "MainBoardCPLD": 3,
                # "Front_HDD_CPLD": 4,
                # "Rear_HDD_CPLD": 5,
                # "PSU": 6,
                "SCMCPLD": 7,
                      }
            fwdictx = {
                "Front_HDD_CPLD": 4,
                "Rear_HDD_CPLD": 5,
                "PSU": 6,
                      }

            for key in fwraw.keys():
                break

            if key in fwdict:
                return fwdict.get(key)
            else:
                for fkey in fwdictx.keys():
                    if key.startswith(fkey + "_"):
                        #PSU_0
                        return float(str(fwdictx.get(fkey)) + "." + key[len(fkey + "_")])
                    if key.startswith(fkey):
                        return float(str(fwdictx.get(fkey)) + "." + key[len(fkey)])
                return 99

        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        fwurl = url_result.get('url') + "?$expand=.($levels=1)"
        result = RedfishTemplate.get_for_object_single(client, fwurl)
        if result.State:
            data = result.Message.get("Members")
            data_sum = []
            name_dict = {
                "Bios": "BIOS",
                "PSU_0": "PSU0",
                "PSU_1": "PSU1",
                "MainBoard0CPLD": "MainBoardCPLD"
            }
            for item in data:
                single_data = collections.OrderedDict()
                if item.get("Id") is not None:
                    name = name_dict.get(item.get('Id'), item.get('Id'))
                    version = item.get('Version', 'N/A')
                    if version is None:
                        version = "N/A"
                    version_index = str(version).find('(')
                    if version_index == -1:
                        single_data[name] = version
                    else:
                        single_data[name] = str(version)[:version_index].strip()
                    data_sum.append(single_data)
            if data_sum:
                data_sum.sort(key=sortfw)
                res.State("Success")
                res.Message(data_sum)
            else:
                data_sum = []
                name_dict = {
                    "Bios": "BIOS",
                    "PSU_0": "PSU0",
                    "PSU_1": "PSU1",
                    "MainBoard0CPLD": "MainBoardCPLD"
                }
                for item in data:
                    fw_single_url = item.get("@odata.id")
                    fw_single_res = RedfishTemplate.get_for_object_single(client, fw_single_url)

                    if fw_single_res.State:
                        single_data = collections.OrderedDict()
                        fw_single_json = fw_single_res.Message
                        name = fw_single_json.get('Id', 'N/A')
                        version = fw_single_json.get('Version', 'N/A')
                        if version is None:
                            version = "N/A"
                        version_index = str(version).find('(')
                        if version_index == -1:
                            single_data[name] = version
                        else:
                            single_data[name] = str(version)[:version_index].strip()
                        data_sum.append(single_data)

                if data_sum:
                    data_sum.sort(key=sortfw)
                    res.State("Success")
                    res.Message(data_sum)
                else:
                    res.State("Failure")
                    res.Message("Cannot get fw version")
        else:
            res = result
        return res

    def gethdddisk(self, client, args):
        url_result = self.get_url_info("getharddisk")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            data = []
            hddraw = result.Message
            hddurllist = hddraw.get("Members")
            for urldict in hddurllist:
                hddurl = urldict.get("@odata.id")
                hddid = hddurl.split("/")[-1]

                if len(hddid) < 2:
                    continue
                else:
                    locate = hddid[:2]
                    if str(locate) == "FP":
                        continue
                    elif str(locate) == "RP":
                        continue
                    elif str(locate) == "OB":
                        obresult = RedfishTemplate.get_for_object_single(client, hddurl)
                    else:
                        continue

                if obresult.State:
                    item = obresult.Message

                    single_data = collections.OrderedDict()
                    hddindex = hddid.replace("OB", "")
                    if hddindex.isdigit():
                        hddindex = str(int(hddindex))
                    single_data['ID'] = hddindex
                    single_data['Present'] = 'Present'
                    single_data['Status'] = str(item.get('Status', {}).get("Health", "N/A"))
                    capacityBytes = item.get('CapacityBytes')
                    if capacityBytes:
                        capacityBytes = capacityBytes // 1024 // 1024 //1024
                    else:
                        capacityBytes = "N/A"
                    single_data['Capacity(GB)'] = capacityBytes
                    if "ModuleNumber" in item:
                        single_data['Model'] = str(item.get('ModuleNumber', 'N/A'))
                    else:
                        #ham
                        single_data['Model'] = item.get("Oem", {}).get("Public", {}).get("ModuleNumber", 'N/A')
                    single_data['Media'] = str(item.get('MediaType', 'N/A'))
                    single_data['SN'] = str(item.get('SerialNumber', 'N/A'))
                    single_data['Firmware'] = str(item.get('Revision', 'N/A'))
                    single_data['Manufacturer'] = str(item.get('Manufacturer', 'N/A'))
                    single_data['CapableSpeed'] = str(item.get('CapableSpeedGbs', 'N/A'))
                    single_data['NegotiatedSpeedGbs'] = str(item.get('NegotiatedSpeedGbs', 'N/A'))
                    data.append(single_data)


            res.State("Success")
            res.Message(data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getharddisk(self, client, args):
        def compareId(harddisk):
            if len(harddisk.get("BackplaneIndex")) < 2:
                b = "0" + harddisk.get("BackplaneIndex")
            else:
                b = harddisk.get("BackplaneIndex")
            if len(harddisk.get("ID")) < 2:
                d = "0" + harddisk.get("ID")
            else:
                d = harddisk.get("ID")
            return harddisk.get("Front/Rear") + b + d
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data = []
            for item in info:
                Oem = item.get('Oem', {}).get('Public', {})
                single_data = collections.OrderedDict()
                disk_id = item.get("Id", "")
                if len(disk_id) < 2:
                    single_data['Front/Rear'] = "Unknown"
                else:
                    locate = disk_id[:2]
                    if str(locate) == "FP":
                        single_data['Front/Rear'] = "Front"
                    elif str(locate) == "RP":
                        single_data['Front/Rear'] = "Rear"
                    elif str(locate) == "OB":
                        continue
                    else:
                        single_data['Front/Rear'] = "Unknown"

                if len(disk_id) == 9:
                    # locate = disk_id[:2]
                    plane_id = disk_id[2:4]
                    single_id = disk_id[7:9]
                    single_data['BackplaneIndex'] = str(int(plane_id))
                    single_data['ID'] = str(int(single_id))
                else:
                    single_data['BackplaneIndex'] = "N/A"
                    single_data['ID'] = str(disk_id)
                single_data['Present'] = 'Present' if 'enable' in str(
                    item.get('Status', {}).get("State", "N/A")).lower() else "Absent"

                if "ModuleNumber" in item:
                    single_data['Model'] = str(item.get('ModuleNumber', 'N/A'))
                else:
                    # ham
                    single_data['Model'] = item.get("Oem", {}).get("Public", {}).get("ModuleNumber", 'N/A')

                single_data['Vendor'] = item.get("Manufacturer", "N/A")
                single_data['Media'] = item.get("MediaType", "N/A")
                single_data['Interface'] = Oem.get("InterfaceType", "N/A")
                single_data['FirmwareVersion'] = item.get("Revision", "N/A")
                single_data['SerialNumber'] = item.get("SerialNumber", "N/A")
                single_data['Error'] = Oem.get("ErrorStatus", "N/A")
                single_data['Locate'] = item.get('IndicatorLED') == "Lit" or item.get('IndicatorLED') == "On"
                single_data['Rebuild'] = Oem.get("RebuildStatus", "N/A")
                single_data['NVME'] = "NVMe" == item.get("Protocol", "N/A")
                data.append(single_data)
            res.State("Success")
            data.sort(key=compareId)
            res.Message(data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def gethba(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            hba_info = result.Message
            hba_list = []
            for hba in hba_info:
                hba_result = HBABean()
                hba_result.Id(hba.get('Id', "N/A"))
                hba_result.Name(hba.get('Name', "N/A"))
                hba_result.Manufacturer(hba.get('Manufacturer', "N/A"))
                hba_result.Pn(hba.get('PartNumber', "N/A"))
                hba_result.HbaTemp(hba.get('Vendor', "N/A"))
                hba_result.SN(hba.get('SerialNumber', "N/A"))
                hba_result.PortCount(hba.get('Oem', {}).get('Public', {}).get('PortCount', "N/A"))
                port_url = hba.get('Ports', {}).get("@odata.id", None)
                if port_url:
                    port_res = RedfishTemplate.get_for_collection_object(client, port_url)
                    if port_res.State:
                        postList = []
                        ports = port_res.Message
                        for port in ports:
                            item = port.get('Oem', {}).get('Public', {})
                            hba_post = HBAPost()
                            hba_post.Id(port.get('Id', "N/A"))
                            hba_post.PortWWPN(item.get('WWPN', "N/A"))
                            hba_post.PortWWNN(item.get('WWNN', "N/A"))
                            hba_post.PortLinkState(item.get('LinkState', "N/A"))
                            hba_post.PortLinkSpeed(item.get('LinkSpeed', "N/A"))
                            postList.append(hba_post.dict)
                        hba_result.HBAPost(postList)
                hba_list.append(hba_result.dict)
            res.State("Success")
            res.Message(hba_list)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getpcie(self, client, args):
        res = ResultBean()
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        if result.State:
            data = result.Message
            data_sum = []
            for item in data:
                item_info = {}
                item_url = item.get("PCIeFunctions", {}).get("@odata.id")
                if item_url is not None:
                    item_result = RedfishTemplate.get_for_collection_object(client, item_url[1:])
                    if item_result.State:
                        item_info = item_result.Message[0]
                single_data = collections.OrderedDict()
                single_data['ID'] = item.get('Id', 'N/A')
                single_data['Present'] = "Present" if "enable" in str(
                    item.get('Status', {}).get('State', "N/A")).lower() else "Absent"
                single_data['Location'] = item.get('Oem', {}).get('Public', {}).get('Location', 'N/A')
                single_data['DeviceType'] = item.get('Oem', {}).get('Public', {}).get('DeviceClass', 'N/A')
                single_data['DeviceName'] = item.get('Model', 'N/A')
                single_data['DeviceID'] = item_info.get('DeviceId', 'N/A')
                single_data['SubDeviceID'] = item_info.get('SubsystemId', 'N/A')
                single_data['VendorName'] = item.get('Manufacturer', 'N/A')
                single_data['VendorID'] = item_info.get('VendorId', 'N/A')
                single_data['SubVendorID'] = item_info.get('SubsystemVendorId', 'N/A')
                single_data['RatedLinkSpeed'] = item_info.get('Oem', {}).get("Public", {}).get("LinkSpeedAbility", "N/A")
                single_data['RatedLinkWidth'] = item_info.get('Oem', {}).get("Public", {}).get("LinkWidthAbility",
                                                                                               "N/A")
                single_data['CurrentLinkSpeed'] = item_info.get('Oem', {}).get("Public", {}).get("LinkSpeed",
                                                                                                 "N/A")
                single_data['CurrentLinkWidth'] = item_info.get('Oem', {}).get("Public", {}).get("LinkWidth", "N/A")
                try:
                    single_data['BusNumber'] = hex(item_info.get('Oem', {}).get('Public', {}).get('BusNumber', 'N/A'))
                    single_data['DeviceNumber'] = hex(
                        item_info.get('Oem', {}).get('Public', {}).get('DeviceNumber', 'N/A'))
                    single_data['FunctionNumber'] = hex(
                        item_info.get('Oem', {}).get('Public', {}).get('FunctionNumber', 'N/A'))
                except:
                    single_data['BusNumber'] = "N/A"
                    single_data['DeviceNumber'] = "N/A"
                    single_data['FunctionNumber'] = "N/A"
                try:
                    single_data['RootPortBusNumber'] = hex(
                        item_info.get('Oem', {}).get('Public', {}).get('RootBusNumber', 'N/A'))
                    single_data['RootPortDeviceNumber'] = hex(
                        item_info.get('Oem', {}).get('Public', {}).get('RootDeviceNumber', 'N/A'))
                    single_data['RootPortFunctionNumber'] = hex(
                        item_info.get('Oem', {}).get('Public', {}).get('RootFunctionNumber', 'N/A'))
                except:
                    single_data['RootPortBusNumber'] = "N/A"
                    single_data['RootPortDeviceNumber'] = "N/A"
                    single_data['RootPortFunctionNumber'] = "N/A"
                data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res = result
        return res

    def resetkvm(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        postdata = {"ResetType": "ForceRestart"}
        postBody = {}
        postBody['json'] = postdata
        postBody['url'] = url_result.get('url')
        result = RedfishTemplate.post_for_object(client, postBody)
        res = ResultBean()
        if result.State:
            res.State("Success")
            res.Message(result.Message)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getselftest(self, client, args):
        url_result = self.get_url_info("getBootcode")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            data = collections.OrderedDict()
            data['CurrentBootcode'] = info.get('Current', 'N/A')
            data['CurrentBootcodeDesc'] = info.get('Description', 'N/A')
            data['HistoryBootcode'] = str(" ".join(info.get('History', ['N/A'])))
            res.State('Success')
            res.Message(data)
        else:
            res.State('Failure')
            res.Message(result.Message)
        return res

    def gettemp(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            if not result.Message.get(url_result.get('url')[0]).State:
                res.State("Failure")
                res.Message(result.Message.get(url_result.get('url')[0]).Message)
                return res
            info = result.Message.get(url_result.get('url')[0]).Message.get('Temperatures')
            if info is None:
                res.State("Failure")
                res.Message('Return info has no key of Temperatures.')
                return res
            data_sum = []
            for item in info:
                if item.get('Status', {}).get('State', "N/A") == "Enabled":
                    single_data = collections.OrderedDict()
                    single_data['ID'] = item.get('MemberId', "N/A")
                    single_data['Sensor'] = item.get('Name', "N/A")
                    single_data['State'] = item.get('Status', {}).get('Health', "N/A")
                    single_data['Reading'] = item.get('ReadingCelsius', "N/A")
                    single_data['Unit'] = "degrees C"
                    single_data['LowNRT'] = item.get('LowerThresholdFatal', "N/A")
                    single_data['LowCT'] = item.get('LowerThresholdCritical', "N/A")
                    single_data['LowNCT'] = item.get('LowerThresholdNonCritical', "N/A")
                    single_data['UpNCT'] = item.get('UpperThresholdNonCritical', "N/A")
                    single_data['UpCT'] = item.get('UpperThresholdCritical', "N/A")
                    single_data['UpNRT'] = item.get("UpperThresholdFatal", "N/A")
                    data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getvolt(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            if not result.Message.get(url_result.get('url')[0]).State:
                res.State("Failure")
                res.Message(result.Message.get(url_result.get('url')[0]).Message)
                return res
            info = result.Message.get(url_result.get('url')[0]).Message.get('Voltages')
            if info is None:
                res.State("Failure")
                res.Message('Return info has no key of Voltages.')
                return res
            data_sum = []
            for item in info:
                if item.get('Status', {}).get('State', "N/A") == "Enabled":
                    single_data = collections.OrderedDict()
                    single_data['ID'] = item.get('MemberId', "N/A")
                    single_data['Sensor'] = item.get('Name', "N/A")
                    single_data['State'] = item.get('Status', {}).get('Health', "N/A")
                    try:
                        single_data['Reading'] = round(item.get('ReadingVolts', 0), 2)
                    except:
                        single_data['Reading'] = 'N/A'
                    single_data['Unit'] = "volts"
                    try:
                        single_data['LowNRT'] = round(item.get('LowerThresholdNonRecoverable', 0), 2)
                    except:
                        single_data['LowNRT'] = 'N/A'
                    try:
                        single_data['LowCT'] = round(item.get('LowerThresholdCritical', 0), 2)
                    except:
                        single_data['LowCT'] = 'N/A'
                    try:
                        single_data['LowNCT'] = round(item.get('LowerThresholdNonCritical', 0), 2)
                    except:
                        single_data['LowNCT'] = 'N/A'
                    try:
                        single_data['UpNCT'] = round(item.get('UpperThresholdNonCritical', 0), 2)
                    except:
                        single_data['UpNCT'] = 'N/A'
                    try:
                        single_data['UpCT'] = round(item.get('UpperThresholdCritical', 0), 2)
                    except:
                        single_data['UpCT'] = 'N/A'
                    try:
                        single_data['UpNRT'] = round(item.get("UpperThresholdNonRecoverable", 0), 2)
                    except:
                        single_data['UpNRT'] = 'N/A'
                    data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getsensor(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            data_sum = []
            if result.Message.get(url_result.get('url')[0]).State:
                info = result.Message.get(url_result.get('url')[0]).Message.get('Sensors')
                if info is None:
                    res.State("Failure")
                    res.Message('Return info has no key of Sensors.')
                    return res
                unit_dict = {
                    "volts": "Volts",
                    "deg_c": "degrees C",
                    "watts": "Watts",
                    "rpm": "RPM",
                    "Percent": "Percent"
                }
                for item in info:
                    single_data = collections.OrderedDict()
                    single_data['ID'] = item.get('SensorIndex', "N/A")
                    single_data['Sensor'] = item.get('Name', "N/A")
                    single_data['State'] = item.get('Status', {}).get('State', "N/A")
                    # if single_data['State'] == "Enabled" and "Reading" not in item:
                    #     single_data['State'] = "Disabled"
                    if single_data['State'] == "Enabled":
                        single_data['State'] = item.get('Status', {}).get('Health', "N/A")
                        reading = item.get('Reading', "N/A")
                        try:
                            single_data['Reading'] = round(reading, 3)
                        except:
                            single_data['Reading'] = "N/A"
                    else:
                        single_data['Reading'] = "Disabled"
                    single_data['Unit'] = unit_dict.get(item.get('ReadingUnits', "N/A"), item.get('ReadingUnits', "N/A"))
                    try:
                        single_data['LowNRT'] = round(item.get('LowerThresholdFatal'), 3)
                    except:
                        single_data['LowNRT'] = "N/A"
                    try:
                        single_data['LowCT'] = round(item.get('LowerThresholdCritical'), 3)
                    except:
                        single_data['LowCT'] = "N/A"
                    try:
                        single_data['LowNCT'] = round(item.get('LowerThresholdNonCritical'), 3)
                    except:
                        single_data['LowNCT'] = "N/A"
                    try:
                        single_data['UpNCT'] = round(item.get('UpperThresholdNonCritical'), 3)
                    except:
                        single_data['UpNCT'] = "N/A"
                    try:
                        single_data['UpCT'] = round(item.get('UpperThresholdCritical'), 3)
                    except:
                        single_data['UpCT'] = "N/A"
                    try:
                        single_data['UpNRT'] = round(item.get("UpperThresholdFatal"), 3)
                    except:
                        single_data['UpNRT'] = "N/A"
                    data_sum.append(single_data)
            if result.Message.get(url_result.get('url')[1]).State:
                info = result.Message.get(url_result.get('url')[1]).Message.get('Sensors')
                if info is None:
                    res.State("Failure")
                    res.Message('Return info has no key of Sensors.')
                    return res
                for item in info:
                    single_data = collections.OrderedDict()
                    single_data['ID'] = item.get('SensorIndex', "N/A")
                    single_data['Sensor'] = item.get('Name', "N/A")
                    single_data['State'] = item.get('Status', {}).get('State', "N/A")
                    single_data['Reading'] = "N/A"
                    single_data['Unit'] = "Discrete"
                    single_data['LowNRT'] = "N/A"
                    single_data['LowCT'] = "N/A"
                    single_data['LowNCT'] = "N/A"
                    single_data['UpNCT'] = "N/A"
                    single_data['UpCT'] = "N/A"
                    single_data['UpNRT'] = "N/A"
                    data_sum.append(single_data)
            res.State("Success")
            res.Message(data_sum)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getbmcinfo(self, client, args):
        result = ResultBean()
        infoList = []
        status = 0
        product = IpmiFunc.getAllFruByIpmi(client)
        if product:
            frubean = FruBean()
            frubean.FRUID(product.get('fru_id', None))
            frubean.ChassisType(product.get('Chassis Type', None))
            frubean.ProductManufacturer(
                product.get('Product Manufacturer', None))
            frubean.ProductName(product.get('Product Name', None))
            frubean.ProductPartNumber(
                product.get('Product Part Number', None))
            frubean.ProductSerial(product.get('Product Serial', None))
            frubean.ProductAssetTag(product.get('Product Asset Tag', None))
            infoList.append(frubean.dict)
        else:
            result.State('Failure')
            result.Message('Can not get - information')
            return result
        res = self.getnetwork(client, args)
        if res.State != 'Success':
            result.State("Failure")
            result.Message(["cannot get lan information"])
            return result
        else:
            infoList.extend(res.Message)
        result.State("Success")
        result.Message(infoList)
        return result

    def getserver(self, client, args):
        url_result = self.get_url_info("getoverview")
        res = ResultBean()
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message
            healthSumary = info.get("HealthSumary")
            data = {}
            data['UIDLed'] = info.get("IndicatorLED", "N/A")
            data['CPU'] = healthSumary.get("Processor", "N/A")
            data['Memory'] = healthSumary.get("Memory", "N/A")
            data['System'] = healthSumary.get("Whole", "N/A")
            data['Storage'] = healthSumary.get("Drive", "N/A")
            data['Fan'] = healthSumary.get("Fan", "N/A")
            data['Network'] = healthSumary.get("NetWorkAdapter", "N/A")
            data['Pcie'] = healthSumary.get("PCIeDevice", "N/A")
            data['PSU'] = healthSumary.get("Power", "N/A")
            data['TEMP'] = info.get("TemperatureSensorState", "N/A")
            res.State("Success")
            res.Message(data)
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def getsessions(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            session_data = result.Message
            seList = []
            for item in session_data:
                session_result = SessionBean()
                session_result.SessionID(item.get('Id', None))
                session_result.SessionType(item.get('SessionType', None))
                session_result.ClientIP(item.get('ClientOriginIPAddress', None))
                session_result.UserName(item.get('UserName', None))
                seList.append(session_result.dict)
            res.State('Success')
            res.Message(seList)
        else:
            res.State("Failure")
            res.Message([result.Message])
        return res

    def delsession(self, client, args):
        # 先get
        id_list = []
        url_result = self.get_url_info("getsessions")
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            session_data = result.Message
            for item in session_data:
                id_list.append(item.get('Id'))

            # 如果输入参数，检查参数范围，如果正确，进行删除
            if args.id == 'all':
                # 如果不输入，循环调用，全部删除
                flag = []
                for id in id_list:
                    delete_url = url_result.get('url') + "/" + id
                    del_result = RedfishTemplate.delete_for_object(client, delete_url)
                    if del_result.State:
                        continue
                    else:
                        flag.append(id)
                        continue
                if len(flag) != 0:
                    res.State('Failure')
                    res.Message(['delete session id {0} failed.'.format(
                        ','.join(flag) if len(flag) > 1 else flag)])
                else:
                    res.State('Success')
                    res.Message(['delete session id {0} success, please wait a few seconds.'.format(
                        ','.join(id_list) if len(id_list) > 1 else id_list)])
            else:
                if str(args.id) in id_list:
                    delete_url = url_result.get('url') + "/" + args.id
                    del_result = RedfishTemplate.delete_for_object(client, delete_url)
                    if del_result.State:
                        res.State('Success')
                        res.Message(['delete session id {0} success, please wait a few seconds.'.format(args.id)])
                    else:
                        res.State('Failure')
                        res.Message(['delete session id {0} failed， '.format(args.id) + del_result.Message])
                else:
                    res.State('Failure')
                    res.Message(['wrong session id, please input right id, id list is {0}.'.format(
                        ','.join(id_list) if len(id_list) > 1 else id_list)])
        else:
            res.State('Failure')
            res.Message(['failed to get session info, ' + result.Message])
        return res

    def getusergroup(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_collection_object(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            uglist = []
            for item in info:
                userGroup = collections.OrderedDict()
                userGroup["GroupId"] = item['Id']
                userGroup["GroupName"] = item['RoleId']
                group = item['AssignedPrivileges']
                oemgroup = item['OemPrivileges']
                userGroup["UserConfig"] = "Y" if 'ConfigureUsers' in group else "-"
                userGroup["CommConfig"] = "Y" if 'ConfigureComponents' in group else "-"
                userGroup["PowerCon"] = "Y" if 'OemPowerControl' in oemgroup else "-"
                userGroup["RemoteMedia"] = "Y" if 'OemRemoteMedia' in oemgroup else "-"
                userGroup["RemoteKVM"] = "Y" if 'OemRemoteKvm' in oemgroup else "-"
                userGroup["SecuCon"] = "Y" if 'OemSecureMgmt' in oemgroup else "-"
                userGroup["Debug"] = "Y" if 'OemDebug' in oemgroup else "-"
                userGroup["InfoQuery"] = "Y" if 'Login' in group else "-"
                userGroup["SelfSet"] = "Y" if 'ConfigureSelf' in group else "-"

                uglist.append(userGroup)
            res.State("Success")
            res.Message([{"UserGroup": uglist}])
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def addusergroup(self, client, args):
        login_res = ResultBean()
        login_res.State("Failure")
        login_res.Message(["only support modify user group(OEM1/OEM2/OEM3/OEM4)."])
        return login_res

    def setusergroup(self, client, args):
        res = ResultBean()
        if args.name in ["Administrator", " Operator", "User"]:
            res.State("Failure")
            res.Message(
                ["Cannot modify default user group(Administrator/Operator/User)."])
            return res
        if args.name not in ["OEM1", "OEM2", "OEM3", "OEM4"]:
            res.State("Failure")
            res.Message(
                ["only support modify user group(OEM1/OEM2/OEM3/OEM4)."])
            return res

        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get("url") + '/' + args.name)
        if result.State:
            info = result.Message
            group = list(info['AssignedPrivileges'])
            oemgroup = list(info['OemPrivileges'])
        if args.general is not None:
            if 'enable' == args.general:
                group.append('ConfigureComponents')
            else:
                group.remove('ConfigureComponents')
        if args.power is not None:
            if 'enable' == args.power:
                oemgroup.append('OemPowerControl')
            else:
                oemgroup.remove('OemPowerControl')
        if args.media is not None:
            if 'enable' == args.media:
                oemgroup.append('OemRemoteMedia')
            else:
                oemgroup.remove('OemRemoteMedia')
        if args.kvm is not None:
            if 'enable' == args.kvm:
                oemgroup.append('OemRemoteKvm')
            else:
                oemgroup.remove('OemRemoteKvm')
        if args.security is not None:
            if 'enable' == args.security:
                oemgroup.append('OemSecureMgmt')
            else:
                oemgroup.remove('OemSecureMgmt')
        if args.debug is not None:
            if 'enable' == args.debug:
                oemgroup.append('OemDebug')
            else:
                oemgroup.remove('OemDebug')
        if args.self is not None:
            if 'enable' == args.self:
                group.append('ConfigureSelf')
            else:
                group.remove('ConfigureSelf')
        patchBody = {}
        patchBody['url'] = url_result.get('url') + '/' + args.name
        patchBody['json'] = {'AssignedPrivileges': group, 'OemPrivileges': oemgroup}
        result = RedfishTemplate.patch_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message('')
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def delusergroup(self, client, args):
        login_res = ResultBean()
        login_res.State("Failure")
        login_res.Message(["Not Support, Cannot delete user group.(edit it instead)"])
        return login_res

    def editusergroup(self, client, args):
        result = ResultBean()
        if args.state == 'absent':
            result = self.delusergroup(client, args)
        elif args.state == 'present':
            result = ResultBean()
            group = ['OEM1', 'OEM2','OEM3','OEM4']

            if args.name in group:
                result = self.setusergroup(client, args)
            else:
                result = self.addusergroup(client, args)
        return result

    def getssl(self, client, args):
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        res = ResultBean()
        if result.State:
            info = result.Message
            pub= info.get('Oem', {}).get('Public', {})
            sslInfo = collections.OrderedDict()
            sslInfo["Certificate Version"] = pub.get('CertificateVersion', 'N/A')
            sslInfo["SerialNumber"] = pub.get('SerialNumber', 'N/A')
            sslInfo["Signature Algorithms"] = pub.get('SignatureAlgorithm', 'N/A')
            sslInfo["Valid Not After"] = info.get('ValidNotAfter', 'N/A')
            sslInfo["Valid Not Before"] = info.get('ValidNotBefore', 'N/A')
            issuer = info.get('Issuer', {})
            sslInfo["Issuer Common Name"] = issuer.get('CommonName', 'N/A')
            sslInfo["Issuer Country"] = issuer.get('Country', 'N/A')
            sslInfo["Issuer Organization Unit"] = 'N/A'
            sslInfo["Issuer Organization"] = issuer.get('Organization', 'N/A')
            sslInfo["Issuer State"] = 'N/A'
            sslInfo["Issuer City"] = 'N/A'
            sslInfo["Issuer Email"] = 'N/A'
            subject = info.get('Subject', {})
            sslInfo["Subject Common Name"] = subject.get('CommonName', 'N/A')
            sslInfo["Subject Country"] = subject.get('Country', 'N/A')
            sslInfo["Subject Organization Unit"] = 'N/A'
            sslInfo["Subject Organization"] = subject.get('Organization', 'N/A')
            sslInfo["Subject State"] = 'N/A'
            sslInfo["Subject City"] = 'N/A'
            sslInfo["Subject Email"] = 'N/A'
            res.State("Success")
            res.Message([sslInfo])
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def setssl(self, client, args):
        res = ResultBean()
        if args.commonname is None or args.organization is None or args.organizationunit is None or \
                args.citylocality is None or args.stateprovince is None or args.country is None or \
                args.email is None or args.validtime is None:
            res.State("Failure")
            res.Message(["All the parameters must not be left blank."])
            return res
        if not self._validate_64_str(args.commonname):
            res.State("Failure")
            res.Message(["CommonName should be a string with a maximum length of 64 characters which allow letters, numbers, hyphens (-), underscores (_), dots (.), and spaces."])
            return res
        if not self._validate_64_str(args.organization):
            res.State("Failure")
            res.Message(["Organization should be a string with a maximum length of 64 characters which allow letters, numbers, hyphens (-), underscores (_), dots (.), and spaces."])
            return res
        if not self._validate_64_str(args.organizationunit):
            res.State("Failure")
            res.Message(["OrganizationUnit should be a string with a maximum length of 64 characters which allow letters, numbers, hyphens (-), underscores (_), dots (.), and spaces."])
            return res
        if not self._validate_128_str(args.citylocality):
            res.State("Failure")
            res.Message(["Citylocality should be a string with a maximum length of 128 characters which allow letters, numbers, hyphens (-), underscores (_), dots (.), and spaces"])
            return res
        if not self._validate_128_str(args.stateprovince):
            res.State("Failure")
            res.Message(["StateProvince should be a string with a maximum length of 128 characters which allow letters, numbers, hyphens (-), underscores (_), dots (.), and spaces"])
            return res
        if not self._validate_2_str(args.country):
            res.State("Failure")
            res.Message(["Country should be two characters and not allow special characters"])
            return res
        if args.validtime < 1 or args.validtime > 3650:
            res.State("Failure")
            res.Message(["ValidTime should be within the range of 1 to 3650 days"])
            return res
        url_result = self.get_url_info(sys._getframe().f_code.co_name)
        data = {
            "Country":args.country,
            "CommonName":args.commonname,
            "City":args.citylocality,
            "State":args.stateprovince,
            "OrgName":args.organization,
            "OrgUnit":args.organizationunit,
            "EmailID":args.email,
            "ValidDays":args.validtime,
            "KeyLength":2048
        }
        patchBody = {}
        patchBody['url'] = url_result.get('url') + + args.name
        patchBody['json'] = data
        result = RedfishTemplate.post_for_object(client, patchBody)
        if result.State:
            res.State("Success")
            res.Message('')
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    def _validate_64_str(self, input_str):
        pattern = '^[a-zA-Z0-9\-\_\. ]{1,64}$'
        return bool(re.search(pattern, input_str, re.I))

    def _validate_128_str(self, input_str):
        pattern = '^[a-zA-Z0-9\-\_\. ]{1,128}$'
        return bool(re.search(pattern, input_str, re.I))

    def _validate_2_str(self, input_str):
        pattern = '^[A-Z]{2}$'
        return bool(re.search(pattern, input_str, re.I))

    def uploadssl(self, client, args):
        res = ResultBean()
        if args.certificate is None or args.private is None:
            res.State("Failure")
            res.Message(["All the parameters must not be left blank."])
            return res
        url_result = self.get_url_info("uploadssl")
        postBody = {}
        postBody['data'] = {}
        postBody['file'] = [('new_certificate', open(args.certificate, 'rb')),
                            ('new_private_key', open(args.private, 'rb')),
                            ('current_password', args.passcode),
                            ('encrypt_flag', False)]
        postBody['url'] = url_result.get('url')
        result = RedfishTemplate.post_for_object(client, postBody)
        if result.State:
            res.State("Success")
            res.Message('')
        else:
            res.State("Failure")
            res.Message(result.Message)
        return res

    #update
    def fwupdate(self, client, args):
        if args.type == "BMC":
            return self.updatebmc(client, args)
        elif args.type == "BIOS":
            return self.updatebios(client, args)
        else:
            res = ResultBean()
            res.State("Failure")
            res.Message(["Not Support, Update " + args.type + " is not support"])
            return res

    def gettaskid(self, client, args):
        if args.type in self.task_dict:
            return self.task_dict.get(args.type)
        elif args.type == "BP_CPLD":
            url_result = self.get_url_info("get_update_process")
            res = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
            if res.State:
                urllist = res.Message.get("Members")
                for urlbody in urllist:
                    taskid = urlbody.get("@odata.id").split("/")[-1]
                    if "BP" in taskid and "_CPLD" in taskid:
                        return taskid
        return None


    def getrollbacktaskid(self, client, args):
        url_result = self.get_url_info("get_update_process")
        res = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if res.State:
            urllist = res.Message.get("Members")
            for urlbody in urllist:
                taskid = urlbody.get("@odata.id").split("/")[-1]
                if "rollback" in taskid.lower():
                    return taskid
        return None

    def updatebios(self, client, args):
        result = ResultBean()
        # 文件校验
        if not os.path.exists(args.url):
            result.State("Failure")
            result.Message("File not exist. Please select valid image file.")
            return result
        if not os.path.isfile(args.url):
            result.State("Failure")
            result.Message("Please select valid image file")
            return result

        hpmflag, hpminfo = getHpmInfo(args.url)
        if not hpmflag:
            result.State("Failure")
            result.Message([hpminfo])
            return result

        #校验
        if hpminfo.get("des") == "BIOS_PFR":
            args.type = "BIOS_PFR"
            return self.updatebiosPFR(client, args)

        if hpminfo.get("des") != "BIOS":
            result.State("Failure")
            result.Message("not valid BIOS update file")
            return result

        log_path = self._get_update_log_path(client, args)
        wirte_log(log_path, "Upload File", "Network Ping OK", "")
        try:
            update_flag = self._get_update_service(client, args)
            if update_flag:
                wirte_log(log_path, "Upload File", "Update service is enabled", "")
            else:
                result.State("Failure")
                result.Message("Update service is disabled, please check server manually.")
                return result

            fw_version = self._get_firmware_version(client, args)
            if fw_version != "":
                wirte_log(log_path, "Upload File", "current BIOS version: " + str(fw_version), "")
            wirte_log(log_path, "Upload File", "start to update " + args.type, "")
            wirte_log(log_path, "Upload File", "Upload file start " + os.path.abspath(args.url), "")
            flag, message = self._upload_file(client, args)
            if flag:
                wirte_log(log_path, "Upload File", "upload file successfully", "")
            else:
                wirte_log(log_path, "Upload File", "upload file failed", message)
                result.State("Failure")
                result.Message("update %s failed." % args.type)
                return result

            if args.override == 0:
                wirte_log(log_path, "Apply", "start to execute update with all preserve", "")
            else:
                wirte_log(log_path, "Apply", "start to execute update with no preserve", "")
            flag, message = self._execute_update(client, args)
            if flag:
                wirte_log(log_path, "Apply", "execute update successfully", "")
                wirte_log(log_path, "Apply", "Apply(Flash) start", "")
            else:
                wirte_log(log_path, "Apply", "execute update failed", message)
                result.State("Failure")
                result.Message("update %s failed." % args.type)
                return result

            # 尝试获取进度
            time.sleep(30)
            #获取新增的bios进度

            #获取开关机状态
            powerstatus = None
            power_info = self.getpowerstatus(client, args)
            if power_info.State == "Success":
                powerstatus = power_info.Message.get("PowerStatus")


            if powerstatus and powerstatus.lower() == "on":
                if args.mode == 'Manual':
                    wirte_log(log_path, "Apply", "Apply(FLASH) pending, trigger: power off.", "")
                    result.State('Success')
                    result.Message("Apply(FLASH) pending, trigger: power off.")
                    return result
                else:
                    args.state = "cycle"
                    power_info = self.powercontrol(client, args)
                    if power_info.State == "Success":
                        wirte_log(log_path, "Activate", "Set power cycle successfully", "")
                    else:
                        wirte_log(log_path, "Activate", "Set power cycle failed", "please check the server")
                        result.State("Failure")
                        result.Message("Update bios complete, but power cycle server failed. " + str(power_info.Message))
                        return result

            #
            task0 = "/redfish/v1/TaskService/Tasks/BIOS0"
            task1 = "/redfish/v1/TaskService/Tasks/BIOS1"
            task0status = False
            stime = time.time()
            while True:
                ftime = time.time()
                if ftime - stime > 600:
                    wirte_log(log_path, "Apply", "Apply(Flash) timeout", "")
                    result.State('Failure')
                    result.Message("Apply(FLASH) timeout.")
                    return result


                res = RedfishTemplate.get_for_object_single(client, task0)
                if res.State:
                    taskinfo = res.Message
                    if taskinfo.get("TaskStatus") == "OK":
                        if taskinfo.get("TaskState") == "Running":
                            wirte_log(log_path, "Apply", "In Progress",
                                      "progress:" + str(taskinfo.get("PercentComplete")) + "%")
                            time.sleep(10)
                        elif taskinfo.get("TaskState") == "Completed":
                            task0status = True
                            wirte_log(log_path, "Apply", "In Progress",
                                      "progress:" + str(taskinfo.get("PercentComplete")) + "%")
                            if task0 == task1:
                                wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
                                break
                                # result.State('Success')
                                # result.Message("")
                                # return result
                            else:
                                task0 = task1
                                time.sleep(20)
                        else:
                            continue
                    else:
                        wirte_log(log_path, "Apply", "Flash", "task failed")
                        result.State("Failure")
                        result.Message("Update failed. " + str(taskinfo))
                        return result

                else:
                    #镜像0刷新完成
                    if task0status:
                        wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
                        break
                    continue

            if powerstatus and powerstatus.lower() == "off":
                if args.mode == 'Auto':
                    args.state = "on"
                    power_info = self.powercontrol(client, args)
                    if power_info.State == "Success":
                        wirte_log(log_path, "Activate", "Set power on successfully", "")
                        result.State('Success')
                        result.Message("")
                    else:
                        wirte_log(log_path, "Activate", "Set power cycle failed", "please check the server")
                        result.State("Failure")
                        result.Message("Update bios complete, but power on server failed. " + str(power_info.Message))
                else:
                    result.State('Success')
                    result.Message("")
            else:
                result.State('Success')
                result.Message("")

        except Exception as e:
            result = ResultBean()
            result.State("Failure")
            result.Message(str(e))
        return result

    def updatebiosPFR(self, client, args):
        result = ResultBean()
        # 文件校验
        if not os.path.exists(args.url):
            result.State("Failure")
            result.Message("File not exist. Please select valid image file.")
            return result
        if not os.path.isfile(args.url):
            result.State("Failure")
            result.Message("Please select valid image file")
            return result

        log_path = self._get_update_log_path(client, args)

        hpmflag, hpminfo = getHpmInfo(args.url)
        if not hpmflag:
            result.State("Failure")
            result.Message([hpminfo])
            return result
        wirte_log(log_path, "Upload File", "Network Ping OK", "")

        try:
            update_flag = self._get_update_service(client, args)
            if update_flag:
                wirte_log(log_path, "Upload File", "Update service is enabled", "")
            else:
                result.State("Failure")
                result.Message("Update service is disabled, please check server manually.")
                return result

            fw_version = self._get_firmware_version(client, args)
            if fw_version != "":
                wirte_log(log_path, "Upload File", "current BIOS version: " + str(fw_version), "")
            wirte_log(log_path, "Upload File", "start to update " + args.type, "")
            wirte_log(log_path, "Upload File", "Upload file start " + os.path.abspath(args.url), "")
            flag, message = self._upload_file(client, args)
            if flag:
                wirte_log(log_path, "Upload File", "upload file successfully", "")
            else:
                wirte_log(log_path, "Upload File", "upload file failed", message)
                result.State("Failure")
                result.Message("update %s failed." % args.type)
                return result

            if args.override == 0:
                wirte_log(log_path, "Apply", "start to execute update with all preserve", "")
            else:
                wirte_log(log_path, "Apply", "start to execute update with no preserve", "")
            flag, message = self._execute_update(client, args)
            if flag:
                wirte_log(log_path, "Apply", "execute update successfully", "")
                wirte_log(log_path, "Apply", "Apply(Flash) start", "")
            else:
                wirte_log(log_path, "Apply", "execute update failed", message)
                result.State("Failure")
                result.Message("update %s failed." % args.type)
                return result

            # 尝试获取进度
            time.sleep(30)
            #获取新增的bios进度

            #获取开关机状态
            powerstatus = None
            power_info = self.getpowerstatus(client, args)
            if power_info.State == "Success":
                powerstatus = power_info.Message.get("PowerStatus")


            if powerstatus and powerstatus.lower() == "on":
                if args.mode == 'Manual':
                    wirte_log(log_path, "Apply", "Apply(FLASH) pending, trigger: power off.", "")
                    result.State('Success')
                    result.Message("Apply(FLASH) pending, trigger: power off.")
                    return result
                else:
                    args.state = "cycle"
                    power_info = self.powercontrol(client, args)
                    if power_info.State == "Success":
                        wirte_log(log_path, "Activate", "Set power cycle successfully", "")
                    else:
                        wirte_log(log_path, "Activate", "Set power cycle failed", "please check the server")
                        result.State("Failure")
                        result.Message("Update bios complete, but power cycle server failed. " + str(power_info.Message))
                        return result
            else:
                if args.mode == 'Auto':
                    args.state = "on"
                    power_info = self.powercontrol(client, args)
                    if power_info.State == "Success":
                        wirte_log(log_path, "Activate", "Set power on successfully", "")
                    else:
                        wirte_log(log_path, "Activate", "Set power on failed", "please check the server")
                        result.State("Failure")
                        result.Message("Update bios complete, but power on server failed. " + str(power_info.Message))
                        return result
            #
            task0 = "/redfish/v1/TaskService/Tasks/bios"
            stime = time.time()
            completeflag = False
            while True:
                ftime = time.time()
                if ftime - stime > 600:
                    wirte_log(log_path, "Apply", "Apply(Flash) timeout", "")
                    result.State('Failure')
                    result.Message("Apply(FLASH) timeout.")
                    return result


                res = RedfishTemplate.get_for_object_single(client, task0)
                if res.State:
                    taskinfo = res.Message
                    if taskinfo.get("TaskStatus") == "OK":
                        if taskinfo.get("TaskState") == "Running" or  taskinfo.get("TaskState") == "Starting":
                            wirte_log(log_path, "Apply", "In Progress",
                                      "progress:" + str(taskinfo.get("PercentComplete")) + "%")
                            time.sleep(10)
                        elif taskinfo.get("TaskState") == "Completed":
                            completeflag = True
                            wirte_log(log_path, "Apply", "In Progress",
                                      "progress:" + str(taskinfo.get("PercentComplete")) + "%")
                            wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
                            break
                        else:
                            continue
                    else:
                        wirte_log(log_path, "Apply", "Flash", "task failed")
                        result.State("Failure")
                        result.Message("Update failed. " + str(taskinfo))
                        return result
                else:
                    break
            if not completeflag:
                wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")

            wirte_log(log_path, "Apply", "BMC reboot start, please wait 15 mins", "")
            result.State("Success")
            result.Message("BMC rebooting")
        except Exception as e:
            wirte_log(log_path, "Apply", "update bios exception", str(e))
            result = ResultBean()
            result.State("Failure")
            result.Message(str(e))
        return result

    def updatebmc(self, client, args):
        result = ResultBean()
        # 文件校验
        if not os.path.exists(args.url):
            result.State("Failure")
            result.Message("File not exist. Please select valid image file.")
            return result
        if not os.path.isfile(args.url):
            result.State("Failure")
            result.Message("Please select valid image file")
            return result

        log_path = self._get_update_log_path(client, args)
        hpmflag, hpminfo = getHpmInfo(args.url)
        if not hpmflag:
            result.State("Failure")
            result.Message([hpminfo])
            return result
        if hpminfo.get("des") == "BMC_PFR":
            args.type = "BMC_PFR"
            return self.updatebmcPFR(client, args)
        if hpminfo.get("des") != "APP" and hpminfo.get("des") != "OPENBMC":
            result.State("Failure")
            result.Message("not valid bmc update file")
            return result
        wirte_log(log_path, "Upload File", "Network Ping OK", "")

        update_flag = self._get_update_service(client, args)
        if update_flag:
            wirte_log(log_path, "Upload File", "Update service is enabled", "")
        else:
            result.State("Failure")
            result.Message("Update service is disabled, please check server manually.")
            return result

        fw_version = self._get_firmware_version(client, args)
        if fw_version != "":
            wirte_log(log_path, "Upload File", "current BMC version: " + str(fw_version), "")

        wirte_log(log_path, "Upload File", "start to update " + args.type, "")
        wirte_log(log_path, "Upload File", "Upload file start " + os.path.abspath(args.url), "")
        flag, message = self._upload_file(client, args)
        if flag:
            wirte_log(log_path, "Upload File", "upload file successfully", "")
        else:
            wirte_log(log_path, "Upload File", "upload file failed", message)
            result.State("Failure")
            result.Message("update %s failed." % args.type)
            return result

        if args.override == 0:
            wirte_log(log_path, "Apply", "start to execute update with all preserve", "")
        else:
            wirte_log(log_path, "Apply", "start to execute update with no preserve", "")
        flag, message = self._execute_update(client, args)
        if flag:
            wirte_log(log_path, "Apply", "execute update successfully", "")
            wirte_log(log_path, "Apply", "Apply(Flash) start", "")
        else:
            wirte_log(log_path, "Apply", "execute update failed", message)
            result.State("Failure")
            result.Message("update %s failed." % args.type)
            return result
        taskid = self.gettaskid(client, args)
        count_100 = 0
        error_count = 0
        for i in range(60):
            if error_count > 3:
                wirte_log(log_path, "Apply", "cannot get percentage, try to login BMC...", "")
                break
            flag, message, task_state = self._get_task_percent(client, args, taskid)
            if flag:
                wirte_log(log_path, "Apply", "In progress", "progress: " + str(message) + "%")
                if int(message) == 100 or task_state == "Completed":
                    count_100 += 1
                    break
            else:
                wirte_log(log_path, "Apply", "In progress", "get progress failed...")
                error_count += 1
            time.sleep(10)
        if count_100 >= 1:
            wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")

        wirte_log(log_path, "Apply", "BMC reboot start", "")
        #2024年4月29日 带内不去检查是否成功
        if client.host == "169.254.0.17":
            result.State("Success")
            result.Message("")
            return result
        if client.host == "192.168.1.100":
            result.State("Success")
            result.Message("")
            return result

        time.sleep(60)
        wirte_log(log_path, "Apply", "BMC reboot inprogress", "")
        time.sleep(60)
        wirte_log(log_path, "Apply", "BMC reboot inprogress", "")
        time.sleep(60)

        stime = time.time()
        session_url = self.get_url_info("get_sessions")
        while True:
            rtime = time.time()
            if rtime - stime > 420:
                result.State("Failure")
                uploadfailinfo = "BMC reboot timeout."
                result.Message([uploadfailinfo])
                wirte_log(log_path, "Apply", "BMC reboot timeout", "")
                return result

            # 任意访问一个接口
            login_res = RedfishTemplate.get_for_object_single(client, session_url.get('url'))
            if login_res.State:
                break
            else:
                time.sleep(20)
                continue

        wirte_log(log_path, "Apply", "BMC reboot complete", "")
        abmcversion = "-"
        bbmcversion = "-"
        rollbackflag = False
        bmc_res = self.getfw(client, args)
        if bmc_res.State == "Success":
            bmc_info = bmc_res.Message
            for item in bmc_info:
                if item.get("ActiveBMC"):
                    abmcversion = item.get("ActiveBMC")
                elif item.get("BackupBMC"):
                    bbmcversion = item.get("BackupBMC")
            if abmcversion != "-":
                if abmcversion == bbmcversion:
                    wirte_log(log_path, "Apply", "BMC version: " + abmcversion, "")
                    result.State("Success")
                    result.Message("")
                    return result
                else:
                    rollbackflag = True

        if not rollbackflag:
            result.State("Failure")
            result.Message("BMC update complete, but cannot get active bmc version." + str(bmc_res.Message))
            return result
        else:
            time.sleep(15)
            taskrbid = self.getrollbacktaskid(client, args)
            if taskrbid is not None:
                wirte_log(log_path, "Apply", "BMC rollback start", "")
                url_result = self.get_url_info("get_update_process")
                taskurl = url_result.get('url') + str(taskrbid)
                stime = time.time()
                while True:
                    ftime = time.time()
                    if ftime - stime > 600:
                        wirte_log(log_path, "Apply", "Apply(Flash) timeout", "")
                        result.State('Failure')
                        result.Message("Apply(FLASH) timeout.")
                        return result


                    res = RedfishTemplate.get_for_object_single(client, taskurl)
                    taskinfo = res.Message
                    if res.State:
                        # if taskinfo.get("TaskStatus") == "OK":
                        if taskinfo.get("TaskState") == "Running":
                            wirte_log(log_path, "Apply", "In progress", "progress: " + str(taskinfo.get("PercentComplete")) + "%")
                            time.sleep(10)
                        elif taskinfo.get("TaskState") == "Completed":
                            wirte_log(log_path, "Apply", "In progress",
                                      "progress: " + str(taskinfo.get("PercentComplete")) + "%")
                            wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
                            result.State('Success')
                            result.Message("")
                            return result
                        else:
                            break
                    else:
                        # {'error': 'Task 8 not running!', 'code': 17017}
                        if taskinfo.json().get("code") == 17017:
                            break

        result.State("Success")
        result.Message("")
        return result

    def updatebmcPFR(self, client, args):
        result = ResultBean()
        # 文件校验
        if not os.path.exists(args.url):
            result.State("Failure")
            result.Message("File not exist. Please select valid image file.")
            return result
        if not os.path.isfile(args.url):
            result.State("Failure")
            result.Message("Please select valid image file")
            return result

        log_path = self._get_update_log_path(client, args)

        hpmflag, hpminfo = getHpmInfo(args.url)
        if not hpmflag:
            result.State("Failure")
            result.Message([hpminfo])
            return result

        if hpminfo.get("des") != "BMC_PFR":
            result.State("Failure")
            result.Message("not valid bmc PFR update file")
            return result

        wirte_log(log_path, "Upload File", "Network Ping OK", "")

        update_flag = self._get_update_service(client, args)
        if update_flag:
            wirte_log(log_path, "Upload File", "Update service is enabled", "")
        else:
            result.State("Failure")
            result.Message("Update service is disabled, please check server manually.")
            return result

        fw_version = self._get_firmware_version(client, args)
        if fw_version != "":
            wirte_log(log_path, "Upload File", "current BMC version: " + str(fw_version), "")

        wirte_log(log_path, "Upload File", "start to update " + args.type, "")
        wirte_log(log_path, "Upload File", "Upload file start " + os.path.abspath(args.url), "")
        flag, message = self._upload_file(client, args)
        if flag:
            wirte_log(log_path, "Upload File", "upload file successfully", "")
        else:
            wirte_log(log_path, "Upload File", "upload file failed", message)
            result.State("Failure")
            result.Message("update %s failed." % args.type)
            return result

        if args.override == 0:
            wirte_log(log_path, "Apply", "start to execute update with all preserve", "")
        else:
            wirte_log(log_path, "Apply", "start to execute update with no preserve", "")
        flag, message = self._execute_update(client, args)
        if flag:
            wirte_log(log_path, "Apply", "execute update successfully", "")
            wirte_log(log_path, "Apply", "Apply(Flash) start", "")
        else:
            wirte_log(log_path, "Apply", "execute update failed", message)
            result.State("Failure")
            result.Message("update %s failed." % args.type)
            return result

        taskid = self.gettaskid(client, args)

        error_count = 0
        pro = 0
        message = ""
        for i in range(60):
            if error_count > 3:
                result.State("Failure")
                result.Message("Cannot get task info.")
                return result


            flag, message, task_state = self._get_task_percent(client, args, taskid)
            if flag:
                pro = message
                wirte_log(log_path, "Apply", "In progress", "progress: " + str(pro) + "%")
                if int(message) == 100 or task_state == "Completed":
                    wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
                    break
            else:
                if int(pro) > 80:
                    wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
                    break
                else:
                    wirte_log(log_path, "Apply", "In progress", "get progress failed...")
                    error_count += 1
            time.sleep(10)
        wirte_log(log_path, "Apply", "BMC reboot start, please wait 15 mins.", "")
        result.State("Success")
        result.Message("BMC rebooting")
        return result

    def updatecpld(self, client, args):
        result = ResultBean()
        # 文件校验
        if not os.path.exists(args.url):
            result.State("Failure")
            result.Message(["File not exist. Please select valid image file."])
            return result
        if not os.path.isfile(args.url):
            result.State("Failure")
            result.Message(["Please select valid image file"])
            return result


        #check cpld
        hpmflag, hpminfo = getHpmInfo(args.url)
        if not hpmflag:
            result.State("Failure")
            result.Message([hpminfo])
            return result

        args.type = self.getHpmType(hpminfo)
        log_path = self._get_update_log_path(client, args)

        taskid = self.gettaskid(client, args)
        wirte_log(log_path, "Upload File", "Network Ping OK", "")
        # 获取开关机状态
        powerstatus = None
        power_info = self.getpowerstatus(client, args)
        if power_info.State == "Success":
            powerstatus = power_info.Message.get("PowerStatus")

        update_flag = self._get_update_service(client, args)
        if update_flag:
            wirte_log(log_path, "Upload File", "Update service is enabled", "")
        else:
            result.State("Failure")
            result.Message("Update service is disabled, please check server manually.")
            return result

        wirte_log(log_path, "Upload File", "start to update " + args.type, "")
        wirte_log(log_path, "Upload File", "Upload file start " + os.path.abspath(args.url), "")
        flag, message = self._upload_file(client, args)
        if flag:
            wirte_log(log_path, "Upload File", "upload file successfully", "")
        else:
            wirte_log(log_path, "Upload File", "upload file failed", message)
            result.State("Failure")
            result.Message(["update %s failed." % args.type])
            return result

        wirte_log(log_path, "Apply", "start to execute update", "")
        flag, message = self._execute_update(client, args)
        if flag:
            wirte_log(log_path, "Apply", "execute update successfully", "")
            wirte_log(log_path, "Apply", "Apply(Flash) start", "")
        else:
            wirte_log(log_path, "Apply", "execute update failed", message)
            result.State("Failure")
            result.Message(["update %s failed." % args.type])
            return result

        #不支持前后都有背板的机器
        if taskid == "BP_CPLD":
            taskid = self.getbptaskid(client, args)

        if taskid is None:
            wirte_log(log_path, "Apply", "Upload file complete", "cannot get task id")
            result.State('Success')
            result.Message(["Upload file complete, but cannot get task id."])
            return result

        #判断任务状态
        #PowerOff PowerOn
        triggerflag, trigger = self._get_task_trigger(client, args, taskid)
        #
        if not triggerflag:
            wirte_log(log_path, "Apply", "Upload file complete", "cannot get update triggerd")
            result.State('Success')
            result.Message(["Upload file complete, but cannot get update trigger."])
            msg = self.accycleg7(client, args)
            wirte_log(log_path, "Activate", msg, "")
            return result
        #POWEROFF
        if powerstatus and powerstatus.lower() not in trigger.lower():
            result.State('Success')
            result.Message([
                "Apply(FLASH) pending, host is power " + powerstatus + " now. trigger: " + trigger + ". (TaskId=" + str(taskid) + ")"])
            wirte_log(log_path, "Apply", "Apply(FLASH) pending", "host is power " + powerstatus + " now. trigger: " + trigger + ". (TaskId=" + str(taskid) + ")")
            msg = self.accycleg7(client, args)
            wirte_log(log_path, "Activate", msg, "")
            return result

        count_100 = 0
        error_count = 0
        for i in range(60):
            if error_count > 3:
                wirte_log(log_path, "Apply", "In progress", "cannot get progress..")
                break
            flag, message, task_state = self._get_task_percent(client, args, taskid)
            if flag:
                wirte_log(log_path, "Apply", "In progress", "progress: " + str(message) + "%")
                if int(message) == 100 or task_state == "Completed":
                    count_100 += 1
                    break
            else:
                wirte_log(log_path, "Apply", "In progress", "get progress failed...")
                error_count += 1
            time.sleep(10)

        if count_100 >= 1:
            wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
            result.State("Success")
            result.Message([""])
            msg = self.accycleg7(client, args)
            wirte_log(log_path, "Activate", msg, "")
        else:
            wirte_log(log_path, "Apply", "Apply(Flash) failed", "get update progress failed")
            result.State("Failure")
            result.Message(["Update has already begun, please check the server"])

        return result

    def updatepsu(self, client, args):
        result = ResultBean()
        # 文件校验
        if not os.path.exists(args.url):
            result.State("Failure")
            result.Message(["File not exist. Please select valid image file."])
            return result
        if not os.path.isfile(args.url):
            result.State("Failure")
            result.Message(["Please select valid image file"])
            return result

        log_path = self._get_update_log_path(client, args)
        wirte_log(log_path, "Upload File", "Network Ping OK", "")

        # 获取开关机状态
        powerstatus = None
        power_info = self.getpowerstatus(client, args)
        if power_info.State == "Success":
            powerstatus = power_info.Message.get("PowerStatus")

        update_flag = self._get_update_service(client, args)
        if update_flag:
            wirte_log(log_path, "Upload File", "Update service is enabled", "")
        else:
            result.State("Failure")
            result.Message("Update service is disabled, please check server manually.")
            return result

        wirte_log(log_path, "Upload File", "start to update " + args.type, "")
        wirte_log(log_path, "Upload File", "Upload file start " + os.path.abspath(args.url), "")
        flag, message = self._upload_file(client, args)
        if flag:
            wirte_log(log_path, "Upload File", "upload file successfully", "")
        else:
            wirte_log(log_path, "Upload File", "upload file failed", message)
            result.State("Failure")
            result.Message(["update %s failed." % args.type])
            return result

        wirte_log(log_path, "Apply", "start to execute update", "")
        flag, message = self._execute_update(client, args)
        if flag:
            wirte_log(log_path, "Apply", "execute update successfully", "")
            wirte_log(log_path, "Apply", "Apply(Flash) start", "")
        else:
            wirte_log(log_path, "Apply", "execute update failed", message)
            result.State("Failure")
            result.Message(["update %s failed." % args.type])
            return result

        taskid = self.gettaskid(client, args)

        #判断任务状态

        #PowerOff PowerOn
        triggerflag, trigger = self._get_task_trigger(client, args, taskid)
        #
        if not triggerflag:
            result.State('Success')
            result.Message(["Upload file complete, but cannot get update trigger."])
            wirte_log(log_path, "Apply", "Upload file complete", "cannot get update trigger")
            return result
        #POWEROFF
        if powerstatus and powerstatus.lower() not in trigger.lower():
            result.State('Success')
            wirte_log(log_path, "Apply", "Apply(FLASH) pending",
                      "host is power " + powerstatus + " now. trigger: " + trigger + ". (TaskId=" + str(taskid) + ")")
            return result

        error_count = 0
        for i in range(90):
            #2025年4月18日 继续增加时长 从3600增加为8*22*60=10560
            time.sleep(120)
            if error_count > 3:
                wirte_log(log_path, "Apply", "Apply(Flash) failed", "get update progress failed")
                result.State("Failure")
                result.Message(["Update has already begun, please check the server"])
                return result
            flag, message, task_state = self._get_task_percent(client, args, taskid)
            if flag:
                if task_state == "Cancelled":
                    wirte_log(log_path, "Apply", "Apply(Flash) cancelled", "")
                    result.State("Failure")
                    result.Message(["Update cancelled."])
                elif task_state == "Completed":
                    wirte_log(log_path, "Apply", "Apply(Flash) successfully", "")
                    result.State("Success")
                    result.Message([""])
                elif task_state == "Running":
                    wirte_log(log_path, "Apply", "In progress", "progress: " + str(message) + "%")
                    continue
                else:
                    wirte_log(log_path, "Apply", "Apply(Flash) failed", "")
                    result.State("Failure")
                    result.Message(["Update failed."])
                return result

            else:
                wirte_log(log_path, "Apply", "In progress", "get progress failed...")
                error_count += 1
        wirte_log(log_path, "Apply", "Apply(Flash) timeout", "")
        result.State("Failure")
        result.Message(["Apply(Flash) timeout"])
        return result

    task_dict = {
        "BMC": "BMC",
        "BMCRollback": "ROLLBACK",
        "BMC_PFR": "bmc",
        "BIOS": None,
        "MB": "MB_CPLD",
        "SCM_CPLD": "SCM_CPLD",
        # "BP_CPLD": "BP0_CPLD",
    }

    def accycleg7(self, client, args):
        time.sleep(30)
        if "auto_ac" in args and args.auto_ac == 1:
            acres = IpmiFunc.ACCycleG7(client)
            if acres.get("code") == 0:
                return "AC cycle complete."
            else:
                return "AC cycle failed." + acres.get("data")
    def getHpmType(self, hpmrawdict):
        # 解析镜像
        result = ()
        hpmdict = {}
        file_version = hpmrawdict.get("version")
        seamless_version = hpmrawdict.get("seamless_version")
        boardidlist = hpmrawdict.get("boardid")
        file_des = hpmrawdict.get("des")
        typeflag = False
        if str(file_des).upper() == "CPLD":
            if 80 in boardidlist:
                return "SCM_CPLD"
            else:
                return "MB"
        elif str(file_des).upper().startswith('YZBB'):
            return "BP_CPLD"
        elif str(file_des).upper().startswith('YZCF'):
            return "FAN_CPLD"
        else:
            return file_des

    def _get_ftime(self, ff="%Y-%m-%d %H:%M:%S "):
        try:
            localtime = time.localtime()
            f_localtime = time.strftime(ff, localtime)
            return f_localtime
        except:
            return ""

    # 查询当前服务器状态能否升级
    def _get_update_service(self, client, args):
        update_flag = False
        url_result = self.get_url_info("get_update_service")
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message
            update_flag = info.get("ServiceEnabled", False)
        return update_flag

    def _get_firmware_version(self, client, args):
        version = ""
        url_dict = {
            'BMC': 'get_active_bmc_version',
            'BMC_PFR': 'get_active_bmc_version',
            'BIOS': 'get_bios_version',
            'BIOS_PFR': 'get_bios_version',
        }
        url_result = self.get_url_info(url_dict.get(args.type))
        result = RedfishTemplate.get_for_object_single(client, url_result.get('url'))
        if result.State:
            info = result.Message
            version = str(info.get("Version", "")).split("(")[0]
        return version

    # 上传文件
    def _upload_file(self, client, args):
        url_result = self.get_url_info("upload_update_file")
        postBody = {}
        postBody['data'] = {}
        postBody['file'] = [('fwimage', open(args.url, 'rb'))]
        postBody['url'] = url_result.get('url')
        res = RedfishTemplate.post_for_object(client, postBody)
        if res.State:
            return True, None
        else:
            return False, str(res.Message)

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
            data['PFRUpdateDynamic'] = pre_dict.get(args.override)
        else:
            data['PreserveConf'] = pre_dict.get(1 - args.override)
        if args.type == "BIOS":
            data['BiosFlash'] = "Both"

        data = {"Oem": {"Public": data}}
        postBody = {}
        postBody['json'] = data
        postBody['url'] = url_result.get('url')
        res = RedfishTemplate.post_for_object(client, postBody)
        if res.State:
            return True, None
        else:
            return False, str(res.Message)

    def getbptaskid(self, client, args):
        url_result = self.get_url_info("get_update_process")
        res = RedfishTemplate.get_for_object_single(client, url_result.get('url') + "3")
        if res.State:
            return 3
        else:
            return 4

    # 获取进度
    def _get_task_trigger(self, client, args, task_id):
        url_result = self.get_url_info("get_update_process")
        res = RedfishTemplate.get_for_object_single(client, url_result.get('url') + str(task_id))
        if res.State:
            return True, res.Message.get('Oem', {}).get('Public', {}).get("Trigger")
        else:
            return False, str(res.Message)

    # 获取进度
    def _get_task_percent(self, client, args, task_id):
        url_result = self.get_url_info("get_update_process")
        res = RedfishTemplate.get_for_object_single(client, url_result.get('url') + str(task_id))
        if res.State:
            if res.Message.get('PercentComplete') is not None and res.Message.get('TaskState') is not None:
                return True, res.Message.get('PercentComplete'), res.Message.get('TaskState')
            else:
                return False, str(res.Message), "Failed"
        else:
            return False, str(res.Message), "Failed"

    def _get_update_log_path(self, client, args):
        def ftime(ff="%Y-%m-%d %H:%M:%S "):
            try:
                import time
                localtime = time.localtime()
                f_localtime = time.strftime(ff, localtime)
                return f_localtime
            except BaseException:
                return ""
        psn = "UNKNOWN"
        res_syn = self.getfru(client, args)
        if res_syn.State == "Success":
            frulist = res_syn.Message[0].get("FRU", [])
            if frulist != []:
                psn = frulist[0].get('ProductSerial', 'UNKNOWN')
        logtime = ftime("%Y%m%d%H%M%S")
        dir_name = logtime + "_" + psn
        # 创建目录
        T6_path = os.path.abspath(__file__)
        interface_path = os.path.split(T6_path)[0]
        root_path = os.path.dirname(interface_path)
        update_path = os.path.join(root_path, "update")
        if not os.path.exists(update_path):
            os.makedirs(update_path)
        update_plog_path = os.path.join(update_path, dir_name)
        if not os.path.exists(update_plog_path):
            os.makedirs(update_plog_path)
        log_path = os.path.join(update_plog_path, "updatelog")
        if not os.path.exists(log_path):
            with open(log_path, 'w') as newlog:
                log_dict = {"log": []}
                newlog.write(str(log_dict))
        return log_path

    def clearauditlog(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def clearsystemlog(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def collectblackbox(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setmediainstance(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getmediainstance(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getnetworklink(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setnetworklink(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setpowerbudget(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getpowerbudget(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getpreserveconfig(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def preserveconfig(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getpsupeak(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setpsupeak(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setthreshold(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def geteventlogpolicy(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def seteventlogpolicy(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getkvm(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setkvm(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getpowerconsumption(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getsystemlog(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getthreshold(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setthreshold(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setvirtualmedia(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def getvirtualmedia(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setsmtp(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

    def setbmclogsettings(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M8 model does not support this feature.'])
        return result

def filePath(flagtype, args):
    import time
    def ftime(ff="%Y%m%d%H%M%S"):
        try:
            localtime = time.localtime()
            f_localtime = time.strftime(ff, localtime)
            return f_localtime
        except:
            return ""

    checkparam_res = ResultBean()
    local_time = ftime()
    file_name_init = str(args.host) + "_" + flagtype + "_" + str(local_time) + ".json"
    if args.fileurl == ".":
        file_name = file_name_init
        file_path = os.path.abspath(".")
    elif args.fileurl == "..":
        file_name = file_name_init
        file_path = os.path.abspath("..")
    elif re.search("^[C-Zc-z]\:$", args.fileurl, re.I):
        file_name = file_name_init
        file_path = os.path.abspath(args.fileurl + "\\")
    else:
        file_name = os.path.basename(args.fileurl)
        file_path = os.path.dirname(args.fileurl)

        if file_name == "":
            file_name = file_name_init
        if file_path == "":
            file_path = os.path.abspath(".")

    args.fileurl = os.path.join(file_path, file_name)

    if not os.path.exists(file_path):
        try:
            os.makedirs(file_path)
        except:
            checkparam_res.State("Failure")
            checkparam_res.Message(["cannot build path."])
            return checkparam_res
    else:
        filename_0 = os.path.splitext(file_name)[0]
        filename_1 = os.path.splitext(file_name)[1]
        if os.path.exists(args.fileurl):
            name_id = 1
            name_new = filename_0 + "(1)" + filename_1
            file_new = os.path.join(file_path, name_new)
            while os.path.exists(file_new):
                name_id = name_id + 1
                name_new = filename_0 + "(" + str(name_id) + ")" + filename_1
                file_new = os.path.join(file_path, name_new)
            args.fileurl = file_new
    checkparam_res.State("Success")
    checkparam_res.Message('')
    return checkparam_res


def getHpmInfo(hpmurl):
    hpmdict = {}
    file_version = ""
    # 2023年3月14日 无感知升级me microcode以及GAI版本
    seamless_version = ""
    try:
        with open(hpmurl, "rb") as file:
            # header长度为104
            header = 104
            component_index = 1
            version_index = 3
            version_len = 6
            des_index = 9
            des_len = 21
            len_index = 30
            len_len = 4
            file_read = file.read()
            #[113:124]
            file_des = None
            for j in range(des_len):
                if file_read[header + des_index + j] == 0:
                    file_des = str(file_read[header + des_index:header + des_index + j], encoding="utf-8")
                    break

            if not file_des:
                return False, "Invalid image file."

            if file_des == "BOOT":
                file_header_len = file_read[header + len_index + 3] * 256 * 256 * 256 + file_read[
                    header + len_index + 2] * 256 * 256 + file_read[header + len_index + 1] * 256 + file_read[
                                      header + len_index]
                header = header + len_index + len_len + file_header_len
                for k in range(des_len):
                    if file_read[header + des_index + k] == 0:
                        file_des = str(file_read[header + des_index:header + des_index + k], encoding="utf-8")
                        break
            for i in range(version_len):
                file_version = file_version + str(file_read[header + version_index + i]) + "."
            if file_version.endswith(".0.0.0."):
                file_version = file_version[:-7]
            elif file_version.endswith(".0.0."):
                file_version = file_version[:-5]
            elif file_version.endswith(".0."):
                file_version = file_version[:-3]
            elif file_version.endswith("."):
                file_version = file_version[:-1]
            for j in range(48):
                if file_read[52 + j] == 0:
                    break
                seamless_version = seamless_version + chr(file_read[52 + j])
            boardidlist = []
            for j in range(64):
                if file_read[36 + j] == 255:
                    break
                boardidlist.append(file_read[36 + j])
    except Exception as e:
        return False, "Cannot parsing image file: " + str(e)

    # 版本
    file_versions = file_version.split(".")
    if len(file_versions) == 3:
        file_version0 = file_versions[0]
        file_version1 = file_versions[1]
        file_version2 = file_versions[2]
        if len(file_version1) == 1:
            file_version1 = "0" + file_version1
        if len(file_version2) == 1:
            file_version2 = "0" + file_version2
        file_version = file_version0 + "." + file_version1 + "." + file_version2


    hpmdict["des"] = str(file_des).replace('"', '').upper()
    hpmdict["boardid"] = boardidlist
    hpmdict["version"] = file_version
    hpmdict["seamless_version"] = seamless_version
    return True, hpmdict


def wirte_log(log_path, stage="", state="", note=""):
    def ftime(ff="%Y-%m-%d %H:%M:%S "):
        try:
            import time
            localtime = time.localtime()
            f_localtime = time.strftime(ff, localtime)
            return f_localtime
        except BaseException:
            return ""
    try:
        log_list = []
        with open(log_path, 'r') as logfile_last:
            log_cur = logfile_last.read()
            if log_cur != "":
                log_cur_dict = json.loads(str(log_cur).replace("'", '"'))
                log_list = log_cur_dict.get("log")

        with open(log_path, 'w') as logfile:
            # {
            #     "Time":"2018-11-20T10:20:12+08:00",
            #     "Stage":"Upload File",
            #     "State":"Invalid URI",
            #     "Note":"Not support the protocol 'CIFS'."
            #  }
            # 升级阶段：上传文件(Upload File)、文件校验(File Verify)、应用（刷写目标FLASH）(Apply)、生效(Activate)。
            # 错误状态：网络不通(Network Ping NOK)、无效URI(Invalid URI)、连接失败(Connect Failed)、文件不存在(File Not Exist)、空间不足(Insufficient Space)、格式错误(Format Error)、非法镜像(Illegal Image)、机型不支持(Unsupported Machine)、镜像与升级目标部件不匹配(Image and Target Component Mismatch)、BMC重启失败(BMC Reboot Failed)、版本校验失败(Version Verify Failed)、FLASH空间不足(Insufficient Flash)、FLASH写保护(FLASH Write Protection)、数据校验失败(Data Verify Failed)。
            # 正常进展：开始（Start）、进行中（In Progress）、完成（Finish）、成功（Success）、网络能ping通（Network Ping OK）、BMC重启成功（BMC Reboot Success）、升级完删除缓存的镜像成功(Delete Image Success)、升级重试第N次(Upgrade Retry N Times)、刷到暂存FLASH成功(Write to Temporary FLASH Success)、版本校验成功(Version Verify OK)、同步刷新另一片镜像成功(Sync Flash The Other Image Success)……。
            log_time = ftime("%Y-%m-%dT%H:%M:%S")
            import time
            tz = time.timezone
            if tz < 0:
                we = "+"
                tz = abs(tz)
            else:
                we = "-"
            hh = tz // 3600
            if hh < 10:
                hh = "0" + str(hh)
            else:
                hh = str(hh)
            mm = tz % 3600
            if mm < 10:
                mm = "0" + str(mm)
            else:
                mm = str(mm)
            tz_format = we + hh + ":" + mm
            log_time_format = log_time + tz_format

            log = {}
            log["Time"] = log_time_format
            log["Stage"] = stage
            log["State"] = state
            log["Note"] = str(note)
            log_list.append(log)
            log_dict = {"log": log_list}
            logfile.write(
                json.dumps(
                    log_dict,
                    default=lambda o: o.__dict__,
                    sort_keys=True,
                    indent=4,
                    ensure_ascii=False))
        return True
    except Exception as e:
        return (str(e))


class storageFuncs():
    def getraidtype(self, value):
        return value[0]

    def getDeviceID(self, value):
        return utoolUtil.getDeviceName(value)

    # VIRTUAL
    def getRaidLevel(self, var):
        if var:
            if "raid" in var.lower():
                return var.lower().replace("raid", "")

    def kb2gb(self, value):
        try:
            return int(value) // 1024 // 1024
        except:
            return value

    def getPds(self, var):
        if var:
            dlist = []
            for v in var:
                hddurl = v.get("@odata.id")
                dlist.append(hddurl.split("Disk_")[1])
            return ",".join(dlist)
        return var

    #openbmc
    def getid(self, var):
        return var.split("/")[-1]

    def b2gb(self, value):
        try:
            return int(value) // 1024 // 1024 //1024
        except:
            return value

    #pmc Disk_0
    def getpid(self, value):
        if value:
            return value.split("/Drives/")[1]
        return ""

    def getPdsOB(self, var):
        if var:
            return ",".join(var)
        return var
    def getcap(self, var):
        if var:
            if "GB" in var:
                return var.replace("GB", "")
        return var