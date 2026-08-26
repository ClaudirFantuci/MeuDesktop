from django.conf import settings
from django.db import models

# Create your models here.


class SocketChoices(models.TextChoices):
	LGA1700 = "LGA1700", "LGA1700"
	LGA1851 = "LGA1851", "LGA1851"
	LGA1200 = "LGA1200", "LGA1200"
	AM5 = "AM5", "AM5"
	AM4 = "AM4", "AM4"


class TipoMemoriaChoices(models.TextChoices):
	DDR4 = "DDR4", "DDR4"
	DDR5 = "DDR5", "DDR5"


class FormFactorChoices(models.TextChoices):
	ATX = "ATX", "ATX"
	MATX = "MATX", "mATX"
	ITX = "ITX", "ITX"
	EATX = "EATX", "E-ATX"


class TipoArmazenamentoChoices(models.TextChoices):
	SSD_SATA = "SSD_SATA", "SSD SATA"
	SSD_NVME = "SSD_NVME", "SSD NVMe"
	HDD = "HDD", "HDD"


class InterfaceArmazenamentoChoices(models.TextChoices):
	SATA3 = "SATA3", "SATA III"
	M2_NVME = "M2_NVME", "M.2 NVMe"
	M2_SATA = "M2_SATA", "M.2 SATA"


class CertificacaoChoices(models.TextChoices):
	GENERIC = "GENERIC", "Genérica"
	PLUS_80 = "80PLUS", "80 Plus"
	PLUS_80_BRONZE = "80PLUS_BRONZE", "80 Plus Bronze"
	PLUS_80_SILVER = "80PLUS_SILVER", "80 Plus Silver"
	PLUS_80_GOLD = "80PLUS_GOLD", "80 Plus Gold"
	PLUS_80_PLATINUM = "80PLUS_PLATINUM", "80 Plus Platinum"
	PLUS_80_TITANIUM = "80PLUS_TITANIUM", "80 Plus Titanium"


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


class Processador(models.Model):
	nome = models.CharField(max_length=120)
	fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name="processadores")
	socket = models.CharField(max_length=20, choices=SocketChoices.choices)
	cores = models.PositiveSmallIntegerField()
	threads = models.PositiveSmallIntegerField()
	frequencia_base = models.DecimalField(max_digits=4, decimal_places=2)
	frequencia_turbo = models.DecimalField(max_digits=4, decimal_places=2)
	tdp = models.PositiveSmallIntegerField(help_text="Watts")
	tem_video_integrado = models.BooleanField(default=False)
	geracao = models.CharField(max_length=60, blank=True)
	preco = models.DecimalField(max_digits=10, decimal_places=2)
	imagem = models.ImageField(upload_to="componentes/processadores/", blank=True, null=True)
	descricao = models.TextField(blank=True)
	disponivel = models.BooleanField(default=True)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["nome"]
		verbose_name = "Processador"
		verbose_name_plural = "Processadores"


class PlacaMae(models.Model):
	nome = models.CharField(max_length=120)
	fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name="placas_mae")
	socket = models.CharField(max_length=20, choices=SocketChoices.choices)
	chipset = models.CharField(max_length=80)
	tipo_memoria = models.CharField(max_length=10, choices=TipoMemoriaChoices.choices)
	slots_ram = models.PositiveSmallIntegerField()
	max_memoria_gb = models.PositiveSmallIntegerField()
	frequencia_max_ram = models.PositiveIntegerField(help_text="MHz")
	form_factor = models.CharField(max_length=10, choices=FormFactorChoices.choices)
	tem_slot_m2 = models.BooleanField(default=True)
	quantidade_m2 = models.PositiveSmallIntegerField(default=0)
	portas_sata = models.PositiveSmallIntegerField(default=0)
	slot_pcie_x16 = models.PositiveSmallIntegerField(default=1)
	preco = models.DecimalField(max_digits=10, decimal_places=2)
	imagem = models.ImageField(upload_to="componentes/placas_mae/", blank=True, null=True)
	descricao = models.TextField(blank=True)
	disponivel = models.BooleanField(default=True)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["nome"]
		verbose_name = "Placa-mãe"
		verbose_name_plural = "Placas-mãe"


class MemoriaRAM(models.Model):
	nome = models.CharField(max_length=120)
	fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name="memorias_ram")
	tipo = models.CharField(max_length=10, choices=TipoMemoriaChoices.choices)
	capacidade_gb = models.PositiveSmallIntegerField()
	quantidade_modulos = models.PositiveSmallIntegerField(default=1)
	frequencia_mhz = models.PositiveIntegerField()
	latencia = models.CharField(max_length=20, blank=True)
	preco = models.DecimalField(max_digits=10, decimal_places=2)
	imagem = models.ImageField(upload_to="componentes/memorias/", blank=True, null=True)
	descricao = models.TextField(blank=True)
	disponivel = models.BooleanField(default=True)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["nome"]
		verbose_name = "Memória RAM"
		verbose_name_plural = "Memórias RAM"


