from collections import namedtuple

import os
from mock import Mock

from tests.base import BaseTestCase


class GeneralTestCase(BaseTestCase):
    def test_environment(self):
        assert os.getenv('SHOUTIT_ENV', '').lower() == 'testing', "SHOUTIT_ENV should be set to 'testing'"

    def test_tesseract(self):
        import base64
        import pytesseract as pytesseract
        from PIL import Image
        from io import BytesIO

        data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAIEAAAARCAYAAAD6xs8TAAAJYElEQVR4nO2YaXSU5RXHf+/MZLJOdjKTIXtigB'
                                'CSkA0wICHloFQQEZAjIhYBbT2tIicNtVoFtK3FFmsPPVpbKUplsSqKIFA8yr4lBEhMopB9nyQTklkSZn37ITKQ'
                                'vJMw8Dn/T/Pe53//z33fe+c+C4xiFKMYxShGMYpRjGIUgHBH7NDY2cRO+y2BmhwAjB2XqD/zOt11h12cmNxCkv'
                                'LfHFbjWuNRLu6eBYB/WAqZy45haD3H5U/nARCdvZZ7Ct5y62s16zj5d82g+DUpy4hMW0VARDoyuTfmrgoai/9C'
                                'x/cfD/L18g0ndsp6wpMewicwBrvVgKmzjKbiLehrD96V5lCMv/89tOlrMLSdo2TH1LviCTIFsblFRE5aiXdgNB'
                                'ZDE23l/6bh/GZEp12ipZ7wGNFZzxEQkYHTcZ2e5pPUndqIsb0E8CgfCkkAswptfLNZWhwR45aQumAP+tqDVB54'
                                'AofVRGjCXNIXH6By/3J0VbsBaK/YwbXGoxJ/36B4Uhd8TE/jtwPPIUlMXvo1Xr7hboO7uHsWdqtpkE102gY9p8'
                                'zbQcS4xTSXbqXh7B8RRQdjkhaQ+tAe6sImUHdqIwBKfw05T17A1tdJ4/k3MeurUPqNQZvxDOmLv6Lq4Crayrfd'
                                'keZQhMTko01fja2/y+24p7zUh/YQGjeHutObMLYXo1JnEp+3gcDIXMr2LgREAARBTsr8j4hIfoTm0q3UnnwFQa'
                                'YgYvxSJs7fybn3UxCddo/z4YIgU1BQJLoJTSDvF01kPnaUod0j7t7fMXOtES+/MSO+fPJP3iZ/XT9evuH4BMZw'
                                '788byFh6hClPlZO+aL+LF529loIiEYV38Ih6AFFZzxGolf7jJsx9n/x1/cgUvi6bOmUZgmxI0QsycleWkbOi+K'
                                '40b0Cm8GHqmitM+Ol2MpYcIvuJs27jvR1vzD0LKSgSCUuYO8geGjeHgiKRiHGLXbaxGc8w69d2gqNmSOZRKAPd'
                                'zn8rbsmH7LZkAGWABm9VFF3V+7hRiTfQVPJXZF6+qMc/Oqy/wjuYyElP0V6xA1t/F/5hKfT31FL+2cM47RaPYn'
                                'CH5gt/w9Aq/eCG9gvIFD54+99cOnSVOyXtVBSd2Po6cNjMd6V5A/H3vopCqeLqNy+MGO/teNr0NRh1pUOWJ+iu'
                                '/x+GtvNEpq1y2TSpT6KvOUBP8wmJjt1qGDGOIflQAAKCTA4MtBhg0D9GdDpwWAyIogPfkHskgnIvf5y2PlTqzG'
                                'EnHZvxNHKlP00lA2u9vu4Q+rpDIwYalvAA0VnP4z8mDdFpQ19zgKtHC7Ga2kb0A1BFpOO0X8dibpeMCYIcBBne'
                                'AVq06asJ1E6l7Mf9yN1oBkSkE5NbyHf7lmK/fm1Yf094QVF5tH/3gdux3pbTaNNWMdCJRVTqTOpPbUKlySLxvj'
                                '8QHDUD0emgu+Frao4W0Xft6rCxDMmHgrhpL5Ew47VBpFmFN9femuMv0nD2DXSVu9CmP01/Ty3tFR8iOmyExBYQ'
                                'n/cqDpt52LVdkCmIyvwV+rrDmPVVwwYmCXTyszQWb8FibEalySZ++gaytFMp3j55xEr3D5uAZuIKdFW7cNr7Je'
                                'OpC/YwJnkRAH3dP1C68z6MutIRYxlOUxDkTHjgX3Re3Uvnlc+G9feEJ1eqUCgDsZqkhQtgNbcPcLyDEEU7Mrk3'
                                'Kk0mkemraSreQt2pjfiFjiNh+iaylp/m/PbJWIzN0lik+VDQWvZPumr2/0iQk7OihPPbJ9+c3NQKwPeHn8bapy'
                                'Nh+iaS8jcDYGg7T+VXKxk/511E0ek2ePX4pXiroqg6+NSwH+lWtJVt43pvA13VX7g0e1vPYOq4ROay42jTV9NY'
                                'vMWtr9JfTdqiL7Fd11N9bL1bTvWx31B/5vco/TWoUx4n49HDXPrvXNdu+k40o3NewCconsufPDjiO3nKA0C43Y'
                                'lNdHXsQO1USj6cgsXUAgx0C0PrOXJXXiY66zmqjxZJvN3kQ4HVrMNq1g3M/+MyYOq4JHF22vup/raQmqPr8QmK'
                                'xWHvd7VmZUAkxo6LbkOOzlmHqbOc7vojt3m5AditBjqv7pXYe5pPYDG1oNJku/XzCYwlY+kRFN5BlO6aha2v0y'
                                '2v/1q167e+9iBpCz9n/Jx3KP4w5440fYMTiM/bSM2xIpwOq2sjK8gUCIIchXcwTns/3qqxHvEcViN2Sy9KN3sO'
                                'GDjh2K0G7BYDgiDgdFjQVe5yFcANmPWVmPWVBIxJc6vjJh8Kt8SRIIoO+ntqXc9+ocl4B2gxtl+QcENi8lGpMz'
                                '3uAreDICjcnpX9wyeSseQQCAKlO2di1ld6rGnQXSA+8UFurLWeaoYlzEXu5Ufy7K0kz94q0b3v+WvUHH8Rh9Xo'
                                'Ea/h7Bv0Np8kaGye2ziDo6bT23QCEBFFEVNHmdtTDIBM4YvD3iexD5OPOyuCwMgpGNrOuZ4FmYKk/D/jsJnp+O'
                                'ETCT86ex1Wsw5d5U6P5wiNm4NKPZmGc3+S2JX+anqajg2yhyfOI2X+R/Rfq6Hs0/mSfwYMXBTF571K9beFOB2D'
                                'TyMh0TOxmNu4tQA80ey88jnmrgqJPXHmZuTKAK4ceZb+nlpEp8MjHkDL5fdIe+QLwhIfRF9z4Oa7x9+PSpNN+d'
                                '6FLltb+TbGzXmHoLF59LacctmDtNPwC0mi+cLbkjmHycfgIhCddrcXRQBh8Q+QtmgfjcVvoa89gJdPKDG5hag0'
                                '2VR8+bjk8sMvNJnwpHnUndwg+fAjwS90HIkz3yBobB5t332Ara+DwMhc4vJeobf1DO0VO1zcuGkvkzBjE6bOcq'
                                '5+sxZlQCTKgEjXeJ++CofNjNJfjXrCY4TGzqb54lZMneXIvQKInLSSkNgCKvYvv2NNi6nFbXHYr3cDzkEXNJ7y'
                                'uqr30fHDJ6TO303d6Y0Y2ooJ1GQRn7dhYFN59QsXt+XSPwhPnMekhz+l9sRL9HVfISAig/jpGzC2l9Ja9v6Q7z'
                                'psPu7k2lggKvOXaNPX4BeajMNqorvuMPVnXne76x835x0iU3/GqXdjhl2fAXJWlGA1t7uujWGgbUVnryNIOxWF'
                                'TzAWYwu6qt3Un3kNh22gzckUPuSvk+7+b0XJf6a5zvxKfzWxU9YTljgPH1U0dksPpo7L1J95nZ7mk3el6Q4ZSw'
                                '6h8Ake8dp4JJ7k2tjYTFvZNrfXxjK5krhpL6OeuBwfVRTWvg46r3xG7fGXJSeoEfLxf4J8bUZEdSuMAAAAAElF'
                                'TkSuQmCC')
        image = Image.open(BytesIO(data))
        assert pytesseract.image_to_string(image) == '+971523244067'


class MiddlewaresTestCase(BaseTestCase):
    def test_agent_middleware(self):
        # Todo: Can not import AgentMiddleware globally as it leads to issue with post_save signals
        from shoutit.middleware import AgentMiddleware

        # Todo: Add more cases
        AgentCase = namedtuple('AgentCase', ['user_agent', 'app_version', 'build_no', 'os_version'])
        test_cases = [
            AgentCase('Shoutit Staging/3.0.3 (com.appunite.shoutit; build:44000; iOS 9.3.0) Alamofire/4.5.0',
                      app_version='3.0.3', build_no=44000, os_version='9.3.0'),
            AgentCase('Shoutit Staging/com.appunite.shoutit (22000; OS Version 9.3.2 (Build 13F69))',
                      app_version=None, build_no=22000, os_version=None),
        ]
        for case in test_cases:
            request = Mock()
            request.META = {'HTTP_USER_AGENT': case.user_agent}
            AgentMiddleware.process_request(request)
            assert request.app_version == case.app_version
            assert request.build_no == case.build_no
            assert request.os_version == case.os_version
