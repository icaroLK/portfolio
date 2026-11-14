from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from portfolio.models import Project, SiteSettings, Tech, TypeTag

from .helpers import AdminLoginMixin, TempMediaMixin, make_big_png, make_png

ADMIN = f"/{settings.ADMIN_PATH}/"


class AdminPagesLoadTests(AdminLoginMixin, TestCase):
    def test_every_list_and_add_page_loads(self):
        for model in ["project", "typetag", "tech", "experience", "education",
                      "skillgroup", "service"]:
            for page in ["", "add/"]:
                url = f"{ADMIN}portfolio/{model}/{page}"
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_header_shows_site_name(self):
        SiteSettings(site_name="Demo Name", headline="h").save()
        self.assertContains(self.client.get(ADMIN), "Demo Name admin")


class SiteSettingsAdminTests(AdminLoginMixin, TestCase):
    url = f"{ADMIN}portfolio/sitesettings/"

    def test_list_jumps_to_the_single_edit_page(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{self.url}1/change/")

    def test_no_add_or_delete(self):
        SiteSettings.load()
        self.assertEqual(self.client.get(f"{self.url}add/").status_code, 403)
        self.assertEqual(self.client.get(f"{self.url}1/delete/").status_code, 403)
        page = self.client.get(f"{self.url}1/change/")
        self.assertNotContains(page, "deletelink")
        for fieldset in ["Hero", "About", "Links &amp; resume", "SEO", "Section toggles"]:
            self.assertContains(page, fieldset)


class ProjectAdminTests(TempMediaMixin, AdminLoginMixin, TestCase):
    add_url = f"{ADMIN}portfolio/project/add/"

    def setUp(self):
        super().setUp()
        self.tag = TypeTag.objects.create(name="Bot", slug="bot")
        self.techs = [Tech.objects.create(name=f"Tech {i}", slug=f"tech-{i}") for i in range(5)]

    def form_data(self, cover, features=4, stack=5, gallery=3):
        """POST data for the add page: main fields plus the three inlines."""
        data = {
            "title": "Demo", "slug": "demo", "pitch": "p", "what_it_does": "w",
            "type_tags": [self.tag.pk], "is_published": "on", "cover_image": cover,
            "features-TOTAL_FORMS": features, "features-INITIAL_FORMS": 0,
            "stack-TOTAL_FORMS": stack, "stack-INITIAL_FORMS": 0,
            "gallery-TOTAL_FORMS": gallery, "gallery-INITIAL_FORMS": 0,
        }
        for i in range(features):
            data |= {f"features-{i}-text": f"Feature {i}", f"features-{i}-order": i}
        for i in range(stack):
            data |= {f"stack-{i}-tech": self.techs[i].pk, f"stack-{i}-purpose": "x",
                     f"stack-{i}-order": i}
        for i in range(gallery):
            data |= {f"gallery-{i}-image": make_png(f"g{i}.png"), f"gallery-{i}-order": i}
        return data

    def test_project_with_features_stack_and_gallery_in_one_save(self):
        response = self.client.post(self.add_url, self.form_data(make_png()))
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(slug="demo")
        self.assertEqual(project.features.count(), 4)
        self.assertEqual(project.stack.count(), 5)
        self.assertEqual(project.gallery.count(), 3)

    def test_image_over_5mb_is_rejected(self):
        response = self.client.post(self.add_url, self.form_data(make_big_png(), 0, 0, 0))
        self.assertContains(response, "The maximum is 5 MB")
        self.assertFalse(Project.objects.exists())

    def test_exe_upload_is_rejected(self):
        exe =SimpleUploadedFile("tool.exe", b"MZ fake program")
        response = self.client.post(self.add_url, self.form_data(exe, 0, 0, 0))
        self.assertContains(response, "Upload a valid image")
        self.assertFalse(Project.objects.exists())

    def test_list_has_featured_and_published_toggles(self):
        self.client.post(self.add_url, self.form_data(make_png(), 0, 0, 0))
        page = self.client.get(f"{ADMIN}portfolio/project/")
        self.assertContains(page, 'name="form-0-is_featured"')
        self.assertContains(page, 'name="form-0-is_published"')
