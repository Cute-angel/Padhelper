import asyncio
from utils import Config,FileDownloader
from core import Login,SyncRecords

cacheConfigInstance = Config("cache")
loginConfigInstance = Config("login")

loginInstance = Login(loginConfigInstance)
loginInstance.start()


SyncRecords(loginConfigInstance.sessionid,loginConfigInstance.user,cacheConfigInstance)

fileDownloaderInstance = FileDownloader(cacheConfigInstance,"pic",loginInstance=loginConfigInstance)

loop = asyncio.get_event_loop()
loop.run_until_complete(fileDownloaderInstance.main())
