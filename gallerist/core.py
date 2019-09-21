import os
import uuid
import asyncio
from io import BytesIO
from asyncio import AbstractEventLoop
from typing import Sequence, Optional, Dict, List, Generator
from gallerist.abc import FileStoreType, FileStore, SyncFileStore
from PIL import Image, ImageSequence


def exception_str(ex):
    return str(ex) or ex.__class__.__name__


def get_file_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension


class ImageWrapper:

    __slots__ = ('image', 'frames')

    def __init__(self, image, frames=None):
        self.image = image
        self.frames = frames

    @property
    def n_frames(self):
        if self.frames:
            return len(self.frames)
        # frames count can be known, while actual frames are not loaded in memory
        return getattr(self.image, 'n_frames', 1)

    @property
    def is_animated(self):
        return bool(self.frames)

    @property
    def info(self):
        return self.image.info

    @property
    def format(self):
        return self.image.format

    @format.setter
    def format(self, value):
        self.image.format = value

    @classmethod
    def from_frames(cls, frames):
        return cls(frames[0], frames)

    def load_frames(self):
        self.frames = list(ImageSequence.Iterator(self.image))


class ImageFormat:

    def __init__(self,
                 mime: str,
                 name: str,
                 extension: str,
                 quality: int):
        self.mime = mime
        self.name = name
        self.extension = extension
        self.quality = quality

    def __repr__(self):
        return f'<ImageFormat mime="{self.mime}" name="{self.name}" ' \
               f'extension="{self.extension}" quality="{self.quality}">'

    def to_bytes(self, wrapper: ImageWrapper) -> bytes:
        image = wrapper.image
        byte_io = BytesIO()
        if self.quality > 0:
            image.save(byte_io, image.format, quality=self.quality)
        else:
            image.save(byte_io, image.format)
        byte_io.seek(0)
        return byte_io.read()


class JpegFormat(ImageFormat):

    def __init__(self):
        super().__init__('image/jpeg', 'JPEG', '.jpg', 80)


class PJpegFormat(ImageFormat):

    def __init__(self):
        super().__init__('image/pjpeg', 'JPEG', '.jpg', 80)


class PngFormat(ImageFormat):

    def __init__(self):
        super().__init__('image/png', 'PNG', '.png', -1)


class MpoFormat(ImageFormat):

    def __init__(self):
        super().__init__('image/mpo', 'JPEG', '.jpg', 80)


class GifFormat(ImageFormat):

    def __init__(self):
        super().__init__('image/gif', 'GIF', '.gif', -1)

    def to_bytes(self, wrapper: ImageWrapper) -> bytes:
        if wrapper.n_frames == 1:
            return super().to_bytes(wrapper)
        byte_io = BytesIO()

        if not wrapper.frames:
            wrapper.load_frames()

        wrapper.frames[0].save(byte_io,
                               format=self.name,
                               optimize=True,
                               save_all=True,
                               append_images=wrapper.frames[1:],
                               duration=wrapper.info.get('duration', 100),
                               loop=0)
        byte_io.seek(0)
        return byte_io.read()


class ImageSize:
    __slots__ = ('name', 'resize_to')

    def __init__(self,
                 name: str,
                 resize_to: int):
        self.name = name
        self.resize_to = resize_to

    def __repr__(self):
        return f'<ImageSize name="{self.name}" resize_to={self.resize_to}>'


ImageSizesType = Dict[str, Sequence[ImageSize]]


class ImageVersion:

    __slots__ = ('size_name', 'id', 'max_side', 'file_name')

    def __init__(self,
                 size_name: str,
                 id: str,
                 max_side: int,
                 file_name: str = None):
        self.size_name = size_name
        self.id = id
        self.max_side = max_side
        self.file_name = file_name

    def __repr__(self):
        return f'<ImageVersion size_name="{self.size_name}" id="{self.id}" ' \
               f'max_side={self.max_side} file_name="{self.file_name}">'


class ImageMetadata:

    __slots__ = ('width', 'height', 'extension', 'mime', 'versions')

    def __init__(self,
                 width: int,
                 height: int,
                 extension: str,
                 mime: str,
                 versions: List[ImageVersion]):
        self.width = width
        self.height = height
        self.extension = extension
        self.mime = mime
        self.versions = versions

    def __repr__(self):
        return f'<ImageMetadata width={self.width} height={self.height} ' \
               f'extension="{self.extension}" mime="{self.mime}" versions={self.versions}>'

    @property
    def ratio(self) -> float:
        return self.width / self.height


