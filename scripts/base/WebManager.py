# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
from interfaces.GameObject import GameObject
import BottleRouter

TIMERID = 101
TIMEOUTSECOND = 5

import time

"""
这是一个脚本层封装的WEB管理器
"""


class WebManager(KBEngine.Entity, GameObject):

    def __init__(self):
        KBEngine.Entity.__init__(self)
        GameObject.__init__(self)
        self.waitSend = {}
        self.addTimer(1, 1, TIMERID)
        self.root = BottleRouter.startBottle(self)
        KBEngine.globalData["WebManager"] = self

    """
    KBEngine method.
    引擎回调timer触发,等待回调的HTTP请求超时关闭
    """
    def onTimer(self, tid, userArg):
        # DEBUG_MSG("%s::onTimer: %i, tid:%i, arg:%i" % (self.getScriptName(), self.id, tid, userArg))
        if TIMERID == userArg:
            now = time.time()
            for key in list(self.waitSend.keys()):
                if now > self.waitSend[key]:
                    self.root.server.endwait(key, {})
                    del self.waitSend[key]

        GameObject.onTimer(self, tid, userArg)

    def getMembers(self):
        return str(len(KBEngine.entities))

    def wait(self):
        self.waitSend[self.root.curReq.request.fileno()] = time.time() + TIMEOUTSECOND

    def remoteCall(self, fileno, data):
        if self.waitSend.pop(fileno, None) is not None:
            self.root.server.endwait(fileno, data)
