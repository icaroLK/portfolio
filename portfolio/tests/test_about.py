from datetime import date

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from portfolio.models import (
    Education,
    Experience,
    Service,
    SiteSettings,
    Skill,
    SkillGroup,
    Tech,
)

ABOUT = reverse("portfolio:about")


def make_experience(role, order, details="", published=True, end=None):
    return Experience.objects.create(
        role=role,
        company=f"{role} Co",
        location="Remote (US)",
        start_date=date(2025, 3, 1),
        end_date=end,
        summary=f"{role} summary",
        details=details,
        order=order,
        is_published=published,
    )


class AboutTestData(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(
            site_name="Test Name",
            headline="H",
            about_heading="Hi, I'm Test.",
            about_bio="Bio line.",
            services_intro="Services intro line.",
            contact_heading="Let's talk.",
            contact_text="Contact text line.",
            email="hi@example.com",
            notification_email="private-inbox@example.com",
        )
        cls.with_details = make_experience(
            "Engineer", order=1, details="Long text.\n\n- bullet one\n- bullet two",
            end=date(2026, 6, 1),
        )
        cls.no_details = make_experience("Freelancer", order=0)
        make_experience("Hidden job", order=2, published=False)
        cls.with_details.techs.set([Tech.objects.create(name="n8n", slug="n8n")])

        Education.objects.create(
            degree="B.Sc. Software", school="PUCPR", city="Curitiba",
            start_date=date(2023, 2, 1), end_date=date(2027, 6, 1), order=0,
        )
        Education.objects.create(
            degree="Erasmus", school="AGH", start_date=date(2026, 2, 1),
            period_label="Erasmus semester, 2026", order=1,
        )
        Education.objects.create(
            degree="Hidden degree", school="X", start_date=date(2020, 1, 1), is_published=False,
        )

        backend = SkillGroup.objects.create(name="Backend", order=0)
        Skill.objects.create(group=backend, name="Django", order=0)
        SkillGroup.objects.create(name="Empty group", order=1)

        Service.objects.create(title="Websites", description="Sites.", order=5)
        Service.objects.create(title="Bots", description="Bots.", order=9)
        Service.objects.create(title="Hidden service", description="No.", is_published=False)


class AboutPageTests(AboutTestData):
    def test_page_loads_with_intro(self):
        response = self.client.get(ABOUT)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1", count=1)
        self.assertContains(response, "Hi, I&#x27;m Test.")
        self.assertContains(response, "Bio line.")

    def test_header_marks_about_active(self):
        self.assertContains(self.client.get(ABOUT), 'aria-current="page">About')

    def test_only_published_items_in_admin_order(self):
        content = self.client.get(ABOUT).content.decode()
        self.assertLess(content.index("Freelancer"), content.index("Engineer"))
        for hidden in ["Hidden job", "Hidden degree", "Hidden service"]:
            self.assertNotIn(hidden, content)

    def test_show_details_only_when_details_filled(self):
        response = self.client.get(ABOUT)
        self.assertContains(response, "Show details", count=1)
        self.assertContains(response, "<li>bullet one</li>", html=True)

    def test_experience_dates(self):
        response = self.client.get(ABOUT)
        self.assertContains(response, "Mar 2025 – Jun 2026")
        self.assertContains(response, "Mar 2025 – Present")

    def test_education_label_wins_over_dates(self):
        response = self.client.get(ABOUT)
        self.assertContains(response, "Erasmus semester, 2026")
        self.assertContains(response, "Feb 2023 – Jun 2027")

    def test_empty_skill_group_hidden(self):
        response = self.client.get(ABOUT)
        self.assertContains(response, "Backend")
        self.assertNotContains(response, "Empty group")

    def test_services_numbered_from_01(self):
        response = self.client.get(ABOUT)
        self.assertContains(response, "Services intro line.")
        self.assertContains(response, ">01</span>")
        self.assertContains(response, ">02</span>")

    def test_contact_card_texts_from_settings(self):
        response = self.client.get(ABOUT)
        self.assertContains(response, 'id="contact"')
        self.assertContains(response, "Let&#x27;s talk.")
        self.assertContains(response, "Contact text line.")
        self.assertContains(response, 'href="mailto:hi@example.com"')

    def test_notification_email_never_shown(self):
        self.assertNotContains(self.client.get(ABOUT), "private-inbox@example.com")

    def test_success_message_only_after_sending(self):
        self.assertNotContains(self.client.get(ABOUT), "your message was sent")
        self.assertContains(self.client.get(ABOUT + "?sent=1"), "your message was sent")

    def test_fixed_number_of_queries(self):
        # Settings, experiences, their techs, education, skill groups, skills, services.
        # Adding more rows must not add queries.
        self.client.get(ABOUT)  # warm up
        with CaptureQueriesContext(connection) as before:
            self.client.get(ABOUT)
        for i in range(5):
            job = make_experience(f"Extra {i}", order=10 + i)
            job.techs.set(Tech.objects.all())
            Skill.objects.create(group=SkillGroup.objects.create(name=f"G{i}"), name="S")
        with CaptureQueriesContext(connection) as after:
            self.client.get(ABOUT)
        self.assertEqual(len(before), len(after))
        self.assertLessEqual(len(after), 8)


class AboutSectionToggleTests(AboutTestData):
    def turn_off(self, field):
        SiteSettings.objects.filter(pk=1).update(**{field: False})

    def test_each_toggle_hides_its_section(self):
        sections = {
            "show_experience": "experience-heading",
            "show_education": "education-heading",
            "show_skills": "skills-heading",
            "show_services": "services-heading",
        }
        for field, heading_id in sections.items():
            with self.subTest(field=field):
                self.assertContains(self.client.get(ABOUT), heading_id)
                self.turn_off(field)
                self.assertNotContains(self.client.get(ABOUT), heading_id)

    def test_contact_toggle_hides_form_but_keeps_card(self):
        self.turn_off("show_contact_form")
        response = self.client.get(ABOUT)
        self.assertNotContains(response, "Send message")
        self.assertContains(response, 'id="contact"')
        self.assertContains(response, "Let&#x27;s talk.")

    def test_empty_sections_hidden(self):
        Experience.objects.all().delete()
        Service.objects.all().delete()
        response = self.client.get(ABOUT)
        self.assertNotContains(response, "experience-heading")
        self.assertNotContains(response, "services-heading")
