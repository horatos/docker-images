import docker
from docker.types import Mount
import os
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



def test_with_no_input(client):
    """何も入力を渡さないときに正常に終了することを確認する"""
    container = client.containers.run(IMAGE_NAME, detach=True)

    result = container.wait()
    print(container.logs().decode())

    container.remove()

    assert result['StatusCode'] == 0


def test_ls(client, mount_test_dir):
    """lsコマンドを実行してマウント位置が正しいことを確認する"""
    cnt = client.containers.run(IMAGE_NAME, ['-c', 'ls -a'], entrypoint='bash',
            mounts=[mount_test_dir], remove=True)

    file_list = cnt.decode().splitlines()

    assert 'test_textlint-ja.py' in file_list


def test_ja_md(client, mount_test_dir):
    """Markdownファイルのlintができることを確認する"""
    container = client.containers.run(IMAGE_NAME, ['--preset', 'preset-japanese', 'data/ja.md'], mounts=[mount_test_dir], detach=True)

    result = container.wait()
    print(container.logs().decode())

    container.remove()

    assert result['StatusCode'] == 0


def test_latex_ja(client, mount_data_tex_dir):
    """LaTeXファイルのlintができることを確認する"""
    container = client.containers.run(IMAGE_NAME, '*.tex', mounts=[mount_data_tex_dir], detach=True)

    result = container.wait()
    output = container.logs().decode()

    container.remove()

    assert output == ''
    assert result['StatusCode'] == 0
