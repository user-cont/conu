How to make a new gif
=====================

* Recording: `asciinema rec -w 1 -c=ipython3 conu.json`
* Making a gif: `docker run --rm -v $PWD:/data:z asciinema/asciicast2gif -s 2 conu.json conu.gif`

(Cut the size with `-w <columns> -h <rows>`.)


Scenario:

.. code-block:: python

    import logging
    from conu import DockerBackend
    backend = DockerBackend(logging_level=logging.DEBUG)

    image = backend.ImageClass('docker.io/library/nginx')
    container = image.run_via_binary()
    assert container.is_running()

    container.stop()
    assert container.is_running()

    ############ clear screen #################

    from conu import DockerRunBuilder
    run_params = DockerRunBuilder(additional_opts=['--rm'], command=['echo', "Hello world!"])
    container = image.run_via_binary(run_params)
    container.logs().decode('utf-8')

    container.wait_for_port(80, timeout=20)

    container.http_request(port=80)
    assert http_response.ok

    http_response.text

    ############ clear screen #################

    with container.mount() as fs:
        assert fs.file_is_present('/etc/nginx/nginx.conf')
        index_path = '/usr/share/nginx/html/index.html'
        assert fs.file_is_present(index_path)
        index_text = fs.read_file('/usr/share/nginx/html/index.html')
        assert '<h1>Welcome to nginx!</h1>' in index_text
