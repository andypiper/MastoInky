# MastoInky

Fork of @axwax's MastoInky, with some changes to make it work with my hardware (Inky Impression 5.7" rather than Inky Developer 7-colour) and my use case.

(`clean.py` comes from Pimoroni examples)

TODO: add more details here 🙂
TODO: maybe (?) add a config file to make it easier to change settings without editing the code (basically a theme system to pair font, image template, insert sizes)
TODO: printable frame
TODO: button handling

---


Original README follows:

Display image posts from a Mastodon personal, hashtag or public timeline on a Raspberry Pi with the Pimoroni Inky Developer E Ink

## Prerequisites
You will need a Raspberry Pi (I used a Zero W) and the [Pimoroni Inky Developer 7-colour Eink display](https://shop.pimoroni.com/products/inky-dev).

## Installation
1. Follow the installation instructions for the Python library at https://github.com/pimoroni/inkydev-python
```
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
pip3 install inkydev
pip3 install inky[rpi,fonts]
```
2. Install Python libraries
```
pip3 install Mastodon.py
pip3 install pillow
```
3. Download MastoInky to your Pi
```
wget https://github.com/axwax/MastoInky/archive/refs/heads/main.zip
unzip main.zip
cd  MastoInky-main
```
4. Get a Mastodon access token at https://{your mastodon instance}/settings/applications

5. Enter your API credentials in `credentials_example.py` and rename to `credentials.py`

6. If you want to follow an account's timeline, you first have to find the account id
```
python3 search_for_account_id.py
```
and add it to `credentials.py`.

7. At the bottom of `mastoinky.py` uncomment the relevant line for the timeline to use (account, public or hashtag).

8. run
```
python3 mastoinky.py
```
