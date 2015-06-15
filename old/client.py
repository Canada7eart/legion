from __future__ import print_function
import subprocess as sp
import os
import json
if __name__ == "__main__":
    path = os.path.join(os.getcwd(), "task")
    config = {
        "ip-list":["127.0.0.1"]
    }
    json_string = "--json='%s'" % (json.dumps(config))
    print(json_string)
    proc = sp.Popen([path, "--server", json_string])
    proc.wait()
    print("Done.")