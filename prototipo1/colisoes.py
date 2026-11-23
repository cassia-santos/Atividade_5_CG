"""Testes geométricos de colisão contínua, em coordenadas da cena."""

from math import sqrt


def segmento_circulo(inicio, fim, centro, raio):
    """Retorna o primeiro instante t em [0, 1] em que o segmento toca o círculo."""
    dx, dy, dz = fim[0] - inicio[0], fim[1] - inicio[1], fim[2] - inicio[2] 
    ox, oy, oz = inicio[0] - centro[0], inicio[1] - centro[1], inicio[2] - centro[2]
    a = dx * dx + dy * dy + dz * dz
    c = ox * ox + oy * oy + oz * oz - raio * raio
    if c <= 0:
        return 0.0
    if a == 0:
        return None
    b = 2 * (ox * dx + oy * dy + oz * dz)
    discriminante = b * b - 4 * a * c
    if discriminante < 0:
        return None
    t = (-b - sqrt(discriminante)) / (2 * a)
    return t if 0 <= t <= 1 else None


def segmento_caixa(inicio, fim, limites):
    """Interseção do segmento com caixa (xmin, xmax, ymin, ymax)."""
    xmin, xmax, ymin, ymax, zmin, zmax = limites
    t_entrada, t_saida = 0.0, 1.0
    for origem, destino, minimo, maximo in (
        (inicio[0], fim[0], xmin, xmax),
        (inicio[1], fim[1], ymin, ymax),
        (inicio[2], fim[2], zmin, zmax)
    ):
        delta = destino - origem
        if abs(delta) < 1e-12:
            if origem < minimo or origem > maximo:
                return None
            continue
        t1, t2 = (minimo - origem) / delta, (maximo - origem) / delta
        t_entrada = max(t_entrada, min(t1, t2))
        t_saida = min(t_saida, max(t1, t2))
        if t_entrada > t_saida:
            return None
    return t_entrada


def disparo_atinge_asteroide(disparo_antes, disparo_depois,
                            asteroide_antes, asteroide_depois, raio_total):
    """Trajeto relativo dos dois centros: evita atravessar um alvo entre quadros."""
    inicio = (disparo_antes[0] - asteroide_antes[0],
              disparo_antes[1] - asteroide_antes[1],
              disparo_antes[2] - asteroide_antes[2])
    fim = (disparo_depois[0] - asteroide_depois[0],
           disparo_depois[1] - asteroide_depois[1],
           disparo_depois[2] - asteroide_depois[2])
    return segmento_circulo(inicio, fim, (0.0, 0.0, 0.0), raio_total)


def asteroide_atinge_nave(asteroide_antes, asteroide_depois,
                         nave_antes, nave_depois, raio):
    """Asteroide móvel contra caixa da nave, ampliada pelo seu raio."""
    inicio = (asteroide_antes[0] - nave_antes[0],
              asteroide_antes[1] - nave_antes[1],
              asteroide_antes[2] - nave_antes[2])
    fim = (asteroide_depois[0] - nave_depois[0],
           asteroide_depois[1] - nave_depois[1],
           asteroide_depois[2] - nave_depois[2])
    return segmento_caixa(
        inicio, fim, (-0.23 - raio, 0.23 + raio,
                      -0.095 - raio, 0.095 + raio,
                      -0.095 - raio, 0.095 + raio)
    )
