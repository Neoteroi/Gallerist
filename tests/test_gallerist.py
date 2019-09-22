import os
import pytest
import asyncio
from shutil import rmtree
from gallerist.core import Gallerist, FileStore, SyncFileStore, FileInfo, Image


out_path = os.path.join('test', 'out') if os.path.isdir('tests') else 'out'

if os.path.exists(out_path):
    rmtree(out_path)

os.makedirs(out_path, exist_ok=True)


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

    def write_file(self, file_path: str, data: bytes, info: FileInfo):
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

    async def write_file(self, file_path: str, data: bytes, info: FileInfo):
        return await asyncio.get_event_loop().run_in_executor(None, super().write_file, file_path, data, info)

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

    for version in metadata.versions:
        image = Image.open(gallerist.store.full_path(version.file_name))
        assert image is not None
        image.close()


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

    for version in metadata.versions:
        image = Image.open(gallerist.store.full_path(version.file_name))
        assert image is not None
        image.close()


def test_cmyk_gets_converted_to_rgb():
    gallerist = Gallerist(FakeSyncStore())

    metadata = gallerist.process_image('files/channel_digital_image_CMYK_color.jpg')

    assert metadata is not None

    medium_size_picture = [version for version in metadata.versions if version.size_name == 'medium'][0]

    image = Image.open(gallerist.store.full_path(medium_size_picture.file_name))

    assert image.mode == 'RGB'

    image.close()
