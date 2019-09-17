import os
import pytest
from typing import BinaryIO
from gallerist.core import Gallerist, ImageStore


os.makedirs('out', exist_ok=True)


class NoopStore(ImageStore):

    async def store_picture_metadata(self):
        pass

    async def read_file(self, file_path: str) -> BinaryIO:
        pass

    async def write_file(self, file_path: str, stream: BinaryIO):
        pass

    async def delete_file(self, file_path: str):
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize('file_path,file_name_fn,image_format', [
    ['files/pexels-photo-126407.jpeg', lambda i: f'jpg_{i}.jpg', 'JPEG'],
    ['files/png_01.png', lambda i: f'png_{i}.png', 'PNG'],
    ['files/01.gif', lambda i: f'gif_{i}.gif', 'GIF']
])
async def test_prepare_for_web(file_path, file_name_fn, image_format):
    gallerist = Gallerist(NoopStore())

    with open(file_path, 'rb') as file:
        i = 0
        for version, image in gallerist.prepare_images(file, image_format):
            i += 1
            with open(os.path.join('out', file_name_fn(i)), 'wb') as ff:
                ff.write(image)
