import tempfile, operator, sys, os

from twisted.trial import unittest
from twisted.internet import reactor, defer, interfaces
from twisted.python import log
from zope.interface import Interface, Attribute
from zope.interface.declarations import implementer

from twisted.python.util import sibpath
from OPSI.web2 import stream

def bufstr(data):
    try:
        return str(buffer(data))
    except TypeError:
        raise TypeError("%s doesn't conform to the buffer interface" % (data,))
    
    
class SimpleStreamTests:
    text = '1234567890'
    def test_split(self):
        for point in range(10):
            s = self.makeStream(0)
            a,b = s.split(point)
            if point > 0:
                self.assertEqual(bufstr(a.read()), self.text[:point])
            self.assertEqual(a.read(), None)
            if point < len(self.text):
                self.assertEqual(bufstr(b.read()), self.text[point:])
            self.assertEqual(b.read(), None)

        for point in range(7):
            s = self.makeStream(2, 6)
            self.assertEqual(s.length, 6)
            a,b = s.split(point)
            if point > 0:
                self.assertEqual(bufstr(a.read()), self.text[2:point+2])
            self.assertEqual(a.read(), None)
            if point < 6:
                self.assertEqual(bufstr(b.read()), self.text[point+2:8])
            self.assertEqual(b.read(), None)

    def test_read(self):
        s = self.makeStream()
        self.assertEqual(s.length, len(self.text))
        self.assertEqual(bufstr(s.read()), self.text)
        self.assertEqual(s.read(), None)

        s = self.makeStream(0, 4)
        self.assertEqual(s.length, 4)
        self.assertEqual(bufstr(s.read()), self.text[0:4])
        self.assertEqual(s.read(), None)
        self.assertEqual(s.length, 0)

        s = self.makeStream(4, 6)
        self.assertEqual(s.length, 6)
        self.assertEqual(bufstr(s.read()), self.text[4:10])
        self.assertEqual(s.read(), None)
        self.assertEqual(s.length, 0)
    
class FileStreamTest(SimpleStreamTests, unittest.TestCase):
    def makeStream(self, *args, **kw):
        return stream.FileStream(self.f, *args, **kw)
    
    def setUpClass(self):
        f = tempfile.TemporaryFile('w+')
        f.write(self.text)
        f.seek(0, 0)
        self.f = f

    def test_close(self):
        s = self.makeStream()
        s.close()

        self.assertEqual(s.length, 0)
        # Make sure close doesn't close file
        # would raise exception if f is closed
        self.f.seek(0, 0)

    def test_read2(self):
        s = self.makeStream(0)
        s.CHUNK_SIZE = 6
        self.assertEqual(s.length, 10)
        self.assertEqual(bufstr(s.read()), self.text[0:6])
        self.assertEqual(bufstr(s.read()), self.text[6:10])
        self.assertEqual(s.read(), None)

        s = self.makeStream(0)
        s.CHUNK_SIZE = 5
        self.assertEqual(s.length, 10)
        self.assertEqual(bufstr(s.read()), self.text[0:5])
        self.assertEqual(bufstr(s.read()), self.text[5:10])
        self.assertEqual(s.read(), None)

        s = self.makeStream(0, 20)
        self.assertEqual(s.length, 20)
        self.assertEqual(bufstr(s.read()), self.text)
        self.assertRaises(RuntimeError, s.read) # ran out of data

