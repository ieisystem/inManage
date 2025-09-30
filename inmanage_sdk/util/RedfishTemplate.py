# -*- coding:utf-8 -*-
import time

from requests.auth import HTTPBasicAuth
from requests.models import Response
from inmanage_sdk.interface.ResEntity import ResultBean


# 有一个错误则直接返回
def get_for_collection_object(client, url, code=list(range(200, 300)),
                              collection_keys={'key': 'Members', 'sub_key': '@odata.id'}):
    try:
        if client.getHearder():
            response = client.request('GET', url, headers=client.getHearder())
        else:
            response = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode))
        if not response:
            return ResultBean.fail('fail to get object, response is none.')
        elif response.status_code in code:
            members = response.json().get(collection_keys.get('key'))
            result = []
            if isinstance(members, list):
                for member in members:
                    if isinstance(member, dict):
                        if 'sub_key' not in collection_keys.keys():
                            return ResultBean.fail('can not find url')
                        url = member.get(collection_keys.get('sub_key'))
                    else:
                        url = member
                    if str(url).startswith("/"):
                        url = url[1:]
                    if client.getHearder():
                        r = client.request('GET', url, headers=client.getHearder())
                    else:
                        r = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode))
                    if not r:
                        # 目前对于无法访问的member链接直接返回失败
                        return ResultBean.fail('fail to get object, response is none. id: {}'.format(url))
                    elif r.status_code in code:
                        result.append(r.json())
                    else:
                        try:
                            eres = response.json()
                        except:
                            eres = response.content.decode()
                        return ResultBean.fail(str(eres))
            elif isinstance(members, dict):
                if 'sub_key' not in collection_keys.keys():
                    return ResultBean.fail('can not find url')
                url = members.get(collection_keys.get('sub_key'))
                if str(url).startswith("/"):
                    url = url[1:]
                if client.getHearder():
                    r = client.request('GET', url, headers=client.getHearder())
                else:
                    r = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode))
                if not r:
                    return ResultBean.fail(
                        'fail to get object, response is none. id: {}'.format(
                            members.get(collection_keys.get('sub_key'))))
                elif r.status_code in code:
                    result.append(r.json())
                else:
                    try:
                        eres = response.json()
                    except:
                        eres = response.content.decode()
                    return ResultBean.fail(str(eres))
            else:
                return ResultBean.fail("Unknown return format")
            return ResultBean.success(result)
        else:
            try:
                eres = response.json()
            except:
                eres = response.content.decode()
            return ResultBean.fail(str(eres))
    except Exception as e:
        return ResultBean.fail(e)


# 不管单个成功或失败，都执行一遍
def get_for_collection_object_all(client, url, code=list(range(200, 300)),
                                  collection_keys={'key': 'Members', 'sub_key': '@odata.id'}):
    try:
        if client.getHearder():
            response = client.request('GET', url, headers=client.getHearder(), timeout=120)
        else:
            response = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode),timeout=120)
        if not response:
            return ResultBean.fail('fail to get object, response is none.')
        elif response.status_code in code:
            members = response.json().get(collection_keys.get('key'))
            result = []
            if isinstance(members, list):
                for member in members:
                    if isinstance(member, dict):
                        if 'sub_key' not in collection_keys.keys():
                            return ResultBean.fail('can not find url')
                        url = member.get(collection_keys.get('sub_key'))
                    else:
                        url = member
                    if str(url).startswith("/"):
                        url = url[1:]
                    if client.getHearder():
                        r = client.request('GET', url, headers=client.getHearder(), timeout=120)
                    else:
                        r = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode),
                                           timeout=120)
                    if not r:
                        # 显示能获取到的member，无法获取的进一步处理
                        result.append(ResultBean.fail('fail to get object, response is none. id: {}'.format(url)))
                    elif r.status_code in code:
                        result.append(ResultBean.success(r.json()))
                    else:
                        try:
                            eres = response.json()
                        except:
                            eres = response.content.decode()
                        result.append(ResultBean.fail(str(eres)))
            elif isinstance(members, dict):
                if 'sub_key' not in collection_keys.keys():
                    return ResultBean.fail('can not find url')
                url = members.get(collection_keys.get('sub_key'))
                if str(url).startswith("/"):
                    url = url[1:]
                if client.getHearder():
                    r = client.request('GET', url, headers=client.getHearder(), timeout=120)
                else:
                    r = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode),timeout=120)
                if not r:
                    result.append(ResultBean.fail('fail to get object, response is none. id: {}'.
                                                  format(members.get(collection_keys.get('sub_key')))))
                elif r.status_code in code:
                    result.append(ResultBean.success(r.json()))
                else:
                    try:
                        eres = response.json()
                    except:
                        eres = response.content.decode()
                    result.append(ResultBean.fail(str(eres)))
            else:
                return ResultBean.fail("Unknown return format")
            return ResultBean.success(result)
        else:
            try:
                eres = response.json()
            except:
                eres = response.content.decode()
            return ResultBean.fail(str(eres))
    except Exception as e:
        return ResultBean.fail(e)


