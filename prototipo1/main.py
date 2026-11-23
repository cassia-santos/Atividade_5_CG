"""Jogo 3D de asteroides — Computação Gráfica.

Execução: python main.py (a partir desta pasta)
Requisitos: Python 3, glfw, moderngl, numpy e OpenGL 4.0 Core.

Teclas:
  ENTER         iniciar ou reiniciar depois do fim
  SETA CIMA     mover a nave para cima (segurar)
  SETA BAIXO    mover a nave para baixo (segurar)
  SETA ESQ.     mover a nave para esquerda (segurar)
  SETA DIR.     mover a nave para direita (segurar)
  ESPAÇO        disparar
  P             pausar ou retomar
  C             alternar camera entre a seguidora e a geral
  Roda do mouse aproxima ou afasta a camera
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
from malha import Malha
from camera import Camera  

SHADERS = Path(__file__).parent / "shaders"
MODELOS = Path(__file__).parent / "off"
LADO = 800  # viewport quadrado: mesmas unidades em x e y

FUNDO = (0.04, 0.05, 0.09, 1.0)
CINZA = (0.72, 0.76, 0.82, 1.0)
AZUL = (0.15, 0.55, 0.95, 1.0)
VERDE = (0.20, 0.84, 0.49, 1.0)
VERMELHO = (0.94, 0.28, 0.27, 1.0)
INATIVO = (0.22, 0.26, 0.34, 1.0)

F_NAVE = 0.233
AVANCO_CAMERA = 0.8
ZOOM_MIN, ZOOM_MAX = 1.6, 6.0
PASSO_ZOOM = 0.25

def curva_circulo(n=48):
    """Centro, pontos da circunferência e primeiro ponto repetido: leque."""
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    x = np.concatenate(([0.0], np.cos(t), [1.0]))
    y = np.concatenate(([0.0], np.sin(t), [0.0]))
    return np.column_stack((x, y, np.zeros_like(x), np.ones_like(x))).astype("f4")


def criar_geometrias(ctx, programa):
    """Cria todos os VBOs, EBOs e VAOs uma única vez, antes do laço."""
    dados = {
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
    return vaos, [*vaos.values(), *buffers.values(), indices]


def erro_glfw(codigo, descricao):
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


def criar_malha(ctx, programa, caminho):
    malha = Malha(caminho)
    dados, indices = malha.suave()
    vbo = ctx.buffer(dados.tobytes())
    ebo = ctx.buffer(indices.tobytes())
    vao = ctx.vertex_array(programa, [(vbo, "3f 3f", "vPosition", "vNormal")], index_buffer=ebo)
    return malha, vao, [vao, vbo, ebo]

def matriz_normal(modelo):
    """Inversa transposta do bloco 3x3 da matriz de modelo."""
    return glm.transpose(glm.inverse(glm.mat3(modelo)))

def enviar(prog, **uniformes):
    """Envia os uniformes que o programa declara e ignora os outros,
    como vao_de faz com os atributos."""
    for nome, valor in uniformes.items():
        if nome not in prog:
            continue
        if isinstance(valor, (glm.mat3, glm.mat4)):
            prog[nome].write(valor.to_bytes())    # por colunas
        else:
            prog[nome].value = valor

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
        
        programa3d = ctx.program(
            vertex_shader=(SHADERS / "normais.vert").read_text(encoding="utf-8"),
            fragment_shader=(SHADERS / "normais.frag").read_text(encoding="utf-8"),
        )
        
        recursos.append(programa3d)
        malha_nave, vao_nave, rec = criar_malha(ctx, programa3d, MODELOS / "nave.off")
        recursos.extend(rec)
        malha_esfera, vao_esfera, rec = criar_malha(ctx, programa3d, MODELOS / "esfera.off")
        recursos.extend(rec)
        
        cameras = [Camera(distancia=2.6, direcao=(-0.7, 0.6, 0.7)), Camera(distancia=1.6, direcao=(-1.0, 0.3, 0.0))]                            
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
            elif key == glfw.KEY_C:
                modo_camera = 1 - modo_camera
            elif key == glfw.KEY_V:
                vsync = not vsync
                glfw.swap_interval(1 if vsync else 0)

        

        def redimensionou(window, largura, altura):
            largura, altura = max(1, largura), max(1, altura)
            ctx.viewport = (0, 0, largura, altura)
            tela[:] = [largura, altura]
            for camera in cameras:
                camera.aspecto = largura/altura
           
        def roda(window, dx, dy):
            camera = cameras[modo_camera]
            camera.distancia = float(np.clip(
                camera.distancia - dy * PASSO_ZOOM, ZOOM_MIN, ZOOM_MAX))
         
        def viewport_quadrado():
            # Como o placar é desenhado em coordenadas da tela: um viewport quadrado e centrado evita que ele estique.
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
            programa["u_escala"].value = escala
            programa["u_deslocamento"].value = posicao
            programa["u_angulo"].value = angulo
            programa["u_cor"].value = cor
            vaos[nome].render(mode=modo, vertices=vertices, first=primeiro)
            
        def desenhar_malha(vao, modelo):
            enviar(programa3d, u_modelo=modelo, u_normal=matriz_normal(modelo))
            vao.render(moderngl.TRIANGLES)

        def desenhar_nave(posicao, F=F_NAVE):
            modelo = (glm.translate(glm.mat4(1.0), glm.vec3(*posicao))
                      * glm.rotate(glm.mat4(1.0), glm.radians(-90.0),
                                   glm.vec3(0.0, 0.0, 1.0))
                      * malha_nave.matriz_enquadramento(F))
            desenhar_malha(vao_nave, modelo)

        def desenhar_asteroide(posicao, raio):
            modelo = (glm.translate(glm.mat4(1.0), glm.vec3(*posicao))
                      * malha_esfera.matriz_enquadramento(raio))
            desenhar_malha(vao_esfera, modelo)


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
            if jogo.estado == Jogo.INICIO:
                viewport_quadrado()
                desenhar("triangulo", (0.65, 1.2), (0.0, 0.0), VERDE)
                desenhar("circulo", (0.52, 0.52), (0.0, 0.0), CINZA,
                         modo=moderngl.LINE_LOOP, vertices=48, primeiro=1)
                return
            
            camera = cameras[modo_camera]
            if camera is cameras[1]:
                x, y, z = jogo.nave.obter_posicao()
                camera.centro = glm.vec3(x + AVANCO_CAMERA, y, z)
            enviar(programa3d, u_visao=camera.visao(), u_projecao=camera.projecao())
            
            ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
            visiveis = [a for a in jogo.gerenciador.asteroides if a.x - a.raio <= 1.0]
            
            for asteroide in visiveis:
                desenhar_asteroide(asteroide.obter_posicao(),
                                   asteroide.raio_visual)
            
            for disparo in jogo.nave.disparos:
               desenhar_asteroide(disparo.obter_posicao(), disparo.RAIO)
            desenhar_nave(jogo.nave.obter_posicao())
            
            ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
            viewport_quadrado() 
            desenhar("retangulo", (1.92, 0.004), (0.0, 0.83), INATIVO)
            desenhar_hud()

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
                    f"{jogo.vidas} vidas | VSync {'ON' if vsync else 'OFF'} | "
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
