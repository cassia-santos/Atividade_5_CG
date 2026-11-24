#version 400 core

layout(location = 0) in vec4 vPosition;

uniform mat4 u_modelo;
uniform vec4 u_cor;

out vec4 v2fcolor;

void main() {
    // As geometrias 2D usam diretamente o plano normalizado da tela.
    gl_Position = u_modelo * vPosition;
    v2fcolor = u_cor;
}
