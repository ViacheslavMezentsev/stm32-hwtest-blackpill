"""Regression for the real portability failure: ELF holes and RAM VMA / Flash LMA."""
import unittest
from snapshot import load_regions

TABLE = """
  0 .text 00000010 80000000 80000000 00001000 2**2
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
  1 .data 00000010 40000000 80000020 00002000 2**2
                  CONTENTS, ALLOC, LOAD, DATA
  2 .bss 00000040 40000010 80000030 00002100 2**2
                  ALLOC
"""


class RegionTests(unittest.TestCase):
    def test_gap_not_compared_and_data_uses_lma(self):
        regions = load_regions(TABLE, 0x30)
        self.assertEqual([(r["address"], r["size"]) for r in regions],
                         [(0x80000000, 16), (0x80000020, 16)])

    def test_outside_image(self):
        with self.assertRaises(ValueError):
            load_regions(TABLE, 0x20)

    def test_ram_load_rejected(self):
        with self.assertRaises(ValueError):
            load_regions(TABLE.replace("40000000 80000020", "40000000 40000000"), 0x30)

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            load_regions(TABLE.replace("80000020", "80000008"), 0x30)


if __name__ == "__main__":
    unittest.main()
