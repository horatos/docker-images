import os
from contextlib import contextmanager

import docker
from docker.types import Mount
from pytest import fixture


IMAGE_NAME='docker-images_textlint-ja'
HOST_PWD=os.environ['HOST_PWD']


@fixture
def client():
    return docker.from_env()


@fixture
def mount_test_dir():
    return Mount(source=f'{HOST_PWD}/tests', target='/home/node/app', type='bind')


@fixture
def mount_data_tex_dir():
    return Mount(source=f'{HOST_PWD}/data/tex', target='/home/node/app', type='bind')


@contextmanager
def run_container(client, image, command=None, **kwargs):
    container = client.containers.run(image, command, detach=True, **kwargs)
    try:
        yield container
    finally:
        container.remove()


def test_with_no_input(client):
    """何も入力を渡さないときに正常に終了することを確認する"""
    with run_container(client, IMAGE_NAME) as container:
        result = container.wait()
        logs = container.logs().decode()

    assert logs != ''
    assert result['StatusCode'] == 0


def test_ls(client, mount_test_dir):
    """lsコマンドを実行してマウント位置が正しいことを確認する"""
    with run_container(client, IMAGE_NAME, entrypoint="bash -c 'ls -a'", mounts=[mount_test_dir]) as container:
        result = container.wait()
        file_list = container.logs().decode().splitlines()

    assert 'test_textlint-ja.py' in file_list


def test_md_ja(client, mount_test_dir):
    """Markdownファイルのlintができることを確認する"""
    with run_container(client, IMAGE_NAME, ['--preset', 'preset-japanese', 'data/ja.md'], mounts=[mount_test_dir]) as container:
        result = container.wait()
        logs = container.logs().decode()

    assert logs == ''
    assert result['StatusCode'] == 0


def test_latex_ja(client, mount_data_tex_dir):
    """LaTeXファイルのlintができることを確認する"""
    with run_container(client, IMAGE_NAME, '*.tex', mounts=[mount_data_tex_dir]) as container:
        result = container.wait()
        logs = container.logs().decode()

    assert logs == ''
    assert result['StatusCode'] == 0
