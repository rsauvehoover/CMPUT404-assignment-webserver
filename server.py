#  coding: utf-8 
import socketserver
import os
import mimetypes

# Copyright 2013 Abram Hindle, Eddie Antonio Santos, Frederic Sauve-Hoover
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

# Various defines
DIR_WWW = os.getcwd() + '/www'
HTTP_VERSION = "HTTP/1.1"

class HTTPRequestHandler:
    """
    Handles the full http request
    """

    def __init__ (self, request):
        """
        Takes the request text splits into various parts we need
        """
        # our response
        self.http_response = None 
        # what kind of request, i.e. GET POST etc.
        self.request = request.decode().split()
        try:
            self.request_type = self.request[0] 
            # the requested path
            self.request_path = self.request[1]
        except:
            self.http_response = self.handle_405()

    def handle_405(self):
        """
        A small wrapper around the 405 response for convenience
        """
        self.http_response = HTTPResponseBuilder(405, {'Allow': 'GET'}, None) 

    def handle_404(self):
        """
        A small wrapper around the 404 response for convenience
        """
        self.http_response = HTTPResponseBuilder(404, None, None)

    def handle_301(self, location):
        """
        A small wrapper around the 301 response for convenience
        """
        self.http_response = HTTPResponseBuilder(301, {'Location' : location}, None)

    def handle_200(self, headers, body):
        """
        A small wrapper around the 200 response for convenience
        """
        # ensure the path is correct
        self.http_response = HTTPResponseBuilder(200, headers, body)

    def handle_response(self):
        """
        Handles the actual response to the client,
        which files to return and what codes to send to the client
        """
        # Add index.html automatically if no file is specified
        if self.request_path[-1] == '/':
            self.request_path = '/index.html'

        # Check for correct request type
        if self.request_type == 'GET':
            # assert that the path is valid, and doesn't try to access things
            # outside of /www
            realpath = os.path.realpath(DIR_WWW + self.request_path)
            if self.request_path not in realpath:
                self.handle_404();

            elif os.path.exists(realpath):
                # If the file won't open and returns an IsADirectoryError, chances are it's because of 
                # the / not being there when it needed to be, so we return a 301
                try:
                    with open(realpath, 'r') as f:
                        self.handle_200({'content-type' : mimetypes.guess_type(realpath)[0]}, f.read())
                except IsADirectoryError:
                    print(self.request_path)
                    self.handle_301(self.request_path + '/')
            else:
                # if the file doesn't exist
                self.handle_404()
        else:
            # if the wrong request type is sent
            self.handle_405()
        return self.http_response



class HTTPResponseBuilder:
    """
    Handle http responses
    https://www.w3.org/Protocols/rfc2616/rfc2616-sec6.html
    """

    def __init__ (self, status_code, headers={}, message=''):
        # we don't need many reason phrases
        self.status_reason_phrases = {200 : 'OK', 404 : 'Not Found', 405 : 'Method Not Allowed', 301 : 'Moved Permanently', 403 : 'Forbidden'} 
        self.status_line = None

        self.status_code = status_code
        self.headers = headers
        self.message = message

    def _build_status_line(self):
        """
        build the status line
        """
        self.status_line = '{http_version} {status_code} {status_reason} \r\n'.format(http_version=HTTP_VERSION,
                status_code=self.status_code, status_reason=self.status_reason_phrases[self.status_code])

    def _build_response(self):
        """
        build the actual response itself
        """
        # build our status line
        self._build_status_line()

        # initialize the response body
        self.response_body = self.status_line

        # add all header keys to body
        if self.headers:
            for key in self.headers.keys():
                self.response_body += '{key}: {val} \r\n'.format(key=key, val=self.headers[key])
        self.response_body += '\r\n' + str(self.message)

    def __repr__(self):
        """
        lets us just print the object as the response body
        """
        self._build_response()
        return self.response_body

class MyWebServer(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip()
        print ("Got a request of: %s\n" % self.data)
        a = HTTPRequestHandler(self.data).handle_response()
        self.request.sendall(bytearray(str(a),'utf-8'))

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
