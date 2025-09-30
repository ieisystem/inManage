# -*- coding:utf-8 -*-
import sys
import os
import re
import json
from inmanage_sdk.command import IpmiFunc

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
    0xcabc: "Cambricon",
    0x1af4: "Tencent Technology (Shenzhen) Company Limited"
}
PCI_IDS_DEVICE_LIST = {

    0x0014: "MegaRAID Tri-Mode SAS3516",
    0x0016: "MegaRAID Tri-Mode SAS3508",
    0x005b: "MegaRAID SAS 2208",
    0x005d: "MegaRAID SAS-3 3108",
    0x005f: "MegaRAID SAS-3 3008",
    0x0097: "SAS3008 PCI-Express Fusion-MPT SAS-3",
    0x00ac: "SAS3416 Fusion-MPT Tri-Mode I/O Controller Chip (IOC)",
    0x2261: "ISP2722-based 16/32Gb Fibre Channel to PCIe Adapter",
    0xe200: "Lancer-X: LightPulse Fibre Channel Host Adapter",
    0xe300: "Lancer Gen6: LPe32000 Fibre Channel Host Adapter",
    0x5180: "9100 PRO NVMe SSD",
    0x16d7: "BCM57414 NetXtreme-E 10Gb/25Gb RDMA Ethernet Controller",
    0x1003: "MT27500 Family [ConnectX-3]",
    0x1017: "MT27800 Family [ConnectX-5]",
    0x0710: "OneConnect 10Gb NIC (be3)",
    0x1013: "MT27700 Family [ConnectX-4]",
    0x0a03: "SFC9220 10/40G Ethernet Controller",
    0xa804: "NVMe SSD Controller SM961/PM961",
    0x1007: "MT27520 Family [ConnectX-3 Pro]",
    0x1015: "MT27710 Family [ConnectX-4 Lx]",
    0x37d1: "Ethernet Connection X722 for 1GbE",
    0x37d2: "Ethernet Connection X722 for 10GBASE-T",
    0x37d3: "Ethernet Connection X722 for 10GbE SFP+",
    0x0953: "PCIe Data Center SSD",
    0x0a54: "Express Flash NVMe P4510",
    0x10c9: "82576 Gigabit Network Connection",
    0x10f8: "82599 10 Gigabit Dual Port Backplane Connection",
    0x10fb: "82599ES 10-Gigabit SFI/SFP+ Network Connection",
    0x1521: "I350 Gigabit Network Connection",
    0x1528: "Ethernet Controller 10-Gigabit X540-AT2",
    0x1529: "82599 10 Gigabit Dual Port Network Connection with FCoE",
    0x152a: "82599 10 Gigabit Dual Port Backplane Connection with FCoE",
    0x1557: "82599 10 Gigabit Network Connection",
    0x1572: "Ethernet Controller X710 for 10GbE SFP+",
    0x0540: "PBlaze4 NVMe SSD",
    0x0550: "PBlaze5 NVMe SSD",
    # 0xc4: "SAS9305",
    0x028d: "Series 8 12G SAS/PCIe 3",
    0x9361: "MegaRAID SAS 9361-8i",
    0x9371: "MegaRAID SAS 9361-16i",
    0x9364: "MegaRAID SAS 9364-8i",
    0x0017: "MegaRAID Tri-Mode SAS3408",
    0x3090: "SAS9311-8i",
    0x30a0: "SAS9300-8e",
    0x30e0: "SAS9300-8i",
    0x00af: "SAS3408 Fusion-MPT Tri-Mode I/O Controller Chip (IOC)",
    0x00ce: "MegaRAID SAS-3 3316 [Intruder]",
    0x37c8: "PF0 for Intel QuikAssist Technology",
    0x37cc: "10 Gb Ethernet",
    0x37ce: "Ethernet Connection X722 for 10GbE backplane",
    0x37d0: "Ethernet Connection X722 for 10GbE SFP+",
    0x1522: "I350 Gigabit Fiber Network Connection",
    0x1537: "I210 Gigabit Backplane Connection",
    0x1584: "Ethernet Controller XL710 for 40GbE SFP+",
    0x24f0: "Omni-Path HFI Silicon 100 Series [discrete]",
    0x028f: "Smart Storage PQI 12G SAS/PCIe 3",
    0x0100: "MLU100-C3/C4",
    0x13f2: "Tesla M60",
    0x15f8: "Tesla P100 PCIe 16GB",
    0x1b30: "Quadro P6000",
    0x1bb0: "Quadro P5000",
    0x1bb1: "Quadro P4000",
    0x1bb3: "P4 GPU",
    0x1c30: "Quadro P2000",
    0x1db1: "V100-SXM2 GPU",
    0x1db5: "V100-SXM2 GPU",
    0x1b38: "P40 GPU",
    0x1db4: "V100-PCIE GPU",
    # NF5468M5补充
    0x2031: "ISP8324-based 16Gb Fibre Channel to PCI Express Adapter",
    0x2532: "ISP2532-based 8Gb Fibre Channel to PCI Express HBA",
    0x101e: "GK110GL [Tesla K20X]",
    0x101f: "GK110GL [Tesla K20]",
    0x1020: "GK110GL [Tesla K20X]",
    0x1021: "GK110GL [Tesla K20Xm]",
    0x1022: "GK110GL [Tesla K20c]",
    0x1023: "GK110BGL [Tesla K40m]",
    0x1024: "GK110BGL [Tesla K40c]",
    0x1026: "GK110GL [Tesla K20s]",
    0x1027: "GK110BGL [Tesla K40st]",
    0x1028: "GK110GL [Tesla K20m]",
    0x1029: "GK110BGL [Tesla K40s]",
    0x102a: "GK110BGL [Tesla K40t]",
    0x102d: "GK210GL [Tesla K80]",
    0x102e: "GK110BGL [Tesla K40d]",
    0x13bc: "GM107GL [Quadro K1200]",
    0x1431: "GM206GL [Tesla M4]",
    0x13bd: "GM107GL [Tesla M10]",
    0x17fd: "GM200GL [Tesla M40]",
    0x1b06: "GTX1080TI GPU",
    0x1db6: "Tesla V100 PCIE 32G GPU",
    0x15f7: "GP100GL [Tesla P100 PCIe 32GB]",
    0x15f9: "GP100GL [Tesla P100 SXM2 16GB]",
    0xf100: "Saturn-X: LightPulse Fibre Channel Host Adapter",
    0xf180: "LLPSe12002 EmulexSecure Fibre Channel Adapter",
    0x00d1: "HBA 9405W-16i"

}

