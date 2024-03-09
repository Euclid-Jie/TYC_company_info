#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author sanfeng
# @since 2019-09-27
# @description --
import json
import logging
from db.models import Company
from tianyancha import *
from urllib.parse import quote
from util.httpclient import Request


class TycClient:
    def __init__(self, payload=None):
        self.payload = payload
        self.keyword = None
        self.src = []
        self.brand_and_agencies = []
        self.companies = []

    def search(self, keyword: str):
        """
        根据关键字搜索相关企业信息
        :param keyword: 关键字
        :return:
        """
        self.keyword = keyword
        if not self.payload:
            self.payload = {
                "pageNum": 1,
                "pageSize": 20,
                "sortType": 0
            }
        url = TycQueryApi.format(q=quote(keyword))
        data = Request(url, self.payload, headers=REQUEST_HEADERS).data
        if data:
            api_data = json.loads(data)
            if api_data.get("state") == 'ok':
                self.src = api_data.get("data", {}).get("companyList", [])
                self.brand_and_agencies = api_data.get("data", {}).get("brandAndAgencyList", [])
                self.__post_process__()
            else:
                logging.info("查询异常：[%s]" % api_data)
        return self

    def __post_process__(self):
        if not self.src:
            return

        company_list = self.src
        for company in company_list:
            company_entity = Company()
            # 公司检索的关键字
            company_entity.keyword = self.keyword
            # 公司主体基本信息
            self.EntityHelper.__basic_info__(company, company_entity)

    class EntityHelper:
        @staticmethod
        def __basic_info__(src: dict, target: Company):
            # 公司外部系统ID
            target.id = src.get('id', '-')
            # 公司名称
            target.name = src.get('name', '-').replace("</em>","").replace("<em>","")
            # 公司简称
            target.short_name = src.get('alias', '-')
            # 公司法人
            target.representative = src.get('legalPersonName', '-')
            # 公司成立时间
            target.found_time = src.get('estiblishTime', '-')[0:10]
            # 公司地址
            target.company_address = src.get('regLocation', '-')
            # 公司注册地址
            target.register_address = src.get('regLocation', '-')
            # 公司所在省份，例：浙江，北京，广东
            target.province = src.get('base', '-')
            # 公司所在市
            target.city = src.get('city', '-')
            # 公司所在区
            target.district = src.get('district', '-')
            # 公司经营状态
            target.biz_status = src.get('regStatus', '-')
            # 公司地址经纬度坐标
            target.geoloc = str({
                'latitude': src.get('latitude', '-'),
                'longitude': src.get('longitude', '-')
            })
            # 公司邮箱列表
            target.emails = src.get('emails', ['-']).split(';')[0].replace('\t', '')
            # 公司联系方式列表
            target.phones = src.get('phoneList', [])
            # 公司联系方式
            target.contact = src.get('phoneNum', '-')
            # 公司经营范围
            target.biz_scope = src.get('businessScope', '-')
            # 公司类型
            target.company_type = src.get('companyOrgType', '-').replace('\t', '')
            # 公司质量分数
            target.score = src.get('orginalScore', 0)
            # 公司注册资本
            target.register_capital = src.get('regCapital', '-')
            # 公司统一社会信用代码
            target.credit_code = src.get('creditCode', '-')
            # 公司纳税号
            target.taxpayer_code = src.get('taxCode')
            if not target.taxpayer_code:
                target.taxpayer_code = target.credit_code
            # 公司注册号
            target.register_code = src.get('regNumber', '-')
            # 公司组织机构代码
            target.organization_code = src.get('orgNumber', '-')
            # 公司标签列表
            target.tags = src.get('labelListV2', [])
            # 公司行业分类
            target.industry = src.get('categoryStr', '-')

