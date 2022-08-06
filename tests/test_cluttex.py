"""
cluttexイメージをテストする。
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import contextmanager, asynccontextmanager
import os
from pathlib import Path
import shutil
from typing import Union

import aiodocker
import docker
from docker.types import Mount
import pytest
from pytest import fixture


IMAGE_NAME: str = 'docker-images_cluttex'
HOST_PWD: str = os.environ['HOST_PWD']


@fixture
def client() -> docker.DockerClient:
    """Dockerのクライアントを作成するfixture"""
    return docker.from_env()


@fixture
def mount_data_tex_dir() -> Mount:
    """data/texに対するマウントを作成する"""
    return Mount(source=f'{HOST_PWD}/data/tex', target='/home/cluttex', type='bind')


@contextmanager
def run_container(
        client: docker.DockerClient,
        image: str,
        command: Union[list[str], None] = None,
        **kwargs
) -> docker.models.containers.Container:
    """
    Dockerイメージを実行してコンテナを返す。
    """
    container = client.containers.run(image, command, detach=True, **kwargs)
    try:
        yield container
    finally:
        container.remove()


def test_with_no_input(client: docker.DockerClient):
    """何も入力を渡さないときにステータス1で終了することを確認する"""
    with run_container(client, IMAGE_NAME) as container:
        result = container.wait()
        logs = container.logs().decode()

    assert logs != ''
    assert result['StatusCode'] == 1


def test_ls(client: docker.DockerClient, mount_data_tex_dir: Mount):
    """lsコマンドを実行してマウント位置が正しいことを確認する"""
    with run_container(
            client, IMAGE_NAME,
            entrypoint="bash -c 'ls -a'", mounts=[mount_data_tex_dir]
            ) as container:
        result = container.wait()
        file_list = container.logs().decode().splitlines()

    assert 'hello.tex' in file_list
    assert result['StatusCode'] == 0


def test_compile_oneshot(client: docker.DockerClient, mount_data_tex_dir: Mount):
    """一度だけコンパイルすることを確認する"""
    with run_container(
            client, IMAGE_NAME,
            ["-e", "lualatex", "hello"], mounts=[mount_data_tex_dir]
            ) as container:
        result = container.wait()
        logs = container.logs().decode()

    assert 'Output written on hello.pdf' in logs
    assert result['StatusCode'] == 0


@asynccontextmanager
async def run_cluttex_watch() -> AsyncIterator[aiodocker.docker.DockerContainer]:
    """
    `cluttex --watch -e lualatex hello`を実行するコンテナを起動する

    この場合は並行してログを見たいので非同期にしてある。
    あとでコンテナを削除するためにコンテクストマネージャとして実装している。
    """
    docker = aiodocker.Docker()
    config = {
        'Image': IMAGE_NAME,
        'Cmd': ['--watch', '-e', 'lualatex', 'hello'],
        'User': 'root',
        'HostConfig': {
            'Mounts': [
                {
                    "Type": "bind",
                    "Source": f'{HOST_PWD}/data/test_compile_watch',
                    "Target": "/home/cluttex",
                    "Mode": "",
                    "RW": True,
                    "Propagation": "rprivate",
                }
            ]
        }
    }
    container = await docker.containers.run(config)
    try:
        yield container
    finally:
        await container.kill()
        await container.delete()
        await docker.close()


async def output_log_waiter(container: aiodocker.docker.DockerContainer) -> AsyncIterator[str]:
    """
    Output writtenのログ行を見つけたらその行をgenerateするasync generator

    [ERROR]を見つけた場合はその場でストップする
    """
    log = container.log(stdout=True, stderr=True, follow=True)
    async for line in log:
        print(line.encode())
        if line.startswith('Output written on hello.pdf'):
            yield line
        if '[ERROR]' in line:
            raise StopAsyncIteration(line)


@pytest.mark.asyncio
async def test_compile_watch():
    """
    `--watch`オプション付きで起動した時に動作を確認する

    TeXファイルを書き換えた際に自動でコンパイルが走るかを確かめたい。
    """
    # /home/data/tex : 入力用のデータが置かれたディレクトリ
    # /home/data/test_compile_watch : テスト用のディレクトリ
    #
    # 生成されたPDFを確認したいことがあるので、後で削除することはしない。
    data_root = Path("/home/data")
    tex_dir = data_root / 'tex'
    tmp_dir = data_root / 'test_compile_watch'

    hello_tex = tex_dir / 'hello.tex'

    assert tex_dir.exists()
    assert hello_tex.exists()

    tmp_dir.mkdir(exist_ok=True)

    shutil.copyfile(hello_tex, tmp_dir / 'hello.tex')

    # ログを見ながら操作をする必要があるので非同期に実装する。
    async with run_cluttex_watch() as container:
        waiter = output_log_waiter(container)

        # hello.texは1ページからなるPDFを出力する。
        line1 = await asyncio.wait_for(waiter.__anext__(), timeout=60)

        shutil.copyfile(tex_dir / 'hello2.tex', tmp_dir / 'hello.tex')

        # hello2.texは2ページからなるPDFを出力する。
        line2 = await asyncio.wait_for(waiter.__anext__(), timeout=60)

    assert '1 page' in line1
    assert '2 pages' in line2
