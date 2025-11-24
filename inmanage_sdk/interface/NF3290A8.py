# -*- coding:utf-8 -*-
import os

from inmanage_sdk.interface.NF3290M8 import NF3290M8
from ResEntity import ResultBean
from inmanage_sdk.util import RedfishTemplate
from inmanage_sdk.command import IpmiFunc

class NF3290A8(NF3290M8):

    def _get_xml_file(self, args):
        xml_path = os.path.join(IpmiFunc.command_path, "bios") + os.path.sep
        return xml_path + 'NF5468A8.xml'

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
                res.Message([help_list])
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
