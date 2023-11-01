# -*- coding:utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from inmanage_sdk.interface.CommonM5 import CommonM5
from inmanage_sdk.interface.ResEntity import ResultBean


class CommonA5(CommonM5):

    def clearsystemlog(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def getsystemlog(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def getvirtualmedia(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def setvirtualmedia(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def getmediainstance(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def setmediainstance(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def getconnectmedia(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def setconnectmedia(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def collectblackbox(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def exportbioscfg(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

    def importbioscfg(self, client, args):
        result = ResultBean()
        result.State("Not Support")
        result.Message(['The A5 model does not support this feature.'])
        return result

