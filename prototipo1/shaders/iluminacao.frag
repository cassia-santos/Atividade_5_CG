#version 400 core

in vec3 fPosicao;
in vec3 fNormal;
in vec2 fUV;
out vec4 outfragcolor;

uniform vec3 u_olho;
uniform bool u_direcional;
uniform vec3 u_direcao_luz;
uniform vec3 u_cor_direcional;
uniform bool u_pontual;
uniform vec3 u_posicao_luz;
uniform vec3 u_cor_pontual;
uniform vec3 u_atenuacao;

uniform sampler2D u_textura;
uniform bool u_tem_textura;
uniform vec3 u_cor;
uniform float u_ka;
uniform float u_kd;
uniform float u_ks;
uniform float u_brilho;
uniform float u_emissao;

vec3 blinn_phong(vec3 N, vec3 V, vec3 L, vec3 base) {
    float difuso = max(dot(N, L), 0.0);
    float especular = 0.0;
    if (difuso > 0.0) {
        vec3 H = normalize(L + V);
        especular = pow(max(dot(N, H), 0.0), u_brilho);
    }
    return u_kd * difuso * base + vec3(u_ks * especular);
}

vec3 codificar_srgb(vec3 linear) {
    linear = clamp(linear, 0.0, 1.0);
    vec3 baixa = 12.92 * linear;
    vec3 alta = 1.055 * pow(linear, vec3(1.0 / 2.4)) - 0.055;
    return mix(alta, baixa, lessThanEqual(linear, vec3(0.0031308)));
}

void main() {
    vec3 N = normalize(fNormal);
    vec3 V = normalize(u_olho - fPosicao);
    // O formato sRGB da textura entrega RGB linear ao shader.
    vec3 base = u_cor;
    if (u_tem_textura) {
        base *= texture(u_textura, fUV).rgb;
    }

    vec3 cor = base * (0.52 * u_ka + u_emissao);
    if (u_direcional) {
        cor += u_cor_direcional * blinn_phong(N, V, normalize(u_direcao_luz), base);
    }
    if (u_pontual) {
        vec3 ate_luz = u_posicao_luz - fPosicao;
        float d = length(ate_luz);
        float atenuacao = 1.0 / dot(u_atenuacao, vec3(1.0, d, d * d));
        cor += atenuacao * u_cor_pontual
             * blinn_phong(N, V, ate_luz / max(d, 0.00001), base);
    }

    outfragcolor = vec4(codificar_srgb(cor), 1.0);
}
