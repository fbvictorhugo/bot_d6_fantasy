import unittest

from d6_bot.bot import parse_roll_expression


class RollParserTests(unittest.TestCase):
    def test_default_roll_is_two_d6(self):
        self.assertEqual(parse_roll_expression(""), {"dice": 2, "sides": 6, "modifier": 0})

    def test_roll_with_single_dice_expression(self):
        self.assertEqual(parse_roll_expression("1d20"), {"dice": 1, "sides": 20, "modifier": 0})

    def test_roll_with_three_d8(self):
        self.assertEqual(parse_roll_expression("3d8"), {"dice": 3, "sides": 8, "modifier": 0})

    def test_roll_with_modifier_plus(self):
        self.assertEqual(parse_roll_expression("2d6 +1"), {"dice": 2, "sides": 6, "modifier": 1})

    def test_roll_with_plain_number_as_modifier(self):
        self.assertEqual(parse_roll_expression("2"), {"dice": 2, "sides": 6, "modifier": 2})

    def test_roll_with_only_modifier_plus(self):
        self.assertEqual(parse_roll_expression("+1"), {"dice": 2, "sides": 6, "modifier": 1})

    def test_roll_with_modifier_minus(self):
        self.assertEqual(parse_roll_expression("2d6-2"), {"dice": 2, "sides": 6, "modifier": -2})

    def test_roll_with_whitespace(self):
        self.assertEqual(parse_roll_expression("  3d8   + 4  "), {"dice": 3, "sides": 8, "modifier": 4})


if __name__ == "__main__":
    unittest.main()
