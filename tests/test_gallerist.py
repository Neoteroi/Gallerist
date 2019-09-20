import os
import pytest
import asyncio
from shutil import rmtree
from gallerist.core import Gallerist, FileStore, SyncFileStore


if os.path.exists('out'):
    rmtree('out')

os.makedirs('out', exist_ok=True)


class FakeSyncStore(SyncFileStore):

    def __init__(self):
        self.folder_name = 'out'

    def _check_tests_folder(self, full_path):
        if os.path.isdir('tests'):
            return os.path.join('tests', full_path)
        return full_path

    def full_path(self, file_path: str):
        return self._check_tests_folder(os.path.join(self.folder_name, file_path))

    def read_file(self, file_path: str) -> bytes:
        with open(self._check_tests_folder(file_path), 'rb') as file:
            return file.read()

    def write_file(self, file_path: str, data: bytes):
        with open(self.full_path(file_path), 'wb') as file:
            file.write(data)

    def delete_file(self, file_path: str):
        try:
            os.remove(self.full_path(file_path))
        except FileNotFoundError:
            pass


class FakeStore(FakeSyncStore, FileStore):

    async def read_file(self, file_path: str) -> bytes:
        return await asyncio.get_event_loop().run_in_executor(None, super().read_file, file_path)

    async def write_file(self, file_path: str, data: bytes):
        return await asyncio.get_event_loop().run_in_executor(None, super().write_file, file_path, data)

    async def delete_file(self, file_path: str):
        return await asyncio.get_event_loop().run_in_executor(None, super().delete_file, file_path)


@pytest.mark.asyncio
@pytest.mark.parametrize('file_path', [
    'files/pexels-photo-126407.jpeg',
    'files/blacksheep.png',
    'files/01.gif',
    'files/small-png-01.png'
])
async def test_prepare_for_web_async(file_path: str):
    gallerist = Gallerist(FakeStore())

    metadata = await gallerist.process_image_async(file_path)

    assert metadata is not None


@pytest.mark.parametrize('file_path', [
    'files/pexels-photo-126407.jpeg',
    'files/blacksheep.png',
    'files/01.gif',
    'files/small-png-01.png'
])
def test_prepare_for_web_sync(file_path: str):
    gallerist = Gallerist(FakeSyncStore())

    metadata = gallerist.process_image(file_path)

    assert metadata is not None