# 多个不相关的URL列表获取
def get_for_object(client, url, code=None):
    try:
        result = {}
        if code is None:
            code = [list(range(200, 300))] * len(url)
        if isinstance(url, list) and isinstance(code, list) and url and code:
            for u, c in zip(url, code):
                if client.getHearder():
                    response = client.request('GET', u, headers=client.getHearder())
                else:
                    response = client.request('GET', u, auth=HTTPBasicAuth(client.username, client.passcode))
                if not response:
                    result[u] = ResultBean.fail('fail to get object, response is none.')
                elif response.status_code in c:
                    result[u] = ResultBean.success(response.json())
                else:
                    try:
                        eres = response.json()
                    except:
                        eres = response.content.decode()
                    result[u] = ResultBean.fail(str(eres))
            return ResultBean.success(result)
        else:
            return ResultBean.fail(
                'fail to get object, please check url and code. url: {}, code: {}'.format(str(url), str(code)))
    except RedfishSessionException as e:
        if not e.message:
            return ResultBean.fail('fail to open session, response is none')
        elif isinstance(e.message, Response):
            return ResultBean.fail(e.message)
        else:
            return ResultBean.fail(e)
    except Exception as e:
        return ResultBean.fail(e)


# 单个URL获取, eg: 'redfish/v1/AccountService/Accounts'
def get_for_object_single(client, url, code=list(range(200, 300))):
    try:
        result = {}
        if url and code:
            if client.getHearder():
                response = client.request('GET', url, headers=client.getHearder(), timeout=50)
            else:
                response = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode), timeout=50)
            if response.status_code in code:
                try:
                    result = ResultBean.success(response.json())
                except:
                    result = ResultBean.success(response)
            else:
                try:
                    eres = response.json()
                except:
                    eres = response.content.decode()
                result = ResultBean.fail(str(eres))
            return result
        else:
            return ResultBean.fail(
                'fail to get object, please check url and code. url: {}, code: {}'.format(str(url), str(code)))
    except RedfishSessionException as e:
        if not e.message:
            return ResultBean.fail('fail to open session, response is none')
        elif isinstance(e.message, Response):
            return ResultBean.fail(e.message)
        else:
            return ResultBean.fail(e)
    except Exception as e:
        return ResultBean.fail(e)


def get_for_object_return_raw(client, url, code=list(range(200, 300))):
    try:
        result = {}
        if url and code:
            if client.getHearder():
                response = client.request('GET', url, headers=client.getHearder(), timeout=50)
            else:
                response = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode), timeout=50)
            if response.status_code in code:
                result = ResultBean.success(response)
            else:
                try:
                    eres = response.json()
                except:
                    eres = response.content.decode()
                result = ResultBean.fail(str(eres))
            return result
        else:
            return ResultBean.fail(
                'fail to get object, please check url and code. url: {}, code: {}'.format(str(url), str(code)))
    except RedfishSessionException as e:
        if not e.message:
            return ResultBean.fail('fail to open session, response is none')
        elif isinstance(e.message, Response):
            return ResultBean.fail(e.message)
        else:
            return ResultBean.fail(e)
    except Exception as e:
        return ResultBean.fail(e)


