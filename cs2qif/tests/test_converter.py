import unittest

from ..QifConverter import QifConverter


class TestConverter(unittest.TestCase):
    def test_converter_act(self):
        """Test that the the account csv is converted correctly"""
        with QifConverter(
            "./cs2qif/tests/data/konto.csv",
            "./cs2qif/tests/data/konto.qif",
        ) as q:
            q.convertCsv()
            self.assertEqual(len(q.transactions), 63)

    def test_converter_cc(self):
        """Test that the credit card csv is converted correctly"""
        with QifConverter(
            "./cs2qif/tests/data/amex.csv", "./cs2qif/tests/data/amex.qif", True
        ) as q:
            q.convertCsv()
            self.assertEqual(len(q.transactions), 142)


if __name__ == "__main__":
    unittest.main()
