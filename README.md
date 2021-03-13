[![Build](https://github.com/Neoteroi/Gallerist/actions/workflows/build.yml/badge.svg)](https://github.com/Neoteroi/Gallerist/actions/workflows/build.yml)
[![pypi](https://img.shields.io/pypi/v/gallerist.svg)](https://pypi.python.org/pypi/gallerist)
[![versions](https://img.shields.io/pypi/pyversions/gallerist.svg)](https://github.com/Neoteroi/gallerist)
[![codecov](https://codecov.io/gh/Neoteroi/Gallerist/branch/main/graph/badge.svg?token=oiCOiKgSbm)](https://codecov.io/gh/Neoteroi/Gallerist)
[![license](https://img.shields.io/github/license/Neoteroi/gallerist.svg)](https://github.com/Neoteroi/gallerist/blob/main/LICENSE)

# Gallerist
Classes and methods to handle pictures for the web, using
[Pillow](https://pillow.readthedocs.io).

```bash
$ pip install gallerist
```

## Features
* Code api to handle the generation of pictures in various sizes (e.g. medium
  size picture, small size, thumbnail)
* Both asynchronous api and synchronous api
* Supports user defined stores for binaries, for example to read and write
  files in [Azure Blob
  Storage](https://azure.microsoft.com/en-us/services/storage/blobs/), or [AWS
  S3](https://aws.amazon.com/s3/)
* Handles by default JPG, PNG, GIF, MPO; and provides a code api to support
  adding more supported formats
* Supports scaling animated GIF files (resized gifs are still animated)
* Maintains PNG transparencies

## See also
* [Gallerist Azure Storage Blob Service integration](https://github.com/Neoteroi/Gallerist-AzureStorage)
* [Gallerist Azure Functions integration](https://github.com/Neoteroi/Gallerist-AzureFunctions)

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


store = FileSystemSyncFileStore("tests")

# configuring sizes by mime (use '*' to match any other mime):
gallerist = Gallerist(
    store,
    sizes={
        "image/jpeg": [ImageSize("a", 500), ImageSize("b", 400), ImageSize("c", 300)],
        "image/png": [ImageSize("a", 350), ImageSize("b", 250), ImageSize("c", 150)],
    },
)

metadata = gallerist.process_image("files/pexels-photo-126407.jpeg")

print(metadata)
```

The original picture is not modified, it is only read to produce more images
in other sizes.

Metadata:

```
<ImageMetadata width=2520 height=1418 extension=".jpg" mime="image/jpeg" versions=[
  <ImageVersion
    size_name="a"
    id="bbf665ba8dd3412a84ac435a086fc7ad"
    max_side=500
    file_name="a-bbf665ba8dd3412a84ac435a086fc7ad.jpg"
  >,
  <ImageVersion
    size_name="b"
    id="7e4b38b977964c2a91544c1e0621c3a1"
    max_side=400
    file_name="b-7e4b38b977964c2a91544c1e0621c3a1.jpg"
  >,
  <ImageVersion
    size_name="c"
    id="847cad2796004b5086269bec9d705cdc"
    max_side=300
    file_name="c-847cad2796004b5086269bec9d705cdc.jpg"
  >
]>
```
## Implementing a custom file store

Custom stores must implement one of the following protocols:

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