class GalleristError(Exception):
    """Base class for exceptions risen by Gallerist class"""


class MissingImageFormatError(GalleristError):

    def __init__(self):
        super().__init__('Cannot determine image format, please specify it.')


class SizesNotConfiguredForMimeError(GalleristError):

    def __init__(self, image_mime: str):
        super().__init__(f'Image sizes are not configured for mime `{image_mime}`; '
                         f'to correct, use the `sizes` option of the Gallerist constructor; '
                         f'or override `default_sizes` in a base class')


class FormatNotConfiguredWithNameError(GalleristError):

    def __init__(self, format_name: str):
        super().__init__(f'Image format not configured with name `{format_name}`; '
                         f'to correct, use the `formats` option of the Gallerist constructor; '
                         f'or override `default_formats` in a base class')


class FormatNotConfiguredForMimeError(GalleristError):

    def __init__(self, image_mime: str):
        super().__init__(f'Image formats are not configured for mime `{image_mime}`; '
                         f'to correct, use the `formats` option of the Gallerist constructor; '
                         f'or override `default_formats` in a base class')


class InvalidStoreTypeError(GalleristError):
    """Base class for errors related to invalid store configuration."""


class ExpectedSyncStoreError(InvalidStoreTypeError):

    def __init__(self):
        super().__init__(f'A synchronous file store, inheriting {SyncFileStore.__name__}, is required to '
                         f'run the synchronous `process_image`')


class ExpectedAsyncStoreError(InvalidStoreTypeError):

    def __init__(self):
        super().__init__(f'An asynchronous file store, inheriting {FileStore.__name__}, is required to '
                         f'run the asynchronous `process_image_async`')


class SourceImageNotFoundError(GalleristError):

    def __init__(self):
        super().__init__('The source image was not found, or could not be loaded.')


