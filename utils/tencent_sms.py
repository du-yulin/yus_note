# -*- coding: utf-8 -*-
from typing import List, Any, Dict, Literal, Optional
from django.conf import settings
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)

# 导入对应产品模块的client models。
from tencentcloud.sms.v20210111 import sms_client, models

# 导入可选配置类
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile


class SMS:
    """对腾讯sms sdk二次封装
    配置名称与原配置名称一致，仅将原小驼峰命名改为py风格下划线
    """

    __tencent_conf = getattr(settings, "TENCENT", {})

    secret_id = __tencent_conf.get("SECRET_ID", None)
    secret_key = __tencent_conf.get("SECRET_KEY", None)

    def __init__(
        self,
        use_to: str,
    ) -> None:
        try:
            self.sms_conf = self.__tencent_conf.get("SMS", {}).get(use_to)
        except KeyError as e:
            raise KeyError(f"未在settings.TENCENT['SMS']中发现发现对应配置: {use_to}!") from None
        self.cred = credential.Credential(self.secret_id, self.secret_key)
        self.http_profile = HttpProfile(**self.sms_conf.get("HTTP_PROFILE", {}))
        self.client_profile = ClientProfile(
            httpProfile=self.http_profile, **self.sms_conf.get("CLIENT_PROFILE", {})
        )
        self.client = sms_client.SmsClient(
            self.cred, self.sms_conf.get("REGION", ""), self.client_profile
        )

    def send_sms(
        self, to_list: List[str], param_list: List[str]
    ) -> Dict[Literal["successes", "failures", "request_id", "message"], Any]:
        """发送短信

        Args:
            to_list: 下发手机号码，采用 E.164 标准，格式为+[国家或地区码][手机号]，例如：+8613711112222。注：无任何国家或地区码的11位手机号码，前缀默认为+86。
            param_list: 模板参数，若无模板参数，则设置为空。模板参数的个数需要与 TemplateId 对应模板的变量个数保持一致。
        Returns:
            返回成功的SendStatus，失败的SendStatus， RequestId，错误信息，如{'successes':[dict], 'failures':[dict], 'request_id': '', 'message': ''}
        Notices:
            当出现以下错误码时，快速解决方案参考
            - [FailedOperation.SignatureIncorrectOrUnapproved](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Afailedoperation.signatureincorrectorunapproved-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            - [FailedOperation.TemplateIncorrectOrUnapproved](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Afailedoperation.templateincorrectorunapproved-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            - [UnauthorizedOperation.SmsSdkAppIdVerifyFail](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Aunauthorizedoperation.smssdkappidverifyfail-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            - [UnsupportedOperation.ContainDomesticAndInternationalPhoneNumber](https://cloud.tencent.com/document/product/382/9558#.E7.9F.AD.E4.BF.A1.E5.8F.91.E9.80.81.E6.8F.90.E7.A4.BA.EF.BC.9Aunsupportedoperation.containdomesticandinternationalphonenumber-.E5.A6.82.E4.BD.95.E5.A4.84.E7.90.86.EF.BC.9F)
            - 更多错误，可咨询[腾讯云助手](https://tccc.qcloud.com/web/im/index.html#/chat?webAppId=8fa15978f85cb41f7e2ea36920cb3ae1&title=Sms)
        """

        res = {"successes": [], "failures": [], "request_id": "", "message": ""}

        req = models.SendSmsRequest()
        req.PhoneNumberSet = to_list
        req.TemplateParamSet = param_list
        for k, v in self.sms_conf.get("REQUEST", {}).items():
            setattr(req, k, v)

        try:
            # resp.to_json_string(indent=4)
            # {
            #     "Response": {
            #         "SendStatusSet": [
            #             {
            #                 "SerialNo": "5000:1045710669157053657849499619",
            #                 "PhoneNumber": "+8618511122233",
            #                 "Fee": 1,
            #                 "SessionContext": "test",
            #                 "Code": "Ok",
            #                 "Message": "send success",
            #                 "IsoCode": "CN"
            #             },
            #             {
            #                 "SerialNo": "5000:1045710669157053657849499718",
            #                 "PhoneNumber": "+8618511122266",
            #                 "Fee": 1,
            #                 "SessionContext": "test",
            #                 "Code": "Ok",
            #                 "Message": "send success",
            #                 "IsoCode": "CN"
            #             }
            #         ],
            #         "RequestId": "a0aabda6-cf91-4f3e-a81f-9198114a2279"
            #     }
            # }
            resp = self.client.SendSms(req)
            res["request_id"] = resp.RequestId
            for i in resp.SendStatusSet:
                if i["Code"] == "Ok":
                    res["successes"].append(i)
                else:
                    res["failures"].append(i)
        except TencentCloudSDKException as e:
            res["message"] = e.message
            res["request_id"] = e.requestId

        return res
