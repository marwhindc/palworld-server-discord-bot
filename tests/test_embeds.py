import unittest
from utils.embeds import success_embed, info_embed, error_embed

class TestEmbeds(unittest.TestCase):
    def test_embed_colors_and_fields(self):
        """Verifies color coding, title prefixing, and field generation of embeds."""
        embed = success_embed("Test Title", "Test Description", [{"name": "Field1", "value": "Val1", "inline": True}])
        self.assertEqual(embed.title, "🟢 Test Title")
        self.assertEqual(embed.description, "Test Description")
        self.assertEqual(embed.color.value, 0x2ecc71)
        self.assertEqual(len(embed.fields), 1)
        self.assertEqual(embed.fields[0].name, "Field1")
        self.assertEqual(embed.fields[0].value, "Val1")
        
        info = info_embed("Info")
        self.assertEqual(info.title, "🟡 Info")
        self.assertEqual(info.color.value, 0xf1c40f)
        
        err = error_embed("Error")
        self.assertEqual(err.title, "🔴 Error")
        self.assertEqual(err.color.value, 0xe74c3c)

if __name__ == "__main__":
    unittest.main()
