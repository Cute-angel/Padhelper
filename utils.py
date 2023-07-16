import json
import xml
import os
import asyncio
import aiohttp
from xml.dom.minidom import parse
from xml.dom.minidom import parseString



class SOAPHander():
    def __init__(self,Input,elementname):
        q = type(Input)
        if type(Input) is str:
            self.DOMTree = parseString(Input)
            self.collection = self.DOMTree.documentElement
        if type(Input) is xml.dom.minidom.Document:
            self.DOMTree = Input
            self.collection = self.DOMTree.documentElement
        if type(Input) is xml.dom.minicompat.NodeList:
            self.DOMTree = xml.dom.minidom.getDOMImplementation().createDocument(None,'root',None)
            self.collection = self.DOMTree.documentElement            
            for i in range(len(Input)):
                x = Input[i].cloneNode(True)
                self.collection.appendChild(x)
        self.szLoginJson = self.collection.getElementsByTagName(elementname)
        self.lenght = len(self.szLoginJson)
        if self.lenght == 0:
            self.data = None
        if self.lenght == 1:
            # only one childNode use ....[0] to get the element node 
            # use method to get the value 
            self.data = self.childNodeToText(self.szLoginJson[0])
        else: 
            f = lambda i:self.childNodeToText(self.szLoginJson[i])
            self.data = (f(i) for i in range(self.lenght))
    def childNodeToText(self,node):
        if node.hasChildNodes() == True:
            if len(node.childNodes) == 1:
                # one node 
                return self.childNodeToText(node.childNodes[0])
            else:
                return node.childNodes # return the childNodeList it has many nodes.
        else:
            # for text node
            return node.data

class Config():
    global loginPath 
    global cachePath  
    loginPath = "./config/login.json"
    cachePath = "./config/cache.json"
    
    loginPath = os.path.join(os.path.abspath(os.path.dirname(__file__)),loginPath)
    cachePath = os.path.join(os.path.abspath(os.path.dirname(__file__)),cachePath)
     
    def __init__(self,type):
        self.type = type
        self.passwdMd5 = ""
        self.user = ""
        self.recordsList = []
        self.sessenid =""
        self.booknames = []
        self.relayStr =""
        self.recordNum = 0
        
        self.tempList = []
        
        self.checkConfigFile()
    
    def SyncBooknames(self):
        i = 0
        for record in self.recordsList:
            if record["bookname"] in self.booknames:
                pass
            else:
                self.booknames.append(record["bookname"])
        
    def checkConfigFile(self):
        if self.type == "login":
            if not os.path.exists(loginPath):
                self._initConfig(loginPath)
            else:
                with open(loginPath,"r")as f:
                    configJ = json.loads(f.read())
                    self.user = configJ["user"]
                    self.passwdMd5 = configJ["passwd"]
                    self.sessenid = configJ["sessenid"]
                
        if self.type == "cache":
            if not os.path.exists(cachePath):
                self._initConfig(cachePath)
            else:
                with open(cachePath,"r")as f:
                    configJ = json.loads(f.read())
                    self.recordsList = configJ["recordList"]
                    self.booknames = configJ["booknames"]
                    self.recordNum = configJ["recordNum"]
                    self.relayStr = configJ["relayStr"]
    def _initConfig(self,path):

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path,"w") as f:
            f.write("{}")
            
    def UpdateLoginJson(self):
        j = {"user":self.user,"passwd":self.passwdMd5,"sessenid":self.sessenid}
        with open(loginPath,"w")as f:
            f.write(json.dumps(j))
            

    def SyncRecordsList(self):
        cacheDict = {"recordList":self.recordsList,"booknames":self.booknames,"relayStr":self.relayStr,"recordNum":self.recordNum}
        with open(cachePath,"w")as f:
            f.write(json.dumps(cacheDict))

class FileDownloader():
    global filePath
    filePath = "./file"
    filePath = os.path.join(os.path.abspath(os.path.dirname(__file__)),filePath)
    def __init__(self,cfgCacheInstance,type,loginInstance=None) -> None:
        self.cacheCFG = cfgCacheInstance
        self.checkDir()
        self.downloadList = []
        self.login = loginInstance
        if type == "pic":
            rType = "0"
        for record in cfgCacheInstance.recordsList:
            if record["type"] == rType:
                self.downloadList.append((record["packageid"],record['bookname']))
    def checkDir(self):
        for i in self.cacheCFG.booknames:
            path = os.path.join(filePath,i)
            if not os.path.exists(path):
                os.makedirs(path)
    
    
    async def __download(self,packageid,path,user):
        url = f'https://gzzxres.lexuewang.cn:8003/DataSynchronizeGetSingleData?packageid={packageid}&clientid=myipad_{user}'
        headers = {'Cache-Control': 'max-age=1296000, min-fresh=21600', 'Host': 'gzzxres.lexuewang.cn:8003', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip', 'User-Agent': 'okhttp/3.14.9'}
        cookies = {}
        async with aiohttp.ClientSession(headers=headers,cookies=cookies) as session:
            try:
                try:
                    async with session.get(url) as resp:
                        raw = await resp.read()
                except aiohttp.ClientPayloadError:
                    print("try again",packageid)
                    await session.close()
                    session = aiohttp.ClientSession(headers=headers,cookies=cookies)
                    async with session.get(url) as resp:
                        raw = await resp.read()
                    await session.close()
            except Exception as e:
                print(e,packageid)
            else:

                with open(path,"wb")as f:
                    f.write(raw)
                print("end",packageid)
            finally:
                await session.close()
    async def downloadTask(self):
        tasks = []
        for record in self.downloadList:
            packageid = record[0]
            name = record[1]
            path = os.path.join(filePath,name,packageid+'.jpg')
            tasks.append(asyncio.create_task(self.__download(packageid,path,user=self.login.user)))
        return tasks

    async def main(self):
        tasks = await self.downloadTask()
        print("start download")
        await asyncio.wait(tasks)
if __name__ == "__main__":
    cache = Config("cache")
    fileDownloaderInstance = FileDownloader(cache,"pic")
    asyncio.run(fileDownloaderInstance.main())
    print()