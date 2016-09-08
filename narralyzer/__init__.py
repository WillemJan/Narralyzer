import config
import utils

__all__ = ['stanford_probablepeople_wrapper',
           'Language',
           'utils'
           'config']

config = config.Config()

try:
    from stanford_probablepeople_wrapper import sppw
    from lang_lib import Language
except:
    log = utils.logger(__file__)
    log.warn("Did not import sppw and Language")


if __name__ == '__main__':
    print("=sppw=")
    print(dir(sppw))
    print("=Language=")
    print(dir(Language))
