"""Jogo 3D de asteroides — Computação Gráfica.

Execução: na raiz do repositório, com o ambiente da disciplina ativado,
  python prototipo1/main.py
Requisitos: Python 3, GLFW, ModernGL, NumPy, PyGLM, Pillow e OpenGL 4.0 Core.

Teclas:
  ENTER         iniciar ou reiniciar depois do fim
  SETA CIMA     mover a nave para cima (segurar)
  SETA BAIXO    mover a nave para baixo (segurar)
  SETA ESQ.     mover a nave para esquerda (segurar)
  SETA DIR.     mover a nave para direita (segurar)
  ESPAÇO        disparar
  P             pausar ou retomar
  C             alternar entre visão geral e câmera seguidora
  Roda do mouse aproximar ou afastar a câmera
  L             alternar luzes (ambas, direcional, pontual)
  V             ligar ou desligar VSync
  ESC           sair

Objetivo: acertar 10 asteroides antes de perder as 4 vidas. Um asteroide
que toca a nave ou sai pela esquerda custa uma vida. O placar aparece
como 10 marcas no topo da cena; as vidas são os quadrados azuis à direita.
"""

import sys
from pathlib import Path

import glfw
import glm
import moderngl
import numpy as np

from Jogo import Jogo
from camera import Camera
from cena3d import Cena3D

SHADERS = Path(__file__).parent / "shaders"
LADO = 800

FUNDO = (0.025, 0.035, 0.063, 1.0)
ESTRELAS = (0.40, 0.49, 0.64, 1.0)
CINZA = (0.72, 0.76, 0.82, 1.0)
AZUL = (0.15, 0.55, 0.95, 1.0)
VERDE = (0.20, 0.84, 0.49, 1.0)
VERMELHO = (0.94, 0.28, 0.27, 1.0)
INATIVO = (0.22, 0.26, 0.34, 1.0)

AVANCO_CAMERA = 0.70
ZOOM_MIN = (3.80, 1.85)
ZOOM_MAX = 6.0
NOMES_CAMERA = ("geral", "seguidora")
PASSO_ZOOM = 0.25


def curva_circulo(n=48):
    """Centro, pontos da circunferência e primeiro ponto repetido: leque."""
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    x = np.concatenate(([0.0], np.cos(t), [1.0]))
    y = np.concatenate(([0.0], np.sin(t), [0.0]))
    return np.column_stack((x, y, np.zeros_like(x), np.ones_like(x))).astype("f4")


def criar_geometrias(ctx, programa):
    """Cria todos os VBOs, EBOs e VAOs uma única vez, antes do laço."""
    estrelas = np.ones((105, 4), dtype="f4")
    estrelas[:, :2] = np.random.default_rng(5).uniform(-1, 1, (len(estrelas), 2))
    estrelas[:, 2] = 0
    dados = {
        "estrelas": estrelas,
        "triangulo": np.array([
            -0.2, 0.2, 0.0, 1.0,
            -0.2, -0.2, 0.0, 1.0,
            0.8, 0.0, 0.0, 1.0,
        ], dtype="f4"),
        "circulo": curva_circulo(),
        "retangulo": np.array([
            -0.5, -0.5, 0.0, 1.0,
            0.5, -0.5, 0.0, 1.0,
            0.5, 0.5, 0.0, 1.0,
            -0.5, 0.5, 0.0, 1.0,
        ], dtype="f4"),
    }
    buffers = {nome: ctx.buffer(vertices.tobytes())
               for nome, vertices in dados.items()}
    indices = ctx.buffer(np.array([0, 1, 2, 2, 3, 0], dtype="u4").tobytes())
    vaos = {}
    for nome, buffer in buffers.items():
        vaos[nome] = ctx.vertex_array(
            programa, [(buffer, "4f", "vPosition")],
            index_buffer=indices if nome == "retangulo" else None,
        )
    return vaos, [*buffers.values(), indices, *vaos.values()]


def erro_glfw(codigo, descricao):
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


