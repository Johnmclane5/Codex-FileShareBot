from requests import get as rget
import os

CONFIG_FILE_URL = os.environ.get('CONFIG_FILE_URL')
try:
    if len(CONFIG_FILE_URL) == 0:
        raise TypeError
    try:
        res = rget(CONFIG_FILE_URL)
        if res.status_code == 200:
            with open('.env', 'wb+') as f:
                f.write(res.content)
        else:
            print(f"Failed to download info.py {res.status_code}")
    except Exception as e:
        print(f"CONFIG_FILE_URL: {e}")
except Exception as e:
    print(e)
    pass