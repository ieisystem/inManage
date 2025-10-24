# -*- coding:utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import json
import signal
from importlib import import_module
from inmanage_sdk.command import RestFunc
import time
import collections
try:
    from inmanage_sdk.util import configUtil, HostTypeJudge, parameterConversion, RequestClient

    INMANAGE_EXIST = True
except ImportError:
    INMANAGE_EXIST = False
sys.path.append(os.path.join(sys.path[0], "interface"))
current_time = time.strftime(
    '%Y-%m-%d   %H:%M:%S',
    time.localtime(
        time.time()))
__version__ = '1.4.1'


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


def main(params):

    def logout(signum, frame):
        if hasattr(client, "header"):
            RestFunc.logout(client)

    signal.signal(signal.SIGINT, logout)
    signal.signal(signal.SIGTERM, logout)
    signal.signal(signal.SIGABRT, logout)
    # windows下注释下面两行
    signal.signal(signal.SIGHUP, logout)
    signal.signal(signal.SIGQUIT, logout)
    res = {}
    if not INMANAGE_EXIST:
        res['State'] = "Failure"
        res['Message'] = ["Please install the requests library"]
        return res
    param = parameterConversion.getParam(params)
    args = dict_to_object(param)
    args.port = None
    configutil = configUtil.configUtil()
    if args.subcommand is not None and args.subcommand == 'support_model':
        res['State'] = "Success"
        res['Message'] = configutil.getModelSupport()
        return res
    # 使用fru获取机型信息
    hostTypeClient = HostTypeJudge.HostTypeClient()
    result = hostTypeClient.getProductNameByIPMI(args)
    if result['State'] != "Success":
        res['State'] = result['State']
        res['Message'] = result['Message']
        return res
    else:
        data = result['Message']
        impl = data['impl']
        platform = data['platform']
    module_impl = 'inmanage_sdk.interface.' + impl
    obj = import_module(module_impl)
    targetclass = getattr(obj, impl)
    obj = targetclass()
    if args.subcommand is None:
        res['State'] = "Failure"
        res['Message'] = ["please input a subcommand"]
        return res
    targetMed = getattr(obj, args.subcommand)
    client = RequestClient.RequestClient()
    client.setself(
        args.host,
        args.username,
        args.passcode,
        platform,
        args.port,
        'lanplus')
    try:
        resultJson = targetMed(client, args)
    except Exception as e:

        res['State'] = "Failure"
        res['Message'] = ["Error occurs, request failed..."]
        return res
    sortedRes = collections.OrderedDict()
    sortedRes["State"] = resultJson.State
    sortedRes["Message"] = resultJson.Message
    return sortedRes


class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


def dict_to_object(dictobj):
    if not isinstance(dictobj, dict):
        return dictobj
    inst = Dict()
    for k, v in dictobj.items():
        if k == 'password':
            k = 'passcode'
        inst[k] = dict_to_object(v)
    return inst
