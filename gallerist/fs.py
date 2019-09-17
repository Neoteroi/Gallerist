import os
import aiofiles
from typing import BinaryIO
from gallerist.abc import FileStore, ImageStore


class FileSystemFileStore(FileStore):

    async def read_file(self, file_path: str) -> BinaryIO:
        async with aiofiles.open(file_path, mode='rb') as f:
            return await f.read()

    async def write_file(self, file_path: str, stream: BinaryIO):
        async with aiofiles.open(file_path, mode='wb') as f:
            await f.write(stream)

    async def delete_file(self, file_path: str):
        os.remove(file_path)


class FileSystemImageStore(FileSystemFileStore, ImageStore):

    async def store_picture_metadata(self):
        pass
