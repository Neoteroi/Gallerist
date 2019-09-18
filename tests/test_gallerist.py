import os
import pytest
from typing import BinaryIO
from gallerist.core import Gallerist, FileStore


os.makedirs('out', exist_ok=True)


class NoopStore(FileStore):

    async def store_picture_metadata(self):
        pass

    async def read_file(self, file_path: str) -> BinaryIO:
        pass

    async def write_file(self, file_path: str, stream: BinaryIO):
        pass

    async def delete_file(self, file_path: str):
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize('file_path,file_name_fn', [
    # ['files/01.png', lambda i: f'png_{i}.png'],
    ['files/01.gif', lambda i: f'zgif_{i}.gif']
])
async def test_prepare_for_web(file_path, file_name_fn):
    gallerist = Gallerist(NoopStore())

    with open(file_path, 'rb') as file:
        i = 0
        for version, image in gallerist.prepare_images(file):
            i += 1
            with open(os.path.join('out', file_name_fn(i)), 'wb') as ff:
                ff.write(image)
