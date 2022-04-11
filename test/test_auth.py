import unittest
from app.auth import get_hashed_password, verify_password


class AuthTestCase(unittest.TestCase):
    def test_authentication(self):
        password = 'this+is-a#test!password'
        hashed = get_hashed_password(password)
        self.assertTrue(verify_password(password, hashed))

        upassword = u'another1test2password3'
        uhashed = get_hashed_password(upassword)
        self.assertTrue(verify_password(upassword, uhashed))


if __name__ == '__main__':
    unittest.main()
