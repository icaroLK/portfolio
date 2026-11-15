"""Month + year date picker in the admin, and the work mode badge on Experience cards."""

from datetime import date

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from portfolio.models import Experience, SiteSettings
from portfolio.widgets import MonthYearWidget

from .helpers import AdminLoginMixin

ABOUT = reverse("portfolio:about")
ADMIN = f"/{settings.ADMIN_PATH}/"


def make_job(**extra):
    fields = {
        "role": "Junior Developer",
        "company": "Aliest",
        "location": "Curitiba, Brazil",
        "start_date": date(2024, 11, 1),
        "end_date": date(2025, 4, 1),
        "summary": "Rebuilt the system.",
        **extra,
    }
    return Experience.objects.create(**fields)


class MonthYearWidgetTests(SimpleTestCase):
    def read(self, month, year):
        return MonthYearWidget().value_from_datadict(
            {"d_0": month, "d_1": year}, {}, "d"
        )

    def test_month_and_year_become_the_first_of_the_month(self):
        self.assertEqual(self.read("2", "2023"), "2023-02-01")

    def test_both_empty_is_no_date(self):
        self.assertEqual(self.read("", ""), "")

    def test_only_one_picked_is_not_a_date(self):
        self.assertEqual(self.read("2", ""), "incomplete")
        self.assertEqual(self.read("", "2023"), "incomplete")

    def test_existing_date_shows_its_month_and_year(self):
        self.assertEqual(MonthYearWidget().decompress(date(2023, 2, 15)), ["2", "2023"])
        self.assertEqual(MonthYearWidget().decompress(None), ["", ""])

    def test_year_list_reaches_back_to_1990_newest_first(self):
        years = [value for value, _ in MonthYearWidget().widgets[1].choices if value]
        self.assertEqual(years[-1], "1990")
        self.assertGreater(int(years[0]), date.today().year)


class DateAdminTests(AdminLoginMixin, TestCase):
    def test_experience_and_education_use_month_year_dropdowns(self):
        for model in ["experience", "education"]:
            with self.subTest(model=model):
                page = self.client.get(f"{ADMIN}portfolio/{model}/add/")
                self.assertContains(page, 'name="start_date_0"')
                self.assertContains(page, 'name="start_date_1"')
                self.assertContains(page, '<option value="2024">2024</option>', html=True)
                self.assertNotContains(page, "vDateField")  # no day calendar

    def post_job(self, **extra):
        data = {
            "role": "Dev", "company": "Co", "location": "", "work_mode": "remote",
            "start_date_0": "2", "start_date_1": "2023",
            "end_date_0": "", "end_date_1": "",
            "summary": "S", "details": "", "is_published": "on", "order": "0",
            **extra,
        }
        return self.client.post(f"{ADMIN}portfolio/experience/add/", data)

    def test_saving_month_and_year(self):
        response = self.post_job()
        self.assertEqual(response.status_code, 302)
        job = Experience.objects.get()
        self.assertEqual(job.start_date, date(2023, 2, 1))
        self.assertIsNone(job.end_date)  # Present
        self.assertEqual(job.work_mode, "remote")

    def test_month_without_year_shows_an_error(self):
        response = self.post_job(end_date_0="6")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid date.")
        self.assertFalse(Experience.objects.exists())

    def test_work_mode_is_three_radio_buttons(self):
        page = self.client.get(f"{ADMIN}portfolio/experience/add/")
        for value in ["onsite", "hybrid", "remote"]:
            self.assertContains(page, f'type="radio" name="work_mode" value="{value}"')


class WorkModeBadgeTests(TestCase):
    def setUp(self):
        SiteSettings(site_name="T", headline="H").save()

    def test_badge_shows_the_mode_with_its_icon(self):
        make_job(work_mode=Experience.WorkMode.ONSITE)
        response = self.client.get(ABOUT)
        self.assertContains(response, "Work mode: </span>On-site", count=2)  # desktop + mobile spot
        self.assertContains(response, '<path d="M6 22V4')  # building icon

    def test_no_mode_no_badge(self):
        make_job()
        self.assertNotContains(self.client.get(ABOUT), "Work mode:")

    def test_dates_still_show_month_and_year(self):
        make_job()
        self.assertContains(self.client.get(ABOUT), "Nov 2024 – Apr 2025")
