import os
import aiofiles
from typing import Optional
from gallerist.abc import FileStore, SyncFileStore, FileInfo


__all__ = ('FileSystemFileStore', 'FileSystemSyncFileStore')


class BaseFileSystemFileStore:

    def __init__(self, folder_name: Optional[str]):
        self.folder_name = folder_name

    def full_path(self, file_path: str):
        if not self.folder_name:
            return file_path
        return os.path.join(self.folder_name, file_path)


class FileSystemFileStore(FileStore, BaseFileSystemFileStore):

    async def read_file(self, file_path: str) -> bytes:
        async with aiofiles.open(self.full_path(file_path), mode='rb') as f:
            return await f.read()

    async def write_file(self, file_path: str, data: bytes, info: FileInfo):
        async with aiofiles.open(self.full_path(file_path), mode='wb') as f:
            await f.write(data)

    async def delete_file(self, file_path: str):
        try:
            os.remove(self.full_path(file_path))
        except FileNotFoundError:
            pass


class FileSystemSyncFileStore(SyncFileStore, BaseFileSystemFileStore):

    def read_file(self, file_path: str) -> bytes:
        with open(self.full_path(file_path), 'rb') as file:
            return file.read()

    def write_file(self, file_path: str, data: bytes, info: FileInfo):
        with open(self.full_path(file_path), 'wb') as file:
            file.write(data)

    def delete_file(self, file_path: str):
        try:
            os.remove(self.full_path(file_path))
        except FileNotFoundError:
            pass

