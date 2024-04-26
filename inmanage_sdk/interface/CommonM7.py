# -*- coding:utf-8 -*-
import json
import sys
import time

import os
import re
import collections

from inmanage_sdk.util import RegularCheckUtil, RequestClient, fileUtil, configUtil
from inmanage_sdk.command import RestFunc, IpmiFunc, RedfishFunc
from inmanage_sdk.interface.CommonM6 import CommonM6, addPMCLogicalDisk, addMVLogicalDisk
from inmanage_sdk.interface.ResEntity import (
    ResultBean,
    SnmpBean,
    DestinationTXBean,
    HealthBean,
    ProductBean,
    CPUBean, Cpu,
    FanBean, Fan,
    MemoryBean, Memory,
    PSUBean, PSUSingleBean, NICBean, NicAllBean, NicPort, NICController

)

retry_count = 0

PCI_IDS_LIST = {
    0x1000: "LSI Logic / Symbios Logic",
    0x1001: "Kolter Electronic",
    0x1002: "Advanced Micro Devices, Inc",
    0x1003: "ULSI Systems",
    0x1004: "VLSI Technology Inc",
    0x1005: "Avance Logic Inc",
    0x1006: "Reply Group",
    0x1007: "NetFrame Systems Inc",
    0x1008: "Epson",
    0x100a: "Phoenix Technologies",
    0x100b: "National Semiconductor Corporation",
    0x100c: "Tseng Labs Inc",
    0x100d: "AST Research Inc",
    0x100e: "Weitek",
    0x1010: "Video Logic, Ltd",
    0x1011: "Digital Equipment Corporation",
    0x1012: "Micronics Computers Inc",
    0x1013: "Cirrus Logic",
    0x1014: "IBM",
    0x1015: "LSI Logic Corp of Canada",
    0x1016: "ICL Personal Systems",
    0x1017: "SPEA Software AG",
    0x1018: "Unisys Systems",
    0x1019: "Elitegroup Computer Systems",
    0x101a: "AT&T GIS (NCR)",
    0x101b: "Vitesse Semiconductor",
    0x101c: "Western Digital",
    0x101d: "Maxim Integrated Products",
    0x101e: "American Megatrends Inc",
    0x101f: "PictureTel",
    0x1020: "Hitachi Computer Products",
    0x1021: "OKI Electric Industry Co. Ltd",
    0x1022: "Advanced Micro Devices, Inc",
    0x1023: "Trident Microsystems",
    0x1024: "Zenith Data Systems",
    0x1025: "Acer Incorporated",
    0x1028: "Dell",
    0x1029: "Siemens Nixdorf IS",
    0x102a: "LSI Logic",
    0x102b: "Matrox Electronics Systems Ltd",
    0x102c: "Chips and Technologies",
    0x102d: "Wyse Technology Inc",
    0x102e: "Olivetti Advanced Technology",
    0x102f: "Toshiba America",
    0x1030: "TMC Research",
    0x1031: "Miro Computer Products AG",
    0x1032: "Compaq",
    0x1033: "NEC Corporation",
    0x1034: "Framatome Connectors USA Inc",
    0x1035: "Comp. & Comm. Research Lab",
    0x1036: "Future Domain Corp",
    0x1037: "Hitachi Micro Systems",
    0x1038: "AMP, Inc",
    0x1039: "Silicon Integrated Systems",
    0x103a: "Seiko Epson Corporation",
    0x103b: "Tatung Corp. Of America",
    0x103c: "Hewlett-Packard Company",
    0x103e: "Solliday Engineering",
    0x103f: "Synopsys/Logic Modeling Group",
    0x1040: "Accelgraphics Inc",
    0x1041: "Computrend",
    0x1042: "Micron",
    0x1043: "ASUSTeK Computer Inc",
    0x1044: "Adaptec",
    0x1045: "OPTi Inc",
    0x1046: "IPC Corporation, Ltd",
    0x1047: "Genoa Systems Corp",
    0x1048: "Elsa AG",
    0x1049: "Fountain Technologies, Inc",
    0x104a: "STMicroelectronics",
    0x104b: "BusLogic",
    0x104c: "Texas Instruments",
    0x104d: "Sony Corporation",
    0x104e: "Oak Technology, Inc",
    0x104f: "Co-time Computer Ltd",
    0x1050: "Winbond Electronics Corp",
    0x1051: "Anigma, Inc",
    0x1052: "?Young Micro Systems",
    0x1053: "Young Micro Systems",
    0x1054: "Hitachi, Ltd",
    0x1055: "Microchip Technology / SMSC",
    0x1056: "ICL",
    0x1057: "Motorola",
    0x1058: "Electronics & Telecommunications RSH",
    0x1059: "Kontron",
    0x105a: "Promise Technology, Inc",
    0x105b: "Foxconn International, Inc",
    0x105c: "Wipro Infotech Limited",
    0x105d: "Number 9 Computer Company",
    0x105e: "Vtech Computers Ltd",
    0x105f: "Infotronic America Inc",
    0x1060: "United Microelectronics",
    0x1061: "I.I.T.",
    0x1062: "Maspar Computer Corp",
    0x1063: "Ocean Office Automation",
    0x1064: "Alcatel",
    0x1065: "Texas Microsystems",
    0x1066: "PicoPower Technology",
    0x1067: "Mitsubishi Electric",
    0x1068: "Diversified Technology",
    0x1069: "Mylex Corporation",
    0x106a: "Aten Research Inc",
    0x106b: "United Microelectronics",
    0x106c: "Hynix Semiconductor",
    0x106d: "Sequent Computer Systems",
    0x106e: "DFI, Inc",
    0x106f: "City Gate Development Ltd",
    0x1070: "Daewoo Telecom Ltd",
    0x1071: "Mitac",
    0x1072: "GIT Co Ltd",
    0x1073: "Yamaha Corporation",
    0x1074: "NexGen Microsystems",
    0x1075: "Advanced Integrations Research",
    0x1076: "Chaintech Computer Co. Ltd",
    0x1077: "QLogic Corp",
    0x1078: "Cyrix Corporation",
    0x1079: "I-Bus",
    0x107a: "NetWorth",
    0x107b: "Gateway, Inc",
    0x107c: "LG Electronics",
    0x107d: "LeadTek Research Inc",
    0x107e: "Interphase Corporation",
    0x107f: "Data Technology Corporation",
    0x1080: "Contaq Microsystems",
    0x1081: "Supermac Technology",
    0x1082: "EFA Corporation of America",
    0x1083: "Forex Computer Corporation",
    0x1084: "Parador",
    0x1086: "J. Bond Computer Systems",
    0x1087: "Cache Computer",
    0x1088: "Microcomputer Systems (M) Son",
    0x1089: "Data General Corporation",
    0x108a: "SBS Technologies",
    0x108c: "Oakleigh Systems Inc",
    0x108d: "Olicom",
    0x108e: "Oracle/SUN",
    0x108f: "Systemsoft",
    0x1090: "Compro Computer Services, Inc",
    0x1091: "Intergraph Corporation",
    0x1092: "Diamond Multimedia Systems",
    0x1093: "National Instruments",
    0x1094: "First International Computers",
    0x1095: "Silicon Image, Inc",
    0x1096: "Alacron",
    0x1097: "Appian Technology",
    0x1098: "Quantum Designs (H.K.) Ltd",
    0x1099: "Samsung Electronics Co., Ltd",
    0x109a: "Packard Bell",
    0x109b: "Gemlight Computer Ltd",
    0x109c: "Megachips Corporation",
    0x109d: "Zida Technologies Ltd",
    0x109e: "Brooktree Corporation",
    0x109f: "Trigem Computer Inc",
    0x123f: "LSI Logic",
    0x11ca: "LSI Systems, Inc",
    0x11c1: "LSI Corporation",
    0x10db: "Rohm LSI Systems, Inc",
    0x10df: "Emulex Corporation",
    0x1166: "Broadcom",
    0x10de: "NVIDIA Corporation",
    0x11f8: "PMC-Sierra Inc.",
    0x1344: "Micron Technology Inc.",
    0x15b3: "Mellanox Technologies",
    0x19a2: "Emulex Corporation",
    0x1c5f: "Beijing Memblaze Technology Co. Ltd.",
    0x1fc1: "QLogic, Corp.",
    0x8086: "Intel Corporation",
    0x9005: "Adaptec",
    0x9004: "Adaptec",
    0x14e4: "Brodcom Limited",
    0x144d: "Samsung Electronics Co Ltd",
    0x1924: "Solarflare Communications",
    0xcabc: "Cambricon"
}


