from django.db import models

# Create your models here.


class Fabricante(models.Model):
	nome = models.CharField(max_length=80)
	website = models.URLField(blank=True)
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["nome"]
		verbose_name = "Fabricante"
		verbose_name_plural = "Fabricantes"
