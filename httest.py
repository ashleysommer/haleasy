import string, random
from haleasy import HALEasy
name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
h = HALEasy('http://haltalk.herokuapp.com/')
l = h.link(rel='http://haltalk.herokuapp.com/rels/signup')
s = l.follow(method='POST', data={'username': name, 'password': '1234567'})
print(s.doc.as_object())
print(s.properties())