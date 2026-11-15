"""The admin text boxes behave the way they look: dots make lists, Enter makes a new line."""

from django.test import SimpleTestCase

from portfolio.templatetags.markdown_extras import markdown_filter


class MarkdownTidyTests(SimpleTestCase):
    def test_dot_and_hyphen_bullets_both_make_a_list(self):
        for marker in ["·", "•", "-"]:
            with self.subTest(marker=marker):
                html = markdown_filter(f"{marker} one\n{marker} two")
                self.assertIn("<ul>", html)
                self.assertEqual(html.count("<li>"), 2)
                self.assertNotIn(marker + " ", html)

    def test_indented_bullets_right_after_text_still_make_a_list(self):
        html = markdown_filter("What I work on:\n      · Pipelines\n\n      · Agents")
        self.assertIn("<p>What I work on:</p>", html)
        self.assertEqual(html.count("<li>"), 2)
        self.assertNotIn("<pre>", html)  # leading spaces never turn into a code block

    def test_every_enter_is_a_new_line(self):
        html = markdown_filter("First line\nSecond line\n\nNew paragraph")
        self.assertIn("First line<br>", html)
        self.assertEqual(html.count("<p>"), 2)

    def test_bold_and_italic(self):
        html = markdown_filter("an **AI engineer** who *actually* ships")
        self.assertIn("<strong>AI engineer</strong>", html)
        self.assertIn("<em>actually</em>", html)

    def test_titles_become_small_section_headings(self):
        html = markdown_filter("# Big\n\n## Medium\n\n### Small\n\n##### Tiny")
        self.assertEqual(html.count("<h3>"), 3)
        self.assertEqual(html.count("<h4>"), 1)
        self.assertNotIn("<h1>", html)
        self.assertNotIn("<h2>", html)

    def test_fenced_code_keeps_its_spaces(self):
        html = markdown_filter("```\n    indented()\n```")
        self.assertIn("<pre><code>    indented()", html)
