#!/usr/bin/python
# -*- coding: UTF-8 -*-
import asyncio
import requests
import json
from xml.dom.minidom import parseString
from hashlib import md5

from utils import FileDownloader, SOAPHander
from utils import Config

global relayStr

# not to call
def getPicList(sessionid,studId,relayStr =""):
    url = 'https://gzzxres.lexuewang.cn:8003/wmexam/wmstudyservice.WSDL'
    headers = {'Connection': 'keep-alive', 'User-Agent': 'ksoap2-android/2.6.0+', 'SOAPAction': 'http://webservice.myi.cn/wmstudyservice/wsdl/LessonsScheduleGetTableData', 'Content-Type': 'text/xml;charset=utf-8', 'Accept-Encoding': 'gzip'}
    cookies = {'sessionid': sessionid,'userguid':'ffffffffffffffffffffffffffffffff'}
    data = f'''<v:Envelope xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns:d="http://www.w3.org/2001/XMLSchema" xmlns:c="http://schemas.xmlsoap.org/soap/encoding/" xmlns:v="http://schemas.xmlsoap.org/soap/envelope/"><v:Header /><v:Body><LessonsScheduleGetTableData xmlns="http://webservice.myi.cn/wmstudyservice/wsdl/" id="o0" c:root="1"><lpszTableName i:type="d:string">studentquestionbook</lpszTableName><lpszUserClassGUID i:type="d:string"></lpszUserClassGUID><lpszStudentID i:type="d:string">{studId}</lpszStudentID><lpszLastSyncTime i:type="d:string"></lpszLastSyncTime><szReturnXML i:type="d:string">enablesegment=3;{relayStr}</szReturnXML></LessonsScheduleGetTableData></v:Body></v:Envelope>'''
    html = requests.post(url, headers=headers, cookies=cookies, data=data)
    szReturnXML =parseString(SOAPHander(html.text,'AS:szReturnXML').data)
    records = SOAPHander(szReturnXML,"Record").data
    if szReturnXML.documentElement.hasAttribute('hasMoreData'):
        if szReturnXML.documentElement.getAttribute('hasMoreData') == "true":
            hasMoreData= True
        else:
            hasMoreData = False
    return hasMoreData,records

def getAllrecordsList(sessionid,studId,cacheCFG,rStr=""):
    relayStr = rStr
    a = getPicList(sessionid,studId,relayStr=rStr)
    for record in a[1]:
        guid = SOAPHander(record,"guid").data
        modifydate = SOAPHander(record,"modifydate").data
        packageid = SOAPHander(record,"packageid").data
        rType = SOAPHander(record,"type").data
        bookname = SOAPHander(record,"booknames").data
        # hander null pic
        if not rType == "0":
            print("guid",guid,"not a pic. skip.use objectguid instead") 
            packageid = SOAPHander(record,"objectguid").data
        record = {"guid":guid,"modifydate":modifydate,"packageid":packageid,"type":rType,"bookname":bookname}
        cacheCFG.tempList.append(record)
        relayStr = relayStr+guid+"="+modifydate+";"
    if a[0]:
        getAllrecordsList(sessionid,studId,cacheCFG,relayStr)
    else:
        cacheCFG.relayStr = relayStr
        return

def SyncRecords(sessionid,studId,cacheCFG):
    print("当前记录数量:",cacheCFG.recordNum)
    print("正在获取...")
    getAllrecordsList(sessionid,studId,cacheCFG,cacheCFG.relayStr)
    cacheCFG.recordsList += cacheCFG.tempList
    print("新增:",len(cacheCFG.tempList))
    cacheCFG.SyncBooknames()
    cacheCFG.recordNum = len(cacheCFG.recordsList)
    cacheCFG.SyncRecordsList()
    
