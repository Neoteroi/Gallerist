from abc import ABC, abstractmethod
from typing import BinaryIO


class ImageStore(ABC):

    @abstractmethod
    async def store_image(self, file_name: str, file_type: str, image: BinaryIO):
        """Stores an image with given name and type"""


