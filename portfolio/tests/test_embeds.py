from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from portfolio.embeds import embed_url, validate_video_url

YT = "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
LOOM = "https://www.loom.com/embed/0123456789abcdef0123456789abcdef"


class EmbedUrlTests(SimpleTestCase):
    def test_youtube_link_shapes(self):
        links = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ?si=share-token",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/live/dQw4w9WgXcQ",
        ]
        for link in links:
            with self.subTest(link=link):
                self.assertEqual(embed_url(link), YT)

    def test_loom_link_shapes(self):
        for link in [
            "https://www.loom.com/share/0123456789abcdef0123456789abcdef",
            "https://loom.com/share/0123456789abcdef0123456789abcdef?sid=abc",
            "https://www.loom.com/embed/0123456789abcdef0123456789abcdef",
        ]:
            with self.subTest(link=link):
                self.assertEqual(embed_url(link), LOOM)

    def test_unknown_or_broken_links_give_none(self):
        for link in [
            "",
            None,
            "https://vimeo.com/123456",
            "https://www.youtube.com/watch",
            "https://www.youtube.com/watch?v=short",
            "https://www.youtube.com/@somechannel",
            "https://notyoutube.com/watch?v=dQw4w9WgXcQ",
            "https://www.loom.com/looms/videos",
        ]:
            with self.subTest(link=link):
                self.assertIsNone(embed_url(link))

    def test_validator(self):
        validate_video_url("")  # empty is fine: the video box is just hidden
        validate_video_url("https://youtu.be/dQw4w9WgXcQ")
        with self.assertRaises(ValidationError):
            validate_video_url("https://vimeo.com/123456")
