import os
import json
import time
import subprocess


url = 'https://bing.com/chat'
model = ['gpt-3.5-turbo', 'gpt-4']
supports_stream = True

def _create_completion(model: str, messages: list, stream: bool, **kwargs):
    path = os.path.dirname(os.path.realpath(__file__))
    config = json.dumps({
        'messages': messages,
        'model': model}, separators=(',', ':'))
    
    cmd = ['python', f'{path}/bing_helper.py', config]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in iter(p.stdout.readline, b''):
        #print(line)
        yield line.decode('utf-8') #[:-1]

        
