import asyncio

import aiohttp
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from imaginepy import Imagine
from imaginepy.constants import *


class ImageGenerator:
    def __init__(self, HG_IMG2TEXT):
        self.HG_IMG2TEXT = HG_IMG2TEXT
        self.STYLE_OPTIONS = {
            "No Style": "NO_STYLE",
            "Euphoric": "EUPHORIC",
            "Fantasy": "FANTASY",
            "Cyberpunk": "CYBERPUNK",
            "Studio Ghibli": "STUDIO_GHIBLI",
            "Disney": "DISNEY",
            "GTA": "GTA",
            "Kawaii Chibi": "KAWAII_CHIBI",
            "Anime V2": "ANIME_V2",
            "Abstract Vibrant": "ABSTRACT_VIBRANT",
            "Psychedelic": "PSYCHEDELIC",
            "Extra Terrestrial": "EXTRA_TERRESTRIAL",
            "Cosmic": "COSMIC",
            "Macro Photography": "MACRO_PHOTOGRAPHY",
            "Product Photography": "PRODUCT_PHOTOGRAPHY",
            "Polaroid": "POLAROID",
            "Neo Fauvism": "NEO_FAUVISM",
            "Pop Art": "POP_ART",
            "Pop Art II": "POP_ART_II",
            "Graffiti": "GRAFFITI",
            "Surrealism": "SURREALISM",
            "Bauhaus": "BAUHAUS",
            "Cubism": "CUBISM",
            "Japanese Art": "JAPANESE_ART",
            "Sketch": "SKETCH",
            "Illustration": "ILLUSTRATION",
            "Painting": "PAINTING",
            "Palette Knife": "PALETTE_KNIFE",
            "Ink": "INK",
            "Origami": "ORIGAMI",
            "Stained Glass": "STAINED_GLASS",
            "Sticker": "STICKER",
            "Clip Art": "CLIP_ART",
            "Poster Art": "POSTER_ART",
            "Papercut Style": "PAPERCUT_STYLE",
            "Coloring Book": "COLORING_BOOK",
            "Pattern": "PATTERN",
            "Render": "RENDER",
            "Cinematic Render": "CINEMATIC_RENDER",
            "Comic Book": "COMIC_BOOK",
            "Comic V2": "COMIC_V2",
            "Logo": "LOGO",
            "Icon": "ICON",
            "Glass Art": "GLASS_ART",
            "Knolling Case": "KNOLLING_CASE",
            "Scatter": "SCATTER",
            "Poly Art": "POLY_ART",
            "Claymation": "CLAYMATION",
            "Woolitize": "WOOLITIZE",
            "Marble": "MARBLE",
            "Van Gogh": "VAN_GOGH",
            "Salvador Dali": "SALVADOR_DALI",
            "Picasso": "PICASSO",
            "Architecture": "ARCHITECTURE",
            "Interior": "INTERIOR",
            "Abstract Cityscape": "ABSTRACT_CITYSCAPE",
            "Dystopian": "DYSTOPIAN",
            "Futuristic": "FUTURISTIC",
            "Neon": "NEON",
            "Chromatic": "CHROMATIC",
            "Mystical": "MYSTICAL",
            "Landscape": "LANDSCAPE",
            "Rainbow": "RAINBOW",
            "Candyland": "CANDYLAND",
            "Minecraft": "MINECRAFT",
            "Pixel Art": "PIXEL_ART",
            "Renaissance": "RENAISSANCE",
            "Rococo": "ROCOCO",
            "Medieval": "MEDIEVAL",
            "Retro": "RETRO",
            "Retrowave": "RETROWAVE",
            "Steampunk": "STEAMPUNK",
            "Amazonian": "AMAZONIAN",
            "Avatar": "AVATAR",
            "Gothic": "GOTHIC",
            "Haunted": "HAUNTED",
            "Waterbender": "WATERBENDER",
            "Aquatic": "AQUATIC",
            "Firebender": "FIREBENDER",
            "Forestpunk": "FORESTPUNK",
            "Vibrant Viking": "VIBRANT_VIKING",
            "Samurai": "SAMURAI",
            "Elven": "ELVEN",
            "Shamrock Fantasy": "SHAMROCK_FANTASY",
        }
        self.RATIO_OPTIONS = {
            "1:1": "RATIO_1X1",
            "4:3": "RATIO_4X3",
            "3:2": "RATIO_3X2",
            "2:3": "RATIO_2X3",
            "16:9": "RATIO_16X9",
            "9:16": "RATIO_9X16",
            "5:4": "RATIO_5X4",
            "4:5": "RATIO_4X5",
            "3:1": "RATIO_3X1",
            "3:4": "RATIO_3X4",
        }

    async def generate_imagecaption(self, url, HG_TOKEN):
        headers = {"Authorization": f"Bearer {HG_TOKEN}"}
        retries = 0
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp1:
                if resp1.status != 200:
                    return f"Error: failed to download image ({resp1.status})"
                async with session.post(
                    self.HG_IMG2TEXT, headers=headers, data=await resp1.read()
                ) as resp2:
                    if resp2.status == 200:
                        response = await resp2.json()
                        return (
                            "This image looks like a " + response[0]["generated_text"]
                        )
                    elif (
                        resp2.status >= 500 or "loading" in (await resp2.text()).lower()
                    ):
                        retries += 1
                        if retries <= 3:
                            await asyncio.sleep(3)
                            return await self.generate_imagecaption(url, HG_TOKEN)
                        else:
                            return f"Server error: {await resp2.text()}"
                    else:
                        return f"Error: {await resp2.text()}"

    async def generate_image(self, image_prompt, style_value, ratio_value, negative):
        file_path = "downloaded_files/image.png"
        try:
            imagine = Imagine()
            img_data = imagine.sdprem(
                prompt=image_prompt,
                style=Style[style_value],
                ratio=Ratio[ratio_value],
                negative="",
                cfg=16,
                model=Model.REALISTIC,
                asbase64=False,  # default is false, putting it here as presentation.
            )
        except Exception as e:
            print(f"The server does not respond {e}")
            return None

        if img_data is None:
            print("An error occurred while generating the image.")
            return

        # img_data = imagine.upscale(img_data) too big for a photo

        if img_data is None:
            print("An error occurred while upscaling the image.")
            return

        try:
            with open(file_path, mode="wb") as img_file:
                img_file.write(img_data)
                img_file.close()
        except Exception as e:
            print(f"An error occurred while writing the image to file: {e}")
        return file_path

    async def generate_keyboard(self, key):
        markup = ReplyKeyboardMarkup(row_width=5)
        if key == "ratio":
            markup.add(*[KeyboardButton(x) for x in self.RATIO_OPTIONS.keys()])
        elif key == "style":
            markup.add(*[KeyboardButton(x) for x in self.STYLE_OPTIONS.keys()])
        return markup
