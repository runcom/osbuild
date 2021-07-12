#!/usr/bin/python3
"""
Create a boot filesystem tree, can be consumed to create
an efiboot.img.

"""
import contextlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import osbuild.remoteloop as remoteloop
import osbuild.api

SCHEMA_2 = """
"options": {
  "additionalProperties": false,
  "required": ["product", "kernel", "isolabel"],
  "properties": {
    "product": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "version"],
      "properties": {
        "name": {"type": "string"},
        "version": {"type": "string"}
       }
    },
    "kernel": {
      "type": "string"
    },
    "isolabel": {
      "type": "string"
    },
    "efi": {
      "type": "object",
      "additionalProperties": false,
      "required": ["architectures", "vendor"],
      "properties": {
        "architectures": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "vendor": {
            "type": "string"
        }
      }
    },
    "kernel_opts": {
      "description": "Additional kernel boot options",
      "type": "string"
    },
    "templates": {
      "type": "string",
      "default": "99-generic"
    }
  }
},
"inputs": {
  "type": "object",
  "additionalProperties": false,
  "required": ["rootfs"],
  "properties": {
    "rootfs": {
      "type": "object",
      "additionalProperties": true
    },
    "kernel": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
"""

LORAX_TEMPLATES = "/usr/share/lorax/templates.d"

@contextlib.contextmanager
def mount(source, dest):
    subprocess.run(["mount", source, dest], check=True)
    try:
        yield dest
    finally:
        subprocess.run(["umount", "-R", dest], check=True)  

def install(src, dst, mode=None):
    shutil.copyfile(src, dst)
    if mode:
        os.chmod(dst, mode)

def replace(target, patterns):
    finder = [(re.compile(p), s) for p, s in patterns]
    newfile = target + ".replace"

    with open(target, "r") as i, open(newfile, "w") as o:
        for line in i:
            for p, s in finder:
                line = p.sub(s, line)
            o.write(line)
    os.rename(newfile, target)

def main(inputs, root, options, workdir, loop_client):
    name = options["product"]["name"]
    version = options["product"]["version"]
    kernel = options["kernel"]
    isolabel = options["isolabel"]
    templates = options["templates"]
    efi = options.get("efi")
    kopts = options.get("kernel_opts")

    # input directories
    templatedir = os.path.join(LORAX_TEMPLATES, templates)
    configdir = os.path.join(templatedir, "config_files", "x86")

    # output directories
    imgdir = os.path.join(root, "images")
    pxedir = os.path.join(imgdir, "pxeboot")

    os.makedirs(imgdir)

    cmdline = f"edge.liveiso={isolabel}"
    if kopts:
        cmdline += " " + kopts

    info = {
        "version": version,
        "name": name,
        "isolabel": isolabel,
        "workdir": workdir,
        "configdir": configdir,
        "kerneldir": pxedir,
        "imgdir": imgdir,
        "cmdline": cmdline
    }

    #install the kernel
    kerneldir = pxedir
    kernel_input = inputs.get("kernel", inputs["rootfs"])
    kernel_tree = kernel_input["path"]
    bootdir = os.path.join(kernel_tree, "boot")

    os.makedirs(kerneldir)
    install(os.path.join(bootdir, f"vmlinuz-{kernel}"),
            os.path.join(kerneldir, "vmlinuz"))

    install(os.path.join(bootdir, f"initramfs-{kernel}.img"),
            os.path.join(kerneldir, "initrd.img"))

    # install(os.path.join(diskimgpath, "disk.img.xz"),
    #         os.path.join(root, "disk.img.xz"))

    # TODO(runcom): fixes

    arches = efi["architectures"]
    vendor = efi["vendor"]

    efidir = os.path.join(root, "EFI", "BOOT")
    os.makedirs(efidir)

    #arch related data
    for arch in arches:
        arch = arch.lower()
        targets = [
            (f"shim{arch}.efi", f"BOOT{arch}.EFI".upper()),
            (f"mm{arch}.efi", f"mm{arch}.efi"),
            (f"gcd{arch}.efi", f"grub{arch}.efi")
        ]

        for src, dst in targets:
            shutil.copy2(os.path.join("/boot/efi/EFI/", vendor, src),
                         os.path.join(efidir, dst))

    # the font
    fontdir = os.path.join(efidir, "fonts")
    os.makedirs(fontdir, exist_ok=True)
    shutil.copy2("/usr/share/grub/unicode.pf2", fontdir)

    # the config
    configdir = info["configdir"]
    version = info["version"]
    name = info["name"]
    isolabel = info["isolabel"]
    cmdline = info["cmdline"]

    kdir = "/" + os.path.relpath(info["kerneldir"], start=root)
    print(f"kernel dir at {kdir}")

    config = os.path.join(efidir, "grub.cfg")
    shutil.copy2(os.path.join(configdir, "grub2-efi.cfg"), config)

    replace(config, [
        ("@VERSION@", version),
        ("@PRODUCT@", name),
        ("@KERNELNAME@", "vmlinuz"),
        ("@KERNELPATH@", os.path.join(kdir, "vmlinuz")),
        ("@INITRDPATH@", os.path.join(kdir, "initrd.img")),
        ("@ISOLABEL@", isolabel),
        ("@ROOT@", cmdline)
    ])

    if "IA32" in arches:
        shutil.copy2(config, os.path.join(efidir, "BOOT.cfg"))

    # # estimate the size
    # blocksize = 2048
    # size = blocksize * 256  # blocksize * overhead
    # for parent, dirs, files in os.walk(efidir):
    #     for name in files + dirs:
    #         t = os.path.join(parent, name)
    #         s = os.stat(t).st_size
    #         d = s % blocksize
    #         if not s or d:
    #             s += blocksize - d
    #         size += s
    # print(f"Estimates efiboot size to be {size}")

    # # create the image
    # image = os.path.join(info["imgdir"], "efiboot.img")
    # with open(image, "w") as f:
    #     os.ftruncate(f.fileno(), size)

    # root = os.path.join(info["workdir"], "mnt")
    # os.makedirs(root)

    # with loop_client.device(image, 0, size) as dev:
    #     subprocess.run(["mkfs.fat",
    #                     "-n", "COI",
    #                     dev],
    #                    input="y", encoding='utf-8', check=True)

    #     with mount(dev, root):
    #         target = os.path.join(root, "EFI", "BOOT")
    #         shutil.copytree(efidir, target)
    #     subprocess.run(["ls", root], check=True)

if __name__ == '__main__':
    args = osbuild.api.arguments()
    _output_dir = args["tree"]
    with tempfile.TemporaryDirectory(dir=_output_dir) as _workdir:
        ret = main(args["inputs"],
                   _output_dir,
                   args["options"],
                   _workdir,
                   remoteloop.LoopClient("/run/osbuild/api/remoteloop"))
    sys.exit(ret)