def restore(client, path_service):
    # 读取
    f = open(path_service, 'r')
    biosInfo = f.read()
    f.close()
    biosJson = json.loads(biosInfo)
    #2022年8月19日 用户很有可能getbios直接写入文件 这里还是自动去一层吧
    if "State" in biosJson and "Message" in biosJson:
        biosJson = biosJson.get("Message")
    return biosJson

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

    
def utoolPrint(quite, print_info):
    if not quite:
        print(print_info)
    
#1.39 改为 GPU/NIC/RAID/HBA/Acceleration

def getDeviceType(var):
    if var == 0:
        return 'Other'
    elif var == 1:
        return 'Mass storage controller'
    elif var == 2:
        return 'NIC'
    elif var == 3:
        return 'GPU'
    elif var == 4:
        return 'Multimedia device'
    elif var == 5:
        return 'Memory controller'
    elif var == 6:
        return 'Bridge device'
    elif var == 7:
        return 'Simple communication controller'
    elif var == 8:
        return 'Base system peripherals'
    elif var == 9:
        return 'input device'
    elif var == 10:
        return 'Docking stations'
    elif var == 11:
        return 'Processors'
    elif var == 12:
        return 'Serial bus controller'
    elif var == 13:
        return 'Wireless controller'
    elif var == 14:
        return 'intelligent I/O controller'
    elif var == 15:
        return 'Satellite communication controllers'
    elif var == 16:
        return 'Encryption/Decryption controllers'
    elif var == 17:
        return 'Data acquisition and signal processing controllers'
    elif var == 18:
        return 'Acceleration'
    elif var == 19:
        return 'Non-Essential Instrumentation'
    elif var == 64:
        return 'Coprocessor'
    elif var == 255:
        return 'Device does not fit in any defines classes'
    else:
        return 'Unknown DeviceType '+str(var)
        
def getDeviceType1(var):
    if var == 0:
        return 'Device was built before Class Code definitions were finalized'
    elif var == 1:
        return 'Mass storage controller'
    elif var == 2:
        return 'Network controller'
    elif var == 3:
        return 'Display controller'
    elif var == 4:
        return 'Multimedia device'
    elif var == 5:
        return 'Memory controller'
    elif var == 6:
        return 'Bridge device'
    elif var == 7:
        return 'Simple communication controller'
    elif var == 8:
        return 'Base system peripherals'
    elif var == 9:
        return 'input device'
    elif var == 10:
        return 'Docking stations'
    elif var == 11:
        return 'Processors'
    elif var == 12:
        return 'Serial bus controller'
    elif var == 13:
        return 'Wireless controller'
    elif var == 14:
        return 'intelligent I/O controller'
    elif var == 15:
        return 'Satellite communication controllers'
    elif var == 16:
        return 'Encryption/Decryption controllers'
    elif var == 17:
        return 'Data acquisition and signal processing controllers'
    elif var == 18:
        return 'Processing accelerators'
    elif var == 19:
        return 'Non-Essential Instrumentation'
    elif var == 64:
        return 'Coprocessor'
    elif var == 255:
        return 'Device does not fit in any defines classes'
    else:
        return 'Unknown DeviceType '+str(var)
    

