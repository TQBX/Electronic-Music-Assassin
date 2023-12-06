# -*- coding: utf-8 -*-
import requests
import hmac
import hashlib
import base64
import time
import random
import os
import json
import sys
import threading
from datetime import datetime

class Credential:
    def __init__(self, secret_id, secret_key):
        self.secret_id = secret_id
        self.secret_key = secret_key

class FlashRecognitionRequest:
    def __init__(self, engine_type):
        self.engine_type = engine_type
        self.speaker_diarization = 0
        self.filter_dirty = 0
        self.filter_modal = 0
        self.filter_punc = 0
        self.convert_num_mode = 1
        self.word_info = 0
        self.hotword_id = ""
        self.voice_format = ""
        self.first_channel_only = 1

    def set_first_channel_only(self, first_channel_only):
        self.first_channel_only = first_channel_only

    def set_speaker_diarization(self, speaker_diarization):
        self.speaker_diarization = speaker_diarization

    def set_filter_dirty(self, filter_dirty):
        self.filter_dirty = filter_dirty

    def set_filter_modal(self, filter_modal):
        self.filter_modal = filter_modal

    def set_filter_punc(self, filter_punc):
        self.filter_punc = filter_punc

    def set_convert_num_mode(self, convert_num_mode):
        self.convert_num_mode = convert_num_mode

    def set_word_info(self, word_info):
        self.word_info = word_info

    def set_hotword_id(self, hotword_id):
        self.hotword_id = hotword_id

    def set_voice_format(self, voice_format):
        self.voice_format = voice_format

class FlashRecognizer:
    '''
    reponse:  
    字段名            类型
    request_id        string
    status            Integer    
    message           String    
    audio_duration    Integer
    flash_result      Result Array
    Result的结构体格式为:
    text              String
    channel_id        Integer
    sentence_list     Sentence Array
    Sentence的结构体格式为:
    text              String
    start_time        Integer    
    end_time          Integer    
    speaker_id        Integer    
    word_list         Word Array
    Word的类型为:
    word              String 
    start_time        Integer 
    end_time          Integer 
    stable_flag：     Integer 
    '''

    def __init__(self, appid, credential):
        self.credential = credential
        self.appid = appid

    def _format_sign_string(self, param):
        signstr = "POSTasr.cloud.tencent.com/asr/flash/v1/"
        for t in param:
            if 'appid' in t:
                signstr += str(t[1])
                break
        signstr += "?"
        for x in param:
            tmp = x
            if 'appid' in x:
                continue
            for t in tmp:
                signstr += str(t)
                signstr += "="
            signstr = signstr[:-1]
            signstr += "&"
        signstr = signstr[:-1]
        return signstr

    def _build_header(self):
        header = dict()
        header["Host"] = "asr.cloud.tencent.com"
        return header

    def _sign(self, signstr, secret_key):
        hmacstr = hmac.new(secret_key.encode('utf-8'),
                           signstr.encode('utf-8'), hashlib.sha1).digest()
        s = base64.b64encode(hmacstr)
        s = s.decode('utf-8')
        return s

    def _build_req_with_signature(self, secret_key, params, header):
        query = sorted(params.items(), key=lambda d: d[0])
        signstr = self._format_sign_string(query)
        signature = self._sign(signstr, secret_key)
        header["Authorization"] = signature
        requrl = "https://"
        requrl += signstr[4::]
        return requrl

    def _create_query_arr(self, req):
        query_arr = dict()
        query_arr['appid'] = self.appid
        query_arr['secretid'] = self.credential.secret_id
        query_arr['timestamp'] = str(int(time.time()))
        query_arr['engine_type'] = req.engine_type
        query_arr['voice_format'] = req.voice_format
        query_arr['speaker_diarization'] = req.speaker_diarization
        query_arr['hotword_id'] = req.hotword_id
        query_arr['filter_dirty'] = req.filter_dirty
        query_arr['filter_modal'] = req.filter_modal
        query_arr['filter_punc'] = req.filter_punc
        query_arr['convert_num_mode'] = req.convert_num_mode
        query_arr['word_info'] = req.word_info
        query_arr['first_channel_only'] = req.first_channel_only
        return query_arr

    def recognize(self, req, data):
        header = self._build_header()
        query_arr = self._create_query_arr(req)
        req_url = self._build_req_with_signature(self.credential.secret_key, query_arr, header)
        r = requests.post(req_url, headers=header, data=data)
        return r.text





