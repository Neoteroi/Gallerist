import pytest
from typing import BinaryIO
from gallerist.core import Gallerist, ImageStore, GifFormat
from gallerist.giftest import resize_to_max_side
from io import BytesIO
from PIL import Image


class NoopStore(ImageStore):

    async def store_image(self, file_name: str, file_type: str, image: BinaryIO):
        pass


@pytest.mark.asyncio
async def test_prepare_for_web():
    gallerist = Gallerist(NoopStore())
    gif = GifFormat()
    with open('files/gif-05.gif', 'rb') as file:
        i = 0

        for size in [300, 200, 100]:
            i += 1
            image = resize_to_max_side(Image.open(file), size)

            with open(f'test-{i}.gif', 'wb') as f:
                b = gif.to_bytes(image)
                b.seek(0)
                f.write(b.read())

        """
        for image in gallerist.prepare_images(file):
            i += 1
            with open(f'A{i}.gif', 'wb') as ff:
                ff.write(image.read())
        """
        # metadata = gallerist.upload_image(file)

    # assert metadata is not None

