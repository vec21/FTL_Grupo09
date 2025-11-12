from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Informe um email válido.")
    first_name = forms.CharField(label="Nome", max_length=150, required=True)

    class Meta:
        model = User
        fields = ("first_name", "username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este email já está registado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Classes base e atributos de acessibilidade
        for name, field in self.fields.items():
            # classe
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()
            # aria-required
            field.widget.attrs['aria-required'] = 'true' if field.required else 'false'
        # Autocomplete adequado
        self.fields['first_name'].widget.attrs.update({'autocomplete': 'given-name'})
        self.fields['username'].widget.attrs.update({'autocomplete': 'username', 'autocapitalize': 'none'})
        self.fields['email'].widget.attrs.update({'autocomplete': 'email'})
        self.fields['password1'].widget.attrs.update({'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'autocomplete': 'new-password'})
        # Marcar campos inválidos quando formulário está vinculado
        if self.is_bound:
            for name in self.fields:
                if self.errors.get(name):
                    self.fields[name].widget.attrs['aria-invalid'] = 'true'
                else:
                    # garantir limpeza quando não há erro
                    self.fields[name].widget.attrs.pop('aria-invalid', None)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()
            field.widget.attrs['aria-required'] = 'true' if field.required else 'false'
        # Autocomplete adequado
        self.fields['username'].widget.attrs.update({'autocomplete': 'username', 'autocapitalize': 'none'})
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password'})
        # Marcar inválidos se aplicável
        if self.is_bound:
            for name in self.fields:
                if self.errors.get(name):
                    self.fields[name].widget.attrs['aria-invalid'] = 'true'
                else:
                    self.fields[name].widget.attrs.pop('aria-invalid', None)


