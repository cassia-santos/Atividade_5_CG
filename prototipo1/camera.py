"""Câmera LookAt reaproveitada do visualizador, com projeção perspectiva."""

import glm

FOVY = 45.0
NEAR = 0.08
FAR = 12.0


class Camera:
    def __init__(self, distancia=3.0, direcao=(0.0, 0.0, 1.0), centro=(0.0, 0.0, 0.0)):
        self.distancia = distancia
        self.centro = glm.vec3(*centro)
        self.direcao = glm.normalize(glm.vec3(*direcao))
        self.cima = glm.vec3(0.0, 1.0, 0.0)
        self.aspecto = 1.0
        self.fovy = glm.radians(FOVY)

    @property
    def olho(self):
        return self.centro + self.distancia * self.direcao

    def visao(self):
        return glm.lookAt(self.olho, self.centro, self.cima)

    def projecao(self):
        # Preserva o campo horizontal da janela quadrada em formatos estreitos.
        abertura = 2 * glm.atan(glm.tan(self.fovy / 2) / min(1.0, self.aspecto))
        return glm.perspective(abertura, self.aspecto, NEAR, FAR)
