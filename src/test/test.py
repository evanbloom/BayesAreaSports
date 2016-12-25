from main.predicter import *
import unittest

class TestPredictor(unittest.TestCase):

    def test_create_params_p(self):
	p = .15
	N = 30
	alpha, beta = predicter.create_params (p, N)
	self.assertEqual(p, alpha/(alpha + beta))

if __name__ == '__main__':
    unittest.main()
