import unittest

from cwn_coordination_assurance.integrity import canonical_bytes, sign_record, verify_record


class IntegrityTests(unittest.TestCase):
    def test_canonical_order(self): self.assertEqual(canonical_bytes({"b": 1, "a": 2}), canonical_bytes({"a": 2, "b": 1}))
    def test_verify(self):
        record = {"a": 1}
        sig = sign_record(record, b"test-only-key")
        self.assertTrue(verify_record(record, sig, b"test-only-key"))
    def test_tamper(self):
        sig = sign_record({"a": 1}, b"test-only-key")
        self.assertFalse(verify_record({"a": 2}, sig, b"test-only-key"))
    def test_wrong_key(self):
        record = {"a": 1}
        self.assertFalse(verify_record(record, sign_record(record, b"k1"), b"k2"))
    def test_unicode_stable(self): self.assertEqual(canonical_bytes({"x": "é"}), b'{"x":"\xc3\xa9"}')


if __name__ == "__main__": unittest.main()

