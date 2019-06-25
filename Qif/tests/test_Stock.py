import unittest
import HtmlTestRunner

from ..Converter import processCsv

class StockTest(unittest.TestCase):
  def testValMustBeNoneWhenInitialized(self):
    st = Stock()
    self.assertIsNone(st.val)

  def testValHasValueAfterInitialized(self):
    st = Stock(4)
    self.assertIsNotNone(st.val)

if __name__ == '__main__':
  unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output="./reports/"))
