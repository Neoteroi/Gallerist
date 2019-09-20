# Gallerist
Classes and methods to handle pictures for the web, using [Pillow](https://pillow.readthedocs.io).

```bash
$ pip install gallerist
```

## Features
* Code api to handle the generation of pictures in various sizes (e.g. medium size picture, small size, thumbnail)
* Both asynchronous api and synchronous api
* Supports user defined stores for binaries, for example to read and write files in [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/), or [AWS S3](https://aws.amazon.com/s3/)
* Supports scaling animated GIF files
* Maintain PNG transparencies
* Handles by default JPG, PNG, GIF, MPO; and provides a code api to support adding more supported formats

## Examples
Basic example using the synchronous api, and reading files from file system:

```python
from gallerist import Gallerist
from gallerist.fs import FileSystemSyncFileStore


gallerist = Gallerist(FileSystemSyncFileStore('tests'))


metadata = gallerist.process_image('files/blacksheep.png')
```

#### Configuring sizes

```python
from gallerist import Gallerist, ImageSize
from gallerist.fs import FileSystemSyncFileStore


store = FileSystemSyncFileStore('tests')

# configuring sizes by mime (use '*' to match any mime):
gallerist = Gallerist(store, sizes={
    'image/jpeg': [
        ImageSize('a', 500),
        ImageSize('b', 400),
        ImageSize('c', 300)
    ],
    'image/png': [
        ImageSize('a', 350),
        ImageSize('b', 250),
        ImageSize('c', 150)
    ]
})
```

#### Implementing a custom file store

```python
from gallerist.abc import FileStore, SyncFileStore


class MyAsyncFileStore(FileStore):
    """Implement your async file store, then use gallerist.process_image_async method"""

    async def read_file(self, file_path: str) -> bytes:
        pass

    async def write_file(self, file_path: str, data: bytes):
        pass

    async def delete_file(self, file_path: str):
        pass


class MySyncFileStore(SyncFileStore):
    """Implement your sync file store, then use gallerist.process_image method"""

    def read_file(self, file_path: str) -> bytes:
        pass

    def write_file(self, file_path: str, data: bytes):
        pass

    def delete_file(self, file_path: str):
        pass

```
