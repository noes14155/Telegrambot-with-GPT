import json

from plugins.gtts_text_to_speech import GTTSTextToSpeech
from plugins.dice import DicePlugin
from plugins.youtube_audio_extractor import YouTubeAudioExtractorPlugin
from plugins.ddg_image_search import DDGImageSearchPlugin
from plugins.ddg_translate import DDGTranslatePlugin
from plugins.crypto import CryptoPlugin
from plugins.weather import WeatherPlugin
from plugins.ddg_web_search import DDGWebSearchPlugin
from plugins.wolfram_alpha import WolframAlphaPlugin
from plugins.worldtimeapi import WorldTimeApiPlugin
from plugins.whois_ import WhoisPlugin
from plugins.webshot import WebshotPlugin


class PluginManager:
    """
    A class to manage the plugins and call the correct functions
    """

    def __init__(self, plugins):
        """
        Initializes the PluginManager with a list of enabled plugins

        :param plugins: A dictionary containing the list of enabled plugins
        """
        enabled_plugins = plugins.get('plugins', [])
        plugin_mapping = {
            'wolfram': WolframAlphaPlugin,
            'weather': WeatherPlugin,
            'crypto': CryptoPlugin,
            'ddg_web_search': DDGWebSearchPlugin,
            'ddg_translate': DDGTranslatePlugin,
            'ddg_image_search': DDGImageSearchPlugin,
            'worldtimeapi': WorldTimeApiPlugin,
            'youtube_audio_extractor': YouTubeAudioExtractorPlugin,
            'dice': DicePlugin,
            'gtts_text_to_speech': GTTSTextToSpeech,
            'whois': WhoisPlugin,
            'webshot': WebshotPlugin,
        }
        self.plugins = [plugin_mapping[plugin]() for plugin in enabled_plugins if plugin in plugin_mapping]

    def get_functions_specs(self):
        """
        Returns the list of function specs that can be called by the model

        :return: A list of function specs
        """
        return [spec for plugin in self.plugins for spec in plugin.get_spec()]

    async def call_function(self, function_name, arguments):
        """
        Calls a function based on the name and parameters provided

        :param function_name: The name of the function to call
        :param arguments: The arguments to pass to the function
        :return: The result of the function call
        """
        if plugin := self.__get_plugin_by_function_name(function_name):
            return json.dumps(await plugin.execute(function_name, **json.loads(arguments)), default=str)
        else:
            return json.dumps({'error': f'Function {function_name} not found'})

    def get_plugin_source_name(self, function_name) -> str:
        """
        Returns the source name of the plugin

        :param function_name: The name of the function
        :return: The source name of the plugin
        """
        plugin = self.__get_plugin_by_function_name(function_name)
        return '' if not plugin else plugin.get_source_name()

    def __get_plugin_by_function_name(self, function_name):
        """
        Returns the plugin that contains the specified function name

        :param function_name: The name of the function
        :return: The plugin that contains the function, or None if not found
        """
        return next((plugin for plugin in self.plugins if function_name in map(lambda spec: spec.get('name'), plugin.get_spec())), None)