#type       路径                              路径+文件名
#0          默认文件名                        不校验
#1          报错                              校验文件后缀与defaultname的后缀是否相同
#2          根据后面接口返回修改添加名称          校验文件后缀与defaultname的后缀是否相同
#3          默认文件名                        校验文件后缀与defaultname的后缀是否相同
#x          psn+time+defaultname的后缀        校验文件后缀与defaultname的后缀是否相同
def formatFileurl(client, fileurl, type, defaultname):
    renameflag = False
    if fileurl is None:
        return False, None
    extension = ""
    if "." in defaultname:
        extension = "." + defaultname.split(".")[-1]
        if extension == ".gz":
            if defaultname.split(".")[-2] == "tar":
                extension = ".tar.gz"
    if fileurl == ".":
        file_name = ""
        file_path = os.path.abspath("../util")
        fileurl = os.path.join(file_path, file_name)
    elif fileurl == "..":
        file_name = ""
        file_path = os.path.abspath("..")
        fileurl = os.path.join(file_path, file_name)
    elif re.search("^[C-Zc-z]\:$",fileurl,re.I):
        file_name = ""
        file_path = os.path.abspath(fileurl + "\\")
        fileurl = os.path.join(file_path, file_name)
    else:
        file_name = os.path.basename(fileurl)
        file_path = os.path.dirname(fileurl)
    # 只输入文件名字，则默认为当前路径
    if file_path == "":
        file_path = os.path.abspath("../util")
        fileurl = os.path.join(file_path, file_name)

    # 用户输入路径，则默认文件名dump_psn_time.tar
    if file_name == "":
        renameflag = True
        
        if type == 0:
            file_name = defaultname
        elif type == 1:
            return False, "log name is needed."
        elif type == 2:
           file_name = "dduummpp22change"
        elif type == 3:
           file_name = defaultname
        else:
            psn = "UNKNOWN"
            fru = IpmiFunc.getfruByIpmi(client)
            if fru.get('code') == 0 and fru.get('data') is not None:
                product = fru.get('data')
                psn = product.get('product_serial', "UNKNOWN")
            import time
            struct_time = time.localtime()
            logtime = time.strftime("%Y%m%d-%H%M", struct_time)
            file_name = type + "_" + psn + "_" + logtime + extension
        fileurl = os.path.join(file_path, file_name)
    else:
        renameflag = False
        if type != 0:
            if extension != "":
                p = '\.' + extension[1:] + '$'
                if not re.search(p, file_name, re.I):
                    return False, "Filename should be xxx" + extension
    if not os.path.exists(file_path):
        try:
            os.makedirs(file_path)
        except:
            return False, "can not create path."
    else:
        if os.path.exists(fileurl) and renameflag:
            l = len(extension)
            if l > 1:
                l =  -l
            name_id = 1
            name_new = file_name[:l] + "(1)" + extension
            file_new = os.path.join(file_path, name_new)
            while os.path.exists(file_new):
                name_id = name_id + 1
                name_new = file_name[:l] + "(" + str(name_id) + ")" + extension
                file_new = os.path.join(file_path, name_new)
            fileurl = file_new
    
    return True, fileurl

def repeatFunc(retry, func, *args, **kwargs):
    retryCount = 0
    res = func(*args, **kwargs)
    while retryCount < retry:
        if res == {} or res.get('code') != 0:
            #print(res)
            retryCount = retryCount + 1
            #print("loop:" + str(retryCount))
            import time
            time.sleep(5)
            res = func(*args, **kwargs)
        else:
            return res
    return res


def checkVersion(type, target, current):
    if target == current:
        return True
    else:
        return False

#update

# 获取当前时间
def ftime(ff="%Y-%m-%d %H:%M:%S "):
    try:
        import time
        localtime = time.localtime()
        f_localtime = time.strftime(ff, localtime)
        return f_localtime
    except:
        return ""


# 写日志
def wirte_log(log_path, stage="", state="", note=""):
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
            logfile.write(json.dumps(log_dict, default=lambda o: o.__dict__, sort_keys=True, indent=4,
                                     ensure_ascii=False))
        return True
    except Exception as e:
        return (str(e))


    # 创建目录
def mkdirBeforeFwUpdate(client):
    psn = IpmiFunc.getProductSerial(client)
    logtime = ftime("%Y%m%d%H%M%S")
    dir_name = logtime + "_" + psn
    T6_path = os.path.abspath(__file__)
    interface_path = os.path.split(T6_path)[0]
    root_path = os.path.dirname(interface_path)
    update_path = os.path.join(root_path, "update")
    if not os.path.exists(update_path):
        os.makedirs(update_path)
    update_plog_path = os.path.join(update_path, dir_name)
    if not os.path.exists(update_plog_path):
        os.makedirs(update_plog_path)

    log_path = os.path.join(update_plog_path, "updatelog.txt")
    if not os.path.exists(log_path):
        with open(log_path, 'w') as newlog:
            log_dict = {"log": []}
            newlog.write(str(log_dict))
    return log_path, update_plog_path

def getDeviceName(key):
    key = key.lower()
    if "0x" in key:
        key = int(key, 16)
    else:
        key = int("0x" + key, 16)

    return PCI_IDS_DEVICE_LIST.get(key)



if __name__ == "__main__":
    print('main')
