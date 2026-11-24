"""Geometrias, texturas e desenho da cena em coordenadas do mundo."""

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path

import glm
import moderngl
import numpy as np
from PIL import Image

from malha import Malha, normais_de_vertice

PASTA = Path(__file__).resolve().parent
GL_SRGB8_ALPHA8 = 0x8C43
DIRECAO_LUZ = (0.35, 0.70, 0.62)  # do fragmento para a fonte direcional
COR_DIRECIONAL = (0.94, 0.94, 1.0)
COR_PONTUAL = (0.55, 0.88, 1.0)
ATENUACAO = (1.0, 0.23, 0.20)


@dataclass(frozen=True)
class Material:
    cor: tuple
    ka: float
    kd: float
    ks: float
    brilho: float
    emissao: float = 0.0


METAL = Material((0.43, 0.65, 0.82), 0.25, 0.76, 0.53, 44.0)
ROCHA = Material((1.24, 1.20, 1.16), 0.29, 0.95, 0.10, 12.0)
PAINEL = Material((0.98, 1.12, 1.23), 0.28, 0.81, 0.27, 28.0)
SINAL = Material((0.10, 0.63, 0.70), 0.30, 0.46, 0.26, 26.0, 0.60)
DISPARO = Material((0.18, 0.89, 1.0), 0.0, 0.0, 0.0, 1.0, 1.0)
MIRA = Material((0.035, 0.10, 0.14), 0.0, 0.0, 0.0, 1.0, 1.0)


def matriz_normal(modelo):
    """Inversa transposta da parte linear da matriz de modelo."""
    return glm.transpose(glm.inverse(glm.mat3(modelo)))


def enviar(programa, **uniformes):
    for nome, valor in uniformes.items():
        if isinstance(valor, (glm.mat3, glm.mat4)):
            programa[nome].write(valor.to_bytes())
        else:
            programa[nome].value = valor


def triangulo(destino, pontos, uvs):
    a, b, c = pontos
    normal = np.cross(b - a, c - a)
    normal /= np.linalg.norm(normal)
    destino.extend((*p, *normal, *uv) for p, uv in zip(pontos, uvs))


def asteroide(setores=16, faixas=10):
    """Malha esférica irregular, com normais compartilhadas na costura."""
    pontos = [(0.0, -0.84, 0.0)]
    for linha in range(1, faixas):
        phi = pi * (linha / faixas - 0.5)
        for coluna in range(setores):
            theta = 2.0 * pi * coluna / setores
            raio = 0.85 + 0.08 * sin(3 * theta + phi) * cos(phi)
            raio += 0.07 * cos(5 * theta - 4 * phi) * cos(phi)
            pontos.append((raio * cos(phi) * cos(theta), raio * sin(phi),
                           raio * cos(phi) * sin(theta)))
    pontos.append((0.0, 0.84, 0.0))

    def indice(coluna, linha):
        if linha == 0:
            return 0
        if linha == faixas:
            return len(pontos) - 1
        return 1 + (linha - 1) * setores + coluna % setores

    faces, uvs = [], []
    for linha in range(faixas):
        v0, v1 = linha / faixas, (linha + 1) / faixas
        for coluna in range(setores):
            u0, u1 = coluna / setores, (coluna + 1) / setores
            a, b = indice(coluna, linha), indice(coluna + 1, linha)
            c, d = indice(coluna, linha + 1), indice(coluna + 1, linha + 1)
            meio = (u0 + u1) / 2
            if linha != 0:
                faces.append((a, c, b))
                uvs.append(((u0, v0), (meio if linha == faixas - 1 else u0, v1), (u1, v0)))
            if linha != faixas - 1:
                faces.append((b, c, d))
                uvs.append(((meio if linha == 0 else u1, v0), (u0, v1), (u1, v1)))

    pontos = np.asarray(pontos, dtype="f4")
    faces = np.asarray(faces, dtype="u4")
    normais = normais_de_vertice(pontos, faces)
    return np.column_stack((
        pontos[faces].reshape(-1, 3),
        normais[faces].reshape(-1, 3),
        np.asarray(uvs, dtype="f4").reshape(-1, 2),
    ))


def caixa():
    """Cubo unitário com UV planar repetido duas vezes ao longo da face."""
    dados = []
    for eixo in range(3):
        for sinal in (-1, 1):
            normal = np.eye(3)[eixo] * sinal
            direita = np.eye(3)[(eixo + 1) % 3]
            cima = np.cross(normal, direita)
            a = (normal - direita - cima) / 2
            b, c, d = a + direita, a + direita + cima, a + cima
            triangulo(dados, (a, b, c), ((0, 0), (1, 0), (1, 2)))
            triangulo(dados, (a, c, d), ((0, 0), (1, 2), (0, 2)))
    return np.asarray(dados, dtype="f4")


def guia_disparo():
    """Segmentos fixos deslocados junto com a nave, na direção +X."""
    dados = [(x, 0, 0, 0, 1, 0, 0, 0)
             for i in range(9) for x in (0.31 + i * 0.17, 0.39 + i * 0.17)]
    return np.asarray(dados, dtype="f4")


