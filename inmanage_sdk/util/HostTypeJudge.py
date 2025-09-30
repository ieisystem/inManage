# -*- coding:utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from inmanage_sdk.command import IpmiFunc
import sys
import os
import re
import platform
from requests.auth import HTTPBasicAuth
from inmanage_sdk.util import RequestClient, configUtil, RedfishTemplate

sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)),
        "command"))


ERR_dict = {
    'ERR_CODE_CMN_FAIL': 'data acquisition exception',
    'ERR_CODE_PARAM_NULL': 'parameter is null',
    'ERR_CODE_INPUT_ERROR': 'parameter error',
    'ERR_CODE_INTF_FAIL': 'create link exception',
    'ERR_CODE_INTERNAL_ERROR': 'internal error',
    'ERR_CODE_ALLOC_MEM': 'allocated memory exception',
    'ERR_CODE_NETWORK_CONNECT_FAIL': 'network connection failed',
    'ERR_CODE_AUTH_NAME_OR_PWD_ERROR': 'incorrect user name or password',
    'ERR_CODE_USER_NOT_EXIST': 'user not exist'
}

class HostTypeClient():

    def __init__(self):
        self.productName = ""
        self.firmwareVersion = ""

    # 从命令行参数利用IPMI fru命令验证远程主机的机型
    def getProductNameByIPMI(self, args):
        host, username, passcode, port = self.getParam(args)
        if (host is None) or (username is None) or (passcode is None):
            # 默认M5登陆***************************
            if '-V' in args or '-h' in args or '-v' in args:
                return
            # *************************************
            result = {"State": "Failure", "Message": [
                "Parameter is missing,please check -H <HOST> -U <USERNAME> -P <PASSWORD>"]}
            return result
        else:
            res = {}
            pn, version = self.judge_by_ipmi_api(host, username, passcode, port)
            if pn == '':
                pn, version = self.judge_by_redfish_api(host, username, passcode, port)
            if pn == '':
                res['State'] = "Failure"
                res['Message'] = [version]
                return res
            configutil = configUtil.configUtil()
            hosttpye = configutil.get_platform(pn)
            if hosttpye == "":
                hosttpye = pn
            if hosttpye == "M7":
                if IpmiFunc.checkPlatform(client).get("bmc") == "01":
                    hosttpye = "M7_redfish"
            impl, platform = configutil.getRouteOption(pn, version, hosttpye)
            if 'Error' in impl:
                res['State'] = "Failure"
                res['Message'] = [impl]
            else:
                res['State'] = "Success"
                res['Message'] = {"impl": impl, "platform": platform}
            return res

    # 从命令行参数利用IPMI fru命令验证远程主机的机型
    # 返回 机型、host、username、password
    # raw 0x3c 0x42 获取型号不通用，仅在Korea定制化使用。5288返回5280
    def getHostInfoByRaw(self, args):
        sysstr = platform.system()
        if sysstr == 'Windows':
            cmd = "..\\tools\\ipmitool\\ipmitool.exe -I lanplus -H " + args.host + \
                " -U " + args.username + " -P " + args.password + " raw 0x3c 0x42 2>nul"
        elif sysstr == 'Linux' or sysstr == 'Darwin':
            cmd = "ipmitool -I lanplus -H " + args.host + " -U " + args.username + \
                " -P " + args.password + " raw 0x3c 0x42" + " 2>/dev/null"
        result = self.execCmd(cmd).strip()
        if len(result) == 0:
            userInfo = self.getUserInfo(args)
            if userInfo == "":
                return userInfo(args)
            else:
                return [userInfo]
        arr = result.split(" ")
        PN = ""
        for i in range(8):
            PN = PN + chr(int(arr[i], 16))
        #print PN
        if PN == "NF5280M5":
            if sysstr == 'Windows':
                cmdb = "..\\tools\\ipmitool\\ipmitool.exe -I lanplus -H " + args.host + " -U " + \
                    args.username + " -P " + args.password + " mc info|findstr /c:\"Firmware Revision\" 2>nul"
            elif sysstr == 'Linux' or sysstr == 'Darwin':
                cmdb = "ipmitool -I lanplus -H " + args.host + " -U " + args.username + \
                    " -P " + args.password + " mc info |grep 'Firmware Revision'" + " 2>/dev/null"
            resultb = self.execCmd(cmdb).strip()
            if "1." in resultb:
                PN = "NF5288M5"
        PNL = [PN]
        return PNL

    # 发现getHostInfo无法获取机型
    # 需要判断是
    # 1-M4不支持
    # 2-密码错误
    def getUserInfo(self, args):
        sysstr = platform.system()
        if sysstr == 'Windows':
            cmd = "..\\tools\\ipmitool\\ipmitool.exe -I lanplus -H " + args.host + \
                " -U " + args.username + " -P " + args.password + " user list" + " 2>nul"
        elif sysstr == 'Linux' or sysstr == 'Darwin':
            cmd = "ipmitool -I lanplus -H " + args.host + " -U " + args.username + \
                " -P " + args.password + " user list" + " 2>/dev/null"
        result = self.execCmd(cmd).strip()
        if len(result) == 0:
            return "PWError"
        return "M4"

    def judge_by_ipmi_api(self, host, username, passcode, port):
        pn = None
        try:
            client = RequestClient.RequestClient()
            client.setself(host, username, passcode, '', port, "lanplus")
            productName = IpmiFunc.getProductNameByIpmi(client)
            if productName is None:
                return "", "cannot get Product Name(Model)."
            elif productName in ERR_dict:
                res['State'] = "Failure"
                res['Message'] = [ERR_dict.get(productName)]
                return "", ERR_dict.get(productName)
            firmwareVersion = IpmiFunc.getFirmwareVersoinByMcinfo(client)
            if firmwareVersion is None:
                return "", "cannot get Bmc version."

        except Exception as e:
            return "", "get FRU info failed, except info: " + str(e)
        return pn, version

    def judge_by_redfish_api(self, host, username, passcode, port):
        host_type = None
        pn = None
        try:
            client = RequestClient.RequestClient()
            client.setself(host, username, passcode, '', port, "lanplus")
            res = self.getProductName(client)
            pn = ''
            if res['State'] == 'Success':
                pn = res['Message']
            else:
                return "", "cannot get Product Name(Model)."
            res = self.getBmcVersion(client)
            version = ''
            if res['State'] == 'Success':
                version = res['Message']
            else:
                return "", "cannot get Bmc version."

        except Exception as e:
            return "", "get FRU info failed, except info: " + str(e)
        return pn, version

    def getProductName(self, client):
        result = RedfishTemplate.get_for_object_single(client, "redfish/v1/Chassis/1")
        res = {}
        if result.State:
            info = result.Message
            res['State'] = "Success"
            res['Message'] = info.get('Model')
        else:
            res['State'] = "Failure"
            res['Message'] = ["cannot get Product Name(Model)."]
        return res

    def getBmcVersion(self, client):
        result = RedfishTemplate.get_for_object_single(client, "redfish/v1/Managers/1")
        res = {}
        if result.State:
            version = result.Message.get('FirmwareVersion')
            version_index = str(version).find('(')
            if version_index != -1:
                version = str(version)[:version_index].strip()
            res['State'] = "Success"
            res['Message'] = version
        else:
            res['State'] = "Failure"
            res['Message'] = ["cannot get Bmc version."]
        return res

    # 获取参数
    def getParam(self, args):
        # i = 0
        host = args.host
        username = args.username
        passcode = args.passcode
        ipmiport = 623
        return host, username, passcode, ipmiport

    # 执行cmd命令，返回命令行获得的结果
    def execCmd(self, cmd):
        r = os.popen(cmd)
        text = r.read()
        r.close()
        return text

    # 对命令行结果进行解析，返回机型信息
    # result execCmd返回的数据
    # key   获得的某行（“Product Name”）数据的值
    def getFru(self, result, key):
        # print(result)
        par1 = key + r"[\. ]+: ([\w]+)"
        fru = re.findall(par1, result)
        return fru
