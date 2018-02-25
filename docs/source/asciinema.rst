How to make a new gif
=====================

* Recording: `asciinema rec -w 1 -c=ipython3 conu.json` (needs `asciinema` `pip3`/`dnf` package)
* Making a gif: `docker run --rm -v $PWD:/data:z asciinema/asciicast2gif -s 2 conu.json conu.gif`

(Cut the size with `-w <columns> -h <rows>`.)


Scenario:

.. code-block:: python

    from conu import DockerBackend
    backend = DockerBackend()


    image = backend.ImageClass('docker.io/library/nginx')

    container = image.run_via_binary()

    assert container.is_running()
    container.get_IPv4s()
    container.get_ports()

    resp = container.http_request(port=80)
    assert resp.ok
    resp.text

    container.stop()
    container.is_running()

    ############ clean screen ###############

    from conu import DockerRunBuilder

    run_params = DockerRunBuilder(additional_opts=['-e HELLO=hello'], command=['env'])
    container = image.run_via_binary(run_params)
    for l in container.logs():
        print(l)


    ############ clean screen ###############

    with container.mount() as fs:
        assert fs.file_is_present('/etc/nginx/nginx.conf')
