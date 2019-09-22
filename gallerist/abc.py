from abc import ABC, abstractmethod
from typing import Union


class FileInfo:

    __slots__ = ('mime', 'extension')

    def __init__(self, mime: str, extension: str):
        self.mime = mime
        self.extension = extension

    def __repr__(self):
        return f'<FileInfo mime="{self.mime}" extension="{self.extension}">'

    def to_dict(self):
        return {
            'mime': self.mime,
            'extension': self.extension
        }


class FileStore(ABC):
    """A store that operates on files asynchronously."""

    @abstractmethod
    async def read_file(self, file_path: str) -> bytes:
        """Returns file contents by its unique path"""

    @abstractmethod
    async def write_file(self, file_path: str, data: bytes, info: FileInfo):
        """Writes a file to a given unique path"""

    @abstractmethod
    async def delete_file(self, file_path: str):
        """Deletes a file"""


class SyncFileStore(ABC):
    """A store that operates on files synchronously."""

    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        """Returns file contents by its unique path"""

    @abstractmethod
    def write_file(self, file_path: str, data: bytes, info: FileInfo):
        """Writes a file to a given unique path"""

    @abstractmethod
    def delete_file(self, file_path: str):
        """Deletes a file"""


FileStoreType = Union[FileStore, SyncFileStore]