def get_for_object_with_header(client, url, code=list(range(200, 300))):
    try:
        result = {}
        if url and code:
            response = client.request('GET', url, headers=client.getHearder())
            if not response:
                result = ResultBean.fail('fail to get object, response is none.')
            elif response.status_code in code:
                result = ResultBean.success(response.json())
            else:
                try:
                    eres = response.json()
                except:
                    eres = response.content.decode()
                result = ResultBean.fail(str(eres))
            return result
        else:
            return ResultBean.fail(
                'fail to get object, please check url and code. url: {}, code: {}'.format(str(url), str(code)))
    except RedfishSessionException as e:
        if not e.message:
            return ResultBean.fail('fail to open session, response is none')
        elif isinstance(e.message, Response):
            return ResultBean.fail(e.message)
        else:
            return ResultBean.fail(e)
    except Exception as e:
        return ResultBean.fail(e)


# 循环获取进度 M7 redfish
def get_for_object_cycle(client, url, count, func, code=list(range(200, 300))):
    try:
        n = 0
        none_c = 0
        error_c = 0
        error_message = ""
        while n < count:
            if none_c > 3:
                return ResultBean.fail("fail to get object, response is none.")
            if error_c > 3:
                return ResultBean.fail(error_message)
            if client.getHearder():
                response = client.request('GET', url, headers=client.getHearder())
            else:
                response = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode))
            if response is None:
                none_c += 1
            elif response.status_code in code:
                if func(response.json()):
                    return ResultBean.success("get completed.")
            else:
                error_c += 1
                error_message = response
            time.sleep(5)
        if n >= count:
            return ResultBean.fail("number of times exceeded")
    except Exception as e:
        return ResultBean.fail(e)


# 循环获取进度(for kunpeng)
# True complete 升级成功,正常退出
# True response.json() 升级失败,正常退出
# False timeout 超时退出
# False e 异常退出// 一般是bmc断了
def cycle_get(client, url, timeout, retrynum, func, code=list(range(200, 300))):
    import time

    stime = time.time()
    error_c = 0
    while True:
        ctime = time.time()
        if ctime - stime > timeout:
            return ResultBean.fail("timeout")
        if error_c > retrynum and retrynum > -1:
            return ResultBean.fail(error_message)
        try:
            error_message = ""
            if client.getHearder():
                response = client.request('GET', url, headers=client.getHearder(), logflag=True)
            else:
                response = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode), logflag=True)
            if response.status_code in code:
                cycleres = func(response.json())
                if cycleres is None:
                    continue
                elif cycleres == "complete":
                    return ResultBean.success("complete")
                elif cycleres == "warning":
                    return ResultBean.success(str(response.json()))
            else:
                error_c += 1
                error_message = response

        except Exception as e:
            error_c += 1
            error_message = str(e)
        time.sleep(5)


# 循环获取进度 成功推出0；异常退出1；继续执行2
# func 返回 0 msg/1 msg/2 msg
def cycle_get_task(client, url, timeout, retrynum, func, code=list(range(200, 300))):
    import time

    stime = time.time()
    error_c = 0
    while True:
        ctime = time.time()
        if ctime - stime > timeout:
            return ResultBean.fail("timeout")
        if error_c > retrynum and retrynum > -1:
            return ResultBean.fail(error_message)
        try:
            error_message = ""
            if client.getHearder():
                response = client.request('GET', url, headers=client.getHearder(), logflag=True)
            else:
                response = client.request('GET', url, auth=HTTPBasicAuth(client.username, client.passcode), logflag=True)
            if response.status_code in code:
                status, msg = func(response.json())
                if status == 0:
                    return ResultBean.success(msg)
                elif status == 1:
                    return ResultBean.fail(msg)
                elif status == 2:
                    continue
                else:
                    continue
            else:
                error_c += 1
                error_message = response

        except Exception as e:
            error_c += 1
            error_message = str(e)
        time.sleep(5)


