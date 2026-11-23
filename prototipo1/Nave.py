"""Nave controlada pelo jogador."""

from Disparo import Disparo


class Nave:
    def __init__(self, x=-0.8, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.velocidade = 1.1  # unidades da cena por segundo
        self.limite_y = 0.72
        self.limite_z = 0.72
        self.disparos = []

    def obter_posicao(self):
        return self.x, self.y, self.z

    def atualizar_posicao(self, sentido_y, sentido_z, dt):
        self.y += sentido_y * self.velocidade * dt
        self.z += sentido_z * self.velocidade * dt
        self.y = max(-self.limite_y, min(self.limite_y, self.y))
        self.z = max(-self.limite_z, min(self.limite_z, self.z))

    def atirar(self):
        if len(self.disparos) >= 3:
            return
        # A ponta da geometria da nave fica a 0,28 da origem.
        self.disparos.append(Disparo(self.x + 0.28, self.y, self.z))
