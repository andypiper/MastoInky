#!/usr/bin/env python3

# MastoInky
# Display image posts from a Mastodon personal, hashtag or public timeline on a Raspberry Pi with the Pimoroni Inky Impression
# based on code by AxWax (@axwax@fosstodon.org)

# Enter your API credentials in credentials_example.py and rename to credentials.py

# Robot_Font by Fortress Tech at https://www.dafont.com/robot-2.font

import random
import signal
import time
from urllib.request import urlopen
from urllib.error import URLError

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageEnhance
from mastodon import Mastodon
import RPi.GPIO as GPIO
import inky.inky_uc8159 as inky
from inky.auto import auto

from credentials import access_token, api_base_url, account_id

# NB this works with Bullseye but has not been tested under Bookworm

# set up the GPIO pins for the buttons (from top to bottom)
BUTTONS = [5, 6, 16, 24]

# These correspond to buttons A, B, C and D respectively
LABELS = ["A", "B", "C", "D"]

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# configuration
# how many posts should be loaded
max_posts = 20

# image to be placed in front of other layers - should be placed in img folder
# todo: to use the robot image, then the size and positions of text and thumb need to be adjusted
# foreground_img = 'projector.png'
foreground_img = "mascot-projector.png"

# size and position of the (cropped square) thumbnail
thumb_width = 200
thumb_x = 290
thumb_y = 125

# size, position and font of the text in the speech bubble
# note that the text x/y need to be adjusted based on the text box
# being centred on the x axis and anchored to the middle of the text.
text_x = 355
text_y = 75
text_w = 320
text_h = 100

# todo: associate the font used to the foreground image
# font_name = 'Robot_Font.otf'
font_name = "manrope-variable.otf"

post_id = 0
img_id = 0

try:
    # init Mastodon API
    mastodon = Mastodon(access_token=access_token, api_base_url=api_base_url)
except Exception as e:
    print(f"Failed to initialize Mastodon API: {e}")
    exit(1)

# Set up the Inky Display
# display = auto()
# print("Colours: {}".format(display.colour))
# print("Resolution: {}".format(display.resolution))

# this is for the Inky Impression 5.7" display
display = inky.Inky((600, 448))


# Functions
# wrap text even for variable-width fonts
# by Chris Collett at https://stackoverflow.com/a/67203353
def get_wrapped_text(text: str, font: ImageFont.ImageFont, line_length: int):
    lines = [""]
    for word in text.split():
        line = f"{lines[-1]} {word}".strip()
        if font.getlength(line) <= line_length:
            lines[-1] = line
        else:
            lines.append(word)
    return "\n".join(lines)


# find the maximum font size for text to be rendered within the specified rectangle
def find_font_size(the_text, the_font, the_canvas, textbox_width, textbox_height):
    for size in range(
        20, 1, -1
    ):  # we start with font size 20 and make it smaller until it fits
        fo = the_font.font_variant(size=size)
        wrapped_text = get_wrapped_text(the_text, fo, textbox_width)
        left, top, right, bottom = the_canvas.multiline_textbbox(
            (0, 0), wrapped_text, align="center", font=fo
        )
        text_height = bottom - top
        if text_height < textbox_height:
            break
    return [size, wrapped_text]


# These Pillow image cropping helper functions are from
# https://note.nkmk.me/python-pillow-square-circle-thumbnail/
def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(
        (
            (img_width - crop_width) // 2,
            (img_height - crop_height) // 2,
            (img_width + crop_width) // 2,
            (img_height + crop_height) // 2,
        )
    )


# crop a square as big as possible
def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


# helper for gradient background by weihanglo https://gist.github.com/weihanglo/1e754ec47fdd683a42fdf6a272904535
def interpolate(f_co, t_co, interval):
    det_co = [(t - f) / interval for f, t in zip(f_co, t_co)]
    for i in range(interval):
        yield [round(f + det * i) for f, det in zip(f_co, det_co)]


