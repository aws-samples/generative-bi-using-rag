class _Const(object):
    class ConstError(TypeError):
        def __init__(self, msg):
            super().__init__(msg)

    def __setattr__(self, name, value):
        if name in self.__dict__:
            err = self.ConstError("Can't change const.%s" % name)
            raise err
        if not name.isupper():
            err = self.ConstError('Const name "%s" is not all uppercase' % name)
            raise err
        self.__dict__[name] = value


const = _Const()

const.MODE = 'mode'
const.MODE_DEV = 'dev'
const.BEDROCK_MODEL_IDS = ['anthropic.claude-3-sonnet-20240229-v1:0',
                           'anthropic.claude-3-haiku-20240307-v1:0',
                           'anthropic.claude-v2:1',
                           ]