def main():
    glfw.set_error_callback(erro_glfw)
    if not glfw.init():
        raise SystemExit("FALHA: GLFW não inicializou")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
    glfw.window_hint(glfw.SAMPLES, 4)
    janela = glfw.create_window(LADO, LADO, "Asteroides | ENTER inicia", None, None)
    if not janela:
        glfw.terminate()
        raise SystemExit("FALHA: não foi possível criar a janela OpenGL 4.0 Core")

    recursos = []
    try:
        glfw.make_context_current(janela)
        glfw.swap_interval(1)
        ctx = moderngl.create_context(require=400)

        programa = ctx.program(
            vertex_shader=(SHADERS / "acerte_o_alvo.vert").read_text(encoding="utf-8"),
            fragment_shader=(SHADERS / "basico.frag").read_text(encoding="utf-8"),
        )
        recursos.append(programa)
        vaos, geometrias = criar_geometrias(ctx, programa)
        recursos.extend(geometrias)

        cena3d = Cena3D(ctx, recursos)
        ctx.front_face = "ccw"
        ctx.cull_face = "back"

        cameras = (
            Camera(distancia=4.30, direcao=(-0.23, 0.58, 0.91),
                   centro=(0.15, -0.08, 0.0)),
            Camera(distancia=2.0, direcao=(-1.0, 0.38, 0.0)),
        )
        modo_camera = 0
        tela = [LADO, LADO]

        jogo = Jogo()
        vsync = True

        def tecla(window, key, _scancode, action, _mods):
            nonlocal vsync, modo_camera
            if action != glfw.PRESS:
                return
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)
            elif key == glfw.KEY_ENTER:
                jogo.entrar()
            elif key == glfw.KEY_SPACE:
                jogo.atirar()
            elif key == glfw.KEY_P:
                jogo.alternar_pausa()
            elif key == glfw.KEY_C and jogo.estado != Jogo.PAUSADO:
                modo_camera = 1 - modo_camera
            elif key == glfw.KEY_L:
                cena3d.alternar_luz()
            elif key == glfw.KEY_V:
                vsync = not vsync
                glfw.swap_interval(1 if vsync else 0)

        def redimensionou(_window, largura, altura):
            largura, altura = max(1, largura), max(1, altura)
            ctx.viewport = (0, 0, largura, altura)
            tela[:] = [largura, altura]
            for camera in cameras:
                camera.aspecto = largura / altura

        def roda(_window, _dx, dy):
            if jogo.estado == Jogo.PAUSADO:
                return
            camera = cameras[modo_camera]
            camera.distancia = float(np.clip(
                camera.distancia - dy * PASSO_ZOOM, ZOOM_MIN[modo_camera], ZOOM_MAX))

        def viewport_quadrado():
            # O viewport quadrado evita distorcer os símbolos do placar.
            largura, altura = tela
            lado = min(largura, altura)
            ctx.viewport = ((largura - lado) // 2, (altura - lado) // 2,
                            lado, lado)

        glfw.set_key_callback(janela, tecla)
        glfw.set_framebuffer_size_callback(janela, redimensionou)
        glfw.set_scroll_callback(janela, roda)
        redimensionou(janela, *glfw.get_framebuffer_size(janela))

        def desenhar(nome, escala, posicao, cor, modo=moderngl.TRIANGLES,
                     angulo=0.0, vertices=-1, primeiro=0):
            modelo = glm.translate(glm.mat4(1), glm.vec3(*posicao, 0))
            modelo = glm.rotate(modelo, angulo, glm.vec3(0, 0, 1))
            modelo = glm.scale(modelo, glm.vec3(*escala, 1))
            programa["u_modelo"].write(modelo.to_bytes())
            programa["u_cor"].value = cor
            vaos[nome].render(mode=modo, vertices=vertices, first=primeiro)

        def desenhar_hud():
            # A mesma geometria de retângulo representa placar e vidas.
            for i in range(jogo.META):
                cor = VERDE if i < jogo.pontos else INATIVO
                desenhar("retangulo", (0.045, 0.055),
                         (-0.88 + i * 0.066, 0.91), cor)
            for i in range(jogo.VIDAS_INICIAIS):
                cor = AZUL if i < jogo.vidas else INATIVO
                desenhar("retangulo", (0.053, 0.053),
                         (0.68 + i * 0.075, 0.91), cor)

        def desenhar_cena():
            ctx.viewport = (0, 0, *tela)
            ctx.clear(*FUNDO)
            desenhar("estrelas", (1.0, 1.0), (0.0, 0.0), ESTRELAS,
                     modo=moderngl.POINTS)

            camera = cameras[modo_camera]
            if modo_camera == 1:
                x, y, z = jogo.nave.obter_posicao()
                camera.centro = glm.vec3(x + AVANCO_CAMERA, y, z)

            ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
            cena3d.desenhar(jogo, camera)
            ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)

            viewport_quadrado()
            desenhar("retangulo", (1.92, 0.004), (0.0, 0.83), INATIVO)
            desenhar_hud()
            if jogo.estado == Jogo.INICIO:
                desenhar("triangulo", (0.65, 1.2), (0.0, 0.0), VERDE)
                desenhar("circulo", (0.52, 0.52), (0.0, 0.0), CINZA,
                         modo=moderngl.LINE_LOOP, vertices=48, primeiro=1)
                return

            if jogo.estado == Jogo.PAUSADO:
                for x in (-0.08, 0.08):
                    desenhar("retangulo", (0.06, 0.34), (x, 0.0), CINZA)
            elif jogo.estado == Jogo.FIM:
                if jogo.venceu:
                    desenhar("circulo", (0.35, 0.35), (0.0, 0.0), VERDE,
                             modo=moderngl.LINE_LOOP, vertices=48, primeiro=1)
                    desenhar("triangulo", (0.30, 0.38), (0.0, 0.0), VERDE)
                else:
                    desenhar("retangulo", (0.48, 0.07), (0.0, 0.0),
                             VERMELHO, angulo=0.78)
                    desenhar("retangulo", (0.48, 0.07), (0.0, 0.0),
                             VERMELHO, angulo=-0.78)

        instante_anterior = glfw.get_time()
        marco, quadros = instante_anterior, 0
        estado_anterior = jogo.estado

        while not glfw.window_should_close(janela):
            glfw.poll_events()
            agora = glfw.get_time()
            dt = min(max(agora - instante_anterior, 0.0), jogo.DT_MAXIMO)
            instante_anterior = agora

            # A tecla de pausa/início/reinício pode ter mudado o estado durante
            # poll_events. Este quadro não incorpora o tempo gasto na transição.
            if jogo.estado != estado_anterior:
                dt = 0.0
            estado_anterior = jogo.estado

            sobe = glfw.get_key(janela, glfw.KEY_UP) == glfw.PRESS
            desce = glfw.get_key(janela, glfw.KEY_DOWN) == glfw.PRESS
            direita = glfw.get_key(janela, glfw.KEY_RIGHT) == glfw.PRESS
            esquerda = glfw.get_key(janela, glfw.KEY_LEFT) == glfw.PRESS
            jogo.atualizar(dt, int(sobe) - int(desce), int(direita) - int(esquerda))
            desenhar_cena()
            glfw.swap_buffers(janela)

            quadros += 1
            if agora - marco >= 0.5:
                estado = ("vitória" if jogo.venceu else "derrota") \
                    if jogo.estado == Jogo.FIM else jogo.estado
                glfw.set_window_title(
                    janela,
                    f"Asteroides | {estado} | {jogo.pontos}/{jogo.META} pontos | "
                    f"{jogo.vidas} vidas | câmera {NOMES_CAMERA[modo_camera]} | "
                    f"luz {cena3d.MODOS_LUZ[cena3d.modo_luz]} | VSync {'ON' if vsync else 'OFF'} | "
                    f"{quadros / (agora - marco):.1f} FPS"
                )
                marco, quadros = agora, 0
    finally:
        for recurso in reversed(recursos):
            recurso.release()
        glfw.destroy_window(janela)
        glfw.terminate()


if __name__ == "__main__":
    main()