class MMapFileStreamTest(SimpleStreamTests, unittest.TestCase):
    def makeStream(self, *args, **kw):
        return stream.FileStream(self.f, *args, **kw)
    
    def setUpClass(self):
        f = tempfile.TemporaryFile('w+')
        self.text = self.text*(stream.MMAP_THRESHOLD//len(self.text) + 1)
        f.write(self.text)
        f.seek(0, 0)
        self.f=f

    def test_mmapwrapper(self):
        self.assertRaises(TypeError, stream.mmapwrapper)
        self.assertRaises(TypeError, stream.mmapwrapper, offset = 0)
        self.assertRaises(TypeError, stream.mmapwrapper, offset = None)

    if not stream.mmap:
        test_mmapwrapper.skip = 'mmap not supported here'
            
class MemoryStreamTest(SimpleStreamTests, unittest.TestCase):
    def makeStream(self, *args, **kw):
        return stream.MemoryStream(self.text, *args, **kw)

    def test_close(self):
        s = self.makeStream()
        s.close()
        self.assertEqual(s.length, 0)

    def test_read2(self):
        self.assertRaises(ValueError, self.makeStream, 0, 20)


testdata = """I was angry with my friend:
I told my wrath, my wrath did end.
I was angry with my foe:
I told it not, my wrath did grow.

And I water'd it in fears,
Night and morning with my tears;
And I sunned it with smiles,
And with soft deceitful wiles.

And it grew both day and night,
Till it bore an apple bright;
And my foe beheld it shine,
And he knew that is was mine,

And into my garden stole
When the night had veil'd the pole:
In the morning glad I see
My foe outstretch'd beneath the tree"""

class TestSubstream(unittest.TestCase):
    
    def setUp(self):
        self.data = testdata
        self.s = stream.MemoryStream(self.data)

    def suckTheMarrow(self, s):
        return ''.join(map(str, list(iter(s.read, None))))

    def testStart(self):
        s = stream.substream(self.s, 0, 11)
        self.assertEqual('I was angry', self.suckTheMarrow(s))

    def testNotStart(self):
        s = stream.substream(self.s, 12, 26)
        self.assertEqual('with my friend', self.suckTheMarrow(s))

    def testReverseStartEnd(self):
        self.assertRaises(ValueError, stream.substream, self.s, 26, 12)

    def testEmptySubstream(self):
        s = stream.substream(self.s, 11, 11)
        self.assertEqual('', self.suckTheMarrow(s))

    def testEnd(self):
        size = len(self.data)
        s = stream.substream(self.s, size-4, size)
        self.assertEqual('tree', self.suckTheMarrow(s))

    def testPastEnd(self):
        size = len(self.data)
        self.assertRaises(ValueError, stream.substream, self.s, size-4, size+8)


class TestBufferedStream(unittest.TestCase):

    def setUp(self):
        self.data = testdata.replace('\n', '\r\n')
        s = stream.MemoryStream(self.data)
        self.s = stream.BufferedStream(s)

    def _cbGotData(self, data, expected):
        self.assertEqual(data, expected)

    def test_readline(self):
        """Test that readline reads a line."""
        d = self.s.readline()
        d.addCallback(self._cbGotData, 'I was angry with my friend:\r\n')
        return d

    def test_readlineWithSize(self):
        """Test the size argument to readline"""
        d = self.s.readline(size = 5)
        d.addCallback(self._cbGotData, 'I was')
        return d

    def test_readlineWithBigSize(self):
        """Test the size argument when it's bigger than the length of the line."""
        d = self.s.readline(size = 40)
        d.addCallback(self._cbGotData, 'I was angry with my friend:\r\n')
        return d

    def test_readlineWithZero(self):
        """Test readline with size = 0."""
        d = self.s.readline(size = 0)
        d.addCallback(self._cbGotData, '')
        return d

    def test_readlineFinished(self):
        """Test readline on a finished stream."""
        nolines = len(self.data.split('\r\n'))
        for i in range(nolines):
            self.s.readline()
        d = self.s.readline()
        d.addCallback(self._cbGotData, '')
        return d

    def test_readlineNegSize(self):
        """Ensure that readline with a negative size raises an exception."""
        self.assertRaises(ValueError, self.s.readline, size = -1)

    def test_readlineSizeInDelimiter(self):
        """
        Test behavior of readline when size falls inside the
        delimiter.
        """
        d = self.s.readline(size=28)
        d.addCallback(self._cbGotData, "I was angry with my friend:\r")
        d.addCallback(lambda _: self.s.readline())
        d.addCallback(self._cbGotData, "\nI told my wrath, my wrath did end.\r\n")
        
    def test_readExactly(self):
        """Make sure readExactly with no arg reads all the data."""
        d = self.s.readExactly()
        d.addCallback(self._cbGotData, self.data)
        return d

    def test_readExactly(self):
        """Test readExactly with a number."""
        d = self.s.readExactly(10)
        d.addCallback(self._cbGotData, self.data[:10])
        return d

    def test_readExactlyBig(self):
        """
        Test readExactly with a number larger than the size of the
        datastream.
        """
        d = self.s.readExactly(100000)
        d.addCallback(self._cbGotData, self.data)
        return d

    def test_read(self):
        """
        Make sure read() also functions. (note that this test uses
        an implementation detail of this particular stream. s.read()
        isn't guaranteed to return self.data on all streams.)
        """
        self.assertEqual(str(self.s.read()), self.data)


@implementer(stream.IStream, stream.IByteStream)
class TestStreamer:

    length = None

    readCalled=0
    closeCalled=0

    def __init__(self, list):
        self.list = list

    def read(self):
        self.readCalled+=1
        if self.list:
            return self.list.pop(0)
        return None

    def close(self):
        self.closeCalled+=1
        self.list = []
        
class FallbackSplitTest(unittest.TestCase):
    def test_split(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        left,right = stream.fallbackSplit(s, 5)
        self.assertEqual(left.length, 5)
        self.assertEqual(right.length, None)
        self.assertEqual(bufstr(left.read()), 'abcd')
        d = left.read()
        d.addCallback(self._cbSplit, left, right)
        return d

    def _cbSplit(self, result, left, right):
        self.assertEqual(bufstr(result), 'e')
        self.assertEqual(left.read(), None)

        self.assertEqual(bufstr(right.read().result), 'fgh')
        self.assertEqual(bufstr(right.read()), 'ijkl')
        self.assertEqual(right.read(), None)

    def test_split2(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        left,right = stream.fallbackSplit(s, 4)
        
        self.assertEqual(left.length, 4)
        self.assertEqual(right.length, None)
        
        self.assertEqual(bufstr(left.read()), 'abcd')
        self.assertEqual(left.read(), None)

        self.assertEqual(bufstr(right.read().result), 'efgh')
        self.assertEqual(bufstr(right.read()), 'ijkl')
        self.assertEqual(right.read(), None)

    def test_splitsplit(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        left,right = stream.fallbackSplit(s, 5)
        left,middle = left.split(3)
        
        self.assertEqual(left.length, 3)
        self.assertEqual(middle.length, 2)
        self.assertEqual(right.length, None)
        
        self.assertEqual(bufstr(left.read()), 'abc')
        self.assertEqual(left.read(), None)

        self.assertEqual(bufstr(middle.read().result), 'd')
        self.assertEqual(bufstr(middle.read().result), 'e')
        self.assertEqual(middle.read(), None)

        self.assertEqual(bufstr(right.read().result), 'fgh')
        self.assertEqual(bufstr(right.read()), 'ijkl')
        self.assertEqual(right.read(), None)

    def test_closeboth(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        left,right = stream.fallbackSplit(s, 5)
        left.close()
        self.assertEqual(s.closeCalled, 0)
        right.close()

        # Make sure nothing got read
        self.assertEqual(s.readCalled, 0)
        self.assertEqual(s.closeCalled, 1)

    def test_closeboth_rev(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        left,right = stream.fallbackSplit(s, 5)
        right.close()
        self.assertEqual(s.closeCalled, 0)
        left.close()

        # Make sure nothing got read
        self.assertEqual(s.readCalled, 0)
        self.assertEqual(s.closeCalled, 1)

    def test_closeleft(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        left,right = stream.fallbackSplit(s, 5)
        left.close()
        d = right.read()
        d.addCallback(self._cbCloseleft, right)
        return d

    def _cbCloseleft(self, result, right):
        self.assertEqual(bufstr(result), 'fgh')
        self.assertEqual(bufstr(right.read()), 'ijkl')
        self.assertEqual(right.read(), None)

    def test_closeright(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        left,right = stream.fallbackSplit(s, 3)
        right.close()

        self.assertEqual(bufstr(left.read()), 'abc')
        self.assertEqual(left.read(), None)
        
        self.assertEqual(s.closeCalled, 1)


class ProcessStreamerTest(unittest.TestCase):

    if interfaces.IReactorProcess(reactor, None) is None:
        skip = "Platform lacks spawnProcess support, can't test process streaming."

    def runCode(self, code, inputStream=None):
        if inputStream is None:
            inputStream = stream.MemoryStream("")
        return stream.ProcessStreamer(inputStream, sys.executable,
                                      [sys.executable, "-u", "-c", code],
                                      os.environ)

    def test_output(self):
        p = self.runCode("import sys\nfor i in range(100): sys.stdout.write('x' * 1000)")
        l = []
        d = stream.readStream(p.outStream, l.append)
        def verify(_):
            self.assertEqual("".join(l), ("x" * 1000) * 100)
        d2 = p.run()
        return d.addCallback(verify).addCallback(lambda _: d2)

    def test_errouput(self):
        p = self.runCode("import sys\nfor i in range(100): sys.stderr.write('x' * 1000)")
        l = []
        d = stream.readStream(p.errStream, l.append)
        def verify(_):
            self.assertEqual("".join(l), ("x" * 1000) * 100)
        p.run()
        return d.addCallback(verify)

    def test_input(self):
        p = self.runCode("import sys\nsys.stdout.write(sys.stdin.read())",
                         "hello world")
        l = []
        d = stream.readStream(p.outStream, l.append)
        d2 = p.run()
        def verify(_):
            self.assertEqual("".join(l), "hello world")
            return d2
        return d.addCallback(verify)

    def test_badexit(self):
        p = self.runCode("raise ValueError")
        l = []
        from twisted.internet.error import ProcessTerminated
        def verify(_):
            self.assertEqual(l, [1])
            self.assertTrue(p.outStream.closed)
            self.assertTrue(p.errStream.closed)
        return p.run().addErrback(lambda _: _.trap(ProcessTerminated) and l.append(1)).addCallback(verify)

    def test_inputerror(self):
        p = self.runCode("import sys\nsys.stdout.write(sys.stdin.read())",
                         TestStreamer(["hello", defer.fail(ZeroDivisionError())]))
        l = []
        d = stream.readStream(p.outStream, l.append)
        d2 = p.run()
        def verify(_):
            self.assertEqual("".join(l), "hello")
            return d2
        return d.addCallback(verify).addCallback(lambda _: log.flushErrors(ZeroDivisionError))

    def test_processclosedinput(self):
        p = self.runCode("import sys; sys.stdout.write(sys.stdin.read(3));" +
                         "sys.stdin.close(); sys.stdout.write('def')",
                         "abc123")
        l = []
        d = stream.readStream(p.outStream, l.append)
        def verify(_):
            self.assertEqual("".join(l), "abcdef")
        d2 = p.run()
        return d.addCallback(verify).addCallback(lambda _: d2)


class AdapterTestCase(unittest.TestCase):

    def test_adapt(self):
        fName = self.mktemp()
        f = file(fName, "w")
        f.write("test")
        f.close()
        for i in ("test", buffer("test"), file(fName)):
            s = stream.IByteStream(i)
            self.assertEqual(str(s.read()), "test")
            self.assertEqual(s.read(), None)


class ReadStreamTestCase(unittest.TestCase):

    def test_pull(self):
        l = []
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        return readStream(s, l.append).addCallback(
            lambda _: self.assertEqual(l, ["abcd", "efgh", "ijkl"]))
        
    def test_pullFailure(self):
        l = []
        s = TestStreamer(['abcd', defer.fail(RuntimeError()), 'ijkl'])
        def test(result):
            result.trap(RuntimeError)
            self.assertEqual(l, ["abcd"])
        return readStream(s, l.append).addErrback(test)
    
    def test_pullException(self):
        class Failer:
            def read(self): raise RuntimeError
        return readStream(Failer(), lambda _: None).addErrback(lambda _: _.trap(RuntimeError))

    def test_processingException(self):
        s = TestStreamer(['abcd', defer.succeed('efgh'), 'ijkl'])
        return readStream(s, lambda x: 1/0).addErrback(lambda _: _.trap(ZeroDivisionError))


class ProducerStreamTestCase(unittest.TestCase):

    def test_failfinish(self):
        p = stream.ProducerStream()
        p.write("hello")
        p.finish(RuntimeError())
        self.assertEqual(p.read(), "hello")
        d = p.read()
        l = []
        d.addErrback(lambda _: (l.append(1), _.trap(RuntimeError))).addCallback(
            lambda _: self.assertEqual(l, [1]))
        return d


from OPSI.web2.stream import *
class CompoundStreamTest:
    """
    CompoundStream lets you combine many streams into one continuous stream.
    For example, let's make a stream:
    >>> s = CompoundStream()
    
    Then, add a couple streams:
    >>> s.addStream(MemoryStream("Stream1"))
    >>> s.addStream(MemoryStream("Stream2"))
    
    The length is the sum of all the streams:
    >>> s.length
    14
    
    We can read data from the stream:
    >>> str(s.read())
    'Stream1'

    After having read some data, length is now smaller, as you might expect:
    >>> s.length
    7

    So, continue reading...
    >>> str(s.read())
    'Stream2'

    Now that the stream is exhausted:
    >>> s.read() is None
    True
    >>> s.length
    0

    We can also create CompoundStream more easily like so:
    >>> s = CompoundStream(['hello', MemoryStream(' world')])
    >>> str(s.read())
    'hello'
    >>> str(s.read())
    ' world'
    
    For a more complicated example, let's try reading from a file:
    >>> s = CompoundStream()
    >>> s.addStream(FileStream(open(sibpath(__file__, "stream_data.txt"))))
    >>> s.addStream("================")
    >>> s.addStream(FileStream(open(sibpath(__file__, "stream_data.txt"))))

    Again, the length is the sum:
    >>> int(s.length)
    58
    
    >>> str(s.read())
    "We've got some text!\\n"
    >>> str(s.read())
    '================'
    
    What if you close the stream?
    >>> s.close()
    >>> s.read() is None
    True
    >>> s.length
    0

    Error handling works using Deferreds:
    >>> m = MemoryStream("after")
    >>> s = CompoundStream([TestStreamer([defer.fail(ZeroDivisionError())]), m])
    >>> l = []; x = s.read().addErrback(lambda _: l.append(1))
    >>> l
    [1]
    >>> s.length
    0
    >>> m.length # streams after the failed one got closed
    0

    """


__doctests__ = ['OPSI.web2.test.test_stream', 'OPSI.web2.stream']
# TODO: 
# CompoundStreamTest
# more tests for ProducerStreamTest
# StreamProducerTest
