import os
import pytest
from shutil import rmtree
from typing import BinaryIO
from gallerist.core import Gallerist, FileStore


rmtree('out')
os.makedirs('out', exist_ok=True)


class FakeStore(FileStore):

    def __init__(self):
        self.folder_name = 'out'

    def full_path(self, file_path: str):
        return os.path.join(self.folder_name, file_path)

    async def read_file(self, file_path: str) -> BinaryIO:
        return open(file_path, 'rb')

    async def write_file(self, file_path: str, stream: BinaryIO):
        with open(self.full_path(file_path), 'wb') as file:
            stream.seek(0)
            file.write(stream.read())

    async def delete_file(self, file_path: str):
        try:
            os.remove(self.full_path(file_path))
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize('file_path,image_format', [
    ['files/pexels-photo-126407.jpeg', 'JPEG'],
    ['files/blacksheep.png', 'PNG'],
    ['files/01.gif', 'GIF']
])
async def test_prepare_for_web(file_path: str, image_format: str):
    gallerist = Gallerist(FakeStore())

    metadata = await gallerist.process_image_async(file_path, image_format)

    assert metadata is not None

