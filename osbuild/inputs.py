
import json
import subprocess


def export(ip, store, output, libdir):

    msg = {
        "options": ip.options or {},
        "output": output,
        "origin": ip.type,
        "store": store.store,
    }

    r = subprocess.run(
        [f"{libdir}/inputs/{ip.form}"],
        input=json.dumps(msg),
        stdout=subprocess.PIPE,
        encoding="utf-8",
        check=False)

    reply = json.loads(r.stdout)

    if "error" in reply:
        raise RuntimeError(f"{ip.name}: " + reply["error"])

    if r.returncode != 0:
        raise RuntimeError(f"{ip.name}: error {r.returncode}")

    data = {
        "type": ip.type,
        "meta": {
            "options": ip.options
        },
        **reply
    }

    return data
