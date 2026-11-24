"""Dados de um asteroide, independentes do código de desenho."""

from math import sin


class Asteroide:
    LIMITE_Z = 0.62

    def __init__(self, x, y, z=0.0, velocidade=0.35, velocidade_z=0.0, raio=0.075, fase=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.velocidade = velocidade  # unidades da cena por segundo
        self.velocidade_z = velocidade_z
        self.raio = raio
        self.fase = fase

    def atualizar_posicao(self, dt):
        self.x -= self.velocidade * dt
        self.z += self.velocidade_z * dt
        if abs(self.z) > self.LIMITE_Z:
            borda = self.LIMITE_Z if self.z > 0 else -self.LIMITE_Z
            self.z = 2 * borda - self.z
            self.velocidade_z = -self.velocidade_z
        self.fase += 2.4 * dt

    def obter_posicao(self):
        return self.x, self.y, self.z

    @property
    def raio_visual(self):
        return self.raio * (0.94 + 0.06 * sin(self.fase))
