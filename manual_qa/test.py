# test.py
#
# deemed necessary to verify that regexs work

from qa_parser import QALineRes

from unittest import TestCase, main
import re

all_cases = {
    'Header': {
        'good': [
            ('##Name', {'name':'Name'}),
            ('# Name', {'name':'Name'}),
            ],
        'bad': [
            ('foo', None),
            ('', None),
            (' #', None),
            ]
    },
    'Section': {
        'good': [
            ('ABCName', {'name':'ABCName'}),
            ('AB123  ', {'name':'AB123  '}),
            ],
        'bad': [
            ('asdf', None),
            (' ABC', None),
            ('#', None),
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
    'QuestionNumber': {
        'good': [
            ('2. **How many years does Mono exist?** ', 
                {'question':'How many years does Mono exist?','number':'2'}),
            (' 3.  ** foo bar? **', 
                {'question':'foo bar?','number':'3'}),
            ],
        'bad': [
            ('asdf', None),
            ('   ** foo bar? **', None),
            ]
    },
    'Answer': {
        'good': [
            ('a) We\'ve been in business', {'answer':'We\'ve been in business'}),
            ('    We\'ve been in business', {'answer':'We\'ve been in business'}),
            ('****a) ****We cover every aspect',{'answer':'We cover every aspect'}),
            ('   [Contact us](https://www.foo.com) yo momma', {'answer':'[Contact us](https://www.foo.com) yo momma'}),
            ],
        'bad': [
            ('  **We\'ve been in business?**', None),
            ('1. asdf', None),
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
            ('  **greeting message', None),
            ('2.  **question ?**', None),
            ('# header stuff', None),
            ]
    },
    'Empty': {
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
class QuestionNumberReTest(metaclass=ReTestMeta): pass
class AnswerReTest(metaclass=ReTestMeta): pass
class GreetingMessageReTest(metaclass=ReTestMeta): pass
class GreetingReTest(metaclass=ReTestMeta): pass

#
#class HeaderReTest(TestCase):
#    def test_good_Header(self):
#        r = QALineRes['Header']
#        for test,result in Header_cases['good']:
#            self.assertEqual(r.match(test)['name'],result)
#
#    def test_bad_Header(self):
#        r = QALineRes['Header']
#        for test,result in Header_cases['bad']:
#            self.assertEqual(r.match(test),None)


if __name__ == '__main__':
    main()