def post_for_object(client, postBody):
    url = postBody.get("url")
    # auth = patchBody.get("auth")
    # header = patchBody.get("header")
    myjson = postBody.get("json")
    mydata = postBody.get("data")
    myfile = postBody.get("file")
    # func = postBody.get("func")
    code = postBody.get("code")
    timeout = postBody.get("timeout")
    header = postBody.get("header")
    if not header:
        header = client.getHearder()
    if not code:
        code = list(range(200, 300))
    try:
        # print(myjson)
        # return ResultBean.success("ok")
        if header:
            response = client.request('POST', url, headers=header, json=myjson, data=mydata, timeout=timeout, files=myfile)
        else:
            response = client.request('POST', url, auth=HTTPBasicAuth(client.username, client.passcode), json=myjson, data=mydata, timeout=timeout, files=myfile)
        if response is None:
            return ResultBean.fail("response is none")
        elif response.status_code in code:
            return ResultBean.success(response)
        else:
            try:
                eres = response.json()
            except:
                eres = response.content.decode()
            return ResultBean.fail(str(eres))
    except Exception as e:
        return ResultBean.fail(e)


def delete_for_object(client, url, code=list(range(200, 300)), delBody=None):
    try:
        if delBody is not None:
            myjson = delBody.get("json")
            mydata = delBody.get("data")
            timeout = delBody.get("timeout")
            if client.getHearder():
                response = client.request('DELETE', url, headers=client.getHearder(),
                                          json=myjson, data=mydata, timeout=timeout)
            else:
                response = client.request('DELETE', url, auth=HTTPBasicAuth(client.username, client.passcode), json=myjson, data=mydata, timeout=timeout)
        else:
            if client.getHearder():
                response = client.request('DELETE', url, headers=client.getHearder())
            else:
                response = client.request('DELETE', url, auth=HTTPBasicAuth(client.username, client.passcode))
        if response is None:
            return ResultBean.fail("response is none")
        elif response.status_code in code:
            return ResultBean.success(response)
        else:
            try:
                eres = response.json()
            except:
                eres = response.content.decode()
            return ResultBean.fail(str(eres))
    except Exception as e:
        return ResultBean.fail(e)


# flag 判断   0 需要设置， 1 不需要设置，2 输出报错信息
def patch_multi_for_object(client, url, func, code=None):
    try:
        result = {}
        if code is None:
            code = [list(range(200, 300))] * len(url)
        for u, c, f in zip(url, code, func):
            if client.getHearder():
                etag_response = client.request('GET', u, headers=client.getHearder())
            else:
                etag_response = client.request('GET', u, auth=HTTPBasicAuth(client.username, client.passcode))
            if etag_response is not None and etag_response.status_code in c and 'Etag' in etag_response.headers:
                headers = {}
                headers['If-Match'] = etag_response.headers['Etag']
                headers.update(client.getHearder())
                flag, data = f(etag_response)
                if flag == 0:
                    patch_response = client.request("PATCH", u, headers=headers, json=data, auth=HTTPBasicAuth(client.username, client.passcode))
                    if patch_response.status_code in c:
                        result[u] = ResultBean.success(patch_response)
                    else:
                        try:
                            eres = patch_response.json()
                        except:
                            eres = patch_response.content.decode()
                        result[u] = ResultBean.fail(str(eres))
                elif flag == 2:
                    result[u] = ResultBean.fail(data)
            else:
                try:
                    eres = etag_response.json()
                except:
                    eres = etag_response.content.decode()
                result[u] = ResultBean.fail(str(eres))
        return result
    except Exception as e:
        return ResultBean.fail(e)


