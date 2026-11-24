#version 400 core

layout(location = 0) in vec3 vPosition;
layout(location = 1) in vec3 vNormal;
layout(location = 2) in vec2 vUV;

uniform mat4 u_modelo;
uniform mat4 u_visao;
uniform mat4 u_projecao;
uniform mat3 u_normal;

out vec3 fPosicao;
out vec3 fNormal;
out vec2 fUV;

void main() {
    vec4 mundo = u_modelo * vec4(vPosition, 1.0);
    fPosicao = mundo.xyz;
    fNormal = u_normal * vNormal;
    fUV = vUV;
    gl_Position = u_projecao * u_visao * mundo;
}
