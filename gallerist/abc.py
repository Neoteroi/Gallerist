from abc import ABC, abstractmethod
from typing import BinaryIO, Union


class FileStore(ABC):

    @abstractmethod
    async def read_file(self, file_path: str) -> BinaryIO:
        """Reads a file stream by its unique path"""

    @abstractmethod
    async def write_file(self, file_path: str, stream: BinaryIO):
        """Writes a file to a given unique path"""

    @abstractmethod
    async def delete_file(self, file_path: str):
        """Deletes a file"""


class SyncFileStore(ABC):

    @abstractmethod
    def read_file(self, file_path: str) -> BinaryIO:
        """Reads a file stream by its unique path"""

    @abstractmethod
    def write_file(self, file_path: str, stream: BinaryIO):
        """Writes a file to a given unique path"""

    @abstractmethod
    def delete_file(self, file_path: str):
        """Deletes a file"""


FileStoreType = Union[FileStore, SyncFileStore]  # go down this path, to offer both a sync and an async API?


class ImageStore(FileStore):
    """File store specialized for pictures"""

    @abstractmethod
    async def store_picture_metadata(self):
        """Stores metadata about a picture."""
