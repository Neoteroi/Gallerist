import pytest
from typing import BinaryIO
from gallerist.core import Gallerist, ImageStore


class NoopStore(ImageStore):

    async def store_image(self, file_name: str, file_type: str, image: BinaryIO):
        pass


@pytest.mark.asyncio
async def test_prepare_for_web():
    gallerist = Gallerist(NoopStore())

    with open('files/01.png', 'rb') as file:
        i = 0
        for image in gallerist.prepare_images(file):
            i += 1
            with open(f'A{i}.png', 'wb') as ff:
                ff.write(image.read())


