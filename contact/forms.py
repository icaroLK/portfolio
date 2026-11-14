from django import forms

from .models import ContactMessage

# Shared look for every input (V2: soft fill, light border, 10 px radius, 44 px tall).
INPUT_CLASSES = (
    "w-full min-h-11 rounded-btn border border-line-input bg-page px-3.5 py-3 "
    "text-base text-ink aria-invalid:border-error"
)


class ContactForm(forms.ModelForm):
    # Honeypot: hidden from people, so only bots fill it in. Not a model field.
    website = forms.CharField(required=False)

    message = forms.CharField(
        min_length=10,
        max_length=5000,
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "topic", "message"]
        labels = {"topic": "What's this about?"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topic"].initial = ContactMessage.Topic.JOB  # first option, as in the design
        for name, field in self.fields.items():
            if name != "website":
                field.widget.attrs["class"] = INPUT_CLASSES

    def full_clean(self):
        super().full_clean()
        # Point each invalid input at its error line, so screen readers read it out.
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs["aria-describedby"] = f"id_{name}_error"

    def is_spam(self):
        """True when the honeypot was filled in. Checked before validation on purpose,
        so a bot never gets error messages that hint at what went wrong."""
        return bool(self.data.get("website"))