def patch_for_object_no_get(client, patchBody):
    url = patchBody.get("url")
    data = patchBody.get("json")
    code = patchBody.get("code")
    if not code:
        code = list(range(200, 300))
    try:
        if client.getHearder():
            patch_response = client.request("PATCH", url, headers=client.getHearder(), json=data)
        else:
            patch_response = client.request("PATCH", url,
                                        auth=HTTPBasicAuth(client.username, client.passcode), json=data)
        if patch_response.status_code in code:
            return ResultBean.success(patch_response)
        else:
            return ResultBean.fail(str(patch_response.content.decode()))
    except RedfishSessionException as e:
        if not e.message:
            return ResultBean.fail('fail to open session, response is none')
        elif isinstance(e.message, Response):
            return ResultBean.fail(e.message)
    except Exception as e:
        return ResultBean.fail(e)


def patch_for_object(client, patchBody):
    url = patchBody.get("url")
    # auth = patchBody.get("auth")
    # header = patchBody.get("header")
    data = patchBody.get("json")
    # mydata = patchBody.get("data")
    func = patchBody.get("func")
    code = patchBody.get("code")
    etagurl = patchBody.get("etagurl", url)
    if not code:
        code = list(range(200, 300))
    try:
        # with OpenSession(client) as session:
        # headers = {'X-Auth-Token': session.login_headers['X-Auth-Token']}
        if client.getHearder():
            etag_response = client.request('GET', etagurl, headers=client.getHearder())
        else:
            etag_response = client.request('GET', etagurl, auth=HTTPBasicAuth(client.username, client.passcode))
        if etag_response.status_code not in code:
            try:
                eres = etag_response.json()
            except:
                eres = etag_response.content.decode()
            return ResultBean.fail(str(eres))
        headers = {}
        if 'Etag' in etag_response.headers:
            headers['If-Match'] = etag_response.headers['Etag']
            headers['Content-Type'] = 'application/json'
        headers.update(client.getHearder())
        # else:
        #     return ResultBean.fail(etag_response)
        if func:
            result = func(data, etag_response)
            if not result.State:
                return result
            else:
                data = result.Message
        # print(data)
        # return ResultBean.success("ok")
        patch_response = client.request("PATCH", url, headers=headers,
                                        auth=HTTPBasicAuth(client.username, client.passcode), json=data)
        if patch_response.status_code in code:
            return ResultBean.success(patch_response)
        else:
            return ResultBean.fail(str(patch_response.content.decode()))
    except RedfishSessionException as e:
        if not e.message:
            return ResultBean.fail('fail to open session, response is none')
        elif isinstance(e.message, Response):
            return ResultBean.fail(e.message)
    except Exception as e:
        return ResultBean.fail(e)


def patch_for_object_by_id(client, url, code, id, *collection_keys):
    with OpenSession(client) as session:
        headers = {'X-Auth-Token': session.login_headers['X-Auth-Token']}
        response = session.client.request('GET', url, headers=headers)
        if response.status_code in code:
            if not collection_keys:
                collection_keys = ['Member']
            members = response.json()[collection_keys[0]]


class OpenSession:

    def __init__(self, client, login_url=None, logout_url=None):
        self.client = client
        self.login_url = login_url
        self.logout_url = logout_url

    def __enter__(self):
        data = {
            'UserName': str(self.client.username),
            'Password': str(self.client.passcode),
            'SessionTimeOut': '600'
        }
        headers = {'Content-Type': 'application/json'}
        try:
            response = self.client.request('POST', 'redfish/v1/SessionService/Sessions', headers=headers, json=data) \
                if not self.login_url else self.client.request('POST', self.login_url, headers=headers, json=data)
        except Exception:
            raise
        if response and response.status_code == 201:
            self.login_headers = {'X-Auth-Token': response.headers['X-Auth-Token']}
            self.login_id = response.json()['Id']
            return self
        else:
            raise RedfishSessionException(response)

    def __exit__(self, exc_type, exc_val, exc_tb):
        headers = {'X-Auth-Token': self.login_headers['X-Auth-Token']}
        try:
            if not self.logout_url:
                self.client.request("DELETE", "redfish/v1/SessionService/Sessions/" + str(self.login_id),
                                    headers=headers)
            else:
                self.client.request("DELETE", self.logout_url + str(self.login_id), headers=headers)
        except:
            pass
        if exc_type:
            return False


class RedfishSessionException(Exception):
    def __int__(self, message):
        self.message = message