class Gallerist:
    """Provides methods to prepare images in various sizes and store them with metadata."""

    def __init__(self,
                 store: FileStoreType,
                 sizes: Optional[ImageSizesType] = None,
                 formats: Optional[Sequence[ImageFormat]] = None):
        self._sizes = None
        self.store = store
        self.formats = formats or self.default_formats
        self.sizes = sizes or self.default_sizes

    default_sizes = {
        '*': (ImageSize('medium', 1200),
              ImageSize('thumbnail', 200)),
        'image/gif': (ImageSize('medium', 200),
                      ImageSize('thumbnail', 120))
    }

    default_formats = [
        JpegFormat(),
        PJpegFormat(),
        PngFormat(),
        GifFormat(),
        MpoFormat()
    ]

    def is_handled_mime(self, mime_type: str):
        for handled_format in self.formats:
            if handled_format.mime == mime_type:
                return True
        return False

    @property
    def sizes(self):
        return self._sizes

    @sizes.setter
    def sizes(self, value: Optional[ImageSizesType]):
        for key, items in value.items():
            value[key] = sorted(items, key=lambda x: x.resize_to, reverse=True)

        self._sizes = value

    def sizes_for_mime(self, image_mime: str) -> Sequence[ImageSize]:
        if image_mime in self.sizes:
            yield from self.sizes[image_mime]
        elif '*' in self.sizes:
            yield from self.sizes['*']
        else:
            raise SizesNotConfiguredForMimeError(image_mime)

    def get_format(self, image: Image, image_format: Optional[str]) -> ImageFormat:
        if not image_format:
            image_format = image.format

        if not image_format:
            raise MissingImageFormatError()

        image_format = image_format.upper()

        for handled_format in self.formats:
            if handled_format.name == image_format:
                return handled_format

        raise FormatNotConfiguredWithNameError(image_format)

    def format_by_mime(self, image_mime: str) -> ImageFormat:
        for handled_format in self.formats:
            if handled_format.mime == image_mime:
                return handled_format
        raise FormatNotConfiguredForMimeError(image_mime)

    def new_id(self) -> str:
        return str(uuid.uuid4()).replace('-', '')

    def get_extension_by_mime(self, mime: str):
        for handled_format in self.formats:
            if handled_format.mime == mime:
                return handled_format.extension
        raise ValueError(f'Type `{mime}` is not handled by this instance of {self.__class__.__name__}')

    def auto_rotate(self, img: Image) -> Image:
        exif = img.getexif() if hasattr(img, 'getexif') else None

        if not exif:
            return img

        orientation_key = 274  # cf ExifTags
        if orientation_key in exif:
            orientation = exif[orientation_key]

            rotate_values = {
                3: 180,
                6: 270,
                8: 90
            }

            if orientation in rotate_values:
                return img.rotate(rotate_values[orientation], expand=True)
        return img

    def _verify_mode_and_rotation(self, image: Image):
        if image.format == 'GIF':
            return image

        if image.mode == 'CMK':
            image = image.convert('RGB')

        return self.auto_rotate(image)

    def resize_to_max_side(self,
                           image: Image,
                           desired_max_side: int) -> ImageWrapper:
        width, height = image.size

        max_side = max(width, height)

        if max_side <= desired_max_side:
            # return the same image
            return ImageWrapper(image)

        if width >= height:
            # h : 100 = w : x
            ratio = width / desired_max_side
            other_side = height / ratio
            sc = (desired_max_side, int(other_side))
        else:
            # w : 100 = h : x
            ratio = height / desired_max_side
            other_side = width / ratio
            sc = (int(other_side), desired_max_side)

        if getattr(image, 'n_frames', 1) == 1:
            # single frame image
            return ImageWrapper(image.resize(sc, Image.ANTIALIAS))

        return ImageWrapper.from_frames([frame.resize(sc, Image.BOX) for frame in ImageSequence.Iterator(image)])

    def process_image(self, source_image_path: str):
        if not isinstance(self.store, SyncFileStore):
            raise ExpectedSyncStoreError()

        data = self.store.read_file(source_image_path)

        if data is None:
            raise SourceImageNotFoundError()

        image = self.parse_image(data)
        image_format = self.get_format(image, self.format_by_extension(source_image_path) or 'JPEG')

        metadata = self._generate_images(image, image_format)

        return metadata

    def get_image_name(self,
                       version: ImageVersion,
                       image_format: ImageFormat):
        return f'{version.size_name[0]}-{version.id}{image_format.extension}'

    def format_by_extension(self, image_path):
        extension = get_file_extension(image_path).lower()

        if extension == '.jpg' or extension == '.jpeg':
            return 'JPEG'
        if extension == '.png':
            return 'PNG'
        if extension == '.gif':
            return 'GIF'
        return None

    async def process_image_async(self,
                                  source_image_path: str,
                                  loop: Optional[AbstractEventLoop] = None,
                                  executor=None):
        if not isinstance(self.store, FileStore):
            raise ExpectedAsyncStoreError()

        if loop is None:
            loop = asyncio.get_event_loop()

        data = await self.store.read_file(source_image_path)

        if data is None:
            raise SourceImageNotFoundError()

        image = self.parse_image(data)
        image_format = self.get_format(image, self.format_by_extension(source_image_path) or 'JPEG')

        metadata = await self._generate_images_async(image, image_format, loop, executor)

        return metadata

    async def _generate_images_async(self,
                                     image: Image,
                                     image_format: ImageFormat,
                                     loop: AbstractEventLoop,
                                     executor) -> ImageMetadata:
        metadata = self.get_metadata(image, image_format)

        for version in self.get_versions(image_format.mime):
            image_name = self.get_image_name(version, image_format)
            version.file_name = image_name
            metadata.versions.append(version)
            resized_image = await loop.run_in_executor(executor, self.resize_to_max_side, image, version.max_side)
            resized_image.format = image_format.name

            await self.store.write_file(image_name, image_format.to_bytes(resized_image))

        return metadata

    def _generate_images(self,
                         image: Image,
                         image_format: ImageFormat) -> ImageMetadata:
        metadata = self.get_metadata(image, image_format)

        for version in self.get_versions(image_format.mime):
            image_name = self.get_image_name(version, image_format)
            version.file_name = image_name
            metadata.versions.append(version)
            resized_image = self.resize_to_max_side(image, version.max_side)
            resized_image.format = image_format.name

            self.store.write_file(image_name, image_format.to_bytes(resized_image))

        return metadata

    def get_versions(self, image_mime: str) -> Generator[ImageVersion, None, None]:
        """
        Returns versions to be generated for a given image mime, new ids are assigned here.

        :param image_mime: mime type.
        :return: a sequence of ImageVersion
        """
        for size in self.sizes_for_mime(image_mime):
            yield ImageVersion(size.name, self.new_id(), size.resize_to)

    def parse_image(self, data: bytes) -> Image:
        image = Image.open(BytesIO(data))
        image = self._verify_mode_and_rotation(image)
        return image

    def get_metadata(self,
                     image: Image,
                     image_format: ImageFormat):
        width, height = image.size

        return ImageMetadata(width,
                             height,
                             image_format.extension,
                             image_format.mime,
                             [])