class CommonM7(CommonM6):

    def setservice(self, client, args):
        set_result = ResultBean()
        if args.secureport is None and args.nonsecureport is None and args.state is None and args.timeout is None:
            set_result.State("Failure")
            set_result.Message(["please input a subcommand"])
            return set_result
        if args.servicename == 'fd-media' or args.servicename == 'telnet' or args.servicename == "solssh":
            set_result.State("Not Support")
            set_result.Message([])
            return set_result
        if args.servicename == 'ssh':
            if args.nonsecureport is not None:
                set_result.State("Failure")
                set_result.Message(["ssh not support nonsecure port."])
                return set_result
        if args.state is not None and args.state == 'Disabled' and (
                args.secureport is not None or args.nonsecureport is not None):
            set_result.State("Failure")
            set_result.Message(["Settings are not supported when -S is set to Disabled."])
            return set_result
        # WEB 服务使用IPMI命令，其他使用RESTFUL接口
        if args.state is not None:
            if args.servicename == "web":
                if 'Enabled' in args.state:
                    enabled = ' 0x01'
                else:
                    enabled = ' 0x00'
            else:
                if 'Enabled' in args.state:
                    args.state = 1
                else:
                    args.state = 0
        if args.secureport is not None:
            if args.servicename == 'kvm' or args.servicename == "cdmedia" or args.servicename == "hdmedia" or args.servicename == "vnc":
                set_result.State("Failure")
                set_result.Message([str(args.servicename) + " not support setting secureport"])
                return set_result
            if args.secureport < 1 or args.secureport > 65535:
                set_result.State("Failure")
                set_result.Message(["secureport is in 1-65535."])
                return set_result
            else:
                if args.servicename == "web":
                    sp = '{:08x}'.format(args.secureport)
                    sp_hex = hexReverse(sp)

        if args.nonsecureport is not None:
            if args.servicename == 'kvm' or args.servicename == "cdmedia" or args.servicename == "hdmedia" or args.servicename == "ssh":
                set_result.State("Failure")
                set_result.Message([str(args.service) + " not support setting nonsecureport"])
                return set_result
            if args.nonsecureport < 1 or args.nonsecureport > 65535:
                set_result.State("Failure")
                set_result.Message(["nonsecureport is in 1-65535."])
                return set_result
            else:
                if args.servicename == "web":
                    nsp = '{:08x}'.format(args.nonsecureport)
                    nsp_hex = hexReverse(nsp)

        if args.timeout is not None:
            if args.servicename == 'ssh' or args.servicename == 'solssh':
                if args.timeout % 60 == 0 and args.timeout >= 60 and args.timeout <= 1800:
                    pass
                    # t = '{:08x}'.format(args.timeout)
                    # t_hex = hexReverse(t)
                else:
                    set_result.State("Failure")
                    set_result.Message(
                        ["This time is invalid, please enter a multiple of 60 and range from 60 to 1800."])
                    return set_result
            elif args.servicename == 'web':
                if args.timeout % 60 == 0 and args.timeout >= 300 and args.timeout <= 1800:
                    t = '{:08x}'.format(args.timeout)
                    t_hex = hexReverse(t)
                else:
                    set_result.State("Failure")
                    set_result.Message(
                        ["This time is invalid, please enter a multiple of 60 and range from 300 to 1800."])
                    return set_result
            elif args.servicename == 'kvm' or args.servicename == 'vnc':
                if args.timeout % 60 == 0 and args.timeout >= 300 and args.timeout <= 1800:
                    pass
                else:
                    set_result.State("Failure")
                    set_result.Message(
                        ["This time is invalid, please enter a multiple of 60 and range from 300 to 1800."])
                    return set_result
            else:
                set_result.State("Failure")
                set_result.Message(["The timeout(-T) are not support to set."])
                return set_result
        # 获取信息
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        service_name = args.service.replace('-', '').title()
        Info = None
        try:
            if args.servicename == 'web':
                # IPMI命令获取web的service信息
                Info_all = getattr(IpmiFunc, "getM5" + service_name + 'ByIpmi')(client)
                if Info_all:
                    if Info_all.get('code') == 0 and Info_all.get('data') is not None:
                        Info = Info_all.get('data')  # web当前值
                    else:
                        set_result.State("Failure")
                        set_result.Message(["failed to set service info " + Info_all.get('data', '')])
                        RestFunc.logout(client)
                        return set_result
                else:
                    set_result.State("Failure")
                    set_result.Message(["failed to set service info"])
                    RestFunc.logout(client)
                    return set_result
            else:
                # restful方式获取service信息
                rest_result = RestFunc.getServiceInfoByRest(client)
                if rest_result.get('code') == 0 and rest_result.get('data') is not None:
                    for item in rest_result.get('data'):
                        if item['service_name'].replace('-', '') == args.service:
                            Info = item
                            break
                else:
                    set_result.State("Failure")
                    set_result.Message(["failed to set service info"])
                    RestFunc.logout(client)
                    return set_result
        except Exception as e:
            set_result.State('Failure')
            set_result.Message(['this command is incompatible with current server.'])
            RestFunc.logout(client)
            return set_result
        if Info:
            if args.enabled is None:
                if args.servicename == 'web':
                    status_dict = {'Disabled': '00', 'Enabled': '01'}
                    if Info['Status'] == 'Disabled':
                        set_result.State("Failure")
                        set_result.Message(["please set status to Enabled firstly."])
                        RestFunc.logout(client)
                        return set_result
                    enabled = hex(int(status_dict[Info['Status']]))
                else:
                    if Info['state'] == 0:
                        set_result.State("Failure")
                        set_result.Message(["please set status to Enabled firstly."])
                        RestFunc.logout(client)
                        return set_result
                    args.state = 1

            if args.nonsecureport is None:
                if args.servicename == 'web':
                    if Info['NonsecurePort'] == 'N/A':
                        nsp_hex = "0xff " * 4
                    else:
                        nsp = '{:08x}'.format(Info['NonsecurePort'])
                        nsp_hex = hexReverse(nsp)
                else:
                    args.nonsecureport = Info['non_secure_port']

            if args.secureport is None:
                if args.servicename == 'web':
                    if Info['SecurePort'] == 'N/A':
                        sp_hex = "0xff " * 4
                    else:
                        sp = '{:08x}'.format(Info['SecurePort'])
                        sp_hex = hexReverse(sp)
                else:
                    args.secureport = Info['secure_port']

            if args.timeout is None:
                if args.servicename == 'web':
                    if Info['Timeout'] == 'N/A':
                        t_hex = "0xff " * 4
                    else:
                        t = '{:08x}'.format(Info['Timeout'])
                        t_hex = hexReverse(t)
                else:
                    args.timeout = Info['time_out']

            if args.servicename == 'web':
                if Info['InterfaceName'] == 'N/A':
                    interface_temp = "F" * 16
                    interface = ascii2hex(interface_temp, 17)
                else:
                    interface = ascii2hex(Info['InterfaceName'], 17)
            else:
                args.activeSession = Info['active_session']
                args.configurable = 1
                args.id = Info['id']
                args.maximumSessions = Info['maximum_sessions']
                args.serviceId = Info['service_id']
                args.serviceName = Info['service_name']
                args.singleportStatus = Info['singleport_status']

            if args.service == 'web':
                set_Info = getattr(IpmiFunc, "setM5" + service_name + 'ByIpmi')(client, enabled, interface, nsp_hex,
                                                                                sp_hex, t_hex)
            else:
                set_Info = RestFunc.setServiceInfoByRest(client, args, Info['id'])

            if set_Info:
                if set_Info.get('code') == 0:
                    set_result.State("Success")
                    set_result.Message(["set service success."])
                    RestFunc.logout(client)
                    return set_result
                else:
                    set_result.State("Failure")
                    set_result.Message(["failed to set service: " + set_Info.get('data', '')])
                    RestFunc.logout(client)
                    return set_result
            else:
                set_result.State("Failure")
                set_result.Message(["failed to set service, return None."])
                RestFunc.logout(client)
                return set_result
        else:
            set_result.State("Failure")
            set_result.Message(["failed to set service info"])
            RestFunc.logout(client)
            return set_result

    def getnic(self, client, args):
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        nicRes = ResultBean()

        # health
        overalhealth = RestFunc.getHealthSummaryByRest(client)
        if overalhealth.get('code') == 0 and overalhealth.get('data') is not None and 'lan' in overalhealth.get('data'):
            if overalhealth.get('data').get('lan') == 'na':
                health = 'Absent'
            elif overalhealth.get('data').get('lan').lower() == 'info':
                health = 'OK'
            else:
                health = overalhealth.get('data').get('lan').capitalize()
        else:
            health = None
        nicinfo = NicAllBean()
        nicinfo.OverallHealth(health)
        # get
        # res=RestFunc.getAdapterByRest(client)
        res = RestFunc.getAdapterByRest(client)
        if res == {}:
            nicRes.State("Failure")
            nicRes.Message(["cannot get information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            # port_status_dict = {0: "Not Linked", 1: "Linked", 2: "NA", "Unknown": "NA", 255: "NA"}
            nicRes.State("Success")
            PCIElist = []
            data = res.get('data')['sys_adapters']
            for ada in data:
                PCIEinfo = NICBean()
                PCIEinfo.CommonName(ada['location'])
                PCIEinfo.Location("mainboard")
                adapterinfo = NICController()
                adapterinfo.Id(ada['id'])
                adapterinfo.Location(ada.get('location', 'NA'))
                adapterinfo.PortType(ada.get('port_type', 'NA'))
                if ada['vendor'] == "":
                    adapterinfo.Manufacturer(None)
                    PCIEinfo.Manufacturer(None)
                else:
                    if "0x" in ada['vendor']:
                        maf = PCI_IDS_LIST.get(int(ada['vendor'], 16), ada['vendor'])
                        adapterinfo.Manufacturer(maf)
                        PCIEinfo.Manufacturer(maf)
                    else:
                        adapterinfo.Manufacturer(ada['vendor'])
                        PCIEinfo.Manufacturer(ada['vendor'])
                adapterinfo.Model(ada.get('model', None))
                PCIEinfo.Model(ada.get('model', None))
                # 青海湖没有该字段
                # adapterinfo.Serialnumber(ada['serial_num'])
                if 'serial_num' in ada:
                    adapterinfo.Serialnumber(ada['serial_num'])
                elif "sn" in ada:
                    adapterinfo.Serialnumber(ada['sn'])
                else:
                    adapterinfo.Serialnumber(None)
                if 'pn' in ada:
                    adapterinfo.PN(ada['pn'])
                else:
                    adapterinfo.PN(None)
                adapterinfo.FirmwareVersion(ada['fw_ver'])
                ports = ada.get('ports', [])
                adapterinfo.PortCount(len(ports))
                portlist = []
                for port in ports:
                    portBean = NicPort()
                    portBean.Id(port['id'])
                    portBean.MACAddress(port['mac_addr'])
                    # portBean.LinkStatus(port_status_dict.get(port['status'], port['status']))
                    portBean.LinkStatus(port.get('LinkStatus', "N/A"))
                    portBean.MediaType(None)
                    portlist.append(portBean.dict)
                adapterinfo.Port(portlist)
                controllerList = []
                controllerList.append(adapterinfo.dict)
                # PCIEinfo.Serialnumber(ada['serial_num'])
                if 'serial_num' in ada:
                    PCIEinfo.Serialnumber(ada['serial_num'])
                else:
                    PCIEinfo.Serialnumber(None)
                PCIEinfo.State("Enabled")
                if ada['present'] == 1 or ada['present'] == 'OK':
                    PCIEinfo.Health('OK')
                else:
                    PCIEinfo.Health('Warning')
                PCIEinfo.Controller(controllerList)
                PCIElist.append(PCIEinfo.dict)
            nicinfo.Maximum(len(data))
            nicinfo.NIC(PCIElist)
            nicRes.Message([nicinfo.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            nicRes.State("Failure")
            nicRes.Message([res.get('data')])
        else:
            nicRes.State("Failure")
            nicRes.Message(["get information error, error code " + str(res.get('code'))])

        RestFunc.logout(client)
        return nicRes

    def getgpu1(self, client, args):
        res = ResultBean()
        state = "Failure"
        gpu_device_class_type = ["DisplayController", "ProcessingAccelerator"]
        id_res = RedfishFunc.getChassisID(client)
        if id_res.get('code') == 0 and id_res.get('data') is not None:
            id_data = id_res.get('data')
            id_url = None
            for item in id_data:
                id_url = item.get("@odata.id")
                if id_url is not None:
                    break
            if id_url is not None:
                pcie_res = RedfishFunc.getPCIEDevices(client, id_url)
                if pcie_res.get('code') == 0 and pcie_res.get('data') is not None:
                    pcie_data = pcie_res.get('data')
                    gpu_list = []
                    for item in pcie_data:
                        gpu_url = item.get('@odata.id')
                        if gpu_url is not None:
                            gpu_res = RedfishFunc.getPCIEInfo(client, gpu_url)
                            if gpu_res.get('code') == 0 and gpu_res.get('data') is not None:
                                gpu_data = gpu_res.get('data')
                                if gpu_data.get("Oem", {}).get("Public", {}).get("DeviceClass", "N/A") \
                                        in gpu_device_class_type:
                                    gpu_list.append(gpu_data)
                    if len(gpu_list) > 0:
                        state = "Success"
                        message = gpu_list
                    else:
                        state = "Success"
                        message = []
                else:
                    message = "Cannot get pcie info."
            else:
                message = "No chassis id."
        else:
            message = "Cannot get chassis id."
        res.State(state)
        res.Message([message])
        return res

    def getgpu(self, client, args):
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        res = ResultBean()

        gpures = RestFunc.getgpu(client)
        if gpures.get('code') == 0:
            res.State('Success')
            gpurawinfo = gpures.get('data')
            res.Message([gpurawinfo])
        else:
            res.State('Failure')
            res.Message(['get gpu information failed.' + str(gpures.get('date'))])
        # logout
        RestFunc.logout(client)
        return res

    def setpowerbudget(self, client, args):
        import collections

        def getSuspend(start, end, week_str):
            if start is not None and end is not None and week_str is not None:
                if start > 24 or start < 0:
                    value = 'Invalid start, start range from 0-24'
                    return -1, value
                if end > 24 or end < 0:
                    value = 'Invalid end, end range from 0-24'
                    return -1, value
                if start > end:
                    value = 'start time should not be greater than end time!'
                    return -1, value
                weeks = []
                if type(week_str) is str:
                    weeks = str(week_str).split(',')
                elif type(week_str) is list:
                    weeks = week_str
                else:
                    value = 'Invalid week!'
                    return -1, value
                week_dict = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thur': 4, 'Fri': 5, 'Sat': 6, 'Sun': 7}
                list_week = []
                for week in weeks:
                    if week not in week_dict.keys():
                        value = "Invalid week! The input parameters are 'Mon, Tue, Wed, Thur, Fri, Sat, Sun', separated by commas,such as Mon,Wed,Fri"
                        return -1, value
                    list_week.append(week_dict[week])
                list_bin = []
                for i in range(1, 8):
                    if i in list_week:
                        list_bin.append('1')
                    else:
                        list_bin.append('0')
                str_bin = ''.join(list_bin[::-1])
                int_week = int(str_bin, 2)
                item_json = collections.OrderedDict()
                item_json["startTime"] = start * 10
                item_json["endTime"] = end * 10
                item_json["recurrence"] = int_week
                return 0, item_json
            else:
                return 1, None

        res = ResultBean()
        try:
            headers = RestFunc.login_M6(client)
            if headers == {}:
                login_res = ResultBean()
                login_res.State("Failure")
                login_res.Message(["login error, please check username/password/host/port"])
                return login_res
            client.setHearder(headers)
            if args.range is False:
                if args.action == "delete" and args.id is None:
                    res.State("Failure")
                    res.Message(['when action is delete, id cannot be empty!'])
                    RestFunc.logout(client)
                    return res
                if args.action == "add" and (
                        args.id is None or args.watts is None or args.domain is None or args.except_action is None):
                    res.State("Failure")
                    res.Message(['when action is add, id, watts, except_action and domain cannot be empty!'])
                    RestFunc.logout(client)
                    return res
                # action为open或者close时，不输入id则设置功耗策略总开关
                if (args.action == "open" or args.action == "close") and args.id is None:
                    data_all = {"action": 1, "BLADE_NUM": 1}
                    result = RestFunc.setAllPolicy(client, data_all)
                    if result.get('code') == 0:
                        res.State("Success")
                        res.Message(['set power budget controller successfully.'])
                    else:
                        res.State("Failure")
                        res.Message(['set power budget controller failed.'])
                    RestFunc.logout(client)
                    return res

                result = RestFunc.getPowerBudget(client)
                if result.get('code') == 0:
                    get_result = result.get('data')
                else:
                    res.State('Failure')
                    res.Message([result.get('data')])
                    RestFunc.logout(client)
                    return res

                if args.action == "add":
                    for item in get_result:
                        if int(args.id) == int(item.get('PolicyID')):
                            res.State('Failure')
                            res.Message(['policy id ' + str(args.id) + ' already exists'])
                            RestFunc.logout(client)
                            return res
                    domain_dict = {
                        "system": 0,
                        "cpu": 1
                    }
                    data_range = {"BLADE_NUM": 1, "DOMAIN_ID": domain_dict.get(args.domain)}
                    result_range = RestFunc.getPowerBudgetRange(client, data_range)
                    if result_range.get('code') == 0:
                        range_data = result_range.get('data')
                        if args.watts > range_data['MaxPower'] or args.watts < range_data['MinPower']:
                            res.State('Failure')
                            res.Message(['Invalid watts, ' + str(args.domain) + ' watts range from ' + str(
                                range_data['MinPower']) + ' to ' + str(range_data['MaxPower'])])
                            RestFunc.logout(client)
                            return res
                    else:
                        res.State('Failure')
                        res.Message([result_range.get('data')])
                        RestFunc.logout(client)
                        return res
                    suspend_list = []
                    status, values = getSuspend(args.start1, args.end1, args.week1)
                    if status < 0:
                        res.State('Failure')
                        res.Message([values])
                        RestFunc.logout(client)
                        return res
                    elif status == 0:
                        suspend_list.append(values)
                    status, values = getSuspend(args.start2, args.end2, args.week2)
                    if status < 0:
                        res.State('Failure')
                        res.Message([values])
                        RestFunc.logout(client)
                        return res
                    elif status == 0:
                        suspend_list.append(values)
                    status, values = getSuspend(args.start3, args.end3, args.week3)
                    if status < 0:
                        res.State('Failure')
                        res.Message([values])
                        RestFunc.logout(client)
                        return res
                    elif status == 0:
                        suspend_list.append(values)
                    status, values = getSuspend(args.start4, args.end4, args.week4)
                    if status < 0:
                        res.State('Failure')
                        res.Message([values])
                        RestFunc.logout(client)
                        return res
                    elif status == 0:
                        suspend_list.append(values)
                    status, values = getSuspend(args.start5, args.end5, args.week5)
                    if status < 0:
                        res.State('Failure')
                        res.Message([values])
                        RestFunc.logout(client)
                        return res
                    elif status == 0:
                        suspend_list.append(values)
                    data = {"POLICY_ID": args.id,
                            "DOMAIN_ID": domain_dict.get(args.domain),
                            "BLADE_NUM": 1,
                            "TARGET_LIMIT": args.watts,
                            "EXCEPT_ACTION": args.except_action,
                            "suspend": suspend_list}
                    result = RestFunc.addPowerBudget(client, data)
                    if result.get('code') == 0:
                        res.State("Success")
                        res.Message(["set power budget successfully."])
                    else:
                        res.State('Failure')
                        res.Message([result.get('data')])
                else:
                    action_dict = {"close": 0, "open": 1, "delete": 2}
                    data = {}
                    open_list = []  # 已开启的策略ID
                    for item in get_result:
                        if "CurrentStatus" in item and item['CurrentStatus'] == 1:
                            open_list.append(item['PolicyID'])
                        if int(args.id) == int(item.get('PolicyID')):
                            data = {"action": action_dict.get(args.action),
                                    "POLICY_ID": args.id,
                                    "DOMAIN_ID": item.get('DomainID'),
                                    "BLADE_NUM": item.get("BladeNum")}
                    if data == {}:
                        res.State('Failure')
                        res.Message(['No policy id ' + str(args.id)])
                        RestFunc.logout(client)
                        return res
                    if args.action == "delete":
                        result = RestFunc.setPowerBudget(client, data)
                        if result.get('code') == 0:
                            res.State("Success")
                            res.Message(["set power budget successfully."])
                        else:
                            res.State('Failure')
                            res.Message([result.get('data')])
                    elif args.action == "open":
                        if args.id in open_list:
                            res.State("Success")
                            res.Message([str(args.id) + " policy already open. No setting required."])
                            RestFunc.logout(client)
                            return res
                        data_all = {"action": 1, "BLADE_NUM": data['BLADE_NUM']}
                        result = RestFunc.setAllPolicy(client, data_all)
                        if result.get('code') == 0:
                            result_open = RestFunc.setPowerBudget(client, data)
                            if result_open.get('code') == 0:
                                res.State("Success")
                                res.Message(["set power budget successfully."])
                            else:
                                res.State('Failure')
                                res.Message([result_open.get('data')])
                        else:
                            res.State('Failure')
                            res.Message([result.get('data')])
                    else:
                        if args.id not in open_list:
                            res.State("Success")
                            res.Message([str(args.id) + " policy already close. No setting required."])
                            RestFunc.logout(client)
                            return res
                        result_close = RestFunc.setPowerBudget(client, data)
                        if result_close.get('code') == 0:
                            if len(open_list) == 1:
                                data_all = {"action": 0, "BLADE_NUM": data['BLADE_NUM']}
                                result = RestFunc.setAllPolicy(client, data_all)
                            res.State("Success")
                            res.Message(["set power budget successfully."])
                        else:
                            res.State('Failure')
                            res.Message([result_close.get('data')])
            else:
                result_dict = {}
                data_system = {"BLADE_NUM": 1, "DOMAIN_ID": 0}
                result_system = RestFunc.getPowerBudgetRange(client, data_system)
                if result_system.get('code') == 0:
                    result_dict['system'] = result_system.get('data')
                    data_cpu = {"BLADE_NUM": 1, "DOMAIN_ID": 1}
                    result_cpu = RestFunc.getPowerBudgetRange(client, data_cpu)
                    if result_cpu.get('code') == 0:
                        result_dict['cpu'] = result_cpu.get('data')
                        res.State("Success")
                        res.Message([result_dict])
                    else:
                        res.State('Failure')
                        res.Message([result_cpu.get('data')])
                else:
                    res.State('Failure')
                    res.Message([result_system.get('data')])
        except Exception as e:
            res.State("Failure")
            res.Message(["get power budget info failed, " + str(e)])
        RestFunc.logout(client)
        return res

    def checkBiosCfg(self, biospath):
        res = ResultBean()
        if not os.path.exists(biospath):
            res.State("Failure")
            res.Message(["File does not exist."])
            return res
        if not os.path.isfile(biospath):
            res.State("Failure")
            res.Message(["Not a valid file."])
            return res
        with open(biospath, 'r') as f:
            biosInfo = f.read()
            try:
                biosJson = json.loads(biosInfo)
                if biosJson.get("Attributes"):
                    res.State("Failure")
                    res.Message(["The bios json file does not need an Attributes layer."])
                else:
                    res.State("Success")
                    res.Message([""])
            except Exception as e:
                res.State("Failure")
                res.Message(["File content must be in json format."])
            return res

    def getbios(self, client, args):
        #获取bios版本 放在args里面
        self._get_bios_version(client, args)

        bios_result = ResultBean()
        login_header, login_id = RedfishFunc.login(client)
        if not login_header or not login_id or 'login error' in login_id:
            bios_result.State('Failure')
            bios_result.Message(['login session service failed, please check username/password/host/port'])
            return bios_result
        args.Attribute = None
        server_result = RedfishFunc.getBiosV1ByRedfish(client, login_header)
        if server_result.get('code') == 0 and server_result.get('data'):
            server_bios = server_result.get('data')
            RedfishFunc.logout(client, login_id, login_header)

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
                            bios[attr_desc_nospace] = self._transfer_value(l1_bios_value[attr], attr_dict[attr_lower]['setter'],
                                                                   attr_desc)
                        elif attr[:-1] in l1_bios_value:
                            bios[attr_desc_nospace] = self._transfer_value(l1_bios_value[attr[:-1]][int(attr[-1])], attr_dict[attr_lower]['setter'],
                                                                   attr_desc)
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
            bios_result.Message([server_result.get('data')])
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
        #获取bios版本 放在args里面
        self._get_bios_version(client, args)

        res = ResultBean()
        attr_dict = {}
        # 读取映射文件
        mapper_result = self._get_xml_mapper(args, 'value', 'cmd')
        # args.list = False
        if mapper_result[0]:
            if 'list' in args and args.list:  # 打印信息
                help_list = []
                for key, value in mapper_result[1].items():
                    help_list.append('{:<35}: {}'.format(value['description'].replace(" ", ""), list(value['setter'].keys())))
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

        # 校验输入并转换，默认映射文件完全正确，不再和服务器键比对
        user_bios = {}  # 最终会提交到redfish接口中的配置字典
        double_check = []
        for key, value in input_value.items():
            # 校验键
            if key.lower().replace(" ","") not in attr_dict:
                res.Message(['not support setting [{}]. Please refer to [-L]'.format(key)])
                res.State('Failure')
                return res
            # 校验值并转换
            item_dict = attr_dict[key.lower().replace(" ","")]
            attr = item_dict['getter']
            attr_setter = item_dict['setter']
            attr_parent = item_dict['parent']
            #list的3种处理方式 {0:"x", 1:"y"} [x,y,...] x
            if item_dict.get('list') > 0:
                if isinstance(value, dict):
                    for k, v in value.items():  # 根据目前支持的配置项，值统一处理为str
                        user_bios[attr + str(k)] = str(attr_setter[v])
                elif isinstance(value, list):
                    for i in range(len(value)):
                        user_bios[attr + str(i)] = str(attr_setter[value[i]])
                elif isinstance(value, str):
                    if "{" in value:
                        try:
                            valueinjson = json.loads(value)
                            for k, v in valueinjson.items():  # 根据目前支持的配置项，值统一处理为str
                                user_bios[attr + str(k)] = str(attr_setter[v])
                        except Exception as e:
                            res.Message(
                                ['incorrect format for key: [{}], value: [{}]. value format is JSON.'.format(key, value)])
                            res.State('Failure')
                            return res
                    elif "[" in value:
                        valueinlist = value[1:-1].split(",")
                        for i in range(len(valueinlist)):
                            user_bios[attr + str(i)] = str(attr_setter[valueinlist[i]])

            else:
                if len(attr_setter) == 1:
                    #类型
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

                        user_bios[attr] = int(value)
                else:
                    if item_dict['match'] and value not in attr_setter:
                        res.Message(['[{}] is invalid value for bios option [{}], and valid values are [{}].'
                                    .format(value, key, ', '.join(list(attr_setter.keys())))])
                        res.State('Failure')
                        return res

                    user_bios[attr] = str(attr_setter.get(value, value))

        # 调用接口设置
        login_header, login_id = RedfishFunc.login(client)
        if not login_header or not login_id or 'login error' in login_id:
            res.Message(['login session service failed, please check username/password/host/port'])
            res.State('Failure')
            return res
        get_result = RedfishFunc.getBiosV1ByRedfish(client, login_header)
        if get_result.get('code') != 0 or not get_result.get('data'):
            res.Message([get_result.get('data')])
            res.State('Failure')
            RedfishFunc.logout(client, login_id, login_header)
            return res
        # 再次校验列表值
        if double_check:
            server_bios = get_result.get('data')
            # [attr_parent, attr, key.lower()]
            for item in double_check:
                user_bios_item_value = user_bios[item[0]][item[1]]
                if isinstance(server_bios[item[0]], list):
                    res.Message(['not support setting [{}] for now'.format(item[2])])
                    res.State('Failure')
                    RedfishFunc.logout(client, login_id, login_header)
                    return res
                elif isinstance(server_bios[item[0]], dict) and isinstance(server_bios[item[0]][item[1]], list):
                    server_bios_item_value = server_bios[item[0]][item[1]]
                    for key, value in user_bios_item_value.items():
                        try:
                            index = int(key)
                            if index < 0 or index >= len(server_bios_item_value):  # 存在只能修改无法新增配置的问题
                                res.Message(
                                    ['index out of bounds for key [{}]. Min index is 0 and max index is {}'.format(
                                        item[2], len(server_bios_item_value) - 1)])
                                res.State('Failure')
                                RedfishFunc.logout(client, login_id, login_header)
                                return res
                            server_bios_item_value[index] = value  # 根据{index: value}中的index替换从服务器中获取的bios值
                        except ValueError:
                            res.Message(
                                ['incorrect format for key: [{}], value: [{}]. key must be number.'.format(key, value)])
                            res.State('Failure')
                            RedfishFunc.logout(client, login_id, login_header)
                            return res
                    user_bios[item[0]][item[1]] = server_bios_item_value
                elif isinstance(server_bios[item[0]], dict) and isinstance(server_bios[item[0]][item[1]],
                                                                           (str, int, bool)):
                    pass
                else:
                    res.Message(['not support setting value of [{}]: [{}] for now'.format(item[0], item[1])])
                    res.State('Failure')
                    RedfishFunc.logout(client, login_id, login_header)
                    return res

        # 获取future
        future_result = RedfishFunc.getBiosFuture(client, login_header)
        # gethelp


        # 读取映射文件
        flag, bios_info = self._get_xml(args)
        if not flag:
            res.Message([bios_info])
            res.State('Failure')
            return res

        # 检查前置项
        conditionflag, conditionmessage = self.judgeCondition(user_bios, future_result.get('data'),
                                                              get_result.get('data'), bios_info)
        if not conditionflag:
            res.State('Failure')
            res.Message([conditionmessage])
            # logout
            RedfishFunc.logout(client, login_id, login_header)
            return res

        user_bios_f = self.formatBiosPatchBody(user_bios)
        set_result = RedfishFunc.setBiosV1SDByRedfish(client, user_bios_f, get_result.get('headers'), login_header)
        if set_result.get('code') == 0:
            res.Message([''])
            res.State("Success")
        else:
            res.Message([set_result.get('data')])
            res.State('Failure')
        RedfishFunc.logout(client, login_id, login_header)
        return res

    def formatBiosPatchBody(self, user_bios):
        return user_bios

    def _get_bios_version(self, client, args):
        biosversion = None
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            args.biosversion = biosversion
            return biosversion
        client.setHearder(headers)
        # get
        res = RestFunc.getFwVersion(client)
        if res.get('code') == 0 and res.get('data') is not None:
            data = res.get('data')

            for fwinfo in data:
                name_raw = fwinfo.get('dev_name')
                if name_raw != "BIOS":
                    continue
                else:
                    index_version = fwinfo.get('dev_version').find('(')
                    if index_version == -1:
                        biosversion = None if fwinfo.get('dev_version') == '' else fwinfo.get('dev_version')
                    else:
                        biosversion = None if fwinfo.get('dev_version') == '' else fwinfo.get('dev_version')[:index_version].strip()
                    break
        args.biosversion = biosversion
        RestFunc.logout(client)
        return biosversion

    def _get_xml_file(self, args):
        xml_path = os.path.join(IpmiFunc.command_path, "bios") + os.path.sep
        if args.biosversion:
            #M7 5.10.00 开始 bios里面替换为 XCradle
            b1=args.biosversion.split(".")[0]
            b2=args.biosversion.split(".")[1]
            b3=args.biosversion.split(".")[2]
            biosformat = float(b1 + "." + b2 + b3)
            if biosformat >= 5.1000:
                return xml_path + 'M7_5.10.00.xml'
        return xml_path + 'M7.xml'

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
            #xml_filepath = sys.path[0] + '/mappers/bios/M7.xml'
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
            #xml_filepath = sys.path[0] + '/mappers/bios/M7.xml'
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

    # 整理输出
    # type 1本次设置不符合 2即将生效不符合 3当前值不符合
    def formatCondition(self, conditionkey, conditionvalue, conditionvalue2, type):
        conditioninfo = ""
        if type == 1:
            conditioninfo = conditionkey + " must be " + conditionvalue + ", but the value is setted to " + conditionvalue2
        elif type == 2:
            conditioninfo = conditionkey + " must be " + conditionvalue + ", but the value will be setted to " + conditionvalue2
        elif type == 3:
            conditioninfo = conditionkey + " must be " + conditionvalue + ", but the current value is " + conditionvalue2
        return conditioninfo

    # 判断是否可以设置
    # bios_set={redfishkey,redfishvalue}
    # bios_future={redfishkey,redfishvalue}
    # bios_cur={redfishkey,redfishvalue}
    # bios_all_info={isrestkey, allinfo}
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
        errordict={}
        for bioskey, biosvalue in bios_set.items():
            conditions = bios_all_info.get(bioskey, {}).get("conditions", {})
            errorlist = []
            errorinfo = ""
            #如果和当前值相等 不需要考虑condition
            bioskeyparent = bios_all_info.get(bioskey, {}).get("parent")
            if bioskeyparent:
                if bioskeyparent == "FixedBootPriorities":
                    #如果是启动项，可能获取方式有区别
                    bioskeylistname = bioskey[0:-1]
                    bioskeylistid = bioskey[-1]
                    if bios_set.get(bioskey) == bios_cur.get(bioskeyparent, {}).get(bioskeylistname, [])[int(bioskeylistid)]:
                        continue
                else:
                    if bios_cur.get(bioskeyparent, {}).get(bioskey) == bios_set.get(bioskey):
                        continue

            for conditionkey,conditionvalue in conditions.items():
                condition_bios_info = bios_all_info.get(conditionkey)
                #condition 的 isrest 展示 key
                conditionkeyshow = condition_bios_info.get("description")
                #{bmc value: isrest value}
                conditionvaluedict = condition_bios_info.get("setter")
                conditionvalueshow = conditionvaluedict.get(conditionvalue, conditionvalue)
                conditionparent = condition_bios_info.get("parent")
                #比较当前设置值
                conditonvalue_set = None
                if bios_set.get(conditionkey):
                    conditonvalue_set = bios_set.get(conditionkey)
                elif bios_set.get(conditionparent):
                    conditonvalue_set = bios_set.get(conditionparent).get(conditionkey)
                if conditonvalue_set:
                    if conditionvalue == conditonvalue_set:
                        continue
                    else:
                        errorlist.append(self.formatCondition(conditionkeyshow, conditionvalueshow, conditionvaluedict.get(conditonvalue_set), 1))
                        continue
                #比较即将生效值
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
                            errorlist.append(self.formatCondition(conditionkeyshow, conditionvalueshow, conditionvaluedict.get(conditonvalue_future), 2))
                            continue
                #比较当前值
                conditonvalue_current = None
                if bios_cur.get(conditionkey):
                    conditonvalue_current = bios_cur.get(conditionkey)
                elif bios_cur.get(conditionparent):
                    conditonvalue_current = bios_cur.get(conditionparent).get(conditionkey)
                if conditonvalue_current:
                    if conditionvalue == conditonvalue_current:
                        continue
                    else:
                        errorlist.append(self.formatCondition(conditionkeyshow, conditionvalueshow, conditionvaluedict.get(conditonvalue_current), 3))
                        continue
            if errorlist != []:
                errorinfo = ",".join(errorlist)
                errordict[bios_all_info.get(bioskey).get("description")] = errorinfo
        if errordict == {}:
            return True, None
        else:
            return False, errordict

    def getbiosraw(self, client, args):
        bios_result = ResultBean()
        login_header, login_id = RedfishFunc.login(client)
        if not login_header or not login_id or "login error" in login_id:
            bios_result.State("Failure")
            bios_result.Message(['login session service failed, please check username/password/host/port'])
            return bios_result
        server_result = RedfishFunc.getBiosV1ByRedfish(client, login_header)
        if server_result.get('code') == 0 and server_result.get('data'):
            server_bios = server_result.get('data')
            if not args.Attribute:  # 获取全部BIOS项
                bios_result.State('Success')
                bios_result.Message([server_bios])
            else:  # 获取指定BIOS项
                bios = {}
                attr = args.Attribute.lower()
                for key, value in server_bios.items():
                    # 获取第一级BIOS项
                    if attr == key.lower():
                        bios[str(key).replace(" ", "")] = value
                        break
                    # 获取第二级BIOS项
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if attr == k.lower():
                                bios[str(key).replace(" ", "")] = {k: v}
                                break
                    elif isinstance(value, list) and value and isinstance(value[0], dict):
                        for i in value:
                            for k, v in i.items():
                                if attr == k.lower():
                                    bios.get(str(key).replace(" ", ""), []).append({k: v})
                                    break
                if bios:
                    bios_result.State('Success')
                    bios_result.Message([bios])
                else:
                    bios_result.State('Failure')
                    bios_result.Message(['Not support setting [{}] for now.'.format(args.Attribute)])
        else:
            bios_result.State("Failure")
            bios_result.Message([server_result.get('data')])
        RedfishFunc.logout(client, login_id, login_header)
        return bios_result

    def setbiosraw(self, client, args):
        bios_result = ResultBean()

        # 获取用户输入
        input_value = {}
        if args.fileurl:
            if not os.path.exists(args.fileurl) or not os.path.isfile(args.fileurl):
                bios_result.Message(['file path error.'])
                bios_result.State('Failure')
                return bios_result
            try:
                with open(args.fileurl) as f:
                    import json
                    input_value = json.loads(f.read())
            except:
                bios_result.Message(['file format error.'])
                bios_result.State('Failure')
                return bios_result
        if args.attribute:
            input_value[args.attribute.strip()] = args.value.strip()

        login_header, login_id = RedfishFunc.login(client)
        if not login_header or not login_id or "login error" in login_id:
            bios_result.Message(['login session service failed, please check username/password/host/port'])
            bios_result.State('Failure')
            return bios_result
        server_result = RedfishFunc.getBiosV1ByRedfish(client, login_header)
        if server_result.get('code') == 0 and server_result.get('data'):
            server_bios = server_result.get('data')

            # 获取配置项字典
            key_dict = {}
            for key, value in server_bios.items():
                key_dict[key.lower()] = [key, [], [type(value)]]  # ['origin_name', ['parent_key'], ['value_type']]
                if isinstance(value, dict):
                    for k, v in value.items():
                        key_info = key_dict.setdefault(k.lower(), [k, [], []])
                        key_info[1].append(key)
                        key_info[2].append(type(v))
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    for k, v in value[0].items():
                        key_info = key_dict.setdefault(k.lower(), [k, [], []])
                        key_info[1].append(key)
                        key_info[2].append(type(v))

            # 获取最终set_bios
            set_bios = {}
            for key, value in input_value.items():
                key_lower = key.lower()
                if key_lower not in key_dict:
                    bios_result.Message(['[{}] is a invalid bios option, or may not support setting yet'.format(key)])
                    bios_result.State('Failure')
                    break
                key_item = key_dict[key_lower]
                if len(key_item[1]) > 1:
                    bios_result.Message([
                        '{} all have options for [{}], please set by file with parent bios option'.format(
                            key_item[1], key)])
                    bios_result.State('Failure')
                    break
                if not isinstance(value, key_item[2][0]):
                    if args.attribute and key_item[2][0] != str:
                        bios_result.Message(['please set [{}] by file'.format(key)])
                    else:
                        bios_result.Message(['incorrect input format for [{}]'.format(key)])
                    bios_result.State('Failure')
                    break

                parser_dict = {
                    "enabled": "Enabled",
                    "disabled": "Disabled",
                    "true": True,
                    "false": False,
                    "auto": "Auto",
                    "manual": "Manual"
                }

                if key_item[2][0] in (str, int, bool):
                    parent_key_type = key_dict[key_item[1][0].lower()][2][0]
                    if parent_key_type is dict:
                        set_item = set_bios.setdefault(key_item[1][0], {})
                        set_item[key_item[0]] = parser_dict.get(value.lower(), value) if isinstance(value,
                                                                                                    str) else value
                    elif parent_key_type is list:
                        if args.attribute:
                            bios_result.Message(['please set [{}] by file'.format(key)])
                        else:
                            bios_result.Message(
                                ['please set [{}] with parent bios option [{}]'.format(key, key_item[1][0])])
                        bios_result.State('Failure')
                        break
                    else:
                        bios_result.Message(['not support setting value for [{}]'.format(key)])
                        bios_result.State('Failure')
                        break
                elif key_item[2][0] is dict:
                    is_break = False
                    for k, v in value.items():
                        k_lower = k.lower()
                        if k_lower not in key_dict:
                            bios_result.Message(
                                ['[{}] is a invalid bios option, or may not support setting yet'.format(key)])
                            bios_result.State('Failure')
                            is_break = True
                            break
                        k_item = key_dict[k_lower]
                        if key_item[0] not in k_item[1]:
                            bios_result.Message(['[{}] is not sub-option of [{}]'.format(k, key)])
                            bios_result.State('Failure')
                            is_break = True
                            break
                        v_type = dict(zip(k_item[1], k_item[2]))[key_item[0]]
                        if not isinstance(v, v_type):
                            bios_result.Message(['incorrect input format for [{}]'.format(k)])
                            bios_result.State('Failure')
                            is_break = True
                            break
                        if v_type in (str, int, bool):
                            set_item = set_bios.setdefault(key_item[0], {})
                            set_item[k_item[0]] = parser_dict.get(v.lower(), v) if isinstance(v, str) else v
                        elif v_type == list:
                            if len(v) != len(server_bios[key_item[0]][k_item[0]]):
                                bios_result.Message(['input value length not equal for [{}]'.format(k)])
                                bios_result.State('Failure')
                                is_break = True
                                break
                            else:
                                set_item = set_bios.setdefault(key_item[0], {})
                                target_list = [parser_dict.get(vv.lower(), vv) for vv in v if isinstance(vv, str)]
                                if len(target_list) == len(v):
                                    set_item[key_item[0]] = target_list
                                else:
                                    set_item[key_item[0]] = v
                        else:
                            bios_result.Message(['not support setting value for [{}]'.format(k)])
                            bios_result.State('Failure')
                            is_break = True
                            break
                    if is_break:
                        break
                elif key_item[2][0] is list:
                    if not key_item[1]:  # 对于配置文件中配置的一级配置值为list类型的不做任何校验
                        set_item = set_bios.setdefault(key_item[0], [])
                        set_item.extend(value)
                    else:
                        parent_key_type = key_dict[key_item[1][0].lower()][2][0]
                        if parent_key_type is dict:
                            if len(value) != len(server_bios[key_item[1][0]][key_item[0]]):
                                bios_result.Message(['input value length not equal for [{}]'.format(key)])
                                bios_result.State('Failure')
                                break
                            else:
                                set_item = set_bios.setdefault(key_item[1][0], {})
                                target_list = [parser_dict.get(v.lower(), v) for v in value if isinstance(v,str)]
                                if len(target_list) == len(value):
                                    set_item[key_item[0]] = target_list
                                else:
                                    set_item[key_item[0]] = value
                        else:
                            bios_result.Message(['not support setting value for [{}]'.format(key)])
                            bios_result.State('Failure')
                            break
                else:
                    bios_result.Message(['not support setting value for [{}]'.format(key)])
                    bios_result.State('Failure')
                    break
            else:
                # 调用接口设置
                user_bios_f = self.formatBiosPatchBody(set_bios)
                set_server_result = RedfishFunc.setBiosV1SDByRedfish(client, user_bios_f, server_result.get('headers'),
                                                                     login_header)
                if set_server_result.get('code') == 0:
                    bios_result.State("Success")
                    bios_result.Message([])
                else:
                    bios_result.State('Failure')
                    bios_result.Message([set_server_result.get('data')])
        else:
            bios_result.Message([server_result.get('data')])
            bios_result.State('Failure')
        RedfishFunc.logout(client, login_id, login_header)
        return bios_result

    def settrapcom(self, client, args):
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        editFlag = False
        versionFlag = False
        res = RestFunc.getSnmpInfoByRest(client)
        snmpinfo = ResultBean()
        if res == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get snmp information"])
            RestFunc.logout(client)
            return snmpinfo
        elif res.get('code') == 0 and res.get('data') is not None:
            item = res.get('data')
            SnmpTrapCfg = item.get('SnmpTrapCfg')
            default_trap_version = SnmpTrapCfg.get('TrapVersion')
            default_enent_severity = SnmpTrapCfg.get('EventLevelLimit')
            default_community = SnmpTrapCfg.get('Community', '')
            default_v3username = SnmpTrapCfg.get('UserName')
            default_engine_Id = SnmpTrapCfg.get('EngineID')
            default_auth = SnmpTrapCfg.get('AUTHProtocol')
            default_auth_pass = SnmpTrapCfg.get('AUTHPwd', '')
            default_priv = SnmpTrapCfg.get('PrivProtocol')
            default_priv_pass = SnmpTrapCfg.get('PRIVPwd', '')
            default_host_id = SnmpTrapCfg.get('HostID')
            if 'Community' not in SnmpTrapCfg.keys():
                versionFlag = True
        else:
            snmpinfo.Message([res.get('data')])
            RestFunc.logout(client)
            return snmpinfo
        version_dict = {1: "V1", 2: "V2", 3: "V3", 0: "Disable"}
        if args.version is None:
            version = str(default_trap_version)
        else:
            version = version_dict[args.version]
            editFlag = True

        if version == 'Disable':
            eventSeverity = default_enent_severity
            community = ""
            hostid = default_host_id
            v3username = ""
            authProtocol = None
            authPcode = ""
            privacy = None
            privPcode = ""
            engineId = ""
        else:
            if version == 'V3':
                if args.community is not None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['community will be ignored in v3 trap'])
                    RestFunc.logout(client)
                    return snmpinfo
                community = default_community
                if args.v3username is None:
                    v3username = default_v3username
                else:
                    v3username = args.v3username
                    editFlag = True
                if args.authProtocol is None:
                    authProtocol = default_auth
                elif args.authProtocol == 'NONE':
                    authProtocol = 'NONE'
                    editFlag = True
                else:
                    authProtocol = args.authProtocol
                    editFlag = True
                if authProtocol == "":
                    authProtocol = "NONE"
                if args.privProtocol is None:
                    privacy = default_priv
                elif args.privProtocol == 'NONE':
                    privacy = 'NONE'
                    editFlag = True
                else:
                    privacy = args.privProtocol
                    editFlag = True
                if privacy == "":
                    privacy = "NONE"
                if authProtocol == 'SHA' or authProtocol == 'MD5':
                    if args.authPassword is None:
                        if versionFlag:
                            snmpinfo.State("Failure")
                            snmpinfo.Message(
                                ['authentication password connot be empty,when authentication protocol exists'])
                            RestFunc.logout(client)
                            return snmpinfo
                        else:
                            authPcode = default_auth_pass
                    else:
                        authPcode = args.authPassword
                        editFlag = True
                        if not RegularCheckUtil.checkPass(authPcode):
                            snmpinfo.State("Failure")
                            snmpinfo.Message(['password is a string of 8 to 16 alpha-numeric characters'])
                            RestFunc.logout(client)
                            return snmpinfo
                        # authPassword = Encrypt('secret', authPassword)
                else:
                    if args.authPassword is not None:
                        snmpinfo.State("Failure")
                        snmpinfo.Message(['authentication password will be ignored with no authentication protocol'])
                        RestFunc.logout(client)
                        return snmpinfo
                    authPcode = default_auth_pass
                # authProtocol = Encrypt('secret', authProtocol)
                if privacy == 'AES' or privacy == 'DES':
                    if args.privPassword is None:
                        if versionFlag:
                            snmpinfo.State("Failure")
                            snmpinfo.Message(['privacy password connot be empty,when privacy protocol exists'])
                            RestFunc.logout(client)
                            return snmpinfo
                        else:
                            privPcode = default_priv_pass
                    else:
                        privPcode = args.privPassword
                        editFlag = True
                        if not RegularCheckUtil.checkPass(privPcode):
                            snmpinfo.State("Failure")
                            snmpinfo.Message([' password is a string of 8 to 16 alpha-numeric characters'])
                            RestFunc.logout(client)
                            return snmpinfo
                        # privPassword = Encrypt('secret', privPassword)
                else:
                    if args.privPassword is not None:
                        snmpinfo.State("Failure")
                        snmpinfo.Message(['privacy password will be ignored with no privacy protocol'])
                        RestFunc.logout(client)
                        return snmpinfo
                    privPcode = default_priv_pass

                if args.engineId is None:
                    engineId = default_engine_Id
                else:
                    engineId = args.engineId
                    editFlag = True
                    if not RegularCheckUtil.checkEngineId(engineId):
                        snmpinfo.State("Failure")
                        snmpinfo.Message(['Engine ID is a string of 10 to 48 hex characters, must even, can set NULL.'])
                        RestFunc.logout(client)
                        return snmpinfo
            elif version == 'V1' or version == 'V2C' or version == 'V2':
                if args.community is None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['community connot be empty in v1/v2c trap.'])
                    RestFunc.logout(client)
                    return snmpinfo
                else:
                    # community = Encrypt('secret', args.community)
                    community = args.community
                    editFlag = True
                if args.v3username is not None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['username will be ignored in v1/v2c trap'])
                    RestFunc.logout(client)
                    return snmpinfo
                v3username = default_v3username
                if args.authProtocol is not None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['authentication will be ignored in v1/v2c trap'])
                    RestFunc.logout(client)
                    return snmpinfo
                authProtocol = default_auth
                if args.authPassword is not None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['authentication password will be ignored in v1/v2c trap'])
                    RestFunc.logout(client)
                    return snmpinfo
                authPcode = default_auth_pass
                if args.privProtocol is not None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['aprivacy will be ignored in v1/v2c trap'])
                    RestFunc.logout(client)
                    return snmpinfo
                privacy = default_priv
                if args.privPassword is not None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['privacy password will be ignored in v1/v2c trap'])
                    RestFunc.logout(client)
                    return snmpinfo
                privPcode = default_priv_pass
                if args.engineId is not None:
                    snmpinfo.State("Failure")
                    snmpinfo.Message(['engine Id will be ignored in v1/v2c trap'])
                    RestFunc.logout(client)
                    return snmpinfo
                engineId = default_engine_Id
            evnent_severity = {
                'all': 'Info',
                'warning': 'Warning',
                'critical': 'Critical'
            }
            if args.eventSeverity is None:
                eventSeverity = default_enent_severity
            else:
                eventSeverity = evnent_severity.get(args.eventSeverity, 'Info')
                editFlag = True
            if args.hostid is None:
                hostid = default_host_id
            else:
                hostid = args.hostid
                editFlag = True

        trapinfo = {}
        SnmpTrapCfg["TrapVersion"] = version
        SnmpTrapCfg["EventLevelLimit"] = eventSeverity
        SnmpTrapCfg["Community"] = community
        SnmpTrapCfg["HostID"] = hostid
        SnmpTrapCfg["UserName"] = v3username
        SnmpTrapCfg["AUTHProtocol"] = authProtocol
        SnmpTrapCfg["AUTHPwd"] = authPcode
        SnmpTrapCfg["PrivProtocol"] = privacy
        SnmpTrapCfg["PRIVPwd"] = privPcode
        SnmpTrapCfg["EngineID"] = engineId
        SnmpTrapCfg["DeviceType"] = 255
        trapinfo["SnmpTrapCfg"] = SnmpTrapCfg

        # if not change
        if not editFlag:
            snmpinfo.State("Success")
            snmpinfo.Message(["nothing to change."])
            RestFunc.logout(client)
            return snmpinfo

        # trapinfo["CfgType"] = 0
        trapinfo["CfgType"] = "Version"
        res = RestFunc.setTrapComByRest(client, trapinfo)
        if res == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["set snmp error"])
        elif res.get('code') == 0 and res.get('data') is not None:
            snmpinfo.State("Success")
            snmpinfo.Message([])
        elif res.get('code') != 0 and res.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([res.get('data'), trapinfo])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["set snmp error, error code " + str(res.get('code'))])
        RestFunc.logout(client)
        return snmpinfo

    def gettrap(self, client, args):
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        # get
        res = RestFunc.getSnmpInfoByRest(client)
        snmpinfo = ResultBean()
        if res == {}:
            snmpinfo.State("Failure")
            snmpinfo.Message(["cannot get snmp information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            snmpinfo.State("Success")
            version_dict = {1: "V1", 2: "V2", 3: "V3", "V2": "V2"}
            severity_dict = {0: "All", 1: "WarningAndCritical", 2: "Critical", "info": "All",
                             "warning": "WarningAndCritical", "critical": "Critical"}
            status_dict = {1: "Enabled", 0: "Disabled", "Enable": "Enabled", "Disable": "Disabled"}
            authentication_dict = {0: "NONE", 1: "SHA", 2: "MD5"}
            privacy_dict = {0: "NONE", 1: "DES", 2: "AES"}
            item = res.get('data')
            snmpbean = SnmpBean()
            SnmpTrapCfg = item.get('SnmpTrapCfg')
            # if SnmpTrapCfg['TrapVersion'] == 0:
            if SnmpTrapCfg['TrapVersion'] == "Disable":
                snmpbean.Enable('Disabled')
            else:
                snmpbean.Enable('Enabled')
                # 021 returns key012 022+returns value
                snmpbean.TrapVersion(version_dict.get(SnmpTrapCfg['TrapVersion'], SnmpTrapCfg['TrapVersion']))
                snmpbean.Community(SnmpTrapCfg['Community'])
                snmpbean.Severity(severity_dict.get(SnmpTrapCfg['EventLevelLimit'], SnmpTrapCfg['EventLevelLimit']))
                SnmpTrapDestCfg = item.get('SnmpTrapDestCfg')
                snmpTrapDestList = []
                for std in SnmpTrapDestCfg:
                    stdnew = DestinationTXBean()
                    stdnew.Id(std["id"] + 1)
                    stdnew.Enable(status_dict.get(std["Enabled"], std["Enabled"]))
                    if std["Destination"].strip() == "":
                        stdnew.Address(None)
                    else:
                        stdnew.Address(std["Destination"])
                    stdnew.Port(std["port"])
                    snmpTrapDestList.append(stdnew.dict)
                snmpbean.Destination(snmpTrapDestList)
                snmpbean.AUTHProtocol(authentication_dict.get(SnmpTrapCfg['AUTHProtocol'], SnmpTrapCfg['AUTHProtocol']))
                snmpbean.AUTHPwd(SnmpTrapCfg['AUTHPwd'])
                snmpbean.PRIVProtocol(privacy_dict.get(SnmpTrapCfg['PrivProtocol'], SnmpTrapCfg['PrivProtocol']))
                snmpbean.PRIVPwd(SnmpTrapCfg['PRIVPwd'])
                snmpbean.EngineID(SnmpTrapCfg['EngineID'])
                snmpbean.DeviceType(SnmpTrapCfg['DeviceType'])
                snmpbean.HostID(SnmpTrapCfg['HostID'])
                snmpbean.UserName(SnmpTrapCfg['UserName'])
            snmpinfo.Message([snmpbean.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            snmpinfo.State("Failure")
            snmpinfo.Message([res.get('data')])
        else:
            snmpinfo.State("Failure")
            snmpinfo.Message(["get snmp information error, error code " + str(res.get('code'))])

        RestFunc.logout(client)
        return snmpinfo

    def getnetworkadaptivecfg(self, client, args):
        res = ResultBean()
        res.State("Not support")
        res.Message([""])
        return res

    def setnetworkadaptivecfg(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([""])
        return res

    def getncsirange(self, client, args):
        res = ResultBean()
        res.State("Not Support")
        res.Message([""])
        return res

    def setremotesession(self, client, args):
        enable_dict = {"enable": 1, "disable": 0}
        result = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        res = RestFunc.getRemotesession(client)
        if res.get('code') == 0:
            kvm_settings = res.get('data')
            if args.clienttype is not None:
                if args.clienttype == "viewer":
                    kvm_settings["kvm_client"] = 1
                else:
                    kvm_settings["kvm_client"] = 2
            if kvm_settings["kvm_client"] == 1:
                if args.singleport is not None:
                    kvm_settings["single_port"] = enable_dict.get(args.singleport.lower())
                if args.keyboardlanguage is not None:
                    lan_list = ["AD", "DA", "NL-BE", "NL-NL", "GB", "US", "FI", "FR-BE", "FR", "DE", "DE-CH", "IT",
                                "JP", "NO", "PT", "ES", "SV", "TR_F", "TR_Q"]
                    if args.keyboardlanguage not in lan_list:
                        result.State("Failure")
                        result.Message(["Chose keyboardlanguage from: " + ",".join(lan_list)])
                    else:
                        kvm_settings["keyboard_language"] = args.keyboardlanguage
                if args.retrycount is not None:
                    kvm_settings["retry_count"] = args.retrycount
                if args.retrytimeinterval is not None:
                    kvm_settings["retry_time_interval"] = args.retrytimeinterval
                if args.offfeature is not None:
                    kvm_settings["local_monitor_off"] = enable_dict.get(args.offfeature)
                if args.autooff is not None:
                    kvm_settings["automatic_off"] = enable_dict.get(args.autooff)
            else:
                if args.nonsecure is not None:
                    kvm_settings["vnc_non_secure"] = enable_dict.get(args.nonsecure)
                if args.sshvnc is not None:
                    kvm_settings["vnc_over_ssh"] = enable_dict.get(args.sshvnc)

                if kvm_settings["vnc_non_secure"] == 0 and kvm_settings["vnc_over_ssh"] == 0 and \
                        kvm_settings["vnc_over_stunnel"] == 0:
                    result.State("Failure")
                    result.Message(["At least one VNC Connection type should be enabled."])

            if result.State == "Failure":
                RestFunc.logout(client)
                return result

            set_res = RestFunc.setRemotesession(client, kvm_settings)
            if set_res.get("code") == 0:
                result.State("Success")
                result.Message(["set remote session success"])
            else:
                result.State("Failure")
                result.Message(["set remote session failed. " + set_res.get('data')])
        else:
            result.State("Failure")
            result.Message([res.get('data')])

        RestFunc.logout(client)
        return result

    def backup(self, client, args):
        import time

        def ftime(ff="%Y%m%d%H%M%S"):
            try:
                localtime = time.localtime()
                f_localtime = time.strftime(ff, localtime)
                return f_localtime
            except:
                return ""

        checkparam_res = ResultBean()
        args.backupItem = args.item
        args.fileurl = args.bak_file
        if args.backupItem is None:
            checkparam_res.State("Failure")
            checkparam_res.Message(["the item parameter cannot be None."])
            return checkparam_res

        if args.backupItem is not None:
            if "bios" in args.backupItem and ("network" in args.backupItem or "service" in args.backupItem or
                                              "syslog" in args.backupItem or 'ncsi' in args.backupItem):
                checkparam_res.State("Failure")
                checkparam_res.Message(["BIOS configuration cannot be exported with other configurations."])
                return checkparam_res
            if "all" in args.backupItem.lower():
                items = {"network":1,"service":1,"syslog":1,"nicswitch":1,"biosconfig":0,"raidconfig":0,"thermalconfig":0}
            else:
                items = {"network":0,"service":0,"syslog":0,"nicswitch":0,"biosconfig":0,"raidconfig":0,"thermalconfig":0}
                if "syslog" in args.backupItem:
                    items["syslog"] = 1
                if "network" in args.backupItem:
                    items["network"] = 1
                if "ncsi" in args.backupItem:
                    items["nicswitch"] = 1
                if "service" in args.backupItem:
                    items["service"] = 1


        local_time = ftime()
        file_name_init = str(args.host) + "_bmcconfig_" + str(local_time) + ".bak"
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

        # check param end

        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # print(items)
        config_res = RestFunc.setBMCcfgByRestM7(client, args.fileurl, items)
        bmcres = ResultBean()
        if config_res == {}:
            bmcres.State("Failure")
            bmcres.Message(["prepare for BMC cfg error"])
        elif config_res.get('code') == 0:
            bmcres.State("Success")
            bmcres.Message([config_res.get('data')])
        elif config_res.get('code') != 0 and config_res.get('data') is not None:
            bmcres.State("Failure")
            bmcres.Message([config_res.get('data')])
        else:
            bmcres.State("Failure")
            bmcres.Message(["cannot prepare for export BMC cfg"])

        RestFunc.logout(client)
        return bmcres

    def restore(self, client, args):
        checkparam_res = ResultBean()
        args.fileurl = args.bak_file
        if not os.path.exists(args.fileurl):
            checkparam_res.State("Failure")
            checkparam_res.Message(["File not exists."])
            return checkparam_res
        if not os.path.isfile(args.fileurl):
            checkparam_res.State("Failure")
            checkparam_res.Message(["The file url is not file."])
            return checkparam_res
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.importBmcRestoreM7(client, args.fileurl)
        import_Info = ResultBean()
        if res == {}:
            import_Info.State("Failure")
            import_Info.Message(["import bmc configuration file failed."])
        elif res.get('code') == 0:
            import_Info.State('Success')
            import_Info.Message(['import bmc configuration file success.'])
        else:
            import_Info.State("Failure")
            import_Info.Message(["import bmc configuration file error, " + str(res.get('data'))])
        # logout
        # RestFunc.logout(client)
        return import_Info

    def exportbioscfg(self, client, args):
        import time

        def ftime(ff="%Y%m%d%H%M%S"):
            try:
                localtime = time.localtime()
                f_localtime = time.strftime(ff, localtime)
                return f_localtime
            except:
                return ""

        checkparam_res = ResultBean()
        items = {"network": 0, "service": 0, "syslog": 0, "nicswitch": 0, "biosconfig": 0, "raidconfig": 0, "thermalconfig": 0}

        local_time = ftime()
        file_name_init = str(args.host) + "_bios_" + str(local_time) + ".conf"
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

        # check param end

        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # print(items)
        config_res = RestFunc.setBMCcfgByRestM7(client, args.fileurl, items)
        bmcres = ResultBean()
        if config_res == {}:
            bmcres.State("Failure")
            bmcres.Message(["prepare for BIOS cfg error"])
        elif config_res.get('code') == 0:
            bmcres.State("Success")
            bmcres.Message(["Export file in " + str(args.fileurl)])
        elif config_res.get('code') != 0 and config_res.get('data') is not None:
            bmcres.State("Failure")
            bmcres.Message([config_res.get('data')])
        else:
            bmcres.State("Failure")
            bmcres.Message(["cannot prepare for export BIOS cfg"])

        RestFunc.logout(client)
        return bmcres

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
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.importBmcRestoreM7(client, args.fileurl)
        import_Info = ResultBean()
        if res == {}:
            import_Info.State("Failure")
            import_Info.Message(["import bios configuration file failed."])
        elif res.get('code') == 0:
            import_Info.State('Success')
            import_Info.Message(['import bios configuration file success.'])
        else:
            import_Info.State("Failure")
            import_Info.Message(["import bios configuration file error, " + str(res.get('data'))])
        # logout
        # RestFunc.logout(client)
        return import_Info

    def gethealth(self, client, args):
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        Health_Info = HealthBean()
        Health = RestFunc.getHealthSummaryByRest(client)
        # 状态 ok present absent normal warning critical
        Health_dict = {'ok': 0, 'present': 1, 'absent': 2, 'info': 0, 'warning': 4, 'critical': 5, 'na': 2}
        Dist = {'Ok': 'OK', 'Info': 'OK'}
        if Health.get('code') == 0 and Health.get('data') is not None:
            info = Health.get('data')
            if 'whole' in info:
                if info.get('whole') == 'na':
                    Health_Info.System('Absent')
                else:
                    Health_Info.System(Dist.get(info.get('whole').capitalize(), info.get('whole').capitalize()))
            else:
                health_list = [0]
                if 'pcie' in info and Health_dict.get(info['pcie'].lower()) is not None:
                    health_list.append(Health_dict.get(info['pcie'].lower(), 2))
                if 'cpu' in info and Health_dict.get(info['cpu'].lower()) is not None:
                    health_list.append(Health_dict.get(info['cpu'].lower(), 2))
                if 'fan' in info and Health_dict.get(info['fan'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fan'].lower(), 2))
                if 'memory' in info and Health_dict.get(info['memory'].lower()) is not None:
                    health_list.append(Health_dict.get(info['memory'].lower(), 2))
                if 'psu' in info and Health_dict.get(info['psu'].lower()) is not None:
                    health_list.append(Health_dict.get(info['psu'].lower(), 2))
                if 'disk' in info and Health_dict.get(info['disk'].lower()) is not None:
                    health_list.append(Health_dict.get(info['disk'].lower(), 2))
                if 'lan' in info and Health_dict.get(info['lan'].lower()) is not None:
                    health_list.append(Health_dict.get(info['lan'].lower(), 2))
                hel = list(Health_dict.keys())[list(Health_dict.values()).index(max(health_list))]
                Health_Info.System(Dist.get(hel.capitalize(), hel.capitalize()))

            pcie_info = ('Absent' if info.get('pcie', None) == 'na' else info.get('pcie', None)).capitalize()
            Health_Info.Pcie(Dist.get(pcie_info, pcie_info))
            cpu_info = ('Absent' if info.get('cpu', None) == 'na' else info.get('cpu', None)).capitalize()
            Health_Info.CPU(Dist.get(cpu_info, cpu_info))
            mem_info = ('Absent' if info.get('memory', None) == 'na' else info.get('memory', None)).capitalize()
            Health_Info.Memory(Dist.get(mem_info, mem_info))
            stor_info = ('Absent' if info.get('disk', None) == 'na' else info.get('disk', None)).capitalize()
            Health_Info.Storage(Dist.get(stor_info, stor_info))
            net_info = ('Absent' if info.get('lan', None) == 'na' else info.get('lan', None)).capitalize()
            Health_Info.Network(Dist.get(net_info, net_info))
            psu_info = ('Absent' if info.get('psu', None) == 'na' else info.get('psu', None)).capitalize()
            Health_Info.PSU(Dist.get(psu_info, psu_info))
            fan_info = ('Absent' if info.get('fan', None) == 'na' else info.get('fan', None)).capitalize()
            Health_Info.Fan(Dist.get(fan_info, fan_info))
            result.State('Success')
            result.Message([Health_Info.dict])
        elif Health.get('code') != 0 and Health.get('data') is not None:
            result.State("Failure")
            result.Message(["get health information error, " + Health.get('data')])
        else:
            result.State("Failure")
            result.Message(["get health information error, error code " + str(Health.get('code'))])

        # logout
        RestFunc.logout(client)
        return result

    def getproduct(self, client, args):
        '''

        :param client:
        :param args:
        :return:
        '''
        # login
        headers = RestFunc.login_M6(client)
        client.setHearder(headers)
        product_Result = ResultBean()
        product_Info = ProductBean()
        # product_Info.HostingRole('ApplicationServer')
        # ProductName:product_name(product)
        # Manufacturer:manufacturer(product)
        # SerialNumber:serial_number(product)
        # UUID:uuid(device))
        res_2 = RestFunc.getFruByRest(client)
        flag = 1
        if res_2.get('code') == 0 and res_2.get('data') is not None:
            info = res_2.get('data')
            for i in range(len(info)):
                if info[i].get('device') is not None and info[i].get('device').get('name') is not None and info[
                    i].get('device').get('name') == "MB_FRU":
                    flag = 0
                    if info[i].get('product') is not None:
                        product_Info.ProductName(info[i].get('product').get('product_name', None))
                        product_Info.Manufacturer(info[i].get('product').get('manufacturer', None))
                        product_Info.SerialNumber(info[i].get('product').get('serial_number', None))
                        DeviceOwnerID = info[i].get('board').get('serial_number', None)
                        if DeviceOwnerID is not None:
                            product_Info.DeviceOwnerID([DeviceOwnerID])
                        else:
                            product_Info.DeviceOwnerID([])

                    else:
                        product_Info.ProductName(None)
                        product_Info.Manufacturer(None)
                        product_Info.SerialNumber(None)
                        product_Info.DeviceOwnerID([])
                    if info[i].get('device').get('uuid', None) == None:
                        product_Info.SystemUUID(info[i].get('device').get('system_uuid', None))
                        product_Info.DeviceUUID(info[i].get('device').get('device_uuid', None))
                    else:
                        product_Info.SystemUUID(info[i].get('device').get('uuid', None))
                        product_Info.DeviceUUID(None)
        if flag == 1:
            product_Info.ProductName(None)
            product_Info.Manufacturer(None)
            product_Info.SerialNumber(None)
            product_Info.SystemUUID(None)
            product_Info.DeviceUUID(None)
            product_Info.DeviceOwnerID([])

        product_Info.DeviceSlotID("0")
        # get PowerState
        res_1 = RestFunc.getChassisStatusByRest(client)
        if res_1.get('code') == 0 and res_1.get('data') is not None:
            product_Info.PowerState(res_1.get('data').get('power_status', None))
        else:
            product_Info.PowerState(None)
        # TotalPowerWatts
        res_4 = RestFunc.getPsuInfoByRest(client)
        if res_4.get('code') == 0 and res_4.get('data') is not None:
            info = res_4.get('data')
            if 'present_power_reading' in info:
                product_Info.TotalPowerWatts(int(info['present_power_reading']))
            else:
                product_Info.TotalPowerWatts(None)
        else:
            product_Info.TotalPowerWatts(None)
        # Health: Health_Status
        res_3 = RestFunc.getHealthSummaryByRest(client)
        # 状态 ok present absent normal warning critical
        Health_dict = {'ok': 0, 'present': 1, 'absent': 2, 'info': 0, 'warning': 4, 'critical': 5, 'na': 2}
        Dist = {'Ok': 'OK', 'Info': 'OK'}
        if res_3.get('code') == 0 and res_3.get('data') is not None:
            info = res_3.get('data')
            if 'whole' in info:
                product_Info.Health(Dist.get(info.get('whole').capitalize(), info.get('whole').capitalize()))
            else:
                health_list = [0]
                if 'cpu' in info and Health_dict.get(info['cpu'].lower()) is not None:
                    health_list.append(Health_dict.get(info['cpu'].lower(), 2))
                if 'fan' in info and Health_dict.get(info['fan'].lower()) is not None:
                    health_list.append(Health_dict.get(info['fan'].lower(), 2))
                if 'memory' in info and Health_dict.get(info['memory'].lower()) is not None:
                    health_list.append(Health_dict.get(info['memory'].lower(), 2))
                if 'psu' in info and Health_dict.get(info['psu'].lower()) is not None:
                    health_list.append(Health_dict.get(info['psu'].lower(), 2))
                if 'disk' in info and Health_dict.get(info['disk'].lower()) is not None:
                    health_list.append(Health_dict.get(info['disk'].lower(), 2))
                if 'lan' in info and Health_dict.get(info['lan'].lower()) is not None:
                    health_list.append(Health_dict.get(info['lan'].lower(), 2))

                hel = list(Health_dict.keys())[list(Health_dict.values()).index(max(health_list))]
                product_Info.Health(Dist.get(hel.capitalize(), hel.capitalize()))
        else:
            product_Info.Health(None)
        product_Info.IndependentPowerSupply(True)
        if res_1.get('code') != 0 and res_2.get('code') != 0 and res_3.get('code') != 0 and res_4.get('code') != 0:
            product_Result.State('Failure')
            product_Result.Message(['get product information error'])
        else:
            product_Result.State('Success')
            product_Result.Message([product_Info.dict])

        # logout
        RestFunc.logout(client)
        return product_Result

    def getfan(self, client, args):
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        fan_Info = FanBean()

        # get
        res = RestFunc.getFanInfoByRest(client)
        if res == {}:
            result.State('Failure')
            result.Message(['get fan info failed'])
        elif res.get('code') == 0 and res.get('data') is not None:
            overalhealth = RestFunc.getHealthSummaryByRest(client)
            if overalhealth.get('code') == 0 and overalhealth.get('data') is not None and 'fan' in overalhealth.get(
                    'data'):
                if overalhealth.get('data').get('fan') == 'na':
                    fan_Info.OverallHealth('Absent')
                elif overalhealth.get('data').get('fan').lower() == 'info':
                    fan_Info.OverallHealth('OK')
                else:
                    fan_Info.OverallHealth(overalhealth.get('data').get('fan').capitalize())
            else:
                fan_Info.OverallHealth(None)
            fans = res.get('data', [])
            if isinstance(fans, dict):
                fans = fans.get('fans', [])
            size = len(fans)
            Num = IpmiFunc.getM6DeviceNumByIpmi(client, '0x01')
            if Num and Num.get('code') == 0:
                DevConfNum = Num.get('data')[0].get('DevNum')
                fan_Info.Maximum(DevConfNum)
            else:
                fan_Info.Maximum(size)
            list = []
            i = 0
            model_list = []
            persent_list = []
            for fan in fans:
                fan_singe = Fan()
                if 'fan_name' in fan:
                    commonname = fan.get('fan_name')
                else:
                    id1 = i // 2
                    id2 = i % 2
                    commonname = 'Fan' + str(id1) + "_" + str(id2)
                id = fan.get('id', None)
                # if id is not None and id > 0:
                #     id = id - 1
                fan_singe.Id(id)
                if fan.get('present') == 'OK':
                    # 在位
                    fan_singe.CommonName(commonname)
                    fan_singe.Location('chassis')
                    fan_singe.Model(fan.get('fan_model', None))
                    fan_singe.RatedSpeedRPM(fan.get('max_speed_rpm', None))
                    fan_singe.SpeedRPM(fan.get('speed_rpm', None))
                    fan_singe.LowerThresholdRPM(None)
                    fan_singe.DutyRatio(fan.get('speed_percent', None))
                    model_list.append(fan.get('fan_model', None))
                    persent_list.append(fan.get('speed_percent', None))
                    fan_singe.State('Enabled' if fan.get('present') == 'OK' else 'Disabled')
                    fan_singe.Health(fan.get('status', None))
                else:
                    fan_singe.CommonName(commonname)
                    fan_singe.Location('chassis')
                    fan_singe.State('Absent')

                list.append(fan_singe.dict)
                i += 1
            if len(set(model_list)) == 1:
                fan_Info.Model(model_list[0])
            else:
                fan_Info.Model(None)
            if len(set(persent_list)) == 1:
                fan_Info.FanSpeedLevelPercents(persent_list[0])
            else:
                fan_Info.FanSpeedLevelPercents(None)
            if 'control_mode' in res.get('data'):
                fan_Info.FanSpeedAdjustmentMode(
                    'Automatic' if res.get('data').get('control_mode') == 'auto' else 'Manual')
            else:
                mode = RestFunc.getM5FanModeByRest(client)
                if 'code' in mode and mode.get('code') == 0 and mode.get(
                        'data') is not None and 'control_mode' in mode.get('data'):
                    fan_Info.FanSpeedAdjustmentMode(
                        'Automatic' if mode.get('data').get('control_mode') == 'auto' else 'Manual')
                else:
                    fan_Info.FanSpeedAdjustmentMode(None)
            # 通过sensor获取Fan_Power
            sensor = IpmiFunc.getSensorByNameByIpmi(client, 'Fan_Power')
            if sensor and sensor.get('code') == 0:
                temp = sensor.get('data')[0].get('value')
                if temp is not None and temp != 'na':
                    fan_Info.FanTotalPowerWatts(float(temp))
            #     fan_Info.FanTotalPowerWatts(float(temp) if (temp is not None and temp != 'na') else None)
            # else:
            #     fan_Info.FanTotalPowerWatts(None)
            fan_Info.FanManualModeTimeoutSeconds(None)
            fan_Info.Fan(list)
            result.State('Success')
            result.Message([fan_Info.dict])
        elif res.get('code') != 0 and res.get('data') is not None:
            result.State("Failure")
            result.Message(["get fan information error, " + res.get('data')])
        else:
            result.State("Failure")
            result.Message(["get fan information error, error code " + str(res.get('code'))])

        RestFunc.logout(client)
        return result

    # 同M6 restful接口实现
    def fwupdate(self, client, args):
        if args.type == "FPGA":
            res = ResultBean()
            res.State("Not Support")
            res.Message(["Update FPGA is not support"])
            return res

        result = ResultBean()

        # getpsn
        psn = "UNKNOWN"
        res_syn = self.getfru(client, args)
        if res_syn.State == "Success":
            frulist = res_syn.Message[0].get("FRU", [])
            if frulist != []:
                psn = frulist[0].get('ProductSerial', 'UNKNOWN')
        else:
            return res_syn
        if psn is None:
            psn = "UNKNOWN"
        logtime = self.ftime("%Y%m%d%H%M%S")
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
        # session文件
        session_path = os.path.join(update_plog_path, "session")

        self.wirte_log(log_path, "Upload File", "Network Ping OK", "")
        # checkname
        p = '\.hpm$'
        file_name = os.path.basename(args.url)
        if not re.search(p, file_name, re.I):
            result.State("Failure")
            result.Message(["Please input filename with suffix .hpm."])
            self.wirte_log(log_path, "Upload File", "File Not Endwith hpm", result.Message[0])
            return result

        # 文件校验
        if not os.path.exists(args.url):
            result.State("Failure")
            result.Message(["File not exist. Please select valid hpm image file."])
            self.wirte_log(log_path, "Upload File", "File Not Exist", result.Message[0])
            return result
        if not os.path.isfile(args.url):
            result.State("Failure")
            result.Message(["Please select valid hpm image file"])
            self.wirte_log(log_path, "Upload File", "Url Is Not File", result.Message[0])
            return result
        file_des = ""
        try:
            with open(args.url, "rb") as file:
                # header长度为104
                header = 104
                des_index = 9
                des_len = 21
                len_index = 30
                len_len = 4
                file_read = file.read()
                for j in range(des_len):
                    if file_read[header + des_index + j] == 0:
                        file_des = str(file_read[header + des_index:header + des_index + j], encoding="utf-8")
                        break
                if file_des == "BOOT":
                    file_header_len = file_read[header + len_index + 3] * 256 * 256 * 256 + \
                                      file_read[header + len_index + 2] * 256 * 256 + \
                                      file_read[header + len_index + 1] * 256 + \
                                      file_read[header + len_index]
                    header = header + len_index + len_len + file_header_len
                    for k in range(des_len):
                        if file_read[header + des_index + k] == 0:
                            file_des = str(file_read[header + des_index:header + des_index + k], encoding="utf-8")
                            break
        except Exception as e:
            result.State("Failure")
            result.Message(["Cannot parsing image file: " + str(e)])
            self.wirte_log(log_path, "File Verify", "Illegal Image", result.Message[0])
            return result
            # "BMC", "BIOS", "CPLD", "PSUFW", "FRONTDISKBPCPLD", "REARDISKBPCPLD"
        if str(file_des).upper() == "PSU":
            file_des = "PSUFW"
        elif str(file_des).upper() == "APP":
            file_des = "BMC"
        elif str(file_des).upper() == "CPLD":
            file_des = "CPLD"
        elif str(file_des).upper() == "BIOS":
            file_des = "BIOS"
        elif str(file_des).upper().startswith('YZBB'):  # 前置或后置背板CPLD
            file_des = "DISKBPCPLD"
        elif str(file_des).upper() == "BIOS_PFR":
            file_des = "BIOS_PFR"
        elif str(file_des).upper() == "BMC_PFR":
            file_des = "BMC_PFR"
        elif str(file_des).upper() == "CPLD_PFR":
            file_des = "CPLD_PFR"
        else:
            result.State("Not Support")
            result.Message(["Firmware description: " + str(file_des) + " does not support"])
            return result
        if args.type is None:
            args.type = file_des
        elif args.type != file_des and str(args.type) not in file_des:
            result.State("Failure")
            result.Message(
                ["Input firmware type(" + str(args.type) + ") does not match firmware file(" + str(file_des) + ")."])
            self.wirte_log(log_path, "File Verify", "Illegal Image", result.Message[0])
            return result

        args.type = file_des
        args.log_path = log_path
        args.session_path = session_path
        if args.type == "BMC" or args.type == "BMC_PFR":
            result = self.updatebmc(client, args)
        elif args.type == "BIOS" or args.type == "BIOS_PFR":
            result = self.updatebios(client, args)
        elif args.type == "CPLD" or args.type == "DISKBPCPLD" or args.type == "CPLD_PFR":
            result = self.updatecpld1(client, args)
        elif args.type == "PSUFW":
            result = self.updatepsu1(client, args)
        else:
            result.State("Not Support")
            result.Message(["Update firmware only support bmc, bios and cpld"])
        return result

    def updatebmc(self, client, args):
        result = ResultBean()
        args.image = None
        if args.image is not None and args.type != "BMC_PFR":
            result.State("Failure")
            result.Message(["-I parameter only support PFR type."])
            return result
        if args.type == "BMC_PFR" and args.image is None:
            # PFR 固件默认升级active镜像
            args.image = "active"
        log_path = args.log_path
        session_path = args.session_path
        # 异步升级不支持 不保留配置
        if args.override == 1 and args.mode == "Manual" and args.type == "BMC":
            result.State("Failure")
            result.Message(["BMC upgrade cannot set mode to manual if override configuration."])
            self.wirte_log(log_path, "Parameter Verify", "Parameter Error", result.Message[0])
            return result
        upgrade_count = 0
        while True:
            # 判断session是否存在，存在则logout&del
            if os.path.exists(session_path):
                with open(session_path, 'r') as oldsession:
                    headers = oldsession.read()
                    headers_json = json.loads(str(headers).replace("'", '"'))
                    client.setHearder(headers_json)
                    # logout
                    RestFunc.logout(client)  # 删除session
                if os.path.exists(session_path):
                    os.remove(session_path)
            # 删除
            if result.State == "Success":
                return result
            elif result.State == "Abort":
                result.State = "Failure"
                return result
            else:
                if upgrade_count > retry_count:
                    return result
                else:
                    if upgrade_count >= 1:
                        # 重新升级 初始化result
                        self.wirte_log(log_path, "Upload File", "Upgrade Retry " + str(upgrade_count) + " Times", "")
                        result = ResultBean()
                    upgrade_count = upgrade_count + 1
            # login
            headers = {}
            logcount = 0
            while True:
                # 等6分钟
                if logcount > 18:
                    break
                else:
                    logcount = logcount + 1
                    time.sleep(20)
                # login
                headers = RestFunc.login_M6(client)
                if headers != {}:
                    # 记录session
                    with open(session_path, 'w') as new_session:
                        new_session.write(str(headers))
                    client.setHearder(headers)
                    break
                else:
                    self.wirte_log(log_path, "Upload File", "Connect Failed", "Connect number:" + str(logcount))
            # 10次无法登陆 不再重试
            if headers == {}:
                result.State("Failure")
                result.Message(["Cannot log in to BMC."])
                return result

            # 获取BMC版本
            # get old version
            fw_res = RestFunc.getFwVersion(client)
            fw_old = {}
            if fw_res == {}:
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Cannot get current firmware version.")
            elif fw_res.get('code') == 0 and fw_res.get('data') is not None:
                fwdata = fw_res.get('data')
                if args.type == "BMC":
                    for fw in fwdata:
                        if fw.get('dev_version') == '':
                            version = "-"
                        else:
                            index_version = fw.get('dev_version', "").find('(')
                            if index_version == -1:
                                version = fw.get('dev_version')
                            else:
                                version = fw.get('dev_version')[:index_version].strip()
                        if "BMC0" in fw.get("dev_name", ""):
                            fw_old["BMC0"] = version
                            if "Inactivate" in fw.get("dev_name", ""):
                                fw_old["InactivateBMC"] = "BMC0"
                            else:
                                fw_old["ActivateBMC"] = "BMC0"
                        elif "BMC1" in fw.get("dev_name", ""):
                            fw_old["BMC1"] = version
                            if "Inactivate" in fw.get("dev_name", ""):
                                fw_old["InactivateBMC"] = "BMC1"
                            else:
                                fw_old["ActivateBMC"] = "BMC1"

                    if "BMC0" not in fw_old and "BMC1" not in fw_old:
                        version_info = "Cannot get current BMC version, " + str(fwdata)
                        self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)
                else:
                    for fw in fwdata:
                        if fw.get('dev_version') == '':
                            version = "-"
                        else:
                            index_version = fw.get('dev_version', "").find('(')
                            if index_version == -1:
                                version = fw.get('dev_version')
                            else:
                                version = fw.get('dev_version')[:index_version].strip()
                        if "Active" in fw.get("dev_name", ""):
                            fw_old["ActivateBMC"] = version
                        elif "Backup" in fw.get("dev_name", ""):
                            fw_old["InactivateBMC"] = version

                    if "ActivateBMC" not in fw_old and "InactivateBMC" not in fw_old:
                        version_info = "Cannot get current BMC version, " + str(fwdata)
                        self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)

            else:
                version_info = "Cannot get current firmware version, " + str(fw_res.get('data'))
                self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)

            # 调check接口，不管成功与否继续升级
            # 旧版本BMC无此接口，新版本若check失败仍然可以升级获取进度，但是不会生效
            RestFunc.securityCheckByRest(client)
            if args.type == "BMC_PFR":
                res_syn = RestFunc.syncmodePFRByRest(client, args.override, args.mode, args.type, args.image)
            else:
                preserveConfig = RestFunc.preserveBMCConfig(client, args.override)
                if preserveConfig == {}:
                    result.State("Failure")
                    result.Message(["Cannot override config"])
                    continue
                elif preserveConfig.get('code') == 0:
                    res_syn = RestFunc.syncmodeByRest(client, args.override, args.mode)
                else:
                    result.State("Failure")
                    result.Message(["set override config error, " + str(preserveConfig.get('data'))])
                    continue
            if res_syn == {}:
                result.State("Failure")
                result.Message(["cannot set syncmode"])
                self.wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                continue
            elif res_syn.get('code') == 0:
                self.wirte_log(log_path, "Upload File", "Start", "")
            else:
                result.State("Failure")
                result.Message(["set sync mode error, " + str(res_syn.get('data'))])
                self.wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                continue
            res_upload = RestFunc.uploadfirmwareByRest1(client, args.url)
            if res_upload == {}:
                result.State("Failure")
                result.Message(["cannot upload firmware update file"])
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Exceptions occurred while calling interface")
                continue
            elif res_upload.get('code') == 0:
                self.wirte_log(log_path, "Upload File", "Success", "")
            else:
                result.State("Failure")
                result.Message(["upload firmware error, " + str(res_upload.get('data'))])
                if res_upload.get('data', 0) == 1 or res_upload.get('data', 0) == 2:
                    self.wirte_log(log_path, "Upload File", "File Not Exist", str(res_upload.get('data')))
                elif res_upload.get('data', 0) == 404:
                    self.wirte_log(log_path, "Upload File", "Invalid URI", str(res_upload.get('data')))
                else:
                    self.wirte_log(log_path, "Upload File", "Connect Failed", str(res_upload.get('data')))
                continue
            # verify
            if args.type != "BMC_PFR":
                time.sleep(20)
            self.wirte_log(log_path, "File Verify", "Start", "")
            res_verify = RestFunc.getverifyresultByRest(client)
            if res_verify == {}:
                result.State("Failure")
                result.Message(["cannot verify firmware update file"])
                self.wirte_log(log_path, "File Verify", "Connect Failed", "Exceptions occurred while calling interface")
                continue
            elif res_verify.get('code') == 0:
                self.wirte_log(log_path, "File Verify", "Success", "")
            else:
                result.State("Failure")
                result.Message(["cannot verify firmware update file, " + str(res_verify.get('data'))])
                self.wirte_log(log_path, "File Verify", "Data Verify Failed", str(res_verify.get('data')))
                continue
            # apply
            task_dict = {"BMC": 0, "BIOS": 1, "PSUFW": 5, "CPLD": 2, "FRONTDISKBPCPLD": 3, "REARDISKBPCPLD": 4,
                         "BMC_PFR": 10}
            self.wirte_log(log_path, "Apply", "Start", "")
            # max error number
            error_count = 0
            # max progress number
            count = 0
            # 100num  若进度10次都是100 则主动reset
            count_100 = 0
            # 循环查看apply进度
            error_info = ""
            while True:
                if count > 60:
                    break
                if error_count > 10:
                    break
                if count_100 > 5:
                    break
                count = count + 1
                time.sleep(10)
                res_progress = RestFunc.getTaskInfoByRest(client)
                if res_progress == {}:
                    error_count = error_count + 1
                    error_info = 'Failed to call BMC interface api/maintenance/background/task_info ,response is none'
                elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                    tasks = res_progress.get('data')
                    task = None
                    for t in tasks:
                        if t["id"] == task_dict.get(args.type, -1):
                            task = t
                            break
                    # 无任务则退出
                    if task is None:
                        result.State("Failure")
                        result.Message(["No apply task found in task list."])
                        self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                        break
                    error_info = str(task)
                    if task["status"] == "COMPLETE":
                        break
                    elif task["status"] == "FAILED":
                        self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) failed.")
                        result.State("Failure")
                        result.Message(["Apply(FLASH) failed."])
                        break
                    elif task["status"] == "CANCELED":
                        self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) canceled.")
                        result.State("Failure")
                        result.Message(["Apply(FLASH) canceled."])
                        break
                    else:
                        self.wirte_log(log_path, "Apply", "In Progress", "progress:" + str(task["progress"]) + "%")
                        if str(task["progress"]) == 100:
                            count_100 = count_100 + 1
                else:
                    error_count = error_count + 1
                    error_info = str(res_progress.get('data'))

            # 判断apply是否结束
            if result.State == "Failure":
                continue

            # 获取apply进度结束
            self.wirte_log(log_path, "Apply", "Success", "")

            if args.mode == "Manual":
                # manual 需要手动重启bmc
                result.State('Success')
                result.Message(["Activate pending, host is power " + self.getServerStatus(
                    client) + " now, image save in BMC FLASH and will apply later, trigger: bmcreboot."])
                self.wirte_log(log_path, "Activate", "Write to Temporary FLASH Success", "reboot bmc to activate")

            # 判断apply是否结束
            if result.State == "Failure" or result.State == "Success":
                continue

            # 未结束需要等待重启
            # 查看bmc activate状态
            # 并且刷新另一块
            # 一般4 5分钟即可从备镜像启动成功
            # 15分钟未启动则升级失败 从备份镜像启动，启动成功需要rollback
            # 10分钟内启动成功则说明刷新成功
            self.wirte_log(log_path, "Activate", "Start", "BMC will reboot")
            time.sleep(360)

            uname = client.username
            pword = client.passcode
            # web service 是否启动
            reset_try_count = 0
            headers = {}
            while True:
                time.sleep(20)
                reset_try_count = reset_try_count + 1
                # 10分钟未启动 尝试使用 admin 登陆
                if reset_try_count == 30:
                    client.username = "admin"
                    client.passcode = "admin"
                # 使用默认用户admin尝试登陆
                if reset_try_count > 32:
                    result.State('Failure')
                    result.Message(["Cannot login BMC. Get fw version failed."])
                    self.wirte_log(log_path, "Activate", "BMC Reboot Failed", result.Message)
                    break
                try:
                    headers = RestFunc.login_M6(client)
                    if headers != {}:
                        with open(session_path, 'w') as new_session:
                            new_session.write(str(headers))
                        break
                except Exception as e:
                    # print(str(e))
                    continue

            if result.State == 'Failure':
                client.username = uname
                client.passcode = pword
                continue

            client.setHearder(headers)

            # BMC有bug 回滚的时候CPU利用率超高不准 可能出现都不是active的bug
            # 查看BMC启动的主备

            res_ver = IpmiFunc.getMcInfoByIpmi(client)
            image1_update_info = ""
            image2_update_info = ""
            if 'code' in res_ver and res_ver.get("code", 1) == 0:
                version_12 = res_ver.get("data").get("firmware_revision")
                version_3 = int(res_ver.get("data").get("aux_firmware_rev_info").split(";")[0], 16)
                version_new = version_12 + "." + str(version_3)
                if args.type == "BMC_PFR":
                    if args.image == "active":
                        if "ActivateBMC" in fw_old:
                            image1_update_info = "BMC update successfully, Version: image1 image change from " + \
                                                 fw_old.get("ActivateBMC", "-") + " to " + version_new
                        else:
                            image1_update_info = "BMC update successfully, new version: " + version_new
                    else:
                        if "InactivateBMC" in fw_old:
                            if fw_old.get("ActivateBMC", "") == "BMC1":
                                image1_update_info = "BMC update successfully, Version: image1 change from " + \
                                                     fw_old.get("InactivateBMC", "-") + " to " + version_new
                            else:
                                image1_update_info = "BMC update successfully, new version: " + version_new
                else:
                    if fw_old.get("ActivateBMC", "") == "BMC1":
                        image1_update_info = "BMC update successfully, Version: image1 change from " + fw_old.get(
                            "BMC0", "-") + " to " + version_new
                    elif fw_old.get("ActivateBMC", "") == "BMC0":
                        image2_update_info = "BMC update successfully, Version: image2 change from " + fw_old.get(
                            "BMC1", "-") + " to " + version_new
                    else:
                        image1_update_info = "BMC update successfully, new version: " + version_new

                self.wirte_log(log_path, "Activate", "Version Verify OK", image1_update_info + image2_update_info)
            else:
                result.State("Failure")
                result.Message(["Flash image " + fw_old.get("InactivateBMC", "") + " error." + res_ver.get("data", "")])
                self.wirte_log(log_path, "Activate", "Version Verify Failed", result.Message)
                continue

            if args.type == "BMC_PFR":
                result.State("Success")
                result.Message(["update bmc complete"])
                continue

            # 校验第二个镜像
            image_to_set2 = ""
            if "ActivateBMC" in fw_old:
                if fw_old["ActivateBMC"] == "BMC1":
                    image_to_set2 = "Image2"
                elif fw_old["ActivateBMC"] == "BMC0":
                    image_to_set2 = "Image1"
                self.wirte_log(log_path, "Apply", "Start", "Flash" + image_to_set2)
            else:
                self.wirte_log(log_path, "Apply", "Start", "Flash image")

            # max error number
            error_count2 = 0
            # max progress number
            count2 = 0
            # 100num  若进度10次都是100 则主动reset
            count_1002 = 0
            # 循环查看apply进度
            error_info2 = ""
            while True:
                if count2 > 120:
                    result.State("Abort")
                    result.Message([
                        "Apply cost too much time, please check if upgrade is ok or not. Last response is " + error_info2])
                    self.wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                    break
                if error_count2 > 10:
                    result.State("Abort")
                    result.Message(
                        ["Get apply progress error, please check is upgraded or not. Last response is " + error_info2])
                    self.wirte_log(log_path, "Apply", "Connect Failed", result.Message)
                    # check是否升级成功
                    break
                if count_1002 > 5:
                    result.State("Abort")
                    result.Message([
                        "Apply progress is 100% but it does not complete, check if upgrade is ok or not. Last response is " + error_info2])
                    self.wirte_log(log_path, "Apply", "In Progress", result.Message)
                    break
                count2 = count2 + 1
                time.sleep(10)
                res_progress = RestFunc.getTaskInfoByRest(client)
                if res_progress == {}:
                    error_count2 = error_count2 + 1
                    error_info2 = "Failed to call BMC interface api/maintenance/background/task_info ,response is none"
                elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                    tasks = res_progress.get('data')
                    task = None
                    for t in tasks:
                        if t["id"] == task_dict.get(args.type, -1) or "rollback" in t["des"]:
                            task = t
                            break
                    # 无任务则退出
                    if task == None:
                        # 无任务应该是刷的同一版本 无需回滚
                        self.wirte_log(log_path, "Apply", "Success", "")
                        break
                    error_info2 = str(task)
                    if task["status"] == "COMPLETE":
                        self.wirte_log(log_path, "Apply", "Success", "")
                        break
                    elif task["status"] == "FAILED":
                        self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) failed.")
                        result.State("Failure")
                        result.Message(["Apply(FLASH) failed."])
                        break
                    elif task["status"] == "CANCELED":
                        self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) canceled.")
                        result.State("Failure")
                        result.Message(["Apply(FLASH) canceled."])
                        break
                    else:
                        self.wirte_log(log_path, "Apply", "In Progress",
                                       "progress:" + str(task["progress"]) + "%")
                        if str(task["progress"]) == 100:
                            count_1002 = count_1002 + 1

                else:
                    error_count2 = error_count2 + 1
                    error_info2 = str(res_progress.get('data'))

            # 判断第二个bmc apply是否结束
            if result.State == "Failure" or result.State == "Abort":
                if image1_update_info == "":
                    image1_update_info = "BMC image1 update failed: " + result.Message[0]
                if image2_update_info == "":
                    image2_update_info = "BMC image2 update failed: " + result.Message[0]
                result = ResultBean()
                result.State("Success")
                result.Message([image1_update_info, image2_update_info])
                continue
            # 获取第二个bmc的版本
            fw_now2 = {}
            bmcfw_try_count2 = 0
            bmcfw_error_count2 = 0
            while True:
                fw_now2 = {}
                if bmcfw_try_count2 > 3:
                    result.State('Failure')
                    result.Message(["Flash BMC inactive image failed: " + str(res_fw2.get('data'))])
                    self.wirte_log(log_path, "Activate", "Version Verify Failed", result.Message)
                    break
                else:
                    bmcfw_try_count2 = bmcfw_try_count2 + 1
                    time.sleep(20)
                if bmcfw_error_count2 > 3:
                    result.State('Failure')
                    result.Message(["Get BMC fw version failed(inactiveBMC): " + str(res_fw2.get('data'))])
                    self.wirte_log(log_path, "Activate", "Version Verify Failed", result.Message)
                    break

                res_fw2 = RestFunc.getFwVersion(client)
                if res_fw2 == {}:
                    bmcfw_error_count2 = bmcfw_error_count2 + 1
                elif res_fw2.get('code') == 0 and res_fw2.get('data') is not None:
                    fwlist2 = res_fw2.get('data')
                    for fw in fwlist2:
                        if fw.get('dev_version') == '':
                            version = "0.00.00"
                        else:
                            index_version = fw.get('dev_version', "").find('(')
                            if index_version == -1:
                                version = fw.get('dev_version')
                            else:
                                version = fw.get('dev_version')[
                                          :index_version].strip()
                        if "BMC0" in fw.get("dev_name", ""):
                            fw_now2["BMC0"] = version
                            if "Inactivate" in fw.get("dev_name", "") or "Backup" in fw.get("dev_name", ""):
                                fw_now2["InactivateBMC"] = "BMC0"
                            else:
                                fw_now2["ActivateBMC"] = "BMC0"
                        elif "BMC1" in fw.get("dev_name", ""):
                            fw_now2["BMC1"] = version
                            if "Inactivate" in fw.get("dev_name", "") or "Backup" in fw.get("dev_name", ""):
                                fw_now2["InactivateBMC"] = "BMC1"
                            else:
                                fw_now2["ActivateBMC"] = "BMC1"
                        if "ActivateBMC" in fw_now2 and "InactivateBMC" in fw_now2:
                            break
                    if "BMC0" not in fw_now2 and "BMC1" not in fw_now2:
                        bmcfw_error_count2 = bmcfw_error_count2 + 1
                        continue
                    if "ActivateBMC" not in fw_now2 or "InactivateBMC" not in fw_now2:
                        bmcfw_error_count2 = bmcfw_error_count2 + 1
                        continue
                    if fw_now2["BMC0"] == fw_now2["BMC1"]:
                        break
                else:
                    bmcfw_error_count2 = bmcfw_error_count2 + 1

            if result.State == 'Failure':
                if image1_update_info == "":
                    image1_update_info = "BMC image1 update failed: " + result.Message[0]
                if image2_update_info == "":
                    image2_update_info = "BMC image2 update failed: " + result.Message[0]
                result = ResultBean()
                result.State("Success")
                result.Message([image1_update_info, image2_update_info])
                continue

            if "ActivateBMC" in fw_old:
                if fw_old["ActivateBMC"] == "BMC1":
                    image2_update_info = "BMC update successfully, Version: image2 change from " + fw_old.get("BMC1",
                                                                                                              "-") + " to " + fw_now2.get(
                        "BMC1", "-")
                    image1_update_info = "BMC update successfully, Version: image1 change from " + fw_old.get("BMC0",
                                                                                                              "-") + " to " + fw_now2.get(
                        "BMC0", "-")
                elif fw_old["ActivateBMC"] == "BMC0":
                    image1_update_info = "BMC update successfully, Version: image1 change from " + fw_old.get("BMC0",
                                                                                                              "-") + " to " + fw_now2.get(
                        "BMC0", "-")
                    image2_update_info = "BMC update successfully, Version: image2 change from " + fw_old.get("BMC1",
                                                                                                              "-") + " to " + fw_now2.get(
                        "BMC1", "-")

            self.wirte_log(log_path, "Activate", "Version Verify OK", image1_update_info + image2_update_info)

            result.State("Success")
            result.Message([image1_update_info, image2_update_info])
            continue

    def updatebios(self, client, args):
        result = ResultBean()
        log_path = args.log_path
        session_path = args.session_path
        upgrade_count = 0
        while True:
            # 判断session是否存在，存在则logout&del
            if os.path.exists(session_path):
                with open(session_path, 'r') as oldsession:
                    headers = oldsession.read()
                    headers_json = json.loads(str(headers).replace("'", '"'))
                    client.setHearder(headers_json)
                    # logout
                    RestFunc.logout(client)  # 删除session
                if os.path.exists(session_path):
                    os.remove(session_path)
            # 删除
            if result.State == "Success":
                return result
            elif result.State == "Abort":
                result.State = "Failure"
                return result
            else:
                if upgrade_count > retry_count:
                    return result
                else:
                    if upgrade_count >= 1:
                        # 重新升级 初始化result
                        self.wirte_log(log_path, "Upload File", "Upgrade Retry " + str(upgrade_count) + " Times", "")
                        result = ResultBean()
                    upgrade_count = upgrade_count + 1
            # login
            headers = {}
            logcount = 0
            while True:
                # 等6分钟
                if logcount > 18:
                    break
                else:
                    logcount = logcount + 1
                    time.sleep(20)
                # login
                headers = RestFunc.login_M6(client)
                if headers != {}:
                    # 记录session
                    with open(session_path, 'w') as new_session:
                        new_session.write(str(headers))
                    client.setHearder(headers)
                    break
                else:
                    self.wirte_log(log_path, "Upload File", "Connect Failed", "Connect number:" + str(logcount))
            # 10次无法登陆 不再重试
            if headers == {}:
                result.State("Failure")
                result.Message(["Cannot log in to BMC."])
                return result
            # get old version
            fw_res = RestFunc.getFwVersion(client)
            fw_old = {}
            if fw_res == {}:
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Cannot get current firmware version.")
            elif fw_res.get('code') == 0 and fw_res.get('data') is not None:
                fwdata = fw_res.get('data')
                for fw in fwdata:
                    if fw.get('dev_version') == '':
                        version = "-"
                    else:
                        index_version = fw.get('dev_version', "").find('(')
                        if index_version == -1:
                            version = fw.get('dev_version')
                        else:
                            version = fw.get('dev_version')[:index_version].strip()
                    if "BIOS" in fw.get("dev_name", ""):
                        fw_old["BIOS"] = version
                if "BIOS" not in fw_old:
                    version_info = "Cannot get current firmware version, " + str(fwdata)
                    self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)
            else:
                version_info = "Cannot get current firmware version, " + str(fw_res.get('data'))
                self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)

            # BIOS 升级自动重启，先关机
            if args.mode == "Auto" and self.getServerStatus(client) != "off":
                choices = {'on': 1, 'off': 0, 'cycle': 2, 'reset': 3, 'shutdown': 5}
                Power = RestFunc.setM6PowerByRest(client, choices["off"])
                if Power.get('code') == 0 and Power.get('data') is not None:
                    off_count = 0
                    while True:
                        if self.getServerStatus(client) == "off" or off_count > 5:
                            break
                        time.sleep(10)
                        off_count += 1
                    if self.getServerStatus(client) != "off":
                        result.State('Failure')
                        result.Message(['set power off complete, but get power status error.'])
                        self.wirte_log(log_path, "Auto Reset Server", "Get Power Status Error", result.Message)
                        continue
                    else:
                        self.wirte_log(log_path, "Set Power Off", "Successfully", "")
                else:
                    result.State('Failure')
                    result.Message(['set power off failed.'])
                    self.wirte_log(log_path, "Auto Reset Server", "Set Power Off Failed", result.Message)
                    continue
            # set syn mode
            res_syn = {}
            RestFunc.securityCheckByRest(client)
            if args.type == "BIOS_PFR":
                res_syn = RestFunc.syncmodePFRByRest(client, args.override, args.mode, args.type, None)
            else:
                res_syn = RestFunc.syncmodeByRest(client, args.override, None)
            if res_syn == {}:
                result.State("Failure")
                result.Message(["cannot set syncmode"])
                self.wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                continue
            elif res_syn.get('code') == 0:
                self.wirte_log(log_path, "Upload File", "Start", "")
            else:
                result.State("Failure")
                result.Message(["set sync mode error, " + str(res_syn.get('data'))])
                self.wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                continue

            # upload
            res_upload = RestFunc.uploadfirmwareByRest1(client, args.url)
            if res_upload == {}:
                result.State("Failure")
                result.Message(["cannot upload firmware update file"])
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Exceptions occurred while calling interface")
                continue
            elif res_upload.get('code') == 0:
                self.wirte_log(log_path, "Upload File", "Success", "")
            else:
                result.State("Failure")
                result.Message(["upload firmware error, " + str(res_upload.get('data'))])
                if res_upload.get('data', 0) == 1 or res_upload.get('data', 0) == 2:
                    self.wirte_log(log_path, "Upload File", "File Not Exist", str(res_upload.get('data')))
                elif res_upload.get('data', 0) == 404:
                    self.wirte_log(log_path, "Upload File", "Invalid URI", str(res_upload.get('data')))
                else:
                    self.wirte_log(log_path, "Upload File", "Connect Failed", str(res_upload.get('data')))
                continue

            # verify
            if args.type != "BIOS_PFR":
                time.sleep(20)
            self.wirte_log(log_path, "File Verify", "Start", "")
            res_verify = RestFunc.getverifyresultByRest(client)
            if res_verify == {}:
                result.State("Failure")
                result.Message(["cannot verify firmware update file"])
                self.wirte_log(log_path, "File Verify", "Connect Failed", "Exceptions occurred while calling interface")
                continue
            elif res_verify.get('code') == 0:
                self.wirte_log(log_path, "File Verify", "Success", "")
            else:
                result.State("Failure")
                result.Message(["cannot verify firmware update file, " + str(res_verify.get('data'))])
                self.wirte_log(log_path, "File Verify", "Data Verify Failed", str(res_verify.get('data')))
                continue

            # apply
            task_dict = {"BMC": 0, "BIOS": 1, "PSUFW": 5, "CPLD": 2, "FRONTDISKBPCPLD": 3, "REARDISKBPCPLD": 4,
                         "BIOS_PFR": 10}
            if self.getServerStatus(client) != "off":
                time.sleep(10)
                res_progress = RestFunc.getTaskInfoByRest(client)
                if res_progress == {}:
                    result.State("Failure")
                    result.Message(["No apply task found in task list. Call interface "
                                    "api/maintenance/background/task_info returns: " + str(res_progress)])
                    self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                    continue
                elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                    tasks = res_progress.get('data')
                    task = None
                    for t in tasks:
                        if t["id"] == task_dict.get(args.type, -1):
                            task = t
                            break
                    # 无任务则退出
                    if task is None:
                        result.State("Failure")
                        result.Message(["No apply task found in task list." + str(res_progress)])
                        self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                        continue
                    if task["status"] == "FAILED":
                        result.State("Failure")
                        result.Message(["Apply task failed." + str(res_progress)])
                        self.wirte_log(log_path, "Apply", "Data Verify Failed", result.Message)
                        continue

                    result.State('Success')
                    result.Message(["Apply(FLASH) pending, host is power on now, image save in BMC FLASH and will "
                                    "apply later, trigger: poweroff, dcpowercycle, systemreboot. (TaskId=" +
                                    str(task_dict.get(args.type, 0)) + ")"])
                    self.wirte_log(log_path, "Apply", "Finish", result.Message)
                    continue
                else:
                    result.State("Failure")
                    result.Message(["No apply task found in task list." + res_progress])
                    self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                    continue
            else:
                self.wirte_log(log_path, "Apply", "Start", "")
                # max error number
                error_count = 0
                # max progress number
                count = 0
                # 100num  若进度10次都是100 则主动reset
                count_100 = 0
                # 循环查看apply进度
                error_info = ""
                while True:
                    if count > 60:
                        break
                    if error_count > 10:
                        break
                    if count_100 > 5:
                        break
                    count = count + 1
                    time.sleep(10)
                    res_progress = RestFunc.getTaskInfoByRest(client)
                    if res_progress == {}:
                        error_count = error_count + 1
                        error_info = 'Failed to call BMC interface api/maintenance/background/task_info ,response is none'
                    elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                        tasks = res_progress.get('data')
                        task = None
                        for t in tasks:
                            if t["id"] == task_dict.get(args.type, -1):
                                task = t
                                break
                        # 无任务则退出
                        if task is None:
                            result.State("Failure")
                            result.Message(["No apply task found in task list."])
                            self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                            break
                        error_info = str(task)
                        if task["status"] == "COMPLETE":
                            break
                        elif task["status"] == "FAILED":
                            self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) failed.")
                            result.State("Failure")
                            result.Message(["Apply(FLASH) failed."])
                            break
                        elif task["status"] == "CANCELED":
                            self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) canceled.")
                            result.State("Failure")
                            result.Message(["Apply(FLASH) canceled."])
                            break
                        else:
                            self.wirte_log(log_path, "Apply", "In Progress",
                                           "progress:" + str(task["progress"]) + "%")
                            if str(task["progress"]) == 100:
                                count_100 = count_100 + 1
                    else:
                        error_count = error_count + 1
                        error_info = str(res_progress.get('data'))

                # 判断apply是否结束
                if result.State == "Failure":
                    continue

                # 获取apply进度结束
                self.wirte_log(log_path, "Apply", "Success", "")

                if args.type == "BIOS" or args.mode == "Manual":
                    result.State('Success')
                    result.Message([
                        "Activate pending, host is power off now, BIOS will activate later, trigger: power on."])
                    self.wirte_log(log_path, "Apply", "Write to Temporary FLASH Success", result.Message)

                # 判断apply是否结束
                if result.State == "Failure" or result.State == "Success":
                    continue

                # PFR BIOS刷新会重启BMC，自动重启时等待BMC重启后再执行开机命令
                self.wirte_log(log_path, "Activate", "Start", "BMC will reboot")
                time.sleep(360)

                uname = client.username
                pword = client.passcode
                # web service 是否启动
                reset_try_count = 0
                headers = {}
                while True:
                    time.sleep(20)
                    reset_try_count = reset_try_count + 1
                    # 10分钟未启动 尝试使用 admin 登陆
                    if reset_try_count == 30:
                        client.username = "admin"
                        client.passcode = "admin"
                    # 使用默认用户admin尝试登陆
                    if reset_try_count > 32:
                        result.State('Failure')
                        result.Message(["Cannot login BMC. Set power on failed, please check server manually"])
                        self.wirte_log(log_path, "Reboot", "BMC Reboot Failed", result.Message)
                        break
                    try:
                        headers = RestFunc.login_M6(client)
                        if headers != {}:
                            with open(session_path, 'w') as new_session:
                                new_session.write(str(headers))
                            break
                    except:
                        continue

                if result.State == 'Failure':
                    client.username = uname
                    client.passcode = pword
                    continue

                client.setHearder(headers)

                ctr_info = IpmiFunc.powerControlByIpmi(client, "on")
                if ctr_info:
                    if ctr_info.get('code') == 0 and ctr_info.get('data') is not None and ctr_info.get('data').get(
                            'status') is not None:
                        result.State("Success")
                        result.Message(["Set power on success"])
                        self.wirte_log(log_path, "Restart", "Set power on success", result.Message)
                    else:
                        result.State("Failure")
                        result.Message(['set power failed: ' + ctr_info.get('data', ' ')])
                        self.wirte_log(log_path, "Restart", "Set power on failed", result.Message)
                else:
                    result.State("Failure")
                    result.Message(['set power failed.please check server manually'])
                    self.wirte_log(log_path, "Restart", "Set power on failed", result.Message)

                # 判断reboot是否结束
                if result.State == "Failure" or result.State == "Success":
                    continue

    def updatecpld(self, client, args):
        args.type = None
        args.auto_flag = None
        result = self.fwupdate(client, args)
        return result

    def updatecpld1(self, client, args):
        result = ResultBean()
        if args.type == "CPLD_PFR":
            if args.auto_flag is None:
                # 默认同步升级
                args.auto_flag = 1
            if args.auto_flag == 0:
                args.mode = "Manual"
            else:
                args.mode = "Auto"
        else:
            if args.auto_flag is not None:
                result.State("Failure")
                result.Message(["auto_flag parameter only support PFR type."])
                return result
        log_path = args.log_path
        session_path = args.session_path
        upgrade_count = 0
        while True:
            # 判断session是否存在，存在则logout&del
            if os.path.exists(session_path):
                with open(session_path, 'r') as oldsession:
                    headers = oldsession.read()
                    headers_json = json.loads(str(headers).replace("'", '"'))
                    client.setHearder(headers_json)
                    # logout
                    RestFunc.logout(client)  # 删除session
                if os.path.exists(session_path):
                    os.remove(session_path)
            # 删除
            if result.State == "Success":
                return result
            elif result.State == "Abort":
                result.State = "Failure"
                return result
            else:
                if upgrade_count > retry_count:
                    return result
                else:
                    if upgrade_count >= 1:
                        # 重新升级 初始化result
                        self.wirte_log(log_path, "Upload File", "Upgrade Retry " + str(upgrade_count) + " Times", "")
                        result = ResultBean()
                    upgrade_count = upgrade_count + 1
            # login
            headers = {}
            logcount = 0
            while True:
                # 等6分钟
                if logcount > 18:
                    break
                else:
                    logcount = logcount + 1
                    time.sleep(20)
                # login
                headers = RestFunc.login_M6(client)
                if headers != {}:
                    # 记录session
                    with open(session_path, 'w') as new_session:
                        new_session.write(str(headers))
                    client.setHearder(headers)
                    break
                else:
                    # print(ftime() + "Create session failed")
                    self.wirte_log(log_path, "Upload File", "Connect Failed", "Connect number:" + str(logcount))
            # 10次无法登陆 不再重试
            if headers == {}:
                result.State("Failure")
                result.Message(["Cannot log in to BMC."])
                return result
            # get old version
            fw_res = RestFunc.getFwVersion(client)
            fw_old = {}
            if fw_res == {}:
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Cannot get current firmware version.")
            elif fw_res.get('code') == 0 and fw_res.get('data') is not None:
                fwdata = fw_res.get('data')
                for fw in fwdata:
                    if fw.get('dev_version') == '':
                        version = "-"
                    else:
                        index_version = fw.get('dev_version', "").find('(')
                        if index_version == -1:
                            version = fw.get('dev_version')
                        else:
                            version = fw.get('dev_version')[:index_version].strip()
                    if "CPLD" == fw.get("dev_name", "") or "MainBoard0CPLDVersion" == fw.get('dev_name', ""):
                        fw_old["CPLD"] = version
                    elif "Front" in fw.get("dev_name", ""):
                        fw_old["FRONTDISKBPCPLD"] = version
                    elif "Rear" in fw.get("dev_name", ""):
                        fw_old["REARDISKBPCPLD"] = version
                    elif "SCMCPLD" == fw.get('dev_name', ""):
                        fw_old["SCMCPLD"] = version
                if args.type not in fw_old:
                    version_info = "Cannot get current firmware version, " + str(fwdata)
                    self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)
            else:
                version_info = "Cannot get current firmware version, " + str(fw_res.get('data'))
                self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)

            # set syn mode
            # CPLD 不需要保留配置
            RestFunc.securityCheckByRest(client)
            if args.type == "CPLD_PFR":
                # 默认传保留配置
                res_syn = RestFunc.syncmodePFRByRest(client, None, args.mode, args.type, None)
                if res_syn == {}:
                    result.State("Failure")
                    result.Message(["cannot set syncmode"])
                    self.wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    continue
                elif res_syn.get('code') == 0:
                    self.wirte_log(log_path, "Upload File", "Start", "")
                else:
                    result.State("Failure")
                    result.Message(["set sync mode error, " + str(res_syn.get('data'))])
                    self.wirte_log(log_path, "Upload File", "Connect Failed", result.Message)
                    continue
            else:
                self.wirte_log(log_path, "Upload File", "Start", "")

            # upload
            res_upload = RestFunc.uploadfirmwareByRest1(client, args.url)
            if res_upload == {}:
                result.State("Failure")
                result.Message(["cannot upload firmware update file"])
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Exceptions occurred while calling interface")
                continue
            elif res_upload.get('code') == 0:
                self.wirte_log(log_path, "Upload File", "Success", "")
            else:
                result.State("Failure")
                result.Message(["upload firmware error, " + str(res_upload.get('data'))])
                if res_upload.get('data', 0) == 1 or res_upload.get('data', 0) == 2:
                    self.wirte_log(log_path, "Upload File", "File Not Exist", str(res_upload.get('data')))
                elif res_upload.get('data', 0) == 404:
                    self.wirte_log(log_path, "Upload File", "Invalid URI", str(res_upload.get('data')))
                else:
                    self.wirte_log(log_path, "Upload File", "Connect Failed", str(res_upload.get('data')))
                continue

            # verify
            if args.type != "CPLD_PFR":
                time.sleep(20)
            self.wirte_log(log_path, "File Verify", "Start", "")
            res_verify = RestFunc.getverifyresultByRest(client)
            if res_verify == {}:
                result.State("Failure")
                result.Message(["cannot verify firmware update file"])
                self.wirte_log(log_path, "File Verify", "Connect Failed",
                               "Exceptions occurred while calling interface")
                continue
            elif res_verify.get('code') == 0:
                self.wirte_log(log_path, "File Verify", "Success", "")
            else:
                result.State("Failure")
                result.Message(["cannot verify firmware update file, " + str(res_verify.get('data'))])
                self.wirte_log(log_path, "File Verify", "Data Verify Failed", str(res_verify.get('data')))
                continue

            # apply
            task_dict = {"BMC": 0, "BIOS": 1, "PSUFW": 5, "CPLD": 2, "FRONTDISKBPCPLD": 3, "REARDISKBPCPLD": 4,
                         "CPLD_PFR": 10}
            if self.getServerStatus(client) != "off" and args.type != "DISKBPCPLD" and args.type != "CPLD_PFR":
                time.sleep(10)
                res_progress = RestFunc.getTaskInfoByRest(client)
                if res_progress == {}:
                    result.State("Failure")
                    result.Message([
                        "No apply task found in task list. Call interface api/maintenance/background/task_info returns: " + str(
                            res_progress)])
                    self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                    continue
                elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                    tasks = res_progress.get('data')
                    task = None
                    for t in tasks:
                        if args.type == "DISKBPCPLD":
                            if t["id"] == task_dict.get("REARDISKBPCPLD", -1):
                                task = t
                                break
                            elif t["id"] == task_dict.get("FRONTDISKBPCPLD", -1):
                                task = t
                                break
                        else:
                            if t["id"] == task_dict.get(args.type, -1):
                                task = t
                                break
                    # 无任务则退出
                    if task is None:
                        result.State("Failure")
                        result.Message(["No apply task found in task list." + str(res_progress)])
                        self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                        continue
                    if task["status"] == "FAILED":
                        result.State("Failure")
                        result.Message(["Apply task failed." + str(res_progress)])
                        self.wirte_log(log_path, "Apply", "Data Verify Failed", result.Message)
                        continue

                    result.State('Success')
                    if args.type == "DISKBPCPLD":
                        result.Message([
                            "Apply(FLASH) pending, host is power on now, image save in BMC FLASH and will apply later, trigger: poweroff, dcpowercycle, systemreboot. (TaskId=" + str(
                                task['id']) + ")"])
                    else:
                        result.Message([
                            "Apply(FLASH) pending, host is power on now, image save in BMC FLASH and will apply later, trigger: poweroff, dcpowercycle, systemreboot. (TaskId=" + str(
                                task_dict.get(args.type, 0)) + ")"])
                    self.wirte_log(log_path, "Apply", "Finish", result.Message)
                    continue
                else:
                    result.State("Failure")
                    result.Message(["No apply task found in task list." + str(res_progress)])
                    self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                    continue

            else:
                self.wirte_log(log_path, "Apply", "Start", "")
                # max error number
                error_count = 0
                # max progress number
                count = 0
                # 100num  若进度10次都是100 则主动reset
                count_100 = 0
                # 循环查看apply进度
                error_info = ""
                while True:
                    # CPLD PUS BIOS 的启动过程可能会1h, 因此从60改为180
                    if count > 180:
                        break
                    if error_count > 10:
                        break
                    if count_100 > 5:
                        break
                    count = count + 1
                    if args.type != "CPLD_PFR":
                        time.sleep(10)
                    else:
                        time.sleep(3)
                    res_progress = RestFunc.getTaskInfoByRest(client)
                    if res_progress == {}:
                        error_count = error_count + 1
                        error_info = 'Failed to call BMC interface api/maintenance/background/task_info ,response is none'
                    elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                        tasks = res_progress.get('data')
                        task = None
                        for t in tasks:
                            if args.type == "DISKBPCPLD":
                                if t["id"] == task_dict.get("REARDISKBPCPLD", -1):
                                    task = t
                                    break
                                elif t["id"] == task_dict.get("FRONTDISKBPCPLD", -1):
                                    task = t
                                    break
                            else:
                                if t["id"] == task_dict.get(args.type, -1):
                                    task = t
                                    break
                        # 无任务则退出
                        if task is None:
                            result.State("Failure")
                            result.Message(["No apply task found in task list."])
                            self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                            break
                        error_info = str(task)
                        if task["status"] == "COMPLETE":
                            break
                        elif task["status"] == "FAILED":
                            self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) failed.")
                            result.State("Failure")
                            result.Message(["Apply(FLASH) failed."])
                            break
                        elif task["status"] == "CANCELED":
                            self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) canceled.")
                            result.State("Failure")
                            result.Message(["Apply(FLASH) canceled."])
                            break
                        else:
                            self.wirte_log(log_path, "Apply", "In Progress",
                                           "progress:" + str(task["progress"]) + "%")
                            if str(task["progress"]) == 100:
                                count_100 = count_100 + 1
                    else:
                        error_count = error_count + 1
                        error_info = str(res_progress.get('data'))

                # 判断apply是否结束
                if result.State == "Failure":
                    continue

                # 获取apply进度结束
                self.wirte_log(log_path, "Apply", "Success", "")
                if args.type == "CPLD_PFR":
                    if args.mode == "Auto":
                        result.State('Success')
                        result.Message([
                            "Activate pending, CPLD will activate later."])
                        self.wirte_log(log_path, "Apply", "Success", result.Message)
                    else:
                        result.State('Success')
                        result.Message([
                            "Activate pending, image save in BMC FLASH and will apply later, trigger: BMC reboot. (TaskId=10)"])
                        self.wirte_log(log_path, "Apply", "Write to Temporary FLASH Success", result.Message)
                elif args.type == "DISKBPCPLD":
                    result.State('Success')
                    result.Message([
                        "Activate pending, host is power off now, BPCPLD will activate later."])
                    self.wirte_log(log_path, "Apply", "Write to Temporary FLASH Success", result.Message)
                else:
                    fw_res_new = RestFunc.getFwVersion(client)
                    fw_new = {}
                    if fw_res_new == {}:
                        result.State("Failure")
                        result.Message(["Failed to call BMC interface api/version_summary, response is none"])
                        self.wirte_log(log_path, "Activate", "Version verify Failed", result.Message)
                    elif fw_res_new.get('code') == 0 and fw_res_new.get('data') is not None:
                        fwdata = fw_res_new.get('data')
                        for fw in fwdata:
                            if fw.get('dev_version') == '':
                                version = "-"
                            else:
                                index_version = fw.get('dev_version', "").find('(')
                                if index_version == -1:
                                    version = fw.get('dev_version')
                                else:
                                    version = fw.get('dev_version')[:index_version].strip()

                            if "CPLD" == fw.get("dev_name", "") or "MainBoard0CPLDVersion" == fw.get("dev_name", ""):
                                fw_new["CPLD"] = version
                            elif "Front" in fw.get("dev_name", ""):
                                fw_new["FRONTDISKBPCPLD"] = version
                            elif "Rear" in fw.get("dev_name", ""):
                                fw_new["REARDISKBPCPLD"] = version
                            elif "SCMCPLD" == fw.get("dev_name", ""):
                                fw_new["SCMCPLD"] = version
                        if args.type == "CPLD_PFR":
                            if "SCMCPLD" in fw_new:
                                versioncheck = str(args.type) + " update successfully, new version: " + fw_new[
                                    "SCMCPLD"]
                                result.State("Success")
                                result.Message([versioncheck])
                                self.wirte_log(log_path, "Activate", "Success", versioncheck)
                        elif args.type in fw_new:
                            if args.type in fw_old:
                                versioncheck = str(
                                    args.type) + " update successfully, Version: image change from " + fw_old[
                                                   args.type] + " to " + fw_new[args.type]
                            else:
                                versioncheck = str(args.type) + " update successfully, new version: " + fw_new[
                                    args.type]
                            result.State("Success")
                            result.Message([versioncheck])
                            self.wirte_log(log_path, "Activate", "Success", versioncheck)
                        else:
                            versioncheck = " Cannot get " + str(args.type) + " version: " + str(fwdata)
                            result.State("Failure")
                            result.Message([versioncheck])
                            self.wirte_log(log_path, "Upload File", "Connect Failed", versioncheck)
                    else:
                        result.State("Failure")
                        result.Message(["get new fw information error, " + str(fw_res.get('data'))])
                        self.wirte_log(log_path, "Activate", "Data Verify Failed", result.Message)

                # 判断apply是否结束
                if result.State == "Failure" or result.State == "Success":
                    continue

    def updatepsu(self, client, args):
        args.type = None
        args.auto_flag = None
        result = self.fwupdate(client, args)
        return result

    def updatepsu1(self, client, args):
        result = ResultBean()
        log_path = args.log_path
        session_path = args.session_path
        upgrade_count = 0
        while True:
            # 判断session是否存在，存在则logout&del
            if os.path.exists(session_path):
                with open(session_path, 'r') as oldsession:
                    headers = oldsession.read()
                    headers_json = json.loads(str(headers).replace("'", '"'))
                    client.setHearder(headers_json)
                    # logout
                    RestFunc.logout(client)  # 删除session
                if os.path.exists(session_path):
                    os.remove(session_path)
            # 删除
            if result.State == "Success":
                return result
            elif result.State == "Abort":
                result.State = "Failure"
                return result
            else:
                if upgrade_count > retry_count:
                    return result
                else:
                    if upgrade_count >= 1:
                        # 重新升级 初始化result
                        self.wirte_log(log_path, "Upload File", "Upgrade Retry " + str(upgrade_count) + " Times", "")
                        result = ResultBean()
                    upgrade_count = upgrade_count + 1
            # login
            headers = {}
            logcount = 0
            while True:
                # 等6分钟
                if logcount > 18:
                    break
                else:
                    logcount = logcount + 1
                    time.sleep(20)
                # login
                headers = RestFunc.login_M6(client)
                if headers != {}:
                    # 记录session
                    with open(session_path, 'w') as new_session:
                        new_session.write(str(headers))
                    client.setHearder(headers)
                    break
                else:
                    # print(ftime() + "Create session failed")
                    self.wirte_log(log_path, "Upload File", "Connect Failed", "Connect number:" + str(logcount))
            # 10次无法登陆 不再重试
            if headers == {}:
                result.State("Failure")
                result.Message(["Cannot log in to BMC."])
                return result
            # get old version
            fw_res = RestFunc.getFwVersion(client)
            fw_old = {}
            if fw_res == {}:
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Cannot get current firmware version.")
            elif fw_res.get('code') == 0 and fw_res.get('data') is not None:
                fwdata = fw_res.get('data')
                for fw in fwdata:
                    if fw.get('dev_version') == '':
                        version = "-"
                    else:
                        index_version = fw.get('dev_version', "").find('(')
                        if index_version == -1:
                            version = fw.get('dev_version')
                        else:
                            version = fw.get('dev_version')[:index_version].strip()
                    if "PSU" in fw.get("dev_name", ""):
                        fw_old["PSUFW"] = version
                        break
                if args.type not in fw_old:
                    version_info = "Cannot get current firmware version, " + str(fwdata)
                    self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)
            else:
                version_info = "Cannot get current firmware version, " + str(fw_res.get('data'))
                self.wirte_log(log_path, "Upload File", "Connect Failed", version_info)

            # PSU 升级自动重启，先关机
            #
            flag = False
            if args.mode == "Auto" and self.getServerStatus(client) != "off":
                flag = True
                choices = {'on': 1, 'off': 0, 'cycle': 2, 'reset': 3, 'shutdown': 5}
                Power = RestFunc.setM6PowerByRest(client, choices["off"])
                if Power.get('code') == 0 and Power.get('data') is not None:
                    off_count = 0
                    while True:
                        if self.getServerStatus(client) == "off" or off_count > 5:
                            break
                        time.sleep(10)
                        off_count += 1
                    if self.getServerStatus(client) != "off":
                        result.State('Failure')
                        result.Message(['set power off complete, but get power status error.'])
                        self.wirte_log(log_path, "Auto Reset Server", "Get Power Status Error", result.Message)
                        continue
                    else:
                        self.wirte_log(log_path, "Set Power Off", "Successfully", "")
                else:
                    result.State('Failure')
                    result.Message(['set power off failed.'])
                    self.wirte_log(log_path, "Auto Reset Server", "Set Power Off Failed", result.Message)
                    continue

            # set syn mode
            RestFunc.securityCheckByRest(client)
            self.wirte_log(log_path, "Upload File", "Start", "")

            # upload
            res_upload = RestFunc.uploadfirmwareByRest1(client, args.url)
            if res_upload == {}:
                result.State("Failure")
                result.Message(["cannot upload firmware update file"])
                self.wirte_log(log_path, "Upload File", "Connect Failed", "Exceptions occurred while calling interface")
                continue
            elif res_upload.get('code') == 0:
                self.wirte_log(log_path, "Upload File", "Success", "")
            else:
                result.State("Failure")
                result.Message(["upload firmware error, " + str(res_upload.get('data'))])
                if res_upload.get('data', 0) == 1 or res_upload.get('data', 0) == 2:
                    self.wirte_log(log_path, "Upload File", "File Not Exist", str(res_upload.get('data')))
                elif res_upload.get('data', 0) == 404:
                    self.wirte_log(log_path, "Upload File", "Invalid URI", str(res_upload.get('data')))
                else:
                    self.wirte_log(log_path, "Upload File", "Connect Failed", str(res_upload.get('data')))
                continue

            # verify
            time.sleep(20)
            self.wirte_log(log_path, "File Verify", "Start", "")
            res_verify = RestFunc.getverifyresultByRest(client)
            if res_verify == {}:
                result.State("Failure")
                result.Message(["cannot verify firmware update file"])
                self.wirte_log(log_path, "File Verify", "Connect Failed",
                               "Exceptions occurred while calling interface")
                continue
            elif res_verify.get('code') == 0:
                self.wirte_log(log_path, "File Verify", "Success", "")
            else:
                result.State("Failure")
                result.Message(["cannot verify firmware update file, " + str(res_verify.get('data'))])
                self.wirte_log(log_path, "File Verify", "Data Verify Failed", str(res_verify.get('data')))
                continue

            # apply
            task_dict = {"BMC": 0, "BIOS": 1, "PSUFW": 5, "CPLD": 2, "FRONTDISKBPCPLD": 3, "REARDISKBPCPLD": 4,
                         "CPLD_PFR": 10}
            if self.getServerStatus(client) != "off":
                time.sleep(10)
                res_progress = RestFunc.getTaskInfoByRest(client)
                if res_progress == {}:
                    result.State("Failure")
                    result.Message(["No apply task found in task list. Call interface "
                                    "api/maintenance/background/task_info returns: " + str(res_progress)])
                    self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                    continue
                elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                    tasks = res_progress.get('data')
                    task = None
                    for t in tasks:
                        if t["id"] == task_dict.get(args.type, -1):
                            task = t
                            break
                    # 无任务则退出
                    if task is None:
                        result.State("Failure")
                        result.Message(["No apply task found in task list." + str(res_progress)])
                        self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                        continue
                    if task["status"] == "FAILED":
                        result.State("Failure")
                        result.Message(["Apply task failed." + str(res_progress)])
                        self.wirte_log(log_path, "Apply", "Data Verify Failed", result.Message)
                        continue

                    result.State('Success')
                    result.Message(["Apply(FLASH) pending, host is power on now, image save in BMC FLASH and will "
                                    "apply later, trigger: poweroff, dcpowercycle, systemreboot. (TaskId=" +
                                    str(task_dict.get(args.type, 0)) + ")"])
                    self.wirte_log(log_path, "Apply", "Finish", result.Message)
                    continue
                else:
                    result.State("Failure")
                    result.Message(["No apply task found in task list." + str(res_progress)])
                    self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                    continue
            else:
                self.wirte_log(log_path, "Apply", "Start", "")
                # max error number
                error_count = 0
                # max progress number
                count = 0
                # 100num  若进度10次都是100 则主动reset
                count_100 = 0
                # 循环查看apply进度
                error_info = ""
                while True:
                    if count > 60:
                        break
                    if error_count > 10:
                        break
                    if count_100 > 5:
                        break
                    count = count + 1
                    time.sleep(20)
                    res_progress = RestFunc.getTaskInfoByRest(client)
                    if res_progress == {}:
                        error_count = error_count + 1
                        error_info = 'Failed to call BMC interface api/maintenance/background/task_info ,response is none'
                    elif res_progress.get('code') == 0 and res_progress.get('data') is not None:
                        tasks = res_progress.get('data')
                        task = None
                        for t in tasks:
                            if t["id"] == task_dict.get(args.type, -1):
                                task = t
                                break
                        # 无任务则退出
                        if task is None:
                            result.State("Failure")
                            result.Message(["No apply task found in task list."])
                            self.wirte_log(log_path, "Apply", "Image and Target Component Mismatch", result.Message)
                            break
                        error_info = str(task)
                        if task["status"] == "COMPLETE":
                            break
                        elif task["status"] == "FAILED":
                            self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) failed.")
                            result.State("Failure")
                            result.Message(["Apply(FLASH) failed."])
                            break
                        elif task["status"] == "CANCELED":
                            self.wirte_log(log_path, "Apply", "Finish", "Apply(FLASH) canceled.")
                            result.State("Failure")
                            result.Message(["Apply(FLASH) canceled."])
                            break
                        else:
                            self.wirte_log(log_path, "Apply", "In Progress",
                                           "progress:" + str(task["progress"]) + "%")
                            if str(task["progress"]) == 100:
                                count_100 = count_100 + 1
                    else:
                        error_count = error_count + 1
                        error_info = str(res_progress.get('data'))

                # 判断apply是否结束
                if result.State == "Failure":
                    continue

                # 获取apply进度结束
                self.wirte_log(log_path, "Apply", "Success", "")

                fw_res_new = RestFunc.getFwVersion(client)
                fw_new = {}
                if fw_res_new == {}:
                    result.State("Failure")
                    result.Message(
                        ["Failed to call BMC interface api/version_summary, response is none"])
                    self.wirte_log(log_path, "Activate", "Data Verify Failed", result.Message)
                elif fw_res_new.get('code') == 0 and fw_res_new.get('data') is not None:
                    fwdata = fw_res_new.get('data')
                    for fw in fwdata:
                        if fw.get('dev_version') == '':
                            version = "-"
                        else:
                            index_version = fw.get('dev_version', "").find('(')
                            if index_version == -1:
                                version = fw.get('dev_version')
                            else:
                                version = fw.get('dev_version')[:index_version].strip()
                        if "PSU" in fw.get("dev_name", ""):
                            fw_new["PSUFW"] = version
                            break

                    if args.type in fw_new:
                        if args.type in fw_old:
                            versioncheck = str(args.type) + " update successfully, Version: image change from " + fw_old[args.type] + " to " + fw_new[args.type]
                        else:
                            versioncheck = str(args.type) + " update successfully, new version: " + fw_new[args.type]
                        result.State("Success")
                        result.Message([versioncheck])
                        self.wirte_log(log_path, "Activate", "Success", versioncheck)
                    else:
                        versioncheck = " Cannot get " + str(args.type) + " version: " + str(fwdata)
                        result.State("Failure")
                        result.Message([versioncheck])
                        self.wirte_log(log_path, "Upload File", "Connect Failed", versioncheck)
                else:
                    result.State("Failure")
                    result.Message(["get new fw information error, " + str(fw_res.get('data'))])
                    self.wirte_log(log_path, "Activate", "Data Verify Failed", result.Message)

                if flag:
                    result = ResultBean()
                    ctr_info = IpmiFunc.powerControlByIpmi(client, "on")
                    if ctr_info:
                        if ctr_info.get('code') == 0 and ctr_info.get('data') is not None and ctr_info.get('data').get('result') is not None:
                            result.State("Success")
                            result.Message(['Update PSU complete, system auto power on success'])
                            self.wirte_log(log_path, "Restart", "Set power on success", result.Message)
                        else:
                            result.State("Failure")
                            result.Message(['Update PSU complete. But system auto reset failed, please power on manually ...'])
                            self.wirte_log(log_path, "Restart", "Set power on failed", result.Message)
                    else:
                        result.State("Failure")
                        result.Message(['set power failed.please check server manually'])
                        self.wirte_log(log_path, "Restart", "Set power on failed", result.Message)

                # 判断reboot是否结束
                if result.State == "Failure" or result.State == "Success":
                    continue

    def ftime(self, ff="%Y-%m-%d %H:%M:%S "):
        try:
            localtime = time.localtime()
            f_localtime = time.strftime(ff, localtime)
            return f_localtime
        except:
            return ""

    def getServerStatus(self, client):
        try:
            res_1 = RestFunc.getChassisStatusByRest(client)
            if res_1.get('code') == 0 and res_1.get('data') is not None:
                status = res_1.get('data').get('power_status', "unknown")
                if status == "On":
                    return "on"
                elif status == "Off":
                    return "off"
                else:
                    return "unknown"
            else:
                return "unknown"
        except:
            return "unknown"

    def wirte_log(self, log_path, stage="", state="", note=""):
        try:
            log_list = []
            with open(log_path, 'r') as logfile_last:
                log_cur = logfile_last.read()
                if log_cur != "":
                    log_cur_dict = json.loads(str(log_cur).replace("'", '"'))
                    log_list = log_cur_dict.get("log")

            with open(log_path, 'w') as logfile:
                log_time = self.ftime("%Y-%m-%dT%H:%M:%S")
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
                logfile.write(json.dumps(log_dict, default=lambda o: o.__dict__, sort_keys=True, indent=4,
                                         ensure_ascii=False))
            return True
        except Exception as e:
            return str(e)

    def setncsi(self, client, args):
        ncsiinfo = ResultBean()
        if args.mode == "disable":
            set_cmd = " 0x3c 0x13 0x01 0x00 0x0f"
            set_res = IpmiFunc.sendRawByIpmi(client, set_cmd)
            if set_res.get('code') == 0:
                ncsiinfo.State("Success")
                ncsiinfo.Message([""])
            else:
                ncsiinfo.State("Failure")
                ncsiinfo.Message(["set ncsi disable failed."])
            return ncsiinfo
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        # get
        res = RestFunc.getNCSI4jd(client)
        if res == {}:
            ncsiinfo.State("Failure")
            ncsiinfo.Message(["cannot get ncsi information"])
        elif res.get('code') == 0 and res.get('data') is not None:
            data = res.get('data')
            support_list = data.get('Support_Nic_Info', [])
            support_dict = {}
            for item in support_list:
                if "NIC_Name" in item and "Port_Num" in item:
                    support_dict[item.get('NIC_Name')] = item.get('Port_Num')

            if args.mode == "auto":
                mode = "AutoFailover"
            else:
                mode = "Manual"
                if not args.channel_number:
                    ncsiinfo.State("Failure")
                    ncsiinfo.Message(["please input channel_number."])
                    RestFunc.logout(client)
                    return ncsiinfo

            # check
            if args.nic_type:
                if args.nic_type not in support_dict.keys():
                    ncsiinfo.State("Failure")
                    ncsiinfo.Message(["please choose nic_type from " + str(list(support_dict.keys()))])
                    RestFunc.logout(client)
                    return ncsiinfo
                if args.channel_number and mode == "Manual":
                    if args.channel_number not in [i for i in range(int(support_dict.get(args.nic_type)))]:
                        ncsiinfo.State("Failure")
                        ncsiinfo.Message(["please choose channel_number from " +
                                          str([i for i in range(int(support_dict.get(args.nic_type)))])])
                        RestFunc.logout(client)
                        return ncsiinfo
            else:
                args.nic_type = data.get("NIC_Name")
            # set
            res = RestFunc.setNCSI4jd(client, mode, args.nic_type, args.channel_number)

            if res == {}:
                ncsiinfo.State("Failure")
                ncsiinfo.Message(["set ncsi error"])
            elif res.get('code') == 0:
                ncsiinfo.State("Success")
                ncsiinfo.Message([""])
            elif res.get('code') != 0 and res.get('data') is not None:
                ncsiinfo.State("Failure")
                ncsiinfo.Message([res.get('data')])
            else:
                ncsiinfo.State("Failure")
                ncsiinfo.Message(["set ncsi error, error code " + str(res.get('code'))])
        elif res.get('code') != 0 and res.get('data') is not None:
            ncsiinfo.State("Failure")
            ncsiinfo.Message([res.get('data')])
        else:
            ncsiinfo.State("Failure")
            ncsiinfo.Message(["get ncsi information error, error code " + str(res.get('code'))])

        RestFunc.logout(client)
        return ncsiinfo

    def addLogicalDisk(self, client, args):
        '''
        locate disk
        :param client:
        :param args:
        :return:
        '''
        locate_Info = ResultBean()
        if args.vname is None:
            args.vname = ""

        data = {
            "selectSize": args.select,
            "numberPD": len(args.pdlist),
            "ctrlId": args.ctrlId,
            "raidLevel": args.rlevel,
            "stripSize": args.size,
            "accessPolicy": args.access,
            "readPolicy": args.r,
            "writePolicy": args.w,
            "cachePolicy": args.cache,
            "ioPolicy": args.io,
            "initState": args.init,
            "spanDepth": args.spandepth,
            "raidname": args.vname
        }

        for i in range(len(args.pdlist)):
            data["pdDeviceIndex" + str(i)] = args.pdlist[i]

        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        res = RestFunc.addLogicalDisk(client, data)
        if res == {}:
            locate_Info.State("Failure")
            locate_Info.Message(["create virtual drive failed"])
        elif res.get('code') == 0 and res.get('data') is not None:
            IpmiFunc.getStatus(args, args.ctrlId)
            locate_Info.State('Success')
            locate_Info.Message(['create virtual drive successful.'])
        else:
            locate_Info.State("Failure")
            locate_Info.Message(['create virtual drive failed, ' + str(res.get('data'))])

        # logout
        RestFunc.logout(client)
        return locate_Info

    def addfirewall(self, client, args):
        import time
        res = ResultBean()
        try:
            headers = RestFunc.login_M6(client)
            if headers == {}:
                login_res = ResultBean()
                login_res.State("Failure")
                login_res.Message(["login error, please check username/password/host/port"])
                return login_res
            client.setHearder(headers)
            data = {}
            data['rule'] = args.rule
            if args.timeout == "enable":
                data['timeout'] = 1
                start_time = int(time.mktime(time.strptime(args.timestart, "%Y%m%d%H%M%S")))
                end_time = int(time.mktime(time.strptime(args.timeend, "%Y%m%d%H%M%S")))
                data['start_time'] = start_time
                data['end_time'] = end_time
            else:
                data['timeout'] = 0
            if args.firewalltype == "ip":
                if RegularCheckUtil.checkIP(args.start) and not str(args.start).startswith('0.'):
                    data['ip_start'] = args.start
                    if args.end is not None:
                        data['ip_end'] = args.end
                    else:
                        data['ip_end'] = ""
                    result = RestFunc.addIPFirewallByRest(client, data)
                    if result.get('code') == 0:
                        res.State("Success")
                        res.Message(['add ip firewall success.'])
                    else:
                        res.State('Failure')
                        res.Message([result.get('data')])
                else:
                    res.State("Failure")
                    res.Message(["Invalid start IP Address. Input an IPv4 address not start with 0."])
            elif args.firewalltype == "mac":
                if args.firewalltype == "allow":
                    res.State("Failure")
                    res.Message(["only support block rule while add mac firewall"])
                    RestFunc.logout(client)
                    return res
                if args.end is not None:
                    res.State("Failure")
                    res.Message(["not need -E parameter while add mac firewall"])
                    RestFunc.logout(client)
                    return res
                p = '^([0-9a-fA-F]{2})(([/\s:][0-9a-fA-F]{2}){5})$'
                if not re.search(p, str(args.start), re.I):
                    res.State("Failure")
                    res.Message(["Invalid Mac Address. Input mac address, eg, 00:02:50:BE:24:2D"])
                    RestFunc.logout(client)
                    return res
                data['mac_addr'] = args.start
                result = RestFunc.addMacFirewallByRest(client, data)
                if result.get('code') == 0:
                    res.State("Success")
                    res.Message(['add mac firewall success.'])
                else:
                    res.State('Failure')
                    res.Message([result.get('data')])
            else:
                protocol_dict = {
                    "Both": 2,
                    "UDP": 1,
                    "TCP": 0
                }
                data['port_start'] = args.start
                if args.end is not None:
                    data['port_end'] = args.end
                else:
                    data['port_end'] = ""
                # data['network_type'] = args.networktype
                # data['protocol'] = protocol_dict.get(args.protocol)
                result = RestFunc.addPortFirewallByRest(client, data)
                if result.get('code') == 0:
                    res.State("Success")
                    res.Message(['add port firewall success.'])
                else:
                    res.State('Failure')
                    res.Message([result.get('data')])
        except Exception as e:
            res.State("Failure")
            res.Message([str(e)])
        RestFunc.logout(client)
        return res

    def getad(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(
                ["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        res = RestFunc.getADM6(client)
        if res.get('code') == 0 and res.get('data') is not None:
            ad_raw = res.get('data')

            ad_res = collections.OrderedDict()
            ad_res['Enable'] = 'Enable' if ad_raw['enable'] == 1 else "Disabled"
            if "enablessl" in ad_raw:
                ad_res['SSLEnable'] = 'Enable' if ad_raw['enablessl'] == 1 else "Disable"
            ad_res['SecretName'] = ad_raw['secret_username']
            ad_res['UserDomainName'] = ad_raw['user_domain_name']
            ad_res['DomainControllerServerAddress1'] = ad_raw['domain_controller1']
            ad_res['DomainControllerServerAddress2'] = ad_raw['domain_controller2']
            ad_res['DomainControllerServerAddress3'] = ad_raw['domain_controller3']

            result.State("Success")
            result.Message([{"AD": ad_res}])
        else:
            result.State("Failure")
            result.Message([res.get('data')])

        RestFunc.logout(client)
        return result

    def setad(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(
                ["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        # get
        get_res = RestFunc.getADM6(client)
        if get_res.get('code') == 0 and get_res.get('data') is not None:
            ad_raw = get_res.get('data')
        else:
            result.State("Failure")
            result.Message([get_res.get('data')])
            RestFunc.logout(client)
            return result

        if args.enable is not None:
            if args.enable == "enable":
                ad_raw['enable'] = 1
            else:
                ad_raw['enable'] = 0

        if hasattr(args, "ssl_enable"):
            if args.ssl_enable == "enable":
                ad_raw['enablessl'] = 1
            else:
                ad_raw['enablessl'] = 0

        ad_raw['id'] = 1
        ad_raw['secret_password'] = ''

        if ad_raw['enable'] == 1:
            if args.domain is not None:
                ad_raw['user_domain_name'] = args.domain
            if args.name is not None:
                dn = r'^[a-zA-Z][\da-zA-Z]{0,63}$'
                if re.search(dn, args.name, re.I):
                    ad_raw['secret_username'] = args.name
                else:
                    result.State("Failure")
                    result.Message(
                        ['Username should be a string of 1 to 64 alpha-numeric characters.It must start with an alphabetical character.'])
                    RestFunc.logout(client)
                    return result
            if args.code is not None:
                if len(
                        args.code) < 6 or len(
                        args.code) > 127 or " " in args.code:
                    result.State("Failure")
                    result.Message(
                        ['Password must be 6 - 127 characters long. White space is not allowed.'])
                    RestFunc.logout(client)
                    return result
                ad_raw['secret_password'] = args.code
            if args.addr1 is not None:
                if RegularCheckUtil.checkIP(
                        args.addr1) or RegularCheckUtil.checkIPv6(
                        args.addr1):
                    ad_raw['domain_controller1'] = args.addr1
                else:
                    result.State("Failure")
                    result.Message(
                        ['Invalid Domain Controller Server Address. Input an IPv4 or IPv6 address'])
                    RestFunc.logout(client)
                    return result
            if args.addr2 is not None:
                if RegularCheckUtil.checkIP(
                        args.addr2) or RegularCheckUtil.checkIPv6(
                        args.addr2):
                    ad_raw['domain_controller2'] = args.addr2
                else:
                    result.State("Failure")
                    result.Message(
                        ['Invalid Domain Controller Server Address. Input an IPv4 or IPv6 address'])
                    RestFunc.logout(client)
                    return result
            if args.addr3 is not None:
                if RegularCheckUtil.checkIP(
                        args.addr3) or RegularCheckUtil.checkIPv6(
                        args.addr3):
                    ad_raw['domain_controller3'] = args.addr3
                else:
                    result.State("Failure")
                    result.Message(
                        ['Invalid Domain Controller Server Address. Input an IPv4 or IPv6 address'])
                    RestFunc.logout(client)
                    return result

        set_res = RestFunc.setADM6(client, ad_raw)
        if set_res.get('code') == 0 and set_res.get('data') is not None:
            result.State("Success")
            result.Message([set_res.get('data')])
        else:
            result.State("Failure")
            result.Message([set_res.get('data')])

        RestFunc.logout(client)
        return result

    def getmediainstance(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        res = RestFunc.getMediaInstance(client)
        if res.get('code') == 0 and res.get('data') is not None:
            gs = res.get('data')
            media_instance = collections.OrderedDict()
            media_instance["CDNum"] = gs.get("num_cd")
            media_instance["HDNum"] = gs.get("num_hd")
            media_instance["KVMCDNum"] = gs.get("kvm_num_cd")
            media_instance["KVMHDNum"] = gs.get("kvm_num_hd")
            media_instance["SDMedia"] = "Enable" if gs.get("sd_media") == 1 else "Disable"
            media_instance["SecureChannel"] = "Enable" if gs.get("secure_channel") == 1 else "Disable"
            media_instance["PowerSaveMode"] = "Enable" if gs.get("power_save_mode") == 1 else "Disable"
            result.State("Success")
            result.Message([{"Instance": media_instance}])
        else:
            result.State("Failure")
            result.Message([res.get('data')])

        RestFunc.logout(client)
        return result

    def setmediainstance(self, client, args):
        result = ResultBean()
        # 不支持设置-SC参数
        if args.secure_channel is not None:
            result.State("Failure")
            result.Message(["Not support setting secure channel"])
            return result

        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        res = RestFunc.getMediaInstance(client)
        if res.get('code') == 0 and res.get('data') is not None:
            instance = res.get('data')
        else:
            result.State("Failure")
            result.Message([res.get('data')])

            RestFunc.logout(client)
            return result

        if args.num_cd is not None:
            instance['num_cd'] = args.num_cd
        if args.kvm_num_cd is not None:
            if args.kvm_num_cd > instance['num_cd']:
                result.State("Failure")
                result.Message([
                    "Remote KVM CD/DVD device instance value should be less than or equal to virtual CD/DVD device count."])

                RestFunc.logout(client)
                return result
            else:
                instance['kvm_num_cd'] = args.kvm_num_cd

        if args.num_hd is not None:
            instance['num_hd'] = args.num_hd
        if args.kvm_num_hd is not None:
            if args.kvm_num_hd > instance['num_hd']:
                result.State("Failure")
                result.Message(
                    ["Remote KVM Hard disk instance value should be less than or equal to virtual Hard disk count."])

                RestFunc.logout(client)
                return result
            else:
                instance['kvm_num_hd'] = args.kvm_num_hd

        if args.sd_media is not None:
            if args.sd_media == 'Enable':
                instance['sd_media'] = 1
            else:
                instance['sd_media'] = 0

        if args.power_save_mode is not None:
            if args.power_save_mode == 'Enable':
                instance['power_save_mode'] = 1
            else:
                instance['power_save_mode'] = 0

        # print(instance)
        set_res = RestFunc.setMediaInstance(client, instance)
        if set_res.get('code') == 0:
            result.State("Success")
            result.Message(["Set media instance success"])
        else:
            result.State("Failure")
            result.Message(["Set media instance failed. " + set_res.get('data')])

        RestFunc.logout(client)
        return result

    def resetkvm(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(
                ["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        res = RestFunc.resetBMCM7(client, 'kvm')
        if res.get('code') == 0 and res.get('data') is not None:
            result.State("Success")
            result.Message([res.get('data')])
        else:
            result.State("Failure")
            result.Message([res.get('data')])

        RestFunc.logout(client)
        return result

    def resetbmc(self, client, args):
        result = ResultBean()

        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        RestFunc.securityCheckByRest(client)
        res = RestFunc.resetBMCM7(client, 'bmc')
        if res.get('code') == 0 and res.get('data') is not None:
            result.State("Success")
            result.Message([res.get('data')])
        else:
            result.State("Failure")
            result.Message([res.get('data')])

        RestFunc.logout(client)
        return result

    def setuserrule(self, client, args):
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        old_info = RestFunc.getUserRuleByRest(client)  # 现有值
        if old_info.get('code') == 0 and old_info.get('data') is not None:
            old_data = old_info.get('data')
            if old_data.get('enable') == "disable":
                # 禁用->禁用
                if args.state == "disable":
                    result.State('Failure')
                    result.Message(['No setting changed!'])
                # 禁用->启用
                elif args.state == "enable":
                    old_json = {}
                    old_json['id'] = 1
                    old_json['enable'] = args.state
                    old_json['minlength'] = args.minlength if args.minlength else 8
                    old_json['complexityenable'] = args.combination if args.combination else 'disable'
                    old_json['complexitynumber'] = args.complexitynumber if args.complexitynumber else 'disable'
                    old_json['uppercaseletters'] = args.uppercaseletters if args.uppercaseletters else 'disable'
                    old_json['lowercaseletters'] = args.lowercaseletters if args.lowercaseletters else 'disable'
                    old_json['specialcharacters'] = args.specialcharacters if args.specialcharacters else 'disable'
                    old_json['valid_period'] = args.validperiod if args.validperiod else 0
                    old_json['history_records'] = args.historyrecords if args.historyrecords else 0
                    old_json['retry_times'] = args.retrytimes if args.retrytimes else 0
                    old_json['lock_time'] = args.locktime if args.locktime else 5
                    args.json = old_json
                    complexityflag = False
                    if old_json.get('complexityenable') == 'enable':
                        i = 0
                        if old_json.get('complexitynumber') == 'enable':
                            i = i + 1
                        if old_json.get('uppercaseletters') == 'enable':
                            i = i + 1
                        if old_json.get('lowercaseletters') == 'enable':
                            i = i + 1
                        if old_json.get('specialcharacters') == 'enable':
                            i = i + 1
                        if i > 2:
                            complexityflag = True
                    else:
                        complexityflag = True
                    if complexityflag:
                        response = RestFunc.setUserRuleByRest(client, args)
                        if response['code'] == 0:
                            result.State('Success')
                            result.Message(['set user rule success.'])
                        else:
                            result.State('Failure')
                            result.Message([response['data']])
                    else:
                        result.State('Failure')
                        result.Message(['At least three options(CN/UL/LL/SC) must be chosen.'])

                # 禁用->状态为空，有其他值
                else:
                    result.State('Failure')
                    result.Message(['Parameters can be set only when it is enabled!'])
            else:
                old_json = {}
                old_json['id'] = 1
                old_json['enable'] = args.state if args.state else old_data.get('enable')
                old_json['minlength'] = args.minlength if args.minlength else old_data.get('minlength')
                old_json['complexityenable'] = args.combination if args.combination else old_data.get(
                    'complexityenable')
                old_json['complexitynumber'] = args.complexitynumber if args.complexitynumber else old_data.get(
                    'complexitynumber')
                old_json['uppercaseletters'] = args.uppercaseletters if args.uppercaseletters else old_data.get(
                    'uppercaseletters')
                old_json['lowercaseletters'] = args.lowercaseletters if args.lowercaseletters else old_data.get(
                    'lowercaseletters')
                old_json['specialcharacters'] = args.specialcharacters if args.specialcharacters else old_data.get(
                    'specialcharacters')
                old_json['valid_period'] = args.validperiod if args.validperiod else old_data.get('valid_period')
                old_json['history_records'] = args.historyrecords if args.historyrecords else old_data.get(
                    'history_records')
                old_json['retry_times'] = args.retrytimes if args.retrytimes else old_data.get('retry_times')
                old_json['lock_time'] = args.locktime if args.locktime else old_data.get('lock_time')
                args.json = old_json
                complexityflag = False
                if old_json.get('complexityenable') == 'enable':
                    i = 0
                    if old_json.get('complexitynumber') == 'enable':
                        i = i + 1
                    if old_json.get('uppercaseletters') == 'enable':
                        i = i + 1
                    if old_json.get('lowercaseletters') == 'enable':
                        i = i + 1
                    if old_json.get('specialcharacters') == 'enable':
                        i = i + 1
                    if i > 2:
                        complexityflag = True
                else:
                    complexityflag = True
                if complexityflag:
                    response = RestFunc.setUserRuleByRest(client, args)
                    if response['code'] == 0:
                        result.State('Success')
                        result.Message(['set user rule success.'])
                    else:
                        result.State('Failure')
                        result.Message([response['data']])
                else:
                    result.State('Failure')
                    result.Message(['At least three options(CN/UL/LL/SC) must be chosen.'])
        else:
            result.State('Failure')
            result.Message(['get/set user rule failure!'])
        RestFunc.logout(client)
        return result

    def getpsu(self, client, args):
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        psu_return = ResultBean()
        psu_Info = PSUBean()
        List = []

        # get
        res = RestFunc.getPsuInfoByRest(client)
        if res == {}:
            psu_return.State('Failure')
            psu_return.Message(['get psu info failed'])
        elif res.get('code') == 0 and res.get('data') is not None:
            status_dict = {0: 'Unknown', 1: 'Redundancy', 2: 'Redundant Lost', 32: 'Not Redundant'}
            overalhealth = RestFunc.getHealthSummaryByRest(client)
            if overalhealth.get('code') == 0 and overalhealth.get('data') is not None and 'psu' in overalhealth.get(
                    'data'):
                if overalhealth.get('data').get('psu') == 'na':
                    psu_Info.OverallHealth('Absent')
                elif overalhealth.get('data').get('psu').lower() == 'info':
                    psu_Info.OverallHealth('OK')
                else:
                    psu_Info.OverallHealth(overalhealth.get('data').get('psu').capitalize())
            else:
                psu_Info.OverallHealth(None)
            psu_allInfo = res.get('data')
            psu_Info.PsuPresentTotalPower(psu_allInfo.get('present_power_reading', None))
            # 2023年3月27日
            rate_power = psu_allInfo.get('rated_power', 'N/A')
            if rate_power != "N/A":
                psu_Info.PsuRatedPower(psu_allInfo.get('rated_power', 'N/A'))
            psu_Info.PsuStatus(status_dict.get(psu_allInfo.get('power_supplies_redundant', 0)))
            temp = psu_allInfo.get('power_supplies', [])
            size = len(temp)
            Num = IpmiFunc.getM6DeviceNumByIpmi(client, '0x00')
            if Num and Num.get('code') == 0:
                DevConfNum = Num.get('data').get('DevNum')
                psu_Info.Maximum(DevConfNum)
            else:
                psu_Info.Maximum(size)
            for i in range(size):
                psu = PSUSingleBean()
                if temp[i].get('present') == 1:
                    # 在位
                    psu.Id(temp[i].get('id', None))
                    psu.CommonName('PSU' + str(temp[i].get('id')))
                    psu.Location('Chassis')
                    psu.Model(temp[i].get('model', None))
                    psu.Manufacturer(temp[i].get('vendor_id', None))
                    psu.Protocol('PMBus')
                    psu.PowerOutputWatts(temp[i].get('ps_out_power') if 'ps_out_power' in temp[i] else None)
                    psu.InputAmperage(
                        temp[i].get('ps_in_current') if 'ps_in_current' in temp[i] else None)
                    if 'ps_fan_status' in temp[i]:
                        psu.ActiveStandby(temp[i].get('ps_fan_status'))
                    else:
                        psu.ActiveStandby(None)
                    psu.OutputVoltage(temp[i].get('ps_out_volt') if 'ps_out_volt' in temp[i] else None)
                    psu.PowerInputWatts(temp[i].get('ps_in_power') if 'ps_in_power' in temp[i] else None)
                    psu.OutputAmperage(
                        temp[i].get('ps_out_current') if 'ps_out_current' in temp[i] else None)
                    psu.PartNumber(None if temp[i].get('part_num', None) == '' else temp[i].get('part_num', None))
                    psu.PowerSupplyType(temp[i].get('input_type', 'Unknown'))
                    psu.LineInputVoltage(temp[i].get('ps_in_volt') if 'ps_in_volt' in temp[i] else None)
                    # psu.PowerCapacityWatts(temp[i].get('ps_out_power_max', None))
                    # 2023年3月27日
                    psu.PowerCapacityWatts(temp[i].get('rated_power', None))
                    psu.FirmwareVersion(None if temp[i].get('fw_ver', None) == '' else temp[i].get('fw_ver', None))
                    psu.SerialNumber(temp[i].get('serial_num', None))

                    if "temperature" in temp[i]:
                        psu.Temperature(temp[i].get('temperature', None))
                    else:
                        psu.Temperature(temp[i].get('psu_max_temperature', None))
                    if 'status' in temp[i]:
                        psu.Health(
                            'OK' if temp[i].get('status').upper() == 'OK' else temp[i].get('status').capitalize())
                    else:
                        if 'power_status' in temp[i]:
                            psu.Health('OK' if temp[i].get('power_status') == 0 else 'Critical')
                        else:
                            flag = 0
                            psu.Health(None)
                    psu.State('Enabled')
                    psu.ManufatureDate(temp[i].get('mfr_date', None))
                else:
                    psu.Id(temp[i].get('id', 0))
                    psu.CommonName('PSU' + str(temp[i].get('id')))
                    psu.Location('Chassis')
                    psu.State('Absent')
                List.append(psu.dict)
            psu_Info.PSU(List)
            psu_return.State('Success')
            psu_return.Message([psu_Info.dict])
        else:
            psu_return.State('Failure')
            psu_return.Message(['get psu info failed, ' + res.get('data')])

        RestFunc.logout(client)
        return psu_return

    def getSystemLockdownMode(self, client, args):
        res = ResultBean()
        headers = RestFunc.login_M6(client)
        if headers == {}:
            res.State("Failure")
            res.Message("login error, please check username/password/host/port")
            return res
        client.setHearder(headers)
        result = RestFunc.getSystemLockdownMode(client)
        if result.get('code') == 0 and result.get('data') is not None:
            status_dict = {
                0: "Close",
                1: "Open"
            }
            status = status_dict.get(result['data'].get('lock_status', -1), 'Unknown')
            res.State('Success')
            res.Message(status)
        else:
            res.State("Failure")
            res.Message(result.get('data'))
        RestFunc.logout(client)
        return res

    def setSystemLockdownMode(self, client, args):
        res = ResultBean()
        headers = RestFunc.login_M6(client)
        if headers == {}:
            res.State("Failure")
            res.Message("login error, please check username/password/host/port")
            return res
        client.setHearder(headers)
        get_result = RestFunc.getSystemLockdownMode(client)
        if get_result.get('code') == 0 and get_result.get('data') is not None:
            status = get_result['data'].get('lock_status', -1)
            if status == -1:
                res.State("Failure")
                res.Message("Incorrect return format, cannot find 'lock_status'.")
            elif (status == 1 and args.status == "open") or (status == 0 and args.status == 'close'):
                res.State("Failure")
                res.Message("Mode status already {0}, no setting required.".format(str(args.status)))
            else:
                status_dict = {
                    'close': 0,
                    'open': 1
                }
                data = {
                    "lock_status": status_dict.get(args.status)
                }
                result = RestFunc.setSystemLockdownMode(client, data)
                if result.get('code') == 0:
                    res.State("Success")
                    res.Message("")
                else:
                    res.State("Failure")
                    res.Message(str(result.get('data', '')))
        else:
            res.State("Failure")
            res.Message("get mode status failed.")
        RestFunc.logout(client)
        return res

    def gethdddisk(self, client, args):
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        result = ResultBean()
        hdd_info = RestFunc.getHddBMCByRest(client)
        if hdd_info == {}:
            result.State('Failure')
            result.Message(['get on board disk info failed'])
        elif hdd_info.get('code') == 0 and hdd_info.get('data') is not None:
            hdd_data = hdd_info.get('data')
            hdd_list = []
            for item in hdd_data:
                hdd_dict = collections.OrderedDict()
                if "id" in item:
                    hdd_dict['ID'] = item['id']
                if "present" in item:
                    if item['present'] == 1:
                        hdd_dict['PresentStatus'] = "Yes"
                    else:
                        hdd_dict['PresentStatus'] = "No"
                if "enable" in item:
                    if item['enable'] == 1:
                        status = "OK"
                    else:
                        status = "No"
                    hdd_dict['Status'] = status
                if "capacity" in item:
                    hdd_dict['Capacity(GB)'] = item['capacity']
                if "model" in item:
                    hdd_dict['Model'] = str(item['model']).strip()
                if "SN" in item:
                    hdd_dict['SN'] = str(item['SN']).strip()
                if "firmware" in item:
                    hdd_dict['Firmware'] = str(item['firmware']).strip()
                if "location" in item:
                    hdd_dict['Location'] = str(item['location']).strip()
                if "manufacture" in item:
                    hdd_dict['Manufacture'] = str(item['manufacture']).strip()
                if "capablespeed" in item:
                    # 比M6多最大速率字段
                    hdd_dict['CapableSpeed'] = str(item['capablespeed']).strip()
                hdd_list.append(hdd_dict)
            result.State("Success")
            result.Message(hdd_list)
        else:
            result.State("Failure")
            result.Message(["get hard disk info error, error info: " + str(hdd_info.get('data'))])
        RestFunc.logout(client)
        return result

    def addldisk(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(
                ["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        try:
            result = createVirtualDrive(client, args)
        except BaseException:
            RestFunc.logout(client)
        RestFunc.logout(client)
        return result

    # 获取电源还原设置
    def getpowerrestore(self, client, args):
        res = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(
                ["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        policy_dict = {
            2: 'Always Power On',
            0: 'Always Power Off',
            1: 'Restore Last Power State',
            3: 'UnKnown'}
        policy_rest = RestFunc.getPowerPolicyByRest_m7(client)
        if policy_rest.get('code') == 0 and policy_rest.get(
                'data') is not None:
            policy_serult = policy_rest['data']
            JSON = {}
            JSON['policy'] = policy_dict.get(
                policy_serult.get('power_policy', 3), 'UnKnown')
            res.State('Success')
            res.Message([JSON])
        else:
            res.State("Failure")
            res.Message(["get power restore failed"])
        RestFunc.logout(client)
        return res

    # 设置电源还原设置
    # action: on off restore
    # return
    def setpowerrestore(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login_M6(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(
                ["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        res = {}
        policy_dict = {'on': 2, 'off': 0, 'restore': 1}
        action = policy_dict.get(args.option, None)
        if action is None:
            res['State'] = -1
            res['Data'] = " parameter is invalid"
        count = 0
        while True:
            policy_rest = RestFunc.setPowerPolicyByRest_m7(client, action)
            if policy_rest['code'] == 0 and policy_rest['data'] is not None:
                policy_serult = policy_rest['data']
                if policy_serult is not None and 'power_command' in policy_serult:
                    res['State'] = 0
                    res['Data'] = 'set power policy success'
                    break
                else:
                    if count == 0:
                        count += 1
                        continue
                    res['State'] = -1
                    res['Data'] = 'set power policy failed'
                    break
            else:
                if count == 0:
                    count += 1
                    continue
                res['State'] = -1
                res['Data'] = 'request failed'
                break
        if res['State'] == 0:
            result.State('Success')
        else:
            result.State('Failure')
        result.Message(res['Data'])
        RestFunc.logout(client)
        return result

    def getbootimage(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def setbootimage(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def collectblackbox(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def getpowerconsumption(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def getpsupeak(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def getthreshold(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def setthreshold(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def clearauditlog(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def clearsystemlog(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def setnetworkbond(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def getnetworkbond(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def getnetworklink(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def setnetworklink(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def setpsupeak(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M7 model does not support this feature.'])
        return result

    def getpreserveconfig(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M6 model does not support this feature.'])
        return result

    def preserveconfig(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The M6 model does not support this feature.'])
        return result


def createVirtualDrive(client, args):
    result = ResultBean()
    ctrl_id_name_dict = {}
    ctrl_id_list = []
    ctrl_type_dict = {
        "LSI": [],
        "PMC": [],
        "MV": []
    }
    res = RestFunc.getRaidCtrlInfo(client)
    if res.get('code') == 0 and res.get('data') is not None:
        ctrls = res.get('data')
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
        result.State("Failure")
        result.Message(["ctrl Information Request Fail!" + res.get('data')])
        return result
    if ctrl_id_list == []:
        result.State("Failure")
        result.Message(["No raid controller!"])
        return result

    ctrl_list_dict = {}
    pds = {}
    res = RestFunc.getPhysicalDiskInfo(client)
    if res.get('code') == 0 and res.get('data') is not None:
        pds = res.get('data')
        for pd in pds:
            if pd['ControllerName'] not in ctrl_list_dict:
                ctrl_list_dict[pd['ControllerName']] = []
            ctrl_list_dict[pd['ControllerName']].append(pd['DeviceID'])
    else:
        result.State("Failure")
        result.Message(['get physical disk information failed!' + res.get('data')])
        return result
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
                if pd.get("ControllerName") == ctrl_id_name_dict.get(ctrlid):
                    LSI_flag = True
                    pdiskDict = collections.OrderedDict()
                    pdiskDict['Slot Number'] = pd.get("SlotNum", pd.get("slotNum"))
                    pdiskDict['Drive Name'] = pd.get("Name")
                    if "InterfaceType" in pd:
                        pdiskDict['Interface'] = pd.get("InterfaceType")
                    elif "interface_type" in pd:
                        pdiskDict['Interface'] = pd.get("interface_type")
                    else:
                        pdiskDict['Interface'] = None
                    if "MediaType" in pd:
                        pdiskDict['Media Type'] = pd.get("MediaType",)
                    elif "type" in pd:
                        pdiskDict['Media Type'] = pd.get("type")
                    else:
                        pdiskDict['Media Type'] = pd.get("mediaType")
                    if "NONCoercedSize" in pd:
                        pdiskDict['Capacity'] = pd.get("NONCoercedSize")
                    elif "size" in pd:
                        pdiskDict['Capacity'] = pd.get("size")
                    else:
                        pdiskDict['Capacity'] = pd.get("cap")
                    if "FWState" in pd:
                        pdiskDict['Firmware State'] = pd.get("FWState")
                    else:
                        pdiskDict['Firmware State'] = None
                    if "array_number" in pd:
                        pdiskDict['Array Number'] = pd.get("array_number")
                    else:
                        pdiskDict['Array Number'] = None
                    pdiskList.append(pdiskDict)
            raidDict['pdisk'] = pdiskList
            raidList.append(raidDict)
            if not LSI_flag:
                result.State('Failure')
                result.Message(['Device information Not Available (Device absent or failed to get)!'])
                return result
        result.State('Success')
        result.Message(raidList)
        return result
    if args.ctrlId is None:
        result.State('Failure')
        result.Message(["Please input ctrlId parameter!"])
        return result
    elif str(ctrl_id_name_dict.get(args.ctrlId)) in ctrl_type_dict.get('LSI'):
        result = addLogicalDisk(client, args, pds, ctrl_id_name_dict)
    elif str(ctrl_id_name_dict.get(args.ctrlId)) in ctrl_type_dict.get('PMC'):
        result = addPMCLogicalDisk(client, args, pds, ctrl_id_name_dict)
    elif str(ctrl_id_name_dict.get(args.ctrlId)) in ctrl_type_dict.get('MV'):
        result = addMVLogicalDisk(client, args)
    else:
        result.State('Failure')
        result.Message(["No raid controller!"])
    return result


def addLogicalDisk(client, args, pds, ctrl_id_name_dict):
    result = ResultBean()
    if args.ctrlId is None or args.access is None or args.cache is None or args.init is None \
            or args.rlevel is None or args.slot is None or args.size is None or args.r is None or \
            args.w is None or args.io is None or args.select is None or args.vname is None:
        result.State('Failure')
        result.Message(['some parameters are missing'])
        return result

    # args.pd
    if type(args.slot) is str:
        args.pdlist = str(args.slot).split(',')
    elif type(args.slot) is list:
        args.pdlist = args.slot
    else:
        result.State('Failure')
        result.Message(['Invalid slot'])
        return result
    pd_para_len = len(args.pdlist)

    # set raid
    rlevel = None
    if args.rlevel == 1:
        rlevel = False
        if pd_para_len < 2:
            result.State('Failure')
            result.Message(['raid 1 need 2 disks at least'])
            return result
    elif args.rlevel == 5:
        rlevel = False
        if pd_para_len < 3:
            result.State('Failure')
            result.Message(['raid 5 need 3 disks at least'])
            return result
    elif args.rlevel == 6:
        rlevel = False
        if pd_para_len < 4:
            result.State('Failure')
            result.Message(['raid 6 need 4 disks at least'])
            return result
    elif args.rlevel == 10:
        rlevel = True
        if pd_para_len < 4:
            result.State('Failure')
            result.Message(['raid 10 need 4 disks at least'])
            return result
    elif args.rlevel == 50:
        rlevel = True
        if pd_para_len < 6:
            result.State('Failure')
            result.Message(['raid 50 need 6 disks at least'])
            return result
    elif args.rlevel == 60:
        rlevel = True
        if pd_para_len < 8:
            result.State('Failure')
            result.Message(['raid 60 need 8 disks at least'])
            return result

    if 'spanDepth' in args and args.spanDepth is not None:
        if rlevel:
            if args.spanDepth < 2 or args.spanDepth > 8:
                result.State('Failure')
                result.Message(["The RaidLevel {0} input does not match span depth {1}, span depth ranges from 2~8.".format(args.rlevel, args.spanDepth)])
                return result
        else:
            if args.spanDepth != 1:
                result.State('Failure')
                result.Message(["The RaidLevel {0} input does not match span depth {1}, span depth ranges from 1.".format(args.rlevel, args.spanDepth)])
                return result
    else:
        if rlevel:
            args.spanDepth = 2
        else:
            args.spanDepth = 1

    # check select size
    if args.select < 1 or args.select > 100:
        result.State('Failure')
        result.Message(['the select size range in 1 - 100'])
        return result

    raid_dict = {0: "raid0", 1: "raid1", 5: "raid5", 6: "raid6", 10: "raid10"}
    stripsize_dict = {1: "64k", 2: "128k", 3: "256k", 4: "512k", 5: "1024k"}
    access_dict = {1: "Read Write", 2: "Read Only", 3: "Blocked"}
    read_dict = {1: "Always Read Ahead", 2: "No Read Ahead"}
    write_dict = {1: "Write Through", 2: "Write Back with BBU", 3: "Always Write Back"}
    io_dict = {1: "Direct IO", 2: "Cached IO"}
    cache_dict = {1: "Unchanged", 2: "Enabled", 3: "Disabled"}
    init_dict = {1: "No Init", 2: "Quick Init", 3: "Full Init"}

    args.rlevel = raid_dict.get(args.rlevel)
    args.stripSize = stripsize_dict.get(args.size)
    args.access = access_dict.get(args.access)
    args.r = read_dict.get(args.r)
    args.w = write_dict.get(args.w)
    args.io = io_dict.get(args.io)
    args.cache = cache_dict.get(args.cache)
    args.init = init_dict.get(args.init)
    pd_dev_list = []
    for pd_slot_num in args.pdlist:
        for pd in pds:
            if pd['ControllerName'] == ctrl_id_name_dict.get(args.ctrlId) and pd['SlotNum'] == int(pd_slot_num):
                pd_dev_list.append(pd['DeviceID'])
                if pd.get("FWState") != "UNCONFIGURED GOOD":
                    result.State('Failure')
                    result.Message(['The status of physical disk is ' + pd.get("FWState")
                                    + ", logical disk can be created only when its status is UNCONFIGURED GOOD."])
                    return result

    data = {
        "selectSize": args.select,
        "numberPD": len(pd_dev_list),
        "ctrlId": args.ctrlId,
        "raidLevel": args.rlevel,
        "stripSize": args.stripSize,
        "accessPolicy": args.access,
        "readPolicy": args.r,
        "writePolicy": args.w,
        "cachePolicy": args.cache,
        "ioPolicy": args.io,
        "initState": args.init,
        "spanDepth": args.spanDepth
    }
    for i in range(len(pd_dev_list)):
        data["pdDeviceIndex" + str(i)] = pd_dev_list[i]

    res = RestFunc.addLogicalDisk(client, data)
    if res == {}:
        result.State("Failure")
        result.Message(["create virtual drive failed"])
    elif res.get('code') == 0 and res.get('data') is not None:
        result.State('Success')
        result.Message(['create virtual drive successful.'])
    else:
        result.State("Failure")
        result.Message(['create virtual drive failed, ' + str(res.get('data'))])
    return result


# Ascii转十六进制
def ascii2hex(data, length):
    count = length - len(data)
    list_h = []
    for c in data:
        list_h.append(str(hex(ord(c))))
    data = ' '.join(list_h) + ' 0x00' * count
    return data


# 十六进制字符串逆序
def hexReverse(data):
    pattern = re.compile('.{2}')
    time_hex = ' '.join(pattern.findall(data))
    seq = time_hex.split(' ')[::-1]
    data = '0x' + ' 0x'.join(seq)
    return data

