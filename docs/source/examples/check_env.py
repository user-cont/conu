import subprocess

from conu import DockerBackend, DockerRunBuilder

image = DockerBackend.ImageClass('fedora')
cmd = DockerRunBuilder(additional_opts=['-i', '-e', 'KEY=space'])

cont = image.run_via_binary_in_foreground(cmd, popen_params={"stdin": subprocess.PIPE})

try:
    assert cont.is_running()
    assert cont.logs() == b''

    cont.active_write(message=b'echo $KEY\n')
    assert cont.logs() == b'space\n'
finally:
    cont.delete(force=True)
