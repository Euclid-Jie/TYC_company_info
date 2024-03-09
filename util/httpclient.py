#!/usr/bin/python3
# -*-: coding: utf-8 -*-
"""
:author: albert
:date: 02/28/2019
:desc: http请求工具类
"""
import logging
import requests


class Request:
    def __init__(self, url, method=None, params=None, proxy=True, **kwargs):
        self.proxy = proxy
        self.url = url
        self.params = params
        self.data = None
        self.method = method
        if self.method == "post":
            self.post(**kwargs)
        else:
            self.get(**kwargs)

    def get(self, **kwargs):
        resp = requests.get(
            self.url, params=self.params, verify=False, proxies=None, **kwargs
        )
        if resp and resp.status_code == 200:
            self.data = resp.text
        else:
            logging.warning(resp)

    def post(self, **kwargs):
        resp = requests.post(self.url, verify=False, proxies=None, **kwargs)
        if resp and resp.status_code == 200:
            self.data = resp.text
        else:
            logging.warning(resp)
