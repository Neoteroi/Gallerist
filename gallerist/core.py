import uuid
from io import BytesIO
from dataclasses import dataclass
from typing import BinaryIO, Sequence, Optional, Dict, List
from gallerist.abc import ImageStore
from PIL import Image, ImageSequence


def exception_str(ex):
    return str(ex) or ex.__class__.__name__


@dataclass
class ImageFormat:
    mime: str
    name: str
    extension: str
    quality: int

    def to_bytes(self, image: Image) -> BytesIO:
        byte_io = BytesIO()
        if self.quality > 0:
            image.save(byte_io, image.format, quality=self.quality)
        else:
            image.save(byte_io, image.format)
        return byte_io


class GifFormat(ImageFormat):

    def __init__(self):
        super().__init__('image/gif', 'GIF', '.gif', -1)

    def to_bytes(self, all_frames: Image) -> BytesIO:
        # if not image.is_animated:
        #     return super().to_bytes(image)
        byte_io = BytesIO()

        # all_frames = [frame for frame in ImageSequence.Iterator(image)]
        image = all_frames[0]
        all_frames[0].save(byte_io,
                           format=self.name,
                           optimize=True,
                           save_all=True,
                           append_images=all_frames[1:],
                           duration=image.info.get('duration', 100),
                           loop=0)
        """
        image.save(byte_io,
                   self.name,
                   save_all=True,
                   append_images=image[1:],
                   duration=duration,
                   loop=0)
        """
        return byte_io

    def get_mode(self, image: Image):
        """
        Pre-process pass over the image to determine the mode (full or additive).
        Necessary as assessing single frames isn't reliable. Need to know the mode
        before processing all frames.
        """
        try:
            while True:
                if image.tile:
                    tile = image.tile[0]
                    update_region = tile[1]
                    update_region_dimensions = update_region[2:]
                    if update_region_dimensions != image.size:
                        return 'partial'
                image.seek(image.tell() + 1)
        except EOFError:
            pass
        return 'full'

    def extract_frames(self, image: Image, resize_to: int = -1):
        """
        Iterate the GIF, extracting each frame and resizing them

        Returns:
            An array of all frames
        """
        mode = self.get_mode(image)

        palette = image.getpalette()
        last_frame = image.convert('RGBA')

        all_frames = []

        try:
            while True:
                """
                If the GIF uses local colour tables, each frame will have its own palette.
                If not, we need to apply the global palette to the new frame.
                """
                if not image.getpalette():
                    image.putpalette(palette)

                new_frame = Image.new('RGBA', image.size)

                """
                Is this file a "partial"-mode GIF where frames update a region of a different size to the entire image?
                If so, we need to construct the new frame by pasting it on top of the preceding frames.
                """
                if mode == 'partial':
                    new_frame.paste(last_frame)

                new_frame.paste(image, (0, 0), image.convert('RGBA'))

                if resize_to > 0:
                    new_frame.thumbnail(resize_to, Image.ANTIALIAS)
                all_frames.append(new_frame)

                last_frame = new_frame
                image.seek(image.tell() + 1)
        except EOFError:
            pass

        return all_frames


@dataclass
class ImageSize:
    __slots__ = ('name', 'resize_to')

    name: str
    resize_to: int


ImageSizesType = Dict[str, Sequence[ImageSize]]


@dataclass
class ImageVersion:
    name: str
    id: str
    max_side: int


@dataclass
class ImageMetadata:
    width: int
    height: int
    ratio: float
    extension: str
    mime: str
    versions: List[ImageVersion]


class PictureForWebOutput:

    def __init__(self,
                 medium_file_id: str,
                 medium_file_name: str,
                 thumbnail_file_id: str,
                 thumbnail_file_name: str,
                 width: int,
                 height: int,
                 ratio: float,
                 extension: str,
                 mime: str):
        self.medium_file_id = medium_file_id
        self.medium_file_name = medium_file_name
        self.thumbnail_file_id = thumbnail_file_id
        self.thumbnail_file_name = thumbnail_file_name
        self.width = width
        self.height = height
        self.ratio = ratio
        self.extension = extension
        self.mime = mime


class GalleristError(Exception):
    """Base class for exceptions risen by Gallerist class"""


