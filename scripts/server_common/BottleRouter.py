#!/usr/bin/env python
# -*- coding:utf-8 -*-
import KBEngine

from bottle import template, Bottle, static_file, request, response, redirect
import urllib


def make_result(act='', val='', message='', code='ok'):
    return {'act': act, 'val': val, 'message': message, 'code': code}


# def make_json(act='', val='', message='', code='ok'):
#     return json.dumps(make_result(act,val,message,code))

root = Bottle()


@root.route('/login')
def doLogin():
    username = request.query.get('username', None)
    if username is None:
        username = "admin"
    response.set_cookie("username", username, secret='FPIC')
    redirect("/")


@root.route('/hello/<id:int>')
def helloIndex(id):
    try:
        s = str(KBEngine.entities[id])
    except Exception:
        s = "Hello 中国"
    # return make_result('hello', 'index', s, 'ok')
    return template('<b>Hello {{name}}</b>!', name=s)


@root.route('/static/:path#.+#')
def server_static(path):
    return static_file(path, root='./scripts/web/')


@root.get('/')
def homeIndex():
    username = request.get_cookie("username", secret='FPIC', default=None)
    if username is None:
        return "中国"

    return username


@root.route('/favicon.ico')
def get_favicon():
    return server_static('favicon.ico')


@root.route('/wait/')
def waitIndex():
    root.webmgr.wait()
    return make_result('wait', 'index', root.webmgr.getMembers(), 'wait')


@root.route('/go/', method=['post', 'get'])
def goIndex():
    username = request.query.get('username', None)
    if username is None:
        username = "浙江GET"

    password = request.POST.get('password', None)
    if password is None:
        password = "浙江POST"

    checkcode = request.params.get('checkcode', None)
    if checkcode is None:
        checkcode = "浙江PARAM"

    out = {'username': urllib.parse.unquote(username), 'password': password, 'checkcode': checkcode}

    root.webmgr.wait()
    return make_result('go', 'index', out, 'wait')


@root.route('/close/')
def closeIndex():
    return make_result('close', 'index', root.webmgr.getMembers(), 'ok')


def startBottle(webmgr):
    root.run(host='', port=8980, mgr=webmgr)
    root.webmgr = webmgr
    return root
