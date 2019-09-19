import os
import pytest
from shutil import rmtree
from gallerist.core import Gallerist, FileStore


if os.path.exists('out'):
    rmtree('out')

os.makedirs('out', exist_ok=True)


class FakeStore(FileStore):

    def __init__(self):
        self.folder_name = 'out'

    def full_path(self, file_path: str):
        return os.path.join(self.folder_name, file_path)

    async def read_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as file:
            return file.read()

    async def write_file(self, file_path: str, data: bytes):
        with open(self.full_path(file_path), 'wb') as file:
            file.write(data)

    async def delete_file(self, file_path: str):
        try:
            os.remove(self.full_path(file_path))
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize('file_path', [
    'files/pexels-photo-126407.jpeg',
    'files/blacksheep.png',
    'files/01.gif',
    'files/small-png-01.png'
])
async def test_prepare_for_web(file_path: str):
    gallerist = Gallerist(FakeStore())

    metadata = await gallerist.process_image_async(file_path)

    assert metadata is not None

