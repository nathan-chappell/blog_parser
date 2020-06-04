# test.py
#
# deemed necessary to verify that regexs work

from qa_parser_2 import QALineRes

from unittest import TestCase, main
import re

all_cases = {
    'Header': {
        'good': [
            ('##Name', {'header':'Name'}),
            ('# Name', {'header':'Name'}),
            ],
        'bad': [
            ('foo', None),
            ('', None),
            (' #', None),
            ]
    },
    'Section': {
        'good': [
            ('ABCName', {'section':'ABCName'}),
            ('AB123  ', {'section':'AB123  '}),
            ],
        'bad': [
            ('asdf', None),
            (' ABC', None),
            ('#', None),
            ('   ** foo bar? **', None),
            ]
    },
    'Question': {
        'good': [
            ('**foo bar?**', {'question':'foo bar?'}),
            ('   ** foo bar? **', {'question':'foo bar?'}),
            ],
        'bad': [
            ('asdf', None),
            (' ABC', None),
            ('#', None),
            ]
    },
    'Answer': {
        'good': [
            ('    We\'ve been in business', {'answer':'We\'ve been in business'}),
            ('   [Contact us](https://www.foo.com) yo momma', {'answer':'[Contact us](https://www.foo.com) yo momma'}),
            ],
        'bad': [
            ('  **We\'ve been in business?**', None),
            ]
    },
    'GreetingMessage': {
        'good': [
            ('     **GREEting MEssage**   ', {}),
            ('**greeting   message** ', {}),
            ],
        'bad': [
            ('  **greeting message', None),
            ('2.  **greeting message', None),
            ('greeting message', None),
            ]
    },
    'Greeting': {
        'good': [
            ('     scooby doobie doo!', {'greeting':'scooby doobie doo!'}),
            ('foo bar *meow*', {'greeting':'foo bar *meow*'}),
            ],
        'bad': [
            ('  **greeting message**', None),
            ('2.  **question ?**', None),
            ('# header stuff', None),
            ]
    },
    'EmptyOrAst': {
        'good': [
            ('   ', {'line':'   '}),
            ('', {'line':''}),
            (' **** ', {'line':' **** '}),
            ],
        'bad': [
            ('  **greeting message', None),
            ('2.  **question ?**', None),
            ('_', None),
            ]
    },
}

class ReTestMeta(type):
    def __new__(mcs,name,bases,dict_):
        re_name = name[:name.find('ReTest')]
        dict_['regex'] = QALineRes[re_name]

        for i,case in enumerate(all_cases[re_name]['good']):
            def test_(self,i=i,case=case):
                m = self.regex.match(case[0])
                self.assertIsNotNone(m)
                self.assertEqual(case[1],m.groupdict())
            dict_['test_'+re_name+'_good_'+str(i)] = test_

        for i,case in enumerate(all_cases[re_name]['bad']):
            def test_(self,i=i,case=case):
                m = self.regex.match(case[0])
                self.assertIsNone(m)
            dict_['test_'+re_name+'_bad_'+str(i)] = test_

        return type.__new__(mcs,name,(TestCase,),dict_)

class HeaderReTest(metaclass=ReTestMeta): pass
class SectionReTest(metaclass=ReTestMeta): pass
class QuestionReTest(metaclass=ReTestMeta): pass
class AnswerReTest(metaclass=ReTestMeta): pass
class GreetingMessageReTest(metaclass=ReTestMeta): pass
class GreetingReTest(metaclass=ReTestMeta): pass
class EmptyOrAstReTest(metaclass=ReTestMeta): pass


if __name__ == '__main__':
    main()
