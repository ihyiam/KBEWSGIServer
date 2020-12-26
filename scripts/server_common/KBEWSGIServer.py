#!/usr/bin/env python
# -*- coding:utf-8 -*-
import KBEngine
from socketserver import TCPServer
from KBEDebug import *
import json

from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
from wsgiref.handlers import SimpleHandler

import socket

from bottle import response,HTTPResponse



class KBEWSGIServer(WSGIServer):

    def __init__(self, server_address, RequestHandlerClass, webmgr, bind_and_activate=True):
        TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.webmgr = webmgr
        self._clients = {}
        KBEngine.registerReadFileDescriptor(self.socket.fileno(), self.server_for)

    def server_for(self, fileno):
        self.curSock, self.curAddr = self.socket.accept()
        self._clients[self.curSock.fileno()] = [self.curSock, self.curAddr]
        KBEngine.registerReadFileDescriptor(self.curSock.fileno(), self.serve_forever)
        DEBUG_MSG("KBEWSGIServer::server_for: new channel[%s/%i]" % (self.curAddr, self.curSock.fileno()))

    def setHandler(self, req, resp):
        curConnect = self._clients.get(req.request.fileno(), None)
        if curConnect is None:
            return
        curConnect.append(req)
        curConnect.append(resp)
        self.get_app().curReq = req

    def endwait(self, fileno, out):
        curConnect = self._clients.get(fileno, None)
        if curConnect is None:
            return
        if (len(curConnect) == 4):
            curConnect[3].endwait(out)

    def serve_forever(self, fileno):
        """
        KBE事件 有请求
        """
        curConnect = self._clients.get(fileno, None)
        if curConnect is None:
            return

        self._handle_request_noblock(curConnect[0], curConnect[1])

    def process_request(self, request, client_address):
        """Call finish_request.

        Overridden by ForkingMixIn and ThreadingMixIn.

        """
        self.finish_request(request, client_address)
        # self.shutdown_request(request)

    def _handle_request_noblock(self, request, client_address):
        """Handle one request, without blocking.

        I assume that selector.select() has returned that the socket is
        readable before this function was called, so there should be no risk of
        blocking in get_request().
        """

        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except Exception:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
            except:
                self.shutdown_request(request)
                raise
        else:
            self.shutdown_request(request)

    def handle_request(self):
        return self._handle_request_noblock()

    def shutdown_request(self, request):
        KBEngine.deregisterReadFileDescriptor(request.fileno())
        DEBUG_MSG("KBEWSGIServer::shutdown_request: deregisterReadFileDescriptor %d" % (request.fileno()))
        self._clients.pop(request.fileno(), None)
        """Called to shutdown and close an individual request."""
        self.close_request(request)


class KBEServerHandler(SimpleHandler):

    def endwait(self, out):
        if out == {}:
            out = self.out

        out = json.dumps(out)
        out = out.encode(self.waitresp.charset)
        # Byte Strings are just returned
        if isinstance(out, bytes):
            if 'Content-Length' not in self.waitresp:
                self.waitresp['Content-Length'] = len(out)
        self.headers = None
        self.start_response(self.waitresp._status_line, self.waitresp.headerlist)
        self.result = [out]
        self.finish_response()
        self.stdout.close()
        self.request_handler.server.shutdown_request(self.request_handler.request)

    def run(self, application):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.
        try:
            self.setup_environ()

            out = application(self.environ, self.start_response)

            if isinstance(out, dict):

                self.out = out
                if out['code'] == 'wait':
                    self.waitresp = response.copy(cls=HTTPResponse)
                    return

                out = json.dumps(out)
                out = out.encode(response.charset)

                if isinstance(out, bytes):
                    if 'Content-Length' not in response:
                        response['Content-Length'] = len(out)

                self.result = [out]
                self.finish_response()
                self.request_handler.server.shutdown_request(self.request_handler.request)
            else:
                self.result = out
                self.finish_response()
                self.request_handler.server.shutdown_request(self.request_handler.request)

        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            # We expect the client to close the connection abruptly from time
            # to time.
            self.stdout.close()
            return
        except:
            try:
                self.handle_error()
                self.stdout.close()
            except:
                # If we get an error handling an error, just give up already!
                self.close()
                raise  # ...and let the actual server figure it out.


class KBEFixedHandler(WSGIRequestHandler):
    def address_string(self):  # Prevent reverse DNS lookups please.
        return self.client_address[0]

    def log_request(self,*args, **kw):
        if not self.quiet:
            return WSGIRequestHandler.log_request(*args, **kw)

    def finish(self):
        if not self.wfile.closed:
            try:
                self.wfile.flush()
            except socket.error:
                # A final socket error may have occurred here, such as
                # the local error ECONNABORTED.
                pass
        # self.wfile.close()
        self.rfile.close()

    def handle(self):
        """Handle a single HTTP request"""
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return

        except Exception as e:
            # a read or a write timed out.  Discard this connection
            try:
                self.log_error("Request timed out: %r", e)
                self.close_connection = True
                self.server.shutdown_request(self.request)
            except:
                pass
            return

        if not self.parse_request():  # An error code has been sent, just exit
            return

        handler = KBEServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ(),
            multithread=False,
        )
        # self.log_error("Request go....handler: %s", handler)
        self.server.setHandler(self, handler)
        handler.request_handler = self  # backpointer for logging
        handler.run(self.server.get_app())
