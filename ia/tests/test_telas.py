"""Testes de acesso das telas do app ia."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ia.models import RequisicaoIA


User = get_user_model()


class TelasIATestCase(TestCase):
    """Verifica permissões e isolamento do consumo individual."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user(username="comum", password="senha")
        self.outro_usuario = User.objects.create_user(username="outro", password="senha")
        self.superusuario = User.objects.create_superuser(
            username="admin",
            password="senha",
            email="admin@example.com",
        )

    def test_usuario_comum_recebe_403_nas_telas_administrativas(self) -> None:
        """Usuário autenticado comum não acessa as três telas administrativas."""
        self.client.force_login(self.usuario)

        for nome in ("ia:requisicoes", "ia:configuracao", "ia:usuarios"):
            with self.subTest(url=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 403)

    def test_usuario_comum_ve_apenas_o_proprio_consumo(self) -> None:
        """A tela de consumo não expõe requisições de outro usuário."""
        RequisicaoIA.objects.create(
            usuario=self.usuario,
            finalidade="propria",
            provedor="falso",
            modelo="teste",
            tentativa=1,
            situacao="sucesso",
        )
        RequisicaoIA.objects.create(
            usuario=self.outro_usuario,
            finalidade="privada_de_outro",
            provedor="falso",
            modelo="teste",
            tentativa=1,
            situacao="sucesso",
        )
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("ia:consumo"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "propria")
        self.assertNotContains(resposta, "privada_de_outro")

    def test_anonymous_e_redirecionado_para_login(self) -> None:
        """Visitante anônimo recebe redirecionamento para autenticação."""
        for nome in ("ia:requisicoes", "ia:configuracao", "ia:usuarios", "ia:consumo"):
            with self.subTest(url=nome):
                resposta = self.client.get(reverse(nome))
                self.assertRedirects(
                    resposta,
                    f"{reverse('login')}?next={reverse(nome)}",
                )

    def test_superusuario_acessa_telas_administrativas(self) -> None:
        """Superusuário acessa as três telas protegidas."""
        self.client.force_login(self.superusuario)

        for nome in ("ia:requisicoes", "ia:configuracao", "ia:usuarios"):
            with self.subTest(url=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)