class PlacaDeVideo(models.Model):
	nome = models.CharField(max_length=120)
	fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name="placas_video")
	gpu_chip = models.CharField(max_length=100)
	memoria_gb = models.PositiveSmallIntegerField()
	tipo_memoria = models.CharField(max_length=30)
	interface = models.CharField(max_length=30)
	consumo_watts = models.PositiveSmallIntegerField()
	fonte_recomendada_watts = models.PositiveSmallIntegerField()
	comprimento_mm = models.PositiveSmallIntegerField()
	preco = models.DecimalField(max_digits=10, decimal_places=2)
	imagem = models.ImageField(upload_to="componentes/placas_video/", blank=True, null=True)
	descricao = models.TextField(blank=True)
	disponivel = models.BooleanField(default=True)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["nome"]
		verbose_name = "Placa de vídeo"
		verbose_name_plural = "Placas de vídeo"


class Armazenamento(models.Model):
	nome = models.CharField(max_length=120)
	fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name="armazenamentos")
	tipo = models.CharField(max_length=20, choices=TipoArmazenamentoChoices.choices)
	interface = models.CharField(max_length=20, choices=InterfaceArmazenamentoChoices.choices)
	capacidade_gb = models.PositiveIntegerField()
	velocidade_leitura = models.PositiveIntegerField(help_text="MB/s")
	velocidade_escrita = models.PositiveIntegerField(help_text="MB/s")
	preco = models.DecimalField(max_digits=10, decimal_places=2)
	imagem = models.ImageField(upload_to="componentes/armazenamentos/", blank=True, null=True)
	descricao = models.TextField(blank=True)
	disponivel = models.BooleanField(default=True)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["nome"]
		verbose_name = "Armazenamento"
		verbose_name_plural = "Armazenamentos"


class Fonte(models.Model):
	nome = models.CharField(max_length=120)
	fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name="fontes")
	potencia_watts = models.PositiveSmallIntegerField()
	certificacao = models.CharField(max_length=20, choices=CertificacaoChoices.choices, default=CertificacaoChoices.GENERIC)
	modular = models.BooleanField(default=False)
	preco = models.DecimalField(max_digits=10, decimal_places=2)
	imagem = models.ImageField(upload_to="componentes/fontes/", blank=True, null=True)
	descricao = models.TextField(blank=True)
	disponivel = models.BooleanField(default=True)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["nome"]
		verbose_name = "Fonte"
		verbose_name_plural = "Fontes"


class Montagem(models.Model):
	usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="montagens")
	nome = models.CharField(max_length=120)

	processador = models.ForeignKey(Processador, on_delete=models.SET_NULL, blank=True, null=True, related_name="montagens")
	placa_mae = models.ForeignKey(PlacaMae, on_delete=models.SET_NULL, blank=True, null=True, related_name="montagens")
	memoria_ram = models.ForeignKey(MemoriaRAM, on_delete=models.SET_NULL, blank=True, null=True, related_name="montagens")
	placa_de_video = models.ForeignKey(PlacaDeVideo, on_delete=models.SET_NULL, blank=True, null=True, related_name="montagens")
	armazenamento = models.ForeignKey(Armazenamento, on_delete=models.SET_NULL, blank=True, null=True, related_name="montagens")
	fonte = models.ForeignKey(Fonte, on_delete=models.SET_NULL, blank=True, null=True, related_name="montagens")

	data_criacao = models.DateTimeField(auto_now_add=True)
	data_atualizacao = models.DateTimeField(auto_now=True)
	finalizada = models.BooleanField(default=False)

	def __str__(self):
		return self.nome

	class Meta:
		ordering = ["-data_atualizacao"]
		verbose_name = "Montagem"
		verbose_name_plural = "Montagens"


class HistoricoMontagem(models.Model):
	montagem = models.ForeignKey(Montagem, on_delete=models.CASCADE, related_name="historico")
	acao = models.CharField(max_length=20)
	componente_tipo = models.CharField(max_length=40)
	componente_nome = models.CharField(max_length=120, blank=True)
	data = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.acao} - {self.componente_tipo}"

	class Meta:
		ordering = ["-data"]
		verbose_name = "Histórico de Montagem"
		verbose_name_plural = "Históricos de Montagem"
