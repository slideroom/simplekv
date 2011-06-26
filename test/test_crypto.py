#!/usr/bin/env python
# coding=utf8

import hashlib
import hmac
from cStringIO import StringIO
import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from simplekv.crypt import _HMACFileReader, VerificationException


def _alter_byte(s, n):
    return s[:n] + chr((ord(s[n]) + 1) % 255) + s[n + 1:]


class TestHMACFileReader(unittest.TestCase):
    secret_key = 'devkey##123'
    data = 'helloworld!'\
           '@\xa9;\x99\xfai0\xb9!2\xd7\x82\xf4\xf3g\xf8\xa9\xcd\xcf\xff'
    hashfunc = hashlib.sha256
    expected_digest = '\x05n\xbc\x91\x02\x171\xe1G\xcc\xd6\xc6\x01'\
                      '\xc4\x0b+W\xb8W\xb1\x027\x03\xf2B\x98\xf7'\
                      '\xb4\xf7\x91KD'
    stored_data_and_hash = data + expected_digest
    reading_lengths = range(1, len(data) * 3)

    def setUp(self):
        self.buf = StringIO(self.stored_data_and_hash)
        self.hm = hmac.HMAC(self.secret_key, None, self.hashfunc)
        self.reader = _HMACFileReader(self.hm, self.buf)

    def test_setUp_is_correct(self):
        hm = hmac.HMAC(self.secret_key, self.data, self.hashfunc)

        self.assertEqual(hm.digest(), self.expected_digest)

    def test_reading_limit_0(self):
        self.assertEqual('', self.reader.read(0))
        self.assertEqual('', self.reader.read(0))

    def test_reading_with_limit(self):
        # try for different read lengths
        for n in self.reading_lengths:
            buf = StringIO(self.stored_data_and_hash)
            hm = hmac.HMAC(self.secret_key, None, self.hashfunc)

            reader = _HMACFileReader(hm, buf)

            data = ''
            while True:
                r = reader.read(n)
                if '' == r:
                    break
                data += r

            self.assertEqual(data, self.data)

    def test_manipulated_input_full_read(self):
        for n in range(0, 20) + range(-1, -20, -1):
            broken_stored_data_and_hash = _alter_byte(
                self.stored_data_and_hash,
                n
            )

            reader = _HMACFileReader(
                hmac.HMAC(self.secret_key, None, self.hashfunc),
                StringIO(broken_stored_data_and_hash)
            )

            with self.assertRaises(VerificationException):
                reader.read()

    def test_manipulated_input_incremental_read(self):
        for n in range(0, 20) + range(-1, -20, -1):
            broken_stored_data_and_hash = _alter_byte(
                self.stored_data_and_hash,
                n
            )

            reader = _HMACFileReader(
                hmac.HMAC(self.secret_key, None, self.hashfunc),
                StringIO(broken_stored_data_and_hash)
            )

            with self.assertRaises(VerificationException):
                bitesize = 100
                while True:
                    if len(reader.read(bitesize)) != bitesize:
                        break

    def test_input_too_short(self):
        with self.assertRaises(VerificationException):
            reader = _HMACFileReader(
                hmac.HMAC(self.secret_key, None, self.hashfunc),
                StringIO('a')
            )


# run all tests on input that is shorter/longer/equal than the hash
class TestHMACFileReaderLongInput(TestHMACFileReader):
    data = '\x99\xfai0\xb9!2\xd7\x82\xf4\xf3' * 1024 * 1024
    expected_digest = hmac.HMAC(
        TestHMACFileReader.secret_key, data, TestHMACFileReader.hashfunc
    ).digest()
    stored_data_and_hash = data + expected_digest

    reading_lengths = [10 ** n for n in xrange(2, 8)]


class TestHMACFileReaderShortInput(TestHMACFileReader):
    data = 'aca4'
    expected_digest = hmac.HMAC(
        TestHMACFileReader.secret_key, data, TestHMACFileReader.hashfunc
    ).digest()
    stored_data_and_hash = data + expected_digest

    reading_lengths = range(1, 100)


class TestHMACFileReaderEqualInput(TestHMACFileReader):
    # this string is as long as a sha256 sum
    data = '8b97bca79750847558d488e2ea4de79903c9c71c9af27ecf1b3dff5dba2abdd9'
    expected_digest = hmac.HMAC(
        TestHMACFileReader.secret_key, data, TestHMACFileReader.hashfunc
    ).digest()
    stored_data_and_hash = data + expected_digest

    reading_lengths = range(1, 100)


# different digest algorithm and key
class TestHMACFileReaderDifferentHashfuncAndKey(TestHMACFileReader):
    # this string is as long as a sha256 sum
    hashfunc = hashlib.sha1
    secret_key = 'secret_key_b'
    expected_digest = hmac.HMAC(
        secret_key, TestHMACFileReader.data, hashfunc
    ).digest()
    stored_data_and_hash = TestHMACFileReader.data + expected_digest

    reading_lengths = range(1, 100)
