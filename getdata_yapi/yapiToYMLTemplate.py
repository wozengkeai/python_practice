# -*- coding: utf-8 -*-
# @Time : 2021/8/20 11:33
# @Author : zengxiaoyan
# @File : yapiToYMLTemplate.py
import datetime
import json
import logging
import time
import os
import io
import yaml

import jmespath
from common import utils
import requests

class Yapi(object):

    def __init__(self, email, password, group_id):

        self.email = email
        self.password = password
        self.group_id = group_id
        self.interface_datas = []
        # self.project_name = ""
        self.title = ""
        self.base_url = 'http://47.97.5.102:36666'
        self.s = requests.session()
        headers = {'Content-Type': 'application/json;charset=UTF-8',}
        data = {
            'email': self.email,
            'password': self.password,
            }
        self.s.post(self.base_url + '/api/user/login', headers=headers, json=data)

    # ##获取所有项目信息
    def get_project_listdata(self,projectName):
        getdata = {'group_id': self.group_id, 'page': '1', 'limit': '500000'}
        url = self.base_url + '/api/project/list'
        project_listdata = self.s.get(url, params=getdata).json().get('data').get('list')
        project_info = {}
        for i in range(0, len(project_listdata)):
            project_name = project_listdata[i].get('name')
            project_id = project_listdata[i].get('_id')
            project_info[project_name] = project_id
        projectId = project_info[projectName]
        return projectId


    # 获取对应项目的所有接口
    def get_interface_listdata(self,project_name):
        project_id = self.get_project_listdata(project_name)
        getdata = {'page': '1', 'limit': '500000', 'project_id': project_id}
        url = self.base_url + '/api/interface/list'
        interface_listdata = self.s.get(url, params=getdata).json().get('data').get('list')
        for i in range(0, len(interface_listdata)):
            interface_id = interface_listdata[i].get('_id')
            self.get_interface_data(interface_id)



    def dictget(self,dict1):
        """
        递归遍历多层嵌套的字典
        :param dict1:
        :return:
        """
        for k,v in dict1.items():
            if type(v) is dict and v["type"] == "object":
                v = v["properties"]
                dict1[k] = v
                # print(k)
                self.dictget(v)
            elif type(v) is dict and v["type"] == "array":
                v = v['items']
                dict1[k] = v
                if type(v) is dict and v['type'] == 'object':
                    v = v["properties"]
                    dict1[k] = v
                    self.dictget(v)
                elif v['type'] == "array" :
                    v = v['items']
                    self.dictget(v)
                else:
                    dict1[k] = []
                # self.dictget(v)
            else:
                v = ''
                dict1[k] = v
        return dict1



    def get_interface_data(self, interface_id):
        """
        获取模板内参数值
        :param interface_id:
        :return:
        """

        getdata = {'id': interface_id}
        url = self.base_url + '/api/interface/get'
        interface_data = self.s.get(url, params=getdata).json()

        req_body = interface_data.get("data").get("req_body_other")
        if req_body:
            self.req_body_other = eval(req_body).get("properties")
        else:
            #存在不需要传参的接口
            self.req_body_other = {}
        self.jsondata = self.dictget(self.req_body_other)

        self.req_headers = interface_data.get("data").get("req_headers")
        #URL
        self.path = interface_data.get("data").get("path")
        #请求方法
        self.method = interface_data.get("data").get("method")
        self.title = interface_data.get("data").get("title")
        #请求参数
        self.aa = {"json": self.jsondata}
        self.yamldata = yaml.dump(self.aa, allow_unicode=True, default_flow_style=False, indent=8)

        #生成模板
        self.generate_api()




    # 自定义模板
    def generate_api(self):
        case = f"""name: {self.title}
base_url:
variables:
    currtime: ${{make_time()}}
    uuid: ${{make_uuid()}}
    var_access_token: ${{get_accesstoken()}}
    sign: ${{make_sign($currtime, $uuid, $var_access_token)}}
request:
    headers:
        Content-Type: application/json
        User-Agent: abilityIOSAppstore/1180010 CFNetwork/1209 Darwin/20.2.0
        X-MMM-AccessToken: $var_access_token
        X-MMM-AppName: com.maimaimai.abilityIOS
        X-MMM-AppProject: ability
        X-MMM-DeviceType: '0'
        X-MMM-Sign: $sign
        X-MMM-Timestamp: $currtime
        X-MMM-Uuid: $uuid
        X-MMM-Version: 1.18.0
    {self.yamldata}
    method: {self.method}
    url: {self.path}
validate:
-   eq:
    - content.msg
    - ok
"""
        #创建模块目录
        file_path = self.path.split("/")[-2]
        if file_path == '':
            file_path = self.path.split("/")[-1]
        if file_path[0].isalnum() == False:
            file_path = file_path[1::]
        feature_path = os.path.join("F:\createModel\\api","{}".format(file_path))
        utils.mkdir(feature_path)

        #创建api
        filename = self.path.split("/")[-1]
        if filename == '':
            filename = self.path.split("/")[-2]
        if filename[0].isalnum() == False:
            filename = filename[1::]
        test_api = os.path.join(feature_path,"{}.yml".format(filename))
        utils.create_file(test_api,case)



if __name__ == '__main__':
    yapilogin = Yapi(email="***@qq.com", password="***", group_id="14")
    # yapilogin.get_interface_data(3680)


    interface_list = yapilogin.get_interface_listdata('素+销售导航-PC端')

