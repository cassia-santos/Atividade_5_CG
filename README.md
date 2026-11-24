# Atividade 5 de Computação Gráfica

Jogo 3D de nave e asteroides. Acerte dez asteroides antes de perder quatro vidas. Uma colisão com a nave ou um asteroide que atravesse o setor à esquerda custa uma vida.

Com o ambiente da disciplina ativado, execute na raiz do repositório:

```bash
python prototipo1/main.py
```

O jogo usa Python, GLFW, ModernGL, NumPy, PyGLM e Pillow. A placa gráfica e o driver precisam oferecer OpenGL 4.0 Core.

| Controle | Ação |
| --- | --- |
| Enter | Iniciar ou reiniciar após o fim |
| Setas | Mover a nave vertical e lateralmente |
| Espaço | Disparar |
| P | Pausar ou retomar |
| C | Alternar entre visão geral e câmera seguidora |
| Roda do mouse | Ajustar a distância da câmera |
| L | Alternar entre ambas as luzes, a direcional e a pontual |
| V | Ligar ou desligar o VSync |
| Esc | Fechar a janela |

O placar verde à esquerda e as vidas azuis à direita aparecem dentro da cena. O título da janela mostra o estado atual, a câmera, a iluminação, o VSync e o FPS.

O PDF acompanha o ZIP de entrega. No repositório, o fonte do relatório está em `relatorio/`. Para compilar no Overleaf, envie `main.tex` e os PNGs para o mesmo projeto. Os PNGs podem ficar ao lado de `main.tex` ou na pasta `capturas/`. Selecione pdfLaTeX.