class _login(SOAPHander):
    def __init__(self,user,passcodeMd5):
        self.passcodeMd5 = passcodeMd5
        url = 'https://gzzxres.lexuewang.cn:8003/wmexam/wmstudyservice.WSDL'
        headers = {'Connection': 'keep-alive', 'User-Agent': 'ksoap2-android/2.6.0+', 'SOAPAction': 'http://webservice.myi.cn/wmstudyservice/wsdl/UsersLoginJson', 'Content-Type': 'text/xml;charset=utf-8', 'Accept-Encoding': 'gzip'}
        cookies = {'userguid': 'ffffffffffffffffffffffffffffffff;username:paduser'}
        data = f'''<v:Envelope xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns:d="http://www.w3.org/2001/XMLSchema" xmlns:c="http://schemas.xmlsoap.org/soap/encoding/" xmlns:v="http://schemas.xmlsoap.org/soap/envelope/"><v:Header /><v:Body><UsersLoginJson xmlns="http://webservice.myi.cn/wmstudyservice/wsdl/" id="o0" c:root="1"><lpszUserName i:type="d:string">{user}</lpszUserName><lpszPasswordMD5 i:type="d:string">{self.passcodeMd5}</lpszPasswordMD5><lpszClientID i:type="d:string">myipad_</lpszClientID><lpszHardwareKey i:type="d:string">BOARD: SDM450
BOOTLOADER: unknown
BRAND: Lenovo
CPU_ABI: armeabi-v7a
CPU_ABI2: armeabi
DEVICE: X605M
DISPLAY: TB-X605M_S000018_20210616_NingBoRuiYi
FINGERPRINT: Lenovo/LenovoTB-X605M/X605M:8.1.0/OPM1.171019.019/S000018_180906_PRC:user/release-keys
HARDWARE: qcom
HOST: bjws200
ID: OPM1.171019.019
MANUFACTURER: LENOVO
MODEL: Lenovo TB-X605M
PRODUCT: LenovoTB-X605M
RADIO: MPSS.TA.2.3.c1-00705-8953_GEN_PACK-1.159624.0.170600.1
TYPE: user
USER: root
VERSION_CODENAME: REL
VERSION_RELEASE: 8.1.0
VERSION_SDK_INT: 27
WifiMac: BF:56:4B:AA:4E:A3
WifiSSID: "download"
services.jar: 59a4f38ee38bddf7780c961b5f4e0855
framework.jar: 619c504aedd9bb1da652796dfbd0c3d2
PackageName: com.netspace.myipad
ClientVersion: 5.2.4.52455
ClientSign: 308203253082020da00302010202040966f52d300d06092a864886f70d01010b05003042310b300906035504061302434e310f300d060355040713064e696e67426f31223020060355040a13194e696e67426f2052756959694b654a6920436f2e204c74642e3020170d3132313231313130313133355a180f32303632313132393130313133355a3042310b300906035504061302434e310f300d060355040713064e696e67426f31223020060355040a13194e696e67426f2052756959694b654a6920436f2e204c74642e30820122300d06092a864886f70d01010105000382010f003082010a0282010100abf2c60e5fcb7776da3d22c3180e284da9c4e715cec2736646da086cbf979a7f74bc147167f0f32ef0c52458e9183f0dd9571d7971e49564c00fbfd30bef3ca9a2d52bffcd0142c72e10fac158cb62c7bc7e9e17381a555ad7d39a24a470584a0e6aafdce2e4d6877847b15cbf4de89e3e4e71b11dca9920843ccc055acf8781db29bdaf3f06e16f055bf579a35ae3adb4d1149f8d43d90add54596acef8e4a28905f9f19fc0aa7fda9e8d56aa63db5d8d5e0fc4c536629f0a25a44429c699318329af6a3e869dd5e8289c78f55d14563559ffc9ccbf71fac5a03e13a3ee1fb8fc3857d10d5d3990bf9b84cd6fa555eb17a74809a7bb501e953a639104146adb0203010001a321301f301d0603551d0e04160414da4b4d8147840ff4b03f10fc5dd534bb133204e6300d06092a864886f70d01010b05000382010100801b8d796b90ab7a711a88f762c015158d75f1ae5caf969767131e6980ebe7f194ce33750902e6aa561f33d76d37f4482ff22cccbf9d5fecb6ed8e3f278fd1f988ea85ae30f8579d4afe710378b3ccb9cb41beaddef22fb3d128d9d61cfcb3cb05d32ab3b2c4524815bfc9a53c8e5ee3ad4589dc888bcdbdaf9270268eb176ff2d43c2fd236b5bf4ef8ffa8dd920d1583d70f971b988ee4054e1f739ea71510ee7172546ffcda31e6b270178f91086db9ff1051dedf453a6bad4f9b432d362bbe173fd1cc7350853fddd552a27a82fdfaf98e5b08186a03ffc6e187387e4bbd52195126c7c6cec6ab07fd5aadc43a0edb7826b237ba8c8aa443f132516fe89ba
ClientPath: /data/app/com.netspace.myipad-_MfyUxX5i56uhrighuiqwerCCJT_A==/base.apk
ClientMD5: 36386f89d1773aaac2279eb5b823eb09
AppKey: MyiPad
Flavor: normal
AppKey: MyiPad
Flavor: normal
Modules: 326

SignTime: 2023-07-08 19:43:45
Sign: 6c99e0e30cdb25be7962e8fcbdbd843d
</lpszHardwareKey></UsersLoginJson></v:Body></v:Envelope>'''
        html = requests.post(url, headers=headers, cookies=cookies, data=data)
        super().__init__(html.text,'AS:szLoginJson')
        self.loginJson = json.loads(self.data)
        self.sessionid = self.loginJson['sessionid']

class Login(_login):
    def __needInput(self):
        self.user = input("user:")
        self.passwd = input("Password:")
        print("Sync info")
        # update cfg
        self.cfgInstance.user = self.user
        self.passcodeMd5 = self.cfgInstance.passwdMd5 = md5(self.passwd.encode(encoding='UTF-8')).hexdigest()
    
    def __pass(self):
        return
    
    def __init__(self,cfgInstance):
        self.cfgInstance = cfgInstance
        if cfgInstance.user == '' or cfgInstance.passwdMd5 == '':
            self.initF = self.__needInput
        else:
            self.user = cfgInstance.user
            self.passcodeMd5 = cfgInstance.passwdMd5
            self.initF = self.__pass
        
    def start(self):
        self.initF()
        super().__init__(self.user, self.passcodeMd5)
        self.cfgInstance.sessionid = self.sessionid
        self.cfgInstance.UpdateLoginJson()


print()
