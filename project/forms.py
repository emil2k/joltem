from django import forms

from .models import Project

class ProjectSettingsForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ('title', 'description', 'admin_set', 'manager_set',
                  'developer_set')

    def clean_title(self):
        return self.cleaned_data.get('title', '').strip()