# load the post's image, create a composite image and display it
def show_image(img, caption="", media_id=""):
    # load the image, crop it into a square and create a thumb_width * thumb_width pixel thumbnail
    # (this should probably be less square and more landscape)
    image = Image.open(img)
    enhancer = ImageEnhance.Color(image)
    mod_image = enhancer.enhance(1.3)
    im_thumb = crop_max_square(mod_image).resize(
        (thumb_width, thumb_width), Image.LANCZOS
    )

    # load the background as the bottom layer
    newImage = Image.new("RGB", (600, 448))
    rectangle = ImageDraw.Draw(newImage)

    # create a gradient based on two random colours
    f_co = ImageColor.getrgb("hsl(" + str(random.randint(0, 360)) + ", 100%, 50%)")
    t_co = ImageColor.getrgb("hsl(" + str(random.randint(0, 360)) + ", 100%, 50%)")
    for i, color in enumerate(interpolate(f_co, t_co, 600 * 2)):
        rectangle.line([(i, 0), (0, i)], tuple(color), width=1)

    # now add the thumbnail as the next layer
    newImage.paste(im_thumb, (thumb_x, thumb_y))

    # load the projector / avatar / speech bubble layer
    foreground = Image.open("img/" + foreground_img)
    newImage.paste(foreground, (0, 0), foreground)

    # draw the assembled image
    draw = ImageDraw.Draw(newImage)

    # load the font and find the largest possible font size for the caption to stay within the speech bubble
    font = ImageFont.FreeTypeFont(font_name)
    font_size, wrapped_text = find_font_size(caption, font, draw, text_w, text_h)
    font = ImageFont.FreeTypeFont(font_name, font_size)

    # render the text inside the speech bubble
    draw.multiline_text(
        (text_x, text_y),
        wrapped_text,
        font=font,
        fill=(0, 0, 0),
        align="center",
        anchor="mm",
    )

    # send the image to the E Ink display
    display.set_image(newImage)
    display.show()


# grab the Mastodon post's image URL, ALT image description and author name then pass them to the show_image() function
def show_post_image(post_id=0, media_id=0):
    media_url = latest_media_post[post_id].media_attachments[media_id].preview_url
    media_author = latest_media_post[post_id].account.display_name  # or username
    caption = latest_media_post[post_id].media_attachments[media_id].description

    # someone forgot to add their ALT text - let's give them a gentle nudge.
    if not caption:
        caption = "There could be a beautiful image description here. Maybe next time?"

    media_desc = caption + " - wrote " + str(media_author)

    # Let's try to load the image - use 404slide as a fallback when an error occurs
    for _ in range(3):  # Retry up to 3 times
        try:
            the_image = urlopen(media_url)
            show_image(the_image, media_desc, media_id)
            break  # If successful, break out of the loop
        except URLError as e:
            print(f"Failed to load image from {media_url}: {e}")
            time.sleep(1)  # Wait for a second before retrying
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            the_image = "img/404slide.png"
            show_image(the_image, media_desc, media_id)
            break  # If an unexpected error occurs, break out of the loop


# handler for button presses
def handle_button(pin):
    global post_id, img_id, max_post_id
    label = LABELS[BUTTONS.index(pin)]

    # buttons A and B increase / decrease post id
    # buttons C and D increase / decrease media_id within that post
    # todo: make C and D clear the screen, and restart the process
    if str(label) == "A":
        post_id += 1
        img_id = 0
        print("A")
    elif str(label) == "B":
        post_id -= 1
        img_id = 0
        print("B")
    elif str(label) == "C":
        img_id += 1
        print("C")
    elif str(label) == "D":
        if img_id > 0:
            img_id -= 1
        print("D")

        return

    # is the img_id within limits?
    if img_id < 0:
        post_id -= 1
        if post_id < 0:
            post_id = 0
        img_id = len(latest_media_post[post_id].media_attachments) - 1
    elif img_id >= len(latest_media_post[post_id].media_attachments):
        img_id = 0
        post_id += 1

    # is the post_id within limits?
    if post_id < 0:
        post_id = max_posts - 1
    if post_id >= max_posts:
        post_id = 0

    show_post_image(post_id, img_id)


if __name__ == "__main__":
    try:
        # load posts with media attachments from a timeline

        # uncomment the relevant line
        # latest_media_post = mastodon.account_statuses(id = account_id, limit = max_posts, only_media = True) # get images from a personal timeline (change account_id in credentials.py)
        # latest_media_post = mastodon.timeline_public(only_media=True, limit=max_posts) # get images from the public timeline / federated feed
        latest_media_post = mastodon.timeline_hashtag(
            "CatsOfMastodon", limit=max_posts, only_media=True
        )  # all posts from a certain hashtag

        show_post_image(1, 0)

        # add all the button handlers
        for pin in BUTTONS:
            GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=250)

        # wait for button presses
        signal.pause()

    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nSee ya!")
