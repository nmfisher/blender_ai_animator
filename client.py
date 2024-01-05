import os
import time
import socket 
import bpy 
import csv
import random 
import urllib.request

import io
import mimetypes
from urllib import request
import uuid
import json

class MultiPartForm:
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        # Use a large random byte string to separate
        # parts of the MIME data.
        self.boundary = uuid.uuid4().hex.encode('utf-8')
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary={}'.format(
            self.boundary.decode('utf-8'))

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, fileHandle,
                 mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = (
                mimetypes.guess_type(filename)[0] or
                'application/octet-stream'
            )
        self.files.append((fieldname, filename, mimetype, body))
        return

    @staticmethod
    def _form_data(name):
        return ('Content-Disposition: form-data; '
                'name="{}"\r\n').format(name).encode('utf-8')

    @staticmethod
    def _attached_file(name, filename):
        return ('Content-Disposition: file; '
                'name="{}"; filename="{}"\r\n').format(
                    name, filename).encode('utf-8')

    @staticmethod
    def _content_type(ct):
        return 'Content-Type: {}\r\n'.format(ct).encode('utf-8')

    def __bytes__(self):
        """Return a byte-string representing the form data,
        including attached files.
        """
        buffer = io.BytesIO()
        boundary = b'--' + self.boundary + b'\r\n'

        # Add the form fields
        for name, value in self.form_fields:
            buffer.write(boundary)
            buffer.write(self._form_data(name))
            buffer.write(b'\r\n')
            buffer.write(value.encode('utf-8'))
            buffer.write(b'\r\n')

        # Add the files to upload
        for f_name, filename, f_content_type, body in self.files:
            buffer.write(boundary)
            buffer.write(self._attached_file(f_name, filename))
            buffer.write(self._content_type(f_content_type))
            buffer.write(b'\r\n')
            buffer.write(body)
            buffer.write(b'\r\n')

        buffer.write(b'--' + self.boundary + b'--\r\n')
        return buffer.getvalue()


class Client:
    def __init__(self):
        print("Created client")

    def request(self, audio_filepath):
        if audio_filepath.startswith("//"):
            abspath = bpy.path.abspath("//")
            print(f"Normalizing to {abspath}")
            audio_filepath = abspath + audio_filepath[1:]
        print(f"Using audio @ {audio_filepath}")
        with open(audio_filepath, "rb") as infile: 
            data = infile.read()
            form = MultiPartForm()
            form.add_file('audio', os.path.basename(audio_filepath), fileHandle=io.BytesIO(data))
            data = bytes(form)
            r = request.Request('http://10.224.2.142:8080/', data=data)
            r.add_header(       'User-agent',        'PyMOTW (https://pymotw.com/)',    )
            r.add_header('Content-type', form.get_content_type())
            r.add_header('Content-length', len(data))
            with urllib.request.urlopen(r) as response:    
                frame_data = response.read()  
                return json.loads(frame_data)