class SizesNotConfiguredForMimeError(GalleristError):

    def __init__(self, image_mime: str):
        super().__init__(f'Image sizes are not configured for mime `{image_mime}`; '
                         f'to correct, use the `sizes` option of the Gallerist constructor; '
                         f'or override `default_sizes` in a base class')


class FormatNotConfiguredForMimeError(GalleristError):

    def __init__(self, image_mime: str):
        super().__init__(f'Image formats are not configured for mime `{image_mime}`; '
                         f'to correct, use the `formats` option of the Gallerist constructor; '
                         f'or override `default_formats` in a base class')


class ImageResizingException(GalleristError):

    def __init__(self,
                 inner_exception,
                 image_name,
                 available_data: PictureForWebOutput):
        super().__init__(f'An exception happened while resizing the image: {image_name}; error: '
                         + exception_str(inner_exception))
        self.data = available_data


class Gallerist:
    """Provides methods to prepare images in various sizes and store them with metadata."""

    def __init__(self,
                 store: ImageStore,
                 sizes: Optional[ImageSizesType] = None,
                 formats: Optional[Sequence[ImageFormat]] = None,
                 remove_exif: bool = False):
        self._sizes = None
        self.store = store
        self.remove_exif = remove_exif
        self.formats = formats or self.default_formats
        self.sizes = sizes or self.default_sizes

    default_sizes = {
        '*': (ImageSize('medium', 1200),
              ImageSize('thumbnail', 200)),
        'image/gif': (ImageSize('medium', 200),
                      ImageSize('thumbnail', 200))
    }

    default_formats = [
        ImageFormat('image/jpeg', 'JPEG', '.jpg', 80),
        ImageFormat('image/pjpeg', 'JPEG', '.jpg', 80),
        ImageFormat('image/png', 'PNG', '.png', -1),
        GifFormat(),
        ImageFormat('image/mpo', 'JPEG', '.jpg', 80)
    ]

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

    def strip_exif(self, image: Image) -> Image:
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(list(image.getdata()))
        image_without_exif.format = image.format
        return image_without_exif

    def _verify_mode_and_rotation(self, image: Image):
        if image.format == 'GIF':
            return image

        if image.mode != 'RGB':
            image = image.convert('RGB')

        return self.auto_rotate(image)

    def resize_to_max_side(self,
                           image: Image,
                           desired_max_side: int) -> Image:
        width, height = image.size

        max_side = max(width, height)

        if max_side <= desired_max_side:
            # return the same image
            return image

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
            return image.resize(sc, Image.ANTIALIAS)

        all_frames = [frame.resize(sc, Image.BOX) for frame in ImageSequence.Iterator(image)]

        byte_io = BytesIO()

        all_frames[0].save(byte_io,
                           format='GIF',
                           optimize=True,
                           save_all=True,
                           append_images=all_frames[1:],
                           loop=0)

        # return image.resize(sc, Image.ANTIALIAS)
        byte_io.seek(0)
        return Image.open(byte_io)

    def image_to_bytes(self, image: Image) -> BytesIO:
        image_format = self.format_by_mime(Image.MIME[image.format])
        byte_io = image_format.to_bytes(image)
        byte_io.seek(0)
        return byte_io

    async def upload_image(self, stream: BinaryIO):

        for image in self.prepare_images(stream):
            # upload image;
            await self.store.store_image()

    def prepare_images(self, stream: BinaryIO):
        """
        Prepares an image in various sizes, depending on configured sizes by mime type.

        :param stream: binary stream representing an image.
        """
        image = Image.open(stream)
        image = self._verify_mode_and_rotation(image)

        image_format = image.format
        image_mime = Image.MIME[image_format]

        if self.remove_exif:
            image = self.strip_exif(image)

        width, height = image.size
        versions = [ImageVersion('original', self.new_id(), max(width, height))]

        yield self.image_to_bytes(image)

        for size in self.sizes_for_mime(image_mime):
            resized_image = self.resize_to_max_side(image, size.resize_to)
            resized_image.format = image_format
            yield self.image_to_bytes(resized_image)

    def get_image_metadata(self):
        width, height = image.size
        options = self.format_by_mime(image_mime)
        # if storing image bytes, why not metadata as well?
        return ImageMetadata(width,
                             height,
                             width / height,
                             options.extension,
                             image_mime,
                             versions=[])
