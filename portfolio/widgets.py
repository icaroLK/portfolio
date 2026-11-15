"""Admin form widgets."""

from datetime import date

from django.forms import MultiWidget
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextareaWidget


class MarkdownTextarea(UnfoldAdminTextareaWidget):
    """The normal admin text box plus a B / I / H / List / Link toolbar above it."""

    def __init__(self, attrs=None):
        super().__init__(attrs={**(attrs or {}), "data-markdown": "true"})

    class Media:
        js = ["portfolio_admin/markdown_toolbar.js"]
        css = {"all": ["portfolio_admin/markdown_toolbar.css"]}


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
FIRST_YEAR = 1990


class MonthYearWidget(MultiWidget):
    """A date as two dropdowns, month and year. Saved as the 1st of that month.

    Click the year box and type "2024" to jump straight to it.
    Both empty means no date (for example "Present"); only one picked is an error.
    """

    template_name = "portfolio/widgets/month_year.html"

    def __init__(self, attrs=None):
        last_year = date.today().year + 6
        months = [("", "Month")] + [(str(i), name) for i, name in enumerate(MONTHS, start=1)]
        years = [("", "Year")] + [(str(y), str(y)) for y in range(last_year, FIRST_YEAR - 1, -1)]
        widgets = [
            UnfoldAdminSelectWidget(attrs={"aria-label": "Month"}, choices=months),
            UnfoldAdminSelectWidget(attrs={"aria-label": "Year"}, choices=years),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if not value:
            return ["", ""]
        if isinstance(value, str):  # redisplay after a form error
            try:
                value = date.fromisoformat(value)
            except ValueError:
                return ["", ""]
        return [str(value.month), str(value.year)]

    def value_from_datadict(self, data, files, name):
        month, year = super().value_from_datadict(data, files, name)
        if not month and not year:
            return ""
        if not month or not year:
            return "incomplete"  # not a date, so the form shows "Enter a valid date."
        return f"{int(year):04d}-{int(month):02d}-01"
