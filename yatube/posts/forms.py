from django import forms
from django.forms import ModelForm
from django.forms.widgets import Textarea
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post

        fields = ('group', 'text', 'image')

        labels = {
            'group': ('Группа'),
            'text': ('Текст'),
            'image': ('Изображение')
        }

        help_texts = {
            'group': ('Выберите группу для новой записи'),
            'text': ('Добавьте текст для новой записи'),
            'image': ('Загрузите изображение для новой записи')
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': Textarea}
        help_texts = {'text': ('Ваш комментарий')}

    def clean_text(self):
        comment = self.cleaned_data['text']
        if not comment:
            raise forms.ValidationError(
                "Нельзя добавить пустой комментарий")
        return comment
