from math import floor, fabs
from PIL import Image, ImageSequence


def transform_image(original_img, crop_w, crop_h):
    """
    Resizes and crops the image to the specified crop_w and crop_h if necessary.
    Works with multi frame gif and webp images also.

    args:
    original_img is the image instance created by pillow ( Image.open(filepath) )
    crop_w is the width in pixels for the image that will be resized and cropped
    crop_h is the height in pixels for the image that will be resized and cropped

    returns:
    Instance of an Image or list of frames which they are instances of an Image individually
    """
    img_w, img_h = (original_img.size[0], original_img.size[1])
    n_frames = getattr(original_img, 'n_frames', 1)

    def transform_frame(frame):
        """
        Resizes and crops the individual frame in the image.
        """
        # resize the image to the specified height if crop_w is null in the recipe
        if crop_w is None:
            if crop_h == img_h:
                return frame
            new_w = floor(img_w * crop_h / img_h)
            new_h = crop_h
            return frame.resize((new_w, new_h))

        # return the original image if crop size is equal to img size
        if crop_w == img_w and crop_h == img_h:
            return frame

        # first resize to get most visible area of the image and then crop
        w_diff = fabs(crop_w - img_w)
        h_diff = fabs(crop_h - img_h)
        enlarge_image = True if crop_w > img_w or crop_h > img_h else False
        shrink_image = True if crop_w < img_w or crop_h < img_h else False

        if enlarge_image is True:
            new_w = floor(crop_h * img_w / img_h) if h_diff > w_diff else crop_w
            new_h = floor(crop_w * img_h / img_w) if h_diff < w_diff else crop_h

        if shrink_image is True:
            new_w = crop_w if h_diff > w_diff else floor(crop_h * img_w / img_h)
            new_h = crop_h if h_diff < w_diff else floor(crop_w * img_h / img_w)

        left = (new_w - crop_w) // 2
        right = left + crop_w
        top = (new_h - crop_h) // 2
        bottom = top + crop_h

        return frame.resize((new_w, new_h)).crop((left, top, right, bottom))

    # single frame image
    if n_frames == 1:
        return transform_frame(original_img)
    # in the case of a multiframe image
    else:
        frames = []
        for frame in ImageSequence.Iterator(original_img):
            frames.append( transform_frame(frame) )
        return frames
