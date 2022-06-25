from typing import List, Any, Coroutine
from pathlib import Path

import aiohttp
import json
import base64

import asyncio

from . import AsyncClass


# ** Exceptions **

class DallESiteUnavailable(Exception):
    """
    Raised when the DallE API is unavailable.
    """
    pass


# DallE Parsing failed
class DallEParsingFailed(Exception):
    """
    Raised when the DallE API returns an error.
    """
    pass


class DallENotJson(Exception):
    """
    Raised when the DallE API returns an error.
    """
    pass


class DallENoImagesReturned(Exception):
    """
    Raised when the DallE API returns no images.
    """
    pass


# ** Exceptions End **


class GeneratedImage:
    def __init__(self, image_name: str, image_path: str):
        self.image_name = image_name
        self.path = image_path


class DallE(AsyncClass.AsyncClass):
    def __init__(self, prompt: str, author: str):
        self.prompt = prompt
        self.author = author

    async def generate(self) -> list[GeneratedImage]:
        """
        Makes an api request to dall-e endpoint and returns the images
        :return: list
        """
        url = "https://bf.dallemini.ai/generate"

        payload = json.dumps({
            "prompt": f"{self.prompt}"
        })
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://hf.space',
            'Referer': 'https://hf.space/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/15.5 Safari/605.1.15 '
        }

        # Make a request with asyncio
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    if response.headers['Content-Type'] == 'application/json':
                        response_json = await response.json()
                        images = response_json['images']
                        generated_images = []

                        if len(images) == 0:
                            raise DallENoImagesReturned()

                        v = 0
                        for image in images:
                            v += 1
                            converted = self.base_64_to_image(image, v)
                            generated_images.append(converted)

                        return generated_images
                    else:
                        raise DallENotJson()
                else:
                    raise DallESiteUnavailable()

    def base_64_to_image(self, base_64_string: str, number: int) -> GeneratedImage:
        """
        Converts a base64 string to an image
        :param number:
        :param base_64_string:
        :return: GeneratedImage
        """
        path = f"generated_{self.author}_{number}"

        Path(f"./generated/{self.author}").mkdir(parents=True,
                                                 exist_ok=True)  # Create the directory if it doesn't exist

        with open(f"./generated/{self.author}/{path}.jpg", "wb") as fh:
            fh.write(base64.urlsafe_b64decode(base_64_string))

        return GeneratedImage(path + ".jpg", f"./generated/{self.author}/{path}.jpg")


async def test():
    dall_e = await DallE(prompt="DallE", author="DallE")
    generated = await dall_e.generate()
    for image in generated:
        print(image.image_name)
        print(image.path)


if __name__ == '__main__':
    asyncio.run(test())
