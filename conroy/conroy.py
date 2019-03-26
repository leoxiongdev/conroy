import inspect
import logging

from .decorator import Hook, Resource


class Conroy:
    logger = logging.getLogger('Conroy')

    def __init__(self):
        self._hooks = []
        self._plugins = []
        self.resource = {}
        self.call = {}
        self.hooks = {}

    def __del__(self):
        """
        Unload plugins.
        :return:
        """
        for plugin in reversed(self._plugins):
            self.logger.debug('Unloading plugin {}.'.format(type(plugin).__name__))
            plugin.unload()
            self.logger.debug('{} plugin unloaded.'.format(type(plugin).__name__))

    def register_plugin(self, *plugins):
        """
        Register an instance of a ConroyPlugin.

        :param ConroyPlugin plugin: Instance of plugin.
        :return:
        """
        for plugin in plugins:
            plugin_name = type(plugin).__name__
            self.logger.info('Loading plugin {}.'.format(plugin_name))
            plugin.load()

            for attr_name in dir(plugin):
                attr = getattr(plugin, attr_name)

                if isinstance(attr, Hook):
                    self.logger.debug('Found hook {}.'.format(attr.name))
                    self._hooks.append((plugin, attr))

                    def closure(f):
                        def wrap(*args, **kwargs):
                            return f(plugin, *args, **kwargs)

                        return wrap

                    self.hooks['{}.{}'.format(plugin_name, attr.name)] = closure(attr.func)
                elif isinstance(attr, Resource):
                    self.logger.debug('Found resource {}.'.format(attr.name))
                    self.resource['{}.{}'.format(plugin_name, attr.name)] = attr.func(plugin)

            plugin.hooks = self.hooks
            plugin.resource = self.resource
            self.logger.info('{} plugin loaded.'.format(plugin_name))
            self._plugins.append(plugin)

    def recv_msg(self, message):
        self.logger.debug('Received message: {}'.format(message))
        for instance, hook in self._hooks:
            m = hook.regex.match(message)
            if m:
                self.logger.info('Calling hook {}.'.format(hook.name))
                signature = inspect.signature(hook.callback).parameters.keys()
                reply = hook.callback(instance, **{k: v for k, v in m.groupdict().items() if k in signature})
                print(reply)