class Cena3D:
    MODOS_LUZ = ("ambas", "direcional", "pontual")

    def __init__(self, ctx, recursos):
        self.programa = ctx.program(
            vertex_shader=(PASTA / "shaders/iluminacao.vert").read_text(encoding="utf-8"),
            fragment_shader=(PASTA / "shaders/iluminacao.frag").read_text(encoding="utf-8"),
        )
        recursos.append(self.programa)

        def criar_vao(dados):
            vbo = ctx.buffer(dados.tobytes())
            recursos.append(vbo)
            vao = ctx.vertex_array(self.programa,
                                   [(vbo, "3f 3f 2f", "vPosition", "vNormal", "vUV")])
            recursos.append(vao)
            return vao

        def carregar_textura(nome, repetir_v):
            with Image.open(PASTA / "texturas" / nome) as imagem:
                imagem = imagem.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                textura = ctx.texture(imagem.size, 4, imagem.tobytes(),
                                      internal_format=GL_SRGB8_ALPHA8)
            recursos.append(textura)
            textura.repeat_x = True
            textura.repeat_y = repetir_v
            textura.build_mipmaps()
            textura.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
            return textura

        nave = Malha(PASTA / "off/nave.off")
        dados_nave = nave.facetada()
        sem_uv = np.zeros((len(dados_nave), 2), dtype="f4")
        self.nave = criar_vao(np.hstack((dados_nave, sem_uv)))
        self.enquadramento_nave = nave.matriz_enquadramento(0.26)
        self.asteroide = criar_vao(asteroide())
        self.caixa = criar_vao(caixa())
        self.mira = criar_vao(guia_disparo())
        self.textura_rocha = carregar_textura("rocha.png", repetir_v=False)
        self.textura_painel = carregar_textura("paineis.png", repetir_v=True)

        self.modo_luz = 0
        enviar(self.programa, u_textura=0, u_direcao_luz=DIRECAO_LUZ,
               u_cor_direcional=COR_DIRECIONAL, u_cor_pontual=COR_PONTUAL,
               u_atenuacao=ATENUACAO)

    def alternar_luz(self):
        self.modo_luz = (self.modo_luz + 1) % len(self.MODOS_LUZ)

    def desenhar_malha(self, vao, modelo, material, textura=None, modo=moderngl.TRIANGLES):
        if textura is not None:
            textura.use(0)
        enviar(self.programa, u_modelo=modelo, u_normal=matriz_normal(modelo),
               u_tem_textura=textura is not None, u_cor=material.cor,
               u_ka=material.ka, u_kd=material.kd, u_ks=material.ks,
               u_brilho=material.brilho, u_emissao=material.emissao)
        vao.render(modo)

    def desenhar_farol(self):
        partes = (
            ((0.82, -0.72, -0.86), (0.32, 0.12, 0.32), PAINEL, self.textura_painel),
            ((0.82, -0.39, -0.86), (0.22, 0.56, 0.22), PAINEL, self.textura_painel),
            ((0.82, -0.08, -0.86), (0.28, 0.075, 0.28), SINAL, None),
        )
        for posicao, escala, material, textura in partes:
            modelo = glm.scale(glm.translate(glm.mat4(1), glm.vec3(*posicao)), glm.vec3(*escala))
            self.desenhar_malha(self.caixa, modelo, material, textura)

    def desenhar(self, jogo, camera):
        posicao_nave = glm.vec3(*jogo.nave.obter_posicao())
        enviar(self.programa, u_visao=camera.visao(), u_projecao=camera.projecao(),
               u_olho=tuple(camera.olho),
               u_posicao_luz=tuple(posicao_nave + glm.vec3(0.32, 0.40, 0.18)),
               u_direcional=self.modo_luz != 2, u_pontual=self.modo_luz != 1)
        self.desenhar_farol()
        for rocha in jogo.gerenciador.asteroides:
            if rocha.x - rocha.raio > 2.2:
                continue
            modelo = glm.translate(glm.mat4(1), glm.vec3(*rocha.obter_posicao()))
            modelo = glm.rotate(modelo, rocha.fase * 0.35, glm.vec3(0.2, 1.0, 0.4))
            modelo = glm.scale(modelo, glm.vec3(rocha.raio_visual))
            self.desenhar_malha(self.asteroide, modelo, ROCHA, self.textura_rocha)

        for disparo in jogo.nave.disparos:
            modelo = glm.translate(glm.mat4(1), glm.vec3(*disparo.obter_posicao()))
            modelo = glm.scale(modelo, glm.vec3(2 * disparo.RAIO))
            self.desenhar_malha(self.caixa, modelo, DISPARO)

        translacao_nave = glm.translate(glm.mat4(1), posicao_nave)
        self.desenhar_malha(self.nave, translacao_nave * self.enquadramento_nave, METAL)
        if jogo.estado in (jogo.ANDAMENTO, jogo.PAUSADO):
            self.desenhar_malha(self.mira, translacao_nave, MIRA, modo=moderngl.LINES)