def tencent_recong(path, language='en-US'):
    # 注意：使用前务必先填写APPID、SECRET_ID、SECRET_KEY，否则会无法运行！！！
    APPID = "1316104262"
    SECRET_ID = "AKIDzzvkT9kFi7Um1CIWfgZN8563HScQAoLs"
    SECRET_KEY = "VtBLMG3iFevStEurmeRI3iErPvMfrwul"
    if language=='en-US':
        ENGINE_TYPE = "16k_en"
    elif language=='zh-CN':
        ENGINE_TYPE = "16k_zh"
    else:
        print('Please indicate the language!!')
        sys.exit()

    if APPID == "":
        print("Please set APPID!")
        exit(0)
    if SECRET_ID == "":
        print("Please set SECRET_ID!")
        exit(0)
    if SECRET_KEY == "":
        print("Please set SECRET_KEY!")
        exit(0)

    credential_var = Credential(SECRET_ID, SECRET_KEY)
    # 新建FlashRecognizer，一个recognizer可以执行N次识别请求
    recognizer = FlashRecognizer(APPID, credential_var)

    # 新建识别请求
    req = FlashRecognitionRequest(ENGINE_TYPE)
    req.set_filter_modal(0)
    req.set_filter_punc(0)
    req.set_filter_dirty(0)
    req.set_voice_format("wav")
    req.set_word_info(0)
    req.set_convert_num_mode(1)

    # 音频路径
    with open(path, 'rb') as f:
        #读取音频数据
        data = f.read()
        #执行识别
        resultData = recognizer.recognize(req, data)
        resp = json.loads(resultData)
        #print(resp)
        request_id = resp["request_id"]
        code = resp["code"]
        success = True
        result = resp["flash_result"][0]['text']
        if code != 0:
            # print("recognize faild! request_id: ", request_id, " code: ", code, ", message: ", resp["message"])
            success = False
            result = resp['message']

        # print("request_id: ", request_id)
        #一个channl_result对应一个声道的识别结果
        #大多数音频是单声道，对应一个channl_result
        #for channl_result in resp["flash_result"]:
        #    # print("channel_id: ", channl_result["channel_id"])
        #    print(channl_result["text"])

        return result,success


if __name__ == "__main__":
    path = "/home/yxj/Phantom-of-Formants/whereismycarTTSaudio2s.wav"
    #path = "/home/yxj/Phantom-of-Formants/find-result/TF/2/rock_1105_11000_3to13_pick_50d1449_743c04c21bbb932a/"
    re,success,na = tencent_recong(path)
    print(re,na)







'''
# -*- coding:utf-8 -*-
import base64
from tencentcloud.asr.v20190614 import asr_client, models
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
import scipy.io.wavfile as wav


filename = path.split('/home/yxj/Phantom-of-Formants/find-result/TF/2/')[-1]
    # appid = '1252836971'  #可以不使用
    cred = credential.Credential("AKIDdP5jIcfRxDDepkOyWyKYhkgVCi13pLbZ",
                                 "mHXWFhvuc3D7mBMHvIPGq9B2cuvf9MIy")  # SecretId and SecretKey
    httpProfile = HttpProfile()
    httpProfile.endpoint = "asr.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    clientProfile.signMethod = "TC3-HMAC-SHA256"
    client = asr_client.AsrClient(cred, "ap-shanghai", clientProfile)

    # 读取文件以及base64
    fwave = open(path, mode='rb').read()
    dataLen = len(fwave)
    base64Wav = base64.b64encode(fwave).decode('utf8')
    # print(base64Wav)
    # 发送请求
    req = models.SentenceRecognitionRequest()
    params = {
        "ProjectId": 0,
        "SubServiceType": 2,
        "EngSerViceType": "16k_en",  # 识别16k的英语音频
        "SourceType": 1,
        "Url": "",
        "VoiceFormat": "wav",
        "UsrAudioKey": "session-123",
        "Data": base64Wav,
        "DataLen": dataLen}

    rate, _ = wav.read(path)
    params['EngSerViceType']=f"{int(rate/1000)}k_en"
    req._deserialize(params)

    resp = client.SentenceRecognition(req)

    result = resp.Result
    success = True
    if result == "":
        result = "null"
        success = False
    return result, success, filename
'''
